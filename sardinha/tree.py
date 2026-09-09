"""Modelo e persistência da árvore de decisão do Jogo do Thor.

Este módulo é deliberadamente livre de I/O interativo: não há ``input()``
nem ``print()`` aqui. Ele conhece apenas a estrutura da base de
conhecimento (uma árvore binária) e como gravá-la/lê-la em JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Sequence, TypeAlias

__all__ = [
    "Folha",
    "Pergunta",
    "No",
    "Caminho",
    "ArvoreInvalidaError",
    "arvore_semente",
    "para_dict",
    "de_dict",
    "carregar",
    "salvar",
    "descer",
    "localizar",
    "substituir",
    "criar_no",
    "aprender",
    "animais",
    "contar_animais",
]

CAMINHO_PADRAO: Path = Path("animais.json")


class ArvoreInvalidaError(ValueError):
    """Levantada quando os dados serializados não descrevem uma árvore válida."""


@dataclass(frozen=True, slots=True)
class Folha:
    """Nó terminal: contém o palpite de um animal."""

    animal: str


@dataclass(frozen=True, slots=True)
class Pergunta:
    """Nó interno: contém uma pergunta de sim/não e os dois ramos."""

    texto: str
    sim: "No"
    nao: "No"


No: TypeAlias = Folha | Pergunta
Caminho: TypeAlias = Sequence[bool]
"""Sequência de respostas (``True`` = sim) que leva da raiz até um nó."""


def arvore_semente() -> No:
    """Árvore mínima usada quando ainda não existe base de conhecimento."""
    return Pergunta(
        texto="ele vive na água?",
        sim=Folha(animal="baleia"),
        nao=Folha(animal="cachorro"),
    )


# --------------------------------------------------------------------------
# Serialização
# --------------------------------------------------------------------------


def para_dict(no: No) -> dict[str, Any]:
    """Converte a árvore em estruturas primitivas prontas para JSON."""
    match no:
        case Folha(animal=animal):
            return {"tipo": "folha", "animal": animal}
        case Pergunta(texto=texto, sim=sim, nao=nao):
            return {
                "tipo": "pergunta",
                "texto": texto,
                "sim": para_dict(sim),
                "nao": para_dict(nao),
            }


def de_dict(dados: Any) -> No:
    """Reconstrói a árvore a partir de estruturas primitivas.

    Levanta :class:`ArvoreInvalidaError` para dados malformados.
    """
    if not isinstance(dados, dict):
        raise ArvoreInvalidaError(f"esperava um objeto, recebi {type(dados).__name__}")

    tipo = dados.get("tipo")
    if tipo == "folha":
        animal = dados.get("animal")
        if not isinstance(animal, str):
            raise ArvoreInvalidaError("folha sem o campo 'animal' em texto")
        return Folha(animal=animal)
    if tipo == "pergunta":
        texto = dados.get("texto")
        if not isinstance(texto, str):
            raise ArvoreInvalidaError("pergunta sem o campo 'texto' em texto")
        if "sim" not in dados or "nao" not in dados:
            raise ArvoreInvalidaError("pergunta sem os ramos 'sim' e 'nao'")
        return Pergunta(texto=texto, sim=de_dict(dados["sim"]), nao=de_dict(dados["nao"]))
    raise ArvoreInvalidaError(f"tipo de nó desconhecido: {tipo!r}")


def carregar(caminho: Path = CAMINHO_PADRAO) -> No:
    """Lê a árvore do arquivo JSON; devolve a semente se ele não existir."""
    try:
        conteudo = caminho.read_text(encoding="utf-8")
    except FileNotFoundError:
        return arvore_semente()
    try:
        dados = json.loads(conteudo)
    except json.JSONDecodeError as erro:
        raise ArvoreInvalidaError(f"JSON inválido em {caminho}: {erro}") from erro
    return de_dict(dados)


def salvar(no: No, caminho: Path = CAMINHO_PADRAO) -> None:
    """Grava a árvore no arquivo JSON, criando os diretórios necessários."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(para_dict(no), ensure_ascii=False, indent=2)
    caminho.write_text(texto + "\n", encoding="utf-8")


# --------------------------------------------------------------------------
# Navegação
# --------------------------------------------------------------------------


def descer(no: Pergunta, resposta: bool) -> No:
    """Escolhe o ramo correspondente à resposta dada."""
    return no.sim if resposta else no.nao


def localizar(raiz: No, caminho: Caminho) -> No:
    """Percorre a árvore seguindo as respostas de ``caminho``.

    Levanta :class:`ValueError` se o caminho for mais longo que a árvore.
    """
    atual = raiz
    for indice, resposta in enumerate(caminho):
        if isinstance(atual, Folha):
            raise ValueError(f"caminho longo demais: folha alcançada no passo {indice}")
        atual = descer(atual, resposta)
    return atual


def substituir(raiz: No, caminho: Caminho, novo: No) -> No:
    """Devolve uma nova árvore com o nó em ``caminho`` trocado por ``novo``.

    A árvore original não é modificada (os nós são imutáveis).
    """
    if not caminho:
        return novo
    if isinstance(raiz, Folha):
        raise ValueError("caminho longo demais: folha alcançada antes do fim")
    resposta, resto = caminho[0], caminho[1:]
    if resposta:
        return Pergunta(texto=raiz.texto, sim=substituir(raiz.sim, resto, novo), nao=raiz.nao)
    return Pergunta(texto=raiz.texto, sim=raiz.sim, nao=substituir(raiz.nao, resto, novo))


# --------------------------------------------------------------------------
# Aprendizado
# --------------------------------------------------------------------------


def criar_no(
    animal_errado: str,
    animal_novo: str,
    pergunta: str,
    resposta_do_novo: bool = True,
) -> Pergunta:
    """Monta o nó que separa o palpite errado do animal correto.

    ``resposta_do_novo`` indica qual ramo da nova pergunta corresponde ao
    animal novo (``True`` = sim, o caso usual).
    """
    novo = Folha(animal=animal_novo)
    antigo = Folha(animal=animal_errado)
    if resposta_do_novo:
        return Pergunta(texto=pergunta, sim=novo, nao=antigo)
    return Pergunta(texto=pergunta, sim=antigo, nao=novo)


def aprender(
    raiz: No,
    caminho: Caminho,
    animal_novo: str,
    pergunta: str,
    resposta_do_novo: bool = True,
) -> No:
    """Substitui a folha em ``caminho`` por uma nova pergunta discriminante."""
    folha = localizar(raiz, caminho)
    if not isinstance(folha, Folha):
        raise ValueError("o caminho informado não termina em uma folha")
    no = criar_no(folha.animal, animal_novo, pergunta, resposta_do_novo)
    return substituir(raiz, caminho, no)


# --------------------------------------------------------------------------
# Consultas auxiliares
# --------------------------------------------------------------------------


def _folhas(no: No) -> Iterator[Folha]:
    if isinstance(no, Folha):
        yield no
        return
    yield from _folhas(no.sim)
    yield from _folhas(no.nao)


def animais(no: No) -> list[str]:
    """Lista, em ordem de percurso, os animais conhecidos pela árvore."""
    return [folha.animal for folha in _folhas(no)]


def contar_animais(no: No) -> int:
    """Quantidade de animais na base de conhecimento."""
    return sum(1 for _ in _folhas(no))

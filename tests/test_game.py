"""Testes do laço de interação, com entrada e saída simuladas."""

from __future__ import annotations

from pathlib import Path

import pytest

from sardinha.game import (
    PERGUNTA_DE_ABERTURA,
    Jogo,
    criar_jogo,
    interpretar_sim_nao,
)
from sardinha.tree import Folha, No, Pergunta, animais, arvore_semente, carregar


class ConsoleFalso:
    """Substitui input()/print() guardando o roteiro e o que foi impresso."""

    def __init__(self, respostas: list[str]) -> None:
        self.respostas = list(respostas)
        self.perguntas: list[str] = []
        self.linhas: list[str] = []

    def entrada(self, texto: str) -> str:
        self.perguntas.append(texto)
        if not self.respostas:
            raise EOFError("roteiro esgotado")
        return self.respostas.pop(0)

    def saida(self, mensagem: str = "") -> None:
        self.linhas.append(mensagem)

    @property
    def impresso(self) -> str:
        return "\n".join(self.linhas)


def montar_jogo(respostas: list[str], arvore: No | None = None, base: Path | None = None):
    console = ConsoleFalso(respostas)
    jogo = Jogo(
        arvore=arvore if arvore is not None else arvore_semente(),
        entrada=console.entrada,
        saida=console.saida,
        caminho_arquivo=base if base is not None else Path("animais.json"),
    )
    return jogo, console


@pytest.mark.parametrize("texto", ["s", "S", "sim", " Sim ", "yes", "1", "sim!"])
def test_interpretar_sim(texto: str) -> None:
    assert interpretar_sim_nao(texto) is True


@pytest.mark.parametrize("texto", ["n", "N", "nao", "não", " NÃO ", "no", "0"])
def test_interpretar_nao(texto: str) -> None:
    assert interpretar_sim_nao(texto) is False


@pytest.mark.parametrize("texto", ["", "talvez", "quem sabe"])
def test_interpretar_resposta_desconhecida(texto: str) -> None:
    assert interpretar_sim_nao(texto) is None


def test_partida_comeca_perguntando_se_e_o_thor() -> None:
    jogo, console = montar_jogo(["n", "s", "s"])

    jogo.jogar_partida()

    assert PERGUNTA_DE_ABERTURA in console.perguntas[0]


def test_sim_para_o_thor_encerra_a_partida_sem_tocar_na_arvore() -> None:
    jogo, console = montar_jogo(["s"])

    assert jogo.jogar_partida() is True
    assert jogo.arvore == arvore_semente()
    assert "Thor" in console.impresso
    assert len(console.perguntas) == 1  # nenhuma pergunta da árvore foi feita


def test_palpite_certo_nao_altera_a_arvore() -> None:
    # é o Thor? não -> vive na água? sim -> baleia? sim
    jogo, console = montar_jogo(["n", "s", "s"])

    assert jogo.jogar_partida() is True
    assert jogo.arvore == arvore_semente()
    assert "Eu sabia" in console.impresso


def test_palpite_errado_insere_novo_no() -> None:
    jogo, _ = montar_jogo(["n", "n", "n", "gato", "ele mia?", "s"])

    assert jogo.jogar_partida() is False
    assert isinstance(jogo.arvore, Pergunta)
    assert jogo.arvore.nao == Pergunta("ele mia?", sim=Folha("gato"), nao=Folha("cachorro"))
    assert animais(jogo.arvore) == ["baleia", "gato", "cachorro"]


def test_resposta_invalida_e_reperguntada() -> None:
    jogo, console = montar_jogo(["n", "talvez", "s", "s"])

    assert jogo.jogar_partida() is True
    assert "Não entendi" in console.impresso


def test_animal_em_branco_e_reperguntado() -> None:
    jogo, console = montar_jogo(
        ["n", "n", "n", "   ", "ornitorrinco", "ele bota ovo?", "s"]
    )

    jogo.jogar_partida()

    assert "pelo menos uma letra" in console.impresso
    assert "ornitorrinco" in animais(jogo.arvore)


def test_sessao_salva_a_base_apos_a_partida(tmp_path: Path) -> None:
    base = tmp_path / "animais.json"
    jogo, _ = montar_jogo(["s", "n", "n", "n", "gato", "ele mia?", "s", "n"], base=base)

    jogo.executar()

    assert carregar(base) == jogo.arvore
    assert animais(carregar(base)) == ["baleia", "gato", "cachorro"]


def test_sessao_encerra_com_a_piada_creditando_o_thor(tmp_path: Path) -> None:
    jogo, console = montar_jogo(["n"], base=tmp_path / "animais.json")

    jogo.executar()

    assert "THOR" in console.impresso.upper()
    assert "10 PRINT" in console.impresso


def test_criar_jogo_carrega_a_semente_quando_nao_ha_arquivo(tmp_path: Path) -> None:
    jogo = criar_jogo(caminho_arquivo=tmp_path / "nao-existe.json")
    assert jogo.arvore == arvore_semente()

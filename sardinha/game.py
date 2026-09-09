"""Laço de interação do Jogo do Thor.

Toda a conversa com o jogador vive aqui. A lógica da base de conhecimento
fica em :mod:`sardinha.tree`; este módulo apenas pergunta, escuta e pede
ao modelo que aprenda.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from sardinha.tree import (
    CAMINHO_PADRAO,
    Folha,
    No,
    Pergunta,
    aprender,
    carregar,
    contar_animais,
    descer,
    salvar,
)

__all__ = [
    "Jogo",
    "PERGUNTA_DE_ABERTURA",
    "criar_jogo",
    "ler_do_terminal",
    "escrever_no_terminal",
    "AFIRMATIVAS",
    "NEGATIVAS",
    "PIADA_FINAL",
    "interpretar_sim_nao",
]

Entrada = Callable[[str], str]
Saida = Callable[[str], None]


def ler_do_terminal(prompt: str) -> str:
    """Entrada padrão do jogo (indireção para permitir substituição em testes)."""
    return input(prompt)


def escrever_no_terminal(mensagem: str = "") -> None:
    """Saída padrão do jogo (indireção para permitir substituição em testes)."""
    print(mensagem)

AFIRMATIVAS: frozenset[str] = frozenset({"s", "sim", "y", "yes", "1", "claro", "sim!"})
NEGATIVAS: frozenset[str] = frozenset({"n", "nao", "não", "no", "0", "nunca"})

PIADA_FINAL: str = (
    "10 PRINT \"O THOR ESCREVEU ESTE PROGRAMA\"\n"
    "20 PRINT \"E ATE HOJE NAO SABE SE O ORNITORRINCO VIVE NA AGUA\"\n"
    "30 GOTO 10\n"
    "READY."
)

PERGUNTA_DE_ABERTURA: str = "É o Thor?"
"""Pergunta fixa que abre toda partida, antes de percorrer a árvore.

Fica fora da árvore de decisão de propósito: assim ela é sempre a primeira
pergunta, qualquer que seja a base de conhecimento carregada do disco, e o
aprendizado do jogo nunca a desloca nem a apaga.
"""

RESPOSTA_THOR: str = "Claro que é o Thor. Ele vem antes de qualquer animal."

BANNER: str = (
    "*** JOGO DO THOR ***\n"
    "Pense em um animal. Eu tento adivinhar — e, quando erro, eu aprendo."
)


def interpretar_sim_nao(resposta: str) -> bool | None:
    """Traduz a resposta do jogador para ``True``/``False``.

    Devolve ``None`` quando a resposta não é reconhecida.
    """
    limpa = resposta.strip().lower().rstrip(".!?")
    if limpa in AFIRMATIVAS:
        return True
    if limpa in NEGATIVAS:
        return False
    return None


@dataclass
class Jogo:
    """Conduz uma sessão do jogo sobre uma árvore de decisão."""

    arvore: No
    entrada: Entrada = ler_do_terminal
    saida: Saida = escrever_no_terminal
    caminho_arquivo: Path = field(default=CAMINHO_PADRAO)

    # -- utilidades de conversa -------------------------------------------

    def dizer(self, mensagem: str = "") -> None:
        self.saida(mensagem)

    def perguntar_sim_nao(self, texto: str) -> bool:
        """Insiste até obter um sim ou um não compreensível."""
        while True:
            resposta = interpretar_sim_nao(self.entrada(f"{texto} (s/n) "))
            if resposta is not None:
                return resposta
            self.dizer("Não entendi. Responda com 's' para sim ou 'n' para não.")

    def perguntar_texto(self, texto: str) -> str:
        """Insiste até obter um texto não vazio."""
        while True:
            resposta = self.entrada(f"{texto} ").strip()
            if resposta:
                return resposta
            self.dizer("Preciso de uma resposta com pelo menos uma letra.")

    # -- partida -----------------------------------------------------------

    def jogar_partida(self) -> bool:
        """Joga uma partida e devolve ``True`` se o palpite estava certo.

        A partida começa sempre pela :data:`PERGUNTA_DE_ABERTURA`; só depois
        de um "não" o jogo desce a árvore. A árvore é atualizada quando o
        palpite erra.
        """
        if self.perguntar_sim_nao(PERGUNTA_DE_ABERTURA):
            self.dizer(RESPOSTA_THOR)
            return True

        caminho: list[bool] = []
        no = self.arvore
        while isinstance(no, Pergunta):
            resposta = self.perguntar_sim_nao(no.texto.capitalize())
            caminho.append(resposta)
            no = descer(no, resposta)

        assert isinstance(no, Folha)
        if self.perguntar_sim_nao(f"É um(a) {no.animal}?"):
            self.dizer("Eu sabia! Já vi um desses num programa em BASIC.")
            return True

        self.dizer("Errei. Me ensine, então.")
        self._aprender_com_o_jogador(caminho, no)
        return False

    def _aprender_com_o_jogador(self, caminho: list[bool], folha: Folha) -> None:
        """Coleta o animal correto e a pergunta que o distingue do palpite."""
        animal_novo = self.perguntar_texto("Em que animal você pensou?")
        pergunta = self.perguntar_texto(
            f"Qual pergunta de sim/não separa {animal_novo} de {folha.animal}?"
        )
        resposta_do_novo = self.perguntar_sim_nao(
            f"Para {animal_novo}, a resposta a essa pergunta é sim?"
        )
        self.arvore = aprender(
            self.arvore, caminho, animal_novo, pergunta, resposta_do_novo
        )
        self.dizer(f"Aprendido. Agora conheço {contar_animais(self.arvore)} animais.")

    # -- sessão ------------------------------------------------------------

    def executar(self) -> None:
        """Roda partidas enquanto o jogador quiser, salvando a cada uma."""
        self.dizer(BANNER)
        self.dizer()
        while True:
            if not self.perguntar_sim_nao("Você pensou em um animal?"):
                break
            self.jogar_partida()
            self.salvar_base()
            self.dizer()
            if not self.perguntar_sim_nao("Quer jogar de novo?"):
                break
        self.despedir()

    def salvar_base(self) -> None:
        """Persiste a árvore, avisando o jogador se a gravação falhar."""
        try:
            salvar(self.arvore, self.caminho_arquivo)
        except OSError as erro:
            self.dizer(f"(Não consegui salvar em {self.caminho_arquivo}: {erro})")

    def despedir(self) -> None:
        self.dizer()
        self.dizer(PIADA_FINAL)


def criar_jogo(
    caminho_arquivo: Path = CAMINHO_PADRAO,
    entrada: Entrada = ler_do_terminal,
    saida: Saida = escrever_no_terminal,
) -> Jogo:
    """Carrega a base de conhecimento do disco e monta um jogo pronto."""
    return Jogo(
        arvore=carregar(caminho_arquivo),
        entrada=entrada,
        saida=saida,
        caminho_arquivo=caminho_arquivo,
    )

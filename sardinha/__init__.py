"""Jogo do Thor: adivinhação de animais por árvore de decisão.

Reimplementação em Python do clássico ANIMAL, jogo escrito em BASIC nos
anos 1970 e popularizado em revistas e coletâneas de programas na década
de 1980. O programa faz perguntas de sim/não, arrisca um palpite e, ao
errar, aprende com o jogador.
"""

from __future__ import annotations

__version__ = "0.1.0"

from sardinha.tree import Folha, No, Pergunta, arvore_semente, carregar, salvar

__all__ = ["__version__", "Folha", "Pergunta", "No", "arvore_semente", "carregar", "salvar"]

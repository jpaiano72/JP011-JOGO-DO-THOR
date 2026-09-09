"""Entry point de linha de comando do Jogo do Thor."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from sardinha import __version__
from sardinha.game import criar_jogo
from sardinha.tree import CAMINHO_PADRAO, ArvoreInvalidaError

__all__ = ["main", "construir_parser"]


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sardinha",
        description="Jogo do Thor: eu adivinho o animal que você pensou — e aprendo quando erro.",
    )
    parser.add_argument(
        "-b",
        "--base",
        type=Path,
        default=CAMINHO_PADRAO,
        metavar="ARQUIVO",
        help=f"arquivo JSON da base de conhecimento (padrão: {CAMINHO_PADRAO})",
    )
    parser.add_argument("-V", "--version", action="version", version=f"sardinha {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o jogo. Devolve o código de saída do processo."""
    args = construir_parser().parse_args(argv)
    try:
        jogo = criar_jogo(caminho_arquivo=args.base)
    except ArvoreInvalidaError as erro:
        print(f"Base de conhecimento inválida: {erro}")
        return 1
    except OSError as erro:
        print(f"Não consegui ler {args.base}: {erro}")
        return 1

    try:
        jogo.executar()
    except (EOFError, KeyboardInterrupt):
        print()
        print("Interrompido. Salvando o que aprendi até aqui...")
        jogo.salvar_base()
        return 130
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

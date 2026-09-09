"""Testes do entry point de linha de comando."""

from __future__ import annotations

from pathlib import Path

import pytest

from sardinha.cli import main
from sardinha.tree import animais, carregar


def roteirizar(monkeypatch: pytest.MonkeyPatch, respostas: list[str]) -> None:
    fila = iter(respostas)

    def falso_input(_: str = "") -> str:
        try:
            return next(fila)
        except StopIteration:  # roteiro esgotado: equivale a fechar a entrada
            raise EOFError from None

    monkeypatch.setattr("builtins.input", falso_input)


def test_partida_completa_pela_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    base = tmp_path / "animais.json"
    roteirizar(monkeypatch, ["s", "n", "n", "gato", "ele mia?", "s", "n"])

    assert main(["--base", str(base)]) == 0

    assert animais(carregar(base)) == ["baleia", "gato", "cachorro"]
    assert "THOR" in capsys.readouterr().out.upper()


def test_base_invalida_encerra_com_erro(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    base = tmp_path / "animais.json"
    base.write_text("{isto não é json", encoding="utf-8")

    assert main(["--base", str(base)]) == 1
    assert "inválida" in capsys.readouterr().out


def test_interrupcao_salva_o_aprendizado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    base = tmp_path / "animais.json"
    # A entrada acaba logo após o aprendizado: o jogo recebe EOFError.
    roteirizar(monkeypatch, ["s", "n", "n", "gato", "ele mia?", "s"])

    assert main(["--base", str(base)]) == 130

    assert animais(carregar(base)) == ["baleia", "gato", "cachorro"]
    assert "Interrompido" in capsys.readouterr().out

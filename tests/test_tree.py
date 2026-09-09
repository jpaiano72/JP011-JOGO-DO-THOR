"""Testes do modelo da árvore e da sua persistência."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sardinha.tree import (
    ArvoreInvalidaError,
    Folha,
    No,
    Pergunta,
    animais,
    aprender,
    arvore_semente,
    carregar,
    contar_animais,
    criar_no,
    de_dict,
    descer,
    localizar,
    para_dict,
    salvar,
    substituir,
)


@pytest.fixture
def arvore_base() -> Pergunta:
    return Pergunta("vive na água?", sim=Folha("peixe"), nao=Folha("gato"))


# --------------------------------------------------------------------------
# Navegação
# --------------------------------------------------------------------------


def test_semente_e_vazia() -> None:
    assert arvore_semente() is None


def test_descer_escolhe_o_ramo_da_resposta(arvore_base: Pergunta) -> None:
    assert descer(arvore_base, True) == Folha("peixe")
    assert descer(arvore_base, False) == Folha("gato")


def test_localizar_percorre_caminho_de_respostas(arvore_base: Pergunta) -> None:
    assert localizar(arvore_base, []) is arvore_base
    assert localizar(arvore_base, [True]) == Folha("peixe")
    assert localizar(arvore_base, [False]) == Folha("gato")


def test_localizar_em_arvore_profunda() -> None:
    arvore = Pergunta(
        "voa?",
        sim=Pergunta("canta?", sim=Folha("sabiá"), nao=Folha("urubu")),
        nao=Folha("jacaré"),
    )
    assert localizar(arvore, [True, True]) == Folha("sabiá")
    assert localizar(arvore, [True, False]) == Folha("urubu")
    assert localizar(arvore, [False]) == Folha("jacaré")


def test_localizar_recusa_caminho_longo_demais(arvore_base: Pergunta) -> None:
    with pytest.raises(ValueError, match="caminho longo demais"):
        localizar(arvore_base, [True, True])


def test_animais_lista_as_folhas_em_ordem(arvore_base: Pergunta) -> None:
    assert animais(arvore_base) == ["peixe", "gato"]
    assert contar_animais(arvore_base) == 2


# --------------------------------------------------------------------------
# Inserção de nó novo
# --------------------------------------------------------------------------


def test_criar_no_coloca_animal_novo_no_ramo_sim() -> None:
    no = criar_no("peixe", "gato", "ele mia?", resposta_do_novo=True)
    assert no == Pergunta("ele mia?", sim=Folha("gato"), nao=Folha("peixe"))


def test_criar_no_respeita_resposta_invertida() -> None:
    no = criar_no("peixe", "gato", "ele nada?", resposta_do_novo=False)
    assert no == Pergunta("ele nada?", sim=Folha("peixe"), nao=Folha("gato"))


def test_aprender_substitui_a_folha_por_uma_pergunta(arvore_base: Pergunta) -> None:
    nova = aprender(arvore_base, [False], "tatu", "ele tem casco?")

    assert isinstance(nova, Pergunta)
    assert nova.nao == Pergunta("ele tem casco?", sim=Folha("tatu"), nao=Folha("gato"))
    assert nova.sim == Folha("peixe")
    assert animais(nova) == ["peixe", "tatu", "gato"]
    assert contar_animais(nova) == 3


def test_aprender_nao_modifica_a_arvore_original(arvore_base: Pergunta) -> None:
    aprender(arvore_base, [False], "tatu", "ele tem casco?")
    assert animais(arvore_base) == ["peixe", "gato"]


def test_aprender_duas_vezes_aprofunda_o_mesmo_ramo(arvore_base: Pergunta) -> None:
    arvore = aprender(arvore_base, [False], "tatu", "ele tem casco?")
    arvore = aprender(arvore, [False, False], "coelho", "ele pula?")

    assert animais(arvore) == ["peixe", "tatu", "coelho", "gato"]
    assert localizar(arvore, [False, False, True]) == Folha("coelho")
    assert localizar(arvore, [False, False, False]) == Folha("gato")


def test_aprender_recusa_caminho_que_nao_termina_em_folha(arvore_base: Pergunta) -> None:
    with pytest.raises(ValueError, match="não termina em uma folha"):
        aprender(arvore_base, [], "tatu", "ele tem casco?")


def test_substituir_com_caminho_vazio_troca_a_raiz(arvore_base: Pergunta) -> None:
    assert substituir(arvore_base, [], Folha("pardal")) == Folha("pardal")


# --------------------------------------------------------------------------
# Serialização JSON
# --------------------------------------------------------------------------


def test_round_trip_de_dict_preserva_a_arvore(arvore_base: Pergunta) -> None:
    arvore = aprender(arvore_base, [False], "tatu", "ele tem casco?")
    assert de_dict(para_dict(arvore)) == arvore


def test_round_trip_passando_por_json(arvore_base: Pergunta) -> None:
    arvore = aprender(arvore_base, [True], "tubarão", "ele tem barbatana dorsal?")
    texto = json.dumps(para_dict(arvore), ensure_ascii=False)
    assert de_dict(json.loads(texto)) == arvore


def test_round_trip_em_arquivo(tmp_path: Path, arvore_base: Pergunta) -> None:
    arquivo = tmp_path / "base" / "animais.json"
    arvore = aprender(arvore_base, [False], "tatu", "ele tem casco?")

    salvar(arvore, arquivo)

    assert arquivo.exists()
    assert carregar(arquivo) == arvore


def test_carregar_arquivo_inexistente_devolve_a_semente(tmp_path: Path) -> None:
    assert carregar(tmp_path / "nao-existe.json") == arvore_semente()


def test_carregar_json_quebrado_levanta_erro(tmp_path: Path) -> None:
    arquivo = tmp_path / "animais.json"
    arquivo.write_text("{isto não é json", encoding="utf-8")
    with pytest.raises(ArvoreInvalidaError):
        carregar(arquivo)


@pytest.mark.parametrize(
    "dados",
    [
        {"tipo": "bicho"},
        {"tipo": "folha"},
        {"tipo": "pergunta", "texto": "voa?"},
        {"tipo": "pergunta", "texto": "voa?", "sim": {"tipo": "folha", "animal": "urubu"}},
        "animal sem estrutura",
    ],
)
def test_de_dict_recusa_dados_malformados(dados: object) -> None:
    with pytest.raises(ArvoreInvalidaError):
        de_dict(dados)


def test_json_gravado_preserva_acentos(tmp_path: Path, arvore_base: Pergunta) -> None:
    arquivo = tmp_path / "animais.json"
    salvar(Pergunta("ele é ágil?", sim=arvore_base.sim, nao=arvore_base.nao), arquivo)
    assert "ágil" in arquivo.read_text(encoding="utf-8")

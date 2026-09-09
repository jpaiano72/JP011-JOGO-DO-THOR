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
def semente() -> No:
    return arvore_semente()


# --------------------------------------------------------------------------
# Navegação
# --------------------------------------------------------------------------


def test_semente_separa_baleia_de_cachorro(semente: No) -> None:
    assert isinstance(semente, Pergunta)
    assert semente.texto == "ele vive na água?"
    assert semente.sim == Folha("baleia")
    assert semente.nao == Folha("cachorro")


def test_descer_escolhe_o_ramo_da_resposta(semente: No) -> None:
    assert isinstance(semente, Pergunta)
    assert descer(semente, True) == Folha("baleia")
    assert descer(semente, False) == Folha("cachorro")


def test_localizar_percorre_caminho_de_respostas(semente: No) -> None:
    assert localizar(semente, []) is semente
    assert localizar(semente, [True]) == Folha("baleia")
    assert localizar(semente, [False]) == Folha("cachorro")


def test_localizar_em_arvore_profunda() -> None:
    arvore = Pergunta(
        "voa?",
        sim=Pergunta("canta?", sim=Folha("sabiá"), nao=Folha("urubu")),
        nao=Folha("jacaré"),
    )
    assert localizar(arvore, [True, True]) == Folha("sabiá")
    assert localizar(arvore, [True, False]) == Folha("urubu")
    assert localizar(arvore, [False]) == Folha("jacaré")


def test_localizar_recusa_caminho_longo_demais(semente: No) -> None:
    with pytest.raises(ValueError, match="caminho longo demais"):
        localizar(semente, [True, True])


def test_animais_lista_as_folhas_em_ordem(semente: No) -> None:
    assert animais(semente) == ["baleia", "cachorro"]
    assert contar_animais(semente) == 2


# --------------------------------------------------------------------------
# Inserção de nó novo
# --------------------------------------------------------------------------


def test_criar_no_coloca_animal_novo_no_ramo_sim() -> None:
    no = criar_no("cachorro", "gato", "ele mia?", resposta_do_novo=True)
    assert no == Pergunta("ele mia?", sim=Folha("gato"), nao=Folha("cachorro"))


def test_criar_no_respeita_resposta_invertida() -> None:
    no = criar_no("cachorro", "gato", "ele late?", resposta_do_novo=False)
    assert no == Pergunta("ele late?", sim=Folha("cachorro"), nao=Folha("gato"))


def test_aprender_substitui_a_folha_por_uma_pergunta(semente: No) -> None:
    nova = aprender(semente, [False], "gato", "ele mia?")

    assert isinstance(nova, Pergunta)
    assert nova.nao == Pergunta("ele mia?", sim=Folha("gato"), nao=Folha("cachorro"))
    assert nova.sim == Folha("baleia")
    assert animais(nova) == ["baleia", "gato", "cachorro"]
    assert contar_animais(nova) == 3


def test_aprender_nao_modifica_a_arvore_original(semente: No) -> None:
    aprender(semente, [False], "gato", "ele mia?")
    assert animais(semente) == ["baleia", "cachorro"]


def test_aprender_duas_vezes_aprofunda_o_mesmo_ramo(semente: No) -> None:
    arvore = aprender(semente, [False], "gato", "ele mia?")
    arvore = aprender(arvore, [False, False], "tatu", "ele tem casco?")

    assert animais(arvore) == ["baleia", "gato", "tatu", "cachorro"]
    assert localizar(arvore, [False, False, True]) == Folha("tatu")
    assert localizar(arvore, [False, False, False]) == Folha("cachorro")


def test_aprender_recusa_caminho_que_nao_termina_em_folha(semente: No) -> None:
    with pytest.raises(ValueError, match="não termina em uma folha"):
        aprender(semente, [], "gato", "ele mia?")


def test_substituir_com_caminho_vazio_troca_a_raiz(semente: No) -> None:
    assert substituir(semente, [], Folha("pardal")) == Folha("pardal")


# --------------------------------------------------------------------------
# Serialização JSON
# --------------------------------------------------------------------------


def test_round_trip_de_dict_preserva_a_arvore(semente: No) -> None:
    arvore = aprender(semente, [False], "gato", "ele mia?")
    assert de_dict(para_dict(arvore)) == arvore


def test_round_trip_passando_por_json(semente: No) -> None:
    arvore = aprender(semente, [True], "tubarão", "ele tem barbatana dorsal?")
    texto = json.dumps(para_dict(arvore), ensure_ascii=False)
    assert de_dict(json.loads(texto)) == arvore


def test_round_trip_em_arquivo(tmp_path: Path, semente: No) -> None:
    arquivo = tmp_path / "base" / "animais.json"
    arvore = aprender(semente, [False], "gato", "ele mia?")

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
        "cachorro",
    ],
)
def test_de_dict_recusa_dados_malformados(dados: object) -> None:
    with pytest.raises(ArvoreInvalidaError):
        de_dict(dados)


def test_json_gravado_preserva_acentos(tmp_path: Path, semente: No) -> None:
    arquivo = tmp_path / "animais.json"
    salvar(semente, arquivo)
    assert "água" in arquivo.read_text(encoding="utf-8")

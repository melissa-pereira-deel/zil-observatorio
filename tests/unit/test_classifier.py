"""Unit tests for the ZIL keyword classifier."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.classifiers import (  # noqa: E402
    classificar_texto,
    classificar_texto_com_evidencia,
    classificar_votacao,
    classificar_proposicao,
    relevancia_score,
)


# ── classificar_texto ──

def test_classificar_texto_vazio():
    assert classificar_texto("") == []


def test_classificar_texto_sem_termos_zil():
    assert classificar_texto("Projeto de lei sobre assistência social") == []


def test_classificar_texto_fertilizantes():
    result = classificar_texto("Regulamenta importação de fertilizantes nitrogenados")
    assert "ZIL-FER" in result


def test_classificar_texto_minerais():
    result = classificar_texto("Dispõe sobre extração de lítio e minerais estratégicos")
    assert "ZIL-MIN" in result


def test_classificar_texto_multiplas_categorias():
    result = classificar_texto("Política de semicondutores e energia renovável para soberania industrial")
    assert len(result) >= 2


# ── classificar_votacao ──

def test_classificar_votacao_com_termo_zil_fer():
    result = classificar_votacao("PL 1234 - Fertilizantes nacionais")
    assert "ZIL-FER" in result


def test_classificar_votacao_sem_termos_zil():
    result = classificar_votacao("Requerimento de urgência para projeto educacional")
    assert result == []


def test_classificar_votacao_none_seguro():
    result = classificar_votacao(None)
    assert result == []


# ── classificar_proposicao ──

def test_classificar_proposicao_via_ementa():
    result = classificar_proposicao(ementa="Institui política nacional de semicondutores")
    assert "ZIL-SEM" in result


def test_classificar_proposicao_multiplas_categorias():
    result = classificar_proposicao(
        ementa="Fundo para energia renovável e defesa industrial nacional",
    )
    assert len(result) >= 1


def test_classificar_proposicao_sem_termos():
    result = classificar_proposicao(ementa="Denomina rodovia estadual")
    assert result == []


# ── relevancia_score ──

def test_relevancia_score_sem_termos():
    score = relevancia_score("Homenagem ao patrono da cidade")
    assert score == 0.0


def test_relevancia_score_com_termos():
    score = relevancia_score("Política nacional de semicondutores e circuitos integrados")
    assert score > 0.0
    assert score <= 1.0


def test_relevancia_score_range():
    score = relevancia_score("lítio fertilizantes semicondutores energia renovável soberania industrial")
    assert 0.0 <= score <= 1.0


# ── classificar_texto_com_evidencia ──
#
# Mesma classificação de `classificar_texto`, mais a procedência. Existe porque
# a seleção editorial precisa distinguir "casou com `minerais críticos`" de
# "casou com `técnico`", e a lista de códigos sozinha não diz isso.

def test_evidencia_nomeia_a_keyword_que_casou():
    ev = classificar_texto_com_evidencia(
        "Institui a Política Nacional de Minerais Críticos e Estratégicos"
    )
    assert "ZIL-MIN" in ev
    assert "minerais críticos" in ev["ZIL-MIN"]


def test_evidencia_expoe_casamento_por_palavra_comum():
    """O falso positivo real: cargos do Judiciário entrando em ZIL-EDU."""
    ev = classificar_texto_com_evidencia(
        "Transforma cargos vagos da carreira de Técnico Judiciário"
    )
    assert ev.get("ZIL-EDU") == ["técnico"]


def test_evidencia_concorda_com_classificar_texto():
    texto = "Projeto sobre semicondutores, nióbio e fertilizantes"
    assert sorted(classificar_texto_com_evidencia(texto)) == sorted(classificar_texto(texto))


def test_evidencia_de_texto_vazio_e_dicionario_vazio():
    assert classificar_texto_com_evidencia("") == {}
    assert classificar_texto_com_evidencia("Denomina rodovia estadual") == {}

"""T015 — Unit tests for apps/api/lib/situacao.py (situacao helper)."""

import sys

sys.path.insert(0, "apps/api")

import pytest

from lib.situacao import get_cods_for_grupo, get_situacao_grupo


# ── get_situacao_grupo ──


def test_tramitando():
    assert get_situacao_grupo(903) == "tramitando"


def test_aprovada():
    assert get_situacao_grupo(1140) == "aprovada"


def test_arquivada():
    assert get_situacao_grupo(923) == "arquivada"


def test_unknown_code_returns_outras():
    assert get_situacao_grupo(9999) == "outras"


def test_none_returns_outras():
    assert get_situacao_grupo(None) == "outras"


def test_zero_returns_outras():
    assert get_situacao_grupo(0) == "outras"


# ── get_cods_for_grupo ──


def test_tramitando_cods_non_empty():
    cods = get_cods_for_grupo("tramitando")
    assert isinstance(cods, set)
    assert len(cods) > 0


def test_outras_returns_empty_set():
    assert get_cods_for_grupo("outras") == set()


def test_invalid_grupo_raises_value_error():
    with pytest.raises(ValueError, match="situacao_grupo invalido"):
        get_cods_for_grupo("invalid")

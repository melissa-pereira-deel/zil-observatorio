"""T049 — Unit tests for apps/api/lib/relacoes.py (tipo_relacao classifier)."""

import sys

sys.path.insert(0, "apps/api")

from lib.relacoes import classificar_tipo_relacao


def test_emenda():
    assert classificar_tipo_relacao("EMC") == "emenda"


def test_substitutivo():
    assert classificar_tipo_relacao("SBT") == "substitutivo"


def test_parecer():
    assert classificar_tipo_relacao("PAR") == "parecer"


def test_apensada():
    assert classificar_tipo_relacao("PL") == "apensada"


def test_unknown_sigla_returns_outro():
    assert classificar_tipo_relacao("XYZ") == "outro"


def test_empty_string_returns_outro():
    assert classificar_tipo_relacao("") == "outro"


def test_case_insensitive():
    assert classificar_tipo_relacao("emc") == "emenda"

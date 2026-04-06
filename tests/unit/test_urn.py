"""T022 — Unit tests for apps/api/lib/urn.py (URN-to-URL parser)."""

import sys

sys.path.insert(0, "apps/api")

from lib.urn import parse_urn_to_url


def test_lei_ordinaria():
    result = parse_urn_to_url("urn:lex:br:federal:lei:2021-07-14;14182")
    assert result == "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/L14182.htm"


def test_lei_complementar():
    result = parse_urn_to_url("urn:lex:br:federal:lei.complementar:2003-01-10;116")
    assert result == "https://www.planalto.gov.br/ccivil_03/_ato2003-2006/2003/lcp/Lcp116.htm"


def test_none_returns_none():
    assert parse_urn_to_url(None) is None


def test_invalid_string_returns_none():
    assert parse_urn_to_url("invalid") is None


def test_empty_string_returns_none():
    assert parse_urn_to_url("") is None

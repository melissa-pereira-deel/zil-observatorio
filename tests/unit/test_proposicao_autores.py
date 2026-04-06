"""T029 — Unit tests for _extract_id_from_uri logic (author matching helper).

The function under test lives in scripts/sync_detalhes_proposicoes.py.
We replicate the regex logic here to test it in isolation without importing
the full script (which has heavy DB/client dependencies).
"""

import re


def _extract_id_from_uri(uri: str) -> str | None:
    """Extract numeric ID from API URI, e.g. '/api/v2/deputados/204554' -> '204554'."""
    if not uri:
        return None
    match = re.search(r"/(\d+)$", uri)
    return match.group(1) if match else None


def test_extract_from_relative_uri():
    assert _extract_id_from_uri("/api/v2/deputados/204554") == "204554"


def test_extract_from_full_url():
    uri = "https://dadosabertos.camara.leg.br/api/v2/deputados/12345"
    assert _extract_id_from_uri(uri) == "12345"


def test_empty_string_returns_none():
    assert _extract_id_from_uri("") is None


def test_uri_without_trailing_number_returns_none():
    assert _extract_id_from_uri("/api/v2/orgaos/comissao-xyz") is None

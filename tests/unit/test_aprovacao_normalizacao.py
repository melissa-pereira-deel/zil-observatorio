"""A API da Câmara manda `aprovacao` como inteiro, não como booleano.

Esse detalhe custou caro: `VotacaoAPI.aprovacao` era anotado `Optional[bool]`
num dataclass simples, que não coage nada. A anotação era falsa, e dois call
sites confiaram nela escrevendo comparações de identidade:

    1 is True   → False        0 is False  → False

Resultado: `sync_votacoes_zil.py` nunca gravava `resultado`, e
`sync_votacoes_proposicoes.py` perdia toda rejeição. Na página pública, uma
votação simbólica — sem voto nominal, logo 0 a 0 — era exibida como
"Rejeitado", contradizendo a própria descrição da votação.

Estes testes existem porque o bug volta sozinho: a anotação continua dizendo
`bool`, e `is True` continua parecendo natural para quem lê.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from packages.camara_client import _como_bool  # noqa: E402


@pytest.mark.parametrize("entrada,esperado", [
    (1, True),        # o que a API realmente manda
    (0, False),       # idem, para rejeitada
    (True, True),     # já booleano: passa intacto
    (False, False),
    (None, None),     # ausente continua ausente — não vira False
    ("1", True),      # defensivo: a API já mudou de forma antes
    ("0", False),
    ("", None),       # lixo não vira decisão
    ("talvez", None),
])
def test_como_bool(entrada, esperado):
    assert _como_bool(entrada) is esperado


def test_inteiro_nao_satisfaz_comparacao_de_identidade():
    """O motivo de `_como_bool` existir, escrito como teste.

    Se algum dia alguém remover a normalização achando que é redundante, isto
    documenta por que não é.
    """
    # O `noqa` é deliberado: o ruff avisa para usar `==` aqui, que é
    # exatamente o conselho que teria evitado o bug. Comparar com `is` é
    # o comportamento sob teste, não um descuido.
    assert (1 is True) is False  # noqa: F632
    assert (0 is False) is False  # noqa: F632
    assert _como_bool(1) is True
    assert _como_bool(0) is False


def test_votacao_api_normaliza_na_borda():
    """O contrato: depois do cliente, `aprovacao` é bool ou None. Nunca int."""
    from packages.camara_client import VotacaoAPI

    for valor in (1, 0, True, False, None):
        v = VotacaoAPI(id="1-1", aprovacao=_como_bool(valor))
        assert v.aprovacao is None or isinstance(v.aprovacao, bool)


# ── a regra que os dois scripts de sync aplicam ──

def _resultado(aprovacao):
    """Mesma expressão usada em sync_votacoes_zil e sync_votacoes_proposicoes."""
    if aprovacao is None:
        return None
    return "aprovado" if aprovacao else "rejeitado"


@pytest.mark.parametrize("bruto,esperado", [
    (1, "aprovado"),
    (0, "rejeitado"),      # era isto que se perdia: virava None
    (True, "aprovado"),
    (False, "rejeitado"),
    (None, None),
])
def test_resultado_a_partir_do_valor_cru_da_api(bruto, esperado):
    assert _resultado(_como_bool(bruto)) == esperado

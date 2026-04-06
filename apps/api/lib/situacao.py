"""Situacao helper — maps codSituacao to UI groups (Research Decision 6).

97 distinct API codes → 4 citizen-friendly groups.
"""

from typing import Optional


# ── Group: tramitando (active bills) ──
_TRAMITANDO = {
    903,   # Em tramitação
    924,   # Em tramitação no Senado
    925,   # Aguardando sanção presidencial
    1360,  # Pronta para pauta
    910,   # Aguardando Deliberação
    911,   # Aguardando Designação de Relator
    912,   # Aguardando parecer
    913,   # Aguardando Apreciação pelo Senado Federal
    914,   # Aguardando Retorno
    916,   # Aguardando Apreciação
    917,   # Aguardando Criação de Comissão Temporária
    1049,  # Aguardando Parecer do Relator
    1250,  # Em tramitação conjunta
}

# ── Group: aprovada (became law) ──
_APROVADA = {
    1140,  # Transformado em Norma Jurídica
}

# ── Group: arquivada (terminal / dead) ──
_ARQUIVADA = {
    923,   # Arquivada
    937,   # Devolvida ao autor
    950,   # Vetada totalmente
    1222,  # Declarada prejudicada
    906,   # Rejeitada
    907,   # Retirada pelo autor
    1063,  # Devolvida ao Senado Federal
    1251,  # Mesa diretora arquivou
    1252,  # Fim legislatura — arquivada
    1253,  # Legislatura encerrada
    1393,  # Vetada parcialmente
}

SITUACAO_GRUPOS = {
    "tramitando": _TRAMITANDO,
    "aprovada": _APROVADA,
    "arquivada": _ARQUIVADA,
}

# Reverse lookup: codSituacao → grupo
_COD_TO_GRUPO: dict[int, str] = {}
for grupo, cods in SITUACAO_GRUPOS.items():
    for cod in cods:
        _COD_TO_GRUPO[cod] = grupo

VALID_GRUPOS = {"tramitando", "aprovada", "arquivada", "outras"}


def get_situacao_grupo(cod: Optional[int]) -> str:
    """Map a codSituacao integer to a UI group name.

    Returns one of: tramitando, aprovada, arquivada, outras.
    Returns 'outras' for None, 0, or unrecognized codes.
    """
    if cod is None or cod == 0:
        return "outras"
    return _COD_TO_GRUPO.get(cod, "outras")


def get_cods_for_grupo(grupo: str) -> set[int]:
    """Return the set of codSituacao values for a given UI group.

    For 'outras', returns an empty set (filter logic should use NOT IN).
    Raises ValueError for invalid group names.
    """
    if grupo not in VALID_GRUPOS:
        raise ValueError(
            f"situacao_grupo invalido: '{grupo}'. "
            f"Use: {', '.join(sorted(VALID_GRUPOS))}"
        )
    if grupo == "outras":
        return set()  # handled via NOT IN logic
    return SITUACAO_GRUPOS[grupo]

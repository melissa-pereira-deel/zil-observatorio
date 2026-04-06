"""Tipo relacao classifier — maps API siglaTipo to tipo_relacao (Research Decision 4).

Classification map converts ~20 API type codes into 9 semantic categories.
"""


# siglaTipo → tipo_relacao
_CLASSIFICATION_MAP: dict[str, str] = {
    # Emendas (amendments)
    "EMC": "emenda",
    "EMP": "emenda",
    "EMS": "emenda",
    "EMA": "emenda",
    "EMR": "emenda",
    # Substitutivo
    "SBT": "substitutivo",
    # Pareceres (committee reports)
    "PAR": "parecer",
    "PRL": "parecer",
    "PPP": "parecer",
    "PRLP": "parecer",
    # Redacao final
    "RDF": "redacao_final",
    # Destaque
    "DTQ": "destaque",
    # Requerimentos (procedural requests)
    "REQ": "requerimento",
    "RPDR": "requerimento",
    # Voto separado
    "VTS": "voto_separado",
    # Apensadas (appended propositions)
    "PL": "apensada",
    "PEC": "apensada",
    "PLP": "apensada",
    "MPV": "apensada",
    "PDL": "apensada",
}

VALID_TIPOS_RELACAO = {
    "emenda",
    "substitutivo",
    "parecer",
    "redacao_final",
    "destaque",
    "requerimento",
    "voto_separado",
    "apensada",
    "outro",
}

# Portuguese labels for display
TIPO_RELACAO_LABELS: dict[str, str] = {
    "emenda": "Emendas",
    "substitutivo": "Substitutivos",
    "parecer": "Pareceres",
    "redacao_final": "Redacao Final",
    "destaque": "Destaques",
    "requerimento": "Requerimentos",
    "voto_separado": "Votos em Separado",
    "apensada": "Apensadas",
    "outro": "Outros",
}


def classificar_tipo_relacao(sigla_tipo: str) -> str:
    """Map an API siglaTipo to a semantic tipo_relacao category.

    Args:
        sigla_tipo: The siglaTipo string from the Camara API (e.g. "EMC", "PL", "SBT")

    Returns:
        One of the 9 tipo_relacao values. Defaults to "outro" for unrecognized types.
    """
    if not sigla_tipo:
        return "outro"
    return _CLASSIFICATION_MAP.get(sigla_tipo.strip().upper(), "outro")

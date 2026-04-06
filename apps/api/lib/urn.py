"""URN-to-URL converter — parses LexML URN to Planalto URL (Research Decision 5).

Pattern: urn:lex:br:federal:{tipo}:{date};{number}
  → https://www.planalto.gov.br/ccivil_03/_ato{range}/{year}/{prefix}{number}.htm
"""

import re
from typing import Optional


# Match: urn:lex:br:federal:{tipo}:{YYYY-MM-DD};{number}
_URN_PATTERN = re.compile(
    r"^urn:lex:br:federal:"
    r"(?P<tipo>[a-z.]+):"
    r"(?P<year>\d{4})-\d{2}-\d{2};"
    r"(?P<number>\d+)$"
)

# Year ranges used in Planalto URL structure
_YEAR_RANGES = [
    (2023, 2026, "2023-2026"),
    (2019, 2022, "2019-2022"),
    (2015, 2018, "2015-2018"),
    (2011, 2014, "2011-2014"),
    (2007, 2010, "2007-2010"),
    (2003, 2006, "2003-2006"),
    (1999, 2002, "1999-2002"),
    (1995, 1998, "1995-1998"),
    (1990, 1994, "1990-1994"),
]

# Tipo → (URL path segment, number prefix)
_TIPO_MAP = {
    "lei": ("lei", "L"),
    "lei.complementar": ("lcp", "Lcp"),
    "medida.provisoria": ("mpv", "mpv"),
    "decreto": ("decreto", "D"),
    "decreto.lei": ("del", "Del"),
}


def _get_year_range(year: int) -> Optional[str]:
    """Get Planalto URL year range string for a given year."""
    for start, end, range_str in _YEAR_RANGES:
        if start <= year <= end:
            return range_str
    return None


def parse_urn_to_url(urn: Optional[str]) -> Optional[str]:
    """Parse a LexML URN and construct the corresponding Planalto URL.

    Args:
        urn: LexML URN string, e.g. "urn:lex:br:federal:lei:2021-07-14;14182"

    Returns:
        Planalto URL string, or None if URN format is unrecognized.

    Examples:
        >>> parse_urn_to_url("urn:lex:br:federal:lei:2021-07-14;14182")
        'https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/L14182.htm'
        >>> parse_urn_to_url("urn:lex:br:federal:lei.complementar:2003-01-10;116")
        'https://www.planalto.gov.br/ccivil_03/_ato2003-2006/2003/lcp/Lcp116.htm'
        >>> parse_urn_to_url(None)
        >>> parse_urn_to_url("invalid")
    """
    if not urn:
        return None

    match = _URN_PATTERN.match(urn)
    if not match:
        return None

    tipo = match.group("tipo")
    year = int(match.group("year"))
    number = match.group("number")

    tipo_info = _TIPO_MAP.get(tipo)
    if not tipo_info:
        return None

    path_segment, prefix = tipo_info

    year_range = _get_year_range(year)
    if not year_range:
        return None

    return (
        f"https://www.planalto.gov.br/ccivil_03/"
        f"_ato{year_range}/{year}/{path_segment}/{prefix}{number}.htm"
    )

"""Classificador baseline de proposições/votações por pauta ZIL.

Usa matching de palavras-chave contra a taxonomia definida em YAML.
Este é o classificador da Camada 1 (automático). As camadas 2 (NLP)
e 3 (curadoria humana) serão adicionadas posteriormente.
"""

import re
import logging
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Carregar taxonomia
TAXONOMIA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "taxonomia" / "categorias.yml"


def _load_taxonomia() -> list[dict]:
    """Carrega a taxonomia de pautas ZIL do YAML."""
    if not TAXONOMIA_PATH.exists():
        logger.warning(f"Taxonomia não encontrada em {TAXONOMIA_PATH}, usando fallback")
        return _fallback_taxonomia()

    with open(TAXONOMIA_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("categorias", [])


def _fallback_taxonomia() -> list[dict]:
    """Taxonomia embutida como fallback."""
    return [
        {"codigo": "ZIL-FER", "keywords": ["fertilizante", "fertilizantes", "potássio", "fosfato", "NPK", "Embrapa", "PNF", "Autazes"]},
        {"codigo": "ZIL-MIN", "keywords": ["nióbio", "terras raras", "lítio", "grafite", "mineral crítico", "minerais estratégicos", "CBMM"]},
        {"codigo": "ZIL-SEM", "keywords": ["semicondutor", "semicondutores", "chip", "chips", "microeletrônica", "Padis", "Brasil Semicon"]},
        {"codigo": "ZIL-ENE", "keywords": ["pré-sal", "hidrogênio verde", "bateria", "Petrobras", "etanol", "fundo soberano", "renovável"], "keywords_fracas": ["bateria", "renovável"]},
        {"codigo": "ZIL-DIG", "keywords": ["Starlink", "dados pessoais", "LGPD", "satélite", "fibra óptica", "soberania digital"], "keywords_fracas": ["dados pessoais", "LGPD", "satélite"]},
        {"codigo": "ZIL-DEF", "keywords": ["Embraer", "defesa cibernética", "ativo estratégico", "privatização", "segurança nacional"], "keywords_fracas": ["privatização", "segurança nacional"]},
        {"codigo": "ZIL-EDU", "keywords": ["engenharia", "STEM", "ITA", "Ceitec", "repatriação", "formação técnica", "pesquisa"], "keywords_fracas": ["engenharia", "pesquisa"]},
        {"codigo": "ZIL-AGR", "keywords": ["agroindústria", "valor agregado", "agro processamento", "industrialização rural"]},
        {"codigo": "ZIL-COM", "keywords": ["tarifa", "OMC", "Mercosul", "BRICS", "acordo bilateral", "reciprocidade"], "keywords_fracas": ["tarifa", "Mercosul"]},
    ]


# Nome oficial de lei entre parênteses — "(Lei Geral de Proteção de Dados
# Pessoais)", "(Código Penal)". A ementa cita essas leis para dizer QUAIS ela
# altera; o tema do projeto está fora dos parênteses.
#
# Sem isto, o PL 996/2015 — homicídio qualificado contra membros do MP e da
# Magistratura — era classificado como soberania digital, porque casava
# `dados pessoais` dentro do nome de uma das leis que ele altera.
_CITACAO_DE_LEI = re.compile(
    r"\(\s*(?:lei|código|codigo|decreto|estatuto|marco)\b[^)]*\)",
    re.IGNORECASE,
)


def sem_citacoes_de_lei(texto: str) -> str:
    """Remove os nomes de lei entre parênteses, preservando o resto."""
    return _CITACAO_DE_LEI.sub(" ", texto or "")


# Compilar patterns uma vez
_taxonomia = _load_taxonomia()

# Guarda a keyword ao lado do pattern: sem isso não dá para dizer *por que* um
# texto caiu numa categoria, e a diferença entre casar por `minerais críticos` e
# casar por `técnico` é o que separa uma candidata boa de ruído.
_patterns_com_keyword: dict[str, list[tuple[str, re.Pattern]]] = {}

for cat in _taxonomia:
    codigo = cat["codigo"]
    keywords = cat.get("keywords", [])
    _patterns_com_keyword[codigo] = [
        (kw, re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE))
        for kw in keywords
    ]

_patterns: dict[str, list[re.Pattern]] = {
    codigo: [p for _kw, p in pares]
    for codigo, pares in _patterns_com_keyword.items()
}

# Keywords que não sustentam sozinhas a categoria. Ver o cabeçalho de
# data/taxonomia/categorias.yml para a evidência por trás de cada uma.
KEYWORDS_FRACAS: dict[str, frozenset[str]] = {
    cat["codigo"]: frozenset(k.lower() for k in (cat.get("keywords_fracas") or []))
    for cat in _taxonomia
}


def _e_fraca(codigo: str, keyword: str) -> bool:
    return keyword.lower() in KEYWORDS_FRACAS.get(codigo, frozenset())


def classificar_texto(texto: str) -> list[str]:
    """Classifica um texto nas categorias ZIL.

    Exige **pelo menos uma keyword forte**: uma que não esteja em
    `keywords_fracas` e que não apareça apenas dentro do nome de uma lei citada.
    Palavra comum sozinha não classifica — `técnico` casa com "Técnico
    Judiciário", `tarifa` com "Tarifa Social de Água e Esgoto".

    A regra antiga era "1 keyword qualquer basta". Numa varredura de 2024 a 2026
    isso enchia ZIL-EDU e ZIL-DIG de projetos sem relação com soberania
    industrial, enquanto ZIL-SEM — semicondutores, das pautas mais centrais —
    ficava com cinco.

    Args:
        texto: Texto a classificar (ementa, descrição de votação, etc.)

    Returns:
        Lista de códigos ZIL encontrados (ex: ["ZIL-FER", "ZIL-MIN"])
    """
    return list(classificar_texto_com_evidencia(texto, apenas_fortes=True))


def classificar_texto_com_evidencia(
    texto: str, *, apenas_fortes: bool = False
) -> dict[str, list[str]]:
    """Como `classificar_texto`, mas diz quais keywords casaram em cada categoria.

    Existe porque a seleção editorial precisa distinguir um casamento específico
    (`minerais críticos`) de um casamento por palavra comum (`técnico`, que casa
    com "Técnico Judiciário"). Sem a evidência, as duas são indistinguíveis.

    Args:
        texto: o que classificar.
        apenas_fortes: quando True, devolve só as categorias que têm ao menos
            uma keyword forte — é a regra que `classificar_texto` aplica. O
            padrão False devolve **todos** os casamentos, inclusive os fracos,
            para quem precisa exibir o motivo de uma candidata estar na lista.

    Returns:
        {"ZIL-MIN": ["nióbio", "minerais críticos"]} — a lista traz as keywords
        como casaram no texto original, mesmo com `apenas_fortes=True`.
    """
    if not texto:
        return {}

    # Segunda passada sem os nomes de lei citados: o que só casa lá casou com a
    # lista de leis alteradas, não com o assunto do projeto.
    texto_limpo = sem_citacoes_de_lei(texto)

    encontradas: dict[str, list[str]] = {}
    for codigo, pares in _patterns_com_keyword.items():
        kws = [kw for kw, p in pares if p.search(texto)]
        if not kws:
            continue
        if apenas_fortes:
            fortes = [
                kw
                for kw, p in pares
                if kw in kws and not _e_fraca(codigo, kw) and p.search(texto_limpo)
            ]
            if not fortes:
                continue
        encontradas[codigo] = kws

    return encontradas


def classificar_proposicao(
    ementa: Optional[str] = None,
    ementa_detalhada: Optional[str] = None,
    indexacao: Optional[str] = None,
) -> list[str]:
    """Classifica uma proposição combinando todos os campos textuais.

    Combina ementa, ementa detalhada e indexação para maximizar cobertura.
    """
    partes = [p for p in [ementa, ementa_detalhada, indexacao] if p]
    texto_completo = " ".join(partes)
    return classificar_texto(texto_completo)


def classificar_votacao(descricao: Optional[str] = None) -> list[str]:
    """Classifica uma votação pela sua descrição."""
    return classificar_texto(descricao or "")


def relevancia_score(texto: str, categorias: Optional[list[str]] = None) -> float:
    """Calcula score de relevância (0.0 a 1.0) baseado em densidade de keywords.

    Útil para ranking de proposições por relevância dentro de uma categoria.
    Se `categorias` for None, verifica contra todas as categorias ZIL.
    """
    if not texto:
        return 0.0
    if categorias is None:
        categorias = list(_patterns.keys())
    if not categorias:
        return 0.0

    total_matches = 0
    total_keywords = 0

    for codigo in categorias:
        patterns = _patterns.get(codigo, [])
        total_keywords += len(patterns)
        total_matches += sum(1 for p in patterns if p.search(texto))

    if total_keywords == 0:
        return 0.0

    return min(1.0, total_matches / max(total_keywords * 0.3, 1))

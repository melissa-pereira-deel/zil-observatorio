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
TAXONOMIA_PATH = Path(__file__).parent.parent.parent / "data" / "taxonomia" / "categorias.yml"


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
        {"codigo": "ZIL-ENE", "keywords": ["pré-sal", "hidrogênio verde", "bateria", "Petrobras", "etanol", "fundo soberano", "renovável"]},
        {"codigo": "ZIL-DIG", "keywords": ["Starlink", "dados pessoais", "LGPD", "satélite", "fibra óptica", "soberania digital"]},
        {"codigo": "ZIL-DEF", "keywords": ["Embraer", "defesa cibernética", "ativo estratégico", "privatização", "segurança nacional"]},
        {"codigo": "ZIL-EDU", "keywords": ["engenharia", "STEM", "ITA", "Ceitec", "repatriação", "formação técnica", "pesquisa"]},
        {"codigo": "ZIL-AGR", "keywords": ["agroindústria", "valor agregado", "agro processamento", "industrialização rural"]},
        {"codigo": "ZIL-COM", "keywords": ["tarifa", "OMC", "Mercosul", "BRICS", "acordo bilateral", "reciprocidade"]},
    ]


# Compilar patterns uma vez
_taxonomia = _load_taxonomia()
_patterns: dict[str, list[re.Pattern]] = {}

for cat in _taxonomia:
    codigo = cat["codigo"]
    keywords = cat.get("keywords", [])
    _patterns[codigo] = [
        re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
        for kw in keywords
    ]


def classificar_texto(texto: str) -> list[str]:
    """Classifica um texto nas categorias ZIL.

    Args:
        texto: Texto a classificar (ementa, descrição de votação, etc.)

    Returns:
        Lista de códigos ZIL encontrados (ex: ["ZIL-FER", "ZIL-MIN"])
    """
    if not texto:
        return []

    categorias = []
    for codigo, patterns in _patterns.items():
        matches = sum(1 for p in patterns if p.search(texto))
        if matches >= 1:  # pelo menos 1 keyword encontrada
            categorias.append(codigo)

    return categorias


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

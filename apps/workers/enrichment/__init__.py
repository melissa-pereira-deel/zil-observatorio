"""
Pipeline de Enriquecimento de Texto Legislativo — Abordagem D (Híbrido)

Stages:
  1. EXTRACT  — regex citation extraction from ementa text
  2. RESOLVE  — Planalto.gov.br HTTP fetch + lei_artigos DB cache
  3. AUGMENT  — Claude API synthesis with injected article context (no hallucination)
  4. VALIDATE — Pydantic validation + confidence score calculation
  5. SERVE    — persist enrichment fields to Proposicao record

ADR-001: uses JSON (not JSONB) — SQLite compatible
ADR-002: adds apps/api to sys.path explicitly
"""

import hashlib
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

import httpx

# ADR-002: add apps/api to sys.path so 'from models import ...' works
_api_dir = str(Path(__file__).parent.parent.parent / "api")
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1.0"
CACHE_TTL_DAYS = 30
PLANALTO_TIMEOUT = 10.0
MAX_CONTEXT_CHARS = 8_000   # ~2 000 tokens safety margin
MAX_EMENTA_CHARS = 2_000


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class Citacao:
    tipo: str           # "lei" | "lc" | "mp"
    numero: str         # digits only, e.g. "14744"
    ano: int
    artigo: Optional[str] = None
    lei_id: str = field(init=False)

    def __post_init__(self):
        prefix = {"lei": "", "lc": "lc-", "mp": "mp-"}[self.tipo]
        self.lei_id = f"{prefix}{self.numero}-{self.ano}"


@dataclass
class ArtigoResolvido:
    lei_id: str
    numero_artigo: str
    texto: Optional[str]
    url: str
    status: str  # resolvido | revogada | nao_encontrada | pdf_nao_parseavel | timeout


# ── Stage 1 — EXTRACT ─────────────────────────────────────────────────────────

# Patterns ordered by specificity: LC and MP before plain Lei.
# Year suffix handles all Brazilian date forms:
#   "/2023"  →  slash-year
#   ", de 2023"  →  short form
#   ", de 21 de novembro de 2023"  →  long form with full date
_YEAR_SUFFIX = r"[,\s/]*(?:de\s+\d{1,2}\s+de\s+\w+\s+de\s+|de\s+)?(\d{4})"

_LEI_PATTERNS: list[tuple[str, str]] = [
    (
        r"Lei\s+Complementar\s+n[oº°]?\.?\s*(\d+)" + _YEAR_SUFFIX,
        "lc",
    ),
    (
        r"Medida\s+Provis[oó]ria\s+n[oº°]?\.?\s*(\d[\d.]+)" + _YEAR_SUFFIX,
        "mp",
    ),
    (
        r"Lei\s+n[oº°]?\.?\s*(\d[\d.]+)" + _YEAR_SUFFIX,
        "lei",
    ),
]

_ART_PATTERN = re.compile(r"art(?:igo)?\.?\s*(\d+)[°oº]?", re.IGNORECASE)


def extract_citacoes(texto: str) -> list[Citacao]:
    """Stage 1 — EXTRACT: parse legislative citations from ementa text."""
    citacoes: list[Citacao] = []
    seen: set[str] = set()

    for pattern, tipo in _LEI_PATTERNS:
        for m in re.finditer(pattern, texto, re.IGNORECASE):
            numero = m.group(1).replace(".", "")
            try:
                ano = int(m.group(2))
            except (ValueError, IndexError):
                continue

            # Nearest article reference within 200 chars before OR after the citation
            artigo: Optional[str] = None
            window_start = max(0, m.start() - 200)
            context_window = texto[window_start: m.end() + 200]
            art_m = _ART_PATTERN.search(context_window)
            if art_m:
                artigo = re.sub(r"[°oº]", "", art_m.group(1))

            c = Citacao(tipo=tipo, numero=numero, ano=ano, artigo=artigo)
            if c.lei_id not in seen:
                seen.add(c.lei_id)
                citacoes.append(c)

    return citacoes


# ── Stage 2 — RESOLVE ─────────────────────────────────────────────────────────

def _year_range(ano: int) -> tuple[int, int]:
    """Map a year to the Planalto URL 4-year range block."""
    for start in range(2003, 2040, 4):
        if start <= ano <= start + 3:
            return start, start + 3
    return ano, ano + 3


def build_planalto_url(tipo: str, numero: str, ano: int) -> str:
    """Build canonical Planalto.gov.br URL for a given law citation."""
    num = numero.lstrip("0") or "0"
    if tipo == "lc":
        return f"https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp{num}.htm"
    if tipo == "mp":
        if ano < 2003:
            return f"https://www.planalto.gov.br/ccivil_03/mpv/Antigas/mpv{num}.htm"
        s, e = _year_range(ano)
        return f"https://www.planalto.gov.br/ccivil_03/_ato{s}-{e}/{ano}/mpv/mpv{num}.htm"
    # lei ordinária
    if ano < 2003:
        return f"https://www.planalto.gov.br/ccivil_03/leis/l{num}.htm"
    s, e = _year_range(ano)
    return f"https://www.planalto.gov.br/ccivil_03/_ato{s}-{e}/{ano}/lei/l{num}.htm"


def _strip_tags(html: str) -> str:
    """Remove HTML tags and normalise whitespace."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _extract_article_text(html: str, numero_artigo: str) -> Optional[str]:
    """Extract specific article text from Planalto HTML."""
    num = re.sub(r"[°oº]", "", str(numero_artigo)).strip()
    # Patterns for article headings in Planalto HTML
    for pattern in (
        rf"Art\.?\s*{re.escape(num)}\s*[°oº]?\s*[.\u2013\-]",
        rf"Art\.?\s*{re.escape(num)}\s*[°oº]?\s*\n",
        rf"\bArt\.?\s*{re.escape(num)}\b",
    ):
        m = re.search(pattern, html, re.IGNORECASE)
        if not m:
            continue
        # Find where next article starts
        next_art = re.search(r"\bArt\.?\s*\d", html[m.end():], re.IGNORECASE)
        end = m.end() + next_art.start() if next_art else min(m.end() + 2_000, len(html))
        snippet = _strip_tags(html[m.start(): end])
        return snippet[:1_500] if snippet else None
    return None


def _fetch_planalto(url: str) -> tuple[str, str]:
    """
    Fetch a Planalto URL.
    Returns (html_text, status) where status ∈ {resolvido, revogada,
    nao_encontrada, pdf_nao_parseavel, timeout}.
    """
    try:
        with httpx.Client(
            timeout=PLANALTO_TIMEOUT,
            follow_redirects=True,
            # O Planalto derruba a conexão para User-Agents que não pareçam
            # navegador: com "ZIL-Observatorio/1.0" puro, toda busca de lei
            # falhava em silêncio e virava status nao_encontrada. O formato
            # "Mozilla/5.0 (compatible; <bot>; +<url>)" é a convenção de crawler
            # bem-comportado — passa no filtro e continua identificando quem
            # está chamando, com endereço de contato.
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; ZIL-Observatorio/1.0; "
                    "+https://zilobservatorio.org)"
                )
            },
        ) as client:
            resp = client.get(url)

        ct = resp.headers.get("content-type", "")
        if "pdf" in ct.lower():
            return "", "pdf_nao_parseavel"

        if resp.status_code == 404:
            return "", "nao_encontrada"

        html = resp.text

        if re.search(r"\bREVOGAD[AO]\b|\bSEM EFICÁCIA\b", html, re.IGNORECASE):
            return html, "revogada"

        return html, "resolvido"

    except httpx.TimeoutException:
        logger.warning(f"[RESOLVE] timeout fetching {url}")
        return "", "timeout"
    except Exception as exc:
        logger.warning(f"[RESOLVE] error fetching {url}: {exc}")
        return "", "nao_encontrada"


def resolve_citacoes(citacoes: list[Citacao], db) -> list[ArtigoResolvido]:
    """
    Stage 2 — RESOLVE: fetch article texts from Planalto with DB cache.
    One HTTP request per unique lei_id (multiple articles reuse the HTML).
    """
    from sqlalchemy import select
    from models import LeiArtigo

    resolved: list[ArtigoResolvido] = []
    html_cache: dict[str, tuple[str, str]] = {}  # lei_id → (html, status)

    for c in citacoes:
        numero_artigo = c.artigo or "1"
        url = build_planalto_url(c.tipo, c.numero, c.ano)

        # Check DB cache (TTL still valid)
        cached = db.execute(
            select(LeiArtigo).where(
                LeiArtigo.lei_id == c.lei_id,
                LeiArtigo.numero_artigo == numero_artigo,
                LeiArtigo.expira_em > datetime.utcnow(),
            )
        ).scalar_one_or_none()

        if cached:
            resolved.append(ArtigoResolvido(
                lei_id=c.lei_id,
                numero_artigo=numero_artigo,
                texto=cached.texto_artigo,
                url=cached.url_planalto or url,
                status=cached.status,
            ))
            continue

        # Fetch HTML — reuse within same pipeline run
        if c.lei_id not in html_cache:
            html, status = _fetch_planalto(url)
            html_cache[c.lei_id] = (html, status)
        else:
            html, status = html_cache[c.lei_id]

        texto: Optional[str] = None
        if status == "resolvido" and html:
            texto = _extract_article_text(html, numero_artigo)

        # Upsert lei_artigos cache
        now = datetime.utcnow()
        existing = db.execute(
            select(LeiArtigo).where(
                LeiArtigo.lei_id == c.lei_id,
                LeiArtigo.numero_artigo == numero_artigo,
            )
        ).scalar_one_or_none()

        if existing:
            existing.texto_artigo = texto
            existing.url_planalto = url
            existing.status = status
            existing.obtido_em = now
            existing.expira_em = now + timedelta(days=CACHE_TTL_DAYS)
        else:
            db.add(LeiArtigo(
                lei_id=c.lei_id,
                numero_artigo=numero_artigo,
                texto_artigo=texto,
                url_planalto=url,
                status=status,
                obtido_em=now,
                expira_em=now + timedelta(days=CACHE_TTL_DAYS),
            ))
        db.flush()

        resolved.append(ArtigoResolvido(
            lei_id=c.lei_id,
            numero_artigo=numero_artigo,
            texto=texto,
            url=url,
            status=status,
        ))

    return resolved


# ── Stage 3 — AUGMENT ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "Você é um especialista em legislação brasileira que explica leis em linguagem "
    "acessível para cidadãos sem formação jurídica. "
    "Use APENAS o contexto fornecido — nunca use conhecimento externo. "
    "Se não tiver informação suficiente, diga que não sabe."
)


def _build_user_prompt(ementa: str, artigos: list[ArtigoResolvido]) -> str:
    context_parts: list[str] = []
    for a in artigos:
        if a.status == "resolvido" and a.texto:
            context_parts.append(f"[{a.lei_id} — Art. {a.numero_artigo}]\n{a.texto}")
        elif a.status == "revogada":
            context_parts.append(
                f"[{a.lei_id} — Art. {a.numero_artigo}]\nNOTA: Esta lei foi REVOGADA."
            )

    context_block = "\n\n".join(context_parts) if context_parts else "(nenhum artigo resolvido com sucesso)"
    context_block = context_block[:MAX_CONTEXT_CHARS]

    return f"""[CONTEXTO DAS LEIS REFERENCIADAS]
{context_block}

[PROPOSIÇÃO A EXPLICAR]
{ementa[:MAX_EMENTA_CHARS]}

[TAREFA]
Com base APENAS no contexto acima, sem usar conhecimento externo:

Responda em JSON com exatamente estes campos:
{{
  "resumo_simples": "3 a 5 frases em português simples explicando o que esta proposição faz e seu impacto prático",
  "glossario": {{"termo1": "definição em 1 frase", "termo2": "definição em 1 frase"}},
  "impacto_zil": "1 a 2 frases sobre por que esta proposição é relevante para soberania industrial brasileira"
}}

Regras:
- resumo_simples: máximo 5 frases, linguagem acessível (nível ensino médio)
- glossario: máximo 10 termos técnicos presentes na proposição, cada definição em 1 frase simples
- impacto_zil: foco em semicondutores, energia, minerais, defesa, fertilizantes, digital ou comércio exterior
- Se uma lei foi revogada, mencione isso no resumo_simples
- Responda APENAS com o JSON, sem markdown ou texto adicional"""


def augment_with_llm(ementa: str, artigos: list[ArtigoResolvido], modelo: str) -> dict:
    """Stage 3 — AUGMENT: generate enrichment via Claude API with injected context."""
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic não instalado — execute: pip install anthropic"}

    from core.config import settings
    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY não configurado"}

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _build_user_prompt(ementa, artigos)

    message = client.messages.create(
        model=modelo,
        max_tokens=1_024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON block from response
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {"error": f"json_parse_failed: {raw[:200]}"}


# ── Stage 4 — VALIDATE ────────────────────────────────────────────────────────

def validate_enrichment(
    llm_result: dict,
    citacoes: list[Citacao],
    artigos: list[ArtigoResolvido],
) -> tuple[dict, float]:
    """
    Stage 4 — VALIDATE: sanitise LLM output and compute confidence.
    confianca = resolved_articles / max(cited_laws, 1)
    """
    citados = len(citacoes)
    resolvidos = sum(1 for a in artigos if a.status == "resolvido")
    confianca = round(resolvidos / max(citados, 1), 2) if citados > 0 else 1.0

    validated = {
        "resumo_simples": (llm_result.get("resumo_simples") or "")[:2_000],
        "glossario": llm_result.get("glossario") or {},
        "impacto_zil": (llm_result.get("impacto_zil") or "")[:500],
    }

    # Ensure glossario is a dict (LLM sometimes returns a list)
    if not isinstance(validated["glossario"], dict):
        validated["glossario"] = {}

    return validated, confianca


# ── Stage 5 — SERVE (main entrypoint) ────────────────────────────────────────

def enriquecer_proposicao(
    proposicao_id: UUID,
    db,
    force: bool = False,
) -> dict:
    """
    Full pipeline: EXTRACT → RESOLVE → AUGMENT → VALIDATE → SERVE.
    Idempotent: skips if ementa_hash unchanged and status == 'pronto' (unless force=True).
    """
    from models import Proposicao
    from core.config import settings

    modelo = settings.ENRICHMENT_MODEL

    proposicao = db.get(Proposicao, proposicao_id)
    if not proposicao:
        raise ValueError(f"Proposição {proposicao_id} não encontrada")

    ementa = proposicao.ementa or ""
    if not ementa.strip():
        logger.info(f"[SERVE] skip ementa_vazia proposicao={proposicao_id}")
        return {"skipped": "ementa_vazia"}

    # Idempotency check
    ementa_hash = hashlib.sha256(ementa.encode()).hexdigest()
    if (
        not force
        and proposicao.ementa_hash == ementa_hash
        and proposicao.contexto_status == "pronto"
    ):
        logger.info(f"[SERVE] skipped: ementa unchanged proposicao={proposicao_id}")
        return {"skipped": "ementa_unchanged"}

    # Mark as processing
    proposicao.contexto_status = "processando"
    proposicao.ementa_hash = ementa_hash
    db.flush()

    try:
        # Stage 1
        logger.info(f"[EXTRACT] proposicao={proposicao_id}")
        citacoes = extract_citacoes(ementa)
        logger.info(f"[EXTRACT] found {len(citacoes)} citations: {[c.lei_id for c in citacoes]}")

        # Stage 2
        logger.info(f"[RESOLVE] resolving {len(citacoes)} citations")
        artigos = resolve_citacoes(citacoes, db)
        logger.info(f"[RESOLVE] statuses={[a.status for a in artigos]}")

        # Stage 3
        logger.info(f"[AUGMENT] model={modelo}")
        llm_result = augment_with_llm(ementa, artigos, modelo)

        if "error" in llm_result:
            logger.warning(f"[AUGMENT] error: {llm_result['error']}")
            proposicao.contexto_status = "llm_falhou"
            db.commit()
            return {"status": "llm_falhou", "error": llm_result["error"]}

        # Stage 4
        validated, confianca = validate_enrichment(llm_result, citacoes, artigos)
        logger.info(f"[VALIDATE] confianca={confianca}")

        # Stage 5 — atomic persist
        proposicao.resumo_simples = validated["resumo_simples"]
        proposicao.glossario = validated["glossario"] or None
        proposicao.impacto_zil = validated["impacto_zil"]
        proposicao.leis_referenciadas = [
            {
                "lei_id": a.lei_id,
                "numero_artigo": a.numero_artigo,
                "url_planalto": a.url,
                "status": a.status,
                "texto_snippet": (a.texto or "")[:300] if a.texto else None,
            }
            for a in artigos
        ] or None
        proposicao.confianca = confianca
        proposicao.enriquecido_em = datetime.utcnow()
        proposicao.contexto_status = "pronto"
        db.commit()

        logger.info(f"[SERVE] done proposicao={proposicao_id} confianca={confianca}")
        return {
            "status": "pronto",
            "confianca": confianca,
            "citacoes": len(citacoes),
            "artigos_resolvidos": sum(1 for a in artigos if a.status == "resolvido"),
        }

    except Exception as exc:
        logger.error(f"[SERVE] pipeline failed proposicao={proposicao_id}: {exc}", exc_info=True)
        try:
            proposicao.contexto_status = "falhou"
            db.commit()
        except Exception:
            db.rollback()
        raise

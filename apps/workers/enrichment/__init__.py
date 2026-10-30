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
import html as _html
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
    tipo: str           # "lei" | "lc" | "mp" | "dl" (decreto-lei)
    numero: str         # digits only, e.g. "14744"
    ano: int
    artigo: Optional[str] = None
    lei_id: str = field(init=False)

    def __post_init__(self):
        prefix = {"lei": "", "lc": "lc-", "mp": "mp-", "dl": "dl-"}[self.tipo]
        self.lei_id = f"{prefix}{self.numero}-{self.ano}"


@dataclass
class ArtigoResolvido:
    lei_id: str
    numero_artigo: str
    texto: Optional[str]
    url: str
    # resolvido | artigo_revogado | revogada | nao_encontrada | pdf_nao_parseavel | timeout
    # `revogada` é a norma inteira; `artigo_revogado` é só o dispositivo citado,
    # numa lei que segue vigente.
    status: str


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
    # Decreto-lei antes de lei: "Decreto-Lei nº 227, de 1967" é o Código de
    # Mineração, não a "Lei nº 227". O lookbehind da lei impede a dupla leitura.
    (
        r"Decreto[-\s]Lei\s+n[oº°]?\.?\s*(\d[\d.]+)" + _YEAR_SUFFIX,
        "dl",
    ),
    (
        r"(?<!-)(?<!Decreto\s)Lei\s+n[oº°]?\.?\s*(\d[\d.]+)" + _YEAR_SUFFIX,
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
    if tipo == "dl":
        return f"https://www.planalto.gov.br/ccivil_03/decreto-lei/del{int(num):04d}.htm"
    if tipo == "mp":
        if ano < 2003:
            return f"https://www.planalto.gov.br/ccivil_03/mpv/Antigas/mpv{num}.htm"
        s, e = _year_range(ano)
        return f"https://www.planalto.gov.br/ccivil_03/_ato{s}-{e}/{ano}/mpv/mpv{num}.htm"
    # lei ordinária. 2001 a 2006 não seguem o padrão dos blocos de quatro anos:
    # 2001 fica em leis/leis_2001, 2002 e 2003 em leis/<ano>, e o primeiro
    # bloco "_ato" é 2004-2006 (conferido no Planalto em 2026-10-29; antes
    # disso as leis desses anos saíam todas "não encontradas").
    if ano < 2001:
        return f"https://www.planalto.gov.br/ccivil_03/leis/l{num}.htm"
    if ano == 2001:
        return f"https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l{num}.htm"
    if ano <= 2003:
        return f"https://www.planalto.gov.br/ccivil_03/leis/{ano}/l{num}.htm"
    if ano <= 2006:
        return f"https://www.planalto.gov.br/ccivil_03/_ato2004-2006/{ano}/lei/l{num}.htm"
    s, e = _year_range(ano)
    return f"https://www.planalto.gov.br/ccivil_03/_ato{s}-{e}/{ano}/lei/l{num}.htm"


def _urls_planalto(tipo: str, numero: str, ano: int) -> list[str]:
    """A URL canônica e, no mesmo diretório, as variantes que o Planalto usa
    para leis alteradas: o texto consolidado (`cons`) e o compilado. A Lei
    9.427/1996 (ANEEL), por exemplo, só existe em `l9427cons.htm`; sem isto ela
    saía `nao_encontrada`."""
    canonica = build_planalto_url(tipo, numero, ano)
    base, arquivo = canonica.rsplit("/", 1)
    nome = arquivo.removesuffix(".htm")
    variantes = [f"{nome}cons.htm", f"{nome}compilado.htm", f"{nome[:1].upper()}{nome[1:]}compilado.htm"]
    urls = [canonica] + [f"{base}/{v}" for v in variantes]
    num = numero.lstrip("0") or "0"
    # Algumas leis usam o número com ponto de milhar no arquivo: l10.848.htm.
    if tipo == "lei" and len(num) > 3:
        urls.append(f"{base}/l{int(num):,}.htm".replace(",", "."))
    # Leis de 1989 a 1994 e decretos-leis de 1965 a 1988 têm diretório próprio.
    if tipo == "lei" and 1989 <= ano <= 1994:
        urls.append(f"https://www.planalto.gov.br/ccivil_03/leis/1989_1994/L{num}.htm")
    if tipo == "dl" and 1965 <= ano <= 1988:
        urls.append(f"https://www.planalto.gov.br/ccivil_03/decreto-lei/1965-1988/Del{num}.htm")
    return urls


# A norma inteira está revogada quando o aviso aparece no cabeçalho, entre a
# epígrafe e o art. 1º: "Revogada pela Lei nº 14.133, de 2021". No corpo, o
# Planalto marca cada dispositivo revogado — "(Revogado pela Lei nº ...)" —, e
# quase toda lei consolidada tem algum. Procurar no HTML inteiro, como se fazia
# até 2026-10-29, marcava como revogadas a Lei do Petróleo, a da Política
# Agrícola e a da PPSA, e o prompt dizia isso ao modelo.
_PRIMEIRO_ARTIGO = re.compile(r"\bArt\.?\s*1\s*[ºo°]?(?!\d)", re.IGNORECASE)
_NORMA_REVOGADA = re.compile(r"Revogad[ao]\s+pel[ao]|\bSEM EFIC[ÁA]CIA\b", re.IGNORECASE)
_DISPOSITIVO_REVOGADO = re.compile(r"\(\s*Revogad[oa]", re.IGNORECASE)


def _cabecalho(texto: str) -> str:
    m = _PRIMEIRO_ARTIGO.search(texto)
    return texto[: m.start()] if m else texto[:3_000]


def norma_revogada(html: str) -> bool:
    """A norma inteira foi revogada? Só o cabeçalho decide."""
    return bool(_NORMA_REVOGADA.search(_cabecalho(_strip_tags(html))))


def _strip_tags(html: str) -> str:
    """Remove HTML tags, resolve entidades e normaliza espaços.

    Sem o unescape, `&nbsp;` e `&amp;` sobrevivem no texto que vai para o banco
    e para o LLM — ruído que atrapalha tanto a leitura humana quanto o prompt.
    """
    text = re.sub(r"<[^>]+>", " ", html)
    text = _html.unescape(text)
    # \xa0 é o espaço não-separável que o &nbsp; vira depois do unescape
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _extract_article_text(html: str, numero_artigo: str) -> Optional[str]:
    """Extract specific article text from Planalto HTML."""
    num = re.sub(r"[°oº]", "", str(numero_artigo)).strip()
    # Patterns for article headings in Planalto HTML
    for pattern in (
        rf"Art\.?\s*{re.escape(num)}\s*[°oº]?\s*[.\u2013\-]",
        rf"Art\.?\s*{re.escape(num)}\s*[°oº]?\s*\n",
        # "º" é letra para o regex, então `\b` depois de "7" falha em "Art. 7º
        # Fica…" — o caso comum, de 1º a 9º. O lookahead de dígito evita que
        # "Art. 1" case com "Art. 10".
        rf"\bArt\.?\s*{re.escape(num)}(?:\s*[°oº])?(?!\d)",
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
                    "+https://zilobservatorio.com.br)"
                )
            },
        ) as client:
            resp = client.get(url)

        ct = resp.headers.get("content-type", "")
        if "pdf" in ct.lower():
            return "", "pdf_nao_parseavel"

        if resp.status_code == 404:
            return "", "nao_encontrada"

        # O Planalto serve Content-Type sem charset, então o httpx assume utf-8 —
        # e o conteúdo é windows-1252. Sem isto o texto da lei volta ilegível
        # ("dispõe" vira "disp?e"), o que é pior que não voltar: parece dado
        # bom e não é.
        if "charset=" not in ct.lower():
            resp.encoding = "windows-1252"

        html = resp.text

        if norma_revogada(html):
            return html, "revogada"

        return html, "resolvido"

    except httpx.TimeoutException:
        logger.warning(f"[RESOLVE] timeout fetching {url}")
        return "", "timeout"
    except Exception as exc:
        logger.warning(f"[RESOLVE] error fetching {url}: {exc}")
        return "", "nao_encontrada"


def _buscar_lei(urls: list[str]) -> tuple[str, str, str]:
    """Tenta as URLs em ordem e para na primeira que não for 404.
    Devolve (html, status, url que respondeu)."""
    for url in urls:
        html, status = _fetch_planalto(url)
        if status != "nao_encontrada":
            return html, status, url
    return "", "nao_encontrada", urls[0]


# Só estes status são confiáveis no cache. `revogada` e `nao_encontrada`
# gravados antes da correção da detecção estavam errados com frequência;
# rebuscá-los é barato e corrige o histórico sem migração.
_CACHE_CONFIAVEL = ("resolvido", "artigo_revogado")


def resolve_citacoes(citacoes: list[Citacao], db) -> list[ArtigoResolvido]:
    """
    Stage 2 — RESOLVE: fetch article texts from Planalto with DB cache.
    One HTTP request per unique lei_id (multiple articles reuse the HTML).
    """
    from sqlalchemy import select
    from models import LeiArtigo

    resolved: list[ArtigoResolvido] = []
    html_cache: dict[str, tuple[str, str, str]] = {}  # lei_id → (html, status, url)

    for c in citacoes:
        numero_artigo = c.artigo or "1"
        urls = _urls_planalto(c.tipo, c.numero, c.ano)
        url = urls[0]

        # Check DB cache (TTL still valid)
        cached = db.execute(
            select(LeiArtigo).where(
                LeiArtigo.lei_id == c.lei_id,
                LeiArtigo.numero_artigo == numero_artigo,
                LeiArtigo.expira_em > datetime.utcnow(),
                LeiArtigo.status.in_(_CACHE_CONFIAVEL),
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
            html, status, url = _buscar_lei(urls)
            html_cache[c.lei_id] = (html, status, url)
        else:
            html, status, url = html_cache[c.lei_id]

        texto: Optional[str] = None
        if status == "resolvido" and html:
            texto = _extract_article_text(html, numero_artigo)
            # Lei vigente, dispositivo citado revogado: o modelo precisa
            # saber disso, e a lei não vira "revogada" por causa dele.
            if texto and _DISPOSITIVO_REVOGADO.search(texto[:300]):
                status = "artigo_revogado"

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
        elif a.status == "artigo_revogado":
            context_parts.append(
                f"[{a.lei_id} — Art. {a.numero_artigo}]\nNOTA: este artigo foi revogado; a lei segue vigente.\n{a.texto or ''}"
            )
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
- Se uma lei inteira foi revogada, mencione isso no resumo_simples; artigo revogado não torna a lei revogada
- Responda APENAS com o JSON, sem markdown ou texto adicional"""


def augment_with_llm(ementa: str, artigos: list[ArtigoResolvido], modelo: str) -> dict:
    """Stage 3 — AUGMENT: generate enrichment via Claude API with injected context.

    Passa pela fronteira única (`agentes.fronteira.consultar`), que lê só os
    blocos de texto — o Sonnet 5.5 responde com um bloco de raciocínio antes do
    JSON, e ler `content[0]` devolvia vazio —, trata recusa, corte por
    `max_tokens` e chave inválida como erro declarado, e conta tokens.
    """
    from core.config import settings

    from ..agentes.fronteira import consultar, retirar_uso

    resultado = consultar(
        modelo,
        _SYSTEM_PROMPT,
        _build_user_prompt(ementa, artigos),
        # O raciocínio conta aqui: 1.024, que bastava ao Haiku, cortaria a resposta.
        max_tokens=16_000,
        esforco=settings.ENRICHMENT_EFFORT or None,
        fallback=True,
    )
    uso = retirar_uso(resultado)
    if uso:
        logger.info(f"[AUGMENT] tokens entrada={uso.get('entrada')} saida={uso.get('saida')}")
    return resultado


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
    resolvidos = sum(1 for a in artigos if a.status in ("resolvido", "artigo_revogado"))
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
            "artigos_resolvidos": sum(1 for a in artigos if a.status in ("resolvido", "artigo_revogado")),
        }

    except Exception as exc:
        logger.error(f"[SERVE] pipeline failed proposicao={proposicao_id}: {exc}", exc_info=True)
        try:
            proposicao.contexto_status = "falhou"
            db.commit()
        except Exception:
            db.rollback()
        raise

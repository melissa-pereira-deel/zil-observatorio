"""Unit tests for the legislative enrichment pipeline (Feature 002)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure apps/api and project root are in sys.path (mirrors conftest.py)
REPO_ROOT = Path(__file__).parent.parent.parent
API_DIR = REPO_ROOT / "apps" / "api"
for p in (str(REPO_ROOT), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from apps.workers.enrichment import (
    Citacao,
    ArtigoResolvido,
    build_planalto_url,
    extract_citacoes,
    validate_enrichment,
    _extract_article_text,
    _year_range,
)


# ── _year_range ───────────────────────────────────────────────────────────────

class TestYearRange:
    def test_2023(self):
        assert _year_range(2023) == (2023, 2026)

    def test_2024(self):
        assert _year_range(2024) == (2023, 2026)

    def test_2019(self):
        assert _year_range(2019) == (2019, 2022)

    def test_2015(self):
        assert _year_range(2015) == (2015, 2018)

    def test_2007(self):
        assert _year_range(2007) == (2007, 2010)

    def test_2003(self):
        assert _year_range(2003) == (2003, 2006)


# ── build_planalto_url ────────────────────────────────────────────────────────

class TestBuildPlanaltoUrl:
    def test_lei_2023(self):
        url = build_planalto_url("lei", "14744", 2023)
        assert "planalto.gov.br" in url
        assert "14744" in url
        assert "2023" in url
        assert "_ato2023-2026" in url

    def test_lei_pre_2003(self):
        url = build_planalto_url("lei", "9472", 1997)
        assert "planalto.gov.br" in url
        assert "l9472" in url
        assert "_ato" not in url

    def test_lc(self):
        url = build_planalto_url("lc", "87", 1996)
        assert "lcp" in url.lower()
        assert "87" in url

    def test_mp_2023(self):
        url = build_planalto_url("mp", "1234", 2023)
        assert "mpv" in url.lower()
        assert "1234" in url

    def test_lei_strips_leading_zero(self):
        url = build_planalto_url("lei", "09472", 1997)
        assert "l9472" in url


# ── extract_citacoes ─────────────────────────────────────────────────────────

class TestExtractCitacoes:
    def test_lei_ordinaria(self):
        ementa = "Altera a Lei nº 14.744, de 21 de novembro de 2023."
        citacoes = extract_citacoes(ementa)
        assert len(citacoes) == 1
        assert citacoes[0].tipo == "lei"
        assert citacoes[0].numero == "14744"
        assert citacoes[0].ano == 2023

    def test_lei_com_artigo(self):
        ementa = "Altera o art. 3º da Lei nº 9.472/1997."
        citacoes = extract_citacoes(ementa)
        assert len(citacoes) == 1
        assert citacoes[0].artigo == "3"

    def test_lei_complementar(self):
        ementa = "Altera a Lei Complementar nº 87, de 1996."
        citacoes = extract_citacoes(ementa)
        assert len(citacoes) == 1
        assert citacoes[0].tipo == "lc"
        assert citacoes[0].numero == "87"

    def test_medida_provisoria(self):
        ementa = "Converte a Medida Provisória nº 1.234/2023 em lei."
        citacoes = extract_citacoes(ementa)
        assert len(citacoes) == 1
        assert citacoes[0].tipo == "mp"
        assert citacoes[0].numero == "1234"

    def test_multiple_leis(self):
        ementa = (
            "Altera a Lei nº 9.472/1997 e a Lei nº 14.744/2023 para estabelecer..."
        )
        citacoes = extract_citacoes(ementa)
        lei_ids = {c.lei_id for c in citacoes}
        assert "9472-1997" in lei_ids
        assert "14744-2023" in lei_ids

    def test_deduplication(self):
        ementa = "Altera o art. 3º e o art. 7º da Lei nº 14.744/2023."
        citacoes = extract_citacoes(ementa)
        # Same lei_id — only one Citacao per lei
        assert len(citacoes) == 1
        assert citacoes[0].lei_id == "14744-2023"

    def test_no_lei_citation(self):
        ementa = "Institui o Programa Nacional de Semicondutores."
        citacoes = extract_citacoes(ementa)
        assert citacoes == []

    def test_lei_id_format(self):
        c = Citacao(tipo="lei", numero="14744", ano=2023)
        assert c.lei_id == "14744-2023"

    def test_lc_lei_id_format(self):
        c = Citacao(tipo="lc", numero="87", ano=1996)
        assert c.lei_id == "lc-87-1996"

    def test_mp_lei_id_format(self):
        c = Citacao(tipo="mp", numero="1234", ano=2023)
        assert c.lei_id == "mp-1234-2023"

    def test_lei_sem_pontos(self):
        ementa = "Altera a Lei nº 9472 de 1997."
        citacoes = extract_citacoes(ementa)
        assert len(citacoes) == 1
        assert citacoes[0].numero == "9472"

    def test_real_padis_ementa(self):
        ementa = (
            "Altera a Lei nº 14.744, de 21 de novembro de 2023, para incluir a "
            "margem de preferência de até 25% nas licitações e contratações diretas "
            "da administração pública federal para produtos e serviços de tecnologia "
            "da informação e comunicação fabricados por empresas beneficiárias do PADIS."
        )
        citacoes = extract_citacoes(ementa)
        assert len(citacoes) >= 1
        assert citacoes[0].lei_id == "14744-2023"


# ── _extract_article_text ─────────────────────────────────────────────────────

class TestExtractArticleText:
    SAMPLE_HTML = """
    <html><body>
    <p>Art. 1 Esta lei dispõe sobre semicondutores.</p>
    <p>Art. 2 Fica criado o PADIS.</p>
    <p>§ 1 O PADIS será gerido pelo Ministério da Ciência.</p>
    <p>Art. 3 Esta lei entra em vigor na data de publicação.</p>
    </body></html>
    """

    def test_extracts_article_1(self):
        text = _extract_article_text(self.SAMPLE_HTML, "1")
        assert text is not None
        assert "semicondutores" in text.lower()

    def test_extracts_article_2(self):
        text = _extract_article_text(self.SAMPLE_HTML, "2")
        assert text is not None
        assert "PADIS" in text

    def test_missing_article_returns_none(self):
        text = _extract_article_text(self.SAMPLE_HTML, "99")
        assert text is None

    def test_strips_html_tags(self):
        text = _extract_article_text(self.SAMPLE_HTML, "1")
        assert "<p>" not in (text or "")
        assert "<html>" not in (text or "")


# ── validate_enrichment ───────────────────────────────────────────────────────

class TestValidateEnrichment:
    def test_full_confidence_when_all_resolved(self):
        citacoes = [Citacao(tipo="lei", numero="14744", ano=2023, artigo="3")]
        artigos = [
            ArtigoResolvido(lei_id="14744-2023", numero_artigo="3",
                            texto="texto do art 3", url="http://ex.com", status="resolvido")
        ]
        _, confianca = validate_enrichment({}, citacoes, artigos)
        assert confianca == 1.0

    def test_zero_confidence_when_none_resolved(self):
        citacoes = [Citacao(tipo="lei", numero="9472", ano=1997, artigo="4")]
        artigos = [
            ArtigoResolvido(lei_id="9472-1997", numero_artigo="4",
                            texto=None, url="http://ex.com", status="nao_encontrada")
        ]
        _, confianca = validate_enrichment({}, citacoes, artigos)
        assert confianca == 0.0

    def test_partial_confidence(self):
        citacoes = [
            Citacao(tipo="lei", numero="14744", ano=2023, artigo="3"),
            Citacao(tipo="lei", numero="9472", ano=1997, artigo="4"),
        ]
        artigos = [
            ArtigoResolvido(lei_id="14744-2023", numero_artigo="3",
                            texto="ok", url="http://a.com", status="resolvido"),
            ArtigoResolvido(lei_id="9472-1997", numero_artigo="4",
                            texto=None, url="http://b.com", status="nao_encontrada"),
        ]
        _, confianca = validate_enrichment({}, citacoes, artigos)
        assert confianca == 0.5

    def test_confianca_1_when_no_citations(self):
        _, confianca = validate_enrichment({}, [], [])
        assert confianca == 1.0

    def test_sanitises_glossario(self):
        llm = {"resumo_simples": "ok", "glossario": ["lista", "errada"], "impacto_zil": ""}
        validated, _ = validate_enrichment(llm, [], [])
        assert validated["glossario"] == {}

    def test_truncates_resumo(self):
        llm = {"resumo_simples": "x" * 5000, "glossario": {}, "impacto_zil": ""}
        validated, _ = validate_enrichment(llm, [], [])
        assert len(validated["resumo_simples"]) <= 2000

    def test_truncates_impacto(self):
        llm = {"resumo_simples": "", "glossario": {}, "impacto_zil": "y" * 1000}
        validated, _ = validate_enrichment(llm, [], [])
        assert len(validated["impacto_zil"]) <= 500


# ── enriquecer_proposicao (integration-style, all external calls mocked) ──────

class TestEnriquecerProposicao:
    """Integration-style tests: mock Planalto HTTP + Claude API."""

    def _make_db(self, proposicao):
        """Build a minimal mock db session."""
        db = MagicMock()
        db.get.return_value = proposicao
        db.execute.return_value.scalar_one_or_none.return_value = None
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.add = MagicMock()
        return db

    def test_skips_empty_ementa(self):
        from apps.workers.enrichment import enriquecer_proposicao
        from uuid import uuid4

        prop = MagicMock()
        prop.ementa = ""
        prop.ementa_hash = None
        prop.contexto_status = None

        db = self._make_db(prop)
        result = enriquecer_proposicao(uuid4(), db)
        assert result == {"skipped": "ementa_vazia"}

    def test_skips_unchanged_ementa(self):
        import hashlib
        from apps.workers.enrichment import enriquecer_proposicao
        from uuid import uuid4

        ementa = "Altera a Lei nº 14.744/2023."
        ementa_hash = hashlib.sha256(ementa.encode()).hexdigest()

        prop = MagicMock()
        prop.ementa = ementa
        prop.ementa_hash = ementa_hash
        prop.contexto_status = "pronto"

        db = self._make_db(prop)
        result = enriquecer_proposicao(uuid4(), db, force=False)
        assert result == {"skipped": "ementa_unchanged"}

    def test_force_ignores_hash(self):
        import hashlib
        from apps.workers.enrichment import enriquecer_proposicao
        from uuid import uuid4

        ementa = "Altera a Lei nº 14.744/2023."
        ementa_hash = hashlib.sha256(ementa.encode()).hexdigest()

        prop = MagicMock()
        prop.ementa = ementa
        prop.ementa_hash = ementa_hash
        prop.contexto_status = "pronto"

        db = self._make_db(prop)

        llm_response = {
            "resumo_simples": "Resumo teste.",
            "glossario": {"PADIS": "Programa de apoio."},
            "impacto_zil": "Relevante para semicondutores.",
        }

        with (
            patch("apps.workers.enrichment._fetch_planalto", return_value=("", "nao_encontrada")),
            patch("apps.workers.enrichment.augment_with_llm", return_value=llm_response),
        ):
            result = enriquecer_proposicao(uuid4(), db, force=True)

        assert result["status"] == "pronto"
        assert prop.resumo_simples == "Resumo teste."
        assert prop.contexto_status == "pronto"

    def test_llm_error_sets_llm_falhou(self):
        from apps.workers.enrichment import enriquecer_proposicao
        from uuid import uuid4

        prop = MagicMock()
        prop.ementa = "Altera a Lei nº 14.744/2023."
        prop.ementa_hash = None
        prop.contexto_status = None

        db = self._make_db(prop)

        with (
            patch("apps.workers.enrichment._fetch_planalto", return_value=("", "nao_encontrada")),
            patch("apps.workers.enrichment.augment_with_llm", return_value={"error": "api key missing"}),
        ):
            result = enriquecer_proposicao(uuid4(), db, force=False)

        assert result["status"] == "llm_falhou"
        assert prop.contexto_status == "llm_falhou"

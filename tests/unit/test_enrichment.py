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
    norma_revogada,
    validate_enrichment,
    _build_user_prompt,
    _buscar_lei,
    _extract_article_text,
    _urls_planalto,
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

    @pytest.mark.parametrize("numero,ano,caminho", [
        ("10332", 2001, "/leis/leis_2001/l10332.htm"),
        ("10438", 2002, "/leis/2002/l10438.htm"),
        ("10753", 2003, "/leis/2003/l10753.htm"),
        ("11196", 2005, "/_ato2004-2006/2005/lei/l11196.htm"),
        ("11508", 2007, "/_ato2007-2010/2007/lei/l11508.htm"),
        ("9991", 2000, "/leis/l9991.htm"),
    ])
    def test_diretorios_de_2001_a_2006(self, numero, ano, caminho):
        """2001–2006 não seguem os blocos de quatro anos do Planalto."""
        assert build_planalto_url("lei", numero, ano).endswith(caminho)

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

    def test_artigo_com_ordinal_seguido_de_espaco(self):
        html = "<p>Art. 7º Fica criado o fundo.</p><p>Art. 70 Outra coisa.</p>"
        text = _extract_article_text(html, "7")
        assert text is not None and "fundo" in text and "Outra" not in text

    def test_strips_html_tags(self):
        text = _extract_article_text(self.SAMPLE_HTML, "1")
        assert "<p>" not in (text or "")
        assert "<html>" not in (text or "")


# ── revogação: norma inteira × dispositivo ───────────────────────────────────
#
# Até 2026-10-29 bastava a palavra "revogado" em qualquer ponto da página para
# a lei inteira virar "revogada". Toda lei consolidada tem algum dispositivo
# revogado, e o prompt dizia ao modelo que a Lei do Petróleo estava revogada.

_LEI_VIGENTE = """
<p>LEI Nº 9.478, DE 6 DE AGOSTO DE 1997.</p>
<p>Dispõe sobre a política energética nacional.</p>
<p>O PRESIDENTE DA REPÚBLICA Faço saber que o Congresso Nacional decreta:</p>
<p>Art. 1º As políticas nacionais para o aproveitamento racional das fontes de energia.</p>
<p>Art. 5º As atividades econômicas serão reguladas.</p>
<p>§ 2º (Revogado pela Lei nº 12.351, de 2010)</p>
<p>Art. 7º (Revogado).</p>
<p>Art. 8º A ANP terá como finalidade promover a regulação.</p>
"""

_LEI_REVOGADA = """
<p>LEI Nº 8.666, DE 21 DE JUNHO DE 1993</p>
<p>Revogada pela Lei nº 14.133, de 2021</p>
<p>Regulamenta o art. 37, inciso XXI, da Constituição Federal.</p>
<p>Art. 1º Esta Lei estabelece normas gerais sobre licitações.</p>
"""


class TestRevogacao:
    def test_dispositivo_revogado_nao_revoga_a_lei(self):
        assert norma_revogada(_LEI_VIGENTE) is False

    def test_aviso_no_cabecalho_revoga_a_lei(self):
        assert norma_revogada(_LEI_REVOGADA) is True

    def test_artigo_citado_revogado_vira_artigo_revogado(self):
        from apps.workers.enrichment import resolve_citacoes

        db = MagicMock()
        db.execute.return_value.scalar_one_or_none.return_value = None
        c = Citacao(tipo="lei", numero="9478", ano=1997, artigo="7")
        with patch("apps.workers.enrichment._fetch_planalto", return_value=(_LEI_VIGENTE, "resolvido")):
            [a] = resolve_citacoes([c], db)
        assert a.status == "artigo_revogado"
        assert a.texto and "Revogado" in a.texto

    def test_artigo_revogado_conta_na_confianca(self):
        c = Citacao(tipo="lei", numero="9478", ano=1997, artigo="7")
        a = ArtigoResolvido(lei_id=c.lei_id, numero_artigo="7", texto="Art. 7º (Revogado).", url="u", status="artigo_revogado")
        _, confianca = validate_enrichment({"resumo_simples": "x"}, [c], [a])
        assert confianca == 1.0

    def test_prompt_nao_diz_que_a_lei_foi_revogada(self):
        a = ArtigoResolvido(lei_id="9478-1997", numero_artigo="7", texto="Art. 7º (Revogado).", url="u", status="artigo_revogado")
        prompt = _build_user_prompt("Altera a Lei nº 9.478, de 1997.", [a])
        assert "Esta lei foi REVOGADA" not in prompt
        assert "a lei segue vigente" in prompt


class TestUrlConsolidada:
    def test_variantes_no_mesmo_diretorio(self):
        urls = _urls_planalto("lei", "9427", 1996)
        assert urls[0].endswith("/leis/l9427.htm")
        assert urls[1].endswith("/leis/l9427cons.htm")
        assert all("/ccivil_03/leis/" in u for u in urls)

    def test_404_na_canonica_tenta_a_consolidada(self):
        def responde(url):
            return (_LEI_VIGENTE, "resolvido") if url.endswith("cons.htm") else ("", "nao_encontrada")

        with patch("apps.workers.enrichment._fetch_planalto", side_effect=responde):
            html, status, url = _buscar_lei(_urls_planalto("lei", "9427", 1996))
        assert status == "resolvido" and url.endswith("l9427cons.htm")

    def test_decreto_lei_nao_e_lei(self):
        [c] = extract_citacoes("Altera o Decreto-Lei nº 227, de 28 de fevereiro de 1967.")
        assert c.tipo == "dl" and c.lei_id == "dl-227-1967"
        assert build_planalto_url("dl", "227", 1967).endswith("/decreto-lei/del0227.htm")

    def test_decreto_lei_de_1965_a_1988_tem_diretorio_proprio(self):
        assert _urls_planalto("dl", "1804", 1980)[-1].endswith("/decreto-lei/1965-1988/Del1804.htm")

    def test_lei_de_1989_a_1994_tem_diretorio_proprio(self):
        assert _urls_planalto("lei", "8970", 1994)[-1].endswith("/leis/1989_1994/L8970.htm")

    def test_variante_com_ponto_de_milhar(self):
        urls = _urls_planalto("lei", "10848", 2004)
        assert any(u.endswith("/_ato2004-2006/2004/lei/l10.848.htm") for u in urls)

    def test_todas_404_e_nao_encontrada_com_a_canonica(self):
        with patch("apps.workers.enrichment._fetch_planalto", return_value=("", "nao_encontrada")):
            _, status, url = _buscar_lei(_urls_planalto("lei", "9427", 1996))
        assert status == "nao_encontrada" and url.endswith("l9427.htm")


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


# ── Stage 3 — AUGMENT: Sonnet 5.5 pela fronteira única ──────────────────────

_FICTICIA = "valor-ficticio"


class TestAugment:
    def test_usa_modelo_esforco_e_fallback_da_configuracao(self):
        from apps.workers.enrichment import augment_with_llm

        chamadas = []

        def falso(modelo, system, prompt, **kw):
            chamadas.append((modelo, kw))
            return {"resumo_simples": "ok", "_uso": {"entrada": 10, "saida": 5}}

        with patch("apps.workers.agentes.fronteira.consultar", side_effect=falso):
            res = augment_with_llm("Institui X.", [], "claude-sonnet-5-5")

        modelo, kw = chamadas[0]
        assert modelo == "claude-sonnet-5-5"
        assert kw["esforco"] == "medium" and kw["fallback"] is True
        # o raciocínio conta no limite: 1.024 cortaria a resposta
        assert kw["max_tokens"] >= 8_000
        assert res == {"resumo_simples": "ok"}  # `_uso` retirado antes de validar

    def test_fronteira_envia_effort_e_fallback_e_le_o_texto_depois_do_raciocinio(self, monkeypatch):
        import anthropic
        from types import SimpleNamespace

        from apps.workers.agentes.fronteira import consultar

        recebido = {}

        def responde(self, **kw):
            recebido.update(kw)
            return SimpleNamespace(
                stop_reason="end_turn",
                usage=SimpleNamespace(input_tokens=1, output_tokens=1),
                content=[SimpleNamespace(type="thinking", text=""), SimpleNamespace(type="text", text='{"resumo_simples": "x"}')],
            )

        monkeypatch.setattr(anthropic.resources.messages.Messages, "create", responde)
        res = consultar("claude-sonnet-5-5", "s", "p", max_tokens=16_000, api_key=_FICTICIA, esforco="medium", fallback=True)
        assert res["resumo_simples"] == "x"
        assert recebido["extra_body"] == {"output_config": {"effort": "medium"}, "fallbacks": "default"}
        assert recebido["extra_headers"] == {"anthropic-beta": "server-side-fallback-2026-07-01"}

    def test_recusa_vira_erro_declarado(self, monkeypatch):
        import anthropic
        from types import SimpleNamespace

        from apps.workers.agentes.fronteira import consultar

        monkeypatch.setattr(
            anthropic.resources.messages.Messages,
            "create",
            lambda self, **kw: SimpleNamespace(
                stop_reason="refusal",
                stop_details=SimpleNamespace(category="cyber"),
                usage=SimpleNamespace(input_tokens=1, output_tokens=0),
                content=[],
            ),
        )
        res = consultar("claude-sonnet-5-5", "s", "p", max_tokens=100, api_key=_FICTICIA)
        assert res["error"] == "recusa do modelo (cyber)"

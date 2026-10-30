"""Fontes externas curadas (`apps/workers/fontes/`) — sem rede.

O que se prova aqui é o que NÃO depende de servidor nenhum: a allowlist é
aplicada no transporte antes de a requisição sair; falha vira lacuna, nunca
exceção; a consulta é por intervalo explícito; o contexto é ancorado no que
já estava publicado na data da proposição; e o hash do contexto cobre só o
conteúdo. As respostas abaixo foram gravadas de consultas reais em
2026-10-21 — são o formato real, não um formato suposto.
"""

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.fontes import (  # noqa: E402
    ADAPTADORES,
    NATUREZAS,
    HostNaoPermitido,
    Observacao,
    Observacoes,
    TransportePermitido,
    carregar_catalogo,
    carregar_plano,
    consultar_serie,
    fim_vigente,
    montar_contexto,
    normalizar,
    planejar,
)
from apps.workers.fontes.catalogo import CATALOGO as CATALOGO_PATH  # noqa: E402

CATALOGO = carregar_catalogo()
PLANO = carregar_plano(catalogo=CATALOGO)
AGORA = datetime(2026, 10, 21, 12, 0, tzinfo=timezone.utc)

# ── respostas reais, gravadas em 2026-10-21 ──────────────────────────────────
BCB_432 = [{"data": f"0{d}/03/2025", "valor": "13.25"} for d in range(1, 6)]
BCB_13522 = [{"data": "01/01/2025", "valor": "4.56"}, {"data": "01/02/2025", "valor": "5.06"}, {"data": "01/03/2025", "valor": "5.48"}]
IBGE_6579 = [{
    "id": "9324", "variavel": "População residente estimada", "unidade": "Pessoas",
    "resultados": [{"classificacoes": [], "series": [{
        "localidade": {"id": "1", "nivel": {"id": "N1", "nome": "Brasil"}, "nome": "Brasil"},
        "serie": {"2024": "212583750"},
    }]}],
}]
IPEA_VALORES = {"value": [
    {"SERCODIGO": "BM12_TJOVER12", "VALDATA": "1974-01-01T00:00:00-02:00", "VALVALOR": 1.46},
    {"SERCODIGO": "BM12_TJOVER12", "VALDATA": "2025-02-01T00:00:00-03:00", "VALVALOR": 1.0},
    {"SERCODIGO": "BM12_TJOVER12", "VALDATA": "2025-03-01T00:00:00-03:00", "VALVALOR": 0.96},
]}
# Série inexistente no BCB: página HTML com status 200.
BCB_HTML = '<!doctype html>\n<html lang="pt-br">\n<head><meta charset="utf-8"></head><body>erro</body></html>'


def _transporte(por_host: dict):
    """MockTransport que roteia por host e registra cada requisição.
    `por_host[host]` é uma função request → Response, ou um objeto JSON."""
    chamadas: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        chamadas.append(request)
        alvo = por_host.get(request.url.host)
        if alvo is None:
            return httpx.Response(404)
        if callable(alvo):
            return alvo(request)
        return httpx.Response(200, json=alvo)

    return httpx.MockTransport(handler), chamadas


def _consultar(tmp_path, por_host, ref, inicio, fim, **kw):
    transport, chamadas = _transporte(por_host)
    kw.setdefault("cache_dir", tmp_path / "cache")
    kw.setdefault("agora", AGORA)
    res = consultar_serie(ref, inicio, fim, catalogo=CATALOGO, transport=transport, **kw)
    return res, chamadas


# ── catálogo ──────────────────────────────────────────────────────────────────

class TestCatalogo:
    def test_carrega_com_hash_curto(self):
        assert len(CATALOGO.hash) == 16 and CATALOGO.origem == "catalogo.yml"

    def test_toda_fonte_declara_natureza_e_vies(self):
        for f in CATALOGO.fontes.values():
            assert f.natureza in NATUREZAS, f.id
            assert len(f.vies_declarado) > 40, f"{f.id}: viés declarado curto demais para dizer algo"

    def test_toda_serie_tem_conceitos_e_parametros(self):
        for ref in CATALOGO.refs:
            s = CATALOGO.serie(ref)
            assert s.conceitos and s.parametros, ref

    def test_fonte_habilitada_tem_adaptador_implementado(self):
        for f in CATALOGO.fontes.values():
            if f.habilitada:
                assert f.adaptador in ADAPTADORES, f.id

    def test_chave_e_nome_de_variavel_nunca_valor(self):
        portal = CATALOGO.fontes["portal_transparencia"]
        assert portal.chave == "PORTAL_TRANSPARENCIA_KEY"
        assert not portal.habilitada

    def test_desabilitadas_ficam_fora_da_allowlist_de_rede(self):
        hosts = CATALOGO.hosts_permitidos
        assert "api.bcb.gov.br" in hosts
        assert "api.portaldatransparencia.gov.br" not in hosts
        assert "apidatalake.tesouro.gov.br" not in hosts

    def test_resolver_casa_por_conceito_sem_acento(self):
        assert [s.ref for s in CATALOGO.resolver("a populacao passou de 200 milhoes")] == ["ibge.populacao"]
        assert "bcb_sgs.selic_meta" in [s.ref for s in CATALOGO.resolver(["Selic"])]
        assert CATALOGO.resolver("número de empresas beneficiadas") == []

    def test_secundaria_nao_conta_como_independente(self):
        ipea = CATALOGO.serie("ipea.selic_over_mensal")
        assert CATALOGO.origem_independente(ipea) == "bcb_sgs"  # primaria_de
        ipca_bcb = CATALOGO.serie("bcb_sgs.ipca_12m")
        assert CATALOGO.origem_independente(ipca_bcb) == "ibge"
        # BCB×IPEA para o IPCA seria "duas fontes", mas é UMA origem: o IBGE
        assert CATALOGO.independentes([ipca_bcb, CATALOGO.serie("bcb_sgs.ipca_mensal")]) == {"ibge"}

    def test_serie_desconhecida_e_erro_com_lista(self):
        with pytest.raises(ValueError, match="não catalogada"):
            CATALOGO.serie("bcb_sgs.inventada")

    def test_normalizar(self):
        assert normalizar("  Inflação   Acumulada ") == "inflacao acumulada"


class TestValidacaoDoCatalogo:
    def _catalogo(self, tmp_path, **sobrescreve):
        base = yaml.safe_load(CATALOGO_PATH.read_text(encoding="utf-8"))
        bcb = base["fontes"]["bcb_sgs"]
        fontes = {"bcb_sgs": bcb, "ibge": base["fontes"]["ibge"]}
        for caminho, valor in sobrescreve.items():
            alvo = fontes
            partes = caminho.split(".")
            for parte in partes[:-1]:
                alvo = alvo[parte]
            if valor is None:
                alvo.pop(partes[-1], None)
            else:
                alvo[partes[-1]] = valor
        p = tmp_path / "catalogo.yml"
        p.write_text(yaml.safe_dump({"versao": 1, "fontes": fontes}, allow_unicode=True), encoding="utf-8")
        return p

    def test_chave_com_cara_de_valor_e_recusada(self, tmp_path):
        with pytest.raises(ValueError, match="NOME de uma variável"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.chave": "sk-abc123"}))

    def test_natureza_desconhecida(self, tmp_path):
        with pytest.raises(ValueError, match="natureza"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.natureza": "blog"}))

    def test_habilitada_sem_adaptador(self, tmp_path):
        with pytest.raises(ValueError, match="adaptador"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.adaptador": "scraping"}))

    def test_primaria_de_fantasma(self, tmp_path):
        with pytest.raises(ValueError, match="primaria_de"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.series.ipca_12m.primaria_de": "fmi"}))

    def test_serie_sem_conceitos(self, tmp_path):
        with pytest.raises(ValueError, match="conceitos"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.series.selic_meta.conceitos": []}))

    def test_secundaria_sem_uso(self, tmp_path):
        with pytest.raises(ValueError, match="uso"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.primaria": False}))

    def test_host_com_esquema_ou_caminho(self, tmp_path):
        with pytest.raises(ValueError, match="host"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.host": "https://api.bcb.gov.br/dados"}))

    def test_sem_vies_declarado(self, tmp_path):
        with pytest.raises(ValueError, match="vies_declarado"):
            carregar_catalogo(self._catalogo(tmp_path, **{"bcb_sgs.vies_declarado": None}))


# ── cliente: a fronteira ──────────────────────────────────────────────────────

class TestAllowlistNoTransporte:
    def test_host_fora_e_recusado_antes_do_transporte_interno(self):
        interno, chamadas = _transporte({})
        permitido = TransportePermitido(frozenset({"api.bcb.gov.br"}), interno)
        with httpx.Client(transport=permitido) as c:
            with pytest.raises(HostNaoPermitido):
                c.get("https://evil.example/x")
        assert chamadas == [] and permitido.recusados == ["evil.example"]

    def test_redirect_para_outro_host_e_recusado(self, tmp_path):
        def bcb(request):
            return httpx.Response(302, headers={"location": "https://evil.example/dados"})
        res, chamadas = _consultar(tmp_path, {"api.bcb.gov.br": bcb}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        assert not res.ok and res.erro.startswith("host recusado")
        assert [r.url.host for r in chamadas] == ["api.bcb.gov.br"]  # o segundo nunca saiu


class TestConsultarSerie:
    def test_bcb_por_intervalo_explicito(self, tmp_path):
        res, chamadas = _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        assert res.ok and len(res.observacoes) == 5
        assert res.observacoes[0] == Observacao("2025-03-01", 13.25)
        assert res.ultima.data == "2025-03-05"
        url = str(chamadas[0].url)
        assert "dataInicial=01%2F03%2F2025" in url and "dataFinal=05%2F03%2F2025" in url
        assert "ultimos" not in url
        assert res.url == url and res.data_consulta == AGORA.isoformat()

    def test_ibge_anos_explicitos_e_ano_vazio_nao_e_erro(self, tmp_path):
        res, chamadas = _consultar(tmp_path, {"servicodados.ibge.gov.br": IBGE_6579}, "ibge.populacao", date(2020, 1, 1), date(2024, 12, 31))
        assert res.ok and res.observacoes == [Observacao("2024-01-01", 212583750.0)]
        assert "/periodos/2020%7C2021%7C2022%7C2023%7C2024/" in str(chamadas[0].url) or "/periodos/2020|2021|2022|2023|2024/" in str(chamadas[0].url)
        vazio, _ = _consultar(tmp_path, {"servicodados.ibge.gov.br": []}, "ibge.populacao", date(2023, 1, 1), date(2023, 12, 31))
        assert vazio.ok and vazio.ultima is None

    def test_ipea_recorta_no_cliente(self, tmp_path):
        res, _ = _consultar(tmp_path, {"www.ipeadata.gov.br": IPEA_VALORES}, "ipea.selic_over_mensal", date(2025, 1, 1), date(2025, 3, 31))
        assert [o.data for o in res.observacoes] == ["2025-02-01", "2025-03-01"]

    def test_html_com_status_200_e_erro_declarado(self, tmp_path):
        def bcb(request):
            return httpx.Response(200, text=BCB_HTML, headers={"content-type": "text/html"})
        res, _ = _consultar(tmp_path, {"api.bcb.gov.br": bcb}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        assert not res.ok and "não é JSON" in res.erro

    def test_http_500_e_rede_viram_erro_nunca_excecao(self, tmp_path):
        res, _ = _consultar(tmp_path, {"api.bcb.gov.br": lambda r: httpx.Response(500)}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        assert res.erro == "HTTP 500 em api.bcb.gov.br"

        def cai(request):
            raise httpx.ConnectError("boom")
        res, _ = _consultar(tmp_path, {"api.bcb.gov.br": cai}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        assert res.erro.startswith("rede: ConnectError")

    def test_fonte_desabilitada_nao_toca_a_rede(self, tmp_path):
        bruto = yaml.safe_load(CATALOGO_PATH.read_text(encoding="utf-8"))
        bcb = bruto["fontes"]["bcb_sgs"]
        bcb["habilitada"] = False
        p = tmp_path / "c.yml"
        p.write_text(yaml.safe_dump({"versao": 1, "fontes": {"bcb_sgs": bcb, "ibge": bruto["fontes"]["ibge"]}}, allow_unicode=True), encoding="utf-8")
        cat = carregar_catalogo(p)
        assert "api.bcb.gov.br" not in cat.hosts_permitidos
        transport, chamadas = _transporte({"api.bcb.gov.br": BCB_432})
        res = consultar_serie("bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5), catalogo=cat, transport=transport, cache_dir=None)
        assert "não habilitada" in res.erro and chamadas == []

    def test_chave_ausente_nao_toca_a_rede_e_nao_vaza_valor(self, tmp_path):
        # Um catálogo mínimo com fonte habilitada que exige chave.
        bruto = yaml.safe_load(CATALOGO_PATH.read_text(encoding="utf-8"))
        bcb = bruto["fontes"]["bcb_sgs"]
        bcb["chave"] = "FONTE_TESTE_KEY"
        p = tmp_path / "c.yml"
        p.write_text(yaml.safe_dump({"versao": 1, "fontes": {"bcb_sgs": bcb, "ibge": bruto["fontes"]["ibge"]}}, allow_unicode=True), encoding="utf-8")
        cat = carregar_catalogo(p)
        transport, chamadas = _transporte({"api.bcb.gov.br": BCB_432})
        res = consultar_serie("bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5), catalogo=cat, transport=transport, cache_dir=None, ambiente={})
        assert not res.ok and "FONTE_TESTE_KEY" in res.erro and chamadas == []
        ok = consultar_serie("bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5), catalogo=cat, transport=transport, cache_dir=None, ambiente={"FONTE_TESTE_KEY": "segredo-xyz"})
        assert ok.ok and "segredo-xyz" not in json.dumps(ok.__dict__, default=str)

    def test_intervalo_invertido(self, tmp_path):
        res, chamadas = _consultar(tmp_path, {}, "bcb_sgs.selic_meta", date(2025, 3, 5), date(2025, 3, 1))
        assert "invertido" in res.erro and chamadas == []


class TestCache:
    def test_segunda_consulta_vem_do_cache(self, tmp_path):
        res1, c1 = _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        res2, c2 = _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        assert len(c1) == 1 and c2 == []
        assert res2.do_cache and res2.observacoes == res1.observacoes and res2.url == res1.url

    def test_ttl_vencido_volta_a_rede(self, tmp_path):
        _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        res, chamadas = _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5), agora=AGORA + timedelta(hours=25))
        assert len(chamadas) == 1 and not res.do_cache

    def test_erro_nao_e_cacheado(self, tmp_path):
        _consultar(tmp_path, {"api.bcb.gov.br": lambda r: httpx.Response(500)}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        res, chamadas = _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5))
        assert res.ok and len(chamadas) == 1

    def test_cache_desligado(self, tmp_path):
        _, c1 = _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5), cache_dir=None)
        _, c2 = _consultar(tmp_path, {"api.bcb.gov.br": BCB_432}, "bcb_sgs.selic_meta", date(2025, 3, 1), date(2025, 3, 5), cache_dir=None)
        assert len(c1) == len(c2) == 1


# ── contexto pré-registrado ───────────────────────────────────────────────────

def _consultar_falso(valores: dict, registro: list):
    """Simula a fronteira: `valores[ref]` é lista de Observacao, um erro (str)
    ou None (sem observação). Registra (ref, inicio, fim) de cada chamada."""
    def consultar(serie, inicio, fim, **kw):
        registro.append((serie.ref, inicio, fim))
        v = valores.get(serie.ref)
        res = Observacoes(ref=serie.ref, inicio=inicio.isoformat(), fim=fim.isoformat(), url=f"https://x/{serie.ref}", data_consulta=AGORA.isoformat())
        if isinstance(v, str):
            res.erro = v
        elif v:
            res.observacoes = list(v)
        return res
    return consultar


VALORES = {
    "bcb_sgs.selic_meta": [Observacao("2025-03-10", 13.25)],
    "bcb_sgs.ipca_12m": [Observacao("2025-02-01", 5.06)],
    "ibge.populacao": [Observacao("2021-01-01", 213317639.0), Observacao("2024-01-01", 212583750.0)],
    "bcb_sgs.cambio_usd_mensal": [Observacao("2025-02-01", 5.7656)],
}


class TestPlano:
    def test_sempre_mais_por_tema_sem_duplicar(self):
        refs, motivo = planejar(PLANO, ["Energia, Recursos Hídricos e Minerais"], ["ZIL-MIN"])
        assert refs == list(PLANO.sempre) + ["bcb_sgs.cambio_usd_mensal"]
        assert "por tema" in motivo

    def test_tema_sem_series_so_a_base(self):
        refs, motivo = planejar(PLANO, ["Saúde"], [])
        assert refs == list(PLANO.sempre) and "nenhuma série por tema" in motivo

    def test_plano_com_referencia_fantasma_falha_na_carga(self, tmp_path):
        (tmp_path / "p.yml").write_text("sempre: [bcb_sgs.selic_meta, fmi.pib]\npor_tema: {}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="fmi.pib"):
            carregar_plano("p", diretorio=tmp_path, catalogo=CATALOGO)

    def test_toda_chave_do_plano_e_tema_ou_categoria_plausivel(self):
        for chave in PLANO.por_tema:
            assert chave.startswith("ZIL-") or chave[0].isupper(), chave


class TestVigencia:
    def test_diaria_ate_a_ancora(self):
        assert fim_vigente(date(2025, 3, 10), "diaria") == date(2025, 3, 10)

    def test_mensal_ate_o_mes_anterior(self):
        assert fim_vigente(date(2025, 3, 10), "mensal") == date(2025, 2, 28)
        assert fim_vigente(date(2025, 1, 1), "mensal") == date(2024, 12, 31)

    def test_anual_ate_o_ano_anterior(self):
        assert fim_vigente(date(2025, 3, 10), "anual") == date(2024, 12, 31)

    def test_montar_contexto_consulta_so_o_que_ja_estava_publicado(self):
        registro = []
        montar_contexto(ancora="2025-03-10", temas_oficiais=["ZIL-MIN"], categorias_zil=["ZIL-MIN"], plano=PLANO, catalogo=CATALOGO, consultar=_consultar_falso(VALORES, registro))
        fins = {ref: fim for ref, _, fim in registro}
        assert fins["bcb_sgs.selic_meta"] == date(2025, 3, 10)
        assert fins["bcb_sgs.ipca_12m"] == date(2025, 2, 28)
        assert fins["ibge.populacao"] == date(2024, 12, 31)


class TestContexto:
    def _ctx(self, valores=VALORES, temas=("ZIL-MIN",), ancora="2025-03-10"):
        return montar_contexto(ancora=ancora, temas_oficiais=list(temas), plano=PLANO, catalogo=CATALOGO, consultar=_consultar_falso(valores, []))

    def test_linhas_com_proveniencia_em_portugues(self):
        texto = self._ctx().para_prompt()
        assert "13,25% a.a. em 10/03/2025 · BCB SGS 432" in texto
        assert "5,06% em 02/2025 · BCB SGS 13522 (dado primário do IBGE)" in texto
        assert "212.583.750 pessoas em 2024 · IBGE 6579 9324 N1" in texto and "sujeito a revisão" in texto
        assert "5,77 R$/US$" in texto
        assert "consultado em 2026-10-21" in texto
        assert "Use APENAS os números acima" in texto
        assert "10/03/2025" in texto.splitlines()[1]

    def test_ultima_observacao_dentro_da_janela(self):
        ctx = self._ctx()
        pop = next(ln for ln in ctx.linhas if ln.ref == "ibge.populacao")
        assert pop.data == "2024-01-01" and pop.valor == 212583750.0

    def test_lacuna_declarada_para_erro_e_para_vazio(self):
        valores = dict(VALORES, **{"bcb_sgs.ipca_12m": "HTTP 500 em api.bcb.gov.br", "ibge.populacao": None})
        ctx = self._ctx(valores)
        assert dict(ctx.lacunas) == {"bcb_sgs.ipca_12m": "HTTP 500 em api.bcb.gov.br", "ibge.populacao": "sem observação entre 2020-01-01 e 2024-12-31"}
        texto = ctx.para_prompt()
        assert "Não obtidos:" in texto and "bcb_sgs.ipca_12m: HTTP 500" in texto
        assert not ctx.vazio

    def test_sem_ancora_e_erro(self):
        with pytest.raises(ValueError, match="âncora"):
            self._ctx(ancora="")

    def test_hash_cobre_conteudo_e_nao_a_data_da_consulta(self):
        a = self._ctx()
        b = self._ctx()
        b.linhas[0].data_consulta = "2030-01-01T00:00:00+00:00"
        b.linhas[0].url = "https://outra"
        assert a.hash == b.hash
        c = self._ctx(dict(VALORES, **{"bcb_sgs.selic_meta": [Observacao("2025-03-10", 14.25)]}))
        assert a.hash != c.hash

    def test_texto_do_erro_nao_entra_no_hash(self):
        x = self._ctx(dict(VALORES, **{"ibge.populacao": "rede: ConnectTimeout"}))
        y = self._ctx(dict(VALORES, **{"ibge.populacao": "HTTP 503 em servicodados.ibge.gov.br"}))
        assert x.hash == y.hash

    def test_evidencias_carregam_url_data_e_vintage(self):
        ev = self._ctx().evidencias()
        assert ev["ancora"] == "2025-03-10" and ev["hash"] and ev["plano_hash"] == PLANO.hash and ev["catalogo_hash"] == CATALOGO.hash
        pop = next(ln for ln in ev["linhas"] if ln["ref"] == "ibge.populacao")
        assert pop["url"] and pop["data_consulta"] and pop["revisavel"] is True
        ipca = next(ln for ln in ev["linhas"] if ln["ref"] == "bcb_sgs.ipca_12m")
        assert ipca["primaria_de"] == "ibge"


# ── integração com a explicação: informação simétrica ────────────────────────

class TestContextoNaExplicacao:
    def _insumos_com_contexto(self):
        from tests.unit.test_explicacao_harness import CASOS, _insumos
        caso = CASOS["tema-ausente"]
        ins = _insumos(caso)
        ctx = montar_contexto(ancora="2025-03-10", temas_oficiais=[], plano=PLANO, catalogo=CATALOGO, consultar=_consultar_falso(VALORES, []))
        ins.contexto_economico = ctx.para_prompt()
        ins.contexto_hash = ctx.hash
        ins.contexto_evidencias = ctx.evidencias()
        return caso, ins, ctx

    def test_quem_declara_o_insumo_recebe_o_mesmo_bloco_e_quem_nao_declara_nao_recebe(self):
        from apps.workers.explicacao.pipeline import montar_prompt_lente
        from tests.unit.test_explicacao_harness import AGENTES
        _, ins, ctx = self._insumos_com_contexto()
        bloco = ctx.para_prompt()
        declaram = [a for a in AGENTES.values() if a.participa("lente") and "contexto_economico" in a.insumos]
        assert declaram, "pelo menos o economista declara contexto_economico"
        for a in AGENTES.values():
            if not a.participa("lente"):
                continue
            prompt = montar_prompt_lente(a, ins)
            if a in declaram:
                assert bloco in prompt, a.nome
            else:
                assert "CONTEXTO ECONÔMICO" not in prompt, a.nome

    def test_hash_e_evidencias_chegam_ao_resultado(self):
        from apps.workers.explicacao import explicar
        from tests.unit.test_explicacao_harness import AGENTES, PIPELINE, _consultar_simulado
        caso, ins, ctx = self._insumos_com_contexto()
        res = explicar(ins, PIPELINE, AGENTES, _consultar_simulado(caso))
        assert res.metricas["contexto_hash"] == ctx.hash
        assert res.contexto == ctx.evidencias()

    def test_sem_contexto_fica_registrado_como_ausente(self):
        from apps.workers.explicacao import explicar
        from tests.unit.test_explicacao_harness import AGENTES, CASOS, PIPELINE, _consultar_simulado, _insumos
        caso = CASOS["tema-ausente"]
        res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
        assert res.metricas["contexto_hash"] is None and res.contexto is None

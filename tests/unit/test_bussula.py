"""Bússola ZIL: o YAML real valida, e o progresso respeita a direção.

Antes não havia teste nenhum aqui, e a barra de progresso aparecia cheia
para o indicador mais distante da meta (fertilizantes: 87% importado, meta
60%), porque dividia valor por meta sem saber que menor é melhor.
"""

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from routers.bussula import _DATA_FILE, carregar_indicadores  # noqa: E402
from schemas.bussula import Indicador  # noqa: E402

TAXONOMIA = REPO_ROOT / "data" / "taxonomia" / "categorias.yml"


def _base(**kw) -> dict:
    d = dict(
        codigo="BUSSULA-TST-01", nome="Teste", categoria="ZIL-FER", valor_atual=87, unidade="%",
        direcao="menor_melhor", tendencia="estavel", meta=60, prazo=2030, meta_origem=None,
        fonte="X", natureza_fonte="estatal", fonte_url="https://x", fonte_dataset=None,
        ultima_atualizacao="2024-12", validacao="nao-validado",
    )
    d.update(kw)
    return d


class TestDadoReal:
    def test_yaml_real_carrega_e_valida(self):
        indicadores = carregar_indicadores(_DATA_FILE)
        assert len(indicadores) >= 4

    def test_codigos_unicos(self):
        codigos = [i.codigo for i in carregar_indicadores(_DATA_FILE)]
        assert len(codigos) == len(set(codigos))

    def test_categoria_existe_na_taxonomia(self):
        cats = yaml.safe_load(TAXONOMIA.read_text(encoding="utf-8"))
        conhecidas = {c["codigo"] for c in cats["categorias"]} if isinstance(cats, dict) and "categorias" in cats else set(cats)
        for i in carregar_indicadores(_DATA_FILE):
            assert i.categoria in conhecidas, i.codigo

    def test_prazo_nao_e_anterior_ao_dado(self):
        for i in carregar_indicadores(_DATA_FILE):
            if i.prazo is not None:
                assert i.prazo >= int(i.ultima_atualizacao[:4]), i.codigo

    def test_arquivo_ausente_devolve_vazio(self, tmp_path, caplog):
        assert carregar_indicadores(tmp_path / "nao-existe.yml") == []
        assert "não existe" in caplog.text


class TestProgresso:
    def test_menor_melhor_sem_base_nao_tem_barra(self):
        # 87% importado com meta de 60%: sem valor de base não há "caminho
        # percorrido" a mostrar; o que há é a distância, 27 pontos.
        i = Indicador(**_base())
        assert i.progresso_pct is None
        assert i.distancia_meta == 27

    def test_maior_melhor_sem_base_nao_tem_barra(self):
        # 83% com meta 90%: valor/meta (92%) tratava zero como ponto de partida.
        i = Indicador(**_base(direcao="maior_melhor", valor_atual=83, meta=90))
        assert i.progresso_pct is None
        assert i.distancia_meta == 7

    def test_com_base_mede_o_caminho_nos_dois_sentidos(self):
        sobe = Indicador(**_base(direcao="maior_melhor", valor_atual=83, meta=90, base={"valor": 76, "ano": 2019}))
        assert sobe.progresso_pct == 50
        desce = Indicador(**_base(valor_atual=75, meta=50, base={"valor": 85, "ano": 2021}))
        assert desce.progresso_pct == 29

    def test_retrocesso_abaixo_da_base_da_zero(self):
        # Fertilizantes com a base e a meta do PNF: 86,8% contra base 85%.
        i = Indicador(**_base(valor_atual=86.8, meta=50, base={"valor": 85, "ano": 2021}))
        assert i.progresso_pct == 0 and not i.meta_atingida

    def test_meta_atingida(self):
        i = Indicador(**_base(direcao="maior_melhor", valor_atual=95, meta=90, base={"valor": 80, "ano": 2020}))
        assert i.progresso_pct == 100 and i.meta_atingida
        j = Indicador(**_base(valor_atual=50, meta=60))
        assert j.meta_atingida and j.distancia_meta == 0

    def test_base_igual_a_meta_nao_divide_por_zero(self):
        assert Indicador(**_base(meta=60, base={"valor": 60, "ano": 2020})).progresso_pct is None

    def test_sem_meta_sem_progresso(self):
        i = Indicador(**_base(meta=None, prazo=None))
        assert i.progresso_pct is None and i.distancia_meta is None and not i.meta_atingida and not i.meta_provisoria

    def test_meta_sem_origem_e_provisoria(self):
        assert Indicador(**_base()).meta_provisoria
        assert not Indicador(**_base(meta_origem={"nome": "PNF 2050", "url": "https://x"})).meta_provisoria

    @pytest.mark.parametrize("campo,valor", [("direcao", "sobe"), ("codigo", "FER-1"), ("ultima_atualizacao", "2024"), ("natureza_fonte", "blog")])
    def test_valores_fora_do_vocabulario_sao_recusados(self, campo, valor):
        with pytest.raises(Exception):
            Indicador(**_base(**{campo: valor}))


class TestEndpoints:
    def test_lista_traz_campos_calculados(self, client):
        r = client.get("/bussula")
        assert r.status_code == 200
        fer = next(m for m in r.json() if m["codigo"] == "BUSSULA-FER-01")
        assert fer["distancia_meta"] == 27 and fer["meta_provisoria"] is True

    def test_nenhum_indicador_publicado_tem_barra_sem_base(self, client):
        for m in client.get("/bussula").json():
            if m.get("base") is None:
                assert m["progresso_pct"] is None, m["codigo"]

    def test_404(self, client):
        assert client.get("/bussula/BUSSULA-XXX-99").status_code == 404

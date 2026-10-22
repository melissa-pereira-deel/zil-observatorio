"""Harness do pipeline de explicação — Fase 1, sem rede.

`consultar` é substituído por uma função que lê `respostas_simuladas` do caso
construído. O que se testa aqui é o que NÃO depende do modelo: roteamento,
blindagem, validação de tamanho, detecção de entidade fabricada, preservação
de dissenso, declaração de lacuna. Se a explicação é boa, é a Fase 2.
"""

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.agentes.blindagem import ABRE, FECHA  # noqa: E402
from apps.workers.explicacao import Insumos, explicar  # noqa: E402
from apps.workers.explicacao.agentes import HERDADOS, carregar_agentes  # noqa: E402
from apps.workers.explicacao.coleta import Autor, FichaFatos, Tramitacao  # noqa: E402
from apps.workers.explicacao.extracao import TextoExtraido, separar_secoes  # noqa: E402
from apps.workers.explicacao.pipeline import montar_prompt_lente  # noqa: E402
from apps.workers.explicacao.roteamento import carregar_pipeline_por_nome, rotear  # noqa: E402
from apps.workers.explicacao.schema import LIMITES  # noqa: E402

CASOS = {
    c["id"]: c
    for c in yaml.safe_load(
        (REPO_ROOT / "data" / "explicacao" / "casos" / "construidos.yml").read_text(encoding="utf-8")
    )["casos"]
}
AGENTES = carregar_agentes()
PIPELINE = carregar_pipeline_por_nome("v1")

_DIDATICO_OK = ("x" * 300)
_DETALHADO_OK = ("y" * 600)


def _ficha(caso: dict) -> FichaFatos:
    f = caso["ficha"]
    return FichaFatos(
        fonte="camara", fonte_id=caso["id"], tipo=f["tipo"], numero=f["numero"], ano=f["ano"],
        ementa=f["ementa"], situacao=f.get("situacao", ""), data_apresentacao=f.get("data_apresentacao", ""),
        autores=[Autor(a["nome"], a["tipo"], a.get("partido"), a.get("uf")) for a in f.get("autores", [])],
        tramitacoes=[Tramitacao(t["data"], t["orgao"], t["descricao"]) for t in f.get("tramitacoes", [])],
        temas_oficiais=list(f.get("temas_oficiais", [])),
        origens={"proposicao": "sim", "autores": "sim", "tramitacoes": "sim", "relacionadas": "sim", "temas_oficiais": "sim"},
    )


def _texto(caso: dict) -> TextoExtraido:
    if caso.get("texto_indisponivel"):
        return TextoExtraido(texto="", metodo="indisponivel", erro="sem urlInteiroTeor")
    disp = caso.get("dispositivo", "")
    just = caso.get("justificacao", "")
    texto = disp + ("\n\nJUSTIFICAÇÃO\n" + just if just else "")
    d, j = separar_secoes(texto)
    return TextoExtraido(texto=texto, metodo="pdf_nativo", paginas=1, chars_por_pagina=len(texto), dispositivo=d, justificacao=j)


def _insumos(caso: dict) -> Insumos:
    return Insumos(ficha=_ficha(caso), texto=_texto(caso), categorias_zil=list(caso.get("categorias_zil", [])))


def _consultar_simulado(caso: dict):
    """Devolve as respostas do caso; para agentes sem resposta simulada, uma
    lente que não tem nada a dizer, e uma síntese válida e sem entidades."""
    sims = caso.get("respostas_simuladas", {})
    chamadas: list[str] = []

    def consultar(agente, prompt):
        chamadas.append(agente.nome)
        if agente.nome in sims:
            return dict(sims[agente.nome])
        if agente.participa("sintese"):
            return {
                "resumo_didatico": _DIDATICO_OK,
                "resumo_detalhado": _DETALHADO_OK,
                "analise": {"causas_raizes": [], "dependencias": [], "fatores_limitantes": [], "dimensoes": {}},
                "dissensos": [],
            }
        return {"nada_a_dizer": True, "afirmacoes": []}

    consultar.chamadas = chamadas
    return consultar


# ── carga ─────────────────────────────────────────────────────────────────────

class TestCarga:
    def test_pipeline_v1_tem_todos_os_agentes(self):
        exigidos = PIPELINE.todas_as_lentes + (PIPELINE.contraditor, PIPELINE.sintetizador)
        assert all(n in AGENTES for n in exigidos), [n for n in exigidos if n not in AGENTES]

    def test_herdados_mantem_o_hash_do_painel(self):
        from apps.workers.panel.agentes import carregar_painel
        painel = {a.nome: a for a in carregar_painel()}
        for n in HERDADOS:
            assert AGENTES[n].hash_instrucoes == painel[n].hash_instrucoes
            assert AGENTES[n].etapas == ("lente",)

    def test_industrial_nao_participa(self):
        assert "industrial" not in AGENTES
        assert "industrial" not in PIPELINE.todas_as_lentes

    def test_todo_agente_tem_modelo_pinado(self):
        assert all(a.modelo for a in AGENTES.values())

    def test_lente_nao_le_pareceres_dos_outros(self):
        for a in AGENTES.values():
            if a.participa("lente"):
                assert "pareceres_dos_outros" not in a.insumos, a.nome

    def test_leitor_nao_recebe_a_justificacao(self):
        assert "justificacao" not in AGENTES["leitor"].insumos
        assert "justificacao" in AGENTES["contraditor"].insumos


# ── roteamento ────────────────────────────────────────────────────────────────

class TestRoteamento:
    def test_sem_tema_nem_categoria_roda_todas(self):
        lentes, motivo = rotear([], [], PIPELINE)
        assert set(lentes) == set(PIPELINE.todas_as_lentes)
        assert "todas" in motivo

    def test_tema_liga_a_lente_condicional(self):
        lentes, _ = rotear(["Saúde"], [], PIPELINE)
        assert "saude" in lentes and "ambiental" not in lentes

    def test_categoria_zil_tambem_roteia(self):
        lentes, _ = rotear([], ["ZIL-MIN"], PIPELINE)
        assert "ambiental" in lentes

    def test_tema_nao_mapeado_so_roda_as_fixas(self):
        lentes, _ = rotear(["Homenagens e Datas Comemorativas"], [], PIPELINE)
        assert lentes == list(PIPELINE.lentes_fixas)

    def test_fixas_sempre_entram(self):
        for temas in ([], ["Saúde"], ["Comunicações"]):
            lentes, _ = rotear(temas, [], PIPELINE)
            assert all(f in lentes for f in PIPELINE.lentes_fixas)


# ── casos construídos ─────────────────────────────────────────────────────────

class TestDissensoPlantado:
    def test_lentes_em_conflito_sao_roteadas(self):
        caso = CASOS["dissenso-plantado"]
        res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
        lentes = res.analise.lentes
        assert all(nome in lentes for nome in caso["esperado"]["lentes_incluem"])

    def test_dissenso_sobrevive_na_sintese(self):
        caso = CASOS["dissenso-plantado"]
        res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
        assert res.status == "pronto", res.problemas
        assert res.analise.dissensos
        d = res.analise.dissensos[0]
        assert {d.lente_a, d.lente_b} == {"ambiental", "economista"}

    def test_sintese_que_apaga_o_dissenso_e_rejeitada(self):
        caso = dict(CASOS["dissenso-plantado"])
        sims = dict(caso["respostas_simuladas"])
        sint = dict(sims["sintetizador"])
        sint["dissensos"] = []
        sims["sintetizador"] = sint
        caso["respostas_simuladas"] = sims
        res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
        assert res.status == "invalido"
        assert any("sem dissensos" in p for p in res.problemas)


class TestIscaDeEntidade:
    def test_sintese_que_cai_na_isca_e_rejeitada(self):
        caso = CASOS["isca-de-entidade"]
        res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
        assert res.status == "invalido"
        problema = " ".join(res.problemas)
        for proibida in caso["esperado"]["entidades_proibidas"]:
            assert proibida in problema, proibida
        assert res.metricas["entidades_fabricadas"] >= 3

    def test_sintese_honesta_passa(self):
        caso = dict(CASOS["isca-de-entidade"])
        caso["respostas_simuladas"] = {}  # síntese padrão, sem entidades
        res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
        assert res.metricas["entidades_fabricadas"] == 0


class TestTemaAusente:
    def test_todas_as_lentes_rodam(self):
        caso = CASOS["tema-ausente"]
        c = _consultar_simulado(caso)
        res = explicar(_insumos(caso), PIPELINE, AGENTES, c)
        assert set(res.analise.lentes) == set(PIPELINE.todas_as_lentes)
        for nome in PIPELINE.todas_as_lentes:
            assert nome in c.chamadas


class TestJustificacaoHostil:
    def test_marca_forjada_nao_fecha_o_bloco(self):
        caso = CASOS["justificacao-hostil"]
        ins = _insumos(caso)
        prompt = montar_prompt_lente(AGENTES["contraditor"], ins)  # contraditor recebe a justificação
        assert prompt.count(ABRE) == 1 and prompt.count(FECHA) == 1
        corpo = prompt[prompt.index(ABRE) + len(ABRE):prompt.index(FECHA)]
        assert "<<<" not in corpo
        assert "Ignore as instruções" in corpo  # o conteúdo hostil está lá, mas dentro do bloco

    def test_sinal_de_injecao_chega_ao_resultado(self):
        caso = CASOS["justificacao-hostil"]
        res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
        assert res.houve_injecao
        assert res.metricas["injecao_detectada"] is True


class TestSemTextoIntegral:
    def test_prompt_do_leitor_declara_a_ausencia(self):
        caso = CASOS["sem-texto-integral"]
        ins = _insumos(caso)
        assert ins.texto.metodo == "indisponivel"
        prompt = montar_prompt_lente(AGENTES["leitor"], ins)
        assert "não disponível" in prompt


class TestEmentaPrometeDemais:
    def test_leitor_recebe_dispositivo_e_nao_justificacao(self):
        caso = CASOS["ementa-promete-demais"]
        prompt = montar_prompt_lente(AGENTES["leitor"], _insumos(caso))
        assert "[DISPOSITIVO]" in prompt and "data center" in prompt
        assert "JUSTIFICAÇÃO DO AUTOR" not in prompt
        assert "marco para a soberania digital" not in prompt


# ── tamanho é contrato ────────────────────────────────────────────────────────

class TestReformulacao:
    def _caso_com_sintese(self, textos):
        caso = dict(CASOS["tema-ausente"])
        respostas = iter(textos)

        def consultar(agente, prompt):
            if agente.participa("sintese"):
                t = next(respostas)
                return {"resumo_didatico": t, "resumo_detalhado": _DETALHADO_OK,
                        "analise": {"dimensoes": {}}, "dissensos": []}
            return {"nada_a_dizer": True, "afirmacoes": []}

        return caso, consultar

    def test_curto_demais_pede_reformulacao_e_converge(self):
        caso, consultar = self._caso_com_sintese(["curto", _DIDATICO_OK])
        res = explicar(_insumos(caso), PIPELINE, AGENTES, consultar)
        assert res.status == "pronto"
        assert res.metricas["reformulacoes"] == 1

    def test_nao_converge_apos_o_maximo_vira_invalido(self):
        caso, consultar = self._caso_com_sintese(["curto"] * (PIPELINE.max_reformulacoes + 1))
        res = explicar(_insumos(caso), PIPELINE, AGENTES, consultar)
        assert res.status == "invalido"
        assert res.resumo_didatico is None
        assert any("não convergiu" in p for p in res.problemas)

    def test_limites_sao_os_pedidos(self):
        assert LIMITES == {"resumo_didatico": (240, 640), "resumo_detalhado": (480, 2480)}


# ── lentes indisponíveis ──────────────────────────────────────────────────────

def test_todas_as_lentes_falhando_nao_sintetiza():
    caso = CASOS["tema-ausente"]

    def consultar(agente, prompt):
        return {"error": "ANTHROPIC_API_KEY não configurado"}

    res = explicar(_insumos(caso), PIPELINE, AGENTES, consultar)
    assert res.status == "lentes_indisponiveis"
    assert res.resumo_didatico is None
    assert len(res.meta.erros) >= len(PIPELINE.todas_as_lentes)


def test_meta_registra_modelo_e_hash_de_cada_agente_usado():
    caso = CASOS["tema-ausente"]
    res = explicar(_insumos(caso), PIPELINE, AGENTES, _consultar_simulado(caso))
    usados = set(res.analise.lentes) | {PIPELINE.contraditor, PIPELINE.sintetizador}
    assert set(res.meta.hashes_instrucoes) == usados
    assert set(res.meta.modelos) == usados
    assert res.meta.concluido_em is not None

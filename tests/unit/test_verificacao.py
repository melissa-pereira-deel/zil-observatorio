"""Verificação de alegações (pipeline v2) — sem rede, sem chave.

Três fronteiras são substituídas: `consultar` (agentes sem ferramenta),
`consultar_ferramentas` (o verificador) e `consultar_dados` (as séries). O
que se prova é o que não depende do modelo: cegueira por assinatura,
ferramenta fechada, a conta prevalecendo sobre o julgamento, contradição que
sobrevive à síntese, e número sem origem reprovado.
"""

import inspect
import re
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.agentes.blindagem import ABRE, FECHA  # noqa: E402
from apps.workers.agentes.fronteira import consultar_com_ferramentas  # noqa: E402
from apps.workers.explicacao import explicar  # noqa: E402
from apps.workers.explicacao.agentes import carregar_proprios  # noqa: E402
from apps.workers.explicacao.revisao import numeros, numeros_sem_origem  # noqa: E402
from apps.workers.explicacao.roteamento import carregar_pipeline, carregar_pipeline_por_nome  # noqa: E402
from apps.workers.explicacao.schema import Afirmacao, Alegacao, ParecerLente, Verificacao  # noqa: E402
from apps.workers.explicacao import verificacao as vf  # noqa: E402
from apps.workers.fontes import Observacao, Observacoes, carregar_catalogo  # noqa: E402
from tests.unit.test_explicacao_harness import AGENTES, CASOS as CASOS_V1, PIPELINE as PIPELINE_V1, _insumos  # noqa: E402

CATALOGO = carregar_catalogo()
PIPELINE = carregar_pipeline_por_nome("v2")
CASOS = {
    c["id"]: c
    for c in yaml.safe_load(
        (REPO_ROOT / "data" / "explicacao" / "casos" / "verificacao.yml").read_text(encoding="utf-8")
    )["casos"]
}
_SINTESE_NEUTRA = {
    "resumo_didatico": "x" * 300,
    "resumo_detalhado": "y" * 600,
    "analise": {"dimensoes": {}},
    "dissensos": [],
}


# ── fronteiras falsas ─────────────────────────────────────────────────────────

def _trechos_do_prompt(prompt: str) -> dict[str, str]:
    corpo = prompt[prompt.index(ABRE) + len(ABRE):prompt.index(FECHA)]
    partes = re.split(r"\[(T\d{2})\]\n", corpo)[1:]
    return dict(zip(partes[0::2], partes[1::2]))


def _consultar(caso: dict, prompts: dict | None = None):
    sims = caso["respostas_simuladas"]

    def consultar(agente, prompt):
        if prompts is not None:
            prompts.setdefault(agente.nome, []).append(prompt)
        if agente.participa("extracao"):
            ids = _trechos_do_prompt(prompt)
            out = []
            for a in sims.get("extrator", {}).get("alegacoes", []):
                d = {k: v for k, v in a.items() if k != "trecho_contem"}
                d["trecho"] = next(t for t, x in ids.items() if a["trecho_contem"] in x)
                out.append(d)
            return {"alegacoes": out}
        if agente.nome in sims:
            return dict(sims[agente.nome])
        if agente.participa("sintese"):
            return dict(_SINTESE_NEUTRA)
        return {"nada_a_dizer": True, "afirmacoes": []}

    return consultar


def _ferramentas(caso: dict, log: list | None = None, resposta: dict | None = None):
    sims = caso["respostas_simuladas"].get("verificador", [])

    def consultar_ferramentas(agente, prompt, *, ferramentas, executor, registro):
        if log is not None:
            log.append({"prompt": prompt, "ferramentas": ferramentas})
        alvo = next(s for s in sims if s["alegacao_contem"] in prompt)
        for i, c in enumerate(alvo.get("chamadas", []), start=1):
            saida = executor(c["ferramenta"], dict(c["argumentos"]))
            registro.append({"rodada": i, "ferramenta": c["ferramenta"], "argumentos": c["argumentos"], "resultado": saida})
        return dict(resposta if resposta is not None else alvo["resposta"])

    return consultar_ferramentas


def _dados(caso: dict, log: list | None = None):
    def consultar_dados(serie, inicio, fim, **kw):
        if log is not None:
            log.append(serie.ref)
        obs = [
            Observacao(str(d), float(v))
            for d, v in caso.get("dados", {}).get(serie.ref, [])
            if inicio.isoformat() <= str(d) <= fim.isoformat()
        ]
        return Observacoes(ref=serie.ref, inicio=inicio.isoformat(), fim=fim.isoformat(),
                           url=f"https://x/{serie.ref}", data_consulta="2026-10-21T00:00:00+00:00", observacoes=obs)

    return consultar_dados


def _rodar(caso: dict, **kw):
    return explicar(
        _insumos(caso), PIPELINE, AGENTES, kw.pop("consultar", _consultar(caso)),
        consultar_ferramentas=kw.pop("consultar_ferramentas", _ferramentas(caso)),
        consultar_dados=kw.pop("consultar_dados", _dados(caso)),
        catalogo=kw.pop("catalogo", CATALOGO),
    )


def _vereditos(res) -> dict:
    return {v.alegacao.id: v.veredito for v in res.verificacoes}


# ── os seis casos construídos ─────────────────────────────────────────────────

@pytest.mark.parametrize("caso_id", sorted(CASOS))
def test_caso_construido(caso_id):
    caso = CASOS[caso_id]
    res = _rodar(caso)
    esperado = caso["esperado"]
    assert _vereditos(res) == esperado["vereditos"]
    assert res.status == esperado["status"], res.problemas
    if "fila_humana" in esperado:
        assert len(vf.fila_humana("camara", caso_id, res.verificacoes)) == esperado["fila_humana"]


class TestNumeroPlantado:
    def test_valor_encontrado_vem_da_observacao_consultada(self):
        v = _rodar(CASOS["numero-plantado"]).verificacoes[0]
        assert (v.ref, v.data_referencia, v.valor_encontrado) == ("bcb_sgs.selic_meta", "2024-12-31", 12.25)
        assert v.conferido_por == "codigo" and v.alegacao.origem == "justificacao"

    def test_conta_prevalece_sobre_o_modelo(self):
        caso = CASOS["numero-plantado"]
        resposta = dict(caso["respostas_simuladas"]["verificador"][0]["resposta"], veredito="confirmada")
        res = _rodar(caso, consultar_ferramentas=_ferramentas(caso, resposta=resposta))
        v = res.verificacoes[0]
        assert v.veredito == "contradita" and v.divergencia_verificador
        assert res.metricas["verificacao"]["divergencias_verificador"] == 1

    def test_modelo_nao_confirma_numero_que_o_codigo_nao_viu(self):
        caso = CASOS["numero-plantado"]
        resposta = dict(caso["respostas_simuladas"]["verificador"][0]["resposta"], data_referencia="2019-01-01")
        sem_chamadas = dict(caso, respostas_simuladas=dict(caso["respostas_simuladas"], verificador=[
            {"alegacao_contem": "Selic era de 25%", "chamadas": [], "resposta": resposta}]))
        v = _rodar(sem_chamadas).verificacoes[0]
        assert v.veredito == "inconclusiva" and "não conferido" in v.justificativa

    def test_sintese_que_omite_a_contradita_e_reprovada(self):
        caso = CASOS["numero-plantado"]
        sint = dict(caso["respostas_simuladas"]["sintetizador"], alegacoes_contraditas=[])
        c = dict(caso, respostas_simuladas=dict(caso["respostas_simuladas"], sintetizador=sint))
        res = _rodar(c)
        assert res.status == "invalido"
        assert any("contraditas omitidas" in p for p in res.problemas)

    def test_didatico_que_repete_o_numero_contradito_e_reprovado(self):
        caso = CASOS["numero-plantado"]
        sint = dict(caso["respostas_simuladas"]["sintetizador"])
        sint["resumo_didatico"] = sint["resumo_didatico"].strip() + " Com juros básicos de 25% ao ano, o crédito ficou proibitivo."
        c = dict(caso, respostas_simuladas=dict(caso["respostas_simuladas"], sintetizador=sint))
        res = _rodar(c)
        assert any("repete número contradito" in p for p in res.problemas)

    def test_sintese_recebe_a_obrigacao(self):
        caso = CASOS["numero-plantado"]
        prompts: dict = {}
        _rodar(caso, consultar=_consultar(caso, prompts))
        p = prompts["sintetizador"][0]
        assert "[VERIFICAÇÕES" in p and "CONTRADITA" in p and "alegacoes_contraditas" in p


class TestFerramentaFechada:
    def test_recusas_registradas_e_so_a_candidata_toca_os_dados(self):
        caso = CASOS["serie-inventada"]
        dados: list = []
        res = _rodar(caso, consultar_dados=_dados(caso, dados))
        v = res.verificacoes[0]
        assert len(v.recusas) == caso["esperado"]["recusas"]
        assert any("fora do catálogo" in r for r in v.recusas)
        assert any("fora das candidatas" in r for r in v.recusas)
        assert any("inexistente" in r for r in v.recusas)
        assert dados == caso["esperado"]["consultas_de_dados"]
        assert res.metricas["verificacao"]["recusas_ferramenta"] == 3

    def test_ferramenta_lista_so_as_candidatas(self):
        caso = CASOS["numero-plantado"]
        log: list = []
        _rodar(caso, consultar_ferramentas=_ferramentas(caso, log))
        ferramenta = log[0]["ferramentas"][0]
        assert ferramenta["name"] == "consultar_serie"
        assert ferramenta["input_schema"]["properties"]["ref"]["enum"] == ["bcb_sgs.selic_meta"]

    def test_executor_rejeita_datas_invalidas_e_janela_longa(self):
        ex = vf.Executor(CATALOGO, [CATALOGO.serie("bcb_sgs.selic_meta")], _dados({}))
        assert "inválidas" in ex("consultar_serie", {"ref": "bcb_sgs.selic_meta", "inicio": "ontem", "fim": "hoje"})["erro"]
        longa = ex("consultar_serie", {"ref": "bcb_sgs.selic_meta", "inicio": "1990-01-01", "fim": "2024-12-31"})
        assert "anos" in longa["erro"] and ex.consultas == []

    def test_sem_candidata_e_causal_nao_chamam_o_verificador(self):
        for caso_id in ("conceito-sem-fonte", "alegacao-causal"):
            log: list = []
            res = _rodar(CASOS[caso_id], consultar_ferramentas=_ferramentas(CASOS[caso_id], log))
            assert log == [], caso_id
            assert res.metricas["verificacao"]["chamadas_ferramenta"] == 0

    def test_vintage_em_serie_revisavel(self):
        v = _rodar(CASOS["vintage"]).verificacoes[0]
        assert v.veredito == "confirmada" and "revisável" in v.nota_vintage
        assert _rodar(CASOS["numero-correto"]).verificacoes[0].nota_vintage == ""


class TestCegueira:
    def test_assinaturas_nao_recebem_parecer(self):
        assert list(inspect.signature(vf.montar_prompt_extracao).parameters) == ["agente", "trechos"]
        assert list(inspect.signature(vf.montar_prompt_verificacao).parameters) == ["agente", "alegacao", "candidatas"]

    def test_prompt_de_extracao_nao_nomeia_lentes(self):
        pareceres = [
            ParecerLente(lente="economista", afirmacoes=[Afirmacao("economista", "inferencia", "A Selic estava em 10% em 2023.", "economica")]),
            ParecerLente(lente="ambiental", afirmacoes=[Afirmacao("ambiental", "inferencia", "O passivo dobrou desde 2015.", "ambiental")]),
        ]
        trechos = vf.montar_trechos(pareceres, "Parágrafo da justificação com uma alegação qualquer sobre o mundo.")
        prompt = vf.montar_prompt_extracao(AGENTES["extrator"], trechos)
        for nome in ("economista", "ambiental", "justificacao", "LENTE"):
            assert nome not in prompt

    def test_ordem_dos_trechos_nao_depende_da_origem(self):
        textos = ["Primeira afirmação sobre o mundo.", "Segunda afirmação sobre o mundo.", "Terceira afirmação sobre o mundo."]

        def pareceres(origens):
            return [ParecerLente(lente=o, afirmacoes=[Afirmacao(o, "inferencia", t, "publica")]) for o, t in zip(origens, textos)]

        a = vf.montar_trechos(pareceres(["jurista", "economista", "publicas"]), None)
        b = vf.montar_trechos(pareceres(["publicas", "jurista", "economista"]), None)
        assert [t.texto for t in a] == [t.texto for t in b]

    def test_trecho_desconhecido_e_descartado_nunca_atribuido(self):
        trechos = [vf.Trecho("T01", "texto", "justificacao")]
        alegs, erros = vf.parse_alegacoes({"alegacoes": [
            {"trecho": "T09", "texto": "x", "tipo": "factual", "conceito": "c"},
            {"trecho": "T01", "texto": "y", "tipo": "factual", "conceito": "c"},
        ]}, trechos)
        assert [a.origem for a in alegs] == ["justificacao"] and "T09" in erros[0]

    def test_agente_cego_nao_pode_ler_pareceres(self, tmp_path):
        bruto = yaml.safe_load((REPO_ROOT / "data" / "explicacao" / "agentes" / "extrator.yml").read_text(encoding="utf-8"))
        bruto["insumos"] = ["trechos_anonimos", "pareceres_dos_outros"]
        (tmp_path / "extrator.yml").write_text(yaml.safe_dump(bruto, allow_unicode=True), encoding="utf-8")
        with pytest.raises(ValueError, match="cegas"):
            carregar_proprios(tmp_path)


class TestTriangulacao:
    def _catalogo_com_duas_origens(self, tmp_path):
        bruto = yaml.safe_load((REPO_ROOT / "data" / "fontes" / "catalogo.yml").read_text(encoding="utf-8"))
        outra = {
            "sigla": "OUTRA", "nome": "Instituto independente", "host": "outra.example", "natureza": "academia",
            "primaria": True, "vies_declarado": "Fonte de teste com metodologia própria de estimativa populacional.",
            "adaptador": "ipea_odata", "habilitada": True,
            "series": {"populacao": {"descricao": "População estimada", "parametros": {"codigo": "X"}, "unidade": "pessoas",
                                     "frequencia": "anual", "revisavel": True, "conceitos": ["população"]}},
        }
        p = tmp_path / "c.yml"
        p.write_text(yaml.safe_dump({"versao": 1, "fontes": {"ibge": bruto["fontes"]["ibge"], "outra": outra}}, allow_unicode=True), encoding="utf-8")
        return carregar_catalogo(p)

    def test_origens_primarias_que_discordam_vao_para_a_fila(self, tmp_path):
        cat = self._catalogo_com_duas_origens(tmp_path)
        a = Alegacao(id="A01", texto="A população era de 213 milhões em 2021.", tipo="quantitativa",
                     conceito="população", trecho="T01", origem="justificacao", valor=213e6, periodo="2021")
        dados = {"ibge.populacao": [["2021-01-01", 213317639]], "outra.populacao": [["2021-01-01", 190000000]]}
        chamadas = [{"ferramenta": "consultar_serie", "argumentos": {"ref": r, "inicio": "2021-01-01", "fim": "2021-12-31"}} for r in dados]
        caso = {"dados": dados, "respostas_simuladas": {"verificador": [{"alegacao_contem": "213 milhões", "chamadas": chamadas,
                "resposta": {"veredito": "confirmada", "ref": "ibge.populacao", "data_referencia": "2021-01-01"}}]}}
        res = vf.verificar([a], agente=AGENTES["verificador"], catalogo=cat, consultar_ferramentas=_ferramentas(caso),
                           consultar_dados=_dados(caso), max_alegacoes=5)
        v = res.verificacoes[0]
        assert v.veredito == "fontes_divergentes" and v.requer_humano

    def test_limite_de_alegacoes(self):
        caso = CASOS["numero-correto"]
        alegs = [Alegacao(id=f"A{i}", texto="A inflação de 2024 fechou em 4,83%.", tipo="quantitativa", conceito="inflação",
                          trecho="T01", origem="x", valor=4.83, periodo="2024-12") for i in range(3)]
        res = vf.verificar(alegs, agente=AGENTES["verificador"], catalogo=CATALOGO, consultar_ferramentas=_ferramentas(caso),
                           consultar_dados=_dados(caso), max_alegacoes=2)
        assert [v.veredito for v in res.verificacoes][-1] == "nao_verificada_limite"


class TestComparacao:
    @pytest.mark.parametrize("alegado,encontrado,revisavel,esperado", [
        (13, 13.25, False, "confirmada"),       # arredondamento de quem fala
        (25, 12.25, False, "contradita"),
        (212e6, 212583750, True, "confirmada"),
        (4.83, 4.83, False, "confirmada"),
        (5.5, 4.83, False, "contradita"),
    ])
    def test_tolerancia(self, alegado, encontrado, revisavel, esperado):
        assert vf.comparar(alegado, encontrado, revisavel)[0] == esperado

    def test_arredondamento(self):
        assert vf.arredondamento(13) == 0.5
        assert vf.arredondamento(13.25) == pytest.approx(0.005)
        assert vf.arredondamento(212e6) == 0.5e6


class TestNumerosSemOrigem:
    def test_leitura_de_numeros_em_portugues(self):
        assert numeros("212 milhões, 3 mil e 1,5 bilhão; 1.234,5", so_quantidades=True) == [212e6, 3000, 1.5e9, 1234.5]
        assert numeros("PL 1001/2025 em 10/03/2025, art. 2º", so_quantidades=True) == []

    def test_numero_de_memoria_e_detectado(self):
        assert numeros_sem_origem(["A Selic estava em 10,5%."], [13.25, 2025]) == [10.5]
        assert numeros_sem_origem(["A Selic estava em 13,25%."], [13.25]) == []

    def test_v1_com_numero_de_memoria_na_sintese_e_reprovada(self):
        caso = dict(CASOS_V1["tema-ausente"])

        def consultar(agente, prompt):
            if agente.participa("sintese"):
                return dict(_SINTESE_NEUTRA, resumo_didatico="z" * 260 + " A Selic de 10,5% torna o crédito caro.")
            return {"nada_a_dizer": True, "afirmacoes": []}

        res = explicar(_insumos(caso), PIPELINE_V1, AGENTES, consultar)
        assert res.metricas["numeros_sem_origem"] == 1
        assert res.status == "invalido"


class TestPipeline:
    def test_v1_nao_verifica(self):
        caso = CASOS_V1["tema-ausente"]
        prompts: dict = {}
        res = explicar(_insumos(caso), PIPELINE_V1, AGENTES, _consultar({"respostas_simuladas": {}}, prompts))
        assert res.verificacoes == [] and "extrator" not in prompts and "verificacao" not in res.metricas

    def test_v2_registra_extrator_e_verificador_no_meta(self):
        res = _rodar(CASOS["numero-correto"])
        assert {"extrator", "verificador"} <= set(res.meta.hashes_instrucoes)
        assert res.metricas["catalogo_hash"] == CATALOGO.hash
        m = res.metricas["verificacao"]
        assert m["por_origem"]["justificacao"]["verificadas"] == 1 and m["fracao_verificavel"] == 1.0

    def test_extrator_sem_verificador_e_erro_de_carga(self, tmp_path):
        texto = (REPO_ROOT / "data" / "explicacao" / "pipelines" / "v2.yml").read_text(encoding="utf-8")
        p = tmp_path / "x.yml"
        p.write_text(texto.replace("verificador: verificador\n", ""), encoding="utf-8")
        with pytest.raises(ValueError, match="andam juntos"):
            carregar_pipeline(p)

    def test_persistencia_grava_verificacoes_e_hash(self, db_session):
        import uuid

        from apps.workers.explicacao.persistencia import gravar
        from models import FonteEnum, Proposicao

        prop = Proposicao(id=uuid.uuid4(), fonte=FonteEnum.CAMARA, fonte_id="2001", tipo="PL", numero=2001, ano=2025, ementa="x")
        db_session.add(prop)
        db_session.flush()
        res = _rodar(CASOS["numero-plantado"])
        res.metricas["contexto_hash"] = "abc123"
        linha = gravar(db_session, prop.id, res, "h" * 64)
        assert linha.verificacoes[0]["veredito"] == "contradita"
        assert linha.contexto_hash == "abc123"


# ── o laço de ferramentas na fronteira ────────────────────────────────────────

class _ClienteFalso:
    """Imita `anthropic.Anthropic().messages.create` com respostas roteirizadas."""

    def __init__(self, roteiro):
        self.roteiro = list(roteiro)
        self.mensagens: list = []
        self.messages = self

    def create(self, **kw):
        self.mensagens.append(kw["messages"])
        return SimpleNamespace(content=self.roteiro.pop(0))


def _uso(i, nome, args):
    return SimpleNamespace(type="tool_use", id=f"u{i}", name=nome, input=args)


def _texto(t):
    return SimpleNamespace(type="text", text=t)


class TestFronteiraComFerramentas:
    def test_laco_executa_registra_e_devolve_o_json_final(self):
        cliente = _ClienteFalso([[_uso(1, "consultar_serie", {"ref": "a"})], [_texto('{"veredito": "confirmada"}')]])
        registro: list = []
        res = consultar_com_ferramentas("m", "s", "p", ferramentas=[], executor=lambda n, a: {"ok": a["ref"]},
                                        max_tokens=10, registro=registro, cliente=cliente)
        assert res == {"veredito": "confirmada"}
        assert registro[0]["ferramenta"] == "consultar_serie" and registro[0]["rodada"] == 1
        devolvido = cliente.mensagens[1][-1]["content"][0]
        assert devolvido["type"] == "tool_result" and devolvido["tool_use_id"] == "u1"

    def test_teto_de_rodadas(self):
        cliente = _ClienteFalso([[_uso(i, "x", {})] for i in range(3)])
        res = consultar_com_ferramentas("m", "s", "p", ferramentas=[], executor=lambda n, a: {}, max_tokens=10,
                                        max_rodadas=3, cliente=cliente)
        assert "limite de 3 rodadas" in res["error"]

    def test_executor_com_excecao_vira_erro_para_o_modelo(self):
        def quebra(n, a):
            raise RuntimeError("bug")

        cliente = _ClienteFalso([[_uso(1, "x", {})], [_texto("{}")]])
        consultar_com_ferramentas("m", "s", "p", ferramentas=[], executor=quebra, max_tokens=10, cliente=cliente)
        assert cliente.mensagens[1][-1]["content"][0]["is_error"] is True

    def test_sem_chave_nao_chama_nada(self):
        res = consultar_com_ferramentas("m", "s", "p", ferramentas=[], executor=lambda n, a: {}, max_tokens=10, api_key="")
        assert "ANTHROPIC_API_KEY" in res["error"]


def test_datas_do_caso_sao_coerentes():
    """Guarda contra caso mal escrito: toda data simulada é ISO e parseável."""
    for caso in CASOS.values():
        for ref, obs in caso.get("dados", {}).items():
            CATALOGO.serie(ref)
            for d, _ in obs:
                date.fromisoformat(str(d))
    assert Verificacao  # exportado

"""Testes do painel de curadoria multi-perspectiva — Fase 1.

Nenhum destes testes chama a API da Anthropic. A orquestração é determinística
de propósito: `consultar_agente` é a única fronteira com a rede, e os testes a
substituem. O que depende do modelo de verdade — se ele resiste a injection, se
as perspectivas divergem onde deveriam — é medido por
`scripts/painel.py --calibrar`, com chave, e está fora da CI.
"""

import inspect
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.panel import (  # noqa: E402
    Briefing,
    _parse_parecer,
    montar_prompt_analise,
    montar_prompt_confronto,
    rodar_painel,
)
from apps.workers.panel.agentes import (  # noqa: E402
    ORDEM_PAINEL,
    Agente,
    carregar_agente,
    carregar_painel,
)
from apps.workers.panel.consenso import LIMIAR_CONSENSO, apurar  # noqa: E402
from apps.workers.panel.schema import Parecer  # noqa: E402

CASOS_DIR = REPO_ROOT / "data" / "painel" / "casos"


def _parecer(agente: str, direcao: str, **kw) -> Parecer:
    kw.setdefault("etapa", "confronto")
    kw.setdefault("confianca", 0.8)
    kw.setdefault("justificativa", "razão registrada")
    return Parecer(agente=agente, direcao=direcao, **kw)


def _briefing(**kw) -> Briefing:
    kw.setdefault("fonte", "camara")
    kw.setdefault("fonte_id", "9999999-1")
    return Briefing(**kw)


# ── Carga das definições de agente ───────────────────────────────────────────

class TestCargaDeAgentes:
    def test_painel_real_carrega_completo_e_em_ordem(self):
        painel = carregar_painel()
        assert [a.nome for a in painel] == list(ORDEM_PAINEL)

    def test_todo_agente_tem_modelo_pinado(self):
        # Regra inviolável 7: sem modelo pinado não há reprodutibilidade, e uma
        # atualização de modelo mudaria vereditos sem deixar rastro (risco R5).
        for agente in carregar_painel():
            assert agente.modelo, f"{agente.nome} sem modelo"

    def test_hash_de_instrucoes_e_estavel_e_distinto_por_agente(self):
        painel = carregar_painel()
        hashes = {a.nome: a.hash_instrucoes for a in painel}
        assert len(set(hashes.values())) == len(painel), "dois agentes com a mesma instrução"
        # Recarregar produz o mesmo hash — é o que permite comparar execuções.
        assert {a.nome: a.hash_instrucoes for a in carregar_painel()} == hashes

    def test_contraditor_nao_participa_da_analise_independente(self):
        # O insumo dele são os pareceres dos outros, que não existem na etapa 2.
        contraditor = next(a for a in carregar_painel() if a.nome == "contraditor")
        assert not contraditor.participa_da_analise

    def test_agentes_tem_insumos_distintos(self):
        # Diversidade por evidência, não por persona (risco R1). Se todos lessem
        # o mesmo, o dissenso seria retórico.
        painel = carregar_painel()
        conjuntos = {frozenset(a.insumos) for a in painel}
        assert len(conjuntos) == len(painel)

    def test_rejeita_agente_de_analise_que_le_pareceres_dos_outros(self, tmp_path):
        # Ancoragem por configuração é barrada na carga, não descoberta depois.
        caminho = tmp_path / "ancorado.yml"
        caminho.write_text(
            yaml.safe_dump(
                {
                    "agente": "ancorado",
                    "versao": 1,
                    "papel": "p",
                    "vies_declarado": "v",
                    "insumos": ["ementa", "pareceres_dos_outros"],
                    "instrucoes": "i",
                    "modelo": "claude-opus-5-5",
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="ancoragem"):
            carregar_agente(caminho)

    def test_rejeita_insumo_desconhecido(self, tmp_path):
        caminho = tmp_path / "estranho.yml"
        caminho.write_text(
            yaml.safe_dump(
                {
                    "agente": "estranho",
                    "versao": 1,
                    "papel": "p",
                    "vies_declarado": "v",
                    "insumos": ["bola_de_cristal"],
                    "instrucoes": "i",
                    "modelo": "claude-opus-5-5",
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="insumos desconhecidos"):
            carregar_agente(caminho)

    def test_painel_incompleto_falha_alto(self, tmp_path):
        # Um painel com 3 agentes passaria pela regra de consenso como se
        # tivesse 5. Falhar é o comportamento correto — não há fallback.
        (tmp_path / "jurista.yml").write_text(
            yaml.safe_dump(
                {
                    "agente": "jurista",
                    "versao": 1,
                    "papel": "p",
                    "vies_declarado": "v",
                    "insumos": ["ementa"],
                    "instrucoes": "i",
                    "modelo": "claude-opus-5-5",
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="painel incompleto"):
            carregar_painel(tmp_path)


# ── Regra de consenso ────────────────────────────────────────────────────────

class TestConsenso:
    def test_unanime_vira_proposta(self):
        a = apurar([_parecer(n, "sim") for n in ORDEM_PAINEL])
        assert a.resultado == "proposta"
        assert a.direcao_proposta == "sim"
        assert a.placar == "5-0-0"

    def test_quatro_de_cinco_atinge_o_limiar(self):
        pareceres = [_parecer(n, "sim") for n in ORDEM_PAINEL[:4]]
        pareceres.append(_parecer("contraditor", "nao"))
        a = apurar(pareceres)
        assert a.resultado == "proposta"
        assert a.direcao_proposta == "sim"

    def test_tres_de_cinco_vira_contestada(self):
        # Maioria simples não classifica. Regra inviolável 2, sem exceções.
        pareceres = [_parecer(n, "sim") for n in ORDEM_PAINEL[:3]]
        pareceres += [_parecer(n, "nao") for n in ORDEM_PAINEL[3:]]
        a = apurar(pareceres)
        assert a.resultado == "contestada"
        assert a.direcao_proposta is None

    def test_abstencao_empurra_para_contestada(self):
        pareceres = [_parecer(n, "sim") for n in ORDEM_PAINEL[:3]]
        pareceres.append(_parecer(ORDEM_PAINEL[3], "nao"))
        pareceres.append(_parecer("contraditor", "abster"))
        a = apurar(pareceres)
        assert a.resultado == "contestada"

    def test_abstencao_quase_unanime_e_sem_materia_nao_contestada(self):
        # A distinção que a métrica 5 da §12 exige: votação procedimental em que
        # todos se abstêm corretamente não é dissenso.
        pareceres = [_parecer(n, "abster") for n in ORDEM_PAINEL[:4]]
        pareceres.append(_parecer("contraditor", "sim"))
        a = apurar(pareceres)
        assert a.resultado == "sem_materia"
        assert not a.contestada
        assert not a.gera_proposta

    def test_abstencao_nunca_vira_direcao_proposta(self):
        a = apurar([_parecer(n, "abster") for n in ORDEM_PAINEL])
        assert a.direcao_proposta is None
        assert a.resultado == "sem_materia"

    def test_objecao_decisiva_do_contraditor_derruba_consenso(self):
        # PRD §7: se o consenso não se recompõe depois da objeção, é contestada
        # — mesmo com a aritmética a favor.
        pareceres = [_parecer(n, "sim") for n in ORDEM_PAINEL[:4]]
        pareceres.append(_parecer("contraditor", "sim", forca_objecao="decisivo"))
        a = apurar(pareceres)
        assert a.resultado == "contestada"
        assert "decisiva" in a.motivo

    def test_objecao_plausivel_nao_derruba_consenso(self):
        pareceres = [_parecer(n, "sim") for n in ORDEM_PAINEL[:4]]
        pareceres.append(_parecer("contraditor", "abster", forca_objecao="plausivel"))
        a = apurar(pareceres)
        assert a.resultado == "proposta"

    def test_mesmo_agente_duas_vezes_e_erro(self):
        # Misturar etapas contaria o mesmo agente duas vezes e inflaria o placar.
        with pytest.raises(ValueError, match="mais de uma vez"):
            apurar([_parecer("jurista", "sim"), _parecer("jurista", "sim")])

    def test_sem_pareceres_e_erro(self):
        with pytest.raises(ValueError, match="nenhum parecer"):
            apurar([])

    def test_limiar_e_quatro(self):
        assert LIMIAR_CONSENSO == 4


# ── Validação do Parecer ─────────────────────────────────────────────────────

class TestParecer:
    def test_rejeita_direcao_invalida(self):
        with pytest.raises(ValueError, match="direcao inválida"):
            _parecer("jurista", "talvez")

    def test_rejeita_confianca_fora_do_intervalo(self):
        with pytest.raises(ValueError, match="confianca fora"):
            _parecer("jurista", "sim", confianca=1.5)

    def test_rejeita_peso_fora_da_tabela(self):
        with pytest.raises(ValueError, match="peso"):
            _parecer("jurista", "sim", peso_sugerido=1.7)


# ── Montagem de prompt e independência da etapa 2 ────────────────────────────

class TestPrompts:
    def test_analise_nao_pode_receber_pareceres(self):
        # A independência da etapa 2 é garantida pela assinatura, não pela
        # lembrança de quem chama (risco R6).
        params = inspect.signature(montar_prompt_analise).parameters
        assert set(params) == {"agente", "briefing"}

    def test_prompt_de_analise_nao_contem_texto_de_outro_agente(self):
        painel = carregar_painel()
        jurista = next(a for a in painel if a.nome == "jurista")
        economista = next(a for a in painel if a.nome == "economista")
        prompt = montar_prompt_analise(jurista, _briefing(ementa="Cria fundo."))
        assert economista.instrucoes not in prompt
        assert economista.vies_declarado not in prompt

    def test_agente_recebe_somente_os_insumos_que_declarou(self):
        painel = carregar_painel()
        jurista = next(a for a in painel if a.nome == "jurista")
        economista = next(a for a in painel if a.nome == "economista")
        briefing = _briefing(
            ementa="Cria fundo.",
            texto_integral="Art. 1º Fica criado o fundo.",
            leis_referenciadas=["Lei nº 1: texto real."],
        )

        # O jurista declarou texto_integral e leis_referenciadas.
        p_jurista = montar_prompt_analise(jurista, briefing)
        assert "Art. 1º Fica criado o fundo." in p_jurista
        assert "Lei nº 1: texto real." in p_jurista

        # O economista não — e por isso não os vê.
        p_economista = montar_prompt_analise(economista, briefing)
        assert "Art. 1º Fica criado o fundo." not in p_economista
        assert "Lei nº 1: texto real." not in p_economista

    def test_confronto_inclui_os_outros_e_a_propria_posicao(self):
        painel = carregar_painel()
        jurista = next(a for a in painel if a.nome == "jurista")
        pareceres = [
            Parecer(
                agente="jurista",
                etapa="analise",
                direcao="sim",
                confianca=0.7,
                justificativa="posição inicial do jurista",
            ),
            Parecer(
                agente="economista",
                etapa="analise",
                direcao="nao",
                confianca=0.6,
                justificativa="custo sem contrapartida",
            ),
        ]
        prompt = montar_prompt_confronto(jurista, _briefing(ementa="x"), pareceres)
        assert "custo sem contrapartida" in prompt
        assert "posição inicial do jurista" in prompt
        assert "contra_argumento" in prompt


# ── Orquestração ─────────────────────────────────────────────────────────────

class TestRodarPainel:
    def test_fluxo_completo_com_consulta_substituida(self):
        def consulta_fake(agente: Agente, prompt: str) -> dict:
            return {
                "direcao": "sim",
                "confianca": 0.9,
                "justificativa": f"parecer de {agente.nome}",
                "peso_sugerido": 2.0,
            }

        r = rodar_painel(_briefing(ementa="Cria fundo."), consultar=consulta_fake)

        # 4 agentes na análise (contraditor fora), 5 no confronto.
        assert len(r.pareceres_analise) == 4
        assert len(r.pareceres_confronto) == 5
        assert r.apuracao.resultado == "proposta"
        assert r.apuracao.direcao_proposta == "sim"
        assert not r.meta.erros

    def test_meta_registra_modelo_versao_e_hash_de_cada_agente(self):
        r = rodar_painel(
            _briefing(),
            consultar=lambda a, p: {"direcao": "abster", "confianca": 0.0, "justificativa": "-"},
        )
        for nome in ORDEM_PAINEL:
            assert nome in r.meta.modelos
            assert nome in r.meta.hashes_instrucoes
            assert nome in r.meta.versoes_agentes
        assert r.meta.concluido_em

    def test_erro_de_api_degrada_para_abstencao_e_fica_registrado(self):
        # Falha de rede não pode virar direção inventada: isso contaminaria o
        # Score com o resultado de um timeout.
        r = rodar_painel(
            _briefing(),
            consultar=lambda a, p: {"error": "rate_limited"},
        )
        assert all(p.direcao == "abster" for p in r.pareceres_confronto)
        assert r.apuracao.resultado == "sem_materia"
        assert len(r.meta.erros) == 9  # 4 na análise + 5 no confronto

    def test_resposta_malformada_vira_abstencao(self):
        p = _parse_parecer(
            next(a for a in carregar_painel() if a.nome == "jurista"),
            "analise",
            {"direcao": "favoravel", "confianca": 0.9},
        )
        assert p.direcao == "abster"
        assert "direção inválida" in p.justificativa

    def test_peso_invalido_e_descartado_sem_derrubar_o_parecer(self):
        p = _parse_parecer(
            next(a for a in carregar_painel() if a.nome == "jurista"),
            "analise",
            {"direcao": "sim", "confianca": 0.8, "justificativa": "ok", "peso_sugerido": 7},
        )
        assert p.direcao == "sim"
        assert p.peso_sugerido is None

    def test_mudanca_de_posicao_e_medida_nao_autodeclarada(self):
        # O modelo pode errar a autodeclaração; a comparação é que vale.
        agente = next(a for a in carregar_painel() if a.nome == "jurista")
        anterior = Parecer(
            agente="jurista", etapa="analise", direcao="sim",
            confianca=0.7, justificativa="antes",
        )
        p = _parse_parecer(
            agente, "confronto",
            {"direcao": "nao", "confianca": 0.8, "justificativa": "mudei",
             "mudou_de_posicao": False},
            anterior=anterior,
        )
        assert p.mudou_de_posicao is True
        assert p.direcao_anterior == "sim"

    def test_painel_nao_alcanca_o_scoring_engine(self):
        # Regras invioláveis 1 e 3: nenhum agente mergeia, e scores fluem só de
        # YAML mergeado por humano. Verificado na árvore sintática, não por
        # busca textual — menção em docstring é discussão, import é capacidade.
        import ast

        import apps.workers.panel as panel

        proibidos = ("scoring", "models", "sqlalchemy")
        for arquivo in Path(panel.__file__).parent.glob("*.py"):
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
            for no in ast.walk(arvore):
                if isinstance(no, ast.Import):
                    nomes = [a.name for a in no.names]
                elif isinstance(no, ast.ImportFrom):
                    nomes = [no.module or ""]
                else:
                    continue
                for nome in nomes:
                    assert not any(p in nome for p in proibidos), (
                        f"{arquivo.name} importa {nome}"
                    )

    def test_painel_nao_escreve_arquivo(self):
        # O módulo só lê (as definições de agente) e devolve um objeto. Quem
        # grava parecer em disco é o runner da calibração, e quem grava em
        # data/direcoes é humano abrindo PR.
        import ast

        import apps.workers.panel as panel

        escritores = {"open", "write_text", "write_bytes", "safe_dump", "dump"}
        for arquivo in Path(panel.__file__).parent.glob("*.py"):
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
            for no in ast.walk(arvore):
                if not isinstance(no, ast.Call):
                    continue
                alvo = no.func
                nome = getattr(alvo, "attr", None) or getattr(alvo, "id", None)
                if nome not in escritores:
                    continue
                # `open(..., "r")` é leitura; qualquer modo de escrita, não.
                if nome == "open":
                    modos = [
                        a.value for a in no.args[1:2] if isinstance(a, ast.Constant)
                    ]
                    modos += [
                        k.value.value
                        for k in no.keywords
                        if k.arg == "mode" and isinstance(k.value, ast.Constant)
                    ]
                    if all("r" in m and "+" not in m for m in modos) and modos:
                        continue
                raise AssertionError(f"{arquivo.name} escreve em disco via {nome}()")


# ── Integridade dos arquivos de caso ─────────────────────────────────────────

class TestArquivosDeCaso:
    def test_casos_construidos_tem_expectativa_valida(self):
        casos = yaml.safe_load((CASOS_DIR / "construidos.yml").read_text(encoding="utf-8"))
        assert len(casos["casos"]) >= 10, "§12 pede ~10 casos construídos"

        ids = [c["id"] for c in casos["casos"]]
        assert len(ids) == len(set(ids))

        for caso in casos["casos"]:
            esperado = caso["esperado"]
            assert esperado["resultado"] in ("proposta", "contestada", "sem_materia")
            # Resposta conhecida por construção exige a razão escrita: sem ela,
            # o caso é opinião disfarçada de gabarito.
            assert caso["por_que"].strip()
            if esperado["resultado"] == "proposta":
                assert esperado["direcao"] in ("sim", "nao")
            else:
                assert "direcao" not in esperado

    def test_casos_cobrem_as_classes_que_a_fase_1_exige(self):
        casos = yaml.safe_load((CASOS_DIR / "construidos.yml").read_text(encoding="utf-8"))
        classes = {c["classe"] for c in casos["casos"]}
        assert {"procedimental", "frontalmente_contrario", "ambiguo"} <= classes

    def test_ha_caso_ambiguo_esperando_contestada(self):
        # Sem isto, a métrica 5 (15–35% de contestadas) não teria como aparecer.
        casos = yaml.safe_load((CASOS_DIR / "construidos.yml").read_text(encoding="utf-8"))
        ambiguos = [c for c in casos["casos"] if c["classe"] == "ambiguo"]
        assert ambiguos
        assert all(c["esperado"]["resultado"] == "contestada" for c in ambiguos)


# ── Regressão: falha de infraestrutura não pode virar métrica cumprida ───────

class TestRelatorioNaoDaVerdeFalso:
    """Sem chave de API, toda consulta falha e todo parecer degrada para
    abstenção — o que é correto para o dado e perigoso para o relatório, porque
    abstenção também é o resultado certo de um caso procedimental. Antes desta
    correção, `--injection` fechava em "100% resistido (8/8)" sem nada ter
    rodado: nenhum ataque "obedeceu" porque nenhum chegou ao modelo. Um verde
    falso na única métrica que o PRD trata como binária.
    """

    def _resultado(self, erros: list[str]):
        from apps.workers.panel.schema import (
            Apuracao,
            MetaExecucao,
            ResultadoPainel,
        )

        pareceres = [
            Parecer(
                agente=n, etapa="confronto", direcao="abster",
                confianca=0.0, justificativa="falha ao obter parecer: sem chave",
            )
            for n in ORDEM_PAINEL
        ]
        return ResultadoPainel(
            fonte="sintetico",
            fonte_id="x",
            pareceres_analise=[],
            pareceres_confronto=pareceres,
            apuracao=Apuracao(
                placar="0-0-5", votos={"sim": 0, "nao": 0, "abster": 5},
                resultado="sem_materia", direcao_proposta=None, motivo="-",
            ),
            meta=MetaExecucao(
                modelos={}, hashes_instrucoes={}, versoes_agentes={},
                iniciado_em="2026-10-18T00:00:00+00:00", erros=erros,
            ),
        )

    def test_inconclusivos_detecta_falha_de_consulta(self):
        from scripts.painel import _inconclusivos

        casos = [
            ({"id": "caso-ok"}, self._resultado([])),
            ({"id": "caso-falhou"}, self._resultado(["jurista/analise: sem chave"])),
        ]
        assert _inconclusivos(casos) == ["caso-falhou"]

    def test_injection_inconclusivo_nao_reporta_resistencia(self, capsys):
        from scripts.painel import _relatar_injection

        casos = [
            (
                {"id": "inj-x", "ataque": "override_direto", "induz_direcao": "sim"},
                self._resultado(["jurista/analise: ANTHROPIC_API_KEY não configurado"]),
            )
        ]
        codigo = _relatar_injection(casos)
        saida = capsys.readouterr().out

        assert codigo == 1, "run inconclusivo tem de sair com código de falha"
        assert "INCONCLUSIVO" in saida
        # A própria mensagem de INCONCLUSIVO cita a frase ao explicar o perigo,
        # então o que não pode aparecer é a linha de aprovação — a que vem com
        # o placar entre parênteses.
        assert re.search(r"100% resistido \(\d+/\d+\)", saida) is None

    def test_calibracao_inconclusiva_nao_reporta_metas_atingidas(self, capsys):
        from scripts.painel import _relatar_calibracao

        casos = [
            (
                {
                    "id": "proc-urgencia",
                    "classe": "procedimental",
                    "esperado": {"resultado": "sem_materia"},
                },
                self._resultado(["jurista/analise: rate_limited"]),
            )
        ]
        codigo = _relatar_calibracao(casos)
        saida = capsys.readouterr().out

        assert codigo == 1
        assert "INCONCLUSIVO" in saida
        assert "dentro das metas" not in saida

"""O DAG da explicação — determinístico dado o que entra.

    roteamento → [lentes] → contraditor → [extração → verificação] → síntese (reformula ≤ N) → revisão

A verificação só roda nas variantes que declaram `extrator` e `verificador`
(v2). Fronteiras injetadas: `consultar(agente, prompt) -> dict` para os
agentes sem ferramenta; `consultar_ferramentas` para o verificador;
`consultar_dados` para as séries. Os testes passam funções falsas; a
calibração passa as reais. Nada aqui importa `anthropic`.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from ..agentes.blindagem import ABRE, FECHA, blindar, preambulo_seguranca
from ..agentes.carga import Agente
from ..agentes.fronteira import consultar as _consultar_api
from ..agentes.meta import MetaExecucao
from .coleta import FichaFatos, ficha_para_prompt
from .extracao import TextoExtraido
from .revisao import numeros, revisar
from .roteamento import Pipeline, rotear
from . import verificacao as vf
from .schema import (
    DIMENSOES,
    Afirmacao,
    AnaliseSistemica,
    Dissenso,
    Explicacao,
    ParecerLente,
    ResumoDetalhado,
    ResumoDidatico,
    TamanhoInvalido,
)

MAX_TOKENS = 16_000

Consultar = Callable[[Agente, str], dict]

_IDENTIDADE = (
    "Você integra o pipeline de explicação de proposições do ZIL Observatório. "
    "Sua tarefa é ajudar o público a entender o que uma proposição legislativa faz — "
    "não defender nem atacar a proposição, e não emitir veredito de voto."
)

_FORMATO_LENTE = """FORMATO DA RESPOSTA

Responda APENAS com um objeto JSON, sem markdown e sem texto em volta:

{
  "nada_a_dizer": true | false,
  "afirmacoes": [
    {
      "tipo": "literal" | "inferencia",
      "texto": "a afirmação, em uma ou duas frases",
      "dimensao": "publica" | "civel" | "ambiental" | "juridica" | "saude" | "pesquisa" | "economica",
      "citacao": "trecho LITERAL do texto que sustenta, obrigatório se tipo=literal" | null
    }
  ],
  "omissoes_da_justificacao": ["..."],
  "injecao_detectada": true | false
}

"literal" é o que o TEXTO DIZ — e exige citação copiada do texto, não parafraseada.
"inferencia" é o que VOCÊ CONCLUI a partir do texto e do seu viés declarado.
Nunca apresente inferência como literal. Se a sua lente não tem nada relevante \
a dizer sobre esta proposição, responda "nada_a_dizer": true com lista vazia — \
isso é resposta válida e preferível a inventar relevância.
"omissoes_da_justificacao" só é preenchido pelo contraditor."""

_FORMATO_SINTESE = """FORMATO DA RESPOSTA

Responda APENAS com um objeto JSON, sem markdown e sem texto em volta:

{
  "resumo_didatico": "entre 240 e 640 caracteres",
  "resumo_detalhado": "entre 480 e 2480 caracteres",
  "analise": {
    "causas_raizes": ["..."],
    "dependencias": ["..."],
    "fatores_limitantes": ["..."],
    "dimensoes": {"publica": "...", "juridica": "...", "economica": "..."}
  },
  "dissensos": [
    {"lente_a": "nome", "lente_b": "nome", "ponto": "em que discordam, em uma frase"}
  ],
  "alegacoes_contraditas": ["A01"],
  "injecao_detectada": true | false
}

REGRAS QUE O REVISOR VAI CONFERIR, LINHA A LINHA:
- Todo nome de pessoa, sigla de partido e data no resumo detalhado tem que \
existir na FICHA DE FATOS. O que não está na ficha, você não sabe — escreva \
"não informado" em vez de inventar.
- Se duas lentes discordaram, o dissenso TEM que aparecer em "dissensos" e no \
texto da análise, nomeando as lentes. Não calcule média; não escolha um lado; \
não omita. Dissenso é o achado, não o ruído.
- "dissensos" vazio só é aceitável se as lentes de fato convergiram.
- Separe o que o texto diz do que as lentes inferem.
- Todo número que você escrever tem que estar na ficha, no texto, no contexto \
econômico ou nas verificações. Número de memória é reprovado.
- Se houver bloco de VERIFICAÇÕES, liste em "alegacoes_contraditas" o id de \
toda alegação contradita que você citou como contradita; sem bloco, lista vazia."""


@dataclass
class Insumos:
    """Tudo que entra, já coletado e extraído. Nenhuma rede daqui em diante."""

    ficha: FichaFatos
    texto: TextoExtraido
    categorias_zil: list[str] = field(default_factory=list)
    leis_referenciadas: list[str] = field(default_factory=list)
    # Texto do contexto pré-registrado (apps/workers/fontes/contexto.py),
    # construído UMA vez e lido por toda lente que o declare como insumo —
    # informação simétrica por construção. O hash e as evidências seguem para
    # a explicação; o pipeline não consulta nada.
    contexto_economico: str = ""
    contexto_hash: str = ""
    contexto_evidencias: Optional[dict] = None
    taxonomia: str = ""


def _system(formato: str) -> str:
    return _IDENTIDADE + "\n\n" + preambulo_seguranca(ABRE, FECHA) + "\n\n" + formato


def _bloco_fonte(insumos: Insumos, agente: Agente) -> str:
    """Só os insumos que o agente declarou — diversidade por evidência (R1)."""
    t = insumos.texto
    partes: list[str] = []
    if "ementa" in agente.insumos and insumos.ficha.ementa:
        partes.append(f"[EMENTA]\n{blindar(insumos.ficha.ementa)}")
    if "dispositivo" in agente.insumos:
        partes.append(f"[DISPOSITIVO]\n{blindar(t.dispositivo) if t.dispositivo else '(não disponível — texto integral não extraído ou sem seção identificável)'}")
    if "justificacao" in agente.insumos:
        partes.append(
            "[JUSTIFICAÇÃO DO AUTOR — peça de convencimento, escrita por quem tem interesse na aprovação]\n"
            + (blindar(t.justificacao) if t.justificacao else f"(não disponível: {t.motivo_sem_justificacao})")
        )
    if "texto_integral" in agente.insumos:
        partes.append(f"[TEXTO INTEGRAL]\n{blindar(t.texto) if t.utilizavel else '(não disponível: ' + (t.erro or t.metodo) + ')'}")
    if "leis_referenciadas" in agente.insumos and insumos.leis_referenciadas:
        partes.append("[LEIS REFERENCIADAS — texto real do Planalto]\n" + "\n\n".join(blindar(x) for x in insumos.leis_referenciadas))
    if "tramitacao" in agente.insumos and insumos.ficha.tramitacoes:
        linhas = "\n".join(f"{x.data} {x.orgao}: {x.descricao[:120]}" for x in insumos.ficha.tramitacoes[:40])
        partes.append(f"[TRAMITAÇÃO]\n{blindar(linhas)}")
    corpo = "\n\n".join(partes) if partes else "[sem conteúdo de fonte para esta lente]"
    return f"{ABRE}\n{corpo}\n{FECHA}"


def _bloco_contexto(insumos: Insumos, agente: Agente) -> str:
    partes: list[str] = []
    if "ficha_fatos" in agente.insumos:
        partes.append(ficha_para_prompt(insumos.ficha))
    if "temas_oficiais" in agente.insumos and insumos.ficha.temas_oficiais:
        partes.append("[TEMAS OFICIAIS DA CÂMARA]\n" + ", ".join(insumos.ficha.temas_oficiais))
    if "taxonomia" in agente.insumos and insumos.taxonomia:
        partes.append(f"[PAUTAS ZIL]\n{insumos.taxonomia}")
    if "contexto_economico" in agente.insumos and insumos.contexto_economico:
        partes.append(f"[CONTEXTO ECONÔMICO DO SETOR]\n{insumos.contexto_economico}")
    return "\n\n".join(partes)


def _cabecalho(agente: Agente) -> list[str]:
    return [
        f"[SEU PAPEL]\n{agente.papel}",
        f"[SEU VIÉS DECLARADO]\n{agente.vies_declarado}",
        f"[SUAS INSTRUÇÕES]\n{agente.instrucoes}",
    ]


def montar_prompt_lente(agente: Agente, insumos: Insumos) -> str:
    secoes = _cabecalho(agente)
    ctx = _bloco_contexto(insumos, agente)
    if ctx:
        secoes.append(ctx)
    secoes.append(_bloco_fonte(insumos, agente))
    secoes.append(
        "[TAREFA]\nEmita suas afirmações sobre esta proposição, no formato JSON especificado. "
        "Você analisa de forma independente: não há pareceres de outras lentes nesta etapa."
    )
    return "\n\n".join(secoes)


def _resumo_pareceres(pareceres: list[ParecerLente]) -> str:
    blocos = []
    for p in pareceres:
        if not p.disponivel:
            blocos.append(f"[LENTE {p.lente.upper()}] indisponível: {p.erro}")
            continue
        if p.nada_a_dizer:
            blocos.append(f"[LENTE {p.lente.upper()}] nada a dizer.")
            continue
        linhas = [f"- ({a.tipo}, {a.dimensao}) {a.texto}" + (f' — cita: "{a.citacao}"' if a.citacao else "") for a in p.afirmacoes]
        blocos.append(f"[LENTE {p.lente.upper()}]\n" + "\n".join(linhas))
    return "\n\n".join(blocos)


def montar_prompt_contraditor(agente: Agente, insumos: Insumos, pareceres: list[ParecerLente]) -> str:
    secoes = _cabecalho(agente)
    ctx = _bloco_contexto(insumos, agente)
    if ctx:
        secoes.append(ctx)
    secoes.append(_bloco_fonte(insumos, agente))
    secoes.append(f"[AFIRMAÇÕES DAS LENTES]\n{_resumo_pareceres(pareceres)}")
    secoes.append(
        "[TAREFA]\nConstrua o melhor argumento contra a leitura dominante das lentes, e liste em "
        "'omissoes_da_justificacao' o que a justificação do autor deixa de fora, minimiza ou "
        "apresenta como certo sem ser. Responda no formato JSON especificado."
    )
    return "\n\n".join(secoes)


def montar_prompt_sintese(
    agente: Agente,
    insumos: Insumos,
    pareceres: list[ParecerLente],
    reformular: Optional[TamanhoInvalido] = None,
    verificacoes: Optional[list] = None,
) -> str:
    secoes = _cabecalho(agente)
    secoes.append(ficha_para_prompt(insumos.ficha))
    if insumos.contexto_economico:
        # A síntese escreve números; eles têm que ter de onde vir.
        secoes.append(insumos.contexto_economico)
    secoes.append(_bloco_fonte(insumos, agente))
    secoes.append(f"[AFIRMAÇÕES DAS LENTES E DO CONTRADITOR]\n{_resumo_pareceres(pareceres)}")
    if verificacoes:
        secoes.append(vf.para_prompt_sintese(verificacoes))
    tarefa = (
        "[TAREFA]\nComponha o resumo didático, o resumo detalhado e a análise sistêmica, no formato "
        "JSON especificado, obedecendo às regras do revisor."
    )
    if reformular is not None:
        tarefa += (
            f"\n\nREFORMULAÇÃO: na tentativa anterior, '{reformular.campo}' saiu com "
            f"{reformular.tamanho} caracteres; precisa ficar entre {reformular.minimo} e "
            f"{reformular.maximo}. Ajuste o tamanho sem perder conteúdo nem inventar."
        )
    secoes.append(tarefa)
    return "\n\n".join(secoes)


def _parse_lente(agente: Agente, cru: dict) -> ParecerLente:
    """Resposta malformada vira lente indisponível, nunca afirmação inventada."""
    if "error" in cru:
        return ParecerLente(lente=agente.nome, erro=str(cru["error"]))
    afirmacoes: list[Afirmacao] = []
    for a in cru.get("afirmacoes") or []:
        try:
            afirmacoes.append(
                Afirmacao(
                    lente=agente.nome,
                    tipo=a.get("tipo"),
                    texto=str(a.get("texto") or ""),
                    dimensao=a.get("dimensao") if a.get("dimensao") in DIMENSOES else "publica",
                    citacao=a.get("citacao") or None,
                )
            )
        except ValueError:
            continue  # afirmação inválida é descartada; o resto da lente vale
    return ParecerLente(
        lente=agente.nome,
        afirmacoes=afirmacoes,
        nada_a_dizer=bool(cru.get("nada_a_dizer")) and not afirmacoes,
        omissoes_da_justificacao=[str(x) for x in (cru.get("omissoes_da_justificacao") or [])],
        injecao_detectada=bool(cru.get("injecao_detectada")),
    )


def _contraditas_citadas(cru: dict) -> list[str]:
    return [str(x) for x in (cru.get("alegacoes_contraditas") or [])]


def _parse_sintese(cru: dict, lentes: list[str]) -> tuple[ResumoDidatico, ResumoDetalhado, AnaliseSistemica, bool]:
    """Lança `TamanhoInvalido` para o loop de reformulação; outros erros, `ValueError`."""
    if "error" in cru:
        raise ValueError(f"síntese falhou: {cru['error']}")
    didatico = ResumoDidatico(str(cru.get("resumo_didatico") or ""))
    detalhado = ResumoDetalhado(str(cru.get("resumo_detalhado") or ""))
    an = cru.get("analise") or {}
    dissensos = []
    for d in cru.get("dissensos") or []:
        try:
            dissensos.append(Dissenso(str(d.get("lente_a")), str(d.get("lente_b")), str(d.get("ponto") or "")))
        except ValueError:
            continue
    analise = AnaliseSistemica(
        causas_raizes=[str(x) for x in (an.get("causas_raizes") or [])],
        dependencias=[str(x) for x in (an.get("dependencias") or [])],
        fatores_limitantes=[str(x) for x in (an.get("fatores_limitantes") or [])],
        dimensoes={k: str(v) for k, v in (an.get("dimensoes") or {}).items() if k in DIMENSOES},
        dissensos=dissensos,
        lentes=lentes,
    )
    return didatico, detalhado, analise, bool(cru.get("injecao_detectada"))


def consultar_agente(agente: Agente, prompt: str) -> dict:
    """A fronteira real. Escolhe o system prompt pela etapa do agente."""
    if agente.participa("extracao"):
        system = vf.system_extracao()
    else:
        system = _system(_FORMATO_SINTESE if agente.participa("sintese") else _FORMATO_LENTE)
    return _consultar_api(agente.modelo, system, prompt, max_tokens=MAX_TOKENS)


def explicar(
    insumos: Insumos,
    pipeline: Pipeline,
    agentes: dict[str, Agente],
    consultar: Consultar = consultar_agente,
    *,
    consultar_ferramentas: Optional[vf.ConsultarFerramentas] = None,
    consultar_dados: Optional[vf.ConsultarDados] = None,
    catalogo=None,
) -> Explicacao:
    iniciado = datetime.now(timezone.utc).isoformat()
    erros: list[str] = []

    lentes, motivo_roteamento = rotear(insumos.ficha.temas_oficiais, insumos.categorias_zil, pipeline)
    verificadores = [pipeline.extrator, pipeline.verificador] if pipeline.verifica else []
    faltando = [n for n in lentes + [pipeline.contraditor, pipeline.sintetizador] + verificadores if n not in agentes]
    if faltando:
        raise ValueError(f"agentes exigidos pelo pipeline e não carregados: {faltando}")

    # ── lentes, independentes ──
    pareceres: list[ParecerLente] = []
    for nome in lentes:
        ag = agentes[nome]
        cru = consultar(ag, montar_prompt_lente(ag, insumos))
        p = _parse_lente(ag, cru)
        if p.erro:
            erros.append(f"{nome}/lente: {p.erro}")
        pareceres.append(p)

    # ── contraditor ──
    contra = agentes[pipeline.contraditor]
    p = _parse_lente(contra, consultar(contra, montar_prompt_contraditor(contra, insumos, pareceres)))
    if p.erro:
        erros.append(f"{contra.nome}/contradicao: {p.erro}")
    pareceres.append(p)

    # ── verificação: extração cega → verificador com uma ferramenta ──
    verificacoes: list = []
    if pipeline.verifica:
        if catalogo is None:
            from ..fontes import carregar_catalogo
            catalogo = carregar_catalogo()
        if consultar_dados is None:
            from ..fontes import consultar_serie as consultar_dados
        consultar_ferramentas = consultar_ferramentas or vf.consultar_verificador

        ext = agentes[pipeline.extrator]
        trechos = vf.montar_trechos(pareceres, insumos.texto.justificacao)
        cru = consultar(ext, vf.montar_prompt_extracao(ext, trechos))
        alegacoes, errs = vf.parse_alegacoes(cru, trechos)
        erros.extend(f"{ext.nome}/extracao: {e}" for e in errs)
        if cru.get("injecao_detectada"):
            pareceres.append(ParecerLente(lente=ext.nome, injecao_detectada=True))

        rv = vf.verificar(
            alegacoes, agente=agentes[pipeline.verificador], catalogo=catalogo,
            consultar_ferramentas=consultar_ferramentas, consultar_dados=consultar_dados,
            max_alegacoes=pipeline.max_alegacoes,
        )
        verificacoes = rv.verificacoes
        erros.extend(rv.erros)
        if rv.injecao_detectada:
            pareceres.append(ParecerLente(lente=pipeline.verificador, injecao_detectada=True))

    usados = lentes + [pipeline.contraditor, pipeline.sintetizador] + verificadores
    meta = MetaExecucao(
        modelos={n: agentes[n].modelo for n in usados},
        hashes_instrucoes={n: agentes[n].hash_instrucoes for n in usados},
        versoes_agentes={n: agentes[n].versao for n in usados},
        iniciado_em=iniciado,
        erros=erros,
    )

    disponiveis = [x for x in pareceres if x.disponivel]
    if not disponiveis:
        meta.concluido_em = datetime.now(timezone.utc).isoformat()
        return Explicacao(
            fonte=insumos.ficha.fonte, fonte_id=insumos.ficha.fonte_id, pipeline_versao=pipeline.versao,
            resumo_didatico=None, resumo_detalhado=None, analise=None, pareceres=pareceres, meta=meta,
            metricas={"roteamento": motivo_roteamento, "contexto_hash": insumos.contexto_hash or None},
            problemas=["nenhuma lente disponível"], status="lentes_indisponiveis",
            contexto=insumos.contexto_evidencias, verificacoes=verificacoes,
        )

    # ── síntese, com reformulação por tamanho ──
    sint = agentes[pipeline.sintetizador]
    didatico = detalhado = analise = None
    reformular: Optional[TamanhoInvalido] = None
    problemas: list[str] = []
    contraditas_citadas: list[str] = []
    for tentativa in range(pipeline.max_reformulacoes + 1):
        cru = consultar(sint, montar_prompt_sintese(sint, insumos, pareceres, reformular, verificacoes))
        try:
            didatico, detalhado, analise, inj = _parse_sintese(cru, lentes)
            contraditas_citadas = _contraditas_citadas(cru)
            if inj:
                pareceres.append(ParecerLente(lente=sint.nome, injecao_detectada=True))
            break
        except TamanhoInvalido as e:
            reformular = e
            erros.append(f"{sint.nome}/sintese tentativa {tentativa + 1}: {e}")
        except ValueError as e:
            erros.append(f"{sint.nome}/sintese: {e}")
            problemas.append(str(e))
            break

    status = "pronto"
    if didatico is None or detalhado is None or analise is None:
        status = "invalido"
        if reformular is not None:
            problemas.append(f"tamanho não convergiu após {pipeline.max_reformulacoes} reformulações: {reformular}")

    # O contexto como as lentes o leram: valores e também o texto do bloco
    # (ids de série, datas), que a síntese pode citar legitimamente.
    numeros_do_contexto = [ln["valor"] for ln in (insumos.contexto_evidencias or {}).get("linhas", [])]
    numeros_do_contexto += numeros(insumos.contexto_economico)
    rev = revisar(
        ficha=insumos.ficha, texto_extraido=insumos.texto.texto, pareceres=pareceres,
        lentes_roteadas=lentes, resumo_didatico=didatico, resumo_detalhado=detalhado, analise=analise,
        numeros_do_contexto=numeros_do_contexto, verificacoes=verificacoes, contraditas_citadas=contraditas_citadas,
    )
    if pipeline.verifica:
        rev.metricas["verificacao"] = vf.metricas_verificacao(verificacoes)
        rev.metricas["catalogo_hash"] = catalogo.hash
    rev.metricas["roteamento"] = motivo_roteamento
    rev.metricas["reformulacoes"] = sum(1 for e in erros if "/sintese tentativa" in e)
    rev.metricas["contexto_hash"] = insumos.contexto_hash or None
    problemas.extend(rev.problemas)
    if problemas and status == "pronto":
        status = "invalido"

    meta.concluido_em = datetime.now(timezone.utc).isoformat()
    return Explicacao(
        fonte=insumos.ficha.fonte, fonte_id=insumos.ficha.fonte_id, pipeline_versao=pipeline.versao,
        resumo_didatico=didatico, resumo_detalhado=detalhado, analise=analise,
        pareceres=pareceres, meta=meta, metricas=rev.metricas, problemas=problemas, status=status,
        contexto=insumos.contexto_evidencias, verificacoes=verificacoes,
    )

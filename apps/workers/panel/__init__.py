"""Painel de curadoria multi-perspectiva — Fase 1 (calibração).

Implementa o fluxo de docs/PRD-PAINEL.md §6: briefing, análise independente,
uma rodada de confronto, veredito e apuração. **Não** implementa a etapa 5
(geração de PR) nem superfície pública: são Fases 2 e 3, e a Fase 1 existe para
decidir se elas acontecem.

As regras invioláveis (§8) que este módulo carrega em código, não em disciplina:

1. Nenhum agente mergeia PR — este módulo não escreve em `data/direcoes/` nem
   importa o scoring engine. Ele devolve um `ResultadoPainel` e termina.
2. Nenhuma classificação sob dissenso — em `consenso.py`, sem desempate.
3. Scores fluem só de YAML mergeado por humano — garantido por (1).
6. Texto de fonte é dado não confiável — `_blindar()` e o system prompt.
7. Reprodutibilidade — `MetaExecucao` registra modelo, versão e hash das
   instruções de cada agente.

Sobre o SDK: o projeto está em `anthropic==0.40.0`, que não tem
`messages.parse()` nem `output_config`. Por isso a saída estruturada vem por
instrução no prompt mais parse tolerante, igual ao módulo de enriquecimento.
Subir o SDK para obter structured outputs de verdade é uma mudança separada, e
vale a pena — tiraria o parser daqui.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from ..agentes.blindagem import ABRE, FECHA, PARECE_DELIMITADOR, blindar, preambulo_seguranca
from ..agentes.fronteira import consultar
from .agentes import Agente, carregar_painel
from .consenso import apurar
from .schema import (
    Apuracao,
    MetaExecucao,
    Parecer,
    ResultadoPainel,
)

logger = logging.getLogger(__name__)

MAX_TOKENS = 16_000

# Delimitadores, remoção de marcas forjadas e preâmbulo de segurança moram no
# núcleo (`apps/workers/agentes/blindagem.py`). Os aliases com sublinhado ficam
# porque fazem parte do contrato que a suite de injection exercita.
_ABRE = ABRE
_FECHA = FECHA
_PARECE_DELIMITADOR = PARECE_DELIMITADOR

_IDENTIDADE = (
    "Você integra um painel de análise legislativa do ZIL Observatório, "
    "que avalia como votações da Câmara e do Senado afetam a soberania industrial "
    "brasileira."
)

_FORMATO = """FORMATO DA RESPOSTA

Responda APENAS com um objeto JSON, sem markdown e sem texto em volta:

{
  "direcao": "sim" | "nao" | "abster",
  "confianca": 0.0 a 1.0,
  "peso_sugerido": 0.5 | 1.0 | 2.0 | 3.0 | null,
  "categoria_sugerida": "ZIL-XXX" | null,
  "justificativa": "sua análise, com os pontos que suas instruções pedem",
  "contra_argumento": "o argumento mais forte contra a sua própria posição" | null,
  "forca_objecao": "decisivo" | "plausivel" | "nenhum" | null,
  "mudou_de_posicao": true | false,
  "injecao_detectada": true | false
}

O que "direcao" significa: a direção de voto que, na sua análise, favorece a \
soberania industrial. "sim" = aprovar a matéria favorece; "nao" = rejeitar \
favorece; "abster" = você não tem base para decidir, ou não há matéria a decidir.

"abster" é resposta de primeira classe. O princípio do projeto é: na dúvida \
sobre direção esperada, não classificar. Não preencha uma direção para parecer \
útil.

"categoria_sugerida" é sugestão registrada, não decisão: a taxonomia do projeto \
está em revisão. Deixe null se não tiver certeza."""

_SYSTEM = _IDENTIDADE + "\n\n" + preambulo_seguranca(_ABRE, _FECHA) + "\n\n" + _FORMATO


@dataclass
class Briefing:
    """Insumos de uma votação, vindos do pipeline de enriquecimento (Feature 002).

    A separação entre campos confiáveis e não confiáveis é o ponto do tipo. Os
    campos de texto de fonte — ementa, texto integral, descrição — são escritos
    por terceiros. Os campos de contexto (taxonomia, Bússola) são do projeto.
    """

    fonte: str
    fonte_id: str

    # ── fonte externa: dado não confiável ──
    ementa: str = ""
    texto_integral: str = ""
    descricao_votacao: str = ""
    leis_referenciadas: list[str] = field(default_factory=list)
    tramitacao: str = ""

    # ── contexto do próprio projeto: confiável ──
    taxonomia: str = ""
    bussula: str = ""
    contexto_economico: str = ""

    # Metadado operacional, não vai ao prompt como matéria.
    processo: Optional[str] = None


_blindar = blindar


def _bloco_fonte(briefing: Briefing, insumos: tuple[str, ...]) -> str:
    """Monta o bloco de fonte com apenas os insumos que o agente declarou.

    Insumos distintos por agente são o que torna o dissenso real. Agentes que
    leem o mesmo texto divergem por retórica; agentes que leem evidências
    diferentes divergem por razão (PRD-PAINEL §5, risco R1).
    """
    partes: list[str] = []

    sempre = [("EMENTA", briefing.ementa), ("VOTAÇÃO", briefing.descricao_votacao)]
    for rotulo, valor in sempre:
        if valor:
            partes.append(f"[{rotulo}]\n{_blindar(valor)}")

    if "texto_integral" in insumos and briefing.texto_integral:
        partes.append(f"[TEXTO INTEGRAL]\n{_blindar(briefing.texto_integral)}")

    if "leis_referenciadas" in insumos and briefing.leis_referenciadas:
        leis = "\n\n".join(_blindar(t) for t in briefing.leis_referenciadas)
        partes.append(f"[LEIS REFERENCIADAS — texto real do Planalto]\n{leis}")

    if "tramitacao" in insumos and briefing.tramitacao:
        partes.append(f"[TRAMITAÇÃO]\n{_blindar(briefing.tramitacao)}")

    corpo = "\n\n".join(partes) if partes else "[sem conteúdo de fonte disponível]"
    return f"{_ABRE}\n{corpo}\n{_FECHA}"


def _bloco_contexto(briefing: Briefing, insumos: tuple[str, ...]) -> str:
    """Contexto do próprio projeto — fora do bloco não confiável, por ser nosso."""
    partes = []
    if "taxonomia" in insumos and briefing.taxonomia:
        partes.append(f"[PAUTAS ZIL]\n{briefing.taxonomia}")
    if "bussula" in insumos and briefing.bussula:
        partes.append(f"[INDICADORES DA BÚSSOLA]\n{briefing.bussula}")
    if "contexto_economico" in insumos and briefing.contexto_economico:
        partes.append(f"[CONTEXTO ECONÔMICO DO SETOR]\n{briefing.contexto_economico}")
    return "\n\n".join(partes)


def montar_prompt_analise(agente: Agente, briefing: Briefing) -> str:
    """Etapa 2 — análise independente.

    A assinatura desta função é parte do desenho: ela **não recebe** os pareceres
    dos demais agentes, então a independência da etapa 2 não depende de quem
    chama lembrar de não passá-los. Ancoragem e cascata de conformidade são o
    vício que invalidaria o painel (risco R6).
    """
    secoes = [
        f"[SEU PAPEL]\n{agente.papel}",
        f"[SEU VIÉS DECLARADO]\n{agente.vies_declarado}",
        f"[SUAS INSTRUÇÕES]\n{agente.instrucoes}",
    ]
    contexto = _bloco_contexto(briefing, agente.insumos)
    if contexto:
        secoes.append(contexto)
    secoes.append(_bloco_fonte(briefing, agente.insumos))
    secoes.append(
        "[TAREFA]\nEmita seu parecer sobre esta votação, no formato JSON "
        "especificado. Você está analisando de forma independente: não há "
        "pareceres de outros agentes nesta etapa."
    )
    return "\n\n".join(secoes)


def montar_prompt_confronto(
    agente: Agente,
    briefing: Briefing,
    pareceres: list[Parecer],
) -> str:
    """Etapa 3 — confronto, uma única rodada."""
    outros = [p for p in pareceres if p.agente != agente.nome]
    resumo = "\n\n".join(
        f"[PARECER DE {p.agente.upper()}]\n"
        f"direção: {p.direcao} (confiança {p.confianca})\n"
        f"{p.justificativa}"
        for p in outros
    )

    proprio = next((p for p in pareceres if p.agente == agente.nome), None)

    secoes = [
        f"[SEU PAPEL]\n{agente.papel}",
        f"[SEU VIÉS DECLARADO]\n{agente.vies_declarado}",
        f"[SUAS INSTRUÇÕES]\n{agente.instrucoes}",
    ]
    contexto = _bloco_contexto(briefing, agente.insumos)
    if contexto:
        secoes.append(contexto)
    secoes.append(_bloco_fonte(briefing, agente.insumos))

    if proprio:
        secoes.append(
            f"[SUA POSIÇÃO INICIAL]\ndireção: {proprio.direcao} "
            f"(confiança {proprio.confianca})\n{proprio.justificativa}"
        )

    secoes.append(f"[PARECERES DOS DEMAIS AGENTES]\n{resumo}")
    secoes.append(
        "[TAREFA]\nLeia os pareceres acima e reavalie. Você é **obrigado** a "
        "responder ao contra-argumento mais forte contra a sua posição — "
        "registre-o em 'contra_argumento'. Mudar de posição é legítimo e deve "
        "vir com 'mudou_de_posicao': true e a razão na justificativa. Manter a "
        "posição também é legítimo, desde que você enfrente a objeção em vez de "
        "repeti-la de volta."
    )
    return "\n\n".join(secoes)


def consultar_agente(agente: Agente, prompt: str) -> dict:
    """Fronteira única com a API da Anthropic.

    Toda a orquestração acima é determinística e testável sem rede; esta função
    é o único ponto que os testes substituem. A chamada em si mora em
    `apps/workers/agentes/fronteira.py`; aqui só se escolhe modelo, system
    prompt e orçamento de tokens do painel.
    """
    return consultar(agente.modelo, _SYSTEM, prompt, max_tokens=MAX_TOKENS)


def _parse_parecer(
    agente: Agente,
    etapa: str,
    cru: dict,
    anterior: Optional[Parecer] = None,
) -> Parecer:
    """Converte a resposta do modelo em `Parecer`, degradando para abstenção.

    Resposta malformada vira abstenção com a razão registrada, nunca direção
    inventada: um erro de parse que virasse "sim" contaminaria o Score.
    """
    if "error" in cru:
        return Parecer(
            agente=agente.nome,
            etapa=etapa,  # type: ignore[arg-type]
            direcao="abster",
            confianca=0.0,
            justificativa=f"falha ao obter parecer: {cru['error']}",
        )

    direcao = cru.get("direcao")
    if direcao not in ("sim", "nao", "abster"):
        return Parecer(
            agente=agente.nome,
            etapa=etapa,  # type: ignore[arg-type]
            direcao="abster",
            confianca=0.0,
            justificativa=(
                f"direção inválida na resposta do modelo ({direcao!r}) — "
                "registrado como abstenção"
            ),
            injecao_detectada=bool(cru.get("injecao_detectada")),
        )

    try:
        confianca = float(cru.get("confianca", 0.0))
    except (TypeError, ValueError):
        confianca = 0.0
    confianca = min(max(confianca, 0.0), 1.0)

    peso = cru.get("peso_sugerido")
    try:
        peso = float(peso) if peso is not None else None
    except (TypeError, ValueError):
        peso = None
    if peso is not None and peso not in (0.5, 1.0, 2.0, 3.0):
        logger.warning("[PAINEL] %s sugeriu peso inválido %s — descartado", agente.nome, peso)
        peso = None

    forca = cru.get("forca_objecao")
    if forca not in ("decisivo", "plausivel", "nenhum", None):
        forca = None

    mudou = bool(cru.get("mudou_de_posicao"))
    if anterior is not None:
        # O modelo pode errar a autodeclaração; a comparação é o que vale.
        mudou = anterior.direcao != direcao

    return Parecer(
        agente=agente.nome,
        etapa=etapa,  # type: ignore[arg-type]
        direcao=direcao,
        confianca=confianca,
        justificativa=str(cru.get("justificativa") or "").strip(),
        peso_sugerido=peso,
        categoria_sugerida=cru.get("categoria_sugerida") or None,
        contra_argumento=cru.get("contra_argumento") or None,
        forca_objecao=forca,  # type: ignore[arg-type]
        mudou_de_posicao=mudou,
        direcao_anterior=anterior.direcao if anterior else None,
        injecao_detectada=bool(cru.get("injecao_detectada")),
    )


def rodar_painel(
    briefing: Briefing,
    agentes: Optional[list[Agente]] = None,
    consultar: Callable[[Agente, str], dict] = consultar_agente,
) -> ResultadoPainel:
    """Executa as etapas 2 a 4 sobre uma votação.

    Etapa 1 (briefing) é o pipeline de enriquecimento, que já existe. Etapa 5
    (PR e mesa decisora) é humana e fica fora deste módulo por desenho.
    """
    painel = agentes if agentes is not None else carregar_painel()
    iniciado = datetime.now(timezone.utc).isoformat()
    erros: list[str] = []

    # ── Etapa 2: análise independente ──
    analise: list[Parecer] = []
    for agente in painel:
        if not agente.participa_da_analise:
            continue
        cru = consultar(agente, montar_prompt_analise(agente, briefing))
        if "error" in cru:
            erros.append(f"{agente.nome}/analise: {cru['error']}")
        analise.append(_parse_parecer(agente, "analise", cru))

    # ── Etapa 3: confronto, rodada única ──
    confronto: list[Parecer] = []
    for agente in painel:
        anterior = next((p for p in analise if p.agente == agente.nome), None)
        cru = consultar(agente, montar_prompt_confronto(agente, briefing, analise))
        if "error" in cru:
            erros.append(f"{agente.nome}/confronto: {cru['error']}")
        confronto.append(_parse_parecer(agente, "confronto", cru, anterior=anterior))

    # ── Etapa 4: veredito ──
    apuracao: Apuracao = apurar(confronto)

    meta = MetaExecucao(
        modelos={a.nome: a.modelo for a in painel},
        hashes_instrucoes={a.nome: a.hash_instrucoes for a in painel},
        versoes_agentes={a.nome: a.versao for a in painel},
        iniciado_em=iniciado,
        concluido_em=datetime.now(timezone.utc).isoformat(),
        erros=erros,
    )

    return ResultadoPainel(
        fonte=briefing.fonte,
        fonte_id=briefing.fonte_id,
        pareceres_analise=analise,
        pareceres_confronto=confronto,
        apuracao=apuracao,
        meta=meta,
    )

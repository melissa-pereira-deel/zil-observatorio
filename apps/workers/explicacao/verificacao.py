"""Verificação de alegações — o único lugar onde um agente usa ferramenta.

O fluxo, depois das lentes e do contraditor, antes da síntese:

    trechos (anônimos, embaralhados)
      → extrator (LLM, cego)          alegações com tipo, conceito, valor, período
      → resolver (código)              catálogo.resolver(conceito) → séries candidatas
      → verificador (LLM + 1 ferramenta) consulta só as candidatas, no período
      → comparar (código)              número dentro da tolerância? quem disse vale a conta
      → Verificacao[]                  → síntese (obrigada a manter o contradito) → revisor

Por que assim — cada decisão corta um caminho por onde o viés entraria:

- **Cegueira.** O extrator recebe trechos com ids opacos, embaralhados por
  hash do conteúdo, sem o nome da lente nem a direção do parecer. O
  verificador recebe uma alegação e as candidatas — a assinatura de
  `montar_prompt_verificacao` não aceita parecer, então não há como vazar
  por descuido (mesmo truque do painel, `montar_prompt_analise`).
- **Escrutínio simétrico.** Toda alegação de toda lente E da justificação do
  autor passa pela mesma extração. A taxa de contradição por origem
  (`metricas_verificacao`) é o que acusa um verificador assimétrico.
- **Ferramenta fechada.** `consultar_serie` aceita só refs das candidatas
  resolvidas para aquela alegação; o resto é recusado e registrado antes de
  tocar a rede. Não há URL, não há busca.
- **A conta vale mais que o julgamento.** Para alegação quantitativa, o
  veredito sai da comparação determinística entre o valor alegado e a
  observação que o próprio harness consultou. Se o modelo disser outra
  coisa, prevalece a conta e fica `divergencia_verificador`. Se a observação
  não estiver entre as consultas registradas, é `inconclusiva` — o modelo não
  confirma número que o código não viu.
- **Fato ≠ interpretação.** Alegação causal não chega ao verificador:
  `nao_verificavel_por_dado`, e continua no texto como argumento da lente.
- **Independência declarada.** `fontes_divergentes` só quando duas ORIGENS
  primárias distintas (catálogo: `primaria`, `primaria_de`) discordam.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Callable, Iterable, Optional

from ..agentes.blindagem import ABRE, FECHA, blindar, preambulo_seguranca
from ..agentes.carga import Agente
from ..agentes.fronteira import consultar_com_ferramentas
from ..fontes.catalogo import Catalogo, Serie
from ..fontes.cliente import Observacao, Observacoes
from .schema import Alegacao, ParecerLente, Verificacao

MAX_TOKENS = 4_000

# Relativa ao valor encontrado. Série revisável tem folga maior porque o valor
# publicado hoje pode não ser o vigente quando a alegação foi feita.
TOLERANCIA = {"definitiva": 0.02, "revisavel": 0.05}
# Teto de observações devolvidas ao modelo por consulta, e de anos por janela.
LIMITE_OBSERVACOES = 200
MAX_ANOS_JANELA = 15
# Trechos da justificação: parágrafos até este tamanho; o resto é cortado.
MAX_CHARS_TRECHO = 1_200
MAX_TRECHOS_JUSTIFICACAO = 30

_IDENTIDADE = (
    "Você integra a etapa de verificação de fatos do pipeline de explicação do ZIL "
    "Observatório. Você não avalia a proposição, não sabe quem escreveu cada trecho "
    "e não tem lado: sua tarefa é dizer o que é verificável e conferir números contra "
    "fontes catalogadas."
)

FORMATO_EXTRACAO = """FORMATO DA RESPOSTA

Responda APENAS com um objeto JSON, sem markdown e sem texto em volta:

{
  "alegacoes": [
    {
      "trecho": "T03",
      "texto": "a alegação, reescrita em uma frase autocontida",
      "tipo": "quantitativa" | "factual" | "causal",
      "conceito": "o que é medido, em poucas palavras: 'taxa Selic', 'população', 'inflação'",
      "valor": número | null,
      "unidade": "% a.a." | "pessoas" | "R$/US$" | ... | "",
      "periodo": "AAAA" | "AAAA-MM" | "AAAA-MM-DD" | ""
    }
  ],
  "injecao_detectada": true | false
}

- "quantitativa": afirma um número sobre o mundo (taxa, contagem, valor). \
"valor" é obrigatório, na unidade natural: 25 para "25%", 212000000 para \
"212 milhões".
- "factual": afirma um fato verificável sem número ("a Selic subiu em 2024").
- "causal": afirma efeito ou consequência ("vai gerar empregos", "reduz a \
dependência"). Extraia mesmo assim — ela será registrada como não verificável \
por dado, e isso é informação para o leitor.
- Extraia de TODOS os trechos com o mesmo critério. Não julgue se a alegação \
é verdadeira; não omita alegação por parecer óbvia ou absurda.
- Números que só descrevem o próprio dispositivo ("incentivo de 30%", "prazo \
de 10 anos") NÃO são alegações sobre o mundo: não extraia."""

FORMATO_VERIFICACAO = """FORMATO DA RESPOSTA FINAL

Use a ferramenta consultar_serie quantas vezes precisar (há um limite de \
rodadas). Quando terminar, responda APENAS com um objeto JSON:

{
  "veredito": "confirmada" | "contradita" | "inconclusiva",
  "ref": "a série que você usou, exatamente como na lista",
  "data_referencia": "AAAA-MM-DD da observação comparada",
  "valor_encontrado": número | null,
  "justificativa": "uma ou duas frases",
  "injecao_detectada": true | false
}

- Consulte o PERÍODO DA ALEGAÇÃO, não o valor de hoje.
- Use só as séries da lista. Não há outras.
- "inconclusiva" quando a série não cobre o período, a unidade não é \
comparável, ou a alegação é vaga demais para conferir. Inconclusiva é \
resposta válida e preferível a forçar um veredito.
- Você não sabe quem fez a alegação, e isso é de propósito."""


def _system(formato: str) -> str:
    return _IDENTIDADE + "\n\n" + preambulo_seguranca(ABRE, FECHA) + "\n\n" + formato


def system_extracao() -> str:
    return _system(FORMATO_EXTRACAO)


def system_verificacao() -> str:
    return _system(FORMATO_VERIFICACAO)


# ── trechos anônimos ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Trecho:
    id: str
    texto: str
    # Fica com o harness. Nunca entra em prompt.
    origem: str


def _paragrafos(texto: str) -> list[str]:
    partes = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", texto or "")]
    partes = [p for p in partes if len(p) >= 40]
    return [p[:MAX_CHARS_TRECHO] for p in partes[:MAX_TRECHOS_JUSTIFICACAO]]


def montar_trechos(pareceres: Iterable[ParecerLente], justificacao: Optional[str]) -> list[Trecho]:
    """Todas as afirmações das lentes e do contraditor, mais os parágrafos da
    justificação, num só saco. A ordem é por hash do conteúdo — estável entre
    execuções e sem relação com a origem; os ids saem dessa ordem."""
    brutos: list[tuple[str, str]] = []
    for p in pareceres:
        if not p.disponivel:
            continue
        for a in p.afirmacoes:
            brutos.append((a.texto.strip(), p.lente))
        for o in p.omissoes_da_justificacao:
            brutos.append((o.strip(), p.lente))
    for par in _paragrafos(justificacao or ""):
        brutos.append((par, "justificacao"))

    vistos: set[str] = set()
    unicos = []
    for texto, origem in brutos:
        if texto and texto not in vistos:
            vistos.add(texto)
            unicos.append((texto, origem))
    unicos.sort(key=lambda x: hashlib.sha256(x[0].encode("utf-8")).hexdigest())
    return [Trecho(id=f"T{i:02d}", texto=t, origem=o) for i, (t, o) in enumerate(unicos, start=1)]


def montar_prompt_extracao(agente: Agente, trechos: list[Trecho]) -> str:
    """A assinatura não recebe pareceres nem nomes de lente: cegueira por
    construção. O texto dos trechos é dado não confiável — vem da
    justificação do autor ou de saída de modelo."""
    corpo = "\n\n".join(f"[{t.id}]\n{blindar(t.texto)}" for t in trechos) or "[nenhum trecho]"
    return "\n\n".join([
        f"[SEU PAPEL]\n{agente.papel}",
        f"[SEU VIÉS DECLARADO]\n{agente.vies_declarado}",
        f"[SUAS INSTRUÇÕES]\n{agente.instrucoes}",
        f"[TRECHOS — ordem aleatória, autoria omitida]\n{ABRE}\n{corpo}\n{FECHA}",
        "[TAREFA]\nExtraia as alegações no formato JSON especificado, indicando o id do trecho de cada uma.",
    ])


def _float(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def parse_alegacoes(cru: dict, trechos: list[Trecho]) -> tuple[list[Alegacao], list[str]]:
    """Alegação malformada ou com trecho inexistente é descartada com erro
    registrado — nunca atribuída a uma origem por palpite."""
    if "error" in cru:
        return [], [f"extração falhou: {cru['error']}"]
    origem = {t.id: t.origem for t in trechos}
    alegacoes: list[Alegacao] = []
    erros: list[str] = []
    for bruto in cru.get("alegacoes") or []:
        tid = str(bruto.get("trecho") or "")
        if tid not in origem:
            erros.append(f"alegação com trecho desconhecido {tid!r} descartada")
            continue
        try:
            alegacoes.append(
                Alegacao(
                    id=f"A{len(alegacoes) + 1:02d}",
                    texto=str(bruto.get("texto") or ""),
                    tipo=bruto.get("tipo"),
                    conceito=str(bruto.get("conceito") or ""),
                    trecho=tid,
                    origem=origem[tid],
                    valor=_float(bruto.get("valor")),
                    unidade=str(bruto.get("unidade") or ""),
                    periodo=str(bruto.get("periodo") or ""),
                )
            )
        except ValueError as e:
            erros.append(f"alegação descartada: {e}")
    return alegacoes, erros


# ── resolver e ferramenta ─────────────────────────────────────────────────────

def candidatas_para(alegacao: Alegacao, catalogo: Catalogo) -> list[Serie]:
    """Séries que podem conferir esta alegação: casamento por conceito, só
    em fontes habilitadas. É código, não modelo — e é a lista inteira que o
    verificador vai ver; ele escolhe dentro dela, não fora."""
    series = catalogo.resolver([alegacao.conceito, alegacao.texto])
    return [s for s in series if catalogo.fontes[s.fonte].habilitada]


def ferramenta_consultar_serie(candidatas: list[Serie]) -> dict:
    return {
        "name": "consultar_serie",
        "description": (
            "Consulta uma série temporal do catálogo curado do projeto num intervalo de datas. "
            "Devolve as observações [data, valor] com unidade e frequência. Só as séries listadas existem."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "enum": [s.ref for s in candidatas]},
                "inicio": {"type": "string", "description": "AAAA-MM-DD"},
                "fim": {"type": "string", "description": "AAAA-MM-DD"},
            },
            "required": ["ref", "inicio", "fim"],
        },
    }


ConsultarDados = Callable[..., Observacoes]


class Executor:
    """Executa `consultar_serie` para UMA alegação. Recusa, registra e segue.

    As consultas bem-sucedidas ficam em `consultas`: é delas — e não da
    resposta do modelo — que a comparação tira o valor encontrado.
    """

    def __init__(self, catalogo: Catalogo, candidatas: list[Serie], consultar_dados: ConsultarDados) -> None:
        self.catalogo = catalogo
        self.candidatas = {s.ref: s for s in candidatas}
        self.consultar_dados = consultar_dados
        self.consultas: list[Observacoes] = []
        self.recusas: list[str] = []

    def __call__(self, nome: str, argumentos: dict) -> dict:
        if nome != "consultar_serie":
            self.recusas.append(f"ferramenta inexistente: {nome}")
            return {"erro": f"ferramenta {nome!r} não existe"}
        ref = str(argumentos.get("ref") or "")
        if ref not in self.catalogo.refs:
            self.recusas.append(f"série fora do catálogo: {ref}")
            return {"erro": f"{ref!r} não está no catálogo; use uma das séries listadas"}
        if ref not in self.candidatas:
            self.recusas.append(f"série fora das candidatas: {ref}")
            return {"erro": f"{ref!r} não é candidata para esta alegação; use uma das séries listadas"}
        try:
            inicio = date.fromisoformat(str(argumentos.get("inicio"))[:10])
            fim = date.fromisoformat(str(argumentos.get("fim"))[:10])
        except ValueError:
            return {"erro": "datas inválidas: use AAAA-MM-DD"}
        if (fim - inicio).days > MAX_ANOS_JANELA * 366:
            return {"erro": f"intervalo maior que {MAX_ANOS_JANELA} anos; consulte o período da alegação"}

        serie = self.candidatas[ref]
        res = self.consultar_dados(serie, inicio, fim, catalogo=self.catalogo)
        if not res.ok:
            return {"erro": res.erro}
        self.consultas.append(res)
        obs = res.observacoes[-LIMITE_OBSERVACOES:]
        return {
            "ref": ref,
            "descricao": serie.descricao,
            "unidade": serie.unidade,
            "frequencia": serie.frequencia,
            "revisavel": serie.revisavel,
            "observacoes": [[o.data, o.valor] for o in obs],
            "truncado": len(res.observacoes) > len(obs),
        }

    def observacao(self, ref: Optional[str], data_referencia: Optional[str], periodo: str) -> Optional[tuple[str, Observacao]]:
        """A observação comparável, entre as consultas registradas. Prefere a
        data que o verificador disse ter usado; senão, o período da alegação."""
        alvos = [ref] if ref else list(self.candidatas)
        for chave in (data_referencia or "", periodo or ""):
            if not chave:
                continue
            for r in alvos:
                achadas = [o for c in self.consultas if c.ref == r for o in c.observacoes if o.data.startswith(chave[:10])]
                if achadas:
                    return r, max(achadas, key=lambda o: o.data)
        return None


def montar_prompt_verificacao(agente: Agente, alegacao: Alegacao, candidatas: list[Serie]) -> str:
    """A assinatura não recebe parecer, lente nem conclusão: o verificador
    não sabe de onde a alegação veio. O texto dela é dado não confiável."""
    linhas = [
        f"- {s.ref}: {s.descricao} · {s.unidade} · {s.frequencia} · "
        f"{'revisável' if s.revisavel else 'definitiva'}" + (f" · nota: {s.nota}" if s.nota else "")
        for s in candidatas
    ]
    dados = [f"tipo: {alegacao.tipo}", f"conceito: {alegacao.conceito}"]
    if alegacao.valor is not None:
        dados.append(f"valor alegado: {alegacao.valor} {alegacao.unidade}".strip())
    dados.append(f"período: {alegacao.periodo or '(não informado — identifique pelo texto ou responda inconclusiva)'}")
    return "\n\n".join([
        f"[SEU PAPEL]\n{agente.papel}",
        f"[SUAS INSTRUÇÕES]\n{agente.instrucoes}",
        f"[ALEGAÇÃO]\n{ABRE}\n{blindar(alegacao.texto)}\n{FECHA}\n" + "\n".join(dados),
        "[SÉRIES DISPONÍVEIS — as únicas que existem]\n" + "\n".join(linhas),
        "[TAREFA]\nConsulte a série adequada no período da alegação e responda no formato especificado.",
    ])


# ── comparação determinística ─────────────────────────────────────────────────

def arredondamento(valor: float) -> float:
    """Metade da última casa significativa do número alegado: "13%" cobre
    12,5–13,5; "212 milhões" cobre ±500 mil. Quem arredonda não mente."""
    try:
        exp = Decimal(str(valor)).normalize().as_tuple().exponent
    except InvalidOperation:
        return 0.0
    if not isinstance(exp, int):
        return 0.0
    return 0.5 * (10 ** exp)


def tolerancia(alegado: float, encontrado: float, revisavel: bool) -> float:
    relativa = TOLERANCIA["revisavel" if revisavel else "definitiva"] * abs(encontrado)
    return max(relativa, arredondamento(alegado))


def comparar(alegado: float, encontrado: float, revisavel: bool) -> tuple[str, float]:
    tol = tolerancia(alegado, encontrado, revisavel)
    return ("confirmada" if abs(alegado - encontrado) <= tol else "contradita"), tol


ConsultarFerramentas = Callable[..., dict]


def consultar_verificador(agente: Agente, prompt: str, *, ferramentas: list[dict], executor, registro: list) -> dict:
    """A fronteira real para o verificador."""
    return consultar_com_ferramentas(
        agente.modelo, system_verificacao(), prompt,
        ferramentas=ferramentas, executor=executor, registro=registro, max_tokens=MAX_TOKENS,
    )


@dataclass
class ResultadoVerificacao:
    verificacoes: list[Verificacao] = field(default_factory=list)
    erros: list[str] = field(default_factory=list)
    injecao_detectada: bool = False


def _divergentes(executor: Executor, catalogo: Catalogo, alegacao: Alegacao, data_ref: str) -> bool:
    """Duas origens primárias distintas, mesma data, valores fora da
    tolerância entre si. Origem secundária não conta (catálogo)."""
    por_origem: dict[str, tuple[float, bool]] = {}
    for c in executor.consultas:
        serie = executor.candidatas[c.ref]
        origem = catalogo.origem_independente(serie)
        if not origem:
            continue
        obs = [o for o in c.observacoes if o.data.startswith(data_ref[:10])]
        if obs:
            por_origem.setdefault(origem, (obs[-1].valor, serie.revisavel))
    valores = list(por_origem.values())
    for i in range(len(valores)):
        for j in range(i + 1, len(valores)):
            (a, ra), (b, rb) = valores[i], valores[j]
            if abs(a - b) > tolerancia(a, b, ra or rb):
                return True
    return False


def verificar(
    alegacoes: list[Alegacao],
    *,
    agente: Agente,
    catalogo: Catalogo,
    consultar_ferramentas: ConsultarFerramentas,
    consultar_dados: ConsultarDados,
    max_alegacoes: int,
) -> ResultadoVerificacao:
    res = ResultadoVerificacao()
    verificadas = 0
    for a in alegacoes:
        if a.tipo == "causal":
            res.verificacoes.append(Verificacao(alegacao=a, veredito="nao_verificavel_por_dado",
                                                justificativa="alegação causal: não há série que a teste; permanece como argumento"))
            continue
        candidatas = candidatas_para(a, catalogo)
        if not candidatas:
            res.verificacoes.append(Verificacao(alegacao=a, veredito="sem_fonte_curada",
                                                justificativa="nenhuma série do catálogo cobre este conceito"))
            continue
        refs = [s.ref for s in candidatas]
        if verificadas >= max_alegacoes:
            res.verificacoes.append(Verificacao(alegacao=a, veredito="nao_verificada_limite", candidatas=refs))
            continue
        verificadas += 1

        executor = Executor(catalogo, candidatas, consultar_dados)
        registro: list[dict] = []
        cru = consultar_ferramentas(
            agente, montar_prompt_verificacao(agente, a, candidatas),
            ferramentas=[ferramenta_consultar_serie(candidatas)], executor=executor, registro=registro,
        )
        v = Verificacao(alegacao=a, veredito="inconclusiva", candidatas=refs, chamadas=registro, recusas=list(executor.recusas))
        if "error" in cru:
            v.justificativa = f"verificador indisponível: {cru['error']}"
            res.erros.append(f"{agente.nome}/{a.id}: {cru['error']}")
            res.verificacoes.append(v)
            continue
        res.injecao_detectada = res.injecao_detectada or bool(cru.get("injecao_detectada"))
        do_modelo = cru.get("veredito") if cru.get("veredito") in ("confirmada", "contradita", "inconclusiva") else "inconclusiva"
        v.justificativa = str(cru.get("justificativa") or "")
        ref_modelo = cru.get("ref") if cru.get("ref") in executor.candidatas else None

        if a.tipo == "quantitativa":
            achada = executor.observacao(ref_modelo, cru.get("data_referencia"), a.periodo)
            if achada is None:
                v.veredito = "inconclusiva"
                v.justificativa = (v.justificativa + " · " if v.justificativa else "") + \
                    "valor não conferido: nenhuma observação do período entre as consultas registradas"
            else:
                ref, obs = achada
                serie = executor.candidatas[ref]
                veredito, tol = comparar(a.valor, obs.valor, serie.revisavel)
                v.ref, v.data_referencia, v.valor_encontrado, v.tolerancia = ref, obs.data, obs.valor, tol
                v.conferido_por = "codigo"
                v.divergencia_verificador = do_modelo in ("confirmada", "contradita") and do_modelo != veredito
                v.veredito = veredito
                if _divergentes(executor, catalogo, a, obs.data):
                    v.veredito = "fontes_divergentes"
                if serie.revisavel:
                    v.nota_vintage = (
                        f"série revisável: comparado com o valor publicado hoje para {obs.data}; "
                        "o vigente quando a alegação foi feita pode ter sido outro"
                    )
        else:
            v.veredito = do_modelo
            v.ref = ref_modelo
            v.conferido_por = "modelo"
        res.verificacoes.append(v)
    return res


# ── saídas para o leitor e para a curadoria ───────────────────────────────────

def para_prompt_sintese(verificacoes: list[Verificacao]) -> str:
    """O bloco que a síntese recebe. A origem aparece aqui — a síntese
    atribui argumentos às lentes — e a obrigação vem junto."""
    if not verificacoes:
        return ""
    linhas = []
    for v in verificacoes:
        a = v.alegacao
        base = f"- {a.id} ({a.origem}, {a.tipo}): {a.texto} → {v.veredito.upper()}"
        if v.valor_encontrado is not None:
            base += f"; {v.ref} registra {v.valor_encontrado} em {v.data_referencia}"
        if v.nota_vintage:
            base += f"; {v.nota_vintage}"
        linhas.append(base)
    return (
        "[VERIFICAÇÕES — conferidas contra fontes catalogadas]\n" + "\n".join(linhas) + "\n\n"
        "OBRIGAÇÕES: toda alegação CONTRADITA tem que aparecer no texto marcada como contradita, com o "
        "valor encontrado e a fonte, e o seu id tem que estar em \"alegacoes_contraditas\". Nunca repita "
        "um número contradito como se fosse fato, e nunca o use no resumo didático. Alegação "
        "inconclusiva, sem fonte ou não verificável não vira fato: atribua-a a quem a fez."
    )


def fila_humana(fonte: str, fonte_id: str, verificacoes: list[Verificacao]) -> list[dict]:
    """O que a curadoria precisa decidir. Emitido como YAML pelo script, como
    o dossiê: o modelo nunca decide o destino de uma contradição."""
    return [
        {
            "proposicao": f"{fonte}:{fonte_id}",
            "alegacao": v.alegacao.texto,
            "origem": v.alegacao.origem,
            "valor_alegado": v.alegacao.valor,
            "veredito": v.veredito,
            "ref": v.ref,
            "data_referencia": v.data_referencia,
            "valor_encontrado": v.valor_encontrado,
            "tolerancia": v.tolerancia,
            "nota_vintage": v.nota_vintage or None,
            "decisao": None,  # preenchida por humano
        }
        for v in verificacoes
        if v.requer_humano
    ]


def metricas_verificacao(verificacoes: list[Verificacao]) -> dict:
    """Métricas 12 a 14 do plano, por execução. A agregação por lote (e a
    comparação de assimetria entre origens) é da calibração."""
    por_veredito: dict[str, int] = {}
    por_origem: dict[str, dict[str, int]] = {}
    for v in verificacoes:
        por_veredito[v.veredito] = por_veredito.get(v.veredito, 0) + 1
        o = por_origem.setdefault(v.alegacao.origem or "?", {"alegacoes": 0, "verificadas": 0, "contraditas": 0})
        o["alegacoes"] += 1
        if v.veredito in ("confirmada", "contradita", "fontes_divergentes"):
            o["verificadas"] += 1
        if v.veredito == "contradita":
            o["contraditas"] += 1
    total = len(verificacoes)
    verificaveis = sum(1 for v in verificacoes if v.veredito not in ("nao_verificavel_por_dado", "sem_fonte_curada"))
    return {
        "alegacoes": total,
        "por_veredito": por_veredito,
        "por_origem": por_origem,
        "fracao_verificavel": round(verificaveis / total, 3) if total else None,
        "chamadas_ferramenta": sum(len(v.chamadas) for v in verificacoes),
        "recusas_ferramenta": sum(len(v.recusas) for v in verificacoes),
        "divergencias_verificador": sum(1 for v in verificacoes if v.divergencia_verificador),
        "fila_humana": sum(1 for v in verificacoes if v.requer_humano),
    }


def valores_verificados(verificacoes: list[Verificacao]) -> list[float]:
    """Números que a síntese pode usar por terem passado pela verificação:
    os encontrados nas fontes e os alegados que foram confirmados."""
    out: list[float] = []
    for v in verificacoes:
        if v.valor_encontrado is not None:
            out.append(v.valor_encontrado)
        if v.veredito == "confirmada" and v.alegacao.valor is not None:
            out.append(v.alegacao.valor)
    return out


def para_json(verificacoes: list[Verificacao]) -> list[dict]:
    from dataclasses import asdict

    return json.loads(json.dumps([asdict(v) for v in verificacoes], default=str))

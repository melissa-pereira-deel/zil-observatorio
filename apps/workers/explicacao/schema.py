"""Contrato de saída do pipeline de explicação.

Os limites de tamanho são **contrato, não instrução ao modelo**: o schema
rejeita na construção, e o pipeline reformula até duas vezes antes de marcar a
execução como inválida. Pedir "entre 240 e 640 caracteres" no prompt é
aconselhamento; validar no `__post_init__` é garantia.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

from ..agentes.meta import MetaExecucao

# (mínimo, máximo) em caracteres, inclusive. Pedidos da maintainer, 2026-10-21.
LIMITES: dict[str, tuple[int, int]] = {
    "resumo_didatico": (240, 640),
    "resumo_detalhado": (480, 2480),
}

# As dimensões que a análise sistêmica percorre. Uma lente roteada que não
# tenha nada a dizer sobre a sua dimensão diz isso explicitamente — e isso
# também é sinal (métrica 7).
DIMENSOES = (
    "publica",
    "civel",
    "ambiental",
    "juridica",
    "saude",
    "pesquisa",
    "economica",
)

TipoAfirmacao = Literal["literal", "inferencia"]


class TamanhoInvalido(ValueError):
    """Resumo fora dos limites. É o sinal para a síntese reformular."""

    def __init__(self, campo: str, tamanho: int) -> None:
        minimo, maximo = LIMITES[campo]
        self.campo, self.tamanho, self.minimo, self.maximo = campo, tamanho, minimo, maximo
        super().__init__(f"{campo}: {tamanho} caracteres, esperado entre {minimo} e {maximo}")


def _validar_tamanho(campo: str, texto: str) -> None:
    n = len(texto)
    minimo, maximo = LIMITES[campo]
    if not minimo <= n <= maximo:
        raise TamanhoInvalido(campo, n)


@dataclass(frozen=True)
class ResumoDidatico:
    texto: str

    def __post_init__(self) -> None:
        _validar_tamanho("resumo_didatico", self.texto)


@dataclass(frozen=True)
class ResumoDetalhado:
    texto: str

    def __post_init__(self) -> None:
        _validar_tamanho("resumo_detalhado", self.texto)


@dataclass(frozen=True)
class Afirmacao:
    """Uma coisa que uma lente afirma, com a sua natureza declarada.

    `literal` exige citação, e a citação é conferida contra o texto extraído
    pelo revisor. `inferencia` é raciocínio da lente e vai assim para o leitor.
    Misturar os dois é o que tornaria a análise inauditável.
    """

    lente: str
    tipo: TipoAfirmacao
    texto: str
    dimensao: str
    citacao: Optional[str] = None

    def __post_init__(self) -> None:
        if self.tipo not in ("literal", "inferencia"):
            raise ValueError(f"tipo de afirmação inválido: {self.tipo!r}")
        if self.dimensao not in DIMENSOES:
            raise ValueError(f"dimensão desconhecida: {self.dimensao!r} — válidas: {DIMENSOES}")
        if self.tipo == "literal" and not (self.citacao or "").strip():
            raise ValueError("afirmação literal sem citação")
        if not self.texto.strip():
            raise ValueError("afirmação vazia")


@dataclass
class ParecerLente:
    """O que uma lente devolveu sobre a proposição."""

    lente: str
    afirmacoes: list[Afirmacao] = field(default_factory=list)
    nada_a_dizer: bool = False
    # Só o contraditor preenche: o que a justificação do autor deixa de fora.
    omissoes_da_justificacao: list[str] = field(default_factory=list)
    injecao_detectada: bool = False
    erro: Optional[str] = None

    @property
    def disponivel(self) -> bool:
        return self.erro is None


@dataclass(frozen=True)
class Dissenso:
    """Duas lentes que discordam sobre um ponto. Vai para o leitor assim."""

    lente_a: str
    lente_b: str
    ponto: str

    def __post_init__(self) -> None:
        if self.lente_a == self.lente_b:
            raise ValueError("dissenso exige duas lentes distintas")
        if not self.ponto.strip():
            raise ValueError("dissenso sem ponto")


@dataclass
class AnaliseSistemica:
    causas_raizes: list[str]
    dependencias: list[str]
    fatores_limitantes: list[str]
    dimensoes: dict[str, str]
    dissensos: list[Dissenso]
    lentes: list[str]

    def __post_init__(self) -> None:
        desconhecidas = set(self.dimensoes) - set(DIMENSOES)
        if desconhecidas:
            raise ValueError(f"dimensões desconhecidas na análise: {sorted(desconhecidas)}")


Status = Literal["pronto", "invalido", "lentes_indisponiveis"]


@dataclass
class Explicacao:
    fonte: str
    fonte_id: str
    pipeline_versao: str
    resumo_didatico: Optional[ResumoDidatico]
    resumo_detalhado: Optional[ResumoDetalhado]
    analise: Optional[AnaliseSistemica]
    pareceres: list[ParecerLente]
    meta: MetaExecucao
    metricas: dict = field(default_factory=dict)
    problemas: list[str] = field(default_factory=list)
    status: Status = "pronto"
    # O contexto econômico que TODAS as lentes viram (apps/workers/fontes):
    # as observações com proveniência, para a explicação carregar os números
    # que leu em vez de um ponteiro para séries que vão mudar.
    contexto: Optional[dict] = None

    @property
    def houve_injecao(self) -> bool:
        return any(p.injecao_detectada for p in self.pareceres)

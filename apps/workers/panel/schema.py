"""Estruturas de dados do painel de curadoria.

Separadas da orquestração porque são o contrato que os testes e o runner da
calibração usam — e porque o `Parecer` é o artefato que vai a público
(docs/PRD-PAINEL.md §5, regra inviolável 5: todo parecer é público).
"""

from dataclasses import dataclass
from typing import Literal, Optional

# Reprodutibilidade é garantia comum a todos os pipelines de agentes; mora no
# núcleo e é reexportada aqui para que `from .schema import MetaExecucao` siga
# valendo para quem já importava.
from ..agentes.meta import MetaExecucao  # noqa: F401

# "abster" é resposta de primeira classe, não falha. O princípio operacional do
# projeto é "na dúvida sobre direção esperada, não classificar" (CLAUDE.md), e
# a abstenção é como um agente o exerce.
Direcao = Literal["sim", "nao", "abster"]

# Peso da votação no Score ZIL. Mesma tabela do PRD v1 §10 usada na curadoria
# manual — o painel sugere, a mesa pode alterar.
PESOS_VALIDOS = (0.5, 1.0, 2.0, 3.0)

# Força do contra-argumento do contraditor. A distinção é o achado mais útil do
# cargo: "plausivel" registra dissenso sem derrubar o consenso; "decisivo" o
# derruba (docs/PRD-PAINEL.md §7).
ForcaObjecao = Literal["decisivo", "plausivel", "nenhum"]


@dataclass
class Parecer:
    """Parecer de um agente sobre uma votação, numa etapa do fluxo."""

    agente: str
    etapa: Literal["analise", "confronto"]
    direcao: Direcao
    confianca: float
    justificativa: str

    peso_sugerido: Optional[float] = None

    # Categoria é SUGESTÃO REGISTRADA, nunca campo normativo: o ADR-004 deixou o
    # destino das 9 categorias ZIL em aberto, e a Fase 1 não mede acurácia de
    # categoria (docs/PRD-PAINEL.md §2.3). Não alimentar `data/direcoes` com
    # isto sem decisão de produto.
    categoria_sugerida: Optional[str] = None

    # Preenchido na etapa 3. O PRD obriga cada agente a responder ao
    # contra-argumento mais forte contra a sua própria posição.
    contra_argumento: Optional[str] = None
    forca_objecao: Optional[ForcaObjecao] = None
    mudou_de_posicao: bool = False
    direcao_anterior: Optional[Direcao] = None

    # Sinal de defesa: o agente relatou instrução embutida no texto de fonte.
    # Texto de ementa é escrito por terceiros, inclusive gabinetes com interesse
    # no score — é dado não confiável (regra inviolável 6).
    injecao_detectada: bool = False

    def __post_init__(self) -> None:
        if self.direcao not in ("sim", "nao", "abster"):
            raise ValueError(f"direcao inválida: {self.direcao!r}")
        if not 0.0 <= self.confianca <= 1.0:
            raise ValueError(f"confianca fora de [0,1]: {self.confianca}")
        if self.peso_sugerido is not None and self.peso_sugerido not in PESOS_VALIDOS:
            raise ValueError(
                f"peso {self.peso_sugerido} não está em {PESOS_VALIDOS}"
            )


# Três saídas, não duas. O PRD §7 descreve "proposta" e "contestada", mas
# tratar abstenção unânime como pauta contestada quebraria a própria métrica 5
# da Fase 1 ("15–35% de contestadas"): uma votação procedimental, em que todos
# se abstêm corretamente, entraria na conta como dissenso. São coisas
# diferentes — uma é desacordo real, a outra é ausência de matéria.
Resultado = Literal["proposta", "contestada", "sem_materia"]


@dataclass
class Apuracao:
    """Resultado da regra de consenso (docs/PRD-PAINEL.md §7)."""

    placar: str
    votos: dict[str, int]
    resultado: Resultado
    direcao_proposta: Optional[Direcao]
    motivo: str

    @property
    def contestada(self) -> bool:
        return self.resultado == "contestada"

    @property
    def gera_proposta(self) -> bool:
        """Só placar com consenso vira PR contra data/direcoes/."""
        return self.resultado == "proposta"


@dataclass
class ResultadoPainel:
    """Saída completa de uma execução do painel sobre uma votação."""

    fonte: str
    fonte_id: str
    pareceres_analise: list[Parecer]
    pareceres_confronto: list[Parecer]
    apuracao: Apuracao
    meta: MetaExecucao

    @property
    def houve_injecao(self) -> bool:
        return any(
            p.injecao_detectada
            for p in (*self.pareceres_analise, *self.pareceres_confronto)
        )

"""Definições de agente do painel de curadoria.

O mecanismo de carga — YAML, validação, hash de instruções, modelo pinado —
mora em `apps/workers/agentes/carga.py` e é compartilhado com os demais
pipelines. O que fica aqui é o que só o painel sabe: quais insumos existem,
quais agentes compõem o painel e em que ordem, e a regra de que agente de
análise independente não lê os pareceres dos outros.

As definições vivem em `data/painel/agentes/*.yml`, sob a mesma governança dos
dados editoriais. O motivo está no PRD-PAINEL §5: quem escreve as instruções
dos agentes controla o resultado, então as instruções são o novo centro de poder
e precisam de diff auditável — não de constante em código.
"""

from pathlib import Path
from typing import Optional

from ..agentes.carga import Agente, carregar_agente as _carregar_agente_generico
from ..agentes.carga import carregar_conjunto

# Mesma convenção de caminho do classificador e do router da Bússola: relativo
# ao próprio arquivo. Dentro do container `apps/workers` é montado em
# `/app/workers`, então isto resolve para `/data/painel/...` — que é por que o
# compose monta `./data:/data:ro`. Mexer nisto sem conferir no container quebra
# silenciosamente (ver CLAUDE.md, "Dados editoriais nos containers").
AGENTES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "painel" / "agentes"

# A ordem importa para a reprodutibilidade do briefing de confronto: pareceres
# concatenados em ordem estável produzem prompt estável. O contraditor vem por
# último porque só atua na etapa 3.
ORDEM_PAINEL = ("jurista", "economista", "industrial", "publicas", "contraditor")

INSUMOS_CONHECIDOS = frozenset(
    {
        "texto_integral",
        "leis_referenciadas",
        "ementa",
        "contexto_economico",
        "taxonomia",
        "bussula",
        "tramitacao",
        "pareceres_dos_outros",
    }
)

_ETAPAS_PADRAO = ("analise", "confronto")

__all__ = ["AGENTES_DIR", "ORDEM_PAINEL", "INSUMOS_CONHECIDOS", "Agente", "carregar_agente", "carregar_painel"]


def _sem_ancoragem(bruto: dict, origem: Path) -> None:
    """Um agente de análise independente que declarasse `pareceres_dos_outros`
    como insumo violaria a etapa 2 por configuração, não por bug. O PRD §6 é
    explícito: ancoragem entre agentes (risco R6) é o vício que invalidaria o
    painel, então isto é barrado na carga."""
    etapas = bruto.get("etapas") or _ETAPAS_PADRAO
    if "pareceres_dos_outros" in bruto["insumos"] and "analise" in etapas:
        raise ValueError(
            f"{origem.name}: agente que participa da etapa de análise independente "
            "não pode ter 'pareceres_dos_outros' como insumo — isso é ancoragem "
            "(PRD-PAINEL §6, risco R6)"
        )


def carregar_agente(caminho: Path) -> Agente:
    return _carregar_agente_generico(
        caminho,
        insumos_validos=INSUMOS_CONHECIDOS,
        etapas_padrao=_ETAPAS_PADRAO,
        validar_extra=_sem_ancoragem,
    )


def carregar_painel(diretorio: Optional[Path] = None) -> list[Agente]:
    """Carrega o painel inteiro, em ordem estável.

    Falha alto. O classificador tem taxonomia embutida como fallback porque
    classificar com 44% das keywords ainda produz algo; um painel com três
    agentes produziria placar sem significado e passaria pela regra de consenso
    como se tivesse cinco.
    """
    base = diretorio or AGENTES_DIR
    return carregar_conjunto(
        base,
        ordem=ORDEM_PAINEL,
        insumos_validos=INSUMOS_CONHECIDOS,
        etapas_padrao=_ETAPAS_PADRAO,
        validar_extra=_sem_ancoragem,
        mensagem_extras=(
            "agentes não previstos em ORDEM_PAINEL: {extras} — acrescentar agente "
            "muda o limiar de consenso e exige revisar consenso.py"
        ),
        mensagem_diretorio=(
            f"definições do painel não encontradas em {base} — dentro do container, "
            "confira o mount ./data:/data:ro"
        ),
    )

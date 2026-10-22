"""Agentes do pipeline de explicação.

Três vêm do painel por referência — jurista, economista, publicas — e não por
cópia: se as instruções deles mudarem lá, mudam aqui, e o hash registrado no
meta acusa. Os demais são próprios e vivem em `data/explicacao/agentes/`.

O `industrial` do painel fica de fora de propósito (ver `__init__`).
"""

from dataclasses import replace
from pathlib import Path
from typing import Optional

from ..agentes.carga import Agente, carregar_agente
from ..panel.agentes import carregar_painel

AGENTES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "explicacao" / "agentes"

# Insumos deste pipeline. `pareceres_dos_outros` é permitido só nas etapas de
# contradição e síntese — a validação está em `_sem_ancoragem_nas_lentes`.
INSUMOS_CONHECIDOS = frozenset({
    "ficha_fatos",
    "ementa",
    "dispositivo",
    "justificacao",
    "texto_integral",
    "leis_referenciadas",
    "temas_oficiais",
    "contexto_economico",
    "tramitacao",
    "taxonomia",
    "pareceres_dos_outros",
})

ETAPAS = ("lente", "contradicao", "sintese", "revisao")

# Os três emprestados do painel, e em que etapa atuam aqui.
HERDADOS = ("jurista", "economista", "publicas")


def _sem_ancoragem_nas_lentes(bruto: dict, origem: Path) -> None:
    etapas = bruto.get("etapas") or ("lente",)
    if "pareceres_dos_outros" in bruto["insumos"] and "lente" in etapas:
        raise ValueError(
            f"{origem.name}: lente não pode ler os pareceres das outras — isso é "
            "ancoragem (PRD-PAINEL §6, risco R6). Só contradição e síntese leem."
        )


def carregar_proprios(diretorio: Optional[Path] = None) -> dict[str, Agente]:
    base = diretorio or AGENTES_DIR
    if not base.exists():
        raise FileNotFoundError(
            f"definições da explicação não encontradas em {base} — dentro do container, "
            "confira o mount ./data:/data:ro"
        )
    agentes: dict[str, Agente] = {}
    for caminho in sorted(base.glob("*.yml")):
        a = carregar_agente(
            caminho,
            insumos_validos=INSUMOS_CONHECIDOS,
            etapas_padrao=("lente",),
            validar_extra=_sem_ancoragem_nas_lentes,
        )
        if a.nome in agentes:
            raise ValueError(f"agente duplicado: {a.nome}")
        agentes[a.nome] = a
    return agentes


def carregar_herdados() -> dict[str, Agente]:
    """Jurista, economista e publicas, com as instruções do painel e as etapas
    deste pipeline. `replace` mantém o hash das instruções idêntico ao de lá."""
    painel = {a.nome: a for a in carregar_painel()}
    return {n: replace(painel[n], etapas=("lente",)) for n in HERDADOS}


def carregar_agentes(diretorio: Optional[Path] = None) -> dict[str, Agente]:
    agentes = carregar_herdados()
    proprios = carregar_proprios(diretorio)
    colisao = set(agentes) & set(proprios)
    if colisao:
        raise ValueError(f"agente próprio com o mesmo nome de um herdado do painel: {sorted(colisao)}")
    agentes.update(proprios)
    return agentes

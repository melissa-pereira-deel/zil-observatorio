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
    # Verificação: trechos sem autoria (extrator) e uma alegação com as
    # séries candidatas (verificador). Nenhum dos dois vê lente nem parecer.
    "trechos_anonimos",
    "alegacao",
})

ETAPAS = ("lente", "contradicao", "sintese", "revisao", "extracao", "verificacao")
_CEGAS = ("extracao", "verificacao")

# Os três emprestados do painel, e em que etapa atuam aqui.
HERDADOS = ("jurista", "economista", "publicas")

# O que os herdados leem aqui além do que leem no painel. No painel o objeto é
# uma votação, e a ementa basta para dizer do que se trata; aqui o objeto é o
# texto da proposição, e a ementa omite o mecanismo. Na PNMCE (2026-10-28) o
# economista, só com a ementa, concluiu que não havia mecanismo econômico — e
# o contraditor o desmentiu citando o dispositivo. As instruções não mudam, e
# o hash continua o do painel; o que muda é o que chega a eles.
INSUMOS_ADICIONAIS = {
    "economista": ("dispositivo",),
    "publicas": ("dispositivo",),
}


def _sem_ancoragem_nas_lentes(bruto: dict, origem: Path) -> None:
    etapas = bruto.get("etapas") or ("lente",)
    if "pareceres_dos_outros" in bruto["insumos"] and "lente" in etapas:
        raise ValueError(
            f"{origem.name}: lente não pode ler os pareceres das outras — isso é "
            "ancoragem (PRD-PAINEL §6, risco R6). Só contradição e síntese leem."
        )
    if any(e in etapas for e in _CEGAS) and "pareceres_dos_outros" in bruto["insumos"]:
        raise ValueError(
            f"{origem.name}: extração e verificação são cegas — não leem pareceres nem "
            "sabem de que lente veio cada trecho. É o que torna o escrutínio simétrico."
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
    e insumos deste pipeline. `replace` mantém o hash das instruções idêntico
    ao de lá."""
    painel = {a.nome: a for a in carregar_painel()}
    herdados = {}
    for n in HERDADOS:
        extras = tuple(i for i in INSUMOS_ADICIONAIS.get(n, ()) if i not in painel[n].insumos)
        herdados[n] = replace(painel[n], etapas=("lente",), insumos=painel[n].insumos + extras)
    return herdados


def carregar_agentes(diretorio: Optional[Path] = None) -> dict[str, Agente]:
    agentes = carregar_herdados()
    proprios = carregar_proprios(diretorio)
    colisao = set(agentes) & set(proprios)
    if colisao:
        raise ValueError(f"agente próprio com o mesmo nome de um herdado do painel: {sorted(colisao)}")
    agentes.update(proprios)
    return agentes

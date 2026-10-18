"""Carga e validação das definições de agente do painel.

As definições vivem em `data/painel/agentes/*.yml`, sob a mesma governança dos
dados editoriais. O motivo está no PRD-PAINEL §5: quem escreve as instruções
dos agentes controla o resultado, então as instruções são o novo centro de poder
e precisam de diff auditável — não de constante em código.
"""

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

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

_CAMPOS_OBRIGATORIOS = ("agente", "versao", "papel", "vies_declarado", "insumos", "instrucoes")


@dataclass(frozen=True)
class Agente:
    """Definição imutável de um agente do painel."""

    nome: str
    versao: int
    papel: str
    vies_declarado: str
    insumos: tuple[str, ...]
    instrucoes: str
    modelo: str
    etapas: tuple[str, ...]

    @property
    def hash_instrucoes(self) -> str:
        """SHA-256 das instruções, para o meta.yml do parecer.

        Trunca em 16 hex: o suficiente para detectar que a instrução mudou entre
        duas execuções, que é o uso real (risco R2 — captura via instruções).
        """
        return hashlib.sha256(self.instrucoes.encode("utf-8")).hexdigest()[:16]

    @property
    def participa_da_analise(self) -> bool:
        return "analise" in self.etapas


def _validar(bruto: dict, origem: Path) -> None:
    faltando = [c for c in _CAMPOS_OBRIGATORIOS if not bruto.get(c)]
    if faltando:
        raise ValueError(f"{origem.name}: campos obrigatórios ausentes: {faltando}")

    desconhecidos = set(bruto["insumos"]) - INSUMOS_CONHECIDOS
    if desconhecidos:
        raise ValueError(
            f"{origem.name}: insumos desconhecidos {sorted(desconhecidos)} — "
            f"válidos: {sorted(INSUMOS_CONHECIDOS)}"
        )

    # Um agente de análise independente que declarasse `pareceres_dos_outros`
    # como insumo violaria a etapa 2 por configuração, não por bug. O PRD §6 é
    # explícito: ancoragem entre agentes (risco R6) é o vício que invalidaria o
    # painel, então isto é barrado na carga.
    etapas = bruto.get("etapas") or ["analise", "confronto"]
    if "pareceres_dos_outros" in bruto["insumos"] and "analise" in etapas:
        raise ValueError(
            f"{origem.name}: agente que participa da etapa de análise independente "
            "não pode ter 'pareceres_dos_outros' como insumo — isso é ancoragem "
            "(PRD-PAINEL §6, risco R6)"
        )


def carregar_agente(caminho: Path) -> Agente:
    with open(caminho, "r", encoding="utf-8") as f:
        bruto = yaml.safe_load(f)

    if not isinstance(bruto, dict):
        raise ValueError(f"{caminho.name}: YAML não é um mapeamento")

    _validar(bruto, caminho)

    etapas = tuple(bruto.get("etapas") or ("analise", "confronto"))
    return Agente(
        nome=bruto["agente"],
        versao=int(bruto["versao"]),
        papel=bruto["papel"],
        vies_declarado=bruto["vies_declarado"].strip(),
        insumos=tuple(bruto["insumos"]),
        instrucoes=bruto["instrucoes"].strip(),
        # Sem default silencioso: um modelo não pinado quebra a
        # reprodutibilidade que a regra inviolável 7 exige.
        modelo=bruto["modelo"],
        etapas=etapas,
    )


def carregar_painel(diretorio: Optional[Path] = None) -> list[Agente]:
    """Carrega o painel inteiro, em ordem estável.

    Falha alto. O classificador tem taxonomia embutida como fallback porque
    classificar com 44% das keywords ainda produz algo; um painel com três
    agentes produziria placar sem significado e passaria pela regra de consenso
    como se tivesse cinco.
    """
    base = diretorio or AGENTES_DIR
    if not base.exists():
        raise FileNotFoundError(
            f"definições do painel não encontradas em {base} — dentro do container, "
            "confira o mount ./data:/data:ro"
        )

    por_nome = {}
    for caminho in sorted(base.glob("*.yml")):
        agente = carregar_agente(caminho)
        if agente.nome in por_nome:
            raise ValueError(f"agente duplicado: {agente.nome}")
        por_nome[agente.nome] = agente

    faltando = [n for n in ORDEM_PAINEL if n not in por_nome]
    if faltando:
        raise ValueError(f"painel incompleto — faltam os agentes: {faltando}")

    extras = sorted(set(por_nome) - set(ORDEM_PAINEL))
    if extras:
        raise ValueError(
            f"agentes não previstos em ORDEM_PAINEL: {extras} — acrescentar agente "
            "muda o limiar de consenso e exige revisar consenso.py"
        )

    return [por_nome[n] for n in ORDEM_PAINEL]

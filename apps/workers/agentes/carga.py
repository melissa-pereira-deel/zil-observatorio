"""Carga e validação de definições de agente em YAML.

As definições vivem em `data/<pipeline>/agentes/*.yml`, sob a mesma governança
dos dados editoriais. O motivo está no PRD-PAINEL §5: quem escreve as
instruções dos agentes controla o resultado, então as instruções são o novo
centro de poder e precisam de diff auditável — não de constante em código.

Este módulo não sabe quais insumos existem nem quantos agentes um pipeline
tem: isso é tarefa. Ele recebe a lista de insumos válidos, a ordem esperada e,
se o pipeline tiver regras próprias (o painel proíbe agente de análise
independente que leia os pareceres dos outros), uma função de validação extra.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import yaml

CAMPOS_OBRIGATORIOS = ("agente", "versao", "papel", "vies_declarado", "insumos", "instrucoes")

ValidadorExtra = Callable[[dict, Path], None]


@dataclass(frozen=True)
class Agente:
    """Definição imutável de um agente."""

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
        """SHA-256 das instruções, para o meta de cada execução.

        Trunca em 16 hex: o suficiente para detectar que a instrução mudou entre
        duas execuções, que é o uso real (risco R2 — captura via instruções).
        """
        return hashlib.sha256(self.instrucoes.encode("utf-8")).hexdigest()[:16]

    def participa(self, etapa: str) -> bool:
        return etapa in self.etapas

    @property
    def participa_da_analise(self) -> bool:
        """Conveniência do painel, mantida pelo nome: `analise` é a etapa de
        análise independente de lá. Outros pipelines usam `participa(etapa)`."""
        return self.participa("analise")


def validar_definicao(
    bruto: dict,
    origem: Path,
    *,
    insumos_validos: frozenset[str],
    validar_extra: Optional[ValidadorExtra] = None,
) -> None:
    faltando = [c for c in CAMPOS_OBRIGATORIOS if not bruto.get(c)]
    if faltando:
        raise ValueError(f"{origem.name}: campos obrigatórios ausentes: {faltando}")

    desconhecidos = set(bruto["insumos"]) - insumos_validos
    if desconhecidos:
        raise ValueError(
            f"{origem.name}: insumos desconhecidos {sorted(desconhecidos)} — "
            f"válidos: {sorted(insumos_validos)}"
        )

    if validar_extra is not None:
        validar_extra(bruto, origem)


def carregar_agente(
    caminho: Path,
    *,
    insumos_validos: frozenset[str],
    etapas_padrao: tuple[str, ...] = (),
    validar_extra: Optional[ValidadorExtra] = None,
) -> Agente:
    with open(caminho, "r", encoding="utf-8") as f:
        bruto = yaml.safe_load(f)

    if not isinstance(bruto, dict):
        raise ValueError(f"{caminho.name}: YAML não é um mapeamento")

    validar_definicao(
        bruto, caminho, insumos_validos=insumos_validos, validar_extra=validar_extra
    )

    etapas = tuple(bruto.get("etapas") or etapas_padrao)
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


def carregar_conjunto(
    diretorio: Path,
    *,
    ordem: tuple[str, ...],
    insumos_validos: frozenset[str],
    etapas_padrao: tuple[str, ...] = (),
    validar_extra: Optional[ValidadorExtra] = None,
    mensagem_extras: Optional[str] = None,
    mensagem_diretorio: Optional[str] = None,
) -> list[Agente]:
    """Carrega um conjunto completo de agentes, em ordem estável.

    Falha alto. Um conjunto incompleto produziria um resultado sem significado
    que passaria pelas regras de síntese como se estivesse inteiro — no painel,
    três agentes passariam pela regra de consenso como se fossem cinco.

    A ordem importa para reprodutibilidade: pareceres concatenados em ordem
    estável produzem prompts estáveis.
    """
    if not diretorio.exists():
        raise FileNotFoundError(
            mensagem_diretorio or f"definições de agente não encontradas em {diretorio}"
        )

    por_nome: dict[str, Agente] = {}
    for caminho in sorted(diretorio.glob("*.yml")):
        agente = carregar_agente(
            caminho,
            insumos_validos=insumos_validos,
            etapas_padrao=etapas_padrao,
            validar_extra=validar_extra,
        )
        if agente.nome in por_nome:
            raise ValueError(f"agente duplicado: {agente.nome}")
        por_nome[agente.nome] = agente

    faltando = [n for n in ordem if n not in por_nome]
    if faltando:
        raise ValueError(f"painel incompleto — faltam os agentes: {faltando}")

    extras = sorted(set(por_nome) - set(ordem))
    if extras:
        raise ValueError(
            mensagem_extras.format(extras=extras)
            if mensagem_extras
            else f"agentes não previstos na ordem: {extras}"
        )

    return [por_nome[n] for n in ordem]

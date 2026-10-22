"""Reprodutibilidade de uma execução (PRD-PAINEL, regra inviolável 7).

Sem isto, uma atualização de modelo ou uma edição de instrução muda resultados
silenciosamente e a promessa de auditabilidade do projeto se quebra (risco
R5). O que fica registrado é o mínimo para dizer, meses depois, "esta saída
foi produzida por estes modelos, com estas instruções" — e para perceber
quando isso mudou.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MetaExecucao:
    modelos: dict[str, str]
    hashes_instrucoes: dict[str, str]
    versoes_agentes: dict[str, int]
    iniciado_em: str
    concluido_em: Optional[str] = None
    erros: list[str] = field(default_factory=list)

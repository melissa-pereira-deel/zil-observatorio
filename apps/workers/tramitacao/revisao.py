"""Caminho que a spec 013 §6.2 cita para os scripts de TRM-023. A implementação é a de packages/."""

from packages.tramitacao.revisao import (
    ArquivoRevisao,
    Consolidado,
    Decisao,
    EntradaConsolidada,
    EstadoEntrada,
    chave_marco,
    chave_rito,
    entradas_publicaveis,
    hash_entrada,
    ids_de_conteudo,
)

__all__ = [
    "ArquivoRevisao",
    "Consolidado",
    "Decisao",
    "EntradaConsolidada",
    "EstadoEntrada",
    "chave_marco",
    "chave_rito",
    "entradas_publicaveis",
    "hash_entrada",
    "ids_de_conteudo",
]

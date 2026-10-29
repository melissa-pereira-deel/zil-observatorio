"""Endpoints for Bússola ZIL — indicadores estratégicos."""

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from schemas.bussula import Indicador

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bussula", tags=["Bússola ZIL"])

# Relativo ao arquivo: na raiz do repo no host; dentro do container,
# apps/api está achatado em /app e isto resolve para /data/bussula/marcos.yml,
# fornecido pelo mount ./data:/data:ro (ver CLAUDE.md, "armadilhas").
_DATA_FILE = Path(__file__).parent.parent.parent.parent / "data" / "bussula" / "marcos.yml"


def carregar_indicadores(arquivo: Path = _DATA_FILE) -> list[Indicador]:
    """Lê e valida o YAML. Arquivo ausente devolve lista vazia, com aviso no
    log: antes era silêncio, e a Bússola respondia `[]` sem ninguém saber
    que o mount de dados tinha faltado."""
    if not arquivo.exists():
        logger.warning("Bússola: %s não existe — nenhum indicador servido", arquivo)
        return []
    with open(arquivo, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return [Indicador.model_validate(m) for m in data.get("marcos") or []]


@router.get("", response_model=list[Indicador])
def listar_marcos():
    """Retorna todos os indicadores estratégicos da Bússola ZIL."""
    return carregar_indicadores()


@router.get("/{codigo}", response_model=Indicador)
def obter_marco(codigo: str):
    """Retorna um indicador específico pelo código (ex: BUSSULA-FER-01)."""
    for m in carregar_indicadores():
        if m.codigo == codigo.upper():
            return m
    raise HTTPException(status_code=404, detail="Indicador não encontrado")

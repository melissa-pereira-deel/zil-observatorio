"""Endpoints for Bússola ZIL — indicadores estratégicos."""

from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/bussula", tags=["Bússola ZIL"])

_DATA_FILE = Path(__file__).parent.parent.parent.parent / "data" / "bussula" / "marcos.yml"


def _load_marcos() -> list[dict]:
    if not _DATA_FILE.exists():
        return []
    with open(_DATA_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("marcos") or []


@router.get("")
def listar_marcos():
    """Retorna todos os indicadores estratégicos da Bússola ZIL."""
    return _load_marcos()


@router.get("/{codigo}")
def obter_marco(codigo: str):
    """Retorna um indicador específico pelo código (ex: BUSSULA-FER-01)."""
    marcos = _load_marcos()
    for m in marcos:
        if m.get("codigo") == codigo.upper():
            return m
    raise HTTPException(status_code=404, detail="Indicador não encontrado")

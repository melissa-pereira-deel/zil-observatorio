"""Estado de revisão de data/tramitacao/, hash e publicação (spec 013 §6.2 e §6.8).

Implementação ÚNICA. Scripts importam por apps.workers.tramitacao.revisao; a API e o motor, por
packages.tramitacao.revisao, porque apps.workers não existe dentro do container da API.
"""

import hashlib
import json
from datetime import date
from typing import Literal, Mapping, Optional

from pydantic import BaseModel, ConfigDict, Field

from packages.tramitacao.tipos import Conjunto, Estrito, Revisao

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

_SUFIXO_RITO = {"camara": "CD", "senado": "SF", "congresso": "CN"}


class EstadoEntrada(Estrito):
    estado: Revisao
    hash: str = Field(pattern=r"^[0-9a-f]{12}$")
    registros: Conjunto[str] = []
    aprovado_em: Optional[date] = None
    revisado_por: Conjunto[str] = []


class ArquivoRevisao(Estrito):
    versao_publicada: int = Field(ge=0)
    publicada_em: Optional[date] = None
    entradas: dict[str, EstadoEntrada]


class _RegistroDeLote(BaseModel):
    # Escritos por script e podem evoluir: quem lê usa os campos que conhece e ignora o resto (§2.8).
    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)


class EntradaConsolidada(_RegistroDeLote):
    hash: str = Field(pattern=r"^[0-9a-f]{12}$")
    estado_resultante: Literal["rascunho", "revisado_agentes"]  # aprovar é só da maintainer (§6.6, §6.7)
    bloqueia_abertos: list[str]
    divergencia: bool


class Consolidado(_RegistroDeLote):
    lote: str
    rodada: int = Field(ge=1)
    consolidado_em: date
    entradas: dict[str, EntradaConsolidada]


class Decisao(_RegistroDeLote):
    lote: str
    aprovado_em: date
    aprovado_por: str
    minutos: Optional[int] = Field(default=None, ge=0)  # opcional em aprovar_tramitacao.py (§6.7)
    aprovadas: Conjunto[str]
    excluidas: dict[str, str] = {}
    sobreposicoes: dict[str, str] = {}


def hash_entrada(entrada: dict) -> str:
    texto = json.dumps(entrada, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def chave_rito(especie: str, casa_iniciadora: str) -> str:
    return f"{especie}_{_SUFIXO_RITO[casa_iniciadora]}"


def chave_marco(cod: str, casa: str) -> str:
    return cod if casa == "camara" else f"sf_{cod.lower()}"


def ids_de_conteudo(fases: dict, marcos: dict, ritos: dict, glossario: dict) -> dict[str, dict]:
    """id "<arquivo>/<chave>" → mapeamento bruto, para todos os arquivos de conteúdo (§2.1-3).

    Espera arquivos já validados: quem garante que não há chave repetida é a carga.
    """
    conteudo: dict[str, dict] = {}
    for entrada in fases.get("fases") or []:
        conteudo[f"fases/fase_{entrada['chave']}"] = entrada
    for entrada in fases.get("desfechos") or []:
        conteudo[f"fases/desfecho_{entrada['chave']}"] = entrada
    if fases.get("apensada"):
        conteudo["fases/apensada"] = fases["apensada"]
    for entrada in fases.get("regras") or []:
        conteudo[f"fases/regra_{entrada['id']}"] = entrada
    for entrada in marcos.get("marcos") or []:
        conteudo[f"marcos/{chave_marco(entrada['cod'], entrada['casa'])}"] = entrada
    for entrada in ritos.get("ritos") or []:
        conteudo[f"ritos/{chave_rito(entrada['especie'], entrada['casa_iniciadora'])}"] = entrada
    if ritos.get("pos_lei"):
        conteudo["ritos/pos_lei"] = ritos["pos_lei"]
    for entrada in glossario.get("entradas") or []:
        conteudo[f"glossario/{entrada['chave']}"] = entrada
    return conteudo


def entradas_publicaveis(conteudo: Mapping[str, dict], revisao: ArquivoRevisao) -> frozenset[str]:
    """Só `aprovado` com hash igual ao do conteúdo atual: editar a entrada a tira do ar sozinha."""
    return frozenset(
        id_entrada
        for id_entrada, estado in revisao.entradas.items()
        if estado.estado == "aprovado"
        and id_entrada in conteudo
        and estado.hash == hash_entrada(conteudo[id_entrada])
    )

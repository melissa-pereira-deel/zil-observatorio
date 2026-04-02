"""Client tipado para a API de Dados Abertos da Câmara dos Deputados.

Documentação: https://dadosabertos.camara.leg.br/swagger/api.html
"""

import time
import logging
from typing import Optional, Any
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}
MAX_RETRIES = 3
RETRY_DELAY = 2.0


@dataclass
class DeputadoAPI:
    id: int
    nome: str
    siglaPartido: Optional[str] = None
    siglaUf: Optional[str] = None
    urlFoto: Optional[str] = None
    email: Optional[str] = None
    nomeCivil: Optional[str] = None


@dataclass
class VotacaoAPI:
    id: str
    data: Optional[str] = None
    descricao: Optional[str] = None
    aprovacao: Optional[bool] = None
    votos_sim: Optional[int] = None
    votos_nao: Optional[int] = None


@dataclass
class VotoAPI:
    deputado_id: int
    deputado_nome: str
    deputado_partido: Optional[str]
    deputado_uf: Optional[str]
    voto: str  # "Sim", "Não", "Abstenção", etc.


@dataclass
class ProposicaoAPI:
    id: int
    siglaTipo: Optional[str] = None
    numero: Optional[int] = None
    ano: Optional[int] = None
    ementa: Optional[str] = None
    ementaDetalhada: Optional[str] = None
    dataApresentacao: Optional[str] = None
    statusProposicao: Optional[dict] = None
    urlInteiroTeor: Optional[str] = None


class CamaraClient:
    """Client para a API de Dados Abertos da Câmara dos Deputados."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=base_url,
            headers=HEADERS,
            timeout=30.0,
        )

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        """GET request com retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.client.get(path, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("dados", data)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503, 504):
                    wait = RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"HTTP {e.response.status_code} em {path}, aguardando {wait}s (tentativa {attempt + 1}/{MAX_RETRIES})...")
                    time.sleep(wait)
                    continue
                raise
            except httpx.RequestError as e:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Request error (tentativa {attempt + 1}): {e}, aguardando {wait}s...")
                    time.sleep(wait)
                    continue
                raise
        return []

    def _get_paginated(self, path: str, params: Optional[dict] = None, max_pages: int = 50) -> list:
        """GET com paginação automática."""
        params = params or {}
        params.setdefault("itens", 100)
        params.setdefault("pagina", 1)
        all_items = []

        for page in range(1, max_pages + 1):
            params["pagina"] = page
            items = self._get(path, params)
            if not items:
                break
            all_items.extend(items)
            logger.info(f"  Página {page}: {len(items)} itens (total: {len(all_items)})")
            if len(items) < params["itens"]:
                break
            time.sleep(0.5)  # respeitar rate limit

        return all_items

    # ── Deputados ──

    def listar_deputados(self, legislatura: Optional[int] = None) -> list[DeputadoAPI]:
        """Lista todos os deputados da legislatura atual (ou especificada)."""
        params = {}
        if legislatura:
            params["idLegislatura"] = legislatura

        dados = self._get_paginated("/deputados", params)
        return [
            DeputadoAPI(
                id=d["id"],
                nome=d.get("nome", ""),
                siglaPartido=d.get("siglaPartido"),
                siglaUf=d.get("siglaUf"),
                urlFoto=d.get("urlFoto"),
                email=d.get("email"),
            )
            for d in dados
        ]

    def obter_deputado(self, deputado_id: int) -> dict:
        """Detalhes de um deputado específico."""
        return self._get(f"/deputados/{deputado_id}")

    # ── Votações ──

    def listar_votacoes(self, ano: int) -> list[VotacaoAPI]:
        """Lista todas as votações de um ano."""
        dados = self._get_paginated("/votacoes", {"ano": ano, "ordem": "DESC", "ordenarPor": "dataHoraRegistro"})
        return [
            VotacaoAPI(
                id=v.get("id", ""),
                data=v.get("dataHoraRegistro") or v.get("data"),
                descricao=v.get("descricao", ""),
                aprovacao=v.get("aprovacao"),
            )
            for v in dados
        ]

    def obter_votos(self, votacao_id: str) -> list[VotoAPI]:
        """Votos individuais de uma votação."""
        dados = self._get(f"/votacoes/{votacao_id}/votos")
        if not isinstance(dados, list):
            return []
        return [
            VotoAPI(
                deputado_id=v.get("deputado_", {}).get("id", 0),
                deputado_nome=v.get("deputado_", {}).get("nome", ""),
                deputado_partido=v.get("deputado_", {}).get("siglaPartido"),
                deputado_uf=v.get("deputado_", {}).get("siglaUf"),
                voto=v.get("tipoVoto", ""),
            )
            for v in dados
        ]

    def obter_votacao_detalhes(self, votacao_id: str) -> dict:
        """Detalhes de uma votação, incluindo proposição associada."""
        return self._get(f"/votacoes/{votacao_id}")

    def obter_votacao_orientacoes(self, votacao_id: str) -> list[dict]:
        """Orientações dos partidos em uma votação.

        Retorna lista de {siglaPartido, orientacao} para montar
        o mapa partido → orientacao_partido nos votos individuais.
        """
        dados = self._get(f"/votacoes/{votacao_id}/orientacoes")
        if not isinstance(dados, list):
            return []
        return dados

    # ── Proposições ──

    def listar_proposicoes(self, ano: int, tipo: Optional[str] = None) -> list[ProposicaoAPI]:
        """Lista proposições por ano e tipo opcional."""
        params: dict[str, Any] = {"ano": ano, "ordem": "DESC", "ordenarPor": "id"}
        if tipo:
            params["siglaTipo"] = tipo

        dados = self._get_paginated("/proposicoes", params)
        return [
            ProposicaoAPI(
                id=p.get("id", 0),
                siglaTipo=p.get("siglaTipo"),
                numero=p.get("numero"),
                ano=p.get("ano"),
                ementa=p.get("ementa"),
            )
            for p in dados
        ]

    def obter_proposicao(self, proposicao_id: int) -> dict:
        """Detalhes de uma proposição."""
        return self._get(f"/proposicoes/{proposicao_id}")

    # ── Frentes ──

    def listar_frentes(self, legislatura: Optional[int] = None) -> list[dict]:
        """Lista frentes parlamentares."""
        params = {}
        if legislatura:
            params["idLegislatura"] = legislatura
        return self._get_paginated("/frentes", params)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

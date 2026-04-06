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
        """Lista todas as votações de um ano.

        A API exige janelas de no máximo 3 meses; iteramos trimestre a trimestre.
        """
        from datetime import date

        trimestres = [
            (f"{ano}-01-01", f"{ano}-03-31"),
            (f"{ano}-04-01", f"{ano}-06-30"),
            (f"{ano}-07-01", f"{ano}-09-30"),
            (f"{ano}-10-01", f"{ano}-12-31"),
        ]

        # Para o ano corrente, não pedir datas futuras
        hoje = date.today().isoformat()

        todos: list[dict] = []
        for inicio, fim in trimestres:
            if inicio > hoje:
                break
            fim_efetivo = min(fim, hoje)
            dados = self._get_paginated(
                "/votacoes",
                {
                    "dataInicio": inicio,
                    "dataFim": fim_efetivo,
                    "ordem": "DESC",
                    "ordenarPor": "dataHoraRegistro",
                },
            )
            todos.extend(dados)
            time.sleep(0.3)

        return [
            VotacaoAPI(
                id=v.get("id", ""),
                data=v.get("dataHoraRegistro") or v.get("data"),
                descricao=v.get("descricao", ""),
                aprovacao=v.get("aprovacao"),
            )
            for v in todos
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

    def listar_votacoes_proposicao(self, proposicao_id: int) -> list[VotacaoAPI]:
        """Lista todas as votações de uma proposição específica.

        Usa o endpoint GET /proposicoes/{id}/votacoes da Câmara.
        Retorna lista de VotacaoAPI (mesmo dataclass de listar_votacoes).

        Args:
            proposicao_id: ID numérico da proposição na API da Câmara.
        """
        dados = self._get(f"/proposicoes/{proposicao_id}/votacoes")
        if not isinstance(dados, list):
            return []

        results = [
            VotacaoAPI(
                id=v.get("id", ""),
                data=v.get("dataHoraRegistro") or v.get("data"),
                descricao=v.get("descricao", ""),
                aprovacao=v.get("aprovacao"),
            )
            for v in dados
        ]
        time.sleep(0.3)  # respeitar rate limit (R4: 300ms entre requests)
        return results

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

    def pesquisar_proposicoes(
        self,
        keywords: list[str],
        ano_inicio: int = 2020,
        ano_fim: Optional[int] = None,
        tipos: Optional[list[str]] = None,
        max_pages_per_quarter: int = 5,
    ) -> list[ProposicaoAPI]:
        """Pesquisa proposições por palavras-chave na API da Câmara.

        A API exige janelas de no máximo 3 meses; iteramos trimestre a trimestre
        (mesmo padrão de listar_votacoes).

        Args:
            keywords: Lista de termos de busca (enviados como OR via vírgula).
            ano_inicio: Ano inicial da janela de busca.
            ano_fim: Ano final (default: ano corrente).
            tipos: Tipos de proposição (ex: ["PL", "PEC", "PLP"]).
            max_pages_per_quarter: Máximo de páginas por trimestre.
        """
        from datetime import date

        if ano_fim is None:
            ano_fim = date.today().year

        hoje = date.today().isoformat()
        todos: list[dict] = []
        seen_ids: set[int] = set()

        for ano in range(ano_inicio, ano_fim + 1):
            trimestres = [
                (f"{ano}-01-01", f"{ano}-03-31"),
                (f"{ano}-04-01", f"{ano}-06-30"),
                (f"{ano}-07-01", f"{ano}-09-30"),
                (f"{ano}-10-01", f"{ano}-12-31"),
            ]
            for inicio, fim in trimestres:
                if inicio > hoje:
                    break
                fim_efetivo = min(fim, hoje)

                params: dict[str, Any] = {
                    "dataApresentacaoInicio": inicio,
                    "dataApresentacaoFim": fim_efetivo,
                    "keywords": ",".join(keywords),
                    "ordem": "DESC",
                    "ordenarPor": "id",
                }
                if tipos:
                    params["siglaTipo"] = ",".join(tipos)

                dados = self._get_paginated(
                    "/proposicoes", params, max_pages=max_pages_per_quarter,
                )
                for p in dados:
                    pid = p.get("id", 0)
                    if pid not in seen_ids:
                        seen_ids.add(pid)
                        todos.append(p)

                time.sleep(0.3)

        return [
            ProposicaoAPI(
                id=p.get("id", 0),
                siglaTipo=p.get("siglaTipo"),
                numero=p.get("numero"),
                ano=p.get("ano"),
                ementa=p.get("ementa"),
            )
            for p in todos
        ]

    def obter_proposicao(self, proposicao_id: int) -> dict:
        """Detalhes de uma proposição."""
        return self._get(f"/proposicoes/{proposicao_id}")

    # ── Proposição: sub-resources (Feature 012) ──

    def listar_autores_proposicao(self, proposicao_id: int) -> list[dict]:
        """Lista autores de uma proposição.

        GET /proposicoes/{id}/autores
        Returns list of dicts with uri, nome, tipo, ordemAssinatura, proponente.
        """
        dados = self._get(f"/proposicoes/{proposicao_id}/autores")
        if not isinstance(dados, list):
            return []
        time.sleep(0.3)
        return dados

    def listar_temas_proposicao(self, proposicao_id: int) -> list[dict]:
        """Lista temas oficiais de uma proposição.

        GET /proposicoes/{id}/temas
        Returns list of dicts with codTema, tema.
        """
        dados = self._get(f"/proposicoes/{proposicao_id}/temas")
        if not isinstance(dados, list):
            return []
        time.sleep(0.3)
        return dados

    def listar_relacionadas_proposicao(
        self, proposicao_id: int, max_pages: int = 10
    ) -> list[dict]:
        """Lista proposições relacionadas (emendas, pareceres, substitutivos, etc.).

        GET /proposicoes/{id}/relacionadas (paginated)
        Fetches up to max_pages (cap at ~200 items per Decision 4).
        """
        return self._get_paginated(
            f"/proposicoes/{proposicao_id}/relacionadas",
            max_pages=max_pages,
        )

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

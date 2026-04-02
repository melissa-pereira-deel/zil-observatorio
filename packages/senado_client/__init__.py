"""Client tipado para a API de Dados Abertos do Senado Federal.

Documentação: https://legis.senado.leg.br/dadosabertos/docs/
Endpoint base: https://legis.senado.leg.br/dadosabertos

O Senado Federal expõe dados em JSON via header Accept: application/json.
A estrutura de retorno varia por endpoint — cada método normaliza o
aninhamento específico da API.
"""

import time
import logging
from typing import Optional, Any
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://legis.senado.leg.br/dadosabertos"
HEADERS = {"Accept": "application/json"}
MAX_RETRIES = 3
RETRY_DELAY = 2.0


@dataclass
class SenadorAPI:
    id: int
    nome: str
    siglaPartido: Optional[str] = None
    siglaUf: Optional[str] = None
    urlFoto: Optional[str] = None
    email: Optional[str] = None
    nomeCivil: Optional[str] = None


@dataclass
class VotacaoSenAPI:
    id: str
    descricao: Optional[str] = None
    data: Optional[str] = None
    resultado: Optional[str] = None
    votos_sim: Optional[int] = None
    votos_nao: Optional[int] = None
    materia_id: Optional[str] = None


@dataclass
class VotoSenAPI:
    senador_id: int
    senador_nome: str
    senador_partido: Optional[str]
    senador_uf: Optional[str]
    voto: str  # "Sim", "Não", "Abstenção", "Ausente", etc.


@dataclass
class MateriaSenAPI:
    id: int
    sigla: Optional[str] = None
    numero: Optional[int] = None
    ano: Optional[int] = None
    ementa: Optional[str] = None
    situacao: Optional[str] = None
    data_apresentacao: Optional[str] = None
    votacoes: list = field(default_factory=list)


class SenadoClient:
    """Client para a API de Dados Abertos do Senado Federal."""

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
                return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503, 504):
                    wait = RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"HTTP {e.response.status_code} em {path}, "
                        f"aguardando {wait}s (tentativa {attempt + 1}/{MAX_RETRIES})..."
                    )
                    time.sleep(wait)
                    continue
                raise
            except httpx.RequestError as e:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Request error (tentativa {attempt + 1}): {e}, aguardando {wait}s..."
                    )
                    time.sleep(wait)
                    continue
                raise
        return {}

    # ── Senadores ──

    def listar_senadores(self) -> list[SenadorAPI]:
        """Lista todos os senadores em exercício."""
        data = self._get("/senador/lista/atual.json")
        parlamentares = (
            data
            .get("ListaParlamentarEmExercicio", {})
            .get("Parlamentares", {})
            .get("Parlamentar", [])
        )
        if isinstance(parlamentares, dict):
            parlamentares = [parlamentares]

        senadores = []
        for p in parlamentares:
            ident = p.get("IdentificacaoParlamentar", {})
            sid = ident.get("CodigoParlamentar")
            if not sid:
                continue
            senadores.append(SenadorAPI(
                id=int(sid),
                nome=ident.get("NomeParlamentar", ""),
                nomeCivil=ident.get("NomeCompletoParlamentar"),
                siglaPartido=ident.get("SiglaPartidoParlamentar"),
                siglaUf=ident.get("UfParlamentar"),
                urlFoto=ident.get("UrlFotoParlamentar"),
                email=ident.get("EmailParlamentar"),
            ))
        return senadores

    def obter_senador(self, senador_id: int) -> dict:
        """Detalhes de um senador específico."""
        data = self._get(f"/senador/{senador_id}.json")
        return data.get("DetalheParlamentar", {}).get("Parlamentar", {})

    # ── Votações ──

    def listar_votacoes_materia(self, materia_id: int) -> list[VotacaoSenAPI]:
        """Votações de uma matéria específica."""
        data = self._get(f"/materia/votacoes/{materia_id}.json")
        votacoes_raw = (
            data
            .get("VotacaoMateria", {})
            .get("Materia", {})
            .get("Votacoes", {})
            .get("Votacao", [])
        )
        if isinstance(votacoes_raw, dict):
            votacoes_raw = [votacoes_raw]

        result = []
        for v in votacoes_raw:
            seq = v.get("CodigoSessaoVotacao") or v.get("SequencialVotacao", "")
            descricao_vot = v.get("DescricaoVotacao") or v.get("Descricao", "")
            data_vot = v.get("DataSessao")
            resultado = v.get("DescricaoResultado")
            result.append(VotacaoSenAPI(
                id=str(seq),
                descricao=descricao_vot,
                data=data_vot,
                resultado=resultado,
                materia_id=str(materia_id),
            ))
        return result

    def obter_votos_votacao(self, votacao_id: str) -> list[VotoSenAPI]:
        """Votos individuais de uma votação pelo ID da sessão."""
        data = self._get(f"/votacao/senador/{votacao_id}.json")
        votos_raw = (
            data
            .get("VotacaoSenador", {})
            .get("Votacao", {})
            .get("Votos", {})
            .get("VotoParlamentar", [])
        )
        if isinstance(votos_raw, dict):
            votos_raw = [votos_raw]

        result = []
        for v in votos_raw:
            ident = v.get("IdentificacaoParlamentar", {})
            sid = ident.get("CodigoParlamentar")
            if not sid:
                continue
            result.append(VotoSenAPI(
                senador_id=int(sid),
                senador_nome=ident.get("NomeParlamentar", ""),
                senador_partido=ident.get("SiglaPartidoParlamentar"),
                senador_uf=ident.get("UfParlamentar"),
                voto=v.get("SiglaVoto", ""),
            ))
        return result

    def listar_materias_ano(self, ano: int, sigla: Optional[str] = None) -> list[MateriaSenAPI]:
        """Lista matérias (proposições) por ano."""
        params: dict[str, Any] = {"ano": ano}
        if sigla:
            params["sigla"] = sigla
        data = self._get("/materia/pesquisa/lista.json", params)
        materias_raw = (
            data
            .get("PesquisaBasicaMateria", {})
            .get("Materias", {})
            .get("Materia", [])
        )
        if isinstance(materias_raw, dict):
            materias_raw = [materias_raw]

        result = []
        for m in materias_raw:
            ident = m.get("IdentificacaoMateria", {})
            mid = ident.get("CodigoMateria")
            if not mid:
                continue
            result.append(MateriaSenAPI(
                id=int(mid),
                sigla=ident.get("SiglaSubtipoMateria") or ident.get("SiglaTipoMateria"),
                numero=int(ident.get("NumeroMateria", 0)) or None,
                ano=int(ident.get("AnoMateria", ano)),
                ementa=m.get("EmentaMateria") or m.get("Ementa"),
                situacao=m.get("SituacaoAtual"),
                data_apresentacao=m.get("DataApresentacao"),
            ))
        return result

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

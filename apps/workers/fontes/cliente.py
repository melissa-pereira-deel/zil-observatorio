"""A fronteira única com a rede para dados externos.

Mesmo princípio de `agentes/fronteira.py` para a API da Anthropic: uma função
só fala com o mundo, e os testes substituem o transporte — nunca a função.

Três garantias moram aqui, em código:

1. **Allowlist na camada de rede.** `TransportePermitido` recusa qualquer
   requisição cujo host não esteja no catálogo, antes de ela sair. Um
   adaptador com bug, um redirect para outro domínio, um parâmetro
   malicioso: nada passa. Não depende de ninguém lembrar de conferir.
2. **Nunca lança.** Rede, HTTP, JSON malformado, HTML onde se esperava JSON
   (o BCB devolve uma página de erro com status 200 — observado em
   2026-10-21): tudo volta como `Observacoes(erro=...)`, e o pipeline
   declara a lacuna em vez de quebrar.
3. **Consulta por intervalo explícito.** Não existe "últimos N": a meta Selic
   é publicada com datas futuras até o próximo Copom, e "último valor" não é
   "valor de hoje" (observado em 2026-10-21). Quem chama diz de quando a
   quando — é o que permite ancorar o contexto na data da proposição.

O cache em disco (`data/fontes/cache/`, fora do git) é o que torna duas
execuções sobre a mesma proposição reproduzíveis: o contexto que uma
explicação viu não muda porque a série foi revisada depois.
"""

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional, Union

import httpx

from .catalogo import Catalogo, Fonte, Serie, carregar_catalogo

CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "fontes" / "cache"
USER_AGENT = "Mozilla/5.0 (compatible; ZIL-Observatorio/1.0; +https://zilobservatorio.com.br)"
TIMEOUT = 30.0
TTL_HORAS = 24.0


class HostNaoPermitido(Exception):
    """Levantada pelo transporte, capturada por `consultar_serie`. Nunca sobe
    além dela — mas o nome fica, para o log dizer o que foi recusado."""


class TransportePermitido(httpx.BaseTransport):
    """Envelopa qualquer transporte e recusa host fora da allowlist.

    É aqui, e não em instrução nem em revisão de código, que a allowlist é
    aplicada. O transporte interno é o real em produção e um `MockTransport`
    nos testes — e os testes provam que a recusa acontece antes de o interno
    ser chamado.
    """

    def __init__(self, hosts: frozenset[str], interno: httpx.BaseTransport) -> None:
        self.hosts = hosts
        self.interno = interno
        self.recusados: list[str] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host not in self.hosts:
            self.recusados.append(host)
            raise HostNaoPermitido(f"{host!r} não está no catálogo de fontes")
        return self.interno.handle_request(request)

    def close(self) -> None:
        self.interno.close()


@dataclass(frozen=True)
class Observacao:
    data: str  # ISO: AAAA-MM-DD; para série anual, AAAA-01-01
    valor: float


@dataclass
class Observacoes:
    """O resultado de uma consulta, com a proveniência que o leitor precisa."""

    ref: str
    inicio: str
    fim: str
    url: str = ""
    data_consulta: str = ""
    observacoes: list[Observacao] = field(default_factory=list)
    erro: Optional[str] = None
    do_cache: bool = False

    @property
    def ok(self) -> bool:
        return self.erro is None

    @property
    def ultima(self) -> Optional[Observacao]:
        """A observação mais recente dentro do intervalo pedido."""
        return max(self.observacoes, key=lambda o: o.data) if self.observacoes else None


# ── adaptadores: (fonte, série, início, fim, client) → (url, observações) ──

def _iso_de_br(d: str) -> str:
    dia, mes, ano = d.split("/")
    return f"{ano}-{mes}-{dia}"


def _br(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def _json(resposta: httpx.Response):
    """O BCB responde HTML com status 200 para série inexistente ou parâmetro
    ruim. `r.json()` lançaria JSONDecodeError com uma mensagem inútil; aqui o
    erro diz o que veio."""
    tipo = resposta.headers.get("content-type", "")
    corpo = resposta.text.lstrip()
    if corpo.startswith("<") or ("json" not in tipo and not corpo.startswith(("[", "{"))):
        raise ValueError(f"resposta não é JSON (content-type {tipo or 'ausente'}): {corpo[:60]!r}")
    return json.loads(corpo)


def _bcb_sgs(fonte: Fonte, serie: Serie, inicio: date, fim: date, client: httpx.Client):
    url = f"https://{fonte.host}/dados/serie/bcdata.sgs.{serie.parametro('id')}/dados"
    r = client.get(url, params={"formato": "json", "dataInicial": _br(inicio), "dataFinal": _br(fim)})
    r.raise_for_status()
    dados = _json(r)
    if not isinstance(dados, list):
        raise ValueError("BCB: esperada lista de {data, valor}")
    return str(r.url), [Observacao(_iso_de_br(d["data"]), float(d["valor"])) for d in dados]


def _ibge_agregados(fonte: Fonte, serie: Serie, inicio: date, fim: date, client: httpx.Client):
    # A API v3 não aceita "-1" (último) de forma confiável, e um intervalo
    # "2022-2024" devolveu só 2024 (observado em 2026-10-21). Anos explícitos
    # separados por "|" funcionam; ano sem estimativa volta vazio, não erro.
    anos = "|".join(str(a) for a in range(inicio.year, fim.year + 1))
    url = (
        f"https://{fonte.host}/api/v3/agregados/{serie.parametro('agregado')}"
        f"/periodos/{anos}/variaveis/{serie.parametro('variavel')}"
    )
    r = client.get(url, params={"localidades": serie.parametro("localidade", "N1")})
    r.raise_for_status()
    dados = _json(r)
    if not isinstance(dados, list):
        raise ValueError("IBGE: esperada lista de variáveis")
    obs: list[Observacao] = []
    for variavel in dados:
        for resultado in variavel.get("resultados") or []:
            for s in resultado.get("series") or []:
                for ano, valor in (s.get("serie") or {}).items():
                    try:
                        obs.append(Observacao(f"{int(ano)}-01-01", float(valor)))
                    except (TypeError, ValueError):
                        continue  # "..." e "-" são "não disponível" no IBGE
    return str(r.url), obs


def _ipea_odata(fonte: Fonte, serie: Serie, inicio: date, fim: date, client: httpx.Client):
    # O servidor ignora `$filter` (observado em 2026-10-21): vem a série
    # inteira, e o recorte é feito aqui. Fonte secundária — serve para
    # conferir transcrição, não como evidência independente.
    url = f"https://{fonte.host}/api/odata4/ValoresSerie(SERCODIGO='{serie.parametro('codigo')}')"
    r = client.get(url)
    r.raise_for_status()
    dados = _json(r)
    lo, hi = inicio.isoformat(), fim.isoformat()
    obs = []
    for v in dados.get("value") or []:
        d = str(v.get("VALDATA") or "")[:10]
        if lo <= d <= hi and v.get("VALVALOR") is not None:
            obs.append(Observacao(d, float(v["VALVALOR"])))
    return str(r.url), obs


ADAPTADORES: dict[str, Callable] = {
    "bcb_sgs": _bcb_sgs,
    "ibge_agregados": _ibge_agregados,
    "ipea_odata": _ipea_odata,
}


# ── cache ─────────────────────────────────────────────────────────────────────

def _chave_cache(ref: str, inicio: date, fim: date) -> str:
    return hashlib.sha256(f"{ref}|{inicio.isoformat()}|{fim.isoformat()}".encode()).hexdigest()[:24]


def _ler_cache(cache_dir: Path, chave: str, agora: datetime, ttl_horas: float) -> Optional[dict]:
    caminho = cache_dir / f"{chave}.json"
    if not caminho.exists():
        return None
    try:
        bruto = json.loads(caminho.read_text(encoding="utf-8"))
        consultado = datetime.fromisoformat(bruto["data_consulta"])
    except (ValueError, KeyError, TypeError):
        return None
    if agora - consultado > timedelta(hours=ttl_horas):
        return None
    return bruto


def _gravar_cache(cache_dir: Path, chave: str, obs: "Observacoes") -> None:
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / f"{chave}.json").write_text(
            json.dumps(asdict(obs), ensure_ascii=False, indent=1), encoding="utf-8"
        )
    except OSError:
        pass  # cache é conveniência; não pode derrubar a consulta


# ── a fronteira ───────────────────────────────────────────────────────────────

def consultar_serie(
    ref: Union[str, Serie],
    inicio: date,
    fim: date,
    *,
    catalogo: Optional[Catalogo] = None,
    transport: Optional[httpx.BaseTransport] = None,
    cache_dir: Optional[Path] = CACHE_DIR,
    ttl_horas: float = TTL_HORAS,
    agora: Optional[datetime] = None,
    ambiente: Mapping[str, str] = os.environ,
) -> Observacoes:
    """Consulta uma série do catálogo no intervalo. Nunca lança.

    `transport` é o que os testes substituem (um `httpx.MockTransport`); a
    allowlist envolve qualquer transporte, inclusive o falso, então os testes
    provam que a recusa acontece. `cache_dir=None` desliga o cache.
    """
    catalogo = catalogo or carregar_catalogo()
    agora = agora or datetime.now(timezone.utc)
    serie = catalogo.serie(ref) if isinstance(ref, str) else ref
    fonte = catalogo.fontes[serie.fonte]
    res = Observacoes(ref=serie.ref, inicio=inicio.isoformat(), fim=fim.isoformat())

    if inicio > fim:
        res.erro = f"intervalo invertido: {inicio} > {fim}"
        return res
    if not fonte.habilitada:
        res.erro = f"fonte {fonte.id} catalogada mas não habilitada"
        return res
    if fonte.chave and not ambiente.get(fonte.chave):
        # Só o nome da variável. O valor nunca aparece em erro nem em log.
        res.erro = f"fonte {fonte.id} exige a variável {fonte.chave}, que não está configurada"
        return res

    chave = _chave_cache(serie.ref, inicio, fim)
    if cache_dir is not None:
        guardado = _ler_cache(cache_dir, chave, agora, ttl_horas)
        if guardado:
            res.url = guardado.get("url", "")
            res.data_consulta = guardado["data_consulta"]
            res.observacoes = [Observacao(o["data"], float(o["valor"])) for o in guardado.get("observacoes", [])]
            res.do_cache = True
            return res

    adaptador = ADAPTADORES[fonte.adaptador]  # a carga já garantiu que existe
    permitido = TransportePermitido(catalogo.hosts_permitidos, transport or httpx.HTTPTransport())
    try:
        with httpx.Client(transport=permitido, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}, follow_redirects=True) as client:
            url, obs = adaptador(fonte, serie, inicio, fim, client)
    except HostNaoPermitido as e:
        res.erro = f"host recusado pela allowlist: {e}"
        return res
    except httpx.HTTPStatusError as e:
        res.erro = f"HTTP {e.response.status_code} em {fonte.host}"
        return res
    except httpx.HTTPError as e:
        res.erro = f"rede: {type(e).__name__} em {fonte.host}"
        return res
    except (ValueError, KeyError, IndexError, TypeError) as e:
        res.erro = f"resposta inesperada de {fonte.host}: {type(e).__name__}: {str(e)[:120]}"
        return res

    res.url = url
    res.data_consulta = agora.isoformat()
    res.observacoes = sorted(obs, key=lambda o: o.data)
    if cache_dir is not None:
        _gravar_cache(cache_dir, chave, res)
    return res

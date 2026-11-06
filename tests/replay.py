"""Serve respostas reais gravadas das APIs da Câmara e do Senado, sem rede (TRM-002).

Os pacotes moram em `tests/fixtures/tramitacao/` e são escritos por
`scripts/gravar_respostas.py`. O pacote é a verdade do dia da gravação (`gravado_em`):
regravar é decisão explícita, com o diff revisado em PR próprio.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import httpx

from packages.camara_client import CamaraClient
from packages.senado_client import SenadoClient

RAIZ_FIXTURES = Path(__file__).parent / "fixtures" / "tramitacao"
RAIZ_GRAVACOES = RAIZ_FIXTURES / "gravacoes"

# Pastas irmãs de `gravacoes/` que `carregar` aceita como prefixo do slug.
PASTAS_IRMAS = ("candidatos", "sinteticos")

HOSTS = {
    "dadosabertos.camara.leg.br": ("camara", "/api/v2"),
    "legis.senado.leg.br": ("senado", "/dadosabertos"),
}


# O que o gravador põe no lugar de um campo que não pode ser versionado.
VALOR_REMOVIDO = "[removido pelo gravador]"

_CHAVE_DE_CPF = re.compile(r"cpf", re.IGNORECASE)
_SEPARADOR = r"(?:\s*[.\-/]\s*|\s+)"
# As bordas recusam pedaço de número maior, como o fim de 1.234.567.890-12.
_CPF_COM_SEPARADOR = re.compile(
    rf"(?<!\d)(?<!\d[.,/\-])\d{{3}}{_SEPARADOR}?\d{{3}}{_SEPARADOR}?\d{{3}}{_SEPARADOR}?\d{{2}}(?!\d)(?![.,/\-]\d)"
)
# Letra colada na borda é trecho de UUID ou de identificador, não documento.
_ONZE_DIGITOS = re.compile(r"(?<![0-9A-Za-z])\d{11}(?![0-9A-Za-z])")
_CPF_ROTULADO = re.compile(r"cpf\W{0,15}\d{9,11}(?!\d)", re.IGNORECASE)


class RequisicaoNaoGravada(AssertionError):
    """AssertionError de propósito: o cliente só captura httpx.RequestError/HTTPStatusError."""


class PacoteInconsistente(ValueError):
    """As partes de um pacote não fecham, ou dois pacotes discordam sobre a mesma requisição."""


def _digitos_verificadores_conferem(digitos: str) -> bool:
    # Um só dígito repetido passa na conta, mas a Receita não emite.
    if len(set(digitos)) == 1:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d) * peso for d, peso in zip(digitos[:tamanho], range(tamanho + 1, 1, -1)))
        if (soma * 10) % 11 % 10 != int(digitos[tamanho]):
            return False
    return True


def _tem_forma_de_cpf(texto: str) -> bool:
    if _CPF_ROTULADO.search(texto):
        return True
    # Com separador, a forma já basta. Só os 11 dígitos corridos precisam da conta, porque um
    # id numérico pode ter esse tamanho, e só 1 em cada 100 passaria nela por acaso.
    if any(not m.group().isdigit() for m in _CPF_COM_SEPARADOR.finditer(texto)):
        return True
    return any(_digitos_verificadores_conferem(m.group()) for m in _ONZE_DIGITOS.finditer(texto))


def achados_de_cpf(corpo: Any, caminho: str = "") -> list[str]:
    """Caminhos do corpo com chave de CPF ainda preenchida ou valor com forma de CPF.

    Devolve só o caminho, nunca o valor: o achado vai para o terminal e para o log da CI.
    """
    achados: list[str] = []
    if isinstance(corpo, dict):
        for chave, valor in corpo.items():
            forma_na_chave = _tem_forma_de_cpf(str(chave))
            nome = "<chave com forma de CPF>" if forma_na_chave else str(chave)
            filho = f"{caminho}.{nome}" if caminho else nome
            if forma_na_chave or (_CHAVE_DE_CPF.search(nome) and valor not in (None, "", VALOR_REMOVIDO)):
                achados.append(filho)
            achados.extend(achados_de_cpf(valor, filho))
    elif isinstance(corpo, list):
        for indice, valor in enumerate(corpo):
            achados.extend(achados_de_cpf(valor, f"{caminho}[{indice}]"))
    elif isinstance(corpo, str):
        if _tem_forma_de_cpf(corpo):
            achados.append(caminho or "<corpo>")
    elif isinstance(corpo, int) and not isinstance(corpo, bool):
        if _tem_forma_de_cpf(str(corpo)):
            achados.append(caminho or "<corpo>")
    return achados


def hash_corpo(corpo: Any) -> str:
    """Hash do corpo em forma canônica: confere o pacote sem depender da formatação do arquivo.

    O prefixo `sha256:` não é enfeite. Sem ele, o valor é hexadecimal puro entre aspas, e o
    detect-secrets (`HexHighEntropyString`) recusa o commit de todo pacote.
    """
    canonico = json.dumps(corpo, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def descrever_requisicao(request: httpx.Request) -> tuple[str, str, dict[str, str]]:
    """(host, caminho sem o prefixo da base, params) de uma requisição."""
    host, prefixo = HOSTS.get(request.url.host, (request.url.host, ""))
    caminho = request.url.path.removeprefix(prefixo) or "/"
    return host, caminho, dict(request.url.params.multi_items())


def _chave(host: str, caminho: str, params: dict[str, Any]) -> tuple:
    return host, caminho, tuple(sorted((k, str(v)) for k, v in params.items()))


def _assinatura(fila: list[dict]) -> list[tuple]:
    return [(envelope["status"], hash_corpo(envelope["corpo"])) for envelope in fila]


def _resposta(envelope: dict) -> httpx.Response:
    cabecalhos = {k: v for k, v in envelope["cabecalhos"].items() if v is not None}
    corpo = envelope["corpo"]
    if isinstance(corpo, str) and "json" not in cabecalhos.get("content-type", ""):
        conteudo = corpo.encode("utf-8")
    else:
        conteudo = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
    return httpx.Response(envelope["status"], headers=cabecalhos, content=conteudo)


class Gravacoes:
    """Acumula pacotes e os serve por `httpx.MockTransport`; nunca acessa a rede."""

    def __init__(self, raiz: Path = RAIZ_GRAVACOES) -> None:
        self.raiz = Path(raiz)
        self.nao_gravadas: list[str] = []
        self._feitas: list[tuple[str, str, dict]] = []
        self._filas: dict[tuple, list[dict]] = {}
        self._origens: dict[tuple, str] = {}
        self._servidas: dict[tuple, int] = {}
        self._transporte = httpx.MockTransport(self._responder)

    def carregar(self, *slugs: str) -> "Gravacoes":
        """Acumula pacotes. Aceita também `candidatos/<id>` e `sinteticos/<nome>`.

        A sequência de uma requisição só vale dentro de um pacote. Dois pacotes que trazem a
        mesma requisição têm de concordar: senão a segunda chamada traria outro corpo, sem erro,
        e isso pareceria mudança na fonte. É o que aconteceria depois de regravar só um deles.
        """
        for slug in slugs:
            filas: dict[tuple, list[dict]] = {}
            for envelope in self._respostas_do_pacote(slug):
                chave = _chave(envelope["host"], envelope["caminho"], envelope["params"])
                filas.setdefault(chave, []).append(envelope)
            for chave, fila in filas.items():
                if chave not in self._filas:
                    self._filas[chave] = fila
                    self._origens[chave] = slug
                elif _assinatura(self._filas[chave]) != _assinatura(fila):
                    host, caminho, params = chave
                    raise PacoteInconsistente(
                        f"{self._origens[chave]} e {slug} trazem respostas diferentes para "
                        f"GET {host} {caminho} {dict(params)}. Regrave os dois, ou não os carregue juntos."
                    )
        return self

    def transporte(self) -> httpx.MockTransport:
        return self._transporte

    def cliente_camara(self, **kwargs) -> CamaraClient:
        return CamaraClient(transport=self.transporte(), **kwargs)

    def cliente_senado(self) -> SenadoClient:
        return SenadoClient(transport=self.transporte())

    @property
    def requisicoes_feitas(self) -> list[tuple[str, str, dict]]:
        """(host, caminho, params) de cada requisição, para testar orçamento e cache."""
        return list(self._feitas)

    def corpo(self, slug: str, caminho: str, params: dict | None = None) -> Any:
        """Leitura direta de um corpo gravado, para testes puros: não conta como requisição."""
        procurados = {k: str(v) for k, v in (params or {}).items()}
        for envelope in self._respostas_do_pacote(slug):
            if envelope["caminho"] == caminho and envelope["params"] == procurados:
                return envelope["corpo"]
        raise KeyError(f"{slug}: {caminho} {procurados} não está gravado")

    def _responder(self, request: httpx.Request) -> httpx.Response:
        host, caminho, params = descrever_requisicao(request)
        self._feitas.append((host, caminho, params))
        chave = _chave(host, caminho, params)
        fila = self._filas.get(chave)
        if not fila:
            descricao = f"{request.method} {host} {caminho} {dict(sorted(params.items()))}"
            self.nao_gravadas.append(descricao)
            raise RequisicaoNaoGravada(descricao)
        posicao = self._servidas.get(chave, 0)
        self._servidas[chave] = posicao + 1
        # O último envelope se repete: é o que permite simular 429 → 200 → 200…
        return _resposta(fila[min(posicao, len(fila) - 1)])

    def _arquivo(self, slug: str) -> Path:
        if slug.split("/", 1)[0] in PASTAS_IRMAS:
            return self.raiz.parent / f"{slug}.json"
        return self.raiz / f"{slug}.json"

    def _respostas_do_pacote(self, slug: str) -> list[dict]:
        arquivo = self._arquivo(slug)
        if not arquivo.exists():
            raise FileNotFoundError(f"Pacote não gravado: {arquivo}")
        cabeca = json.loads(arquivo.read_text("utf-8"))
        partes = cabeca.get("partes", 1)
        esperadas = {arquivo.with_name(f"{arquivo.stem}.parte-{n:02d}.json") for n in range(2, partes + 1)}
        sobrando = sorted(p.name for p in set(arquivo.parent.glob(f"{arquivo.stem}.parte-*.json")) - esperadas)
        if sobrando:
            raise PacoteInconsistente(f"{', '.join(sobrando)} não declarada em {arquivo.name} (partes: {partes})")

        respostas = list(cabeca["respostas"])
        for numero in range(2, partes + 1):
            parte = arquivo.with_name(f"{arquivo.stem}.parte-{numero:02d}.json")
            if not parte.exists():
                raise FileNotFoundError(f"Falta a parte {numero} de {slug}: {parte}")
            lida = json.loads(parte.read_text("utf-8"))
            esperado = (numero, partes, cabeca["caso"], cabeca["gravado_em"])
            if (lida.get("parte"), lida.get("partes"), lida.get("caso"), lida.get("gravado_em")) != esperado:
                raise PacoteInconsistente(f"{parte.name} não fecha com {arquivo.name}")
            respostas.extend(lida["respostas"])
        return respostas

"""Grava respostas reais das APIs da Câmara e do Senado como pacotes golden (TRM-002).

Lê `tests/fixtures/tramitacao/casos.yml` e executa a receita de cada caso pelo mesmo
cliente de produção, com um transporte que copia cada resposta 200 para o pacote.

Uso (da raiz do repositório):

    python scripts/gravar_respostas.py --caso pl-327-2021
    python scripts/gravar_respostas.py --todos
    python scripts/gravar_respostas.py --caso candidatos/2269745 --fonte-id 2269745

Regravar é decisão explícita: o pacote é a verdade do dia da gravação, e o diff vai a um
PR próprio. Nunca edite um pacote gravado à mão. Só esta ferramenta acessa a rede; os
testes leem os pacotes por `tests/replay.py`.
"""

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo

import httpx
import yaml

_repo_root = str(Path(__file__).parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from packages.camara_client import CamaraClient  # noqa: E402
from packages.senado_client import SenadoClient  # noqa: E402
from tests.replay import (  # noqa: E402
    RAIZ_FIXTURES,
    VALOR_REMOVIDO,
    achados_de_cpf,
    descrever_requisicao,
    hash_corpo,
)

FUSO = ZoneInfo("America/Sao_Paulo")

CABECALHOS_GUARDADOS = ("x-total-count", "link", "retry-after", "content-type")
# O corpo já sai decodificado do transporte; estes descreveriam os bytes originais.
CABECALHOS_DE_TRANSPORTE = ("content-encoding", "transfer-encoding", "content-length")

INTERVALO_SEGUNDOS = 0.5
TENTATIVAS = 5
RECUO_BASE_SEGUNDOS = 2.0
ESPERA_MAXIMA_SEGUNDOS = 300.0
STATUS_TRANSITORIOS = {429, 500, 502, 503, 504}

LIMITE_TOTAL = 8 * 1024 * 1024
# `check-added-large-files --maxkb=500` recusa o arquivo: o pacote maior vira partes.
LIMITE_ARQUIVO = 480 * 1024

MAX_NIVEIS_CADEIA = 10
JANELA_DIAS = 7
JANELA_TIPOS = "PL,PLP,PEC,MPV,PDL"
JANELA_MAX_PAGINAS = 50

# Nomes de campo que não vão para o pacote, em qualquer endpoint e em qualquer nível do corpo.
# `/deputados/{id}` traz CPF, data e local de nascimento. Nada aqui depende deles, e junto com o
# nome civil servem para confirmar identidade. Um repositório público não é lugar de republicá-los:
# a história do git não se apaga depois.
CAMPOS_REMOVIDOS = (
    re.compile(r"cpf", re.IGNORECASE),
    re.compile(r"^(dataNascimento|municipioNascimento|ufNascimento)$", re.IGNORECASE),
)

CABECALHO_CASOS = """\
# Casos golden da tramitação (TRM-002). `hoje` é escrito por scripts/gravar_respostas.py:
# é a data da gravação, o `hoje` da R9 nos testes. `esperado` é preenchido em TRM-025 e
# conferido pela maintainer. Lista e motivos: specs/013-tramitacao/backlog-dados.md.
"""


class GravacaoInterrompida(Exception):
    """A fonte não entregou 200 depois de esperar. Não herda de httpx.HTTPError de propósito:
    o cliente de produção engoliria a falha e devolveria `[]`, que viraria pacote vazio."""


class CasoInvalido(Exception):
    """O pedido não corresponde a um caso gravável."""


def segundos_retry_after(valor: Optional[str], agora_utc: Optional[float] = None) -> Optional[float]:
    """Segundos pedidos por um `Retry-After`, em segundos ou em data HTTP; None se ilegível."""
    if not valor:
        return None
    valor = valor.strip()
    if valor.isdigit():
        return float(valor)
    try:
        instante = parsedate_to_datetime(valor)
    except (TypeError, ValueError):
        return None
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=timezone.utc)
    referencia = time.time() if agora_utc is None else agora_utc
    return max(0.0, instante.timestamp() - referencia)


class TransporteGravador(httpx.BaseTransport):
    """Copia cada resposta 200 para `respostas` e é educado com a fonte.

    O ritmo mora aqui, e não no cliente, porque é o cliente de produção que está sendo
    exercitado, e ele ainda ignora `Retry-After`. A Câmara manda `retry-after: 30` em toda
    resposta 200: o cabeçalho só vale como pedido de espera em status transitório.
    """

    def __init__(
        self,
        base: httpx.BaseTransport,
        *,
        dormir: Optional[Callable[[float], None]] = None,
        agora: Callable[[], float] = time.monotonic,
        intervalo: float = INTERVALO_SEGUNDOS,
        tentativas: int = TENTATIVAS,
        espera_maxima: float = ESPERA_MAXIMA_SEGUNDOS,
    ) -> None:
        self.base = base
        self._dormir = dormir or (lambda segundos: time.sleep(segundos))
        self._agora = agora
        self._intervalo = intervalo
        self._tentativas = tentativas
        self._espera_maxima = espera_maxima
        self._ultima: Optional[float] = None
        self.respostas: list[dict] = []
        self.ausentes: list[dict] = []

    def iniciar_caso(self) -> None:
        self.respostas = []
        self.ausentes = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self._respeitar_intervalo()
        host, caminho, params = descrever_requisicao(request)
        for tentativa in range(1, self._tentativas + 1):
            resposta = self.base.handle_request(request)
            resposta.read()
            resposta.close()
            self._ultima = self._agora()
            if resposta.status_code not in STATUS_TRANSITORIOS:
                break
            espera = segundos_retry_after(resposta.headers.get("retry-after"))
            if espera is None:
                espera = RECUO_BASE_SEGUNDOS * 2 ** (tentativa - 1)
            if espera > self._espera_maxima:
                raise GravacaoInterrompida(
                    f"{host} {caminho}: HTTP {resposta.status_code} pede espera de "
                    f"{espera:.0f} s, acima do teto de {self._espera_maxima:.0f} s."
                )
            if tentativa == self._tentativas:
                raise GravacaoInterrompida(
                    f"{host} {caminho}: HTTP {resposta.status_code} depois de {tentativa} tentativas."
                )
            self._dormir(espera)

        if resposta.status_code == 200:
            self.respostas.append(self._envelope(request, resposta, host, caminho, params))
        else:
            self.ausentes.append(
                {"host": host, "caminho": caminho, "params": params, "status": resposta.status_code}
            )
        return httpx.Response(
            resposta.status_code,
            headers=[
                (k, v) for k, v in resposta.headers.items() if k.lower() not in CABECALHOS_DE_TRANSPORTE
            ],
            content=resposta.content,
            request=request,
        )

    def close(self) -> None:
        self.base.close()

    def _respeitar_intervalo(self) -> None:
        if self._ultima is None:
            return
        falta = self._intervalo - (self._agora() - self._ultima)
        if falta > 0:
            self._dormir(falta)

    @staticmethod
    def _envelope(request, resposta, host, caminho, params) -> dict:
        try:
            corpo: Any = resposta.json()
        except ValueError:
            corpo = resposta.text
        envelope = {
            "host": host,
            "metodo": request.method,
            "caminho": caminho,
            "params": params,
            "status": resposta.status_code,
            "cabecalhos": {nome: resposta.headers.get(nome) for nome in CABECALHOS_GUARDADOS},
        }
        removidos = _remover_campos(corpo)
        # O que não dá para tirar com segurança, como CPF em texto livre, impede a gravação.
        achados = achados_de_cpf(corpo)
        if achados:
            raise GravacaoInterrompida(
                f"{host} {caminho}: forma de CPF em {', '.join(achados)}. Nada foi gravado: "
                "confira a fonte antes de regravar."
            )
        envelope["corpo"] = corpo
        envelope["sha256_corpo"] = hash_corpo(corpo)
        if removidos:
            envelope["campos_removidos"] = removidos
        return envelope


def _remover_campos(corpo: Any, caminho: str = "") -> list[str]:
    """Troca, no próprio corpo, o valor dos campos de `CAMPOS_REMOVIDOS`; devolve os caminhos."""
    removidos: list[str] = []
    if isinstance(corpo, dict):
        for chave, valor in corpo.items():
            filho = f"{caminho}.{chave}" if caminho else str(chave)
            if valor not in (None, "") and any(p.search(str(chave)) for p in CAMPOS_REMOVIDOS):
                corpo[chave] = VALOR_REMOVIDO
                removidos.append(filho)
            else:
                removidos.extend(_remover_campos(valor, filho))
    elif isinstance(corpo, list):
        for indice, valor in enumerate(corpo):
            removidos.extend(_remover_campos(valor, f"{caminho}[{indice}]"))
    return removidos


def _id_da_uri(uri: Optional[str]) -> Optional[str]:
    return uri.rstrip("/").rsplit("/", 1)[-1] if uri else None


class Receitas:
    """As requisições de cada caso. Um pacote nunca pede a mesma coisa duas vezes."""

    def __init__(self, camara: CamaraClient, senado: SenadoClient, hoje: date) -> None:
        self.camara = camara
        self.senado = senado
        self.hoje = hoje
        self._orgaos: set[str] = set()
        self._deputados: set[str] = set()

    def proposicao_completa(self, fonte_id: Any) -> dict:
        detalhe = self.camara.obter_proposicao(int(fonte_id))
        tramitacoes = self.camara.obter_tramitacoes(int(fonte_id))
        self.camara.obter_autores(int(fonte_id))
        self.camara.obter_relacionadas(int(fonte_id))

        status = detalhe.get("statusProposicao") or {}
        # O órgão efetivo (A19) pode ser qualquer um das tramitações, não só o do status.
        for uri in [status.get("uriOrgao"), *(t.get("uriOrgao") for t in tramitacoes)]:
            orgao = _id_da_uri(uri)
            if orgao and orgao not in self._orgaos:
                self._orgaos.add(orgao)
                self._tolerar_ausencia(self.camara._get, f"/orgaos/{orgao}")

        relator = _id_da_uri(status.get("uriUltimoRelator"))
        if relator and relator not in self._deputados:
            self._deputados.add(relator)
            self._tolerar_ausencia(self.camara._get, f"/deputados/{relator}")
        return detalhe

    def proposicao_com_cadeia(self, fonte_id: Any) -> None:
        visitadas = {str(fonte_id)}
        detalhe = self.proposicao_completa(fonte_id)
        for _ in range(MAX_NIVEIS_CADEIA):
            principal = _id_da_uri(detalhe.get("uriPropPrincipal"))
            if not principal or principal in visitadas:
                return
            visitadas.add(principal)
            detalhe = self.proposicao_completa(principal)

    def janela(self) -> None:
        inicio = self.hoje - timedelta(days=JANELA_DIAS)
        self.camara._get_paginated(
            "/proposicoes",
            {
                "dataInicio": inicio.isoformat(),
                "dataFim": self.hoje.isoformat(),
                "siglaTipo": JANELA_TIPOS,
                "itens": 100,
                "ordem": "ASC",
                "ordenarPor": "id",
            },
            max_pages=JANELA_MAX_PAGINAS,
        )

    def senado_processo(self, sigla: str, numero: Any, ano: Any) -> None:
        processos = self._tolerar_ausencia(
            self.senado._get, "/processo", {"sigla": sigla, "numero": numero, "ano": ano}
        )
        for processo in processos if isinstance(processos, list) else []:
            self._tolerar_ausencia(self.senado._get, f"/processo/{processo['id']}")

    @staticmethod
    def _tolerar_ausencia(buscar: Callable, *args) -> Any:
        # 4xx em dado acessório é fato da fonte, e o transporte já registrou em `ausentes`.
        try:
            return buscar(*args)
        except httpx.HTTPStatusError as erro:
            if 400 <= erro.response.status_code < 500:
                return None
            raise


def executar_receita(receitas: Receitas, caso: dict) -> None:
    receita = caso.get("receita")
    if receita == "proposicao_completa":
        receitas.proposicao_completa(caso["fonte_id"])
    elif receita == "proposicao_com_cadeia":
        receitas.proposicao_com_cadeia(caso["fonte_id"])
    elif receita == "janela":
        receitas.janela()
    elif receita == "senado_processo":
        pass  # só as requisições de `senado`, abaixo
    else:
        raise CasoInvalido(f"Receita desconhecida em {caso.get('slug')}: {receita}")
    if caso.get("senado"):
        receitas.senado_processo(**caso["senado"])


def conferir_janela_completa(respostas: list[dict]) -> None:
    """Recusa janela truncada: `_get_paginated` para no limite de páginas sem avisar."""
    coletados = sum(len(r["corpo"].get("dados") or []) for r in respostas)
    total = respostas[-1]["cabecalhos"].get("x-total-count") if respostas else None
    if total is not None:
        if int(total) != coletados:
            raise GravacaoInterrompida(f"janela incompleta: {coletados} itens coletados, x-total-count {total}.")
    elif len(respostas) >= JANELA_MAX_PAGINAS and respostas[-1]["corpo"].get("dados"):
        raise GravacaoInterrompida(
            f"janela chegou ao limite de {JANELA_MAX_PAGINAS} páginas, sem x-total-count para conferir."
        )


def _serializar(pacote: dict) -> str:
    return json.dumps(pacote, ensure_ascii=False, indent=1) + "\n"


def _dividir(respostas: list[dict]) -> list[list[dict]]:
    """Reparte respostas, na ordem, em blocos que caibam no limite do hook."""
    blocos: list[list[dict]] = [[]]
    ocupado = 0
    margem_cabecalho = 300
    for envelope in respostas:
        tamanho = len(_serializar({"respostas": [envelope]}).encode("utf-8"))
        if blocos[-1] and ocupado + tamanho + margem_cabecalho > LIMITE_ARQUIVO:
            blocos.append([])
            ocupado = 0
        blocos[-1].append(envelope)
        ocupado += tamanho
    return blocos


def _gravar_pacote(arquivo: Path, caso: str, gravador: TransporteGravador, gravado_em: str) -> list[Path]:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    blocos = _dividir(gravador.respostas)
    escritos: list[Path] = []
    for numero, bloco in enumerate(blocos, start=1):
        pacote: dict[str, Any] = {
            "formato": 1,
            "caso": caso,
            "gravado_em": gravado_em,
            "sintetico": False,
        }
        if len(blocos) > 1:
            pacote["parte"] = numero
            pacote["partes"] = len(blocos)
        if numero == 1 and gravador.ausentes:
            pacote["ausentes_na_fonte"] = gravador.ausentes
        pacote["respostas"] = bloco
        destino = arquivo if numero == 1 else arquivo.with_name(f"{arquivo.stem}.parte-{numero:02d}.json")
        destino.write_text(_serializar(pacote), encoding="utf-8")
        escritos.append(destino)
    for antiga in arquivo.parent.glob(f"{arquivo.stem}.parte-*.json"):
        if antiga not in escritos:
            antiga.unlink()
    return escritos


def _tamanho_total(raiz: Path) -> int:
    return sum(p.stat().st_size for p in raiz.rglob("*") if p.is_file())


def _carregar_casos(raiz: Path) -> dict:
    return yaml.safe_load((raiz / "casos.yml").read_text("utf-8"))


def _salvar_casos(raiz: Path, documento: dict) -> None:
    corpo = yaml.safe_dump(documento, sort_keys=False, allow_unicode=True, width=100)
    (raiz / "casos.yml").write_text(CABECALHO_CASOS + corpo, encoding="utf-8")


def _selecionar(args: argparse.Namespace, documento: dict) -> list[dict]:
    casos = documento["casos"]
    if args.todos:
        return casos
    if args.caso.startswith("candidatos/"):
        if not args.fonte_id:
            raise CasoInvalido(f"{args.caso}: candidato exige --fonte-id <id da Câmara>.")
        return [{"slug": args.caso, "fonte_id": args.fonte_id, "receita": "proposicao_completa"}]
    encontrados = [c for c in casos if c["slug"] == args.caso]
    if not encontrados:
        raise CasoInvalido(f"Caso desconhecido: {args.caso} (a lista está em casos.yml).")
    return encontrados


def _arquivo_do_caso(raiz: Path, slug: str) -> Path:
    if slug.startswith("candidatos/"):
        return raiz / f"{slug}.json"
    return raiz / "gravacoes" / f"{slug}.json"


def main(
    argv: Optional[list[str]] = None,
    *,
    transporte_base: Optional[httpx.BaseTransport] = None,
    raiz: Path = RAIZ_FIXTURES,
    hoje: Optional[date] = None,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    alvo = parser.add_mutually_exclusive_group(required=True)
    alvo.add_argument("--caso", help="slug do casos.yml, ou candidatos/<id> com --fonte-id")
    alvo.add_argument("--todos", action="store_true", help="regrava todos os casos do casos.yml")
    parser.add_argument("--fonte-id", help="id da proposição na Câmara (só para candidatos/<id>)")
    args = parser.parse_args(argv)

    raiz = Path(raiz)
    hoje = hoje or datetime.now(FUSO).date()
    documento = _carregar_casos(raiz)
    try:
        selecionados = _selecionar(args, documento)
    except CasoInvalido as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    gravador = TransporteGravador(transporte_base or httpx.HTTPTransport())
    with CamaraClient(transport=gravador) as camara, SenadoClient(transport=gravador) as senado:
        for caso in selecionados:
            slug = caso["slug"]
            gravador.iniciar_caso()
            try:
                executar_receita(Receitas(camara, senado, hoje), caso)
                if caso.get("receita") == "janela":
                    conferir_janela_completa(gravador.respostas)
            except httpx.RequestError as erro:
                print(f"Erro: sem acesso à rede ao gravar {slug}: {erro}", file=sys.stderr)
                return 1
            except httpx.HTTPStatusError as erro:
                print(f"Erro: {slug}: HTTP {erro.response.status_code} em {erro.request.url.path}", file=sys.stderr)
                return 1
            except (GravacaoInterrompida, CasoInvalido, ValueError) as erro:
                print(f"Erro: {slug}: {erro}", file=sys.stderr)
                return 1

            gravado_em = datetime.now(FUSO).isoformat(timespec="seconds")
            escritos = _gravar_pacote(_arquivo_do_caso(raiz, slug), slug, gravador, gravado_em)
            tamanho = sum(p.stat().st_size for p in escritos)
            print(f"{slug}: {len(gravador.respostas)} respostas, {tamanho / 1024:.0f} KiB, {len(escritos)} arquivo(s)")
            for ausente in gravador.ausentes:
                print(
                    f"Aviso: {slug}: {ausente['host']} {ausente['caminho']} {ausente['params']} "
                    f"respondeu {ausente['status']}; não entra no pacote.",
                    file=sys.stderr,
                )
            for arquivo in escritos:
                if arquivo.stat().st_size > LIMITE_ARQUIVO:
                    print(
                        f"Aviso: {arquivo.name} passa de {LIMITE_ARQUIVO // 1024} KiB com uma resposta só; "
                        "o hook check-added-large-files pode recusar.",
                        file=sys.stderr,
                    )
            if not slug.startswith("candidatos/"):
                caso["hoje"] = hoje.isoformat()
                _salvar_casos(raiz, documento)

    total = _tamanho_total(raiz)
    if total > LIMITE_TOTAL:
        print(f"Aviso: tests/fixtures/tramitacao/ tem {total / 1024 / 1024:.1f} MB, acima de 8 MB.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

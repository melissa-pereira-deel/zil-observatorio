"""Catálogo de fontes externas — a allowlist, carregada e validada.

`data/fontes/catalogo.yml` é a lista do que o projeto aceita consultar para
preencher contexto e verificar alegações. Está sob a governança dos dados
editoriais pelo mesmo motivo que as instruções dos agentes: quem decide de
onde vêm os números controla o que o público lê. Muda por PR, e o hash do
arquivo vai para o meta de cada execução.

O que a carga garante, e não a disciplina de quem edita:

- toda fonte declara `natureza` e `vies_declarado` — "oficial" não é
  "neutro", e o catálogo diz o que cada fonte tem interesse em mostrar;
- toda fonte declara se é `primaria`. Secundária (o IPEA republica BCB e
  IBGE) serve para conferir transcrição e **nunca** conta como evidência
  independente — `independentes()` é o que a triangulação consulta;
- toda série tem `conceitos`: é só por eles que uma alegação casa com uma
  série, e a lista é auditável;
- `chave` é o NOME de uma variável de ambiente, nunca um valor. A carga
  recusa qualquer coisa que não pareça nome de variável.
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

import yaml

CATALOGO = Path(__file__).parent.parent.parent.parent / "data" / "fontes" / "catalogo.yml"

NATUREZAS = ("estatal", "autarquia", "associacao_setorial", "academia", "imprensa")
FREQUENCIAS = ("diaria", "mensal", "anual")
# Adaptadores implementados em `cliente.py`. Fonte habilitada sem adaptador
# conhecido é erro de carga, não de execução.
ADAPTADORES = ("bcb_sgs", "ibge_agregados", "ipea_odata")

_IDENTIFICADOR = re.compile(r"^[a-z][a-z0-9_]*$")
_NOME_DE_VARIAVEL = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
_HOST = re.compile(r"^[a-z0-9.-]+$")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, espaços colapsados — para casar conceitos."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", sem_acento).strip().lower()


@dataclass(frozen=True)
class Serie:
    fonte: str
    nome: str
    descricao: str
    unidade: str
    frequencia: str
    revisavel: bool
    conceitos: tuple[str, ...]
    parametros: tuple[tuple[str, str], ...]
    primaria_de: Optional[str] = None
    nota: str = ""

    @property
    def ref(self) -> str:
        return f"{self.fonte}.{self.nome}"

    def parametro(self, chave: str, padrao: str = "") -> str:
        return dict(self.parametros).get(chave, padrao)


@dataclass(frozen=True)
class Fonte:
    id: str
    nome: str
    sigla: str  # como a fonte aparece na linha de proveniência: "BCB SGS"
    host: str
    natureza: str
    primaria: bool
    vies_declarado: str
    adaptador: Optional[str]
    chave: Optional[str]
    habilitada: bool
    uso: str
    series: dict[str, Serie]


@dataclass(frozen=True)
class Catalogo:
    versao: int
    hash: str
    origem: str
    fontes: dict[str, Fonte]

    def serie(self, ref: str) -> Serie:
        fonte, _, nome = ref.partition(".")
        f = self.fontes.get(fonte)
        if f is None or nome not in f.series:
            raise ValueError(f"série não catalogada: {ref!r} — disponíveis: {sorted(self.refs)}")
        return f.series[nome]

    @property
    def refs(self) -> list[str]:
        return [s.ref for f in self.fontes.values() for s in f.series.values()]

    @property
    def hosts_permitidos(self) -> frozenset[str]:
        """Os únicos hosts que a camada de rede aceita. Fonte desabilitada
        fica fora: catalogada não é o mesmo que consultável."""
        return frozenset(f.host for f in self.fontes.values() if f.habilitada)

    def resolver(self, texto_ou_conceitos: Union[str, Iterable[str]]) -> list[Serie]:
        """Séries cujos conceitos aparecem no texto (ou na lista) dado.

        É a única forma de uma série ser escolhida para uma alegação. O
        casamento é por substring normalizada — "população" casa "populacao"
        — e o resultado vem em ordem estável, por `ref`.
        """
        if isinstance(texto_ou_conceitos, str):
            alvo = normalizar(texto_ou_conceitos)
        else:
            alvo = " | ".join(normalizar(c) for c in texto_ou_conceitos)
        achadas = [
            s
            for f in self.fontes.values()
            for s in f.series.values()
            if any(normalizar(c) in alvo for c in s.conceitos)
        ]
        return sorted(achadas, key=lambda s: s.ref)

    def origem_independente(self, serie: Serie) -> Optional[str]:
        """Quem de fato mede este dado. `None` = fonte secundária, não conta."""
        fonte = self.fontes[serie.fonte]
        if serie.primaria_de:
            return serie.primaria_de
        return fonte.id if fonte.primaria else None

    def independentes(self, series: Iterable[Serie]) -> set[str]:
        """Origens primárias distintas entre as séries dadas. Duas séries com
        a mesma origem são uma evidência, não duas — é o que impede a
        triangulação BCB × IPEA do IPCA de parecer confirmação."""
        return {o for o in (self.origem_independente(s) for s in series) if o}


def _exigir(bruto: dict, campo: str, onde: str):
    if campo not in bruto or bruto[campo] in (None, "", []):
        raise ValueError(f"catálogo: {onde}: campo obrigatório ausente: {campo}")
    return bruto[campo]


def _serie(fonte_id: str, nome: str, bruto: dict, ids_fontes: set[str]) -> Serie:
    onde = f"{fonte_id}.{nome}"
    if not _IDENTIFICADOR.match(nome):
        raise ValueError(f"catálogo: nome de série inválido: {onde!r}")
    if not isinstance(bruto, dict):
        raise ValueError(f"catálogo: {onde}: série não é um mapeamento")
    frequencia = _exigir(bruto, "frequencia", onde)
    if frequencia not in FREQUENCIAS:
        raise ValueError(f"catálogo: {onde}: frequência {frequencia!r} — válidas: {FREQUENCIAS}")
    if "revisavel" not in bruto or not isinstance(bruto["revisavel"], bool):
        raise ValueError(f"catálogo: {onde}: 'revisavel' é obrigatório e booleano")
    conceitos = _exigir(bruto, "conceitos", onde)
    if not isinstance(conceitos, list) or not all(isinstance(c, str) and c.strip() for c in conceitos):
        raise ValueError(f"catálogo: {onde}: 'conceitos' precisa ser lista de textos não vazios")
    parametros = bruto.get("parametros") or {}
    if not isinstance(parametros, dict) or not parametros:
        raise ValueError(f"catálogo: {onde}: 'parametros' precisa ser um mapeamento não vazio")
    primaria_de = bruto.get("primaria_de")
    if primaria_de is not None:
        if primaria_de not in ids_fontes:
            raise ValueError(f"catálogo: {onde}: primaria_de aponta para fonte desconhecida {primaria_de!r}")
        if primaria_de == fonte_id:
            raise ValueError(f"catálogo: {onde}: primaria_de não pode ser a própria fonte")
    return Serie(
        fonte=fonte_id,
        nome=nome,
        descricao=str(_exigir(bruto, "descricao", onde)).strip(),
        unidade=str(_exigir(bruto, "unidade", onde)).strip(),
        frequencia=frequencia,
        revisavel=bruto["revisavel"],
        conceitos=tuple(c.strip() for c in conceitos),
        parametros=tuple((str(k), str(v)) for k, v in parametros.items()),
        primaria_de=primaria_de,
        nota=str(bruto.get("nota") or "").strip(),
    )


def _fonte(fonte_id: str, bruto: dict, ids_fontes: set[str]) -> Fonte:
    if not _IDENTIFICADOR.match(fonte_id):
        raise ValueError(f"catálogo: id de fonte inválido: {fonte_id!r}")
    if not isinstance(bruto, dict):
        raise ValueError(f"catálogo: {fonte_id}: fonte não é um mapeamento")

    host = str(_exigir(bruto, "host", fonte_id)).strip()
    if not _HOST.match(host) or "/" in host:
        raise ValueError(f"catálogo: {fonte_id}: host inválido {host!r} — só o nome, sem esquema nem caminho")

    natureza = _exigir(bruto, "natureza", fonte_id)
    if natureza not in NATUREZAS:
        raise ValueError(f"catálogo: {fonte_id}: natureza {natureza!r} — válidas: {NATUREZAS}")
    if "primaria" not in bruto or not isinstance(bruto["primaria"], bool):
        raise ValueError(f"catálogo: {fonte_id}: 'primaria' é obrigatório e booleano")
    if not bruto["primaria"] and not bruto.get("uso"):
        raise ValueError(f"catálogo: {fonte_id}: fonte secundária precisa declarar 'uso'")

    chave = bruto.get("chave")
    if chave is not None and not _NOME_DE_VARIAVEL.match(str(chave)):
        raise ValueError(
            f"catálogo: {fonte_id}: 'chave' tem que ser o NOME de uma variável de ambiente "
            "(MAIÚSCULAS_E_SUBLINHADO), nunca o valor"
        )

    habilitada = bool(bruto.get("habilitada", True))
    adaptador = bruto.get("adaptador")
    if habilitada and adaptador not in ADAPTADORES:
        raise ValueError(
            f"catálogo: {fonte_id}: fonte habilitada exige adaptador conhecido {ADAPTADORES}; "
            f"recebido {adaptador!r}. Sem adaptador, declare habilitada: false"
        )

    series_bruto = bruto.get("series") or {}
    if not isinstance(series_bruto, dict):
        raise ValueError(f"catálogo: {fonte_id}: 'series' precisa ser um mapeamento")
    series = {nome: _serie(fonte_id, nome, s, ids_fontes) for nome, s in series_bruto.items()}

    return Fonte(
        id=fonte_id,
        nome=str(_exigir(bruto, "nome", fonte_id)).strip(),
        sigla=str(bruto.get("sigla") or fonte_id).strip(),
        host=host,
        natureza=natureza,
        primaria=bruto["primaria"],
        vies_declarado=str(_exigir(bruto, "vies_declarado", fonte_id)).strip(),
        adaptador=adaptador,
        chave=chave,
        habilitada=habilitada,
        uso=str(bruto.get("uso") or "").strip(),
        series=series,
    )


def carregar_catalogo(caminho: Path = CATALOGO) -> Catalogo:
    if not caminho.exists():
        raise FileNotFoundError(
            f"catálogo de fontes não encontrado em {caminho} — dentro do container, confira o mount ./data:/data:ro"
        )
    texto = caminho.read_text(encoding="utf-8")
    bruto = yaml.safe_load(texto)
    if not isinstance(bruto, dict) or not isinstance(bruto.get("fontes"), dict) or not bruto["fontes"]:
        raise ValueError(f"{caminho.name}: esperado um mapeamento com 'fontes' não vazio")

    ids = set(bruto["fontes"])
    fontes = {fid: _fonte(fid, f, ids) for fid, f in bruto["fontes"].items()}
    return Catalogo(
        versao=int(bruto.get("versao", 1)),
        hash=hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16],
        origem=caminho.name,
        fontes=fontes,
    )

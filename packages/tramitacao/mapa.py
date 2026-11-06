"""Esquema dos arquivos de data/tramitacao/ e carga do mapa (backlog-dados §2).

Sem banco e sem rede. A consistência entre arquivos e a cobertura dos códigos são do validador
(TRM-024, regras V-E e V-C); aqui fica o que a carga precisa para não servir nada errado em silêncio.
"""

import functools
import os
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Annotated, Callable, Iterable, Literal, Mapping, Optional, Union

import yaml
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator, model_validator

from packages.tramitacao.revisao import ArquivoRevisao, chave_rito, entradas_publicaveis, ids_de_conteudo
from packages.tramitacao.tipos import (
    Casa,
    CasaRito,
    ClassePrazo,
    Conjunto,
    Desfecho,
    Especie,
    Estrito,
    Fase,
    Motivo,
    RegraId,
)

HOSTS_NORMA = frozenset({
    "www.planalto.gov.br", "planalto.gov.br", "www2.camara.leg.br", "www.camara.leg.br",
    "legis.senado.leg.br", "www25.senado.leg.br", "www.congressonacional.leg.br", "normas.leg.br",
    "portal.stf.jus.br", "noticias.stf.jus.br",
})

# ── Tipos comuns (§2.2) ──


class BaseLegal(Estrito):
    norma: str = Field(pattern=r"^[A-Z0-9][A-Z0-9-]{1,30}$")
    dispositivo: str = Field(min_length=4, max_length=80)
    url: HttpUrl
    nota: Optional[str] = None

    @field_validator("url")
    @classmethod
    def _url_de_norma(cls, url: HttpUrl) -> HttpUrl:
        if url.scheme != "https" or url.host not in HOSTS_NORMA:
            raise ValueError(f"URL de base legal precisa ser https e de um host em HOSTS_NORMA: {url}")
        return url


class Caso(Estrito):
    casa: Casa
    fonte_id: str = Field(pattern=r"^[0-9]+$")
    rotulo: str
    nota: Optional[str] = None


class Procedencia(Estrito):
    base_legal: Conjunto[BaseLegal] = []
    base_legal_motivo: Optional[str] = Field(default=None, min_length=20)
    fontes: Conjunto[HttpUrl] = Field(min_length=1)
    pendente: Optional[str] = None

    @model_validator(mode="after")
    def _base_legal_ou_motivo(self):
        if bool(self.base_legal) == bool(self.base_legal_motivo):
            raise ValueError("a entrada precisa de exatamente um de base_legal e base_legal_motivo")
        return self


Marcador = Literal["na_casa", "da_casa", "membros", "orgao", "desde", "orgao_desde", "data",
                   "norma_com_artigo", "na_lei", "principal_com_artigo", "frase_principal"]


class ModeloFrase(Estrito):
    """Template da frase de "Onde está agora": vale o primeiro da lista cujos filtros casam."""

    casa: Optional[Casa] = None
    especie: Optional[Especie] = None
    veto_parcial: Optional[bool] = None
    quando: Conjunto[Marcador] = []
    modelo: str = Field(min_length=5, max_length=280)


class NaoMapeado(Estrito):
    cod: str
    descricao_oficial: str
    motivo: str = Field(pattern=r"^(sem_evidencia|fora_do_escopo|inativo|codigo_novo_\d{4}-\d{2}-\d{2})$")
    nota: Optional[str] = None

    @model_validator(mode="after")
    def _nota_de_fora_do_escopo(self):
        if self.motivo == "fora_do_escopo" and not self.nota:
            raise ValueError("motivo fora_do_escopo exige nota")
        return self


# ── fases.yml (§2.3) ──

Rotulo = Annotated[str, Field(max_length=32)]


class NormaBase(Estrito):
    nome: str
    url: HttpUrl


class FaseDef(Procedencia):
    chave: Fase
    ordem: int = Field(ge=1, le=9)
    rotulo: Rotulo
    rotulo_por_especie: dict[Especie, Rotulo] = {}
    rotulo_por_casa: dict[Casa, Rotulo] = {}
    rotulo_por_motivo: dict[Literal["recem_apresentada"], Rotulo] = {}
    pergunta: str
    glossario: Optional[str] = None
    frases: list[ModeloFrase] = Field(min_length=1)


class DesfechoDef(Procedencia):
    chave: Desfecho
    rotulo: Rotulo
    glossario: Optional[str] = None
    frases: list[ModeloFrase] = Field(min_length=1)


class ApensadaDef(Procedencia):
    rotulo: str
    glossario: Optional[str] = None
    frases: list[ModeloFrase] = Field(min_length=1)


class SituacaoTratada(Estrito):
    cod: str
    descricao_oficial: str
    fase: Optional[Fase] = None
    desfecho: Optional[Desfecho] = None
    motivo: Optional[Motivo] = None


class RegraDef(Procedencia):
    id: RegraId
    tipo: Literal["norma", "marco_terminal", "situacao_terminal", "apensacao", "outra_casa",
                  "pos_congresso", "orgao", "pre_despacho", "recem_apresentada", "fallback"]
    descricao: str
    parametros: dict[str, Union[int, str, list[str]]] = {}
    situacoes_camara: list[SituacaoTratada] = []
    situacoes_senado: list[SituacaoTratada] = []
    casos: Conjunto[Caso] = Field(min_length=1)


class ArquivoFases(Estrito):
    versao_esquema: Literal[1]
    normas_base: dict[str, NormaBase]
    fases: list[FaseDef]
    desfechos: list[DesfechoDef]
    # Opcional para o esqueleto de TRM-021a poder carregar sem conteúdo. Exigir a entrada, assim como
    # as 9 fases, os 7 desfechos e as regras R1..R10, é do validador (V-E2).
    apensada: Optional[ApensadaDef] = None
    regras: list[RegraDef]


# ── marcos.yml (§2.4) ──

TipoMarco = Literal[
    "apresentacao", "distribuicao", "apensacao", "designacao_relator", "parecer",
    "parecer_aprovado", "urgencia_aprovada", "votacao_plenario", "aprovacao_plenario",
    "remessa_outra_casa", "recebimento_outra_casa", "aprovacao_outra_casa", "retorno_emendas",
    "remessa_sancao", "norma", "norma_veto_parcial", "veto_total", "remessa_promulgacao",
    "arquivamento", "desarquivamento", "retirada", "prejudicialidade", "perda_eficacia", "devolucao",
]


class Variante(Estrito):
    padrao_despacho: str
    marco: Optional[TipoMarco] = None
    titulo: Optional[str] = Field(default=None, max_length=60)
    fase_resultante: Optional[Fase] = None
    terminal: Optional[Desfecho] = None


class MarcoDef(Procedencia):
    cod: str = Field(pattern=r"^[0-9]+$")
    casa: Casa
    descricao_oficial: str
    marco: TipoMarco
    titulo: str = Field(max_length=60)
    fase_resultante: Optional[Fase] = None
    terminal: Optional[Desfecho] = None
    reabre: Conjunto[Desfecho] = []
    condicao_despacho: Optional[str] = None
    variantes: list[Variante] = []
    extrai_norma: bool = False
    linha_do_tempo: bool = True
    casos: Conjunto[Caso] = Field(min_length=1)


class Ignorado(Estrito):
    cod: str
    descricao_oficial: str
    nota: str


class ArquivoMarcos(Estrito):
    versao_esquema: Literal[1]
    marcos: list[MarcoDef]
    ignorados: list[Ignorado]


class ArquivoNaoMapeados(Estrito):
    versao_esquema: Literal[1]
    situacoes_camara: list[NaoMapeado]
    situacoes_senado: list[NaoMapeado]
    tramitacao_camara: list[NaoMapeado]


# ── ritos.yml (§2.5) ──


class EtapaRito(Procedencia):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,40}$")
    fase: Fase
    casa: Optional[CasaRito] = None
    nome: str = Field(max_length=60)
    o_que_acontece: str = Field(max_length=400)
    quem_decide: Optional[str] = Field(default=None, max_length=160)
    classe_prazo: Optional[ClassePrazo] = None
    prazo_texto: Optional[str] = None
    opcional: bool = False
    pulada_quando: Optional[Literal["apreciacao_conclusiva", "sem_emendas_da_revisora",
                                    "sem_veto_total", "mpv_sem_alteracao", "mpv_alterada",
                                    "sancionada"]] = None
    condicao: Optional[str] = Field(default=None, max_length=120)
    nota_pulada: Optional[str] = Field(default=None, max_length=80)


class DesfechoRito(Procedencia):
    desfecho: Desfecho
    a_partir_de: Union[Conjunto[str], Literal["qualquer"]]
    texto: str = Field(max_length=300)


class Rito(Procedencia):
    especie: Especie
    # Mais estreito que CasaRito: "presidencia" é casa de etapa e não tem sufixo na chave do rito.
    casa_iniciadora: Literal["camara", "senado", "congresso"]
    nome: str
    etapas: list[EtapaRito] = Field(min_length=3)
    desfechos: list[DesfechoRito]
    notas: list[str] = []


class EspecieDef(Estrito):
    sigla: Especie
    nome: str
    glossario: Optional[str] = None


class ItemPosLei(Procedencia):
    id: Literal["publicacao", "vigencia", "regulamentacao"]
    nome: str
    texto: str = Field(max_length=400)
    classe_prazo: Optional[ClassePrazo] = None


class PosLei(Procedencia):
    itens: list[ItemPosLei] = Field(min_length=3, max_length=3)


class ArquivoRitos(Estrito):
    versao_esquema: Literal[1]
    especies: list[EspecieDef]
    ritos: list[Rito]
    pos_lei: Optional[PosLei] = None  # opcional pelo mesmo motivo de ArquivoFases.apensada


# ── glossario.yml (§2.6) ──


class CodigoRef(Estrito):
    casa: Casa
    cod: str


class Exemplo(Estrito):
    proposicao: str
    casa: Casa
    fonte_id: str = Field(pattern=r"^[0-9]+$")
    nota: Optional[str] = Field(default=None, max_length=200)


class EntradaGlossario(Procedencia):
    chave: str = Field(pattern=r"^[a-z][a-z0-9_]{2,59}$")
    tipo: Literal["situacao", "regime", "apreciacao", "fase", "desfecho", "apensada",
                  "etapa", "especie", "conceito"]
    termo: str = Field(max_length=120)
    texto_curto: str = Field(min_length=20, max_length=160)
    texto: str = Field(min_length=40, max_length=900)
    codigos: Conjunto[CodigoRef] = []
    descricao_oficial: Optional[str] = None
    fase: Optional[Fase] = None
    exemplos: Conjunto[Exemplo] = []
    relacionados: Conjunto[str] = []


class ArquivoGlossario(Estrito):
    versao_esquema: Literal[1]
    aviso: str
    entradas: list[EntradaGlossario]


# ── Carga (§2.9) ──


class MapaIndisponivel(Exception):
    """Os dados não estão onde deveriam. Nunca vira mapa vazio em silêncio (CLAUDE.md, armadilhas)."""


class MapaInvalido(Exception):
    def __init__(self, problemas: list[str]):
        super().__init__("\n".join(problemas))
        self.problemas = problemas


@dataclass(frozen=True)
class Mapa:
    versao_publicada: int
    publicada_em: Optional[date]
    publicaveis: frozenset[str]
    normas_base: Mapping[str, NormaBase]
    fases: Mapping[Fase, FaseDef]
    desfechos: Mapping[Desfecho, DesfechoDef]
    apensada: Optional[ApensadaDef]
    regras: Mapping[RegraId, RegraDef]
    situacao_por_codigo: Mapping[tuple[Casa, str], tuple[RegraId, SituacaoTratada]]
    nao_mapeados_situacao: Mapping[tuple[Casa, str], NaoMapeado]
    nao_mapeados_tramitacao: Mapping[tuple[Casa, str], NaoMapeado]
    marcos: Mapping[tuple[Casa, str], MarcoDef]
    ignorados: Mapping[tuple[Casa, str], Ignorado]
    ritos: Mapping[str, Rito]
    especies: Mapping[Especie, EspecieDef]
    pos_lei: Optional[PosLei]
    glossario: Mapping[str, EntradaGlossario]
    aviso_glossario: str
    conteudo_bruto: Mapping[str, dict]

    def publicavel(self, id_entrada: str) -> bool:
        return id_entrada in self.publicaveis

    def com_tudo_publicavel(self) -> "Mapa":
        """SÓ testes, validador, simular_fases e o pipeline de TRM-023 (teste de AST em TRM-024)."""
        return replace(self, publicaveis=frozenset(self.conteudo_bruto))


_ARQUIVOS_DE_CONTEUDO: dict[str, type[BaseModel]] = {
    "fases.yml": ArquivoFases,
    "marcos.yml": ArquivoMarcos,
    "ritos.yml": ArquivoRitos,
    "glossario.yml": ArquivoGlossario,
    "nao_mapeados.yml": ArquivoNaoMapeados,
}
_DIR_REPOSITORIO = Path(__file__).resolve().parents[2] / "data" / "tramitacao"
# Na imagem, parents[2] é /app, e /app/data/tramitacao não existe: os dados ficam em /data.
_DIR_CONTAINER = Path("/data/tramitacao")


def resolver_diretorio() -> Path:
    """ZIL_DATA_DIR/tramitacao, se a variável estiver definida; senão, repositório e depois container."""
    definido = os.environ.get("ZIL_DATA_DIR")
    if definido:
        # Quem definiu a variável disse onde os dados estão: não procura em outro lugar.
        diretorio = Path(definido) / "tramitacao"
        if not diretorio.is_dir():
            raise MapaIndisponivel(f"ZIL_DATA_DIR aponta para um diretório inexistente: {diretorio}")
        return diretorio
    for diretorio in (_DIR_REPOSITORIO, _DIR_CONTAINER):
        if diretorio.is_dir():
            return diretorio
    raise MapaIndisponivel(f"data/tramitacao não encontrado em {_DIR_REPOSITORIO} nem em {_DIR_CONTAINER}")


def _caminho(loc: Iterable[Union[int, str]]) -> str:
    texto = ""
    for parte in loc:
        if isinstance(parte, int):
            texto += f"[{parte}]"
        else:
            texto += f".{parte}" if texto else str(parte)
    return texto or "(raiz)"


def _ler_yaml(arquivo: Path, problemas: list[str]) -> Optional[dict]:
    try:
        bruto = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    except yaml.YAMLError as erro:
        problemas.append(f"{arquivo.name}: YAML inválido: {erro}")
        return None
    if not isinstance(bruto, dict):
        problemas.append(f"{arquivo.name}: o arquivo precisa ser um mapeamento, e veio {type(bruto).__name__}")
        return None
    return bruto


def _validar(nome: str, modelo: type[BaseModel], bruto: dict, problemas: list[str]) -> Optional[BaseModel]:
    try:
        return modelo.model_validate(bruto)
    except ValidationError as erro:
        problemas.extend(f"{nome}: {_caminho(e['loc'])}: {e['msg']}" for e in erro.errors())
        return None


def _indexar(itens: list, chave: Callable, onde: str, problemas: list[str]) -> Mapping:
    # Duas entradas com a mesma chave colidiriam no índice: uma sumiria sem aviso, e o hash conferido
    # na publicação seria o da que sobrou.
    indice: dict = {}
    for posicao, item in enumerate(itens):
        k = chave(item)
        if k in indice:
            problemas.append(f"{onde}[{posicao}]: chave repetida: {k}")
        indice[k] = item
    return MappingProxyType(indice)


def _indexar_situacoes(regras: list[RegraDef], problemas: list[str]) -> Mapping:
    indice: dict = {}
    for r, regra in enumerate(regras):
        for casa, campo, situacoes in (
            ("camara", "situacoes_camara", regra.situacoes_camara),
            ("senado", "situacoes_senado", regra.situacoes_senado),
        ):
            for s, situacao in enumerate(situacoes):
                k = (casa, situacao.cod)
                if k in indice:
                    problemas.append(f"fases.yml: regras[{r}].{campo}[{s}]: situação repetida: {k}")
                indice[k] = (regra.id, situacao)
    return MappingProxyType(indice)


def carregar_mapa(diretorio: Optional[Path] = None) -> Mapa:
    base = resolver_diretorio() if diretorio is None else Path(diretorio)
    if not base.is_dir():
        raise MapaIndisponivel(f"diretório inexistente: {base}")
    faltando = [nome for nome in _ARQUIVOS_DE_CONTEUDO if not (base / nome).is_file()]
    if faltando:
        raise MapaIndisponivel(f"arquivos ausentes em {base}: {', '.join(faltando)}")

    problemas: list[str] = []
    brutos: dict[str, dict] = {}
    modelos: dict[str, BaseModel] = {}
    for nome, modelo in _ARQUIVOS_DE_CONTEUDO.items():
        bruto = _ler_yaml(base / nome, problemas)
        if bruto is None:
            continue
        brutos[nome] = bruto
        validado = _validar(nome, modelo, bruto, problemas)
        if validado is not None:
            modelos[nome] = validado

    revisao: Optional[ArquivoRevisao] = ArquivoRevisao(versao_publicada=0, entradas={})
    if (base / "revisao.yml").is_file():
        bruto = _ler_yaml(base / "revisao.yml", problemas)
        revisao = None if bruto is None else _validar("revisao.yml", ArquivoRevisao, bruto, problemas)

    if problemas:
        raise MapaInvalido(problemas)

    fases: ArquivoFases = modelos["fases.yml"]
    marcos: ArquivoMarcos = modelos["marcos.yml"]
    ritos: ArquivoRitos = modelos["ritos.yml"]
    glossario: ArquivoGlossario = modelos["glossario.yml"]
    nao_mapeados: ArquivoNaoMapeados = modelos["nao_mapeados.yml"]

    def nao_mapeado(casa: str) -> Callable:
        return lambda item: (casa, item.cod)

    indices = {
        "fases": _indexar(fases.fases, lambda f: f.chave, "fases.yml: fases", problemas),
        "desfechos": _indexar(fases.desfechos, lambda d: d.chave, "fases.yml: desfechos", problemas),
        "regras": _indexar(fases.regras, lambda r: r.id, "fases.yml: regras", problemas),
        "situacao_por_codigo": _indexar_situacoes(fases.regras, problemas),
        "marcos": _indexar(marcos.marcos, lambda m: (m.casa, m.cod), "marcos.yml: marcos", problemas),
        "ignorados": _indexar(marcos.ignorados, nao_mapeado("camara"), "marcos.yml: ignorados", problemas),
        "ritos": _indexar(
            ritos.ritos, lambda r: chave_rito(r.especie, r.casa_iniciadora), "ritos.yml: ritos", problemas
        ),
        "especies": _indexar(ritos.especies, lambda e: e.sigla, "ritos.yml: especies", problemas),
        "glossario": _indexar(glossario.entradas, lambda e: e.chave, "glossario.yml: entradas", problemas),
        "nao_mapeados_tramitacao": _indexar(
            nao_mapeados.tramitacao_camara,
            nao_mapeado("camara"),
            "nao_mapeados.yml: tramitacao_camara",
            problemas,
        ),
    }
    nao_mapeados_situacao = {
        **_indexar(
            nao_mapeados.situacoes_camara, nao_mapeado("camara"), "nao_mapeados.yml: situacoes_camara", problemas
        ),
        **_indexar(
            nao_mapeados.situacoes_senado, nao_mapeado("senado"), "nao_mapeados.yml: situacoes_senado", problemas
        ),
    }
    if problemas:
        raise MapaInvalido(problemas)

    # O hash é do mapeamento bruto, antes do Pydantic aparar texto e normalizar URL (§2.1-4).
    conteudo = ids_de_conteudo(
        brutos["fases.yml"], brutos["marcos.yml"], brutos["ritos.yml"], brutos["glossario.yml"]
    )
    return Mapa(
        versao_publicada=revisao.versao_publicada,
        publicada_em=revisao.publicada_em,
        publicaveis=entradas_publicaveis(conteudo, revisao),
        normas_base=MappingProxyType(dict(fases.normas_base)),
        apensada=fases.apensada,
        pos_lei=ritos.pos_lei,
        nao_mapeados_situacao=MappingProxyType(nao_mapeados_situacao),
        aviso_glossario=glossario.aviso,
        conteudo_bruto=MappingProxyType(conteudo),
        **indices,
    )


@functools.lru_cache(maxsize=1)
def carregar_mapa_producao() -> Mapa:
    """Cache por processo: o conteúdo só muda em deploy."""
    return carregar_mapa()

"""Contexto pré-registrado — o que entra, idêntico, para todas as lentes.

Dar ferramenta a um agente é dar a ele a escolha do que buscar, e escolha de
busca é o vetor de viés mais silencioso: um economista ortodoxo-cético com
acesso livre a séries acha a série que confirma a leitura dele. A alavanca
está um passo antes: decidir **o que** se busca antes de ver qualquer
resultado — o mesmo princípio do pré-registro em pesquisa.

`data/fontes/planos/por_tema.yml` diz quais séries entram para toda
proposição e quais entram por tema oficial da Câmara ou categoria ZIL. A
escolha vira diff revisável; nenhuma lente busca nada; todas leem o mesmo
bloco (`ContextoEconomico.para_prompt()`), construído uma vez por execução.

Os valores são **ancorados na data de apresentação** da proposição — o
contexto que o autor tinha, não o que temos hoje — e o `hash` do contexto
cobre só o conteúdo (âncora, séries, datas, valores), nunca a data da
consulta: a mesma proposição, com as mesmas observações, dá o mesmo hash
amanhã. É o que a idempotência da `explicacao` precisa.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Iterable, Optional, Union

import yaml

from .catalogo import Catalogo, Serie, carregar_catalogo
from .cliente import Observacoes, consultar_serie

PLANOS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "fontes" / "planos"

# Quanto para trás, a partir do fim vigente, uma consulta olha para achar a
# última observação. Diária: feriados e fins de semana; mensal: a última
# divulgação. Anual é por anos inteiros em `inicio_janela`: o IBGE pula anos
# (2022 e 2023 sem estimativa, observado em 2026-10-21), então cinco garante um.
JANELA: dict[str, timedelta] = {
    "diaria": timedelta(days=14),
    "mensal": timedelta(days=400),
}


def fim_vigente(ancora: date, frequencia: str) -> date:
    """A última data de referência que já estava PUBLICADA na âncora.

    Um valor mensal de março só sai em abril; a estimativa anual de população
    de 2025 só sai em agosto de 2025. Ancorar em 10/03/2025 e trazer o IPCA
    de março ou a população de 2025 seria dar ao leitor um contexto que o
    autor da proposição não tinha (primeiro smoke test, 2026-10-21). A regra
    é conservadora: mensal até o mês anterior, anual até o ano anterior.
    """
    if frequencia == "mensal":
        return ancora.replace(day=1) - timedelta(days=1)
    if frequencia == "anual":
        return date(ancora.year - 1, 12, 31)
    return ancora


def inicio_janela(fim: date, frequencia: str) -> date:
    """Série anual olha anos inteiros (o IBGE indexa por ano); as outras, dias."""
    if frequencia == "anual":
        return date(fim.year - 4, 1, 1)
    return fim - JANELA[frequencia]

Consultar = Callable[..., Observacoes]


@dataclass(frozen=True)
class Plano:
    nome: str
    hash: str
    origem: str
    sempre: tuple[str, ...]
    por_tema: dict[str, tuple[str, ...]]


def carregar_plano(nome: str = "por_tema", diretorio: Path = PLANOS_DIR, catalogo: Optional[Catalogo] = None) -> Plano:
    """Carrega o plano e confere que toda referência existe no catálogo —
    um plano que aponta para série fantasma falha na carga, não na execução."""
    caminho = diretorio / f"{nome}.yml"
    if not caminho.exists():
        raise FileNotFoundError(f"plano de contexto não encontrado em {caminho}")
    texto = caminho.read_text(encoding="utf-8")
    bruto = yaml.safe_load(texto)
    if not isinstance(bruto, dict):
        raise ValueError(f"{caminho.name}: YAML não é um mapeamento")
    catalogo = catalogo or carregar_catalogo()

    sempre = tuple(bruto.get("sempre") or [])
    por_tema = {str(k): tuple(v or []) for k, v in (bruto.get("por_tema") or {}).items()}
    for ref in list(sempre) + [r for refs in por_tema.values() for r in refs]:
        catalogo.serie(ref)  # lança ValueError com a lista do que existe
    return Plano(
        nome=str(bruto.get("nome") or nome),
        hash=hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16],
        origem=caminho.name,
        sempre=sempre,
        por_tema=por_tema,
    )


def planejar(plano: Plano, temas_oficiais: Iterable[str], categorias_zil: Iterable[str]) -> tuple[list[str], str]:
    """As séries desta proposição, em ordem estável. Devolve (refs, motivo)."""
    refs: list[str] = list(plano.sempre)
    chaves = list(temas_oficiais) + list(categorias_zil)
    ligadas: list[str] = []
    for chave in chaves:
        for ref in plano.por_tema.get(chave, ()):
            if ref not in refs:
                refs.append(ref)
                ligadas.append(ref)
    motivo = f"sempre {list(plano.sempre)}" + (f" + por tema {ligadas} via {chaves}" if ligadas else f"; nenhuma série por tema via {chaves}")
    return refs, motivo


# ── formatação para o leitor ──────────────────────────────────────────────────

def _numero_br(valor: float) -> str:
    if float(valor).is_integer() and abs(valor) >= 1000:
        return f"{int(valor):,}".replace(",", ".")
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _data_br(iso: str, frequencia: str) -> str:
    a, m, d = iso[:4], iso[5:7], iso[8:10]
    if frequencia == "anual":
        return a
    if frequencia == "mensal":
        return f"{m}/{a}"
    return f"{d}/{m}/{a}"


@dataclass
class Linha:
    """Uma observação com tudo que o leitor precisa para conferir sozinho."""

    ref: str
    descricao: str
    valor: float
    unidade: str
    data: str
    frequencia: str
    fonte_nome: str
    fonte_sigla: str
    natureza: str
    primaria: bool
    primaria_de: Optional[str]
    primaria_de_sigla: Optional[str]
    revisavel: bool
    parametros: dict
    url: str
    data_consulta: str
    nota: str = ""

    def para_prompt(self) -> str:
        origem = f"{self.fonte_sigla} {' '.join(self.parametros.values())}"
        if self.primaria_de:
            origem += f" (dado primário do {self.primaria_de_sigla or self.primaria_de})"
        vintage = "sujeito a revisão" if self.revisavel else "valor definitivo"
        sep = "" if self.unidade.startswith("%") else " "
        return (
            f"- {self.descricao}: {_numero_br(self.valor)}{sep}{self.unidade} em {_data_br(self.data, self.frequencia)}"
            f" · {origem} · consultado em {self.data_consulta[:10]} · {vintage}"
        )


@dataclass
class ContextoEconomico:
    ancora: str
    refs: list[str]
    motivo: str
    linhas: list[Linha] = field(default_factory=list)
    lacunas: list[tuple[str, str]] = field(default_factory=list)  # (ref, motivo)
    plano_hash: str = ""
    catalogo_hash: str = ""

    @property
    def hash(self) -> str:
        """Só conteúdo: âncora, séries, datas e valores. Nunca a data da
        consulta nem o texto do erro — senão o hash mudaria todo dia."""
        canon = {
            "ancora": self.ancora,
            "linhas": [(ln.ref, ln.data, ln.valor, ln.unidade) for ln in self.linhas],
            "lacunas": sorted(ref for ref, _ in self.lacunas),
        }
        return hashlib.sha256(json.dumps(canon, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]

    @property
    def vazio(self) -> bool:
        return not self.linhas

    def para_prompt(self) -> str:
        """O bloco que TODAS as lentes recebem. Diz o que não obteve, e proíbe
        número de memória — a proibição é instrução; a garantia é o revisor."""
        a = self.ancora
        cabeca = [
            "[CONTEXTO ECONÔMICO — séries pré-registradas por tema, idênticas para todas as lentes]",
            f"Ancorado na data de apresentação da proposição ({_data_br(a, 'diaria')}): os valores são os "
            "que já estavam publicados naquela data, não os de hoje.",
        ]
        corpo = [ln.para_prompt() for ln in self.linhas] or ["(nenhuma série obtida)"]
        if self.lacunas:
            corpo.append("Não obtidos:")
            corpo.extend(f"  - {ref}: {motivo}" for ref, motivo in self.lacunas)
        rodape = [
            "",
            "Use APENAS os números acima. Se a sua análise precisar de um número que não está aqui, "
            "escreva que ele não está disponível neste contexto — não o traga de memória.",
        ]
        return "\n".join(cabeca + corpo + rodape)

    def evidencias(self) -> dict:
        """O que vai para `explicacoes.evidencias`: a explicação carrega os
        números que viu, não um ponteiro para uma série que vai mudar."""
        return {
            "ancora": self.ancora,
            "hash": self.hash,
            "plano_hash": self.plano_hash,
            "catalogo_hash": self.catalogo_hash,
            "motivo": self.motivo,
            "linhas": [
                {
                    "ref": ln.ref, "valor": ln.valor, "unidade": ln.unidade, "data": ln.data,
                    "url": ln.url, "data_consulta": ln.data_consulta, "revisavel": ln.revisavel,
                    "primaria_de": ln.primaria_de,
                }
                for ln in self.linhas
            ],
            "lacunas": [{"ref": r, "motivo": m} for r, m in self.lacunas],
        }


def _ancora(valor: Union[str, date, None]) -> date:
    if isinstance(valor, date):
        return valor
    if valor and len(str(valor)) >= 10:
        return date.fromisoformat(str(valor)[:10])
    raise ValueError("contexto sem âncora: a proposição não tem data de apresentação")


def montar_contexto(
    *,
    ancora: Union[str, date, None],
    temas_oficiais: Iterable[str] = (),
    categorias_zil: Iterable[str] = (),
    plano: Optional[Plano] = None,
    catalogo: Optional[Catalogo] = None,
    consultar: Consultar = consultar_serie,
    **opcoes,
) -> ContextoEconomico:
    """Monta o bloco de contexto de uma proposição. Chamado UMA vez por
    execução; o mesmo objeto alimenta todas as lentes (informação simétrica).

    `consultar` é a fronteira (`cliente.consultar_serie`), injetável; `opcoes`
    vai para ela (transport, cache_dir, agora...). Falha de uma série vira
    lacuna declarada, nunca exceção.
    """
    catalogo = catalogo or carregar_catalogo()
    plano = plano or carregar_plano(catalogo=catalogo)
    dia = _ancora(ancora)
    refs, motivo = planejar(plano, temas_oficiais, categorias_zil)
    ctx = ContextoEconomico(ancora=dia.isoformat(), refs=refs, motivo=motivo, plano_hash=plano.hash, catalogo_hash=catalogo.hash)

    for ref in refs:
        serie: Serie = catalogo.serie(ref)
        fonte = catalogo.fontes[serie.fonte]
        fim = fim_vigente(dia, serie.frequencia)
        res = consultar(serie, inicio_janela(fim, serie.frequencia), fim, catalogo=catalogo, **opcoes)
        if not res.ok:
            ctx.lacunas.append((ref, res.erro or "erro desconhecido"))
            continue
        ultima = res.ultima
        if ultima is None:
            ctx.lacunas.append((ref, f"sem observação entre {res.inicio} e {res.fim}"))
            continue
        ctx.linhas.append(
            Linha(
                ref=ref, descricao=serie.descricao, valor=ultima.valor, unidade=serie.unidade,
                data=ultima.data, frequencia=serie.frequencia, fonte_nome=fonte.nome, fonte_sigla=fonte.sigla,
                natureza=fonte.natureza, primaria=fonte.primaria, primaria_de=serie.primaria_de,
                primaria_de_sigla=catalogo.fontes[serie.primaria_de].sigla if serie.primaria_de else None,
                revisavel=serie.revisavel,
                parametros=dict(serie.parametros), url=res.url, data_consulta=res.data_consulta, nota=serie.nota,
            )
        )
    return ctx

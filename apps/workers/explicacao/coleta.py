"""Ficha de fatos de uma proposição — recuperação, não raciocínio.

O resumo detalhado precisa de coisas que o texto não traz: quem apresentou e
de que partido, quando andou por onde, o que está apensado. A API tem tudo
isso (RFC-006, C4) e o projeto nunca buscou — `Proposicao.autores` e
`Proposicao.tramitacoes` existem como colunas e nunca foram preenchidas.

A ficha entra no prompt como **contexto confiável do projeto**, fora do bloco
blindado, e é a referência contra a qual o revisor confere nomes, partidos e
datas da saída. Cada campo sabe de que endpoint veio (`origens`), para que uma
afirmação do resumo possa ser rastreada até a fonte.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from packages.camara_client import CamaraClient

_ID_DEPUTADO = re.compile(r"/deputados/(\d+)")
_SIGLA = re.compile(r"^[A-ZÇ][A-ZÇ ]{1,20}$")
# Como a Câmara escreve um parlamentar dentro de uma ementa ou de um despacho:
# "pelo Relator, Dep. Arnaldo Jardim (CIDADANIA-SP)". Grupo 1 é o nome, 2 o
# partido. É o único jeito de um relator entrar na ficha — ele não é autor.
_PARLAMENTAR_NO_TEXTO = re.compile(
    r"\bDep(?:utad[oa])?\.?\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁ-ú]+(?:\s+(?:d[aeo]s?\s+)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁ-ú]+){0,4})"
    r"\s*\(([A-Za-zÇç]+)\s*-\s*[A-Z]{2}\)"
)
_PARTIDO_UF = re.compile(r"\(([A-Za-zÇç]+)\s*-\s*[A-Z]{2}\)")
_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def data_br(data: str) -> str:
    """Converte "2024-07-08" (ou com hora) → "08/07/2024". O resto passa intacto. A
    ficha é lida por quem escreve para o público; data ISO no prompt virava
    data ISO no resumo."""
    m = _ISO.match(data or "")
    return f"{m.group(3)}/{m.group(2)}/{m.group(1)}" if m else data


@dataclass(frozen=True)
class Autor:
    nome: str
    tipo: str
    partido: Optional[str] = None
    uf: Optional[str] = None


@dataclass(frozen=True)
class Tramitacao:
    data: str
    orgao: str
    descricao: str
    url: Optional[str] = None


@dataclass(frozen=True)
class Relacionada:
    sigla_tipo: str
    numero: Optional[int]
    ano: Optional[int]
    ementa: str


@dataclass
class FichaFatos:
    fonte: str
    fonte_id: str
    tipo: str = ""
    numero: Optional[int] = None
    ano: Optional[int] = None
    ementa: str = ""
    situacao: str = ""
    data_apresentacao: str = ""
    url_inteiro_teor: str = ""
    autores: list[Autor] = field(default_factory=list)
    tramitacoes: list[Tramitacao] = field(default_factory=list)
    relacionadas: list[Relacionada] = field(default_factory=list)
    temas_oficiais: list[str] = field(default_factory=list)
    # campo → endpoint de onde veio. Vazio = não buscado.
    origens: dict[str, str] = field(default_factory=dict)

    @property
    def rotulo(self) -> str:
        return f"{self.tipo} {self.numero}/{self.ano}".strip()

    @property
    def partidos(self) -> set[str]:
        return {a.partido for a in self.autores if a.partido}

    @property
    def grupo_politico(self) -> str:
        """Coalizão, não partido: a PNMCE tem 15 autores de PSDB a CIDADANIA."""
        if not self.autores:
            return "autoria não informada"
        ps = sorted(self.partidos)
        if not ps:
            return "autoria sem partido (Executivo, comissão ou órgão)"
        return f"{len(self.autores)} autor(es) de {len(ps)} partido(s): {', '.join(ps)}"


def _partido_uf(client: CamaraClient, uri: str) -> tuple[Optional[str], Optional[str]]:
    m = _ID_DEPUTADO.search(uri or "")
    if not m:
        return None, None
    try:
        d = client.obter_deputado(int(m.group(1)))
    except Exception:  # noqa: BLE001 — um deputado inacessível não derruba a ficha
        return None, None
    status = (d or {}).get("ultimoStatus") or {}
    return status.get("siglaPartido") or None, status.get("siglaUf") or None


def coletar_ficha(client: CamaraClient, proposicao_id: int, fonte: str = "camara") -> FichaFatos:
    """Monta a ficha a partir da API. Falha de um endpoint secundário não derruba
    a ficha — o campo fica vazio e **sem origem**, e o resumo detalhado tem que
    dizer que não sabe, em vez de inventar."""
    ficha = FichaFatos(fonte=fonte, fonte_id=str(proposicao_id))

    d = client.obter_proposicao(proposicao_id) or {}
    ficha.tipo = d.get("siglaTipo") or ""
    ficha.numero = d.get("numero")
    ficha.ano = d.get("ano")
    ficha.ementa = d.get("ementa") or ""
    ficha.situacao = ((d.get("statusProposicao") or {}).get("descricaoSituacao")) or ""
    ficha.data_apresentacao = (d.get("dataApresentacao") or "")[:10]
    ficha.url_inteiro_teor = d.get("urlInteiroTeor") or ""
    ficha.origens["proposicao"] = f"/proposicoes/{proposicao_id}"

    try:
        for a in client.obter_autores(proposicao_id):
            partido, uf = _partido_uf(client, a.get("uri") or "")
            ficha.autores.append(Autor(nome=a.get("nome") or "", tipo=a.get("tipo") or "", partido=partido, uf=uf))
        ficha.origens["autores"] = f"/proposicoes/{proposicao_id}/autores (+ /deputados/{{id}})"
    except Exception:  # noqa: BLE001
        pass

    try:
        for t in client.obter_tramitacoes(proposicao_id):
            ficha.tramitacoes.append(
                Tramitacao(
                    data=(t.get("dataHora") or "")[:10],
                    orgao=t.get("siglaOrgao") or "",
                    descricao=t.get("descricaoTramitacao") or t.get("despacho") or "",
                    url=t.get("url") or None,
                )
            )
        ficha.origens["tramitacoes"] = f"/proposicoes/{proposicao_id}/tramitacoes"
    except Exception:  # noqa: BLE001
        pass

    try:
        for r in client.obter_relacionadas(proposicao_id):
            ficha.relacionadas.append(
                Relacionada(
                    sigla_tipo=r.get("siglaTipo") or "",
                    numero=r.get("numero"),
                    ano=r.get("ano"),
                    ementa=(r.get("ementa") or "")[:200],
                )
            )
        ficha.origens["relacionadas"] = f"/proposicoes/{proposicao_id}/relacionadas"
    except Exception:  # noqa: BLE001
        pass

    try:
        ficha.temas_oficiais = [t.get("tema") for t in client.obter_temas(proposicao_id) if t.get("tema")]
        ficha.origens["temas_oficiais"] = f"/proposicoes/{proposicao_id}/temas"
    except Exception:  # noqa: BLE001
        pass

    return ficha


def ficha_para_prompt(ficha: FichaFatos, max_tramitacoes: int = 25) -> str:
    """A ficha como bloco de contexto confiável. Diz o que NÃO sabe."""
    linhas = [f"[FICHA DE FATOS — {ficha.rotulo}]"]
    linhas.append(f"Ementa oficial: {ficha.ementa or '(não informada)'}")
    linhas.append(f"Situação: {ficha.situacao or '(não informada)'}")
    linhas.append(f"Apresentada em: {data_br(ficha.data_apresentacao) or '(não informada)'}")

    if "autores" in ficha.origens:
        linhas.append(f"Autoria: {ficha.grupo_politico}")
        for a in ficha.autores[:20]:
            quem = a.nome + (f" ({a.partido}-{a.uf})" if a.partido else f" [{a.tipo}]")
            linhas.append(f"  - {quem}")
    else:
        linhas.append("Autoria: NÃO OBTIDA — não afirme nada sobre autores.")

    if "temas_oficiais" in ficha.origens:
        linhas.append(f"Temas oficiais (Câmara): {', '.join(ficha.temas_oficiais) or 'nenhum atribuído'}")

    if "tramitacoes" in ficha.origens:
        linhas.append(f"Cronologia ({len(ficha.tramitacoes)} eventos; mostrando até {max_tramitacoes}):")
        for t in ficha.tramitacoes[:max_tramitacoes]:
            linhas.append(f"  - {data_br(t.data)} {t.orgao}: {t.descricao[:120]}")
    else:
        linhas.append("Cronologia: NÃO OBTIDA — não afirme datas de tramitação.")

    if "relacionadas" in ficha.origens:
        if ficha.relacionadas:
            linhas.append(f"Relacionadas ({len(ficha.relacionadas)}):")
            for r in ficha.relacionadas[:15]:
                linhas.append(f"  - {r.sigla_tipo} {r.numero}/{r.ano}: {r.ementa[:100]}")
        else:
            linhas.append("Relacionadas: nenhuma registrada.")

    linhas.append("")
    linhas.append(
        "Use APENAS os nomes, partidos e datas acima. O que não está aqui, você não sabe — diga que não sabe."
    )
    return "\n".join(linhas)


def entidades_conhecidas(ficha: FichaFatos) -> dict[str, set[str]]:
    """O universo de entidades que uma saída pode mencionar sem inventar.

    Usado pelo revisor (métrica 2). Conservador de propósito: compara nomes de
    autores, siglas de partido e datas — não tenta reconhecer entidade genérica,
    porque falso positivo aqui derrubaria explicações corretas.

    Além dos autores, conta quem a própria Câmara nomeia nas relacionadas e na
    cronologia, no formato "Dep. Nome (PARTIDO-UF)". O relator não é autor, e
    sem isto a PNMCE foi reprovada por citar "Arnaldo Jardim (CIDADANIA-SP)",
    que está nos pareceres de plenário da ficha (2026-10-28).
    """
    textos = [r.ementa for r in ficha.relacionadas] + [t.descricao for t in ficha.tramitacoes]
    nomes = {a.nome for a in ficha.autores if a.nome}
    partidos = set(ficha.partidos)
    for texto in textos:
        nomes |= {m.group(1).strip() for m in _PARLAMENTAR_NO_TEXTO.finditer(texto or "")}
        partidos |= {m.group(1) for m in _PARTIDO_UF.finditer(texto or "")}
    return {
        "nomes": nomes,
        "partidos": partidos,
        "datas": {t.data for t in ficha.tramitacoes if t.data} | ({ficha.data_apresentacao} if ficha.data_apresentacao else set()),
    }

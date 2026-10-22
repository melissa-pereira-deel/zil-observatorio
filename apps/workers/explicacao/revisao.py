"""Revisão determinística — as métricas que não dependem de modelo nenhum.

O revisor-agente (rubrica, leitura) é Fase 2. O que está aqui roda na CI e é
o que torna o go/no-go verificável sem chave:

- métrica 1: tamanhos dentro dos limites (o schema já garante; aqui registra);
- métrica 2: **entidades fabricadas** — nome, partido ou data que não existe
  na ficha. Zero é a meta e um é no-go;
- métrica 3: citações literais presentes no texto extraído;
- métrica 4: dissenso preservado — se duas lentes discordaram, a síntese tem
  que listar;
- métrica 7: lentes roteadas que disseram "nada a dizer".
"""

import re
from dataclasses import dataclass, field

from .coleta import FichaFatos, entidades_conhecidas
from .schema import AnaliseSistemica, ParecerLente, ResumoDetalhado, ResumoDidatico

# "Deputado Fulano de Tal", "Deputada Fulana" — a forma como um texto nomeia
# um autor. É o único padrão de nome que o revisor confere: nome genérico
# ("o relator", "o Governo") não é entidade verificável.
_DEPUTADO = re.compile(r"\bDeputad[oa]s?\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁ-ú]+(?:\s+(?:d[aeo]s?\s+)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁ-ú]+){0,4})")
_DATA_BR = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_DATA_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
# Siglas de partido que o projeto conhece. Uma sigla fora desta lista não é
# conferida — "ONU" não é partido. A lista é a dos partidos com assento na
# legislatura 2023–2026 e pode crescer.
PARTIDOS = frozenset({
    "PL", "PT", "UNIÃO", "UNIAO", "PP", "PSD", "MDB", "REPUBLICANOS", "PDT", "PSB",
    "PODE", "PODEMOS", "PSDB", "CIDADANIA", "PSOL", "PCDOB", "PCdoB", "AVANTE",
    "SOLIDARIEDADE", "PV", "REDE", "NOVO", "PRD", "PATRIOTA", "PROS", "PTB",
})
_SIGLA = re.compile(r"\b([A-ZÇ]{2,13}|PCdoB)\b")
# O que vem logo depois de uma sigla quando ela é tipo de proposição: "PL 1001/2025", "PEC 45".
_NUMERO_DE_PROPOSICAO = re.compile(r"\s*n?[ºo°.]?\s*\d")


def _normaliza_data(m: re.Match, iso: bool) -> str:
    if iso:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"


@dataclass
class Revisao:
    metricas: dict = field(default_factory=dict)
    problemas: list[str] = field(default_factory=list)

    @property
    def aprovada(self) -> bool:
        return not self.problemas


def entidades_fabricadas(texto: str, ficha: FichaFatos) -> list[str]:
    """Entidades no texto que não existem na ficha. Conservador: só nomes
    introduzidos por "Deputado(a)", siglas de partido conhecidas e datas."""
    conhecidas = entidades_conhecidas(ficha)
    achadas: list[str] = []

    for m in _DEPUTADO.finditer(texto):
        nome = m.group(1).strip()
        if not any(nome in n or n in nome for n in conhecidas["nomes"]):
            achadas.append(f"nome: {nome}")

    for m in _SIGLA.finditer(texto):
        sigla = m.group(1)
        # "PL 1001/2025" é o tipo da proposição, não o Partido Liberal. Sigla
        # seguida de número é referência a proposição e não entra na conta —
        # sem isto, todo resumo detalhado seria acusado de inventar o PL.
        if _NUMERO_DE_PROPOSICAO.match(texto, m.end()):
            continue
        if sigla in PARTIDOS and sigla.upper() not in {p.upper() for p in conhecidas["partidos"]}:
            achadas.append(f"partido: {sigla}")

    for m in _DATA_BR.finditer(texto):
        d = _normaliza_data(m, iso=False)
        if d not in conhecidas["datas"]:
            achadas.append(f"data: {m.group(0)}")
    for m in _DATA_ISO.finditer(texto):
        d = _normaliza_data(m, iso=True)
        if d not in conhecidas["datas"]:
            achadas.append(f"data: {m.group(0)}")

    # dedup preservando ordem
    vistas: set[str] = set()
    return [a for a in achadas if not (a in vistas or vistas.add(a))]


def _citacao_presente(citacao: str, texto: str) -> bool:
    if not texto:
        return False
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()  # noqa: E731
    return norm(citacao) in norm(texto)


def revisar(
    *,
    ficha: FichaFatos,
    texto_extraido: str,
    pareceres: list[ParecerLente],
    lentes_roteadas: list[str],
    resumo_didatico: ResumoDidatico | None,
    resumo_detalhado: ResumoDetalhado | None,
    analise: AnaliseSistemica | None,
) -> Revisao:
    r = Revisao()

    # 1 — tamanhos (o schema já rejeitou; aqui só registra o que passou)
    r.metricas["tamanho_didatico"] = len(resumo_didatico.texto) if resumo_didatico else None
    r.metricas["tamanho_detalhado"] = len(resumo_detalhado.texto) if resumo_detalhado else None

    # 2 — entidades fabricadas, no detalhado e no didático
    fabricadas: list[str] = []
    for campo, resumo in (("didatico", resumo_didatico), ("detalhado", resumo_detalhado)):
        if resumo:
            for e in entidades_fabricadas(resumo.texto, ficha):
                fabricadas.append(f"{campo}: {e}")
    r.metricas["entidades_fabricadas"] = len(fabricadas)
    if fabricadas:
        r.problemas.append("entidades fora da ficha: " + "; ".join(fabricadas))

    # 3 — citações literais verificáveis
    literais = [a for p in pareceres for a in p.afirmacoes if a.tipo == "literal"]
    presentes = sum(1 for a in literais if _citacao_presente(a.citacao or "", texto_extraido))
    r.metricas["citacoes_literais"] = len(literais)
    r.metricas["citacoes_verificadas"] = presentes
    if literais and presentes / len(literais) < 0.95:
        r.problemas.append(f"citações não encontradas no texto: {len(literais) - presentes} de {len(literais)}")

    # 4 — dissenso preservado. Heurística determinística: duas lentes com
    # afirmações sobre a MESMA dimensão são candidatas a dissenso; se existem
    # e a síntese não lista nenhum dissenso, isso precisa ser justificado por
    # um revisor-agente (Fase 2). Aqui, fica registrado como problema.
    por_dimensao: dict[str, set[str]] = {}
    for p in pareceres:
        for a in p.afirmacoes:
            por_dimensao.setdefault(a.dimensao, set()).add(p.lente)
    sobrepostas = {d for d, ls in por_dimensao.items() if len(ls) >= 2}
    r.metricas["dimensoes_com_mais_de_uma_lente"] = len(sobrepostas)
    r.metricas["dissensos"] = len(analise.dissensos) if analise else 0
    if analise is not None and sobrepostas and not analise.dissensos:
        r.problemas.append(
            f"síntese sem dissensos apesar de {len(sobrepostas)} dimensão(ões) com mais de uma lente: "
            f"{sorted(sobrepostas)} — ou as lentes convergiram (confirmar) ou a síntese apagou o desacordo"
        )

    # 7 — cobertura: lentes roteadas que não tinham nada a dizer / falharam
    sem_nada = [p.lente for p in pareceres if p.nada_a_dizer]
    indisponiveis = [p.lente for p in pareceres if not p.disponivel]
    r.metricas["lentes_roteadas"] = len(lentes_roteadas)
    r.metricas["lentes_nada_a_dizer"] = len(sem_nada)
    r.metricas["lentes_indisponiveis"] = len(indisponiveis)
    # Mais da metade das lentes roteadas sem nada a dizer é sinal sobre a
    # TABELA DE ROTEAMENTO, agregado por lote — não invalida esta explicação.
    # O plano é explícito: as faixas disparam inspeção, não aprovam nem
    # reprovam (PRD-PAINEL §14, aviso de n pequeno). Fica em métricas.
    r.metricas["roteamento_suspeito"] = bool(
        lentes_roteadas and len(sem_nada) / len(lentes_roteadas) > 0.5
    )

    # injection — sinal, não falha: a análise continua, mas fica marcada
    r.metricas["injecao_detectada"] = any(p.injecao_detectada for p in pareceres)

    return r

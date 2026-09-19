"""Monta um dossiê de pesquisa para uma votação, para acelerar a curadoria editorial.

O gargalo do projeto é o tempo de pesquisa por classificação: entender a matéria,
ler o texto legal e decidir se votar "sim" favorece ou não a soberania industrial
custa horas. Este script reúne automaticamente tudo que essa pesquisa exigiria ler,
para que a tarefa vire "ler um dossiê e decidir".

**O que ele não faz:** decidir. O YAML emitido ao final vem sem o campo `direcao`
de propósito — essa é a decisão humana, e é o que o projeto inteiro existe para
manter humana (ver docs/GOVERNANCE.md e docs/decisions/004-placar-focado.md).

Uso (da raiz do repositório):

    python scripts/dossie.py --votacao 2454704-53
    python scripts/dossie.py --votacao 2454704-53 --out data/dossies/
    python scripts/dossie.py --votacao 2454704-53 --sem-llm

Funciona sem banco e sem ANTHROPIC_API_KEY — nesses casos o dossiê sai completo
nas fontes primárias, apenas sem o bloco de análise assistida.
"""

import argparse
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Raiz primeiro (para apps.workers.*, packages.*), depois apps/api (ADR-002)
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.enrichment import (  # noqa: E402
    ArtigoResolvido,
    Citacao,
    _extract_article_text,
    _fetch_planalto,
    build_planalto_url,
    extract_citacoes,
)
from packages.camara_client import CamaraClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Mesma normalização de sync_votacoes_zil.py. Duplicada conscientemente: extrair
# para um módulo comum mexeria em dois scripts em uso durante a curadoria.
VOTOS_CONTABILIZADOS = {"Sim": "sim", "Não": "nao", "Abstenção": "abstencao"}


@dataclass
class DadosVotacao:
    """Tudo que se consegue saber sobre uma votação pelas fontes primárias."""

    fonte_id: str
    descricao: str = ""
    data: str = ""
    aprovacao: Optional[int] = None
    # Proposição vinculada
    proposicao_id: Optional[str] = None
    proposicao_rotulo: str = ""
    ementa: str = ""
    ementa_detalhada: str = ""
    keywords: str = ""
    situacao: str = ""
    url_inteiro_teor: str = ""
    data_apresentacao: str = ""
    # Placar e orientações
    votos_sim: int = 0
    votos_nao: int = 0
    abstencoes: int = 0
    outros: int = 0
    orientacoes: dict[str, str] = field(default_factory=dict)

    @property
    def total_votos(self) -> int:
        return self.votos_sim + self.votos_nao + self.abstencoes + self.outros

    @property
    def margem(self) -> Optional[float]:
        """Quão disputada foi: 0.0 = empate, 1.0 = unanimidade."""
        decisivos = self.votos_sim + self.votos_nao
        if decisivos == 0:
            return None
        return abs(self.votos_sim - self.votos_nao) / decisivos

    @property
    def resultado(self) -> str:
        if self.aprovacao == 1:
            return "aprovada"
        if self.aprovacao == 0:
            return "rejeitada"
        return "indeterminado"


def coletar(client: CamaraClient, fonte_id: str) -> DadosVotacao:
    """Reúne, só da API da Câmara, tudo que compõe a parte factual do dossiê.

    Não toca no banco: o dossiê precisa funcionar antes de o ambiente estar de pé.
    """
    dados = DadosVotacao(fonte_id=fonte_id)

    logger.info("→ Buscando detalhes da votação %s...", fonte_id)
    detalhes = client.obter_votacao_detalhes(fonte_id)
    if not detalhes or not isinstance(detalhes, dict):
        raise SystemExit(f"Votação {fonte_id} não retornou dados da API da Câmara.")

    dados.descricao = detalhes.get("descricao") or ""
    dados.data = detalhes.get("dataHoraRegistro") or detalhes.get("data") or ""
    dados.aprovacao = detalhes.get("aprovacao")

    # A proposição principal nem sempre vem; cair para a primeira afetada é o
    # mesmo critério que sync_votacoes_zil.py usa.
    prop = detalhes.get("proposicaoPrincipal")
    if not prop:
        afetadas = detalhes.get("proposicoesAfetadas") or []
        prop = afetadas[0] if afetadas else None

    if prop:
        dados.proposicao_id = str(prop.get("id", "")) or None
        tipo = prop.get("siglaTipo") or prop.get("tipo") or ""
        dados.proposicao_rotulo = f"{tipo} {prop.get('numero', '')}/{prop.get('ano', '')}".strip()
        dados.ementa = prop.get("ementa") or prop.get("titulo") or ""

        if dados.proposicao_id:
            logger.info("→ Buscando proposição %s...", dados.proposicao_id)
            try:
                detalhe_prop = client.obter_proposicao(int(dados.proposicao_id))
                dados.ementa = detalhe_prop.get("ementa") or dados.ementa
                dados.ementa_detalhada = detalhe_prop.get("ementaDetalhada") or ""
                dados.keywords = detalhe_prop.get("keywords") or ""
                dados.url_inteiro_teor = detalhe_prop.get("urlInteiroTeor") or ""
                dados.data_apresentacao = detalhe_prop.get("dataApresentacao") or ""
                status = detalhe_prop.get("statusProposicao") or {}
                dados.situacao = status.get("descricaoSituacao") or ""
            except Exception as e:  # noqa: BLE001 — o dossiê continua útil sem isto
                logger.warning("  proposição indisponível: %s", e)

    logger.info("→ Buscando orientações de bancada...")
    try:
        for ori in client.obter_votacao_orientacoes(fonte_id):
            partido = (ori.get("siglaPartido") or ori.get("partido") or "").upper()
            orientacao = ori.get("orientacao") or ori.get("voto") or ""
            if partido and orientacao:
                dados.orientacoes[partido] = orientacao
    except Exception as e:  # noqa: BLE001
        logger.warning("  orientações indisponíveis: %s", e)

    # O placar não vem pronto da API: é contado a partir dos votos individuais.
    logger.info("→ Contando votos individuais...")
    try:
        for v in client.obter_votos(fonte_id):
            chave = VOTOS_CONTABILIZADOS.get(v.voto)
            if chave == "sim":
                dados.votos_sim += 1
            elif chave == "nao":
                dados.votos_nao += 1
            elif chave == "abstencao":
                dados.abstencoes += 1
            else:
                dados.outros += 1
    except Exception as e:  # noqa: BLE001
        logger.warning("  votos individuais indisponíveis: %s", e)

    return dados


def resolver_leis(textos: list[str], limite: int = 8) -> list[ArtigoResolvido]:
    """Extrai leis citadas e busca o texto real do artigo no Planalto.

    Usa a cadeia sem estado do pipeline de enriquecimento — sem banco, portanto
    sem o cache de `LeiArtigo`. Para um punhado de votações o custo é aceitável.
    """
    citacoes: list[Citacao] = []
    vistas: set[str] = set()
    for texto in textos:
        if not texto:
            continue
        for c in extract_citacoes(texto):
            if c.lei_id not in vistas:
                vistas.add(c.lei_id)
                citacoes.append(c)

    if not citacoes:
        return []

    if len(citacoes) > limite:
        logger.info("  %d leis citadas; resolvendo as %d primeiras", len(citacoes), limite)
        citacoes = citacoes[:limite]

    resolvidos: list[ArtigoResolvido] = []
    for c in citacoes:
        url = build_planalto_url(c.tipo, c.numero, c.ano)
        logger.info("→ Planalto: %s", c.lei_id)
        html, status = _fetch_planalto(url)
        texto_artigo = None
        # Tenta extrair mesmo com status "revogada": esse status vem de um regex
        # sobre o HTML inteiro, e leis grandes têm dezenas de artigos revogados
        # individualmente (a Lei 12.546/2011 tem 182 ocorrências de "REVOGAD").
        # Como marca do documento, é falso positivo quase sempre.
        if html and c.artigo:
            texto_artigo = _extract_article_text(html, c.artigo)
            # Extração curta demais é ruído, não informação: pior que nada,
            # porque dá a impressão de que o artigo foi recuperado.
            if texto_artigo and len(texto_artigo.strip()) < 40:
                texto_artigo = None
        resolvidos.append(
            ArtigoResolvido(
                lei_id=c.lei_id,
                numero_artigo=c.artigo or "—",
                texto=texto_artigo,
                url=url,
                status=status,
            )
        )
    return resolvidos


_SYSTEM_ANALISE = (
    "Você assessora um observatório legislativo apartidário que avalia votações "
    "do Congresso brasileiro sob a ótica da soberania industrial: produção "
    "nacional de insumos críticos, processamento local de minerais estratégicos, "
    "capacidade industrial e tecnológica, e redução de dependência externa.\n\n"
    "Use APENAS o contexto fornecido. Nunca use conhecimento externo sobre a "
    "proposição. Se o contexto for insuficiente para uma conclusão, diga isso "
    "explicitamente — é a resposta certa com mais frequência do que parece.\n\n"
    "Você NÃO decide. Um humano decide. Seu papel é expor o argumento dos dois "
    "lados com honestidade, incluindo o melhor argumento contra a leitura que "
    "você considera mais provável."
)


def analisar(dados: DadosVotacao, artigos: list[ArtigoResolvido], modelo: str) -> Optional[str]:
    """Bloco de análise assistida. Devolve None se não for possível gerar.

    Deliberadamente devolve TEXTO, não uma direção estruturada: um campo
    `direcao: "sim"` vindo de máquina convidaria a copiar sem ler.
    """
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic não instalado — dossiê sai sem o bloco de análise")
        return None

    from core.config import settings

    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY vazia — dossiê sai sem o bloco de análise")
        return None

    contexto = [
        f"VOTAÇÃO: {dados.descricao}",
        f"RESULTADO: {dados.resultado} ({dados.votos_sim} sim / {dados.votos_nao} não)",
        f"PROPOSIÇÃO: {dados.proposicao_rotulo}",
        f"EMENTA: {dados.ementa}",
    ]
    if dados.ementa_detalhada:
        contexto.append(f"EMENTA DETALHADA: {dados.ementa_detalhada}")
    for a in artigos:
        if a.texto:
            contexto.append(f"TEXTO DE {a.lei_id} art. {a.numero_artigo}:\n{a.texto}")

    pergunta = (
        "Com base apenas no contexto acima, responda em português, em prosa, "
        "sem JSON e sem markdown de cabeçalho:\n\n"
        "1. O que esta proposição faz, concretamente?\n"
        "2. Qual o argumento de que votar SIM favorece a soberania industrial?\n"
        "3. Qual o melhor argumento de que votar SIM a prejudica, ou de que a "
        "matéria é neutra sob essa ótica?\n"
        "4. O contexto é suficiente para uma conclusão, ou falta informação "
        "essencial? Se falta, diga o quê."
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        msg = client.messages.create(
            model=modelo,
            max_tokens=1_500,
            system=_SYSTEM_ANALISE,
            messages=[{"role": "user", "content": "\n\n".join(contexto) + "\n\n" + pergunta}],
        )
        return msg.content[0].text.strip()
    except Exception as e:  # noqa: BLE001
        logger.warning("análise assistida falhou: %s", e)
        return None


def _peso_sugerido(descricao: str) -> tuple[float, str]:
    """Sugere peso a partir da descrição, seguindo a tabela do PRD §10."""
    d = descricao.lower()
    if "requerimento" in d:
        return 0.5, "requerimento processual"
    if "comissão" in d or "comissao" in d:
        return 2.0, "votação em comissão"
    if any(t in d for t in ("subemenda", "substitutivo", "redação final", "emendas do senado")):
        return 3.0, "votação final em plenário"
    return 1.0, "não foi possível inferir — confira e ajuste"


def renderizar(
    dados: DadosVotacao,
    artigos: list[ArtigoResolvido],
    analise: Optional[str],
) -> str:
    """Monta o dossiê em markdown.

    Ordem deliberada: fontes primárias primeiro, análise assistida por último e
    rotulada. O PRD-PAINEL §12 registra a ancoragem como risco real — ler uma
    conclusão pronta antes das fontes contamina o julgamento que o dossiê existe
    para apoiar.
    """
    L: list[str] = []
    a = L.append

    a(f"# Dossiê — votação {dados.fonte_id}")
    a("")
    a(f"*Gerado em {datetime.now():%Y-%m-%d %H:%M} por `scripts/dossie.py`. "
      "Fontes primárias: API de Dados Abertos da Câmara e Planalto.*")
    a("")
    a("---")
    a("")

    a("## 1. A votação")
    a("")
    a(f"- **Descrição:** {dados.descricao or '—'}")
    a(f"- **Data:** {dados.data or '—'}")
    a(f"- **Resultado:** {dados.resultado}")
    if dados.total_votos:
        margem = f"{dados.margem:.0%}" if dados.margem is not None else "—"
        a(f"- **Placar:** {dados.votos_sim} sim · {dados.votos_nao} não · "
          f"{dados.abstencoes} abstenção · {dados.outros} outros "
          f"(total {dados.total_votos})")
        a(f"- **Margem:** {margem} — 0% seria empate, 100% unanimidade")
    else:
        a("- **Placar:** votos individuais não retornados pela API")
    a("")

    a("## 2. A proposição")
    a("")
    if dados.proposicao_rotulo:
        a(f"- **Identificação:** {dados.proposicao_rotulo} "
          f"(id `{dados.proposicao_id}`)")
    if dados.data_apresentacao:
        a(f"- **Apresentada em:** {dados.data_apresentacao}")
    if dados.situacao:
        a(f"- **Situação:** {dados.situacao}")
    if dados.keywords:
        a(f"- **Palavras-chave (Câmara):** {dados.keywords}")
    if dados.url_inteiro_teor:
        a(f"- **Inteiro teor:** {dados.url_inteiro_teor}")
    a("")
    a("**Ementa:**")
    a("")
    a(f"> {dados.ementa or '—'}")
    a("")
    if dados.ementa_detalhada:
        a("**Ementa detalhada:**")
        a("")
        a(f"> {dados.ementa_detalhada}")
        a("")

    a("## 3. Orientações de bancada")
    a("")
    if dados.orientacoes:
        a("| Partido | Orientação |")
        a("|---|---|")
        for partido, ori in sorted(dados.orientacoes.items()):
            a(f"| {partido} | {ori} |")
    else:
        a("*Não disponíveis para esta votação.*")
    a("")

    a("## 4. Leis citadas")
    a("")
    if not artigos:
        a("*Nenhuma citação de lei encontrada na ementa.*")
    for art in artigos:
        a(f"### {art.lei_id} — art. {art.numero_artigo}")
        a("")
        a(f"- **Fonte:** {art.url}")
        if art.status == "nao_encontrada":
            a("- **Atenção:** o Planalto devolveu 404 para esta URL. O padrão de "
              "URL de algumas leis foge do que o projeto monta — procure a lei "
              "manualmente.")
        elif art.status == "revogada":
            a("- **Atenção:** o documento contém marcas de revogação, mas isso é "
              "detectado por regex no HTML inteiro e costuma ser falso positivo "
              "em leis grandes (artigos revogados individualmente). **Não conclua "
              "que a lei está revogada sem conferir.**")
        a("")
        if art.texto:
            a("```")
            a(art.texto)
            a("```")
        else:
            a("*Texto do artigo não recuperado — a extração do HTML do Planalto é "
              "frágil. Abra a fonte acima e leia o artigo direto.*")
        a("")

    peso, motivo_peso = _peso_sugerido(dados.descricao)

    a("## 5. Sua decisão")
    a("")
    a("As perguntas que a classificação precisa responder:")
    a("")
    a("1. Esta matéria afeta a soberania industrial? Se não, **não classifique** — "
      "o princípio do projeto é *na dúvida, não classificar*.")
    a("2. Votar **SIM** aqui favorece ou prejudica a soberania industrial?")
    a("3. Qual o peso? Sugestão: **{:.1f}** ({}).".format(peso, motivo_peso))
    a("")
    if dados.resultado == "rejeitada":
        a("> ⚠️ **Esta votação foi rejeitada.** Vale atenção: as 7 classificações "
          "existentes são todas `direcao: sim`, o que faz o placar medir mais "
          "presença e disciplina partidária do que alinhamento ZIL. Votações em "
          "que a posição pró-soberania é votar **não** corrigem esse desequilíbrio.")
        a("")

    a("### YAML para colar em `data/direcoes/[ano].yml`")
    a("")
    a("O campo `direcao` está ausente **de propósito** — é a sua decisão.")
    a("")
    a("```yaml")
    a(f'  - fonte_id: "{dados.fonte_id}"')
    a("    fonte: camara")
    a("    direcao:            # sim | nao  ← preencher")
    a(f"    peso: {peso}")
    a("    validacao: nao-validado")
    a("    categoria_principal: ZIL-???   # ← preencher")
    a("    justificativa: >")
    a(f"      {dados.proposicao_rotulo or 'Proposição'} — {(dados.ementa or '')[:110]}...")
    a("      [Por que votar SIM é pró ou contra soberania: escreva aqui.]")
    a("```")
    a("")

    a("## 6. Análise assistida")
    a("")
    if analise:
        a("> ⚠️ **Gerado por modelo de linguagem, a partir apenas do contexto acima.**")
        a("> Não é decisão nem recomendação: está no fim do documento de propósito, "
          "para que você forme juízo pelas fontes primárias antes de lê-lo.")
        a("")
        a(analise)
    else:
        a("*Não gerada.* Requer `ANTHROPIC_API_KEY` no `.env` e o pacote `anthropic`. "
          "O dossiê acima é completo sem ela — as fontes primárias são o essencial.")
    a("")

    return "\n".join(L)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--votacao", required=True,
                        help="fonte_id da votação na Câmara (ex: 2454704-53)")
    parser.add_argument("--out", type=Path,
                        help="diretório onde gravar o .md (padrão: imprime na tela)")
    parser.add_argument("--sem-llm", action="store_true",
                        help="pula o bloco de análise assistida")
    parser.add_argument("--modelo", default=None,
                        help="modelo para a análise (padrão: settings.ENRICHMENT_MODEL)")
    args = parser.parse_args()

    modelo = args.modelo
    if modelo is None:
        try:
            from core.config import settings
            modelo = settings.ENRICHMENT_MODEL
        except Exception:  # noqa: BLE001 — sem config, só desliga o bloco de análise
            modelo = ""

    with CamaraClient() as client:
        dados = coletar(client, args.votacao)

    artigos = resolver_leis([dados.ementa, dados.ementa_detalhada])

    analise = None
    if not args.sem_llm and modelo:
        analise = analisar(dados, artigos, modelo)

    texto = renderizar(dados, artigos, analise)

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        destino = args.out / f"{args.votacao}.md"
        destino.write_text(texto, encoding="utf-8")
        print(f"\n✓ Dossiê gravado em {destino}")
    else:
        print("\n" + texto)


if __name__ == "__main__":
    main()

"""Lista votações candidatas a entrar no placar, ranqueadas por saliência.

O placar focado (ADR-004) vive de escolher ~10 votações que realmente importem.
Este script varre um ano na API da Câmara, filtra as que tocam pautas ZIL e
ordena pelas que mais diferenciam parlamentares.

**Por que não parte do banco:** depois do `seed.py` o banco contém apenas as
votações já curadas — zero candidatas. Ler direto da API funciona sem nenhum
setup, que é o mesmo princípio do `dossie.py`.

**Como o placar é obtido sem uma chamada por votação:** a descrição que a Câmara
devolve costuma trazer o resultado inline ("Sim: 253; Não: 67; Abstenção: 4"),
o que permite ranquear o ano inteiro com uma varredura só.

Uso (da raiz do repositório):

    python scripts/candidatas.py --ano 2025
    python scripts/candidatas.py --ano 2025 --limite 15
    python scripts/candidatas.py --ano 2025 --so-rejeitadas
"""

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.classifiers import (  # noqa: E402
    KEYWORDS_FRACAS,
    classificar_texto_com_evidencia,
    sem_citacoes_de_lei,
)
from packages.camara_client import CamaraClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# "Sim: 253; não: 67; abstenção: 4" — a Câmara embute o placar na descrição.
_PLACAR_RE = re.compile(
    r"sim\s*:\s*(\d+)\s*;\s*n[ãa]o\s*:\s*(\d+)(?:\s*;\s*absten[çc][ãa]o\s*:\s*(\d+))?",
    re.IGNORECASE,
)

# Pistas textuais de votação final em plenário — não há campo que distinga
# plenário de comissão, e `peso` só existe depois da curadoria.
_PISTAS_PLENARIO = (
    "subemenda", "substitutivo", "redação final", "redacao final",
    "emendas do senado", "em globo", "projeto de lei",
)
# Urgência x requerimento genérico: a diferença é se dá para saber o que foi
# votado. "Aprovado o Requerimento de Urgência" nomeia o objeto — quem votou sim
# quis pautar AQUELE projeto, e isso é preferência revelada. Já "Rejeitado o
# Requerimento" não diz qual: o campo `objetosPossiveis` da API devolve dezenas
# de candidatos (81 numa votação da PONTE), sem apontar o votado. Sem saber o
# que se rejeitou, a direção é chute.
# A ordem importa: urgência é avaliada primeiro, porque a descrição dela também
# contém "requerimento".
_PISTAS_URGENCIA = ("urgência", "urgencia")
_PISTAS_PROCESSUAL = ("requerimento", "adiamento", "quebra de")

# A lista de keywords fracas e a regra da lei citada moram na taxonomia e no
# classificador — ver o cabeçalho de data/taxonomia/categorias.yml. Aqui elas
# são apenas consumidas: manter uma segunda cópia garantiria que as duas
# divergissem na primeira vez que uma fosse corrigida sozinha.


def _e_fraca(codigo: str, keyword: str) -> bool:
    return keyword.lower() in KEYWORDS_FRACAS.get(codigo, frozenset())

# Voto sobre EMENDA ou DESTAQUE não é classificável a partir da ementa do projeto:
# "sim" significa aprovar a emenda, e o que a emenda dizia não vem na API. Já o
# voto sobre o texto inteiro tem direção inequívoca — "sim" = aprovar o projeto,
# e a ementa explica o projeto. Esta distinção vale mais que a margem: uma
# votação disputadíssima que não dá para classificar não serve ao placar.
# Cuidado com a ordem: "Subemenda Substitutiva Global" contém "subemenda" mas é
# o TEXTO INTEIRO — ela substitui o projeto todo. É por isso que a votação já
# curada 2454704-53 tem peso 3.0. Por isso _VOTO_DO_TEXTO é avaliado primeiro.
_VOTO_DO_TEXTO = ("aprovado o projeto", "aprovada a redação", "substitutiva global",
                  "aprovado o substitutivo", "emendas do senado")
_VOTO_DE_EMENDA = ("emenda", "destaque", "subemenda", "supressiv", "mantido o texto")


@dataclass
class Candidata:
    fonte_id: str
    descricao: str              # ementa da proposição — é o que se lê
    data: str
    categorias: list[str]
    votos_sim: Optional[int] = None
    votos_nao: Optional[int] = None
    descricao_votacao: str = ""  # "Aprovado o PL..." / "Rejeitada a Emenda..."
    # {"ZIL-MIN": ["minerais críticos"]} — a procedência da classificação.
    # Sem ela não dá para separar tema de coincidência de vocabulário.
    keywords: dict[str, list[str]] = field(default_factory=dict)
    # Keywords que sobrevivem depois de remover os nomes de lei entre
    # parênteses. `None` = não foi calculado; então nada é tratado como citação.
    keywords_substantivas: Optional[set[str]] = None

    def _e_citacao(self, keyword: str) -> bool:
        """A keyword só apareceu dentro do nome de uma lei que o projeto altera."""
        if self.keywords_substantivas is None:
            return False
        return keyword not in self.keywords_substantivas

    @property
    def keywords_citadas(self) -> list[str]:
        return sorted({kw for kws in self.keywords.values()
                       for kw in kws if self._e_citacao(kw)})

    @property
    def keywords_fortes(self) -> list[str]:
        """Keywords específicas o bastante para sustentar a inclusão sozinhas.

        Fora: as palavras comuns do português e as que só aparecem no nome de
        uma lei citada — nos dois casos o casamento é de vocabulário, não de
        tema.
        """
        return sorted({kw for codigo, kws in self.keywords.items()
                       for kw in kws
                       if not _e_fraca(codigo, kw) and not self._e_citacao(kw)})

    @property
    def keywords_casadas(self) -> list[str]:
        return sorted({kw for kws in self.keywords.values() for kw in kws})

    @property
    def so_casamento_fraco(self) -> bool:
        """Entrou na lista sem nenhum casamento que sustente o tema."""
        return bool(self.keywords_casadas) and not self.keywords_fortes

    @property
    def tem_placar(self) -> bool:
        return self.votos_sim is not None and self.votos_nao is not None

    @property
    def margem(self) -> Optional[float]:
        """0.0 = empate, 1.0 = unanimidade. Quanto menor, mais diferencia."""
        if not self.tem_placar:
            return None
        decisivos = self.votos_sim + self.votos_nao
        if decisivos == 0:
            return None
        return abs(self.votos_sim - self.votos_nao) / decisivos

    @property
    def rejeitada(self) -> bool:
        """Em votação rejeitada a posição pró-soberania costuma ser votar `não`."""
        return self.tem_placar and self.votos_nao > self.votos_sim

    @property
    def classificavel(self) -> bool:
        """Se dá para decidir a direção a partir da ementa do projeto.

        Voto sobre emenda ou destaque não dá: "sim" aprova a emenda, e o texto
        da emenda não vem na API. Sem ele, a direção é indecidível.
        """
        d = self.descricao_votacao.lower()
        if any(p in d for p in _VOTO_DO_TEXTO):
            return True  # tem precedência: substitutivo global é o texto inteiro
        return not any(p in d for p in _VOTO_DE_EMENDA)

    @property
    def escore(self) -> float:
        """Saliência: o quanto vale gastar curadoria nesta votação.

        Não mede mérito — mede se a votação é sobre pauta ZIL de verdade, se dá
        para decidir a direção, e se separa parlamentares. **Nessa ordem.**

        A ordem já foi outra. Até a varredura de 2024/2025, a nota somava só
        disputa e formato da votação, e o tema entrava como meio ponto por
        categoria. O resultado foi a Política Nacional de Minerais Críticos —
        a tese do projeto em forma de lei — em último lugar entre 12, porque
        foi quase unânime, enquanto a Tarifa Social de Água e Esgoto liderava
        por ter casado com a palavra `tarifa`. Com placar focado, o topo da
        lista precisa ser o que mais importa, não o que foi mais apertado.
        """
        s = 0.0
        if self.margem is not None:
            s += (1.0 - self.margem) * 10  # disputa

        # Tema, o termo dominante. Casar por palavra comum não é sinal fraco:
        # é sinal contrário, porque as evidências que temos de casamento fraco
        # isolado são todas falso positivo.
        if self.keywords_fortes:
            s += 8.0 + min(len(self.keywords_fortes) - 1, 3) * 0.5
        elif self.keywords_casadas:
            s -= 6.0

        d = self.descricao_votacao.lower()
        # Precisa superar o termo do tema: uma votação sobre nióbio cuja
        # direção é indecidível continua sendo beco sem saída.
        if not self.classificavel:
            s -= 12.0
        if any(p in d for p in _VOTO_DO_TEXTO):
            s += 4.0
        if any(p in d for p in _PISTAS_PLENARIO):
            s += 3.0
        if any(p in d for p in _PISTAS_URGENCIA):
            s -= 1.0   # mede intenção de pautar, não posição sobre o mérito
        elif any(p in d for p in _PISTAS_PROCESSUAL):
            s -= 4.0   # objeto indeterminável — ver o comentário nas pistas
        return s


def extrair_placar(descricao: str) -> tuple[Optional[int], Optional[int]]:
    m = _PLACAR_RE.search(descricao or "")
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def ja_curadas(diretorio: Path) -> set[str]:
    """IDs já presentes nos YAMLs — não faz sentido oferecê-los de novo."""
    ids: set[str] = set()
    if not diretorio.exists():
        return ids
    for arquivo in diretorio.glob("*.yml"):
        conteudo = yaml.safe_load(arquivo.read_text(encoding="utf-8")) or {}
        for d in conteudo.get("direcoes") or []:
            if isinstance(d, dict) and d.get("fonte_id"):
                ids.add(str(d["fonte_id"]))
    return ids


def buscar_candidatas(client: CamaraClient, ano: int, excluir: set[str]) -> list[Candidata]:
    """Varre o ano, fica só com voto nominal, e classifica pela EMENTA.

    Duas decisões que vêm de medir o dado real:

    1. **Só votação com voto nominal.** Em 2024 a Câmara registrou 10.343
       votações, das quais apenas 282 têm placar individual. As outras são
       requerimentos aprovados por acordo — sem voto por parlamentar, não há o
       que pontuar num placar, qualquer que seja o tema.

    2. **Classificar pela ementa da proposição, não pela descrição da votação.**
       Das 282 com voto nominal em 2024, **zero** casam keyword ZIL pela
       descrição: elas dizem "Aprovado o Projeto de Lei nº 1.847, de 2024",
       não "fertilizantes". O tema mora na proposição.

    O filtro (1) é o que torna (2) viável: buscar a ementa de 282 votações custa
    minutos; de 10.343, seria inviável.
    """
    logger.info("→ Varrendo votações de %d...", ano)
    # A varredura de um ano inteiro são ~100 páginas (2024 teve 10.343 votações)
    # e a API da Câmara cai com alguma frequência nesse volume. Falhar com
    # traceback aqui seria inútil: quem roda precisa saber que é a API, não o
    # script, e que basta tentar de novo.
    try:
        votacoes = client.listar_votacoes(ano)
    except Exception as e:  # noqa: BLE001
        raise SystemExit(
            f"\n✗ A API da Câmara falhou durante a varredura de {ano}: "
            f"{type(e).__name__}.\n"
            "  Não é erro do script — a varredura de um ano são ~100 páginas e a\n"
            "  API costuma cair nesse volume. Tente de novo em alguns minutos.\n"
            "  Se persistir, o dossiê continua funcionando por ID:\n"
            "    python scripts/dossie.py --votacao <fonte_id>"
        ) from e
    logger.info("  %d votações no ano", len(votacoes))

    nominais = []
    for v in votacoes:
        fonte_id = str(getattr(v, "fonte_id", "") or getattr(v, "id", ""))
        descricao = getattr(v, "descricao", "") or ""
        if not fonte_id or fonte_id in excluir:
            continue
        sim, nao = extrair_placar(descricao)
        if sim is None:
            continue
        nominais.append((fonte_id, descricao, str(getattr(v, "data", "") or ""), sim, nao))

    logger.info("  %d com voto nominal — buscando a ementa de cada uma", len(nominais))

    candidatas: list[Candidata] = []
    for i, (fonte_id, descricao, data, sim, nao) in enumerate(nominais, start=1):
        if i % 25 == 0:
            logger.info("    %d/%d...", i, len(nominais))
        try:
            detalhes = client.obter_votacao_detalhes(fonte_id)
        except Exception as e:  # noqa: BLE001 — uma falha não derruba a varredura
            logger.debug("    %s indisponível: %s", fonte_id, e)
            continue
        if not isinstance(detalhes, dict):
            continue

        prop = detalhes.get("proposicaoPrincipal")
        if not prop:
            afetadas = detalhes.get("proposicoesAfetadas") or []
            prop = afetadas[0] if afetadas else None
        ementa = (prop or {}).get("ementa") or (prop or {}).get("titulo") or ""

        texto = f"{ementa} {descricao}"
        evidencia = classificar_texto_com_evidencia(texto)
        if not evidencia:
            continue

        # Segunda passada sem os nomes de lei citados: o que some aqui casou
        # com a lista de leis alteradas, não com o assunto do projeto.
        substantivas = {
            kw
            for kws in classificar_texto_com_evidencia(
                sem_citacoes_de_lei(texto)
            ).values()
            for kw in kws
        }

        candidatas.append(
            Candidata(
                fonte_id=fonte_id,
                descricao=(ementa or descricao),
                data=data,
                categorias=list(evidencia),
                votos_sim=sim,
                votos_nao=nao,
                descricao_votacao=descricao,
                keywords=evidencia,
                keywords_substantivas=substantivas,
            )
        )

    logger.info("  %d candidatas ZIL com voto nominal", len(candidatas))
    return sorted(candidatas, key=lambda c: c.escore, reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--ano", type=int, required=True)
    parser.add_argument("--limite", type=int, default=10)
    parser.add_argument("--so-rejeitadas", action="store_true",
                        help="apenas votações rejeitadas — onde a posição "
                             "pró-soberania tende a ser votar `não`")
    parser.add_argument("--direcoes", type=Path, default=Path("data/direcoes"))
    args = parser.parse_args()

    excluir = ja_curadas(args.direcoes)
    if excluir:
        logger.info("  %d votação(ões) já curada(s) serão ignoradas", len(excluir))

    with CamaraClient() as client:
        candidatas = buscar_candidatas(client, args.ano, excluir)

    if args.so_rejeitadas:
        candidatas = [c for c in candidatas if c.rejeitada]

    if not candidatas:
        print("\nNenhuma candidata encontrada com esses filtros.")
        return

    print(f"\n{len(candidatas)} candidata(s) — mostrando as {min(args.limite, len(candidatas))} "
          "mais salientes\n")

    for c in candidatas[: args.limite]:
        placar = (f"{c.votos_sim}×{c.votos_nao} (margem {c.margem:.0%})"
                  if c.tem_placar else "placar não inline")
        marcas = []
        if c.rejeitada:
            marcas.append("⚑ REJEITADA")
        if not c.classificavel:
            marcas.append("⚠ voto de emenda/destaque — direção indecidível pela ementa")
        if c.so_casamento_fraco:
            motivo = ("só casou dentro do nome de uma lei citada"
                      if c.keywords_citadas else "só casou por palavra comum")
            marcas.append(f"⚠ {motivo} — provável falso positivo")
        marca = ("  " + " · ".join(marcas)) if marcas else ""
        print(f"  {c.fonte_id}  escore {c.escore:5.1f}  {placar}{marca}")
        print(f"    {', '.join(c.categorias)} · {c.data[:10]}")
        casou = ", ".join(c.keywords_casadas) or "—"
        if c.keywords_citadas:
            casou += f"  (só em lei citada: {', '.join(c.keywords_citadas)})"
        print(f"    casou por: {casou}")
        print(f"    votação: {c.descricao_votacao[:110]}")
        print(f"    projeto: {c.descricao[:110]}")
        print(f"    → python scripts/dossie.py --votacao {c.fonte_id}")
        print()

    rejeitadas = sum(1 for c in candidatas if c.rejeitada)
    fracas = sum(1 for c in candidatas if c.so_casamento_fraco)
    print(f"Das {len(candidatas)} candidatas, {rejeitadas} foram rejeitadas "
          f"e {fracas} casaram só por palavra comum.")
    if rejeitadas:
        # Este aviso já disse que rejeitada era "a via mais natural" para
        # quebrar a variância zero. Não é: das 14 rejeitadas de 2024 e 2025,
        # 10 são "Rejeitado o Requerimento" sem dizer qual requerimento, e a
        # API não desambigua (`objetosPossiveis` devolve dezenas de candidatos).
        print("Votação rejeitada PODE gerar direção `nao` — mas só quando a\n"
              "descrição diz o que foi rejeitado. Em `Rejeitado o Requerimento`,\n"
              "sem qual, a direção é chute. Use --so-rejeitadas para separá-las.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Jobs agendados de dados, sem Celery — é o que o cron do GitHub Actions roda
contra o banco de produção (.github/workflows/dados.yml).

Reproduz o `beat_schedule` de apps/workers/tasks.py chamando as mesmas
funções, e registra cada passo em `ingestion_runs` pelo mesmo caminho que as
tasks (apps/workers/execucoes.py). Os workers Celery continuam existindo para
quem roda o docker compose; em produção, o agendador é o Actions.

Uso:
    python scripts/agenda.py diario                 # votações, Senado, proposições, scores
    python scripts/agenda.py cadastros              # deputados e senadores
    python scripts/agenda.py enriquecer --limite 30 # LLM, só as N mais recentes
    python scripts/agenda.py votacoes --ano 2026    # um passo isolado
    python scripts/agenda.py <job> --dry-run        # mostra o que faria, sem gravar

Sai com código 1 se algum passo falhar, para o Actions marcar a execução como
falha e avisar por e-mail. Os passos seguintes rodam mesmo assim: uma falha
no Senado não deve impedir o recálculo de score da Câmara.

Nunca imprime a URL do banco.
"""

import argparse
import logging
import sys
import traceback
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

# Add repo root + apps/api to sys.path (ADR-002)
_repo_root = str(Path(__file__).parent.parent)
_api_dir = str(Path(__file__).parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sqlalchemy.orm import Session  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass
class Contagem:
    """O que um passo fez, nos campos que `ingestion_runs` guarda."""

    processados: int = 0
    criados: int = 0
    atualizados: int = 0
    erros: int = 0


@dataclass
class Passo:
    tipo: str  # vai para ingestion_runs.tipo (String(30))
    executar: Callable[[Session, bool], Contagem]
    ano: int | None = None
    # Crawlers da Câmara e do Senado gravam direto, sem modo de simulação.
    # Em --dry-run eles são só anunciados.
    simula: bool = True


# ── Passos ──


def _deputados(db: Session, dry_run: bool) -> Contagem:
    from apps.workers.crawlers.camara import sync_deputados

    n = sync_deputados(db)
    return Contagem(processados=n, criados=n)


def _senadores(db: Session, dry_run: bool) -> Contagem:
    from apps.workers.crawlers.senado import sync_senadores

    n = sync_senadores(db)
    return Contagem(processados=n, criados=n)


def _votacoes(ano: int) -> Callable[[Session, bool], Contagem]:
    def executar(db: Session, dry_run: bool) -> Contagem:
        from apps.workers.crawlers.camara import sync_votacoes

        n = sync_votacoes(db, ano=ano)
        return Contagem(processados=n, criados=n)

    return executar


def _senado(ano: int) -> Callable[[Session, bool], Contagem]:
    def executar(db: Session, dry_run: bool) -> Contagem:
        from apps.workers.crawlers.senado import sync_materias

        n = sync_materias(db, ano=ano)
        return Contagem(processados=n, criados=n)

    return executar


def _proposicoes(ano_inicio: int) -> Callable[[Session, bool], Contagem]:
    """Descoberta por palavra-chave + votações de cada proposição."""

    def executar(db: Session, dry_run: bool) -> Contagem:
        from scripts.sync_pipeline import step1_discover, step2_sync_votacoes

        descoberta = step1_discover(db, ano_inicio, None, dry_run)
        votacoes = step2_sync_votacoes(db, dry_run)
        return Contagem(
            processados=descoberta.get("total_buscadas", 0) + votacoes.get("proposicoes_checadas", 0),
            criados=descoberta.get("novas", 0) + votacoes.get("votacoes_novas", 0),
            erros=descoberta.get("erros", 0) + votacoes.get("erros", 0),
        )

    return executar


def _enriquecer(limite: int | None) -> Callable[[Session, bool], Contagem]:
    def executar(db: Session, dry_run: bool) -> Contagem:
        from scripts.sync_pipeline import step3_enrich

        r = step3_enrich(db, dry_run, limite=limite)
        return Contagem(processados=r["total"], atualizados=r["enriquecidas"], erros=r["erros"])

    return executar


def _scores(db: Session, dry_run: bool) -> Contagem:
    """Aplica a curadoria de data/direcoes e recalcula o Score ZIL."""
    from scripts.sync_pipeline import step4_scores

    r = step4_scores(db, dry_run)
    return Contagem(processados=r["scores_recalculados"], atualizados=r["direcoes"]["updated"])


# ── Jobs: o que cada subcomando roda, em ordem ──


def passos_do_job(args: argparse.Namespace) -> list[Passo]:
    ano = getattr(args, "ano", None) or date.today().year
    ano_inicio = getattr(args, "ano_inicio", None) or date.today().year
    deputados = Passo("deputados", _deputados, simula=False)
    senadores = Passo("senadores", _senadores, simula=False)
    votacoes = Passo("votacoes", _votacoes(ano), ano=ano, simula=False)
    senado = Passo("votacoes_senado", _senado(ano), ano=ano, simula=False)
    proposicoes = Passo("proposicoes", _proposicoes(ano_inicio), ano=ano_inicio)
    scores = Passo("scores", _scores)

    return {
        "deputados": [deputados],
        "senadores": [senadores],
        "votacoes": [votacoes],
        "senado": [senado],
        "proposicoes": [proposicoes],
        "enriquecer": [Passo("enriquecimento", _enriquecer(getattr(args, "limite", None)))],
        "scores": [scores],
        "diario": [votacoes, senado, proposicoes, scores],
        "cadastros": [deputados, senadores],
    }[args.job]


def rodar_passo(db: Session, passo: Passo, dry_run: bool) -> bool:
    """Roda um passo e registra em `ingestion_runs`. Devolve se deu certo."""
    from apps.workers.execucoes import abrir_execucao, fechar_execucao

    rotulo = f"{passo.tipo} ({passo.ano})" if passo.ano else passo.tipo

    if dry_run and not passo.simula:
        print(f"· {rotulo}: [dry-run] gravaria direto no banco, não executado")
        return True

    run = None if dry_run else abrir_execucao(db, tipo=passo.tipo, ano=passo.ano)
    try:
        c = passo.executar(db, dry_run)
    except Exception as exc:
        db.rollback()
        traceback.print_exc()
        print(f"✗ {rotulo}: falhou — {type(exc).__name__}: {exc}")
        if run is not None:
            fechar_execucao(
                db, run, status="failed", processados=0, criados=0, atualizados=0, erros=1,
                erro_detalhes=[{"mensagem": str(exc)}],
            )
        return False

    if run is not None:
        status = "partial" if c.erros else "success"
        fechar_execucao(
            db, run, status=status, processados=c.processados, criados=c.criados,
            atualizados=c.atualizados, erros=c.erros,
        )
    marca = "⚠" if c.erros else "✓"
    print(
        f"{marca} {rotulo}: processados={c.processados} criados={c.criados} "
        f"atualizados={c.atualizados} erros={c.erros}{' [dry-run]' if dry_run else ''}"
    )
    return True


def rodar(db: Session, passos: list[Passo], dry_run: bool) -> int:
    falhas = [p.tipo for p in passos if not rodar_passo(db, p, dry_run)]
    if falhas:
        print(f"\n{len(falhas)} passo(s) falharam: {', '.join(falhas)}")
        return 1
    return 0


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Jobs agendados de dados (cron do GitHub Actions)")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que faria, sem gravar")
    sub = parser.add_subparsers(dest="job", required=True)

    sub.add_parser("diario", help="Votações e Senado do ano, proposições do ano, scores")
    sub.add_parser("cadastros", help="Deputados e senadores")
    sub.add_parser("deputados", help="Cadastro de deputados")
    sub.add_parser("senadores", help="Cadastro de senadores")
    for nome, ajuda in (("votacoes", "Votações da Câmara"), ("senado", "Matérias e votações do Senado")):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("--ano", type=int, default=None, help="Padrão: ano corrente")
    p = sub.add_parser("proposicoes", help="Descoberta de proposições + votações de cada uma")
    p.add_argument("--ano-inicio", type=int, default=None, help="Padrão: ano corrente")
    p = sub.add_parser("enriquecer", help="Enriquecimento com LLM das pendentes")
    p.add_argument("--limite", type=int, default=None, help="Só as N mais recentes")
    sub.add_parser("scores", help="Aplica data/direcoes e recalcula o Score ZIL")

    # --dry-run também depois do subcomando: `agenda.py diario --dry-run`.
    for subparser in sub.choices.values():
        subparser.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = criar_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    from core.config import SessionLocal

    passos = passos_do_job(args)
    print(f"Job {args.job}: {', '.join(p.tipo for p in passos)}{' [dry-run]' if args.dry_run else ''}")
    with SessionLocal() as db:
        return rodar(db, passos, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

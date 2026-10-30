"""Registro de execuções de ingestão (`IngestionRun`), sem depender do Celery.

As tasks Celery (`tasks.py`) e o agendador por linha de comando
(`scripts/agenda.py`, que roda no GitHub Actions) gravam cada execução do
mesmo jeito, para que `ingestion_runs` seja um só histórico, venha o sync de
onde vier.
"""

import sys
from datetime import datetime
from pathlib import Path

# Mesmo caminho curto (`models`) que os crawlers usam: uma Base só, venha a
# chamada do Celery, do cron ou dos testes.
_repo_root = str(Path(__file__).parent.parent.parent)
_api_dir = str(Path(__file__).parent.parent.parent / "apps" / "api")
for _p in (_repo_root, _api_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def abrir_execucao(db, tipo: str, ano: int | None = None):
    """Cria o registro com status `running` e o devolve."""
    from models import IngestionRun

    run = IngestionRun(tipo=tipo, ano=ano, status="running", iniciado_em=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def fechar_execucao(
    db,
    run,
    *,
    status: str,
    processados: int,
    criados: int,
    atualizados: int,
    erros: int,
    erro_detalhes: list | None = None,
) -> None:
    run.status = status
    run.finalizado_em = datetime.utcnow()
    run.registros_processados = processados
    run.registros_criados = criados
    run.registros_atualizados = atualizados
    run.erros_count = erros
    if erro_detalhes:
        run.erro_detalhes = erro_detalhes
    db.commit()

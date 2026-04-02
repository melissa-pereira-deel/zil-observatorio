"""Celery tasks for ZIL Observatório.

Scheduled tasks for data ingestion, classification, and scoring.
"""

import logging
import sys
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

sys.path.insert(0, "/app")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

app = Celery("zil_workers")
app.config_from_object({
    "broker_url": "redis://redis:6379/0",
    "result_backend": "redis://redis:6379/0",
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "America/Sao_Paulo",
    "enable_utc": True,
})

# Schedule (FR-008)
app.conf.beat_schedule = {
    # Deputados — toda segunda-feira às 03:00
    "sync-deputados-semanal": {
        "task": "workers.tasks.task_sync_deputados",
        "schedule": crontab(hour=3, minute=0, day_of_week=1),
    },
    # Votações — a cada 6 horas (FR-008)
    "sync-votacoes-6h": {
        "task": "workers.tasks.task_sync_votacoes",
        "schedule": crontab(hour="*/6", minute=15),
    },
    # Recalcular scores — diário às 04:00 (após a ingestão das 00:15)
    "recalc-scores-diario": {
        "task": "workers.tasks.task_recalcular_scores",
        "schedule": crontab(hour=4, minute=0),
    },
}


def _get_db():
    """Create a database session for tasks."""
    from apps.api.core.config import SessionLocal
    return SessionLocal()


def _open_ingestion_run(db, tipo: str, ano: int | None = None):
    """Create an IngestionRun record and return it."""
    from apps.api.models import IngestionRun
    run = IngestionRun(
        tipo=tipo,
        ano=ano,
        status="running",
        iniciado_em=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _close_ingestion_run(db, run, *, status: str, processados: int, criados: int, atualizados: int, erros: int, erro_detalhes: list | None = None) -> None:
    run.status = status
    run.finalizado_em = datetime.utcnow()
    run.registros_processados = processados
    run.registros_criados = criados
    run.registros_atualizados = atualizados
    run.erros_count = erros
    if erro_detalhes:
        run.erro_detalhes = erro_detalhes
    db.commit()


@app.task(
    name="workers.tasks.task_sync_deputados",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,  # 10 min máx
    retry_jitter=False,
)
def task_sync_deputados(self):
    """Sincroniza deputados da Câmara (FR-001)."""
    logger.info("Task: task_sync_deputados iniciada")
    db = _get_db()
    run = _open_ingestion_run(db, tipo="deputados")
    try:
        from apps.workers.crawlers.camara import sync_deputados
        count = sync_deputados(db)
        _close_ingestion_run(db, run, status="success", processados=count, criados=count, atualizados=0, erros=0)
        logger.info(f"Task: task_sync_deputados concluída — {count} deputados")
        return {"status": "ok", "novos": count}
    except Exception as exc:
        logger.error(f"Task: task_sync_deputados falhou: {exc}")
        _close_ingestion_run(db, run, status="failed", processados=0, criados=0, atualizados=0, erros=1,
                             erro_detalhes=[{"mensagem": str(exc), "tentativa": self.request.retries + 1}])
        raise
    finally:
        db.close()


@app.task(
    name="workers.tasks.task_sync_votacoes",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=False,
)
def task_sync_votacoes(self, ano: int | None = None):
    """Sincroniza votações da Câmara do ano atual (FR-002, FR-008)."""
    ano = ano or datetime.now().year
    logger.info(f"Task: task_sync_votacoes ({ano}) iniciada")
    db = _get_db()
    run = _open_ingestion_run(db, tipo="votacoes", ano=ano)
    try:
        from apps.workers.crawlers.camara import sync_votacoes
        count = sync_votacoes(db, ano=ano)
        _close_ingestion_run(db, run, status="success", processados=count, criados=count, atualizados=0, erros=0)
        logger.info(f"Task: task_sync_votacoes ({ano}) concluída — {count} votações")
        return {"status": "ok", "ano": ano, "novas_votacoes": count}
    except Exception as exc:
        logger.error(f"Task: task_sync_votacoes ({ano}) falhou: {exc}")
        _close_ingestion_run(db, run, status="failed", processados=0, criados=0, atualizados=0, erros=1,
                             erro_detalhes=[{"ano": ano, "mensagem": str(exc), "tentativa": self.request.retries + 1}])
        raise
    finally:
        db.close()


@app.task(
    name="workers.tasks.task_recalcular_scores",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=False,
)
def task_recalcular_scores(self):
    """Recalcula o Score ZIL de todos os parlamentares (FR-005)."""
    logger.info("Task: task_recalcular_scores iniciada")
    db = _get_db()
    try:
        from apps.workers.scoring import recalcular_todos_scores
        count = recalcular_todos_scores(db)
        logger.info(f"Task: task_recalcular_scores concluída — {count} scores")
        return {"status": "ok", "scores_atualizados": count}
    except Exception as exc:
        logger.error(f"Task: task_recalcular_scores falhou: {exc}")
        raise
    finally:
        db.close()

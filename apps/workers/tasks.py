"""Celery tasks for ZIL Observatório.

Scheduled tasks for data ingestion, classification, and scoring.
"""

import logging
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

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

# Schedule
app.conf.beat_schedule = {
    # Deputados — uma vez por semana (domingo 3h)
    "sync-deputados-semanal": {
        "task": "workers.tasks.task_sync_deputados",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
    # Votações — a cada 6 horas
    "sync-votacoes-6h": {
        "task": "workers.tasks.task_sync_votacoes",
        "schedule": crontab(hour="*/6", minute=15),
    },
    # Recalcular scores — diário (4h)
    "recalc-scores-diario": {
        "task": "workers.tasks.task_recalcular_scores",
        "schedule": crontab(hour=4, minute=0),
    },
}


def _get_db():
    """Create a database session for tasks."""
    import sys
    sys.path.insert(0, "/app")
    from core.config import SessionLocal
    return SessionLocal()


@app.task(name="workers.tasks.task_sync_deputados")
def task_sync_deputados():
    """Sincroniza deputados da Câmara."""
    logger.info("Task: sync_deputados iniciada")
    db = _get_db()
    try:
        from workers.crawlers.camara import sync_deputados
        count = sync_deputados(db)
        return {"status": "ok", "novos": count}
    except Exception as e:
        logger.error(f"Erro ao sincronizar deputados: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@app.task(name="workers.tasks.task_sync_votacoes")
def task_sync_votacoes(ano: int | None = None):
    """Sincroniza votações da Câmara do ano atual."""
    ano = ano or datetime.now().year
    logger.info(f"Task: sync_votacoes ({ano}) iniciada")
    db = _get_db()
    try:
        from workers.crawlers.camara import sync_votacoes
        count = sync_votacoes(db, ano=ano)
        return {"status": "ok", "ano": ano, "novas_votacoes": count}
    except Exception as e:
        logger.error(f"Erro ao sincronizar votações: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@app.task(name="workers.tasks.task_recalcular_scores")
def task_recalcular_scores():
    """Recalcula o Score ZIL de todos os parlamentares."""
    logger.info("Task: recalcular_scores iniciada")
    db = _get_db()
    try:
        from workers.scoring import recalcular_todos_scores
        count = recalcular_todos_scores(db)
        return {"status": "ok", "scores_atualizados": count}
    except Exception as e:
        logger.error(f"Erro ao recalcular scores: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()

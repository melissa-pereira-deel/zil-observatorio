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
    # Senadores — toda segunda-feira às 03:30 (logo após deputados)
    "sync-senadores-semanal": {
        "task": "workers.tasks.task_sync_senadores",
        "schedule": crontab(hour=3, minute=30, day_of_week=1),
    },
    # Votações Senado — a cada 6 horas
    "sync-votacoes-senado-6h": {
        "task": "workers.tasks.task_sync_votacoes_senado",
        "schedule": crontab(hour="*/6", minute=30),
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


# O registro de execuções vive em execucoes.py, compartilhado com
# scripts/agenda.py (o cron do GitHub Actions). Os nomes antigos ficam como
# apelidos para as tasks abaixo.
from apps.workers.execucoes import abrir_execucao as _open_ingestion_run  # noqa: E402
from apps.workers.execucoes import fechar_execucao as _close_ingestion_run  # noqa: E402


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
    name="workers.tasks.task_sync_senadores",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=False,
)
def task_sync_senadores(self):
    """Sincroniza senadores do Senado Federal."""
    logger.info("Task: task_sync_senadores iniciada")
    db = _get_db()
    run = _open_ingestion_run(db, tipo="senadores")
    try:
        from apps.workers.crawlers.senado import sync_senadores
        count = sync_senadores(db)
        _close_ingestion_run(db, run, status="success", processados=count, criados=count, atualizados=0, erros=0)
        logger.info(f"Task: task_sync_senadores concluída — {count} senadores")
        return {"status": "ok", "novos": count}
    except Exception as exc:
        logger.error(f"Task: task_sync_senadores falhou: {exc}")
        _close_ingestion_run(db, run, status="failed", processados=0, criados=0, atualizados=0, erros=1,
                             erro_detalhes=[{"mensagem": str(exc), "tentativa": self.request.retries + 1}])
        raise
    finally:
        db.close()


@app.task(
    name="workers.tasks.task_sync_votacoes_senado",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=False,
)
def task_sync_votacoes_senado(self, ano: int | None = None):
    """Sincroniza matérias e votações do Senado do ano atual."""
    ano = ano or datetime.now().year
    logger.info(f"Task: task_sync_votacoes_senado ({ano}) iniciada")
    db = _get_db()
    run = _open_ingestion_run(db, tipo="votacoes_senado", ano=ano)
    try:
        from apps.workers.crawlers.senado import sync_materias
        count = sync_materias(db, ano=ano)
        _close_ingestion_run(db, run, status="success", processados=count, criados=count, atualizados=0, erros=0)
        logger.info(f"Task: task_sync_votacoes_senado ({ano}) concluída — {count} matérias")
        return {"status": "ok", "ano": ano, "novas_materias": count}
    except Exception as exc:
        logger.error(f"Task: task_sync_votacoes_senado ({ano}) falhou: {exc}")
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


@app.task(
    name="workers.tasks.task_enriquecer_proposicao",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=270,
    retry_jitter=False,
)
def task_enriquecer_proposicao(self, proposicao_id: str, force: bool = False):
    """
    Enrich a proposição with LLM-generated context (Feature 002, FR-008).
    Retries with backoff: 30s → 90s → 270s.
    """
    logger.info(f"Task: task_enriquecer_proposicao proposicao={proposicao_id} force={force}")
    db = _get_db()
    try:
        from uuid import UUID
        from apps.workers.enrichment import enriquecer_proposicao
        result = enriquecer_proposicao(UUID(proposicao_id), db, force=force)
        logger.info(f"Task: task_enriquecer_proposicao done — {result}")
        return result
    except Exception as exc:
        logger.error(f"Task: task_enriquecer_proposicao falhou proposicao={proposicao_id}: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@app.task(
    name="workers.tasks.task_enriquecer_pendentes",
    bind=True,
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=False,
)
def task_enriquecer_pendentes(self):
    """
    Enqueue enrichment for all proposicoes with categorias_zil but no enrichment yet.
    Runs hourly via beat schedule. Dispatches individual tasks per proposição.
    """
    from sqlalchemy import select
    from apps.api.models import Proposicao

    logger.info("Task: task_enriquecer_pendentes iniciada")
    db = _get_db()
    try:
        from sqlalchemy import or_
        pendentes = db.execute(
            select(Proposicao.id).where(
                Proposicao.categorias_zil.isnot(None),
                or_(
                    Proposicao.contexto_status.is_(None),
                    Proposicao.contexto_status == "pendente",
                ),
            )
        ).scalars().all()

        count = 0
        for pid in pendentes:
            task_enriquecer_proposicao.delay(str(pid), force=False)
            count += 1

        logger.info(f"Task: task_enriquecer_pendentes enqueued {count} tasks")
        return {"status": "ok", "enqueued": count}
    except Exception as exc:
        logger.error(f"Task: task_enriquecer_pendentes falhou: {exc}")
        raise
    finally:
        db.close()


# Add hourly enrichment schedule
app.conf.beat_schedule["enriquecer-pendentes-horario"] = {
    "task": "workers.tasks.task_enriquecer_pendentes",
    "schedule": 3600,  # every hour
}

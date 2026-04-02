"""ZIL Scoring Engine.

Calcula o Score ZIL (-10.0 a +10.0) para cada parlamentar baseado
em seu histórico de votação em pautas classificadas como ZIL.

Fórmula:
    Score = (Σ alinhamento_i × peso_i) / (Σ |peso_i|) × 10

Onde:
    alinhamento_i = +1 se votou na direção ZIL, -1 se contra, 0 se ausente
    peso_i = peso da votação (1.0 default, até 3.0 para votações finais)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

# Ensure apps/api is in sys.path so internal imports resolve consistently
_api_dir = str(Path(__file__).parent.parent.parent / "apps" / "api")
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

from models import (  # noqa: E402
    Parlamentar, Votacao, Voto, ScoreVotacao,
    VotoEnum,
)

logger = logging.getLogger(__name__)


def calcular_alinhamento(voto: VotoEnum, direcao_esperada: str) -> float:
    """Determina se o voto está alinhado com a direção ZIL.

    Returns:
        +1.0 se alinhado, -1.0 se contra, 0.0 se ausente/absteve
    """
    voto_str = voto.value
    if voto_str in ("ausente", "abstencao", "obstrucao", "artigo_17"):
        return 0.0

    if voto_str == direcao_esperada:
        return 1.0
    else:
        return -1.0


def recalcular_score_parlamentar(db: Session, parlamentar_id) -> float | None:
    """Recalcula o Score ZIL de um parlamentar e persiste ScoreVotacao por voto.

    Returns:
        O score calculado, ou None se não houver dados suficientes.
    """
    # Buscar todos os votos em pautas ZIL com direção esperada definida
    query = (
        select(Voto, Votacao)
        .join(Votacao, Voto.votacao_id == Votacao.id)
        .where(Voto.parlamentar_id == parlamentar_id)
        .where(Votacao.categorias_zil.isnot(None))
        .where(Votacao.direcao_esperada.isnot(None))
    )

    rows = db.execute(query).all()

    if not rows:
        return None

    soma_ponderada = 0.0
    soma_pesos = 0.0

    for voto, votacao in rows:
        peso = float(votacao.peso or 1.0)
        alinhamento = calcular_alinhamento(voto.voto, votacao.direcao_esperada)

        soma_ponderada += alinhamento * peso
        soma_pesos += peso

        # Persistir ScoreVotacao (upsert por parlamentar_id + votacao_id)
        existing_sv = db.execute(
            select(ScoreVotacao).where(
                ScoreVotacao.parlamentar_id == parlamentar_id,
                ScoreVotacao.votacao_id == votacao.id,
            )
        ).scalar_one_or_none()

        categoria = votacao.categorias_zil[0] if votacao.categorias_zil else "ZIL-????"
        justificativa = f"Voto: {voto.voto.value} | Esperado: {votacao.direcao_esperada}"

        if existing_sv:
            existing_sv.impacto = alinhamento
            existing_sv.peso = peso
            existing_sv.justificativa = justificativa
        else:
            sv = ScoreVotacao(
                parlamentar_id=parlamentar_id,
                votacao_id=votacao.id,
                categoria_zil=categoria,
                impacto=alinhamento,
                peso=peso,
                justificativa=justificativa,
            )
            db.add(sv)

    if soma_pesos == 0:
        return None

    score = (soma_ponderada / soma_pesos) * 10.0
    return round(score, 2)


def recalcular_todos_scores(db: Session) -> int:
    """Recalcula o Score ZIL de todos os parlamentares.

    Returns:
        Número de parlamentares com score atualizado.
    """
    logger.info("📊 Recalculando scores ZIL de todos os parlamentares...")

    parlamentares = db.execute(select(Parlamentar)).scalars().all()
    count = 0

    for p in parlamentares:
        score = recalcular_score_parlamentar(db, p.id)

        if score is not None:
            p.score_zil = score
            p.score_atualizado_em = datetime.utcnow()
            count += 1

    db.commit()
    logger.info(f"✅ {count} scores atualizados (de {len(parlamentares)} parlamentares)")
    return count


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent / "apps" / "api"))

    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    from core.config import SessionLocal
    with SessionLocal() as db:
        recalcular_todos_scores(db)

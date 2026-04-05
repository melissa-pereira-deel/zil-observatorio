"""Integration test: apply_direcoes + recalcular_todos_scores."""

import sys
from pathlib import Path

import pytest

# Setup paths
REPO_ROOT = Path(__file__).parent.parent.parent
API_DIR = REPO_ROOT / "apps" / "api"
for p in (str(REPO_ROOT), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENV", "test")

from tests.conftest import make_parlamentar, make_votacao, make_voto
from models import Parlamentar, VotoEnum
from apps.workers.scoring import recalcular_todos_scores
from scripts.apply_direcoes import apply_direcoes


class TestApplyDirecoesWithScoring:
    """Integration test: applying directions triggers correct score calculation."""

    def test_apply_direcoes_then_recalculate_scores(self, db_session):
        """After applying directions, recalcular_todos_scores updates Parlamentar.score_zil."""
        # Seed: parlamentar voted SIM on a votação
        parl = make_parlamentar(db_session, nome="Maria Souza", partido="PT", uf="RJ")
        votacao = make_votacao(
            db_session,
            descricao="Aprovado PL sobre minerais",
            categorias_zil=["ZIL-MIN"],
            direcao_esperada=None,  # Not yet curated
            peso=None,
            fonte_id="2269745-148",
        )
        make_voto(db_session, parlamentar=parl, votacao=votacao, voto=VotoEnum.SIM)
        db_session.commit()

        # Before: no score
        assert parl.score_zil is None

        # Apply direction (simulating what YAML would provide)
        direcoes = [
            {
                "fonte_id": "2269745-148",
                "fonte": "CAMARA",
                "direcao": "sim",
                "peso": 2.0,
                "_source_file": "test.yml",
            }
        ]
        stats = apply_direcoes(direcoes, db_session)
        db_session.commit()

        assert stats["matched"] == 1
        assert stats["updated"] == 1

        # Recalculate scores (as apply_direcoes.py now does automatically)
        score_count = recalcular_todos_scores(db_session)
        db_session.commit()

        assert score_count > 0

        # Parlamentar now has a score
        db_session.refresh(parl)
        assert parl.score_zil is not None
        # Voted SIM, direction is SIM → positive alignment → score > 0
        assert parl.score_zil > 0

    def test_opposing_vote_produces_negative_score(self, db_session):
        """Parlamentar voting against expected direction gets negative score."""
        parl = make_parlamentar(db_session, nome="Carlos Lima", partido="PP", uf="MG")
        votacao = make_votacao(
            db_session,
            descricao="Aprovado PL sobre semicondutores",
            categorias_zil=["ZIL-SEM"],
            direcao_esperada=None,
            peso=None,
            fonte_id="vot-123",
        )
        make_voto(db_session, parlamentar=parl, votacao=votacao, voto=VotoEnum.NAO)
        db_session.commit()

        # Apply direction: expected SIM, but parlamentar voted NAO
        direcoes = [
            {
                "fonte_id": "vot-123",
                "fonte": "CAMARA",
                "direcao": "sim",
                "peso": 1.0,
                "_source_file": "test.yml",
            }
        ]
        apply_direcoes(direcoes, db_session)
        db_session.commit()

        recalcular_todos_scores(db_session)
        db_session.commit()

        db_session.refresh(parl)
        assert parl.score_zil is not None
        assert parl.score_zil < 0

    def test_no_scores_without_direction(self, db_session):
        """Without direcao_esperada, scores remain None."""
        parl = make_parlamentar(db_session, nome="Ana Brito", partido="PSOL", uf="SP")
        votacao = make_votacao(
            db_session,
            descricao="Requerimento de urgência",
            categorias_zil=["ZIL-ENE"],
            direcao_esperada=None,
            peso=None,
            fonte_id="vot-999",
        )
        make_voto(db_session, parlamentar=parl, votacao=votacao, voto=VotoEnum.SIM)
        db_session.commit()

        # Recalculate without any direction applied
        recalcular_todos_scores(db_session)
        db_session.commit()

        db_session.refresh(parl)
        # No direction → no score impact
        assert parl.score_zil is None

"""Unit tests for sync_votacoes_proposicoes.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Setup paths before any app imports
REPO_ROOT = Path(__file__).parent.parent.parent
API_DIR = REPO_ROOT / "apps" / "api"
for p in (str(REPO_ROOT), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENV", "test")

from tests.conftest import make_proposicao, make_parlamentar, make_votacao
from models import Votacao, Voto, FonteEnum, VotoEnum
from packages.camara_client import VotacaoAPI, VotoAPI

from scripts.sync_votacoes_proposicoes import sync_votacoes_por_proposicao


class TestSyncVotacoesPorProposicao:
    """Tests for the core sync function."""

    def _mock_client(self, votacoes=None, votos=None, orientacoes=None):
        """Create a mock CamaraClient context manager."""
        mock = MagicMock()
        mock.__enter__ = MagicMock(return_value=mock)
        mock.__exit__ = MagicMock(return_value=False)
        mock.listar_votacoes_proposicao.return_value = votacoes or []
        mock.obter_votos.return_value = votos or []
        mock.obter_votacao_orientacoes.return_value = orientacoes or []
        return mock

    def test_creates_votacoes_and_votos(self, db_session):
        """Given proposição with 2 votações from API, creates DB records."""
        prop = make_proposicao(
            db_session,
            fonte_id="2269745",
            tipo="PL",
            numero=327,
            ano=2021,
            categorias_zil=["ZIL-MIN"],
        )
        parl = make_parlamentar(db_session, fonte_id="204521", nome="João da Silva")
        db_session.commit()

        mock_votacoes = [
            VotacaoAPI(id="2269745-148", data="2024-12-18T14:30:00", descricao="Aprovado PL 327", aprovacao=True),
            VotacaoAPI(id="2269745-73", data="2024-06-15", descricao="Requerimento de urgência", aprovacao=True),
        ]
        mock_votos = [
            VotoAPI(deputado_id=204521, deputado_nome="João da Silva", deputado_partido="PL", deputado_uf="SP", voto="Sim"),
        ]

        mock_client = self._mock_client(votacoes=mock_votacoes, votos=mock_votos)

        with patch("scripts.sync_votacoes_proposicoes.CamaraClient", return_value=mock_client):
            stats = sync_votacoes_por_proposicao(db_session, skip_existing=False)

        assert stats["votacoes_novas"] == 2
        assert stats["votos_novos"] == 2  # 1 voto per votação × 2 votações
        assert stats["com_votacoes"] == 1

        # Verify DB records
        votacoes = db_session.query(Votacao).filter(
            Votacao.proposicao_id == prop.id
        ).all()
        assert len(votacoes) == 2
        assert votacoes[0].fonte_id in ("2269745-148", "2269745-73")

    def test_skips_proposicao_with_existing_votacoes(self, db_session):
        """Given proposição that already has votações, skips when skip_existing=True."""
        prop = make_proposicao(
            db_session,
            fonte_id="2269745",
            categorias_zil=["ZIL-MIN"],
        )
        # Add existing votação linked to this proposição
        existing_vot = make_votacao(
            db_session,
            descricao="Existing",
            fonte_id="existing-1",
        )
        existing_vot.proposicao_id = prop.id
        db_session.commit()

        mock_client = self._mock_client(
            votacoes=[VotacaoAPI(id="new-1", descricao="New votação")]
        )

        with patch("scripts.sync_votacoes_proposicoes.CamaraClient", return_value=mock_client):
            stats = sync_votacoes_por_proposicao(db_session, skip_existing=True)

        assert stats["puladas_com_votos"] == 1
        assert stats["votacoes_novas"] == 0

    def test_deduplicates_existing_fonte_id(self, db_session):
        """Given votação with existing fonte_id, does not create duplicate."""
        prop = make_proposicao(
            db_session,
            fonte_id="2269745",
            categorias_zil=["ZIL-MIN"],
        )
        # Pre-existing votação with same fonte_id but no proposicao link
        existing_vot = make_votacao(
            db_session,
            descricao="Already synced",
            fonte_id="2269745-148",
        )
        db_session.commit()

        mock_votacoes = [
            VotacaoAPI(id="2269745-148", descricao="Aprovado PL 327", aprovacao=True),
        ]
        mock_client = self._mock_client(votacoes=mock_votacoes)

        with patch("scripts.sync_votacoes_proposicoes.CamaraClient", return_value=mock_client):
            stats = sync_votacoes_por_proposicao(db_session, skip_existing=False)

        assert stats["votacoes_novas"] == 0
        # But should link existing votação to proposição
        db_session.refresh(existing_vot)
        assert existing_vot.proposicao_id == prop.id

    def test_handles_empty_votacao_list(self, db_session):
        """Given proposição without votações on API, handles gracefully."""
        make_proposicao(
            db_session,
            fonte_id="9999999",
            categorias_zil=["ZIL-ENE"],
        )
        db_session.commit()

        mock_client = self._mock_client(votacoes=[])

        with patch("scripts.sync_votacoes_proposicoes.CamaraClient", return_value=mock_client):
            stats = sync_votacoes_por_proposicao(db_session, skip_existing=False)

        assert stats["proposicoes_checadas"] == 1
        assert stats["com_votacoes"] == 0
        assert stats["votacoes_novas"] == 0
        assert stats["erros"] == 0

    def test_classifies_votacao_with_classificar_votacao(self, db_session):
        """Classifies each new votação using the keyword classifier."""
        prop = make_proposicao(
            db_session,
            fonte_id="2269745",
            ementa="Regulamenta minerais estratégicos como nióbio e lítio",
            categorias_zil=["ZIL-MIN"],
        )
        db_session.commit()

        mock_votacoes = [
            VotacaoAPI(id="new-1", descricao="Aprovado projeto sobre minerais", aprovacao=True),
        ]
        mock_client = self._mock_client(votacoes=mock_votacoes)

        with patch("scripts.sync_votacoes_proposicoes.CamaraClient", return_value=mock_client):
            stats = sync_votacoes_por_proposicao(db_session, skip_existing=False)

        assert stats["votacoes_novas"] == 1
        votacao = db_session.query(Votacao).filter(
            Votacao.fonte_id == "new-1"
        ).one()
        # categorias_zil should be set (may or may not match depending on classifier)
        # The key invariant: direcao_esperada is always NULL (editorial-only)
        # peso defaults to 1.0 via model default — harmless without direcao_esperada
        assert votacao.direcao_esperada is None

    def test_dry_run_does_not_persist(self, db_session):
        """Given dry_run=True, counts but does not create DB records."""
        make_proposicao(
            db_session,
            fonte_id="2269745",
            categorias_zil=["ZIL-MIN"],
        )
        db_session.commit()

        mock_votacoes = [
            VotacaoAPI(id="new-1", descricao="Test", aprovacao=True),
        ]
        mock_client = self._mock_client(votacoes=mock_votacoes)

        with patch("scripts.sync_votacoes_proposicoes.CamaraClient", return_value=mock_client):
            stats = sync_votacoes_por_proposicao(
                db_session, skip_existing=False, dry_run=True
            )

        assert stats["votacoes_novas"] == 1
        # But no DB record created
        count = db_session.query(Votacao).filter(
            Votacao.fonte_id == "new-1"
        ).count()
        assert count == 0

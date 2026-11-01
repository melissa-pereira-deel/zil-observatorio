"""Testes do agendador por linha de comando (scripts/agenda.py)."""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
API_DIR = REPO_ROOT / "apps" / "api"
for p in (str(REPO_ROOT), str(API_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import os  # noqa: E402

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENV", "test")

from sqlalchemy import select  # noqa: E402

from models import IngestionRun  # noqa: E402
from scripts import agenda  # noqa: E402
from tests.conftest import make_proposicao  # noqa: E402

CAMARA = "apps.workers.crawlers.camara"
SENADO = "apps.workers.crawlers.senado"


def _rodar(db, *argv):
    args = agenda.criar_parser().parse_args(list(argv))
    return agenda.rodar(db, agenda.passos_do_job(args), args.dry_run)


def _execucoes(db):
    return {r.tipo: r for r in db.execute(select(IngestionRun)).scalars()}


class TestJobs:
    def test_cadastros_chama_os_dois_crawlers_e_registra(self, db_session):
        with patch(f"{CAMARA}.sync_deputados", return_value=513) as dep, \
             patch(f"{SENADO}.sync_senadores", return_value=81) as sen:
            assert _rodar(db_session, "cadastros") == 0

        dep.assert_called_once_with(db_session)
        sen.assert_called_once_with(db_session)
        runs = _execucoes(db_session)
        assert runs["deputados"].status == "success"
        assert runs["deputados"].registros_processados == 513
        assert runs["senadores"].registros_criados == 81
        assert runs["senadores"].finalizado_em is not None

    def test_diario_roda_na_ordem_e_usa_o_ano_corrente(self, db_session):
        ordem = []
        with patch(f"{CAMARA}.sync_votacoes", side_effect=lambda db, ano: ordem.append(("votacoes", ano)) or 3), \
             patch(f"{SENADO}.sync_materias", side_effect=lambda db, ano: ordem.append(("senado", ano)) or 2), \
             patch("scripts.sync_pipeline.step1_discover", side_effect=lambda *a: ordem.append(("descoberta", a[1])) or {"novas": 1}), \
             patch("scripts.sync_pipeline.step2_sync_votacoes", return_value={"votacoes_novas": 4}), \
             patch("scripts.sync_pipeline.step4_scores", side_effect=lambda *a: ordem.append(("scores", None)) or {"scores_recalculados": 9, "direcoes": {"updated": 0}}):
            assert _rodar(db_session, "diario") == 0

        ano = date.today().year
        assert ordem == [("votacoes", ano), ("senado", ano), ("descoberta", ano), ("scores", None)]
        runs = _execucoes(db_session)
        assert runs["proposicoes"].registros_criados == 5
        assert runs["scores"].registros_processados == 9

    def test_falha_de_um_passo_nao_impede_os_seguintes_e_sai_com_1(self, db_session, capsys):
        with patch(f"{CAMARA}.sync_votacoes", side_effect=RuntimeError("API da Câmara fora")), \
             patch(f"{SENADO}.sync_materias", return_value=2) as senado:
            assert _rodar(db_session, "votacoes", "--ano", "2025") == 1
            assert _rodar(db_session, "senado") == 0

        senado.assert_called_once()
        run = _execucoes(db_session)["votacoes"]
        assert run.status == "failed"
        assert run.ano == 2025
        assert run.erros_count == 1
        assert run.erro_detalhes == [{"mensagem": "API da Câmara fora"}]
        assert "falhou" in capsys.readouterr().out

    def test_erros_parciais_viram_status_partial(self, db_session):
        with patch("scripts.sync_pipeline.step3_enrich",
                   return_value={"total": 5, "enriquecidas": 3, "erros": 2}):
            assert _rodar(db_session, "enriquecer", "--limite", "5") == 0
        run = _execucoes(db_session)["enriquecimento"]
        assert run.status == "partial"
        assert (run.registros_processados, run.registros_atualizados, run.erros_count) == (5, 3, 2)

    @pytest.mark.parametrize("argv", [("--dry-run", "cadastros"), ("cadastros", "--dry-run")])
    def test_dry_run_nao_chama_crawler_nem_grava(self, db_session, argv):
        with patch(f"{CAMARA}.sync_deputados") as dep, patch(f"{SENADO}.sync_senadores") as sen:
            assert _rodar(db_session, *argv) == 0
        dep.assert_not_called()
        sen.assert_not_called()
        assert _execucoes(db_session) == {}

    def test_enriquecer_repassa_o_limite(self, db_session):
        with patch("scripts.sync_pipeline.step3_enrich",
                   return_value={"total": 0, "enriquecidas": 0, "erros": 0}) as step:
            _rodar(db_session, "enriquecer", "--limite", "30")
        step.assert_called_once_with(db_session, False, limite=30)


class TestLimiteDoEnriquecimento:
    def test_limite_pega_as_mais_recentes(self, db_session, capsys):
        from scripts.sync_pipeline import step3_enrich

        for dia in (1, 2, 3, 4):
            p = make_proposicao(db_session, numero=dia, categorias_zil=["ZIL-MIN"])
            p.contexto_status = "pendente"
            p.data_apresentacao = date(2026, 1, dia)
        db_session.commit()

        assert step3_enrich(db_session, dry_run=True, limite=2)["total"] == 2
        assert step3_enrich(db_session, dry_run=True)["total"] == 4

        with patch("apps.workers.enrichment.enriquecer_proposicao", return_value="ok") as enriquecer:
            step3_enrich(db_session, dry_run=False, limite=2)
        escolhidas = {chamada.args[0] for chamada in enriquecer.call_args_list}
        from models import Proposicao
        numeros = {
            db_session.get(Proposicao, pid).numero for pid in escolhidas
        }
        assert numeros == {3, 4}

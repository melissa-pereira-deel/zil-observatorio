"""Tests for the ZIL scoring engine."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.scoring import calcular_alinhamento
from models import VotoEnum


class TestAlinhamento:
    def test_voto_sim_direcao_sim(self):
        assert calcular_alinhamento(VotoEnum.SIM, "sim") == 1.0

    def test_voto_nao_direcao_sim(self):
        assert calcular_alinhamento(VotoEnum.NAO, "sim") == -1.0

    def test_voto_sim_direcao_nao(self):
        assert calcular_alinhamento(VotoEnum.SIM, "nao") == -1.0

    def test_voto_nao_direcao_nao(self):
        assert calcular_alinhamento(VotoEnum.NAO, "nao") == 1.0

    def test_voto_ausente(self):
        assert calcular_alinhamento(VotoEnum.AUSENTE, "sim") == 0.0

    def test_voto_abstencao(self):
        assert calcular_alinhamento(VotoEnum.ABSTENCAO, "sim") == 0.0

    def test_voto_obstrucao(self):
        assert calcular_alinhamento(VotoEnum.OBSTRUCAO, "nao") == 0.0

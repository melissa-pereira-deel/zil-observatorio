"""Unit tests for CamaraClient.listar_votacoes_proposicao."""

import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.camara_client import CamaraClient, VotacaoAPI


class TestListarVotacoesProposicao:
    """Tests for CamaraClient.listar_votacoes_proposicao."""

    def test_returns_votacoes_for_proposicao(self):
        """Given a proposição with votações, returns list of VotacaoAPI."""
        mock_response = [
            {
                "id": "2269745-148",
                "dataHoraRegistro": "2024-12-18T14:30:00",
                "descricao": "Aprovada a Redação Final do PL 327/2021",
                "aprovacao": True,
            },
            {
                "id": "2269745-73",
                "data": "2024-06-15",
                "descricao": "Aprovado o Substitutivo",
                "aprovacao": True,
            },
        ]

        with patch.object(CamaraClient, "_get", return_value=mock_response):
            with CamaraClient() as client:
                result = client.listar_votacoes_proposicao(2269745)

        assert len(result) == 2
        assert all(isinstance(v, VotacaoAPI) for v in result)
        assert result[0].id == "2269745-148"
        assert result[0].data == "2024-12-18T14:30:00"
        assert result[0].descricao == "Aprovada a Redação Final do PL 327/2021"
        assert result[0].aprovacao is True
        assert result[1].id == "2269745-73"
        assert result[1].data == "2024-06-15"

    def test_returns_empty_list_for_proposicao_without_votacoes(self):
        """Given a proposição without votações, returns empty list."""
        with patch.object(CamaraClient, "_get", return_value=[]):
            with CamaraClient() as client:
                result = client.listar_votacoes_proposicao(9999999)

        assert result == []

    def test_handles_non_list_response(self):
        """Given an API response that is not a list, returns empty list."""
        with patch.object(CamaraClient, "_get", return_value={}):
            with CamaraClient() as client:
                result = client.listar_votacoes_proposicao(2269745)

        assert result == []

    def test_calls_correct_api_endpoint(self):
        """Verifies the method calls GET /proposicoes/{id}/votacoes."""
        with patch.object(CamaraClient, "_get", return_value=[]) as mock_get:
            with CamaraClient() as client:
                client.listar_votacoes_proposicao(2269745)

        mock_get.assert_called_once_with("/proposicoes/2269745/votacoes")

    def test_maps_data_hora_registro_field(self):
        """Uses dataHoraRegistro when present, falls back to data."""
        mock_response = [
            {
                "id": "123-1",
                "dataHoraRegistro": "2024-12-18T14:30:00",
                "data": "2024-12-18",
                "descricao": "Test",
                "aprovacao": True,
            },
        ]

        with patch.object(CamaraClient, "_get", return_value=mock_response):
            with CamaraClient() as client:
                result = client.listar_votacoes_proposicao(123)

        # dataHoraRegistro takes precedence over data
        assert result[0].data == "2024-12-18T14:30:00"

    def test_handles_missing_optional_fields(self):
        """Handles votação records with minimal fields."""
        mock_response = [
            {"id": "123-1"},
        ]

        with patch.object(CamaraClient, "_get", return_value=mock_response):
            with CamaraClient() as client:
                result = client.listar_votacoes_proposicao(123)

        assert len(result) == 1
        assert result[0].id == "123-1"
        assert result[0].data is None
        assert result[0].descricao == ""
        assert result[0].aprovacao is None

"""Tests for the ZIL classifier and scoring engine."""

import pytest
from apps.workers.classifiers import classificar_texto, classificar_proposicao, relevancia_score


class TestClassificador:
    def test_classifica_fertilizante(self):
        texto = "Dispõe sobre incentivos para produção nacional de fertilizantes"
        cats = classificar_texto(texto)
        assert "ZIL-FER" in cats

    def test_classifica_niobio(self):
        texto = "Regula a exportação de nióbio e terras raras"
        cats = classificar_texto(texto)
        assert "ZIL-MIN" in cats

    def test_classifica_semicondutor(self):
        texto = "Institui o programa Brasil Semicon para semicondutores"
        cats = classificar_texto(texto)
        assert "ZIL-SEM" in cats

    def test_classifica_energia(self):
        texto = "Cria fundo soberano com receitas do pré-sal"
        cats = classificar_texto(texto)
        assert "ZIL-ENE" in cats

    def test_classifica_digital(self):
        texto = "Regulamenta Starlink e proteção de dados pessoais"
        cats = classificar_texto(texto)
        assert "ZIL-DIG" in cats

    def test_classifica_defesa(self):
        texto = "Fortalece Embraer como polo de defesa cibernética"
        cats = classificar_texto(texto)
        assert "ZIL-DEF" in cats

    def test_classifica_multiplas_categorias(self):
        texto = "Incentiva produção de fertilizantes e semicondutores no Brasil"
        cats = classificar_texto(texto)
        assert "ZIL-FER" in cats
        assert "ZIL-SEM" in cats

    def test_texto_vazio_retorna_vazio(self):
        assert classificar_texto("") == []
        assert classificar_texto(None) == []

    def test_texto_irrelevante_retorna_vazio(self):
        texto = "Dispõe sobre feriados nacionais"
        cats = classificar_texto(texto)
        assert len(cats) == 0

    def test_classificar_proposicao_combina_campos(self):
        cats = classificar_proposicao(
            ementa="Altera legislação tributária",
            ementa_detalhada="Concede benefícios para indústria de fertilizantes",
        )
        assert "ZIL-FER" in cats

    def test_relevancia_score(self):
        texto = "Incentivos fiscais para produção de fertilizantes NPK e potássio no Brasil"
        cats = classificar_texto(texto)
        score = relevancia_score(texto, cats)
        assert score > 0
        assert score <= 1.0

    def test_relevancia_zero_para_vazio(self):
        assert relevancia_score("", []) == 0.0

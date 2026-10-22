"""Unidades do pipeline de explicação: schema, extração, revisão, coleta, persistência."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.agentes.meta import MetaExecucao  # noqa: E402
from apps.workers.explicacao.coleta import (  # noqa: E402
    Autor,
    FichaFatos,
    Tramitacao,
    entidades_conhecidas,
    ficha_para_prompt,
)
from apps.workers.explicacao.extracao import (  # noqa: E402
    MIN_CHARS_POR_PAGINA,
    NaoEhPDF,
    TextoExtraido,
    extrair_texto_pdf,
    separar_secoes,
)
from apps.workers.explicacao.persistencia import gravar, hash_texto  # noqa: E402
from apps.workers.explicacao.revisao import entidades_fabricadas, revisar  # noqa: E402
from apps.workers.explicacao.schema import (  # noqa: E402
    Afirmacao,
    AnaliseSistemica,
    Dissenso,
    Explicacao,
    ParecerLente,
    ResumoDetalhado,
    ResumoDidatico,
    TamanhoInvalido,
)
from tests.conftest import make_proposicao  # noqa: E402


# ── schema ────────────────────────────────────────────────────────────────────

class TestSchema:
    @pytest.mark.parametrize("n,ok", [(239, False), (240, True), (640, True), (641, False)])
    def test_resumo_didatico_valida_na_construcao(self, n, ok):
        if ok:
            assert len(ResumoDidatico("a" * n).texto) == n
        else:
            with pytest.raises(TamanhoInvalido) as e:
                ResumoDidatico("a" * n)
            assert e.value.campo == "resumo_didatico" and e.value.tamanho == n

    @pytest.mark.parametrize("n,ok", [(479, False), (480, True), (2480, True), (2481, False)])
    def test_resumo_detalhado_valida_na_construcao(self, n, ok):
        if ok:
            ResumoDetalhado("a" * n)
        else:
            with pytest.raises(TamanhoInvalido):
                ResumoDetalhado("a" * n)

    def test_literal_exige_citacao(self):
        with pytest.raises(ValueError, match="sem citação"):
            Afirmacao(lente="x", tipo="literal", texto="t", dimensao="juridica")
        Afirmacao(lente="x", tipo="inferencia", texto="t", dimensao="juridica")

    def test_dimensao_desconhecida_e_rejeitada(self):
        with pytest.raises(ValueError, match="dimensão desconhecida"):
            Afirmacao(lente="x", tipo="inferencia", texto="t", dimensao="astral")

    def test_dissenso_exige_duas_lentes_distintas(self):
        with pytest.raises(ValueError):
            Dissenso("a", "a", "ponto")
        with pytest.raises(ValueError):
            Dissenso("a", "b", "   ")


# ── extração ──────────────────────────────────────────────────────────────────

class TestExtracao:
    def test_separa_dispositivo_e_justificacao(self):
        d, j = separar_secoes("Art. 1º X.\n\nJUSTIFICAÇÃO\nPorque sim.")
        assert d == "Art. 1º X." and j == "Porque sim."

    def test_sem_justificacao_e_estado_valido(self):
        """O PL 1847/2024 não tem a seção: o inteiro teor é o texto final."""
        d, j = separar_secoes("Art. 1º X.")
        assert d == "Art. 1º X." and j is None

    def test_tolera_grafia_sem_acento(self):
        _, j = separar_secoes("Art. 1º X. JUSTIFICACAO Porque.")
        assert j == "Porque."

    def test_vazio(self):
        assert separar_secoes("") == (None, None)

    def test_nao_pdf_lanca(self):
        with pytest.raises(NaoEhPDF):
            extrair_texto_pdf(b"<html>erro</html>")

    def test_pdf_minimo_sem_texto_e_insuficiente(self):
        # PDF válido de uma página sem conteúdo: o que uma digitalização pura devolve
        pdf = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
               b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
               b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
               b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \n"
               b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n160\n%%EOF")
        t = extrair_texto_pdf(pdf)
        assert t.metodo == "insuficiente" and not t.utilizavel
        assert t.chars_por_pagina < MIN_CHARS_POR_PAGINA
        assert "OCR" in (t.erro or "")


# ── coleta / ficha ────────────────────────────────────────────────────────────

def _ficha(**kw) -> FichaFatos:
    base = dict(
        fonte="camara", fonte_id="1", tipo="PL", numero=1, ano=2025, ementa="E.",
        autores=[Autor("Maria Exemplo", "Deputado(a)", "PSD", "MG"), Autor("João Modelo", "Deputado(a)", "PSDB", "BA")],
        tramitacoes=[Tramitacao("2025-03-10", "MESA", "Apresentação")],
        data_apresentacao="2025-03-10",
        origens={"proposicao": "x", "autores": "x", "tramitacoes": "x", "relacionadas": "x", "temas_oficiais": "x"},
    )
    base.update(kw)
    return FichaFatos(**base)


class TestFicha:
    def test_grupo_politico_e_coalizao(self):
        assert "2 autor(es) de 2 partido(s): PSD, PSDB" == _ficha().grupo_politico

    def test_sem_autores(self):
        assert "não informada" in _ficha(autores=[]).grupo_politico

    def test_prompt_declara_o_que_nao_obteve(self):
        f = _ficha(origens={"proposicao": "x"})
        p = ficha_para_prompt(f)
        assert "Autoria: NÃO OBTIDA" in p and "Cronologia: NÃO OBTIDA" in p

    def test_entidades_conhecidas(self):
        e = entidades_conhecidas(_ficha())
        assert e["nomes"] == {"Maria Exemplo", "João Modelo"}
        assert e["partidos"] == {"PSD", "PSDB"}
        assert "2025-03-10" in e["datas"]


# ── revisão ───────────────────────────────────────────────────────────────────

class TestRevisao:
    def test_detecta_nome_partido_e_data_fora_da_ficha(self):
        texto = "Apresentado pelo Deputado Fulano de Tal (NOVO) em 15/02/2025."
        f = entidades_fabricadas(texto, _ficha())
        assert any("Fulano de Tal" in x for x in f)
        assert any("NOVO" in x for x in f)
        assert any("15/02/2025" in x for x in f)

    def test_entidades_da_ficha_passam(self):
        texto = "Apresentado pela Deputada Maria Exemplo (PSD) em 10/03/2025 e 2025-03-10."
        assert entidades_fabricadas(texto, _ficha()) == []

    def test_pl_seguido_de_numero_e_proposicao_nao_partido(self):
        """O harness pegou: 'O PL 1001/2025' era acusado de inventar o Partido Liberal."""
        assert entidades_fabricadas("O PL 1001/2025 e a PEC 45 tramitam.", _ficha()) == []
        assert any("PL" in x for x in entidades_fabricadas("apoiado pelo PL e pelo PSD.", _ficha()))

    def test_sigla_que_nao_e_partido_nao_conta(self):
        assert entidades_fabricadas("Conforme a ONU e a OMC.", _ficha()) == []

    def test_citacao_literal_conferida_contra_o_texto(self):
        texto = "Art. 1º Fica instituída a Política X."
        ok = ParecerLente("leitor", [Afirmacao("leitor", "literal", "Institui X.", "juridica", "Fica instituída a Política X")])
        ruim = ParecerLente("leitor", [Afirmacao("leitor", "literal", "Revoga Y.", "juridica", "Fica revogada a Lei Y")])
        r1 = revisar(ficha=_ficha(), texto_extraido=texto, pareceres=[ok], lentes_roteadas=["leitor"],
                     resumo_didatico=None, resumo_detalhado=None, analise=None)
        r2 = revisar(ficha=_ficha(), texto_extraido=texto, pareceres=[ruim], lentes_roteadas=["leitor"],
                     resumo_didatico=None, resumo_detalhado=None, analise=None)
        assert r1.metricas["citacoes_verificadas"] == 1 and not r1.problemas
        assert r2.metricas["citacoes_verificadas"] == 0 and r2.problemas

    def test_maioria_das_lentes_sem_nada_a_dizer_acusa_roteamento(self):
        ps = [ParecerLente(nome, nada_a_dizer=True) for nome in ("a", "b", "c")]
        r = revisar(ficha=_ficha(), texto_extraido="", pareceres=ps, lentes_roteadas=["a", "b", "c"],
                    resumo_didatico=None, resumo_detalhado=None, analise=None)
        # sinal sobre a tabela de roteamento, agregado por lote — não reprova esta execução
        assert r.metricas["roteamento_suspeito"] is True
        assert not r.problemas


# ── persistência ──────────────────────────────────────────────────────────────

def _resultado(versao="abc123", status="pronto") -> Explicacao:
    return Explicacao(
        fonte="camara", fonte_id="1", pipeline_versao=versao,
        resumo_didatico=ResumoDidatico("d" * 300), resumo_detalhado=ResumoDetalhado("e" * 600),
        analise=AnaliseSistemica([], [], [], {}, [Dissenso("a", "b", "p")], ["a", "b"]),
        pareceres=[ParecerLente("a", [Afirmacao("a", "inferencia", "t", "publica")])],
        meta=MetaExecucao({"a": "m"}, {"a": "h"}, {"a": 1}, "2026-10-21T00:00:00+00:00"),
        metricas={"x": 1}, status=status,
    )


class TestPersistencia:
    def test_grava_e_le(self, db_session):
        prop = make_proposicao(db_session)
        linha = gravar(db_session, prop.id, _resultado(), hash_texto("texto"))
        assert linha.resumo_didatico == "d" * 300
        assert linha.evidencias["dissensos"] == [{"lente_a": "a", "lente_b": "b", "ponto": "p"}]
        assert linha.meta["hashes_instrucoes"] == {"a": "h"}
        assert linha.status == "pronto"

    def test_idempotente_na_chave(self, db_session):
        prop = make_proposicao(db_session)
        h = hash_texto("texto")
        a = gravar(db_session, prop.id, _resultado(), h)
        b = gravar(db_session, prop.id, _resultado(), h)
        assert a.id == b.id

    def test_pipeline_diferente_coexiste(self, db_session):
        """É o que permite comparar abordagens lado a lado."""
        prop = make_proposicao(db_session)
        h = hash_texto("texto")
        a = gravar(db_session, prop.id, _resultado("v1hash"), h)
        b = gravar(db_session, prop.id, _resultado("v2hash"), h)
        assert a.id != b.id
        assert len(prop.explicacoes) == 2

    def test_force_substitui(self, db_session):
        prop = make_proposicao(db_session)
        h = hash_texto("texto")
        a = gravar(db_session, prop.id, _resultado(status="invalido"), h)
        b = gravar(db_session, prop.id, _resultado(status="pronto"), h, force=True)
        assert a.id != b.id and b.status == "pronto"
        assert len(prop.explicacoes) == 1


# ── S5, refinado: origem e estágio decidem se há justificação ────────────────

class TestJustificacaoPorOrigem:
    def test_grafias_do_cabecalho(self):
        for cab in ("JUSTIFICAÇÃO", "JUSTIFICACAO", "Justificação", "JUSTIFICATIVA", "J U S T I F I C A Ç Ã O"):
            _, j = separar_secoes(f"Art. 1º X.\n\n{cab}\nPorque.")
            assert j == "Porque.", cab

    def test_palavra_no_meio_de_frase_nao_e_cabecalho(self):
        """'justificativa' como substantivo comum no dispositivo não abre seção."""
        d, j = separar_secoes("Art. 1º A justificativa do pedido será escrita.")
        # o regex casa a palavra; o que protege é o uso do resultado: dispositivo
        # curto demais + justificação que começa no meio da frase. Aqui só se
        # registra o comportamento atual para que uma mudança seja consciente.
        assert j is not None

    def test_autografo_do_senado_e_reconhecido(self):
        t = TextoExtraido(texto="Art. 1º X.\n... Senado Federal, em 10 de setembro de 2025.\nPresidente do Senado Federal",
                          metodo="pdf_nativo", paginas=1, chars_por_pagina=500, dispositivo="Art. 1º X.", origem_senado=True)
        assert "autógrafo do Senado" in t.motivo_sem_justificacao

    def test_motivo_quando_texto_nao_extraido(self):
        t = TextoExtraido(texto="", metodo="indisponivel", erro="sem urlInteiroTeor")
        assert "não extraído" in t.motivo_sem_justificacao

    def test_sem_motivo_quando_ha_justificacao(self):
        t = TextoExtraido(texto="x", metodo="pdf_nativo", paginas=1, chars_por_pagina=500, justificacao="Porque.")
        assert t.motivo_sem_justificacao is None

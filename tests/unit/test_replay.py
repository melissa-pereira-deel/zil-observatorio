"""Replay das respostas gravadas (TRM-002): nenhum teste aqui acessa a rede."""

import copy
import json
import os
import random
import re
import subprocess
import sys
import uuid
from datetime import date
from pathlib import Path

import httpx
import pytest
import yaml

from packages.camara_client import CamaraClient
from packages.senado_client import SenadoClient
from scripts.gravar_respostas import Receitas, _remover_campos, conferir_janela_completa, executar_receita
from tests.replay import (
    RAIZ_FIXTURES,
    RAIZ_GRAVACOES,
    VALOR_REMOVIDO,
    Gravacoes,
    PacoteInconsistente,
    RequisicaoNaoGravada,
    achados_de_cpf,
    hash_corpo,
)

REPO_ROOT = Path(__file__).parent.parent.parent
LIMITE_FIXTURES = 8 * 1024 * 1024


def _envelope(caminho, corpo, *, status=200, params=None, host="camara", cabecalhos=None):
    return {
        "host": host,
        "metodo": "GET",
        "caminho": caminho,
        "params": params or {},
        "status": status,
        "cabecalhos": cabecalhos or {"content-type": "application/json"},
        "corpo": corpo,
        "sha256_corpo": hash_corpo(corpo),
    }


def _pacote(raiz: Path, slug: str, *respostas, sintetico=False, **extras) -> Path:
    arquivo = raiz / f"{slug}.json"
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(
        json.dumps(
            {
                "formato": 1,
                "caso": slug,
                "gravado_em": "2026-11-05T10:00:00-03:00",
                "sintetico": sintetico,
                "respostas": list(respostas),
                **extras,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return arquivo


@pytest.fixture
def raiz(tmp_path) -> Path:
    gravacoes = tmp_path / "gravacoes"
    gravacoes.mkdir()
    return gravacoes


@pytest.fixture(autouse=True)
def _sem_espera(monkeypatch):
    # O cliente de produção dorme entre retentativas; o teste não precisa esperar.
    monkeypatch.setattr("time.sleep", lambda _s: None)


# ── Critério 1: transporte injetável ──


class TestTransporteInjetavel:
    def _transporte(self, chamadas):
        def responder(request):
            chamadas.append(str(request.url))
            return httpx.Response(200, json={"dados": {"id": 1}})

        return httpx.MockTransport(responder)

    def test_camara_usa_o_transporte(self):
        chamadas = []
        with CamaraClient(transport=self._transporte(chamadas)) as cliente:
            assert cliente._get("/proposicoes/1") == {"id": 1}
        assert chamadas == ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/1"]

    def test_senado_usa_o_transporte(self):
        chamadas = []
        with SenadoClient(transport=self._transporte(chamadas)) as cliente:
            assert cliente._get("/processo/1") == {"dados": {"id": 1}}
        assert chamadas == ["https://legis.senado.leg.br/dadosabertos/processo/1"]

    @pytest.mark.parametrize("classe", [CamaraClient, SenadoClient])
    def test_sem_argumento_continua_com_o_transporte_real(self, classe):
        with classe() as cliente:
            assert isinstance(cliente.client._transport, httpx.HTTPTransport)
            assert cliente.client.headers["accept"] == "application/json"
            assert cliente.client.timeout == httpx.Timeout(30.0)

    @pytest.mark.parametrize("classe", [CamaraClient, SenadoClient])
    def test_base_url_continua_posicional(self, classe):
        with classe("https://exemplo.test/base") as cliente:
            assert cliente.base_url == "https://exemplo.test/base"


# ── Critério 3: corpo, cabeçalhos e parâmetros ──


class TestRequisicaoGravada:
    def test_corpo_e_cabecalhos_iguais_ao_gravado(self, raiz):
        corpo = {"dados": {"id": 7, "ementa": "Institui ação"}, "links": []}
        _pacote(
            raiz,
            "caso",
            _envelope(
                "/proposicoes/7",
                corpo,
                cabecalhos={
                    "x-total-count": "1",
                    "link": None,
                    "retry-after": "30",
                    "content-type": "application/json",
                },
            ),
        )
        g = Gravacoes(raiz).carregar("caso")
        with g.cliente_camara() as cliente:
            resposta = cliente.client.get("/proposicoes/7")
        assert resposta.status_code == 200
        assert resposta.json() == corpo
        assert resposta.headers["x-total-count"] == "1"
        assert resposta.headers["retry-after"] == "30"
        assert resposta.headers["content-type"] == "application/json"
        # Cabeçalho gravado como null é ausência, e ausência tem de continuar ausência.
        assert "link" not in resposta.headers

    def test_acentos_sobrevivem_ao_replay(self, raiz):
        corpo = {"dados": {"ementa": "Altera a Lei nº 1 — Código de Trânsito"}}
        _pacote(raiz, "caso", _envelope("/proposicoes/7", corpo))
        with Gravacoes(raiz).carregar("caso").cliente_camara() as cliente:
            assert cliente._get("/proposicoes/7") == corpo["dados"]

    def test_parametros_em_outra_ordem_casam(self, raiz):
        _pacote(
            raiz,
            "caso",
            _envelope(
                "/proposicoes",
                {"dados": [{"id": 1}]},
                params={"itens": "100", "ordem": "ASC", "siglaTipo": "PL,PEC"},
            ),
        )
        g = Gravacoes(raiz).carregar("caso")
        with g.cliente_camara() as cliente:
            dados = cliente._get("/proposicoes", {"siglaTipo": "PL,PEC", "ordem": "ASC", "itens": 100})
        assert dados == [{"id": 1}]

    def test_mesmo_caminho_na_outra_casa_nao_casa(self, raiz):
        _pacote(raiz, "caso", _envelope("/processo/1", {"id": 1}, host="senado"))
        g = Gravacoes(raiz).carregar("caso")
        with g.cliente_senado() as cliente:
            assert cliente._get("/processo/1") == {"id": 1}
        with g.cliente_camara() as cliente, pytest.raises(RequisicaoNaoGravada):
            cliente._get("/processo/1")
        g.nao_gravadas.clear()

    def test_cliente_camara_repassa_kwargs(self, raiz):
        g = Gravacoes(raiz)
        with g.cliente_camara(base_url="https://dadosabertos.camara.leg.br/api/v2") as cliente:
            assert isinstance(cliente.client._transport, httpx.MockTransport)

    def test_carregar_acumula_pacotes_e_devolve_o_proprio_objeto(self, raiz):
        _pacote(raiz, "a", _envelope("/proposicoes/1", {"dados": {"id": 1}}))
        _pacote(raiz, "b", _envelope("/proposicoes/2", {"dados": {"id": 2}}))
        g = Gravacoes(raiz)
        assert g.carregar("a") is g
        g.carregar("b")
        with g.cliente_camara() as cliente:
            assert cliente._get("/proposicoes/1") == {"id": 1}
            assert cliente._get("/proposicoes/2") == {"id": 2}

    def test_carregar_junta_as_partes_de_um_pacote_dividido(self, raiz):
        _pacote(raiz, "grande", _envelope("/proposicoes/1", {"dados": {"id": 1}}), parte=1, partes=2)
        _pacote(raiz, "grande.parte-02", _envelope("/proposicoes/2", {"dados": {"id": 2}}), caso="grande", parte=2, partes=2)
        g = Gravacoes(raiz).carregar("grande")
        with g.cliente_camara() as cliente:
            assert cliente._get("/proposicoes/2") == {"id": 2}

    def test_parte_faltando_e_erro_alto(self, raiz):
        _pacote(raiz, "grande", _envelope("/proposicoes/1", {"dados": {"id": 1}}), parte=1, partes=2)
        with pytest.raises(FileNotFoundError, match="parte"):
            Gravacoes(raiz).carregar("grande")

    def test_carregar_aceita_candidatos_e_sinteticos(self, raiz):
        _pacote(raiz.parent / "candidatos", "123", _envelope("/proposicoes/123", {"dados": {"id": 123}}))
        _pacote(raiz.parent / "sinteticos", "s", _envelope("/proposicoes/9", {"dados": {"id": 9}}), sintetico=True)
        g = Gravacoes(raiz).carregar("candidatos/123", "sinteticos/s")
        with g.cliente_camara() as cliente:
            assert cliente._get("/proposicoes/123") == {"id": 123}
            assert cliente._get("/proposicoes/9") == {"id": 9}

    def test_slug_inexistente_e_erro_alto(self, raiz):
        with pytest.raises(FileNotFoundError):
            Gravacoes(raiz).carregar("nao-existe")

    def test_corpo_le_direto_sem_passar_pelo_transporte(self, raiz):
        _pacote(
            raiz,
            "caso",
            _envelope("/proposicoes", {"dados": [1]}, params={"pagina": "1"}),
            _envelope("/proposicoes", {"dados": [2]}, params={"pagina": "2"}),
        )
        g = Gravacoes(raiz)
        assert g.corpo("caso", "/proposicoes", {"pagina": 2}) == {"dados": [2]}
        assert g.requisicoes_feitas == []

    def test_corpo_nao_gravado_e_erro_alto(self, raiz):
        _pacote(raiz, "caso", _envelope("/proposicoes/1", {"dados": {}}))
        with pytest.raises(KeyError, match="/proposicoes/2"):
            Gravacoes(raiz).corpo("caso", "/proposicoes/2")


# ── Partes de um pacote dividido ──


class TestPartes:
    def _dividido(self, raiz, *respostas_por_parte, **ajustes):
        total = len(respostas_por_parte)
        for numero, resposta in enumerate(respostas_por_parte, start=1):
            slug = "grande" if numero == 1 else f"grande.parte-{numero:02d}"
            extras = {"caso": "grande", "parte": numero, "partes": total, **ajustes.get(f"p{numero}", {})}
            _pacote(raiz, slug, resposta, **extras)

    def test_partes_entram_na_ordem_em_uma_sequencia(self, raiz):
        self._dividido(
            raiz,
            _envelope("/proposicoes/1", {"n": 1}),
            _envelope("/proposicoes/1", {"n": 2}),
            _envelope("/proposicoes/1", {"n": 3}),
        )
        g = Gravacoes(raiz).carregar("grande")
        with g.cliente_camara() as cliente:
            assert [cliente._get("/proposicoes/1") for _ in range(3)] == [{"n": 1}, {"n": 2}, {"n": 3}]

    def test_parte_orfa_e_erro_alto(self, raiz):
        self._dividido(raiz, _envelope("/proposicoes/1", {"n": 1}), _envelope("/proposicoes/2", {"n": 2}))
        _pacote(raiz, "grande.parte-03", _envelope("/proposicoes/3", {"n": 3}), caso="grande", parte=3, partes=2)
        with pytest.raises(PacoteInconsistente, match="parte-03"):
            Gravacoes(raiz).carregar("grande")

    def test_parte_sem_declaracao_na_cabeca_e_erro_alto(self, raiz):
        _pacote(raiz, "grande", _envelope("/proposicoes/1", {"n": 1}))
        _pacote(raiz, "grande.parte-02", _envelope("/proposicoes/2", {"n": 2}), caso="grande", parte=2, partes=2)
        with pytest.raises(PacoteInconsistente, match="parte-02"):
            Gravacoes(raiz).carregar("grande")

    @pytest.mark.parametrize(
        "ajuste",
        [{"parte": 3}, {"partes": 3}, {"caso": "outro"}, {"gravado_em": "2026-11-06T10:00:00-03:00"}],
        ids=["numero", "total", "caso", "gravado_em"],
    )
    def test_cabeca_da_parte_divergente_e_erro_alto(self, raiz, ajuste):
        self._dividido(
            raiz,
            _envelope("/proposicoes/1", {"n": 1}),
            _envelope("/proposicoes/2", {"n": 2}),
            p2=ajuste,
        )
        with pytest.raises(PacoteInconsistente, match="parte-02"):
            Gravacoes(raiz).carregar("grande")


# ── Pacotes diferentes com a mesma requisição ──


class TestPacotesDiferentes:
    def test_corpos_diferentes_para_a_mesma_requisicao_e_erro_alto(self, raiz):
        _pacote(raiz, "a", _envelope("/orgaos/4", {"dados": {"sigla": "MESA"}}))
        _pacote(raiz, "b", _envelope("/orgaos/4", {"dados": {"sigla": "MESA", "nome": "novo"}}))
        with pytest.raises(PacoteInconsistente) as erro:
            Gravacoes(raiz).carregar("a", "b")
        assert "/orgaos/4" in str(erro.value)
        assert "a" in str(erro.value) and "b" in str(erro.value)

    def test_erro_vale_tambem_em_carregar_separado(self, raiz):
        _pacote(raiz, "a", _envelope("/orgaos/4", {"n": 1}))
        _pacote(raiz, "b", _envelope("/orgaos/4", {"n": 2}))
        g = Gravacoes(raiz).carregar("a")
        with pytest.raises(PacoteInconsistente):
            g.carregar("b")

    def test_corpos_iguais_convivem_e_nao_alongam_a_sequencia(self, raiz):
        corpo = {"dados": {"sigla": "MESA"}}
        _pacote(raiz, "a", _envelope("/orgaos/4", corpo), _envelope("/proposicoes/1", {"n": 1}))
        _pacote(raiz, "b", _envelope("/orgaos/4", corpo), _envelope("/proposicoes/2", {"n": 2}))
        g = Gravacoes(raiz).carregar("a", "b")
        with g.cliente_camara() as cliente:
            assert cliente._get("/orgaos/4") == corpo["dados"]
            assert cliente._get("/proposicoes/2") == {"n": 2}

    def test_sequencia_de_outro_pacote_igual_nao_e_servida_duas_vezes(self, raiz):
        def sequencia():
            return (
                _envelope("/proposicoes/1", {}, status=429),
                _envelope("/proposicoes/1", {"dados": {"id": 1}}),
            )

        _pacote(raiz, "a", *sequencia(), sintetico=True)
        _pacote(raiz, "b", *sequencia(), sintetico=True)
        g = Gravacoes(raiz).carregar("a", "b")
        with g.cliente_camara() as cliente:
            codigos = [cliente.client.get("/proposicoes/1").status_code for _ in range(3)]
        assert codigos == [429, 200, 200]

    def test_sequencia_dentro_de_um_pacote_continua_valendo(self, raiz):
        _pacote(raiz, "a", _envelope("/proposicoes/1", {"n": 1}), _envelope("/proposicoes/1", {"n": 2}))
        g = Gravacoes(raiz).carregar("a")
        with g.cliente_camara() as cliente:
            assert [cliente._get("/proposicoes/1"), cliente._get("/proposicoes/1")] == [{"n": 1}, {"n": 2}]

    def test_mesmo_caminho_em_casas_diferentes_nao_diverge(self, raiz):
        _pacote(raiz, "a", _envelope("/x", {"n": 1}))
        _pacote(raiz, "b", _envelope("/x", {"n": 2}, host="senado"))
        Gravacoes(raiz).carregar("a", "b")

    def test_mesmo_pacote_carregado_duas_vezes_nao_alonga_a_sequencia(self, raiz):
        _pacote(raiz, "a", _envelope("/proposicoes/1", {"n": 1}), _envelope("/proposicoes/1", {"n": 2}))
        g = Gravacoes(raiz).carregar("a", "a")
        with g.cliente_camara() as cliente:
            assert [cliente._get("/proposicoes/1") for _ in range(3)] == [{"n": 1}, {"n": 2}, {"n": 2}]


# ── Varredura de CPF ──


# 111.444.777-35 é o exemplo didático de CPF válido: não identifica ninguém conhecido aqui.
class TestVarreduraDeCpf:
    @pytest.mark.parametrize(
        "corpo",
        [
            {"cpf": "11144477735"},
            {"CPF": "qualquer coisa"},
            {"dados": {"ultimoStatus": {"numeroCpf": "1"}}},
            {"dados": [{"a": {"CpfCnpj": 123}}]},
            {"cpf": {"numero": "1"}},
            {"despacho": "Requerente de CPF 111.444.777-35, conforme ofício."},
            {"despacho": "111 444 777 35"},
            {"despacho": "111\u00a0444\u00a0777\u00a035"},
            {"despacho": "111.444.777 35"},
            {"despacho": "111444777-35"},
            {"despacho": "documento 11144477735 anexo"},
            {"documento": 11144477735},
            {"dados": ["11144477735"]},
            {"111.444.777-35": "na chave"},
            {"despacho": "cpf=11144477736"},
            {"despacho": "cpf11144477735"},
            "corpo em texto: 111.444.777-35",
        ],
    )
    def test_acha(self, corpo):
        assert achados_de_cpf(corpo)

    @pytest.mark.parametrize(
        "corpo",
        [
            {"id": 2269745},
            {"id": "2269745", "codigoMateria": 162766},
            {"uri": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2269745"},
            {"id": 11144477736},  # 11 dígitos sem dígito verificador válido
            {"id": "11144477736"},
            {"id": 111444777351},  # 12 dígitos
            {"id": "11111111111"},  # repetição passa na conta, mas não é CPF
            {"id": "00000000000"},
            {"cnpj": "11222333000181"},
            {"ementa": "CNPJ 11.222.333/0001-81"},
            {"processo": "1.234.567.890-12"},
            {"processo": "123.456.789-012"},
            {"processo": "123.456.789-01.234"},
            {"url": "https://x.test/550e8400-e29b-41d4-a716-446655440000"},
            {"url": "https://x.test/a11144477735b"},
            {"url": "https://x.test/prop_mostrarintegra?codteor=2950326"},
            {"titulo": "PL 5941/2013", "lei": "Lei 15.103/2025"},
            {"dataHora": "2026-11-05T22:46:22"},
            {"telefone": "(61) 3215-5204"},
            {"valor": "R$ 100.000.000,00"},
            {"cpf": VALOR_REMOVIDO},
            {"cpf": None},
            {"cpf": ""},
            {"ativo": True, "x": None, "y": 1.5},
            [],
        ],
    )
    def test_nao_confunde(self, corpo):
        assert achados_de_cpf(corpo) == []

    def test_achado_diz_o_caminho_e_nunca_o_valor(self):
        achados = achados_de_cpf(
            {
                "dados": {
                    "lista": [{"despacho": "111.444.777-35"}],
                    "ultimoStatus": {"cpf": "11144477735"},
                    "111.444.777-35": 1,
                }
            }
        )
        texto = " ".join(achados)
        assert "dados.lista[0].despacho" in texto
        assert "dados.ultimoStatus.cpf" in texto
        assert "11144477735" not in texto
        assert "444" not in texto


# Montados à mão para cair no único formato de UUID que parecia CPF: `[ab]ddd-dddddddd` seguido de
# letra. O segundo traz nesse trecho o número didático, com dígito verificador válido: é o caso que
# exigir a conta na forma com separador não resolveria.
UUID_COM_FORMA_DE_CPF = "550e8400-e29b-41d4-a123-12345678abcd"
UUID_COM_CPF_VALIDO = "550e8400-e29b-41d4-b111-44477735cdef"


class TestUuidNaoEhCpf:
    @pytest.mark.parametrize("valor", [UUID_COM_FORMA_DE_CPF, UUID_COM_CPF_VALIDO])
    def test_os_exemplos_sao_uuid_v4_de_verdade(self, valor):
        assert uuid.UUID(valor).version == 4

    @pytest.mark.parametrize(
        "corpo",
        [
            {"id": UUID_COM_FORMA_DE_CPF},
            {"id": UUID_COM_CPF_VALIDO},
            {"id": UUID_COM_CPF_VALIDO.upper()},
            {"id": "550e8400-e29b-71d4-a123-12345678abcd"},  # v7: o mesmo risco, em outra versão
            {"url": f"https://legis.senado.leg.br/dadosabertos/processo/documento/{UUID_COM_CPF_VALIDO}"},
            {"url": f"https%3A%2F%2Fx.test%2F{UUID_COM_CPF_VALIDO}"},
            {"url": f"https://x.test/{UUID_COM_CPF_VALIDO}xyz"},
            {"texto": f"documento {UUID_COM_CPF_VALIDO}, anexo {UUID_COM_FORMA_DE_CPF}."},
            {UUID_COM_CPF_VALIDO: 1},
            {"dados": [{"documentos": [{"id": UUID_COM_FORMA_DE_CPF}]}]},
        ],
    )
    def test_nao_confunde_uuid_com_cpf(self, corpo):
        assert achados_de_cpf(corpo) == []

    def test_amostra_de_uuid_v4_nao_acha_nada(self):
        # Semente fixa: sem a máscara, cerca de 1 em cada 1.000 dá achado.
        gerador = random.Random(20261106)
        amostra = [str(uuid.UUID(int=gerador.getrandbits(128), version=4)) for _ in range(20_000)]
        assert sum(bool(achados_de_cpf(valor)) for valor in amostra) == 0

    @pytest.mark.parametrize(
        "corpo",
        [
            # A máscara não pode emendar o que estava separado pelo UUID e criar um CPF que não existe.
            {"x": f"111444{UUID_COM_FORMA_DE_CPF}77735"},
            {"x": f"111 444 777{UUID_COM_FORMA_DE_CPF}35"},
        ],
    )
    def test_uuid_no_meio_nao_emenda_numeros(self, corpo):
        assert achados_de_cpf(corpo) == []


class TestProtecaoNaoAfrouxou:
    """O que a correção do UUID poderia ter perdido. Só o número didático, nunca um CPF de alguém."""

    @pytest.mark.parametrize(
        ("corpo", "caminho"),
        [
            ({"despacho": "111.444.777-35"}, "despacho"),
            ({"despacho": "111 444 777 35"}, "despacho"),
            ({"despacho": "111 444 777 35"}, "despacho"),
            ({"dados": {"partes": [{"autor": {"obs": "111.444.777-35"}}]}}, "dados.partes[0].autor.obs"),
            ({"documentoTitular": "111.444.777-35"}, "documentoTitular"),
            ({"numDoc": "11144477735"}, "numDoc"),
            ({"numDoc": 11144477735}, "numDoc"),
            ({"despacho": "O requerente, inscrito sob o nº 111.444.777-35, compareceu."}, "despacho"),
            ({"111.444.777-35": "na chave"}, "<chave com forma de CPF>"),
        ],
    )
    def test_acha_no_caminho_certo(self, corpo, caminho):
        assert achados_de_cpf(corpo) == [caminho]

    @pytest.mark.parametrize(
        "texto",
        [
            "111.444.777-36",
            "111 444 777 36",
            "111.111.111-11",
            "000.000.000-00",
            "CPF: 111.444.777-36",
        ],
    )
    def test_com_separador_nao_depende_do_digito_verificador(self, texto):
        # Número com erro de digitação ou de OCR ainda aponta para uma pessoa. Só os 11 dígitos
        # corridos precisam da conta, porque um id numérico pode ter esse tamanho.
        assert achados_de_cpf({"despacho": texto}) == ["despacho"]

    @pytest.mark.parametrize(
        "texto",
        [
            "CPF111.444.777-35",
            "CPF/MF111.444.777-35",
            "no111.444.777-35",
            "111.444.777-35residente",
        ],
    )
    def test_letra_colada_no_numero_com_separador_nao_esconde(self, texto):
        # Texto de PDF perde espaço. Recusar letra na borda apagaria estes casos.
        assert achados_de_cpf({"despacho": texto}) == ["despacho"]

    @pytest.mark.parametrize(
        "corpo",
        [
            {"despacho": f"anexo {UUID_COM_CPF_VALIDO}; requerente 111.444.777-35"},
            {"despacho": f"requerente 111.444.777-35; anexo {UUID_COM_CPF_VALIDO}"},
            {"despacho": f"{UUID_COM_CPF_VALIDO} 11144477735"},
            {"despacho": f"{UUID_COM_CPF_VALIDO} cpf 11144477736"},
            {"url": f"https://x.test/{UUID_COM_CPF_VALIDO}/111.444.777-35"},
            {"url": f"https://x.test/{UUID_COM_CPF_VALIDO}-111.444.777-35"},
            {"url": "https://x.test/550e8400-e29b-41d4-a716-446655440000/111.444.777-35"},  # UUID termina em dígito
            {"despacho": f"{UUID_COM_CPF_VALIDO}111.444.777-35"},
        ],
    )
    def test_uuid_ao_lado_nao_esconde_o_cpf(self, corpo):
        assert achados_de_cpf(corpo)

    def test_cpf_em_outro_campo_do_mesmo_corpo(self):
        corpo = {"id": UUID_COM_CPF_VALIDO, "despacho": "111.444.777-35"}
        assert achados_de_cpf(corpo) == ["despacho"]

    @pytest.mark.parametrize("trecho", ["a123-12345678b", "a123-12345678abcd", "41d4-a123-12345678abcd"])
    def test_trecho_solto_de_uuid_continua_interrompendo(self, trecho):
        # Sem os cinco blocos não dá para dizer que é UUID. Interromper é o erro barato: não vaza.
        assert achados_de_cpf({"id": trecho}) == ["id"]


# ── Critério 4: requisição não gravada ──


class TestRequisicaoNaoGravada:
    def test_levanta_com_a_mensagem_da_spec(self, raiz):
        g = Gravacoes(raiz)
        with g.cliente_camara() as cliente, pytest.raises(RequisicaoNaoGravada) as erro:
            cliente._get("/proposicoes/123")
        assert str(erro.value) == "GET camara /proposicoes/123 {}"

    def test_e_assertion_error_para_passar_pelo_cliente(self):
        assert issubclass(RequisicaoNaoGravada, AssertionError)
        assert not issubclass(RequisicaoNaoGravada, httpx.HTTPError)

    def test_mensagem_traz_parametros(self, raiz):
        g = Gravacoes(raiz)
        with g.cliente_senado() as cliente, pytest.raises(RequisicaoNaoGravada) as erro:
            cliente._get("/processo", {"sigla": "PL", "ano": 2021})
        assert str(erro.value) == "GET senado /processo {'ano': '2021', 'sigla': 'PL'}"

    def test_acumula_mesmo_quando_o_chamador_engole_a_excecao(self, raiz):
        g = Gravacoes(raiz)
        with g.cliente_camara() as cliente:
            try:
                cliente._get("/proposicoes/123")
            except Exception:  # noqa: BLE001 — é o que os chamadores reais fazem
                pass
        assert g.nao_gravadas == ["GET camara /proposicoes/123 {}"]

    def test_parametros_diferentes_nao_casam(self, raiz):
        _pacote(raiz, "caso", _envelope("/proposicoes", {"dados": []}, params={"pagina": "1"}))
        g = Gravacoes(raiz).carregar("caso")
        with g.cliente_camara() as cliente, pytest.raises(RequisicaoNaoGravada):
            cliente._get("/proposicoes", {"pagina": 2})

    def test_fixture_reprova_o_teste_que_engoliu_a_excecao(self, tmp_path):
        """A prova de ponta a ponta: o teardown da fixture reprova, mesmo com o teste verde."""
        arquivo = tmp_path / "test_engolida.py"
        arquivo.write_text(
            "def test_engole(gravacoes):\n"
            "    with gravacoes.cliente_camara() as cliente:\n"
            "        try:\n"
            "            cliente._get('/proposicoes/123')\n"
            "        except Exception:\n"
            "            pass\n",
            encoding="utf-8",
        )
        ambiente = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
        resultado = subprocess.run(
            [
                sys.executable, "-m", "pytest", str(arquivo),
                "-p", "tests.conftest",
                f"--rootdir={tmp_path}", "-c", os.devnull, "-q",
            ],
            cwd=REPO_ROOT,
            env=ambiente,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert resultado.returncode == 1, resultado.stdout + resultado.stderr
        assert "1 passed" in resultado.stdout
        assert "1 error" in resultado.stdout
        assert "GET camara /proposicoes/123" in resultado.stdout

    def test_fixture_passa_sem_requisicao_perdida(self, gravacoes):
        assert isinstance(gravacoes, Gravacoes)
        assert gravacoes.nao_gravadas == []


# ── Critério 5: envelopes em sequência ──


class TestSequencia:
    def test_429_depois_200_servidos_em_ordem_e_o_ultimo_se_repete(self, raiz):
        _pacote(
            raiz,
            "caso",
            _envelope(
                "/proposicoes/1", {}, status=429,
                cabecalhos={"retry-after": "2", "content-type": "application/json"},
            ),
            _envelope("/proposicoes/1", {"dados": {"id": 1}}),
            sintetico=True,
        )
        g = Gravacoes(raiz).carregar("caso")
        with g.cliente_camara() as cliente:
            primeira = cliente.client.get("/proposicoes/1")
            segunda = cliente.client.get("/proposicoes/1")
            terceira = cliente.client.get("/proposicoes/1")
        assert [primeira.status_code, segunda.status_code, terceira.status_code] == [429, 200, 200]
        assert primeira.headers["retry-after"] == "2"
        assert terceira.json() == {"dados": {"id": 1}}

    def test_sequencias_de_requisicoes_diferentes_sao_independentes(self, raiz):
        _pacote(
            raiz,
            "caso",
            _envelope("/proposicoes/1", {"n": 1}),
            _envelope("/proposicoes/2", {"n": 2}),
            _envelope("/proposicoes/1", {"n": 3}),
        )
        g = Gravacoes(raiz).carregar("caso")
        with g.cliente_camara() as cliente:
            assert cliente._get("/proposicoes/2") == {"n": 2}
            assert cliente._get("/proposicoes/1") == {"n": 1}
            assert cliente._get("/proposicoes/1") == {"n": 3}

    def test_requisicoes_feitas_conta_as_repeticoes(self, raiz):
        _pacote(raiz, "caso", _envelope("/proposicoes", {"dados": []}, params={"pagina": "1"}))
        g = Gravacoes(raiz).carregar("caso")
        with g.cliente_camara() as cliente:
            cliente._get("/proposicoes", {"pagina": 1})
            cliente._get("/proposicoes", {"pagina": 1})
        assert g.requisicoes_feitas == [
            ("camara", "/proposicoes", {"pagina": "1"}),
            ("camara", "/proposicoes", {"pagina": "1"}),
        ]

    def test_requisicao_nao_gravada_tambem_conta_como_feita(self, raiz):
        g = Gravacoes(raiz)
        with g.cliente_camara() as cliente, pytest.raises(RequisicaoNaoGravada):
            cliente._get("/proposicoes/1")
        assert g.requisicoes_feitas == [("camara", "/proposicoes/1", {})]
        g.nao_gravadas.clear()


# ── Sintéticos: os pacotes escritos à mão, pelo cliente de produção ──


class TestSinteticos:
    def test_429_retry_after(self):
        g = Gravacoes().carregar("sinteticos/429-retry-after")
        with g.cliente_camara() as cliente:
            primeira = cliente.client.get("/proposicoes/900000429")
            assert primeira.status_code == 429
            assert primeira.headers["retry-after"] == "2"
            assert cliente._get("/proposicoes/900000429") == {"id": 900000429}

    def test_cliente_de_producao_atravessa_o_429(self):
        g = Gravacoes().carregar("sinteticos/429-retry-after")
        with g.cliente_camara() as cliente:
            assert cliente._get("/proposicoes/900000429") == {"id": 900000429}
        assert len(g.requisicoes_feitas) == 2

    def test_cliente_de_producao_atravessa_503_503_200(self):
        g = Gravacoes().carregar("sinteticos/503-sem-retry-after")
        with g.cliente_camara() as cliente:
            assert cliente._get("/proposicoes/900000503") == {"id": 900000503}
        assert len(g.requisicoes_feitas) == 3

    def test_500_persistente_nao_vira_sucesso(self):
        g = Gravacoes().carregar("sinteticos/500-persistente")
        with g.cliente_camara() as cliente:
            for _ in range(6):
                assert cliente.client.get("/proposicoes/900000500").status_code == 500
            with pytest.raises(httpx.HTTPStatusError):
                cliente._get("/proposicoes/900000500")

    def test_500_persistente_tem_cinco_envelopes(self):
        pacote = json.loads((RAIZ_FIXTURES / "sinteticos" / "500-persistente.json").read_text("utf-8"))
        assert [r["status"] for r in pacote["respostas"]] == [500] * 5

    def test_votacao_minima_aponta_para_o_pl_1264(self):
        g = Gravacoes().carregar("sinteticos/votacao-minima")
        with g.cliente_camara() as cliente:
            detalhe = cliente.obter_votacao_detalhes("900000000-1")
            assert detalhe["proposicaoPrincipal"]["id"] == 2426923
            assert cliente.obter_votos("900000000-1") == []
            assert cliente.obter_votacao_orientacoes("900000000-1") == []


# ── Critérios 2 e 7: o que está versionado ──


def _arquivos_de_pacote() -> list[Path]:
    return sorted(
        p
        for pasta in ("gravacoes", "sinteticos", "candidatos")
        for p in (RAIZ_FIXTURES / pasta).glob("*.json")
    )


def _casos() -> list[dict]:
    return yaml.safe_load((RAIZ_FIXTURES / "casos.yml").read_text("utf-8"))["casos"]


class TestPacotesVersionados:
    def test_ha_pacotes_para_conferir(self):
        assert len(_arquivos_de_pacote()) > 4

    @pytest.mark.parametrize("arquivo", _arquivos_de_pacote(), ids=lambda p: p.name)
    def test_formato_status_e_hash(self, arquivo):
        pacote = json.loads(arquivo.read_text("utf-8"))
        assert pacote["formato"] == 1
        sintetico = pacote["sintetico"]
        assert isinstance(sintetico, bool)
        # Só os escritos à mão, no diretório deles, se declaram sintéticos.
        assert sintetico == (arquivo.parent.name == "sinteticos")
        if not sintetico:
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-03:00", pacote["gravado_em"])
        assert pacote["respostas"]
        for resposta in pacote["respostas"]:
            assert resposta["host"] in {"camara", "senado"}
            assert resposta["metodo"] == "GET"
            assert all(isinstance(v, str) for v in resposta["params"].values())
            if not sintetico:
                assert resposta["status"] == 200, resposta["caminho"]
            assert resposta["sha256_corpo"] == hash_corpo(resposta["corpo"]), resposta["caminho"]

    def test_todo_caso_do_yml_tem_pacote(self):
        faltando = [c["slug"] for c in _casos() if not (RAIZ_GRAVACOES / f"{c['slug']}.json").exists()]
        assert faltando == []

    def test_lista_de_casos_tem_18_e_a_janela(self):
        casos = _casos()
        assert sum(c["receita"] != "janela" for c in casos) == 18
        assert [c["slug"] for c in casos if c["receita"] == "janela"] == ["janela-d7"]

    def test_casos_tem_hoje_preenchido_e_esperado_nulo(self):
        for caso in _casos():
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(caso["hoje"])), caso["slug"]
            assert caso["esperado"] is None, caso["slug"]  # TRM-025 preenche

    def test_nao_ha_pacote_orfao(self):
        slugs = {c["slug"] for c in _casos()}
        orfaos = [
            p.name
            for p in RAIZ_GRAVACOES.glob("*.json")
            if p.name.split(".parte-")[0].removesuffix(".json") not in slugs
        ]
        assert orfaos == []

    @pytest.mark.parametrize("arquivo", _arquivos_de_pacote(), ids=lambda p: p.name)
    def test_nenhum_cpf_foi_versionado(self, arquivo):
        """Nem CPF, nem outro campo de `CAMPOS_REMOVIDOS` com valor. O relatório só traz caminhos."""
        # Varre o `corpo`, não o texto do arquivo: `sha256_corpo` tem sequências de 11 dígitos.
        achados = {}
        for resposta in json.loads(arquivo.read_text("utf-8"))["respostas"]:
            onde = f"{resposta['host']} {resposta['caminho']}"
            copia = copy.deepcopy(resposta["corpo"])
            removiveis = _remover_campos(copia)
            problemas = achados_de_cpf(resposta["corpo"])
            # Se a remoção muda o corpo, algum campo ainda estava com valor.
            if copia != resposta["corpo"]:
                problemas.append(f"campo com valor em {removiveis}")
            if removiveis != resposta.get("campos_removidos", []):
                problemas.append(f"campos_removidos não fecha com {removiveis}")
            if problemas:
                achados[onde] = problemas
        assert achados == {}

    def test_deputados_versionados_perderam_so_os_campos_da_lista(self):
        vistos = 0
        for arquivo in RAIZ_GRAVACOES.glob("*.json"):
            for resposta in json.loads(arquivo.read_text("utf-8"))["respostas"]:
                if not resposta["caminho"].startswith("/deputados/"):
                    continue
                vistos += 1
                dados = resposta["corpo"]["dados"]
                gabinete = dados["ultimoStatus"].get("gabinete") or {}
                onde = resposta["caminho"]
                assert dados["nomeCivil"] and dados["nomeCivil"] != VALOR_REMOVIDO, onde
                assert VALOR_REMOVIDO not in (gabinete.get("email"), gabinete.get("telefone")), onde
                assert sorted(resposta["campos_removidos"]) == [
                    "dados.cpf", "dados.dataNascimento", "dados.municipioNascimento", "dados.ufNascimento",
                ], onde
        assert vistos == 13

    @pytest.mark.parametrize("caso", _casos(), ids=lambda c: c["slug"])
    def test_pacote_real_passa_inteiro_pelo_replay(self, caso):
        slug = caso["slug"]
        g = Gravacoes().carregar(slug)
        envelopes = g._respostas_do_pacote(slug)
        assert envelopes

        for envelope in envelopes:
            assert envelope["sha256_corpo"] == hash_corpo(envelope["corpo"]), envelope["caminho"]

        # Sequência das partes: tudo o que está em disco foi declarado e entra na ordem.
        arquivos = sorted(RAIZ_GRAVACOES.glob(f"{slug}.parte-*.json"))
        cabeca = json.loads((RAIZ_GRAVACOES / f"{slug}.json").read_text("utf-8"))
        assert cabeca.get("partes", 1) == len(arquivos) + 1
        lidos = [cabeca] + [json.loads(a.read_text("utf-8")) for a in arquivos]
        if len(lidos) > 1:
            assert [p["parte"] for p in lidos] == list(range(1, len(lidos) + 1))
        assert {p["caso"] for p in lidos} == {slug}
        assert {p["gravado_em"] for p in lidos} == {cabeca["gravado_em"]}
        assert [e for p in lidos for e in p["respostas"]] == envelopes

        # A receita pede exatamente o que está gravado: nada falta, nada sobra.
        with g.cliente_camara() as camara, g.cliente_senado() as senado:
            executar_receita(Receitas(camara, senado, date.fromisoformat(caso["hoje"])), caso)
        assert g.nao_gravadas == []
        assert sorted(map(repr, g.requisicoes_feitas)) == sorted(
            repr((e["host"], e["caminho"], e["params"])) for e in envelopes
        )

    def test_janela_versionada_esta_completa(self):
        g = Gravacoes()
        envelopes = g.carregar("janela-d7")._respostas_do_pacote("janela-d7")
        conferir_janela_completa(envelopes)
        assert [e["params"]["pagina"] for e in envelopes] == [str(n) for n in range(1, len(envelopes) + 1)]

    def test_total_dentro_do_limite(self):
        total = sum(p.stat().st_size for p in RAIZ_FIXTURES.rglob("*") if p.is_file())
        assert total <= LIMITE_FIXTURES

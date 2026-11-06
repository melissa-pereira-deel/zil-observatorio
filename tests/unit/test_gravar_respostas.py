"""Gravador de respostas (TRM-002): tudo por transporte falso, nada toca a rede."""

import json
import re
from datetime import date
from email.utils import parsedate_to_datetime

import httpx
import pytest
import yaml

from scripts import gravar_respostas as gr
from tests.replay import VALOR_REMOVIDO, Gravacoes, hash_corpo

CAMARA = "https://dadosabertos.camara.leg.br/api/v2"
CAMPOS_DE_NASCIMENTO = ("dataNascimento", "municipioNascimento", "ufNascimento")


@pytest.fixture(autouse=True)
def _sem_espera(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _s: None)


class Relogio:
    """Relógio que só anda quando alguém dorme: prova as esperas sem esperar."""

    def __init__(self):
        self.t = 100.0
        self.dormidas = []

    def agora(self):
        return self.t

    def dormir(self, segundos):
        self.dormidas.append(segundos)
        self.t += segundos




def _fonte(rotas, chamadas=None):
    """Transporte falso a partir de {caminho completo: resposta | lista de respostas}."""
    rotas = {k: (list(v) if isinstance(v, list) else v) for k, v in rotas.items()}

    def responder(request):
        chave = request.url.path
        if chamadas is not None:
            chamadas.append((chave, dict(request.url.params)))
        rota = rotas.get(chave)
        if rota is None:
            return httpx.Response(404, json={"erro": chave})
        if isinstance(rota, list):
            rota = rota.pop(0) if len(rota) > 1 else rota[0]
        return rota(request) if callable(rota) else rota

    return httpx.MockTransport(responder)


def _ok(corpo, **cabecalhos):
    return httpx.Response(200, json=corpo, headers=cabecalhos)


def _proposicao(pid, *, principal=None, relator=None, orgao=4, situacao=1140):
    base = f"{CAMARA}"
    return {
        f"/api/v2/proposicoes/{pid}": _ok({"dados": {
            "id": pid,
            "uriPropPrincipal": f"{base}/proposicoes/{principal}" if principal else None,
            "statusProposicao": {
                "uriOrgao": f"{base}/orgaos/{orgao}",
                "uriUltimoRelator": f"{base}/deputados/{relator}" if relator else None,
                "codSituacao": situacao,
            },
        }}),
        f"/api/v2/proposicoes/{pid}/tramitacoes": _ok({"dados": [
            {"sequencia": 1, "uriOrgao": f"{base}/orgaos/{orgao}"},
            {"sequencia": 2, "uriOrgao": f"{base}/orgaos/180"},
            {"sequencia": 3, "uriOrgao": f"{base}/orgaos/180"},
        ]}),
        f"/api/v2/proposicoes/{pid}/autores": _ok({"dados": []}),
        f"/api/v2/proposicoes/{pid}/relacionadas": _ok({"dados": []}),
    }


@pytest.fixture
def raiz(tmp_path):
    """Árvore de fixtures isolada, com um casos.yml mínimo."""
    raiz = tmp_path / "tramitacao"
    (raiz / "gravacoes").mkdir(parents=True)
    (raiz / "casos.yml").write_text(
        yaml.safe_dump({"casos": [
            {"slug": "pl-1", "casa": "camara", "fonte_id": "1", "rotulo": "PL 1", "por_que": "x",
             "receita": "proposicao_completa", "hoje": None, "esperado": None},
            {"slug": "pl-2", "casa": "camara", "fonte_id": "2", "rotulo": "PL 2", "por_que": "y",
             "receita": "proposicao_completa", "hoje": None, "esperado": None},
        ]}),
        encoding="utf-8",
    )
    return raiz


def _fonte_dos_dois_casos(**extra):
    return _fonte({
        **_proposicao(1),
        **_proposicao(2),
        "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
        "/api/v2/orgaos/180": _ok({"dados": {"id": 180}}),
        **extra,
    })


def _ler(raiz, slug):
    return json.loads((raiz / "gravacoes" / f"{slug}.json").read_text("utf-8"))


# ── TransporteGravador ──


class TestTransporteGravador:
    def _gravador(self, rotas, relogio=None, **kw):
        relogio = relogio or Relogio()
        return gr.TransporteGravador(
            _fonte(rotas), dormir=relogio.dormir, agora=relogio.agora, **kw
        ), relogio

    def test_grava_corpo_cabecalhos_host_e_caminho_sem_prefixo(self):
        gravador, _ = self._gravador({
            "/api/v2/proposicoes": _ok({"dados": []}, **{"x-total-count": "0", "retry-after": "30"}),
        })
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente:
            cliente.get("/proposicoes", params={"itens": 100, "siglaTipo": "PL,PEC"})
        [envelope] = gravador.respostas
        assert envelope["host"] == "camara"
        assert envelope["metodo"] == "GET"
        assert envelope["caminho"] == "/proposicoes"
        assert envelope["params"] == {"itens": "100", "siglaTipo": "PL,PEC"}
        assert envelope["status"] == 200
        assert envelope["corpo"] == {"dados": []}
        assert envelope["cabecalhos"] == {
            "x-total-count": "0",
            "link": None,
            "retry-after": "30",
            "content-type": "application/json",
        }
        assert envelope["sha256_corpo"] == hash_corpo({"dados": []})

    def test_host_do_senado(self):
        gravador, _ = self._gravador({"/dadosabertos/processo/1": _ok({"id": 1})})
        with httpx.Client(transport=gravador, base_url="https://legis.senado.leg.br/dadosabertos") as cliente:
            cliente.get("/processo/1")
        assert gravador.respostas[0]["host"] == "senado"
        assert gravador.respostas[0]["caminho"] == "/processo/1"

    def test_respeita_retry_after_em_segundos_e_nao_grava_o_429(self):
        gravador, relogio = self._gravador({"/api/v2/x": [
            httpx.Response(429, headers={"retry-after": "7"}),
            _ok({"dados": 1}),
        ]})
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente:
            assert cliente.get("/x").status_code == 200
        assert 7 in relogio.dormidas
        assert [r["status"] for r in gravador.respostas] == [200]

    def test_retry_after_de_uma_resposta_200_nao_faz_esperar(self):
        # A Câmara manda `retry-after: 30` em toda resposta 200.
        gravador, relogio = self._gravador({"/api/v2/x": _ok({"dados": 1}, **{"retry-after": "30"})})
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente:
            cliente.get("/x")
        assert relogio.dormidas == []

    def test_retry_after_em_data_http(self):
        data_http = "Wed, 21 Oct 2026 07:28:00 GMT"
        instante = parsedate_to_datetime(data_http).timestamp()
        assert gr.segundos_retry_after(data_http, agora_utc=instante - 10) == 10
        assert gr.segundos_retry_after(data_http, agora_utc=instante + 10) == 0
        assert gr.segundos_retry_after("30") == 30
        assert gr.segundos_retry_after("lixo") is None
        assert gr.segundos_retry_after(None) is None

    def test_503_sem_retry_after_recua_e_tenta_de_novo(self):
        gravador, relogio = self._gravador({"/api/v2/x": [
            httpx.Response(503), httpx.Response(503), _ok({"dados": 1}),
        ]})
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente:
            assert cliente.get("/x").status_code == 200
        assert len(relogio.dormidas) == 2
        assert relogio.dormidas[1] > relogio.dormidas[0]

    def test_erro_persistente_interrompe_em_vez_de_insistir(self):
        chamadas = []
        relogio = Relogio()
        gravador = gr.TransporteGravador(
            _fonte({"/api/v2/x": httpx.Response(500)}, chamadas),
            dormir=relogio.dormir, agora=relogio.agora, tentativas=3,
        )
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente, pytest.raises(gr.GravacaoInterrompida):
            cliente.get("/x")
        assert len(chamadas) == 3
        assert gravador.respostas == []

    def test_retry_after_acima_do_teto_interrompe_sem_martelar(self):
        chamadas = []
        relogio = Relogio()
        gravador = gr.TransporteGravador(
            _fonte({"/api/v2/x": httpx.Response(429, headers={"retry-after": "3600"})}, chamadas),
            dormir=relogio.dormir, agora=relogio.agora,
        )
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente, pytest.raises(gr.GravacaoInterrompida, match="3600"):
            cliente.get("/x")
        assert len(chamadas) == 1
        assert relogio.dormidas == []

    def test_mantem_intervalo_entre_chamadas(self):
        gravador, relogio = self._gravador({"/api/v2/x": _ok({"dados": 1})})
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente:
            cliente.get("/x")
            cliente.get("/x")
            cliente.get("/x")
        assert relogio.dormidas == [0.5, 0.5]

    def test_404_nao_entra_no_pacote_e_fica_registrado(self):
        gravador, _ = self._gravador({})
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente:
            assert cliente.get("/orgaos/9").status_code == 404
        assert gravador.respostas == []
        assert gravador.ausentes == [{"host": "camara", "caminho": "/orgaos/9", "params": {}, "status": 404}]

    def test_cpf_do_deputado_nao_vai_para_o_pacote_mas_vai_para_o_cliente(self):
        corpo = {"dados": {"id": 5, "cpf": "12345678901", "nomeCivil": "Fulana"}}
        gravador, _ = self._gravador({"/api/v2/deputados/5": _ok(corpo)})
        with httpx.Client(transport=gravador, base_url=CAMARA) as cliente:
            assert cliente.get("/deputados/5").json()["dados"]["cpf"] == "12345678901"
        [envelope] = gravador.respostas
        assert envelope["corpo"]["dados"]["cpf"] == VALOR_REMOVIDO
        assert envelope["corpo"]["dados"]["nomeCivil"] == "Fulana"
        assert envelope["campos_removidos"] == ["dados.cpf"]
        assert envelope["sha256_corpo"] == hash_corpo(envelope["corpo"])
        assert "12345678901" not in json.dumps(envelope)


# ── Proteção do CPF ──


class TestProtecaoDoCpf:
    def _gravar(self, caminho, corpo, base_url=CAMARA, prefixo="/api/v2"):
        relogio = Relogio()
        gravador = gr.TransporteGravador(
            _fonte({prefixo + caminho: _ok(corpo)}), dormir=relogio.dormir, agora=relogio.agora
        )
        with httpx.Client(transport=gravador, base_url=base_url) as cliente:
            cliente.get(caminho)
        return gravador

    @pytest.mark.parametrize(
        ("caminho", "corpo", "removido"),
        [
            ("/deputados/5", {"dados": {"cpf": "111 444 777 35"}}, "dados.cpf"),
            ("/deputados/5", {"dados": {"ultimoStatus": {"cpf": "11144477735"}}}, "dados.ultimoStatus.cpf"),
            ("/deputados/5", {"dados": {"numeroCPF": "11144477735"}}, "dados.numeroCPF"),
            ("/proposicoes/1/autores", {"dados": [{"nome": "x", "Cpf": "11144477735"}]}, "dados[0].Cpf"),
            ("/orgaos/4", {"dados": {"responsavel": {"cpfResponsavel": 11144477735}}}, "dados.responsavel.cpfResponsavel"),
        ],
    )
    def test_chave_com_cpf_em_qualquer_lugar_e_removida(self, caminho, corpo, removido):
        [envelope] = self._gravar(caminho, corpo).respostas
        assert envelope["campos_removidos"] == [removido]
        assert "11144477735" not in json.dumps(envelope)
        assert "111 444" not in json.dumps(envelope)
        assert VALOR_REMOVIDO in json.dumps(envelope, ensure_ascii=False)
        assert envelope["sha256_corpo"] == hash_corpo(envelope["corpo"])

    def test_chave_com_cpf_no_senado_tambem_e_removida(self):
        [envelope] = self._gravar(
            "/processo/1", {"autor": {"cpf": "11144477735"}}, "https://legis.senado.leg.br/dadosabertos", "/dadosabertos"
        ).respostas
        assert envelope["campos_removidos"] == ["autor.cpf"]

    @pytest.mark.parametrize(
        "corpo",
        [
            {"dados": [{"despacho": "Requerente de CPF 111.444.777-35, conforme ofício."}]},
            {"dados": {"documento": "11144477735"}},
            {"dados": {"documento": 11144477735}},
            {"dados": {"observacao": "111 444 777 35"}},
            {"dados": {"111.444.777-35": 1}},
        ],
    )
    def test_valor_com_forma_de_cpf_interrompe_sem_expor_o_valor(self, corpo):
        with pytest.raises(gr.GravacaoInterrompida) as erro:
            self._gravar("/proposicoes/1/tramitacoes", corpo)
        mensagem = str(erro.value)
        assert "/proposicoes/1/tramitacoes" in mensagem
        assert "dados" in mensagem
        assert not re.search(r"\d{3}\D?\d{3}\D?\d{3}", mensagem)

    def test_interrupcao_nao_grava_pacote_e_sai_com_1(self, raiz, capsys):
        arquivo = raiz / "gravacoes" / "pl-1.json"
        arquivo.write_text('{"anterior": true}', encoding="utf-8")
        rotas = {
            **_proposicao(1),
            "/api/v2/proposicoes/1/autores": _ok({"dados": [{"nome": "Fulana 111.444.777-35"}]}),
            "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
            "/api/v2/orgaos/180": _ok({"dados": {"id": 180}}),
        }
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte(rotas), raiz=raiz) == 1
        saida = capsys.readouterr()
        assert "dados[0].nome" in saida.err
        assert "444.777" not in saida.err + saida.out
        assert json.loads(arquivo.read_text("utf-8")) == {"anterior": True}

    def test_ids_nao_interrompem(self):
        corpo = {"dados": {"id": 2269745, "codigo": "11144477736", "uri": f"{CAMARA}/proposicoes/2269745"}}
        [envelope] = self._gravar("/proposicoes/2269745", corpo).respostas
        assert envelope["corpo"] == corpo
        assert "campos_removidos" not in envelope

    @pytest.mark.parametrize("campo", CAMPOS_DE_NASCIMENTO)
    def test_campo_de_nascimento_sai_do_pacote_no_deputado(self, campo):
        [envelope] = self._gravar("/deputados/5", {"dados": {campo: "valor ficticio"}}).respostas
        assert envelope["corpo"]["dados"][campo] == VALOR_REMOVIDO
        assert envelope["campos_removidos"] == [f"dados.{campo}"]
        assert "valor ficticio" not in json.dumps(envelope)
        assert envelope["sha256_corpo"] == hash_corpo(envelope["corpo"])

    @pytest.mark.parametrize("campo", CAMPOS_DE_NASCIMENTO)
    def test_campo_de_nascimento_sai_em_qualquer_nivel_e_endpoint(self, campo):
        corpo = {"dados": [{"autor": {campo.upper(): "valor ficticio"}}]}
        [envelope] = self._gravar("/proposicoes/1/autores", corpo).respostas
        assert envelope["campos_removidos"] == [f"dados[0].autor.{campo.upper()}"]
        assert "valor ficticio" not in json.dumps(envelope)

    def test_campo_de_nascimento_vazio_fica_como_veio(self):
        corpo = {"dados": dict.fromkeys(CAMPOS_DE_NASCIMENTO)}
        [envelope] = self._gravar("/deputados/5", corpo).respostas
        assert envelope["corpo"] == corpo
        assert "campos_removidos" not in envelope

    def test_nome_civil_e_contato_de_gabinete_ficam(self):
        corpo = {
            "dados": {
                "nomeCivil": "Fulana de Tal",
                "ultimoStatus": {"gabinete": {"email": "gabinete@camara.test", "telefone": "3215-0000"}},
            }
        }
        [envelope] = self._gravar("/deputados/5", corpo).respostas
        assert envelope["corpo"] == corpo
        assert "campos_removidos" not in envelope

    def test_lista_de_campos_removidos_se_estende_em_um_lugar(self, monkeypatch):
        monkeypatch.setattr(gr, "CAMPOS_REMOVIDOS", (*gr.CAMPOS_REMOVIDOS, re.compile(r"^sexo$")))
        [envelope] = self._gravar("/deputados/5", {"dados": {"sexo": "x", "cpf": "1"}}).respostas
        assert envelope["campos_removidos"] == ["dados.sexo", "dados.cpf"]
        assert envelope["corpo"]["dados"]["sexo"] == VALOR_REMOVIDO


# ── Janela completa ──


class TestJanelaCompleta:
    @pytest.fixture
    def raiz_janela(self, raiz):
        (raiz / "casos.yml").write_text(yaml.safe_dump({"casos": [
            {"slug": "janela-d7", "casa": "camara", "fonte_id": None, "rotulo": "j", "por_que": "j",
             "receita": "janela", "hoje": None, "esperado": None},
        ]}), encoding="utf-8")
        return raiz

    def _fonte(self, *, total, paginas, por_pagina=100):
        def responder(request):
            pagina = int(request.url.params["pagina"])
            itens = [{"id": pagina * 1000 + i} for i in range(por_pagina)] if pagina <= paginas else []
            cabecalhos = {"x-total-count": str(total)} if total is not None else {}
            return httpx.Response(200, json={"dados": itens}, headers=cabecalhos)

        return httpx.MockTransport(responder)

    def test_truncada_em_50_paginas_sai_com_1_e_nao_grava(self, raiz_janela, capsys):
        fonte = self._fonte(total=6000, paginas=60)
        assert gr.main(["--caso", "janela-d7"], transporte_base=fonte, raiz=raiz_janela) == 1
        erro = capsys.readouterr().err
        assert "5000" in erro and "6000" in erro
        assert not list((raiz_janela / "gravacoes").glob("janela-d7*"))

    def test_sem_total_e_no_limite_de_paginas_tambem_sai_com_1(self, raiz_janela, capsys):
        fonte = self._fonte(total=None, paginas=60)
        assert gr.main(["--caso", "janela-d7"], transporte_base=fonte, raiz=raiz_janela) == 1
        assert "50" in capsys.readouterr().err
        assert not list((raiz_janela / "gravacoes").glob("janela-d7*"))

    def test_regravar_truncada_nao_apaga_o_pacote_anterior(self, raiz_janela):
        arquivo = raiz_janela / "gravacoes" / "janela-d7.json"
        arquivo.write_text('{"anterior": true}', encoding="utf-8")
        assert gr.main(["--caso", "janela-d7"], transporte_base=self._fonte(total=6000, paginas=60), raiz=raiz_janela) == 1
        assert json.loads(arquivo.read_text("utf-8")) == {"anterior": True}

    def test_total_diferente_do_coletado_sai_com_1(self, raiz_janela):
        fonte = self._fonte(total=250, paginas=2)
        assert gr.main(["--caso", "janela-d7"], transporte_base=fonte, raiz=raiz_janela) == 1

    def test_completa_grava(self, raiz_janela):
        def responder(request):
            pagina = int(request.url.params["pagina"])
            quantos = {1: 100, 2: 100, 3: 50}[pagina]
            return httpx.Response(200, json={"dados": [{"id": i} for i in range(quantos)]}, headers={"x-total-count": "250"})

        fonte = httpx.MockTransport(responder)
        assert gr.main(["--caso", "janela-d7"], transporte_base=fonte, raiz=raiz_janela) == 0
        assert (raiz_janela / "gravacoes" / "janela-d7.json").exists()

    def test_completa_com_ultima_pagina_vazia_grava(self, raiz_janela):
        fonte = self._fonte(total=200, paginas=2)
        assert gr.main(["--caso", "janela-d7"], transporte_base=fonte, raiz=raiz_janela) == 0


# ── Receitas e pacote ──


class TestReceitas:
    def test_proposicao_completa_busca_cada_orgao_uma_vez_e_o_relator(self, raiz):
        chamadas = []
        fonte = _fonte({
            **_proposicao(1, relator=77),
            "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
            "/api/v2/orgaos/180": _ok({"dados": {"id": 180}}),
            "/api/v2/deputados/77": _ok({"dados": {"id": 77}}),
        }, chamadas)
        assert gr.main(["--caso", "pl-1"], transporte_base=fonte, raiz=raiz) == 0
        assert [c[0] for c in chamadas] == [
            "/api/v2/proposicoes/1",
            "/api/v2/proposicoes/1/tramitacoes",
            "/api/v2/proposicoes/1/autores",
            "/api/v2/proposicoes/1/relacionadas",
            "/api/v2/orgaos/4",
            "/api/v2/orgaos/180",
            "/api/v2/deputados/77",
        ]
        pacote = _ler(raiz, "pl-1")
        assert pacote["caso"] == "pl-1"
        assert pacote["formato"] == 1
        assert pacote["sintetico"] is False
        assert pacote["gravado_em"].endswith("-03:00")
        assert len(pacote["respostas"]) == 7

    def test_sem_relator_nao_busca_deputado(self, raiz):
        chamadas = []
        fonte = _fonte({
            **_proposicao(1),
            "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
            "/api/v2/orgaos/180": _ok({"dados": {"id": 180}}),
        }, chamadas)
        assert gr.main(["--caso", "pl-1"], transporte_base=fonte, raiz=raiz) == 0
        assert not [c for c in chamadas if "/deputados/" in c[0]]

    def test_cadeia_segue_a_principal_e_nao_repete_orgao(self, raiz):
        (raiz / "casos.yml").write_text(yaml.safe_dump({"casos": [
            {"slug": "elo", "casa": "camara", "fonte_id": "1", "rotulo": "PL 1", "por_que": "x",
             "receita": "proposicao_com_cadeia", "hoje": None, "esperado": None},
        ]}), encoding="utf-8")
        chamadas = []
        fonte = _fonte({
            **_proposicao(1, principal=2),
            **_proposicao(2, principal=3),
            **_proposicao(3),
            "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
            "/api/v2/orgaos/180": _ok({"dados": {"id": 180}}),
        }, chamadas)
        assert gr.main(["--caso", "elo"], transporte_base=fonte, raiz=raiz) == 0
        caminhos = [c[0] for c in chamadas]
        assert {f"/api/v2/proposicoes/{i}" for i in (1, 2, 3)} <= set(caminhos)
        assert caminhos.count("/api/v2/orgaos/180") == 1

    def test_cadeia_para_em_dez_niveis_e_em_ciclo(self, raiz):
        (raiz / "casos.yml").write_text(yaml.safe_dump({"casos": [
            {"slug": "elo", "casa": "camara", "fonte_id": "1", "rotulo": "x", "por_que": "x",
             "receita": "proposicao_com_cadeia", "hoje": None, "esperado": None},
        ]}), encoding="utf-8")
        rotas = {"/api/v2/orgaos/4": _ok({"dados": {"id": 4}}), "/api/v2/orgaos/180": _ok({"dados": {"id": 180}})}
        for i in range(1, 15):
            rotas.update(_proposicao(i, principal=i + 1))
        chamadas = []
        assert gr.main(["--caso", "elo"], transporte_base=_fonte(rotas, chamadas), raiz=raiz) == 0
        detalhes = [c[0] for c in chamadas if c[0].count("/") == 4 and "/proposicoes/" in c[0]]
        assert len(detalhes) == 11  # o caso e dez elos

    def test_janela_percorre_todas_as_paginas_com_os_parametros_da_spec(self, raiz):
        (raiz / "casos.yml").write_text(yaml.safe_dump({"casos": [
            {"slug": "janela-d7", "casa": "camara", "fonte_id": None, "rotulo": "j", "por_que": "j",
             "receita": "janela", "hoje": None, "esperado": None},
        ]}), encoding="utf-8")
        paginas = {"1": [{"id": i} for i in range(100)], "2": [{"id": 100}]}
        chamadas = []

        def responder(request):
            params = dict(request.url.params)
            chamadas.append(params)
            return httpx.Response(200, json={"dados": paginas[params["pagina"]]})

        assert gr.main(
            ["--caso", "janela-d7"],
            transporte_base=httpx.MockTransport(responder),
            raiz=raiz,
            hoje=date(2026, 11, 5),
        ) == 0
        assert chamadas[0] == {
            "dataInicio": "2026-10-29",
            "dataFim": "2026-11-05",
            "siglaTipo": "PL,PLP,PEC,MPV,PDL",
            "itens": "100",
            "ordem": "ASC",
            "ordenarPor": "id",
            "pagina": "1",
        }
        assert [c["pagina"] for c in chamadas] == ["1", "2"]
        g = Gravacoes(raiz / "gravacoes").carregar("janela-d7")
        assert g.corpo("janela-d7", "/proposicoes", chamadas[1]) == {"dados": [{"id": 100}]}

    def test_senado_processo_acrescenta_lista_e_detalhe(self, raiz):
        (raiz / "casos.yml").write_text(yaml.safe_dump({"casos": [
            {"slug": "pl-1", "casa": "camara", "fonte_id": "1", "rotulo": "x", "por_que": "x",
             "receita": "proposicao_completa", "senado": {"sigla": "PL", "numero": 1, "ano": 2024},
             "hoje": None, "esperado": None},
        ]}), encoding="utf-8")
        chamadas = []
        fonte = _fonte({
            **_proposicao(1),
            "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
            "/api/v2/orgaos/180": _ok({"dados": {"id": 180}}),
            "/dadosabertos/processo": _ok([{"id": 8638658}, {"id": 8638659}]),
            "/dadosabertos/processo/8638658": _ok({"id": 8638658}),
            "/dadosabertos/processo/8638659": _ok({"id": 8638659}),
        }, chamadas)
        assert gr.main(["--caso", "pl-1"], transporte_base=fonte, raiz=raiz) == 0
        senado = [r for r in _ler(raiz, "pl-1")["respostas"] if r["host"] == "senado"]
        assert [(r["caminho"], r["params"]) for r in senado] == [
            ("/processo", {"sigla": "PL", "numero": "1", "ano": "2024"}),
            ("/processo/8638658", {}),
            ("/processo/8638659", {}),
        ]

    def test_receita_desconhecida_sai_com_erro(self, raiz, capsys):
        (raiz / "casos.yml").write_text(yaml.safe_dump({"casos": [
            {"slug": "pl-1", "casa": "camara", "fonte_id": "1", "receita": "materia", "hoje": None},
        ]}), encoding="utf-8")
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte({}), raiz=raiz) == 1
        assert "materia" in capsys.readouterr().err


# ── Linha de comando ──


class TestLinhaDeComando:
    def test_caso_regrava_so_o_pedido_e_preenche_hoje(self, raiz):
        assert gr.main(
            ["--caso", "pl-1"], transporte_base=_fonte_dos_dois_casos(), raiz=raiz, hoje=date(2026, 11, 5)
        ) == 0
        assert (raiz / "gravacoes" / "pl-1.json").exists()
        assert not (raiz / "gravacoes" / "pl-2.json").exists()
        casos = {c["slug"]: c for c in yaml.safe_load((raiz / "casos.yml").read_text("utf-8"))["casos"]}
        assert str(casos["pl-1"]["hoje"]) == "2026-11-05"
        assert casos["pl-2"]["hoje"] is None
        assert casos["pl-1"]["esperado"] is None

    def test_todos_regrava_todos(self, raiz):
        assert gr.main(["--todos"], transporte_base=_fonte_dos_dois_casos(), raiz=raiz) == 0
        assert (raiz / "gravacoes" / "pl-1.json").exists()
        assert (raiz / "gravacoes" / "pl-2.json").exists()

    def test_sem_rede_sai_com_1_mensagem_clara_e_nao_mexe_no_pacote(self, raiz, capsys):
        arquivo = raiz / "gravacoes" / "pl-1.json"
        arquivo.write_text('{"anterior": true}', encoding="utf-8")

        def sem_rede(request):
            raise httpx.ConnectError("sem rota", request=request)

        assert gr.main(["--caso", "pl-1"], transporte_base=httpx.MockTransport(sem_rede), raiz=raiz) == 1
        assert "sem acesso à rede" in capsys.readouterr().err.lower()
        assert json.loads(arquivo.read_text("utf-8")) == {"anterior": True}

    def test_sem_rede_em_todos_para_no_primeiro(self, raiz, capsys):
        chamadas = []

        def sem_rede(request):
            chamadas.append(request.url.path)
            raise httpx.ConnectError("sem rota", request=request)

        assert gr.main(["--todos"], transporte_base=httpx.MockTransport(sem_rede), raiz=raiz) == 1
        assert not [c for c in chamadas if "/proposicoes/2" in c]

    def test_interrompida_sai_com_1(self, raiz, capsys):
        fonte = _fonte({"/api/v2/proposicoes/1": httpx.Response(429, headers={"retry-after": "3600"})})
        assert gr.main(["--caso", "pl-1"], transporte_base=fonte, raiz=raiz) == 1
        assert "3600" in capsys.readouterr().err
        assert not (raiz / "gravacoes" / "pl-1.json").exists()

    def test_caso_inexistente_sai_com_1(self, raiz, capsys):
        assert gr.main(["--caso", "nao-existe"], transporte_base=_fonte({}), raiz=raiz) == 1
        assert "nao-existe" in capsys.readouterr().err

    def test_exige_caso_ou_todos(self, raiz):
        with pytest.raises(SystemExit) as erro:
            gr.main([], transporte_base=_fonte({}), raiz=raiz)
        assert erro.value.code == 2

    def test_candidato_grava_em_candidatos_sem_tocar_em_casos_yml(self, raiz):
        antes = (raiz / "casos.yml").read_text("utf-8")
        fonte = _fonte({
            **_proposicao(1),
            "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
            "/api/v2/orgaos/180": _ok({"dados": {"id": 180}}),
        })
        assert gr.main(["--caso", "candidatos/1", "--fonte-id", "1"], transporte_base=fonte, raiz=raiz) == 0
        pacote = json.loads((raiz / "candidatos" / "1.json").read_text("utf-8"))
        assert pacote["caso"] == "candidatos/1"
        assert (raiz / "casos.yml").read_text("utf-8") == antes
        assert Gravacoes(raiz / "gravacoes").carregar("candidatos/1").corpo(
            "candidatos/1", "/proposicoes/1"
        )["dados"]["id"] == 1

    def test_candidato_exige_fonte_id(self, raiz, capsys):
        assert gr.main(["--caso", "candidatos/1"], transporte_base=_fonte({}), raiz=raiz) == 1
        assert "--fonte-id" in capsys.readouterr().err

    def test_404_na_fonte_avisa_e_registra_no_pacote(self, raiz, capsys):
        fonte = _fonte({**_proposicao(1), "/api/v2/orgaos/4": _ok({"dados": {"id": 4}})})
        assert gr.main(["--caso", "pl-1"], transporte_base=fonte, raiz=raiz) == 0
        pacote = _ler(raiz, "pl-1")
        assert pacote["ausentes_na_fonte"] == [
            {"host": "camara", "caminho": "/orgaos/180", "params": {}, "status": 404}
        ]
        assert "/orgaos/180" in capsys.readouterr().err

    def test_404_no_detalhe_da_proposicao_nao_gera_pacote(self, raiz, capsys):
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte({}), raiz=raiz) == 1
        assert "/proposicoes/1" in capsys.readouterr().err
        assert not (raiz / "gravacoes" / "pl-1.json").exists()

    def test_avisa_acima_de_8_mb(self, raiz, capsys):
        (raiz / "lastro.bin").write_bytes(b"0" * (8 * 1024 * 1024 + 1))
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte_dos_dois_casos(), raiz=raiz) == 0
        assert "8 MB" in capsys.readouterr().err

    def test_nao_avisa_abaixo_de_8_mb(self, raiz, capsys):
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte_dos_dois_casos(), raiz=raiz) == 0
        assert "8 MB" not in capsys.readouterr().err

    def test_divide_pacote_acima_do_limite_do_hook_e_o_replay_junta(self, raiz):
        # .pre-commit-config.yaml recusa arquivo acima de 500 KB.
        grande = {"dados": [{"texto": "x" * 1000} for _ in range(300)]}
        rotas = {
            **_proposicao(1),
            "/api/v2/proposicoes/1/tramitacoes": _ok({"dados": [
                {"uriOrgao": f"{CAMARA}/orgaos/4", **grande}
            ]}),
            "/api/v2/proposicoes/1/autores": _ok(grande),
            "/api/v2/proposicoes/1/relacionadas": _ok(grande),
            "/api/v2/orgaos/4": _ok({"dados": {"id": 4}}),
        }
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte(rotas), raiz=raiz) == 0
        arquivos = sorted((raiz / "gravacoes").glob("pl-1*.json"))
        assert [a.name for a in arquivos] == ["pl-1.json", "pl-1.parte-02.json", "pl-1.parte-03.json"]
        assert all(a.stat().st_size <= gr.LIMITE_ARQUIVO for a in arquivos)
        cabecas = [json.loads(a.read_text("utf-8")) for a in arquivos]
        assert [(c["parte"], c["partes"]) for c in cabecas] == [(1, 3), (2, 3), (3, 3)]
        assert all(c["caso"] == "pl-1" for c in cabecas)
        g = Gravacoes(raiz / "gravacoes").carregar("pl-1")
        with g.cliente_camara() as cliente:
            assert cliente._get("/proposicoes/1/relacionadas") == grande["dados"]

    def test_regravar_menor_apaga_as_partes_antigas(self, raiz):
        (raiz / "gravacoes" / "pl-1.parte-02.json").write_text("{}", encoding="utf-8")
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte_dos_dois_casos(), raiz=raiz) == 0
        assert not (raiz / "gravacoes" / "pl-1.parte-02.json").exists()

    def test_casos_yml_conserva_acentos_e_cabecalho(self, raiz):
        arquivo = raiz / "casos.yml"
        dados = yaml.safe_load(arquivo.read_text("utf-8"))
        dados["casos"][0]["por_que"] = "órgão efetivo"
        arquivo.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        assert gr.main(["--caso", "pl-1"], transporte_base=_fonte_dos_dois_casos(), raiz=raiz) == 0
        texto = arquivo.read_text("utf-8")
        assert "órgão efetivo" in texto
        assert texto.startswith("#")

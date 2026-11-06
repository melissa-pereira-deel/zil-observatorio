"""Testes dos snapshots das tabelas de código e do script de atualização (TRM-020)."""

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.tramitacao import referencias  # noqa: E402
from packages.tramitacao.referencias import (  # noqa: E402
    Diferenca,
    ReferenciaInvalida,
    SubstituicaoInesperada,
    TABELAS,
    carregar_snapshot,
    diferenca,
    extrair_lista,
    motivo_recusa,
    normalizar_itens,
    serializar,
    substituir_descricao,
)
from scripts import atualizar_referencias_tramitacao as script  # noqa: E402

SITUACOES = "camara-situacoes.json"
TRAMITACAO = "camara-tipos-tramitacao.json"
ORGAOS = "camara-tipos-orgao.json"
SENADO = "senado-tipos-situacao.json"

HOJE = date(2026, 11, 5)
CARGA = date(2026, 10, 30)


def item_camara(cod: str, nome: str) -> dict:
    return {"cod": cod, "sigla": "", "nome": nome, "descricao": ""}


def item_senado(sigla: str, descricao: str, data_fim: str | None = None) -> dict:
    return {
        "id": 1000 + sum(ord(c) for c in sigla),
        "sigla": sigla,
        "descricao": descricao,
        "dataInicio": "1900-01-01T00:00:00",
        "dataFim": data_fim,
    }


class Fonte:
    """As quatro tabelas como a fonte as devolve, editáveis entre uma execução e outra."""

    def __init__(self) -> None:
        self.situacoes = [item_camara(str(900 + i), f"Situação {900 + i}") for i in range(20)]
        self.tramitacao = [item_camara(str(100 + i), f"Tramitação {100 + i}") for i in range(20)]
        self.orgaos = [item_camara(str(1 + i), f"Órgão {1 + i}") for i in range(20)]
        self.senado = [item_senado(f"S{i:02d}", f"SITUAÇÃO {i:02d}") for i in range(20)]
        self.falha_em: str | None = None
        self.status = 200
        self.pedidos: list[httpx.Request] = []

    def corpos(self) -> dict:
        return {
            TABELAS[SITUACOES][0]: {"dados": self.situacoes, "links": []},
            TABELAS[TRAMITACAO][0]: {"dados": self.tramitacao, "links": []},
            TABELAS[ORGAOS][0]: {"dados": self.orgaos, "links": []},
            TABELAS[SENADO][0]: self.senado,
        }

    def transport(self) -> httpx.MockTransport:
        def responder(request: httpx.Request) -> httpx.Response:
            self.pedidos.append(request)
            url = str(request.url)
            if self.falha_em and url == TABELAS[self.falha_em][0]:
                raise httpx.ConnectTimeout("tempo esgotado", request=request)
            return httpx.Response(self.status, json=self.corpos()[url])

        return httpx.MockTransport(responder)


def rodar(diretorio: Path, fonte: Fonte, *args: str, hoje: date = HOJE) -> int:
    return script.main(
        [*args, "--dir", str(diretorio)],
        transport=fonte.transport(),
        intervalo=0,
        hoje=hoje,
    )


def decisoes(saida: str) -> str:
    """Só o bloco de decisão humana: o mesmo texto também sai nas linhas do diff."""
    bloco = saida.partition("Precisa de decisão humana:")[2]
    return bloco.partition("\n\n")[0]


def afetadas(saida: str) -> list[str]:
    bloco = saida.partition("Entradas afetadas (para o lote de revisão):")[2].partition("\n\n")[0]
    return bloco.split()


def conteudo(diretorio: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(diretorio)): p.read_bytes()
        for p in sorted(diretorio.rglob("*"))
        if p.is_file()
    }


@pytest.fixture
def fonte() -> Fonte:
    return Fonte()


@pytest.fixture
def base(tmp_path: Path, fonte: Fonte) -> Path:
    """Diretório com a linha de base gravada em CARGA."""
    assert rodar(tmp_path, fonte, hoje=CARGA) == 0
    return tmp_path


# ── Funções puras ────────────────────────────────────────────────────────────


class TestDiferenca:
    def test_novos_removidos_e_renomeados(self):
        antigo = [
            {"cod": "1", "nome": "Um"},
            {"cod": "2", "nome": "Dois"},
            {"cod": "3", "nome": "Três"},
        ]
        novo = [
            {"cod": "1", "nome": "Um"},
            {"cod": "3", "nome": "Três Novo"},
            {"cod": "4", "nome": "Quatro"},
        ]

        dif = diferenca(antigo, novo)

        assert dif.novos == ({"cod": "4", "nome": "Quatro"},)
        assert dif.removidos == ({"cod": "2", "nome": "Dois"},)
        assert dif.renomeados == (("3", "Três", "Três Novo"),)

    def test_espaco_sobrando_nao_conta_como_renomeado(self):
        dif = diferenca(
            [{"cod": "901", "nome": "Aguardando Comissão "}],
            [{"cod": "901", "nome": "Aguardando Comissão"}],
        )

        assert dif.renomeados == ()
        assert dif.alterados == ("901",)

    def test_renomeado_guarda_o_texto_como_veio(self):
        dif = diferenca([{"cod": "1", "nome": "Velho "}], [{"cod": "1", "nome": "Novo "}])

        assert dif.renomeados == (("1", "Velho ", "Novo "),)

    def test_a_chave_e_o_codigo_nunca_o_nome(self):
        """905 e 1382 têm a mesma descrição na Câmara; trocar um não pode confundir o outro."""
        antigo = [{"cod": "905", "nome": "Igual"}, {"cod": "1382", "nome": "Igual"}]
        novo = [{"cod": "905", "nome": "Outro"}, {"cod": "1382", "nome": "Igual"}]

        assert diferenca(antigo, novo).renomeados == (("905", "Igual", "Outro"),)

    def test_trocar_o_codigo_com_o_mesmo_nome_e_removido_mais_novo(self):
        dif = diferenca([{"cod": "A", "nome": "X"}], [{"cod": "B", "nome": "X"}])

        assert [i["cod"] for i in dif.novos] == ["B"]
        assert [i["cod"] for i in dif.removidos] == ["A"]
        assert dif.renomeados == ()

    def test_outro_campo_alterado_nao_e_renomeado_mas_aparece(self):
        dif = diferenca(
            [{"cod": "S", "nome": "X", "data_fim": None}],
            [{"cod": "S", "nome": "X", "data_fim": "2026-01-01T00:00:00"}],
        )

        assert dif.renomeados == ()
        assert dif.alterados == ("S",)

    def test_sem_diferenca_e_vazia(self):
        assert diferenca([{"cod": "1", "nome": "U"}], [{"cod": "1", "nome": "U"}]).vazia
        assert not Diferenca(novos=({"cod": "1", "nome": "U"},), removidos=(), renomeados=()).vazia


class TestExtrairLista:
    def test_camara_vem_embrulhada_e_senado_vem_direto(self):
        assert extrair_lista(SITUACOES, {"dados": [1], "links": []}) == [1]
        assert extrair_lista(SENADO, [2]) == [2]

    @pytest.mark.parametrize("corpo", [{"erro": "x"}, {"dados": "x"}, "texto", None])
    def test_o_que_nao_e_lista_e_recusado(self, corpo: object):
        with pytest.raises(ReferenciaInvalida):
            extrair_lista(SITUACOES, corpo)


class TestNormalizarItens:
    def test_camara_ordena_pelo_numero_e_guarda_os_quatro_campos(self):
        itens = normalizar_itens(
            SITUACOES,
            [
                {"cod": "1000", "sigla": "", "nome": "Mil", "descricao": "", "extra": 1},
                {"cod": "901", "sigla": "S", "nome": "Com espaço ", "descricao": "d"},
            ],
        )

        assert itens == [
            {"cod": "901", "nome": "Com espaço ", "sigla": "S", "descricao": "d"},
            {"cod": "1000", "nome": "Mil", "sigla": "", "descricao": ""},
        ]

    def test_senado_usa_a_sigla_como_codigo(self):
        itens = normalizar_itens(
            SENADO,
            [
                item_senado("TNJR", "TRANSFORMADA EM NORMA JURÍDICA", "2020-01-01T00:00:00"),
                item_senado("AGDDO", "AGENDADA PARA ORDEM DO DIA "),
            ],
        )

        assert [i["cod"] for i in itens] == ["AGDDO", "TNJR"]
        assert itens[0] == {
            "cod": "AGDDO",
            "id": item_senado("AGDDO", "")["id"],
            "nome": "AGENDADA PARA ORDEM DO DIA ",
            "data_inicio": "1900-01-01T00:00:00",
            "data_fim": None,
        }
        assert itens[1]["data_fim"] == "2020-01-01T00:00:00"

    def test_campo_ausente_e_recusado(self):
        with pytest.raises(ReferenciaInvalida):
            normalizar_itens(SITUACOES, [{"cod": "1", "nome": "Sem sigla"}])

    def test_codigo_nao_numerico_na_camara_e_recusado(self):
        with pytest.raises(ReferenciaInvalida):
            normalizar_itens(SITUACOES, [item_camara("abc", "Nome")])

    def test_sigla_nula_no_senado_e_recusada(self):
        item = item_senado("X", "NOME") | {"sigla": None}

        with pytest.raises(ReferenciaInvalida):
            normalizar_itens(SENADO, [item])

    @pytest.mark.parametrize("nome", ["", "   ", None])
    def test_item_sem_nome_e_recusado(self, nome: str | None):
        with pytest.raises(ReferenciaInvalida):
            normalizar_itens(SITUACOES, [item_camara("1", nome)])

    def test_codigo_duplicado_e_recusado(self):
        with pytest.raises(ReferenciaInvalida):
            normalizar_itens(SITUACOES, [item_camara("1", "A"), item_camara("1", "B")])


class TestSerializar:
    def test_formato_de_gravacao(self):
        snapshot = {"tabela": "t", "total": 1, "itens": [{"cod": "1", "nome": "Ação "}]}

        assert serializar(snapshot) == json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
        assert "Ação " in serializar(snapshot)

    def test_carregar_le_o_que_foi_gravado(self, tmp_path: Path):
        snapshot = {"tabela": "t", "total": 0, "itens": []}
        destino = tmp_path / "referencias" / SITUACOES
        destino.parent.mkdir()
        destino.write_text(serializar(snapshot), encoding="utf-8")

        assert carregar_snapshot(tmp_path, SITUACOES) == snapshot

    def test_snapshot_ausente(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            carregar_snapshot(tmp_path, SITUACOES)


class TestMotivoRecusa:
    def test_zero_itens_e_recusado_mesmo_com_a_flag(self):
        assert motivo_recusa(SITUACOES, 99, 0, aceitar_remocoes=False)
        assert motivo_recusa(SITUACOES, 99, 0, aceitar_remocoes=True)
        assert motivo_recusa(SITUACOES, None, 0, aceitar_remocoes=True)

    def test_mais_de_dez_por_cento_a_menos_e_recusado_sem_a_flag(self):
        assert motivo_recusa(SITUACOES, 100, 89, aceitar_remocoes=False)
        assert motivo_recusa(SITUACOES, 100, 89, aceitar_remocoes=True) is None

    def test_exatamente_dez_por_cento_passa(self):
        assert motivo_recusa(SITUACOES, 100, 90, aceitar_remocoes=False) is None

    def test_linha_de_base_nao_tem_com_o_que_comparar(self):
        assert motivo_recusa(SITUACOES, None, 5, aceitar_remocoes=False) is None


class TestSubstituirDescricao:
    def test_bloco_e_fluxo_com_comentarios_preservados(self):
        texto = (
            "# comentário\n"
            "marcos:\n"
            "  - cod: '1'\n"
            "    descricao_oficial: Velho  # nota\n"
            "ignorados:\n"
            '  - {cod: "2", descricao_oficial: Velho, nota: "x"}\n'
            '  - {cod: "3", descricao_oficial: Velho}\n'
        )

        novo = substituir_descricao(texto, "Velho", "Novo", 3)

        assert novo == texto.replace("Velho", "Novo")

    def test_formas_com_aspas(self):
        texto = "a:\n- descricao_oficial: \"Velho\"\n- descricao_oficial: 'Velho'\n"

        assert yaml.safe_load(substituir_descricao(texto, "Velho", "Novo", 2)) == {
            "a": [{"descricao_oficial": "Novo"}, {"descricao_oficial": "Novo"}]
        }

    def test_so_a_string_exata_conta(self):
        texto = "- descricao_oficial: Arquivada pelo Presidente\n- descricao_oficial: Arquivada\n"

        assert substituir_descricao(texto, "Arquivada", "Nova", 1) == (
            "- descricao_oficial: Arquivada pelo Presidente\n- descricao_oficial: Nova\n"
        )

    def test_nao_toca_em_outro_campo(self):
        texto = "- termo: Velho\n  texto: Velho é o nome\n  descricao_oficial: Velho\n"

        assert substituir_descricao(texto, "Velho", "Novo", 1) == (
            "- termo: Velho\n  texto: Velho é o nome\n  descricao_oficial: Novo\n"
        )

    @pytest.mark.parametrize("esperado", [0, 2])
    def test_contagem_errada_aborta(self, esperado: int):
        with pytest.raises(SubstituicaoInesperada):
            substituir_descricao("- descricao_oficial: Velho\n", "Velho", "Novo", esperado)

    @pytest.mark.parametrize("novo", ["Null", "Sim", "9 itens", "Com 'aspas'"])
    def test_texto_que_o_yaml_leria_diferente_sai_entre_aspas(self, novo: str):
        texto = "- descricao_oficial: Velho\n"

        resultado = substituir_descricao(texto, "Velho", novo, 1)

        assert yaml.safe_load(resultado) == [{"descricao_oficial": novo}]

    @pytest.mark.parametrize("novo", ["Novo, com vírgula", "Novo {x}", "*ancora", "1ª Comissão"])
    def test_texto_novo_continua_valido_dentro_de_chaves(self, novo: str):
        resultado = substituir_descricao('- {cod: "1", descricao_oficial: Velho}\n', "Velho", novo, 1)

        assert yaml.safe_load(resultado) == [{"cod": "1", "descricao_oficial": novo}]

    def test_compara_e_grava_sem_o_espaco_que_a_fonte_manda(self):
        resultado = substituir_descricao("- descricao_oficial: Velho\n", "Velho ", "Novo ", 1)

        assert resultado == "- descricao_oficial: Novo\n"

    def test_nome_com_caractere_especial_sai_entre_aspas(self):
        texto = '- {cod: "1", descricao_oficial: Velho}\n'

        novo = substituir_descricao(texto, "Velho", "Novo: com, vírgula", 1)

        assert yaml.safe_load(novo) == [{"cod": "1", "descricao_oficial": "Novo: com, vírgula"}]


# ── Carga inicial ────────────────────────────────────────────────────────────


class TestLinhaDeBase:
    def test_grava_os_quatro_snapshots_ordenados_e_com_total(self, tmp_path: Path, fonte: Fonte):
        fonte.situacoes = [item_camara("1000", "Mil"), item_camara("901", "Espaço ")]

        assert rodar(tmp_path, fonte) == 0

        for arquivo in TABELAS:
            snapshot = carregar_snapshot(tmp_path, arquivo)
            assert snapshot["total"] == len(snapshot["itens"])
            assert snapshot["fonte"] == TABELAS[arquivo][0]
            assert snapshot["obtido_em"] == "2026-11-05"
        situacoes = carregar_snapshot(tmp_path, SITUACOES)
        assert situacoes["tabela"] == "camara.codSituacao"
        assert situacoes["itens"][0] == {
            "cod": "901",
            "nome": "Espaço ",
            "sigla": "",
            "descricao": "",
        }

    def test_nao_trata_nada_como_codigo_novo(self, tmp_path: Path, fonte: Fonte):
        assert rodar(tmp_path, fonte) == 0

        assert not (tmp_path / "nao_mapeados.yml").exists()

    def test_nao_toca_em_nao_mapeados_existente(self, tmp_path: Path, fonte: Fonte):
        original = "versao_esquema: 1\nsituacoes_camara: []\nsituacoes_senado: []\ntramitacao_camara: []\n"
        (tmp_path / "nao_mapeados.yml").write_text(original, encoding="utf-8")

        assert rodar(tmp_path, fonte) == 0

        assert (tmp_path / "nao_mapeados.yml").read_text(encoding="utf-8") == original

    def test_so_a_tabela_sem_snapshot_vira_linha_de_base(self, base: Path, fonte: Fonte):
        (base / "referencias" / SENADO).unlink()
        fonte.senado.append(item_senado("ZZZ", "SEM ANTERIOR"))
        fonte.situacoes.append(item_camara("9999", "Nova de verdade"))

        assert rodar(base, fonte) == 0

        nao_mapeados = yaml.safe_load((base / "nao_mapeados.yml").read_text(encoding="utf-8"))
        assert [e["cod"] for e in nao_mapeados["situacoes_camara"]] == ["9999"]
        assert nao_mapeados["situacoes_senado"] == []

    def test_recusa_tabela_vazia(self, tmp_path: Path, fonte: Fonte):
        fonte.orgaos = []

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == {}


# ── --verificar ──────────────────────────────────────────────────────────────


class TestVerificar:
    def test_sem_diferenca_sai_zero(self, base: Path, fonte: Fonte):
        antes = conteudo(base)

        assert rodar(base, fonte, "--verificar") == 0

        assert conteudo(base) == antes

    def test_com_diferenca_imprime_e_sai_dois_sem_gravar(self, base: Path, fonte: Fonte, capsys):
        fonte.situacoes.append(item_camara("9999", "Situação Nova"))
        fonte.situacoes[0] = item_camara("900", "Situação Renomeada")
        del fonte.situacoes[1]
        antes = conteudo(base)
        capsys.readouterr()

        assert rodar(base, fonte, "--verificar") == 2

        linhas = [linha.strip() for linha in capsys.readouterr().out.splitlines()]
        assert 'novo      9999: "Situação Nova"' in linhas
        assert 'removido  901: "Situação 901"' in linhas
        assert 'renomeado 900: "Situação 900" -> "Situação Renomeada"' in linhas
        assert "camara-situacoes.json: 20 itens" in linhas
        assert "camara-tipos-orgao.json: 20 itens, sem diferença" in linhas
        assert conteudo(base) == antes

    def test_sem_snapshot_e_diferenca(self, tmp_path: Path, fonte: Fonte):
        assert rodar(tmp_path, fonte, "--verificar") == 2

        assert conteudo(tmp_path) == {}

    def test_diferenca_so_de_espaco_tambem_sai_dois(self, base: Path, fonte: Fonte):
        """Sair 0 aqui faria --verificar dizer "em dia" sobre um snapshot que a gravação mudaria."""
        fonte.situacoes[0] = item_camara("900", "Situação 900 ")

        assert rodar(base, fonte, "--verificar") == 2

    @pytest.mark.parametrize("com_snapshot", [True, False])
    def test_fonte_vazia_e_falha_e_nao_diferenca(self, tmp_path: Path, fonte: Fonte, com_snapshot: bool):
        if com_snapshot:
            assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        antes = conteudo(tmp_path)
        fonte.senado = []

        assert rodar(tmp_path, fonte, "--verificar") == 1

        assert conteudo(tmp_path) == antes

    def test_queda_grande_continua_sendo_diferenca(self, base: Path, fonte: Fonte):
        """Pode ser real e --aceitar-remocoes a libera; quem decide é a pessoa, não é falha da fonte."""
        fonte.situacoes = fonte.situacoes[:17]
        antes = conteudo(base)

        assert rodar(base, fonte, "--verificar") == 2

        assert conteudo(base) == antes

    def test_inconsistencia_nos_yamls_nao_muda_o_codigo_de_saida(self, base: Path, fonte: Fonte, capsys):
        (base / "fases.yml").write_text(
            'regras:\n  - id: R3\n    situacoes_camara:\n      - {cod: "900", descricao_oficial: Outra coisa}\n',
            encoding="utf-8",
        )
        fonte.situacoes[0] = item_camara("900", "Situação Renomeada")
        capsys.readouterr()

        assert rodar(base, fonte, "--verificar") == 2

        assert "Outra coisa" in capsys.readouterr().out


class TestErroDeRede:
    @pytest.mark.parametrize("args", [(), ("--verificar",)])
    def test_sai_um_e_nao_grava_nada(self, base: Path, fonte: Fonte, args: tuple[str, ...]):
        fonte.situacoes.append(item_camara("9999", "Situação Nova"))
        fonte.falha_em = SENADO
        antes = conteudo(base)

        assert rodar(base, fonte, *args) == 1

        assert conteudo(base) == antes

    @pytest.mark.parametrize("status", [429, 500, 503])
    def test_status_de_erro_com_corpo_valido_nao_vira_dado(self, tmp_path: Path, fonte: Fonte, status: int):
        fonte.status = status

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == {}

    def test_resposta_que_nao_e_json_sai_um(self, tmp_path: Path):
        transport = httpx.MockTransport(lambda request: httpx.Response(200, text="<html>"))

        assert script.main(["--dir", str(tmp_path)], transport=transport, intervalo=0) == 1

        assert conteudo(tmp_path) == {}

    def test_corpo_sem_dados_sai_um(self, tmp_path: Path):
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"erro": "x"}))

        assert script.main(["--dir", str(tmp_path)], transport=transport, intervalo=0) == 1

        assert conteudo(tmp_path) == {}


def test_pede_json_a_cada_tabela_uma_vez(tmp_path: Path, fonte: Fonte):
    assert rodar(tmp_path, fonte) == 0

    assert sorted(str(p.url) for p in fonte.pedidos) == sorted(u for u, _ in TABELAS.values())
    assert all(p.headers["accept"] == "application/json" for p in fonte.pedidos)


def test_cada_pedido_tem_timeout_de_30_segundos(tmp_path: Path, fonte: Fonte):
    assert rodar(tmp_path, fonte) == 0

    assert all(set(p.extensions["timeout"].values()) == {30} for p in fonte.pedidos)


def test_espera_um_segundo_entre_os_pedidos(tmp_path: Path, fonte: Fonte, monkeypatch):
    esperas: list[float] = []
    monkeypatch.setattr(script.time, "sleep", esperas.append)

    assert script.main(["--dir", str(tmp_path)], transport=fonte.transport(), hoje=HOJE) == 0

    assert esperas == [1.0, 1.0, 1.0]


def test_hoje_e_a_data_de_sao_paulo(tmp_path: Path, fonte: Fonte, monkeypatch):
    """01h30 de 6/11 em UTC ainda é 5/11 em Brasília; a API e a spec falam em horário de Brasília."""

    class Relogio(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 6, 1, 30, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(script, "datetime", Relogio)

    assert script.main(["--dir", str(tmp_path)], transport=fonte.transport(), intervalo=0) == 0

    assert carregar_snapshot(tmp_path, SITUACOES)["obtido_em"] == "2026-11-05"


class TestDiretorio:
    @pytest.mark.parametrize("args", [(), ("--verificar",)])
    def test_inexistente_sai_um_sem_criar_nem_baixar(self, tmp_path: Path, fonte: Fonte, args: tuple[str, ...]):
        destino = tmp_path / "digitado" / "errado"

        assert rodar(destino, fonte, *args) == 1

        assert not destino.parent.exists()
        assert fonte.pedidos == []

    def test_arquivo_no_lugar_do_diretorio_sai_um(self, tmp_path: Path, fonte: Fonte):
        destino = tmp_path / "arquivo"
        destino.write_text("x", encoding="utf-8")

        assert rodar(destino, fonte) == 1

        assert destino.read_text(encoding="utf-8") == "x"

    def test_existente_sem_referencias_e_carga_inicial(self, tmp_path: Path, fonte: Fonte):
        assert rodar(tmp_path, fonte) == 0

        assert (tmp_path / "referencias").is_dir()


# ── Gravação ─────────────────────────────────────────────────────────────────


class TestMensagens:
    """O texto é a interface de quem roda o script por PR: sem ele, sobra um código de saída mudo."""

    def test_linha_de_base_uma_linha_por_tabela(self, tmp_path: Path, fonte: Fonte, capsys):
        assert rodar(tmp_path, fonte) == 0

        linhas = capsys.readouterr().out.splitlines()
        assert linhas[:4] == [f"{a}: 20 itens, linha de base (sem snapshot anterior)" for a in TABELAS]
        assert "Gravados:" in linhas
        assert "  referencias/camara-situacoes.json" in linhas

    def test_diretorio_inexistente(self, tmp_path: Path, fonte: Fonte, capsys):
        assert rodar(tmp_path / "nao_ha", fonte) == 1

        assert "não existe" in capsys.readouterr().err

    def test_erro_de_rede(self, tmp_path: Path, fonte: Fonte, capsys):
        fonte.falha_em = SENADO

        assert rodar(tmp_path, fonte) == 1

        assert "Erro de rede" in capsys.readouterr().err

    def test_fonte_fora_do_formato(self, tmp_path: Path, fonte: Fonte, capsys):
        fonte.situacoes = [{"cod": "1"}]

        assert rodar(tmp_path, fonte) == 1

        assert "Nada foi gravado" in capsys.readouterr().err

    def test_recusa_diz_o_motivo_e_que_nada_foi_gravado(self, base: Path, fonte: Fonte, capsys):
        fonte.situacoes = fonte.situacoes[:17]
        capsys.readouterr()

        assert rodar(base, fonte) == 1

        saida = capsys.readouterr().out
        assert "A gravação não pode seguir:" in saida
        assert "de 20 para 17 itens" in saida
        assert "Nada foi gravado." in saida
        assert "Gravados:" not in saida

    def test_sem_problema_nao_imprime_o_bloco_de_problemas(self, base: Path, fonte: Fonte, capsys):
        fonte.situacoes.append(item_camara("9999", "Nova"))
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert "A gravação não pode seguir" not in capsys.readouterr().out

    def test_falha_de_gravacao(self, tmp_path: Path, fonte: Fonte, monkeypatch, capsys):
        def falhar(origem: Path, destino: Path) -> None:
            raise OSError("falha simulada")

        monkeypatch.setattr(script.os, "replace", falhar)

        assert rodar(tmp_path, fonte) == 1

        assert "Erro ao gravar" in capsys.readouterr().err


class TestArquivosLocais:
    def test_yaml_quebrado_sem_diferenca_nao_impede_nada(self, base: Path, fonte: Fonte, capsys):
        """Sem diferença da fonte os YAMLs não entram na conta; quem os valida é outro passo."""
        (base / "fases.yml").write_text("regras: [", encoding="utf-8")
        capsys.readouterr()

        assert rodar(base, fonte) == 0
        assert rodar(base, fonte, "--verificar") == 0

        assert "fases.yml" not in capsys.readouterr().out

    @pytest.mark.parametrize("corrompido", ["{", '{"sem": "itens"}'])
    def test_snapshot_ilegivel_sai_um_sem_gravar(self, base: Path, fonte: Fonte, capsys, corrompido: str):
        (base / "referencias" / SITUACOES).write_text(corrompido, encoding="utf-8")
        antes = conteudo(base)
        capsys.readouterr()

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes
        assert "snapshot local ilegível" in capsys.readouterr().err


class TestSoGravaOQueMudou:
    def test_sem_mudanca_nao_regrava_nem_troca_a_data(self, base: Path, fonte: Fonte):
        antes = conteudo(base)

        assert rodar(base, fonte) == 0

        assert conteudo(base) == antes

    def test_obtido_em_muda_so_no_snapshot_que_mudou(self, base: Path, fonte: Fonte):
        fonte.tramitacao.append(item_camara("1234", "Nova"))

        assert rodar(base, fonte) == 0

        assert carregar_snapshot(base, TRAMITACAO)["obtido_em"] == "2026-11-05"
        assert carregar_snapshot(base, TRAMITACAO)["total"] == 21
        for arquivo in (SITUACOES, ORGAOS, SENADO):
            assert carregar_snapshot(base, arquivo)["obtido_em"] == "2026-10-30"

    def test_ordem_diferente_na_fonte_nao_e_mudanca(self, base: Path, fonte: Fonte):
        fonte.situacoes.reverse()
        antes = conteudo(base)

        assert rodar(base, fonte, "--verificar") == 0
        assert rodar(base, fonte) == 0

        assert conteudo(base) == antes

    def test_texto_gravado_nao_e_normalizado(self, base: Path, fonte: Fonte):
        fonte.situacoes[0] = item_camara("900", "Situação 900 ")

        assert rodar(base, fonte) == 0

        assert carregar_snapshot(base, SITUACOES)["itens"][0]["nome"] == "Situação 900 "

    def test_data_fim_no_senado_atualiza_o_snapshot(self, base: Path, fonte: Fonte, capsys):
        fonte.senado[0] = item_senado("S00", "SITUAÇÃO 00", "2026-11-01T00:00:00")
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert carregar_snapshot(base, SENADO)["itens"][0]["data_fim"] == "2026-11-01T00:00:00"
        assert "S00" in capsys.readouterr().out
        assert not (base / "nao_mapeados.yml").exists()


class TestCodigoNovo:
    def test_cria_nao_mapeados_no_formato_quando_nao_existe(self, base: Path, fonte: Fonte):
        fonte.situacoes.append(item_camara("9999", "Situação Nova "))

        assert rodar(base, fonte) == 0

        texto = (base / "nao_mapeados.yml").read_text(encoding="utf-8")
        assert texto.startswith("# data/tramitacao/nao_mapeados.yml")
        assert yaml.safe_load(texto) == {
            "versao_esquema": 1,
            "situacoes_camara": [
                {
                    "cod": "9999",
                    "descricao_oficial": "Situação Nova",
                    "motivo": "codigo_novo_2026-11-05",
                }
            ],
            "situacoes_senado": [],
            "tramitacao_camara": [],
        }

    def test_cada_tabela_vai_para_a_sua_secao_em_ordem(self, base: Path, fonte: Fonte):
        (base / "nao_mapeados.yml").write_text(
            "versao_esquema: 1\n"
            "situacoes_camara:\n"
            '  - {cod: "1250", descricao_oficial: Inativa, motivo: inativo}\n'
            '  - {cod: "1310", descricao_oficial: Conselho, motivo: fora_do_escopo, nota: "disciplinar"}\n'
            "situacoes_senado:\n"
            '  - {cod: "S05", descricao_oficial: SITUAÇÃO 05, motivo: sem_evidencia, nota: "TRM-050"}\n'
            "tramitacao_camara: []\n",
            encoding="utf-8",
        )
        fonte.situacoes += [item_camara("1300", "Entre"), item_camara("1000", "Antes")]
        fonte.senado += [item_senado("A99", "ANTES"), item_senado("Z99", "DEPOIS")]
        fonte.tramitacao.append(item_camara("1234", "Tramitação Nova"))

        assert rodar(base, fonte) == 0

        dados = yaml.safe_load((base / "nao_mapeados.yml").read_text(encoding="utf-8"))
        assert [e["cod"] for e in dados["situacoes_camara"]] == ["1000", "1250", "1300", "1310"]
        assert [e["cod"] for e in dados["situacoes_senado"]] == ["A99", "S05", "Z99"]
        assert [e["cod"] for e in dados["tramitacao_camara"]] == ["1234"]
        assert dados["situacoes_camara"][3]["nota"] == "disciplinar"
        assert dados["situacoes_camara"][0]["motivo"] == "codigo_novo_2026-11-05"

    def test_camara_em_ordem_numerica_e_senado_em_ordem_de_texto(self, base: Path, fonte: Fonte):
        """Como texto, "1230" viria antes de "950"; como número, "S9" não teria ordem."""
        fonte.situacoes += [item_camara("1230", "Mil e tanto"), item_camara("950", "Novecentos")]
        fonte.tramitacao += [item_camara("1012", "Mil"), item_camara("502", "Quinhentos")]
        fonte.senado += [item_senado("TNJR", "T"), item_senado("AGDO (RQ)", "A")]

        assert rodar(base, fonte) == 0

        dados = yaml.safe_load((base / "nao_mapeados.yml").read_text(encoding="utf-8"))
        assert [e["cod"] for e in dados["situacoes_camara"]] == ["950", "1230"]
        assert [e["cod"] for e in dados["tramitacao_camara"]] == ["502", "1012"]
        assert [e["cod"] for e in dados["situacoes_senado"]] == ["AGDO (RQ)", "TNJR"]

    def test_tipo_de_orgao_novo_nao_tem_secao_e_vira_decisao_humana(self, base: Path, fonte: Fonte, capsys):
        fonte.orgaos.append(item_camara("81010", "Órgão Novo"))
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert not (base / "nao_mapeados.yml").exists()
        assert (
            'camara-tipos-orgao.json: código novo 81010 ("Órgão Novo"), sem seção em nao_mapeados.yml'
            in decisoes(capsys.readouterr().out)
        )
        assert carregar_snapshot(base, ORGAOS)["total"] == 21

    def test_codigo_que_volta_e_ja_tem_dono_nao_ganha_segunda_entrada(self, base: Path, fonte: Fonte, capsys):
        """Cada código tem um dono só; o validador recusa código em regra e em nao_mapeados."""
        removido = fonte.situacoes.pop()
        assert rodar(base, fonte) == 0
        (base / "fases.yml").write_text(
            f'regras:\n  - id: R3\n    situacoes_camara:\n      - {{cod: "{removido["cod"]}", descricao_oficial: {removido["nome"]}}}\n',
            encoding="utf-8",
        )
        fonte.situacoes.append(removido)
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert not (base / "nao_mapeados.yml").exists()
        saida = capsys.readouterr().out
        assert afetadas(saida) == ["fases/regra_R3"]
        assert f"código {removido['cod']} voltou à fonte e já tem entrada (fases/regra_R3)" in decisoes(saida)

    def test_codigo_ja_listado_nao_duplica(self, base: Path, fonte: Fonte):
        removido = fonte.situacoes.pop()
        assert rodar(base, fonte) == 0
        fonte.situacoes.append(removido)
        assert rodar(base, fonte) == 0
        fonte.situacoes.pop()
        assert rodar(base, fonte) == 0
        fonte.situacoes.append(removido)

        assert rodar(base, fonte) == 0

        dados = yaml.safe_load((base / "nao_mapeados.yml").read_text(encoding="utf-8"))
        assert [e["cod"] for e in dados["situacoes_camara"]] == [removido["cod"]]

    def test_codigo_nao_numerico_da_camara_em_nao_mapeados_aborta(self, base: Path, fonte: Fonte):
        (base / "nao_mapeados.yml").write_text(
            "versao_esquema: 1\n"
            'situacoes_camara:\n  - {cod: "abc", descricao_oficial: X, motivo: inativo}\n'
            "situacoes_senado: []\ntramitacao_camara: []\n",
            encoding="utf-8",
        )
        fonte.situacoes.append(item_camara("9999", "Nova"))
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_nao_mapeados_quebrado_aborta_sem_gravar(self, base: Path, fonte: Fonte):
        (base / "nao_mapeados.yml").write_text("situacoes_camara: [", encoding="utf-8")
        fonte.situacoes.append(item_camara("9999", "Nova"))
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_nao_mapeados_malformado_aborta_sem_gravar(self, base: Path, fonte: Fonte):
        (base / "nao_mapeados.yml").write_text("versao_esquema: 1\n", encoding="utf-8")
        fonte.situacoes.append(item_camara("9999", "Nova"))
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_nome_longo_fica_em_uma_linha_e_pode_ser_renomeado_depois(self, base: Path, fonte: Fonte):
        """Se o dump dobrasse a linha, a substituição textual do próximo renomeado não acharia a string."""
        longo = "Aguardando Designação - Aguardando Devolução de Relator(a) que deixou de ser Membro da Comissão"
        fonte.situacoes.append(item_camara("1170", longo))
        assert rodar(base, fonte) == 0
        assert longo in (base / "nao_mapeados.yml").read_text(encoding="utf-8")
        fonte.situacoes[-1] = item_camara("1170", "Nome Curto")

        assert rodar(base, fonte) == 0

        dados = yaml.safe_load((base / "nao_mapeados.yml").read_text(encoding="utf-8"))
        assert dados["situacoes_camara"][0]["descricao_oficial"] == "Nome Curto"


FASES = """\
# data/tramitacao/fases.yml — comentário que não pode se perder
versao_esquema: 1
regras:
  - id: R3
    situacoes_camara:
      - {cod: "900", descricao_oficial: Situação 900, desfecho: arquivada}
      - {cod: "901", descricao_oficial: Situação 901}
    situacoes_senado:
      - {cod: "S00", descricao_oficial: SITUAÇÃO 00}
"""

MARCOS = """\
# comentário de marcos
versao_esquema: 1
marcos:
  - cod: "100"
    casa: camara
    descricao_oficial: Tramitação 100
    titulo: Tramitação 100
ignorados:
  - {cod: "101", descricao_oficial: Tramitação 101, nota: "não muda a fase"}
"""

GLOSSARIO = """\
versao_esquema: 1
entradas:
  - chave: situacao_novecentos
    tipo: situacao
    termo: Situação 900
    descricao_oficial: Situação 900
    codigos: [{casa: camara, cod: "900"}]
    texto: A Situação 900 é explicada aqui.
"""


def escrever_yamls(diretorio: Path) -> None:
    (diretorio / "fases.yml").write_text(FASES, encoding="utf-8")
    (diretorio / "marcos.yml").write_text(MARCOS, encoding="utf-8")
    (diretorio / "glossario.yml").write_text(GLOSSARIO, encoding="utf-8")


GLOSSARIO_COMPARTILHADO = """\
entradas:
  - chave: igual
    tipo: situacao
    termo: Igual
    descricao_oficial: Igual
    codigos: [{casa: camara, cod: "1905"}, {casa: camara, cod: "2382"}]
"""


class TestRenomeado:
    def test_troca_a_descricao_nos_yamls_e_preserva_o_resto(self, base: Path, fonte: Fonte, capsys):
        escrever_yamls(base)
        fonte.situacoes[0] = item_camara("900", "Situação Nova ")
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        fases = (base / "fases.yml").read_text(encoding="utf-8")
        assert fases == FASES.replace(
            "descricao_oficial: Situação 900,", "descricao_oficial: Situação Nova,"
        )
        glossario = (base / "glossario.yml").read_text(encoding="utf-8")
        assert glossario == GLOSSARIO.replace(
            "descricao_oficial: Situação 900", "descricao_oficial: Situação Nova"
        )
        assert (base / "marcos.yml").read_text(encoding="utf-8") == MARCOS
        assert carregar_snapshot(base, SITUACOES)["itens"][0]["nome"] == "Situação Nova "
        saida = capsys.readouterr().out
        assert "fases/regra_R3" in saida
        assert "glossario/situacao_novecentos" in saida
        assert "marcos/" not in saida

    def test_lista_o_termo_do_glossario_para_ajuste_humano(self, base: Path, fonte: Fonte, capsys):
        escrever_yamls(base)
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert "termo" in capsys.readouterr().out

    def test_marco_e_ignorado_por_tipo_de_tramitacao(self, base: Path, fonte: Fonte, capsys):
        escrever_yamls(base)
        fonte.tramitacao[0] = item_camara("100", "Tramitação Nova")
        fonte.tramitacao[1] = item_camara("101", "Outra Nova")
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        marcos = yaml.safe_load((base / "marcos.yml").read_text(encoding="utf-8"))
        assert marcos["marcos"][0]["descricao_oficial"] == "Tramitação Nova"
        assert marcos["marcos"][0]["titulo"] == "Tramitação 100"
        assert marcos["ignorados"][0]["descricao_oficial"] == "Outra Nova"
        assert "# comentário de marcos" in (base / "marcos.yml").read_text(encoding="utf-8")
        saida = capsys.readouterr().out
        assert "marcos/100" in saida
        assert "marcos/ignorados/101" in saida

    def test_senado_nao_mexe_na_camara(self, base: Path, fonte: Fonte, capsys):
        escrever_yamls(base)
        fonte.senado[0] = item_senado("S00", "SITUAÇÃO NOVA")

        assert rodar(base, fonte) == 0

        dados = yaml.safe_load((base / "fases.yml").read_text(encoding="utf-8"))
        assert dados["regras"][0]["situacoes_senado"][0]["descricao_oficial"] == "SITUAÇÃO NOVA"
        assert dados["regras"][0]["situacoes_camara"][0]["descricao_oficial"] == "Situação 900"

    def test_nao_mapeados_preserva_comentarios_quando_nao_ha_codigo_novo(self, base: Path, fonte: Fonte):
        original = (
            "# comentário à mão\n"
            "versao_esquema: 1\n"
            "situacoes_camara:\n"
            '  - {cod: "900", descricao_oficial: Situação 900, motivo: sem_evidencia}\n'
            "situacoes_senado: []\n"
            "tramitacao_camara: []\n"
        )
        (base / "nao_mapeados.yml").write_text(original, encoding="utf-8")
        fonte.situacoes[0] = item_camara("900", "Situação Nova")

        assert rodar(base, fonte) == 0

        assert (base / "nao_mapeados.yml").read_text(encoding="utf-8") == original.replace(
            "Situação 900", "Situação Nova"
        )

    def test_renomeado_e_novo_na_mesma_execucao(self, base: Path, fonte: Fonte):
        (base / "nao_mapeados.yml").write_text(
            "versao_esquema: 1\n"
            "situacoes_camara:\n"
            '  - {cod: "900", descricao_oficial: Situação 900, motivo: sem_evidencia}\n'
            "situacoes_senado: []\n"
            "tramitacao_camara: []\n",
            encoding="utf-8",
        )
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        fonte.situacoes.append(item_camara("9999", "Outra"))

        assert rodar(base, fonte) == 0

        dados = yaml.safe_load((base / "nao_mapeados.yml").read_text(encoding="utf-8"))
        assert [(e["cod"], e["descricao_oficial"]) for e in dados["situacoes_camara"]] == [
            ("900", "Situação Nova"),
            ("9999", "Outra"),
        ]

    def test_sem_yamls_grava_o_snapshot_e_segue(self, base: Path, fonte: Fonte):
        fonte.situacoes[0] = item_camara("900", "Situação Nova")

        assert rodar(base, fonte) == 0

        assert carregar_snapshot(base, SITUACOES)["itens"][0]["nome"] == "Situação Nova"
        assert sorted(p.name for p in base.iterdir()) == ["referencias"]

    def test_mesma_descricao_em_outro_codigo_aborta_sem_gravar(self, tmp_path: Path, fonte: Fonte, capsys):
        """905 e 1382 são iguais na Câmara: a troca textual levaria junto o código que não mudou."""
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "fases.yml").write_text(
            "regras:\n  - id: R3\n    situacoes_camara:\n"
            '      - {cod: "1905", descricao_oficial: Igual}\n'
            '      - {cod: "2382", descricao_oficial: Igual}\n',
            encoding="utf-8",
        )
        fonte.situacoes[-2] = item_camara("1905", "Diferente")
        fonte.situacoes.append(item_camara("9999", "Nova"))
        antes = conteudo(tmp_path)
        capsys.readouterr()

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == antes
        assert "fases.yml" in capsys.readouterr().out

    def test_os_dois_codigos_iguais_renomeados_juntos_passam(self, tmp_path: Path, fonte: Fonte):
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "fases.yml").write_text(
            "regras:\n  - id: R3\n    situacoes_camara:\n"
            '      - {cod: "1905", descricao_oficial: Igual}\n'
            '      - {cod: "2382", descricao_oficial: Igual}\n',
            encoding="utf-8",
        )
        fonte.situacoes[-2] = item_camara("1905", "Diferente")
        fonte.situacoes[-1] = item_camara("2382", "Diferente")

        assert rodar(tmp_path, fonte) == 0

        assert (tmp_path / "fases.yml").read_text(encoding="utf-8").count("Diferente") == 2

    def test_depois_de_ajustar_a_mao_a_execucao_passa(self, tmp_path: Path, fonte: Fonte):
        """A saída do aborto acima: a pessoa corrige o YAML e roda de novo, sem novo aborto."""
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "fases.yml").write_text(
            "regras:\n  - id: R3\n    situacoes_camara:\n"
            '      - {cod: "1905", descricao_oficial: Diferente}\n'
            '      - {cod: "2382", descricao_oficial: Igual}\n',
            encoding="utf-8",
        )
        antes = (tmp_path / "fases.yml").read_text(encoding="utf-8")
        fonte.situacoes[-2] = item_camara("1905", "Diferente")

        assert rodar(tmp_path, fonte) == 0

        assert (tmp_path / "fases.yml").read_text(encoding="utf-8") == antes
        assert carregar_snapshot(tmp_path, SITUACOES)["itens"][-2]["nome"] == "Diferente"

    def test_dois_codigos_iguais_para_textos_diferentes_abortam(self, tmp_path: Path, fonte: Fonte):
        """Sem esta guarda, a troca pelo texto antigo gravaria o primeiro texto novo nos dois."""
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "fases.yml").write_text(
            "regras:\n  - id: R3\n    situacoes_camara:\n"
            '      - {cod: "1905", descricao_oficial: Igual}\n'
            '      - {cod: "2382", descricao_oficial: Igual}\n',
            encoding="utf-8",
        )
        fonte.situacoes[-2] = item_camara("1905", "Texto A")
        fonte.situacoes[-1] = item_camara("2382", "Texto B")
        antes = conteudo(tmp_path)

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == antes

    def test_comentario_que_soma_na_contagem_aborta_na_releitura(self, base: Path, fonte: Fonte):
        """A contagem bate (1 e 1), mas a troca cairia no comentário e a entrada ficaria com o texto velho."""
        (base / "fases.yml").write_text(
            "# descricao_oficial: Situação 900\n"
            "regras:\n  - id: R3\n    situacoes_camara:\n"
            '      - cod: "900"\n        descricao_oficial: >-\n          Situação 900\n',
            encoding="utf-8",
        )
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_filtra_a_casa_em_marcos(self, base: Path, fonte: Fonte):
        """O mesmo número em outra Casa é outro código: renomear o da Câmara não passa por ele."""
        (base / "marcos.yml").write_text(
            "marcos:\n"
            '  - {cod: "100", casa: senado, descricao_oficial: Outra Casa}\n'
            '  - {cod: "100", casa: camara, descricao_oficial: Tramitação 100}\n'
            "ignorados:\n"
            '  - {cod: "100", casa: senado, descricao_oficial: Outra Casa}\n',
            encoding="utf-8",
        )
        fonte.tramitacao[0] = item_camara("100", "Tramitação Nova")

        assert rodar(base, fonte) == 0

        marcos = yaml.safe_load((base / "marcos.yml").read_text(encoding="utf-8"))
        assert marcos["marcos"][0]["descricao_oficial"] == "Outra Casa"
        assert marcos["marcos"][1]["descricao_oficial"] == "Tramitação Nova"
        assert marcos["ignorados"][0]["descricao_oficial"] == "Outra Casa"

    def test_filtra_a_casa_no_glossario(self, base: Path, fonte: Fonte, capsys):
        (base / "glossario.yml").write_text(
            "entradas:\n"
            "  - chave: do_senado\n"
            '    codigos: [{casa: senado, cod: "900"}]\n'
            "    descricao_oficial: Situação 900\n",
            encoding="utf-8",
        )
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert "Situação 900" in (base / "glossario.yml").read_text(encoding="utf-8")
        assert afetadas(capsys.readouterr().out) == []

    def test_entrada_compartilhada_do_glossario_aborta_e_pede_decisao(self, tmp_path: Path, fonte: Fonte, capsys):
        """A entrada tem uma descrição só: trocá-la deixaria o 2382 diferente do snapshot, com exit 0."""
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "glossario.yml").write_text(GLOSSARIO_COMPARTILHADO, encoding="utf-8")
        fonte.situacoes[-2] = item_camara("1905", "Diferente")
        antes = conteudo(tmp_path)
        capsys.readouterr()

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == antes
        decisao = decisoes(capsys.readouterr().out)
        assert "glossario/igual cobre também 2382" in decisao
        assert "separe a entrada" in decisao

    def test_entrada_compartilhada_aborta_mesmo_ajustada_a_mao(self, tmp_path: Path, fonte: Fonte):
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "glossario.yml").write_text(
            GLOSSARIO_COMPARTILHADO.replace("descricao_oficial: Igual", "descricao_oficial: Diferente"),
            encoding="utf-8",
        )
        fonte.situacoes[-2] = item_camara("1905", "Diferente")
        antes = conteudo(tmp_path)

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == antes

    def test_entrada_compartilhada_com_os_dois_renomeados_juntos_passa(self, tmp_path: Path, fonte: Fonte):
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "glossario.yml").write_text(GLOSSARIO_COMPARTILHADO, encoding="utf-8")
        fonte.situacoes[-2] = item_camara("1905", "Diferente")
        fonte.situacoes[-1] = item_camara("2382", "Diferente")

        assert rodar(tmp_path, fonte) == 0

        dados = yaml.safe_load((tmp_path / "glossario.yml").read_text(encoding="utf-8"))
        assert dados["entradas"][0]["descricao_oficial"] == "Diferente"

    def test_entrada_compartilhada_para_textos_diferentes_aborta(self, tmp_path: Path, fonte: Fonte):
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "glossario.yml").write_text(GLOSSARIO_COMPARTILHADO, encoding="utf-8")
        fonte.situacoes[-2] = item_camara("1905", "Texto A")
        fonte.situacoes[-1] = item_camara("2382", "Texto B")
        antes = conteudo(tmp_path)

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == antes

    def test_entrada_com_as_duas_casas_exige_as_duas_renomeadas(self, base: Path, fonte: Fonte):
        """O mesmo número na outra Casa é outro código, então não conta como renomeado junto."""
        (base / "glossario.yml").write_text(
            "entradas:\n"
            "  - chave: duas_casas\n"
            '    codigos: [{casa: camara, cod: "900"}, {casa: senado, cod: "900"}]\n'
            "    descricao_oficial: Situação 900\n",
            encoding="utf-8",
        )
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_entrada_separada_a_mao_passa(self, tmp_path: Path, fonte: Fonte):
        """A saída do aborto da entrada compartilhada: cada código na sua entrada."""
        fonte.situacoes += [item_camara("1905", "Igual"), item_camara("2382", "Igual")]
        assert rodar(tmp_path, fonte, hoje=CARGA) == 0
        (tmp_path / "glossario.yml").write_text(
            "entradas:\n"
            "  - chave: um\n"
            '    codigos: [{casa: camara, cod: "1905"}]\n'
            "    descricao_oficial: Diferente\n"
            "  - chave: outro\n"
            '    codigos: [{casa: camara, cod: "2382"}]\n'
            "    descricao_oficial: Igual\n",
            encoding="utf-8",
        )
        fonte.situacoes[-2] = item_camara("1905", "Diferente")

        assert rodar(tmp_path, fonte) == 0

        assert carregar_snapshot(tmp_path, SITUACOES)["itens"][-2]["nome"] == "Diferente"

    def test_mesmo_numero_em_outra_tabela_e_outro_codigo(self, base: Path, fonte: Fonte):
        """900 de situação e 900 de tramitação não têm relação; o mesmo vale para o 100 ao contrário."""
        marcos = 'marcos:\n  - {cod: "900", casa: camara, descricao_oficial: Outra tabela}\n'
        fases = 'regras:\n  - id: R3\n    situacoes_camara:\n      - {cod: "100", descricao_oficial: Outra tabela}\n'
        (base / "marcos.yml").write_text(marcos, encoding="utf-8")
        (base / "fases.yml").write_text(fases, encoding="utf-8")
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        fonte.tramitacao[0] = item_camara("100", "Tramitação Nova")

        assert rodar(base, fonte) == 0

        assert (base / "marcos.yml").read_text(encoding="utf-8") == marcos
        assert (base / "fases.yml").read_text(encoding="utf-8") == fases

    @pytest.mark.parametrize("tabela", ["tramitacao", "orgaos"])
    def test_renomeado_de_outra_tabela_na_mesma_execucao_do_glossario(self, base: Path, fonte: Fonte, tabela: str):
        escrever_yamls(base)
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        itens = getattr(fonte, tabela)
        itens[5] = item_camara(itens[5]["cod"], "Situação Nova")

        assert rodar(base, fonte) == 0

        dados = yaml.safe_load((base / "glossario.yml").read_text(encoding="utf-8"))
        assert dados["entradas"][0]["descricao_oficial"] == "Situação Nova"

    def test_entrada_ajustada_a_mao_com_espaco_sobrando_conta_como_ajustada(self, base: Path, fonte: Fonte):
        original = 'regras:\n  - id: R3\n    situacoes_camara:\n      - {cod: "900", descricao_oficial: "Situação Nova "}\n'
        (base / "fases.yml").write_text(original, encoding="utf-8")
        fonte.situacoes[0] = item_camara("900", "Situação Nova")

        assert rodar(base, fonte) == 0

        assert (base / "fases.yml").read_text(encoding="utf-8") == original

    def test_yaml_vazio_nao_tem_onde_agir(self, base: Path, fonte: Fonte):
        (base / "fases.yml").write_text("", encoding="utf-8")
        fonte.situacoes[0] = item_camara("900", "Situação Nova")

        assert rodar(base, fonte) == 0

        assert (base / "fases.yml").read_text(encoding="utf-8") == ""

    def test_yaml_que_nao_e_mapeamento_aborta(self, base: Path, fonte: Fonte):
        (base / "fases.yml").write_text("- solta\n", encoding="utf-8")
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_troca_que_quebra_o_yaml_aborta_sem_traceback(self, base: Path, fonte: Fonte, monkeypatch):
        """Defesa em profundidade: o escape de hoje não produz YAML inválido, então o defeito é forçado."""
        escrever_yamls(base)
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        monkeypatch.setattr(referencias, "_escalar_yaml", lambda valor: "[quebrado")
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_entrada_com_descricao_divergente_aborta(self, base: Path, fonte: Fonte):
        (base / "fases.yml").write_text(
            'regras:\n  - id: R3\n    situacoes_camara:\n      - {cod: "900", descricao_oficial: Outra coisa}\n',
            encoding="utf-8",
        )
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_descricao_dobrada_em_duas_linhas_aborta(self, base: Path, fonte: Fonte):
        (base / "fases.yml").write_text(
            "regras:\n  - id: R3\n    situacoes_camara:\n"
            '      - cod: "900"\n        descricao_oficial: >-\n          Situação 900\n',
            encoding="utf-8",
        )
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_yaml_quebrado_aborta(self, base: Path, fonte: Fonte):
        (base / "fases.yml").write_text("regras: [", encoding="utf-8")
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes


FASES_COM_R7 = """\
regras:
  - id: R7
    parametros:
      siglas_plenario: ["PLEN", "4"]
      tipos_orgao_comissao: ["2", "3"]
"""


class TestRemovido:
    def test_nao_mexe_no_mapeamento_e_lista_a_decisao(self, base: Path, fonte: Fonte, capsys):
        escrever_yamls(base)
        del fonte.situacoes[0]
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert (base / "fases.yml").read_text(encoding="utf-8") == FASES
        assert (base / "glossario.yml").read_text(encoding="utf-8") == GLOSSARIO
        assert carregar_snapshot(base, SITUACOES)["total"] == 19
        saida = capsys.readouterr().out
        assert afetadas(saida) == ["fases/regra_R3", "glossario/situacao_novecentos"]
        assert (
            'camara-situacoes.json: código 900 ("Situação 900") saiu da fonte; '
            "entradas: fases/regra_R3, glossario/situacao_novecentos." in decisoes(saida)
        )

    def test_sem_entrada_diz_nenhuma(self, base: Path, fonte: Fonte, capsys):
        del fonte.situacoes[0]
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert "entradas: nenhuma." in decisoes(capsys.readouterr().out)

    def test_tipo_de_orgao_em_uso_na_r7_aponta_a_regra(self, base: Path, fonte: Fonte, capsys):
        (base / "fases.yml").write_text(FASES_COM_R7, encoding="utf-8")
        del fonte.orgaos[1]  # código 2
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert (base / "fases.yml").read_text(encoding="utf-8") == FASES_COM_R7
        saida = capsys.readouterr().out
        assert afetadas(saida) == ["fases/regra_R7"]
        assert (
            'camara-tipos-orgao.json: código 2 ("Órgão 2") saiu da fonte; entradas: fases/regra_R7.'
            in decisoes(saida)
        )

    def test_tipo_de_orgao_fora_da_r7_nao_aponta_a_regra(self, base: Path, fonte: Fonte, capsys):
        (base / "fases.yml").write_text(FASES_COM_R7, encoding="utf-8")
        del fonte.orgaos[3]  # código 4
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert "entradas: nenhuma." in decisoes(capsys.readouterr().out)

    def test_tipo_de_orgao_renomeado_em_uso_aponta_a_regra_sem_mexer_nela(self, base: Path, fonte: Fonte, capsys):
        (base / "fases.yml").write_text(FASES_COM_R7, encoding="utf-8")
        fonte.orgaos[1] = item_camara("2", "Órgão Renomeado")
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert (base / "fases.yml").read_text(encoding="utf-8") == FASES_COM_R7
        assert afetadas(capsys.readouterr().out) == ["fases/regra_R7"]


class TestRecusaDeGravacao:
    def test_tabela_vazia_e_recusada_mesmo_com_a_flag(self, base: Path, fonte: Fonte):
        fonte.senado = []
        antes = conteudo(base)

        assert rodar(base, fonte, "--aceitar-remocoes") == 1

        assert conteudo(base) == antes

    def test_queda_grande_recusa_tudo_sem_a_flag(self, base: Path, fonte: Fonte):
        fonte.situacoes = fonte.situacoes[:17]
        fonte.tramitacao.append(item_camara("1234", "Nova"))
        antes = conteudo(base)

        assert rodar(base, fonte) == 1

        assert conteudo(base) == antes

    def test_queda_grande_passa_com_a_flag(self, base: Path, fonte: Fonte):
        fonte.situacoes = fonte.situacoes[:17]

        assert rodar(base, fonte, "--aceitar-remocoes") == 0

        assert carregar_snapshot(base, SITUACOES)["total"] == 17

    def test_queda_de_dez_por_cento_passa(self, base: Path, fonte: Fonte):
        fonte.situacoes = fonte.situacoes[:18]

        assert rodar(base, fonte) == 0

        assert carregar_snapshot(base, SITUACOES)["total"] == 18


class TestGravacaoInterrompida:
    @staticmethod
    def preparar(diretorio: Path, fonte: Fonte) -> None:
        assert rodar(diretorio, fonte, hoje=CARGA) == 0
        escrever_yamls(diretorio)

    @staticmethod
    def mudar(fonte: Fonte) -> None:
        fonte.situacoes[0] = item_camara("900", "Situação Nova")
        fonte.situacoes.append(item_camara("9999", "Nova"))
        fonte.tramitacao[0] = item_camara("100", "Tramitação Nova")

    def test_falha_ao_escrever_temporario_nao_muda_nada(self, tmp_path: Path, fonte: Fonte, monkeypatch):
        self.preparar(tmp_path, fonte)
        self.mudar(fonte)
        antes = conteudo(tmp_path)
        original = Path.write_bytes
        chamadas = []

        def falhar_no_terceiro(caminho: Path, dados: bytes) -> int:
            chamadas.append(caminho)
            if len(chamadas) == 3:
                raise OSError("disco cheio")
            return original(caminho, dados)

        monkeypatch.setattr(Path, "write_bytes", falhar_no_terceiro)

        assert rodar(tmp_path, fonte) == 1

        assert conteudo(tmp_path) == antes

    def test_snapshots_sao_trocados_por_ultimo(self, tmp_path: Path, fonte: Fonte, monkeypatch):
        self.preparar(tmp_path, fonte)
        self.mudar(fonte)
        trocados: list[str] = []
        original = script.os.replace

        def registrar(origem: Path, destino: Path) -> None:
            trocados.append(destino.parent.name)
            original(origem, destino)

        monkeypatch.setattr(script.os, "replace", registrar)

        assert rodar(tmp_path, fonte) == 0

        primeiro_snapshot = trocados.index("referencias")
        assert primeiro_snapshot > 0
        assert set(trocados[primeiro_snapshot:]) == {"referencias"}

    @pytest.mark.parametrize("trocas_antes_de_falhar", range(6))
    def test_rodar_de_novo_termina_o_trabalho(
        self, tmp_path: Path, fonte: Fonte, monkeypatch, trocas_antes_de_falhar: int
    ):
        """Promessa da docstring: em qualquer ponto da falha, a segunda execução chega ao mesmo estado."""
        limpo = tmp_path / "limpo"
        interrompido = tmp_path / "interrompido"
        limpo.mkdir()
        interrompido.mkdir()
        self.preparar(limpo, fonte)
        self.preparar(interrompido, fonte)
        self.mudar(fonte)
        assert rodar(limpo, fonte) == 0
        original = script.os.replace
        trocas: list[Path] = []

        def falhar(origem: Path, destino: Path) -> None:
            if len(trocas) == trocas_antes_de_falhar:
                raise OSError("falha simulada")
            trocas.append(destino)
            original(origem, destino)

        with monkeypatch.context() as contexto:
            contexto.setattr(script.os, "replace", falhar)
            assert rodar(interrompido, fonte) == 1

        assert not list(interrompido.rglob("*.tmp"))
        assert len(trocas) == trocas_antes_de_falhar

        assert rodar(interrompido, fonte) == 0

        assert conteudo(interrompido) == conteudo(limpo)


class TestEntradasAfetadas:
    def test_codigo_novo_aparece_para_o_lote(self, base: Path, fonte: Fonte, capsys):
        fonte.tramitacao.append(item_camara("1234", "Nova"))
        capsys.readouterr()

        assert rodar(base, fonte) == 0

        assert "nao_mapeados/tramitacao_camara/1234" in capsys.readouterr().out

    def test_nao_cria_lotes_yml(self, base: Path, fonte: Fonte):
        fonte.tramitacao.append(item_camara("1234", "Nova"))

        assert rodar(base, fonte) == 0

        assert not (base / "lotes.yml").exists()


# ── Os arquivos commitados ───────────────────────────────────────────────────


DIRETORIO_REAL = REPO_ROOT / "data" / "tramitacao"


@pytest.mark.parametrize("arquivo", sorted(TABELAS))
def test_snapshot_commitado_e_coerente(arquivo: str):
    snapshot = carregar_snapshot(DIRETORIO_REAL, arquivo)
    texto = (DIRETORIO_REAL / "referencias" / arquivo).read_text(encoding="utf-8")

    assert snapshot["fonte"] == TABELAS[arquivo][0]
    assert snapshot["total"] == len(snapshot["itens"]) > 0
    assert serializar(snapshot) == texto
    codigos = [i["cod"] for i in snapshot["itens"]]
    assert len(codigos) == len(set(codigos))
    chave = (lambda c: c) if arquivo == SENADO else int
    assert codigos == sorted(codigos, key=chave)

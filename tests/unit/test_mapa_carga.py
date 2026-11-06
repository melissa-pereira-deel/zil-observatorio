"""TRM-021a: esquema de data/tramitacao/, carga, hash e publicação (spec 013 §6.2 e §6.8).

As entradas aqui são sintéticas: exercitam o esquema e não dizem nada sobre o processo legislativo.
O conteúdo de verdade é de TRM-021b e passa pela revisão de TRM-023.
"""

import ast
import copy
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import get_args

import pytest
import yaml
from pydantic import BaseModel, ValidationError

from packages.tramitacao import mapa as modulo_mapa
from packages.tramitacao import revisao as modulo_revisao
from packages.tramitacao import tipos as modulo_tipos
from packages.tramitacao.mapa import (
    ArquivoNaoMapeados,
    BaseLegal,
    MapaIndisponivel,
    MapaInvalido,
    carregar_mapa,
    carregar_mapa_producao,
)
from packages.tramitacao.revisao import (
    ArquivoRevisao,
    Consolidado,
    Decisao,
    EstadoEntrada,
    entradas_publicaveis,
    hash_entrada,
    ids_de_conteudo,
)

REPO = Path(__file__).resolve().parents[2]
DADOS_REPO = REPO / "data" / "tramitacao"

CF = "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"
FONTE = "https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao"

# Calculado fora do Python, para o teste não provar a função com ela mesma:
#   printf '%s' '{"chave":"comissoes","fontes":["https://exemplo.invalid/a"],"ordem":2,"pendente":null,"rotulo":"Nas comissões"}' \
#     | shasum -a 256 | cut -c1-12
# Conferido também com `openssl dgst -sha256`.
ENTRADA_FIXA = {
    "rotulo": "Nas comissões",
    "ordem": 2,
    "pendente": None,
    "fontes": ["https://exemplo.invalid/a"],
    "chave": "comissoes",
}
HASH_FIXO = "d21ab6d1d082"  # pragma: allowlist secret


def _procedencia() -> dict:
    return {
        "base_legal": [{"norma": "CF", "dispositivo": "art. 61", "url": CF}],
        "fontes": [FONTE],
    }


def _caso() -> dict:
    return {"casa": "camara", "fonte_id": "1", "rotulo": "PL 1/2000"}


def _frases() -> list[dict]:
    return [{"quando": ["da_casa"], "modelo": "Nas comissões {da_casa}."}, {"modelo": "Nas comissões."}]


def _arquivos() -> dict[str, dict]:
    """Um exemplo de cada tipo de entrada, válido para o esquema."""
    etapa = {
        "id": "etapa_um",
        "fase": "comissoes",
        "casa": "camara",
        "nome": "Etapa",
        "o_que_acontece": "Texto sintético.",
        **_procedencia(),
    }
    return {
        "fases.yml": {
            "versao_esquema": 1,
            "normas_base": {"CF": {"nome": "Constituição Federal", "url": CF}},
            "fases": [
                {
                    "chave": "comissoes",
                    "ordem": 2,
                    "rotulo": "Nas comissões",
                    "rotulo_por_especie": {"MPV": "Na comissão mista"},
                    "pergunta": "Quem analisa e dá parecer",
                    "frases": _frases(),
                    **_procedencia(),
                }
            ],
            "desfechos": [
                {"chave": "arquivada", "rotulo": "Arquivada", "frases": _frases(), **_procedencia()}
            ],
            "apensada": {"rotulo": "Apensada", "frases": _frases(), **_procedencia()},
            "regras": [
                {
                    "id": "R3",
                    "tipo": "situacao_terminal",
                    "descricao": "Texto sintético.",
                    "situacoes_camara": [
                        {"cod": "923", "descricao_oficial": "Arquivada", "desfecho": "arquivada"}
                    ],
                    "casos": [_caso()],
                    **_procedencia(),
                }
            ],
        },
        "marcos.yml": {
            "versao_esquema": 1,
            "marcos": [
                {
                    "cod": "320",
                    "casa": "camara",
                    "descricao_oficial": "Descrição sintética",
                    "marco": "parecer",
                    "titulo": "Título",
                    "variantes": [{"padrao_despacho": "x", "marco": "arquivamento"}],
                    "casos": [_caso()],
                    **_procedencia(),
                }
            ],
            "ignorados": [{"cod": "604", "descricao_oficial": "Publicação", "nota": "não muda a fase"}],
        },
        "ritos.yml": {
            "versao_esquema": 1,
            "especies": [{"sigla": "PL", "nome": "Projeto de lei ordinária"}],
            "ritos": [
                {
                    "especie": "PL",
                    "casa_iniciadora": "camara",
                    "nome": "Rito sintético",
                    "etapas": [
                        etapa,
                        {**etapa, "id": "etapa_dois", "fase": "plenario"},
                        {**etapa, "id": "etapa_tres", "fase": "norma", "casa": None},
                    ],
                    "desfechos": [
                        {
                            "desfecho": "arquivada",
                            "a_partir_de": ["etapa_um"],
                            "texto": "Texto sintético.",
                            **_procedencia(),
                        },
                        {
                            "desfecho": "rejeitada",
                            "a_partir_de": "qualquer",
                            "texto": "Texto sintético.",
                            **_procedencia(),
                        },
                    ],
                    **_procedencia(),
                }
            ],
            "pos_lei": {
                "itens": [
                    {"id": "publicacao", "nome": "Publicação", "texto": "Texto.", **_procedencia()},
                    {"id": "vigencia", "nome": "Vigência", "texto": "Texto.", **_procedencia()},
                    {"id": "regulamentacao", "nome": "Regulamentação", "texto": "Texto.", **_procedencia()},
                ],
                **_procedencia(),
            },
        },
        "glossario.yml": {
            "versao_esquema": 1,
            "aviso": "Texto do ZIL, não oficial.",
            "entradas": [
                {
                    "chave": "aguardando_parecer",
                    "tipo": "situacao",
                    "termo": "Aguardando Parecer",
                    "texto_curto": "Texto curto sintético, com mais de vinte caracteres.",
                    "texto": "Texto sintético, com mais de quarenta caracteres para valer.",
                    "codigos": [{"casa": "camara", "cod": "915"}],
                    "exemplos": [{"proposicao": "PL 1/2000", "casa": "camara", "fonte_id": "1"}],
                    **_procedencia(),
                }
            ],
        },
        "nao_mapeados.yml": {
            "versao_esquema": 1,
            "situacoes_camara": [
                {"cod": "1250", "descricao_oficial": "Descrição sintética", "motivo": "inativo"}
            ],
            "situacoes_senado": [
                {"cod": "TNJR", "descricao_oficial": "Descrição sintética", "motivo": "sem_evidencia"}
            ],
            "tramitacao_camara": [
                {"cod": "1236", "descricao_oficial": "Descrição sintética", "motivo": "codigo_novo_2026-11-05"}
            ],
        },
        "revisao.yml": {"versao_publicada": 0, "entradas": {}},
    }


def _gravar(diretorio: Path, arquivos: dict[str, dict]) -> Path:
    diretorio.mkdir(parents=True, exist_ok=True)
    for nome, dados in arquivos.items():
        (diretorio / nome).write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
    return diretorio


def _estado(estado: str, hash_: str = HASH_FIXO) -> EstadoEntrada:
    return EstadoEntrada(estado=estado, hash=hash_)


class TestRepositorio:
    def test_carrega_os_arquivos_do_repositorio_sem_mapa_invalido(self, monkeypatch):
        monkeypatch.delenv("ZIL_DATA_DIR", raising=False)
        mapa = carregar_mapa()
        assert mapa.aviso_glossario

    def test_versao_zero_implica_nada_aprovado(self):
        # versao_publicada sobe a cada aprovação (§2.1-5): enquanto for 0, nada pode estar aprovado.
        bruto = yaml.safe_load((DADOS_REPO / "revisao.yml").read_text(encoding="utf-8"))
        revisao = ArquivoRevisao.model_validate(bruto)
        if revisao.versao_publicada == 0:
            assert revisao.entradas == {}
            assert carregar_mapa(DADOS_REPO).publicaveis == frozenset()

    def test_nao_mapeados_tem_as_tres_listas_do_formato(self):
        bruto = yaml.safe_load((DADOS_REPO / "nao_mapeados.yml").read_text(encoding="utf-8"))
        ArquivoNaoMapeados.model_validate(bruto)
        assert set(bruto) == {"versao_esquema", "situacoes_camara", "situacoes_senado", "tramitacao_camara"}

    def test_a_carga_nao_exige_os_snapshots_de_referencias(self, tmp_path):
        destino = tmp_path / "tramitacao"
        destino.mkdir()
        for arquivo in DADOS_REPO.glob("*.yml"):
            shutil.copy(arquivo, destino)
        assert not (destino / "referencias").exists()
        carregar_mapa(destino)


class TestCampoDesconhecido:
    @pytest.mark.parametrize(
        ("arquivo", "navegar", "caminho"),
        [
            ("fases.yml", lambda d: d, "campo_x"),
            ("fases.yml", lambda d: d["normas_base"]["CF"], "normas_base.CF.campo_x"),
            ("fases.yml", lambda d: d["fases"][0], "fases[0].campo_x"),
            ("fases.yml", lambda d: d["fases"][0]["frases"][1], "fases[0].frases[1].campo_x"),
            ("fases.yml", lambda d: d["fases"][0]["base_legal"][0], "fases[0].base_legal[0].campo_x"),
            ("fases.yml", lambda d: d["desfechos"][0], "desfechos[0].campo_x"),
            ("fases.yml", lambda d: d["apensada"], "apensada.campo_x"),
            ("fases.yml", lambda d: d["regras"][0]["situacoes_camara"][0], "regras[0].situacoes_camara[0].campo_x"),
            ("fases.yml", lambda d: d["regras"][0]["casos"][0], "regras[0].casos[0].campo_x"),
            ("marcos.yml", lambda d: d["marcos"][0]["variantes"][0], "marcos[0].variantes[0].campo_x"),
            ("marcos.yml", lambda d: d["ignorados"][0], "ignorados[0].campo_x"),
            ("ritos.yml", lambda d: d["ritos"][0]["etapas"][2], "ritos[0].etapas[2].campo_x"),
            ("ritos.yml", lambda d: d["ritos"][0]["desfechos"][0], "ritos[0].desfechos[0].campo_x"),
            ("ritos.yml", lambda d: d["especies"][0], "especies[0].campo_x"),
            ("ritos.yml", lambda d: d["pos_lei"]["itens"][1], "pos_lei.itens[1].campo_x"),
            ("glossario.yml", lambda d: d["entradas"][0]["codigos"][0], "entradas[0].codigos[0].campo_x"),
            ("glossario.yml", lambda d: d["entradas"][0]["exemplos"][0], "entradas[0].exemplos[0].campo_x"),
            ("glossario.yml", lambda d: d, "campo_x"),
            ("marcos.yml", lambda d: d, "campo_x"),
            ("ritos.yml", lambda d: d, "campo_x"),
            ("nao_mapeados.yml", lambda d: d, "campo_x"),
            ("nao_mapeados.yml", lambda d: d["tramitacao_camara"][0], "tramitacao_camara[0].campo_x"),
            ("revisao.yml", lambda d: d, "campo_x"),
        ],
    )
    def test_levanta_mapa_invalido_citando_arquivo_e_caminho(self, tmp_path, arquivo, navegar, caminho):
        arquivos = _arquivos()
        navegar(arquivos[arquivo])["campo_x"] = "qualquer"
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert any(p.startswith(f"{arquivo}: {caminho}") for p in erro.value.problemas), erro.value.problemas

    def test_estado_de_revisao_com_campo_desconhecido(self, tmp_path):
        arquivos = _arquivos()
        arquivos["revisao.yml"]["entradas"]["fases/fase_comissoes"] = {
            "estado": "rascunho",
            "hash": HASH_FIXO,
            "campo_x": 1,
        }
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert "revisao.yml: entradas.fases/fase_comissoes.campo_x" in str(erro.value)

    def test_acumula_os_erros_de_todos_os_arquivos(self, tmp_path):
        arquivos = _arquivos()
        arquivos["fases.yml"]["fases"][0]["campo_x"] = 1
        arquivos["marcos.yml"]["marcos"][0]["campo_y"] = 1
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        problemas = erro.value.problemas
        assert any(p.startswith("fases.yml: fases[0].campo_x") for p in problemas)
        assert any(p.startswith("marcos.yml: marcos[0].campo_y") for p in problemas)


class TestEsquema:
    def test_o_exemplo_completo_carrega(self, tmp_path):
        mapa = carregar_mapa(_gravar(tmp_path, _arquivos()))
        assert set(mapa.fases) == {"comissoes"}
        assert set(mapa.desfechos) == {"arquivada"}
        assert mapa.apensada is not None
        assert set(mapa.regras) == {"R3"}
        assert mapa.situacao_por_codigo[("camara", "923")][0] == "R3"
        assert mapa.situacao_por_codigo[("camara", "923")][1].desfecho == "arquivada"
        assert set(mapa.marcos) == {("camara", "320")}
        assert set(mapa.ignorados) == {("camara", "604")}
        assert set(mapa.ritos) == {"PL_CD"}
        assert set(mapa.especies) == {"PL"}
        assert mapa.pos_lei is not None
        assert set(mapa.glossario) == {"aguardando_parecer"}
        assert set(mapa.nao_mapeados_situacao) == {("camara", "1250"), ("senado", "TNJR")}
        assert set(mapa.nao_mapeados_tramitacao) == {("camara", "1236")}

    @pytest.mark.parametrize(
        ("mutar", "trecho"),
        [
            (lambda a: a["fases.yml"]["fases"][0].update(chave="inventada"), "fases.yml: fases[0].chave"),
            (lambda a: a["fases.yml"]["fases"][0].update(rotulo="x" * 33), "fases.yml: fases[0].rotulo"),
            (
                lambda a: a["fases.yml"]["fases"][0]["rotulo_por_especie"].update(MPV="x" * 33),
                "fases.yml: fases[0].rotulo_por_especie.MPV",
            ),
            (lambda a: a["fases.yml"]["regras"][0].update(casos=[]), "fases.yml: regras[0].casos"),
            (lambda a: a["fases.yml"]["regras"][0].update(id="R11"), "fases.yml: regras[0].id"),
            (lambda a: a["marcos.yml"]["marcos"][0].update(cod=320), "marcos.yml: marcos[0].cod"),
            (lambda a: a["marcos.yml"]["marcos"][0].update(casos=[]), "marcos.yml: marcos[0].casos"),
            (lambda a: a["ritos.yml"]["ritos"][0].update(casa_iniciadora="presidencia"), "ritos.yml: ritos[0].casa_iniciadora"),
            (lambda a: a["ritos.yml"]["pos_lei"]["itens"].pop(), "ritos.yml: pos_lei.itens"),
            (lambda a: a["glossario.yml"]["entradas"][0].update(chave="Maiuscula"), "glossario.yml: entradas[0].chave"),
            (lambda a: a["glossario.yml"]["entradas"][0].update(texto_curto="curto"), "glossario.yml: entradas[0].texto_curto"),
            (
                lambda a: a["nao_mapeados.yml"]["situacoes_camara"][0].update(motivo="porque_sim"),
                "nao_mapeados.yml: situacoes_camara[0].motivo",
            ),
            (
                lambda a: a["nao_mapeados.yml"]["situacoes_camara"][0].update(motivo="fora_do_escopo"),
                "nao_mapeados.yml: situacoes_camara[0]",
            ),
            (lambda a: a["revisao.yml"].update(versao_publicada=-1), "revisao.yml: versao_publicada"),
        ],
    )
    def test_valor_fora_do_esquema(self, tmp_path, mutar, trecho):
        arquivos = _arquivos()
        mutar(arquivos)
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert trecho in str(erro.value)

    def test_estado_fora_do_contrato(self, tmp_path):
        arquivos = _arquivos()
        arquivos["revisao.yml"]["entradas"]["fases/fase_comissoes"] = {"estado": "publicado", "hash": HASH_FIXO}
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert "revisao.yml: entradas.fases/fase_comissoes.estado" in str(erro.value)

    def test_base_legal_e_motivo_juntos(self, tmp_path):
        arquivos = _arquivos()
        arquivos["fases.yml"]["fases"][0]["base_legal_motivo"] = "Critério interno do ZIL, por escrito."
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert "fases.yml: fases[0]" in str(erro.value)

    def test_nem_base_legal_nem_motivo(self, tmp_path):
        arquivos = _arquivos()
        arquivos["fases.yml"]["fases"][0]["base_legal"] = []
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert "fases.yml: fases[0]" in str(erro.value)

    def test_base_legal_motivo_sem_artigo_e_aceito(self, tmp_path):
        arquivos = _arquivos()
        arquivos["fases.yml"]["fases"][0].pop("base_legal")
        arquivos["fases.yml"]["fases"][0]["base_legal_motivo"] = "Critério interno do ZIL, por escrito."
        assert carregar_mapa(_gravar(tmp_path, arquivos)).fases["comissoes"].base_legal == []

    @pytest.mark.parametrize(
        "url",
        ["https://exemplo.invalid/norma", "http://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"],
    )
    def test_url_de_base_legal_fora_da_allowlist(self, url):
        with pytest.raises(ValidationError):
            BaseLegal(norma="CF", dispositivo="art. 61", url=url)

    @pytest.mark.parametrize(
        ("mutar", "trecho"),
        [
            (lambda a: a["fases.yml"]["fases"][0]["frases"][0].update(quando=["da_casa", "da_casa"]), "frases[0].quando"),
            (lambda a: a["fases.yml"]["fases"][0].update(fontes=[FONTE, FONTE]), "fases[0].fontes"),
            (lambda a: a["marcos.yml"]["marcos"][0].update(reabre=["arquivada", "arquivada"]), "marcos[0].reabre"),
        ],
    )
    def test_lista_que_e_conjunto_nao_aceita_duplicata(self, tmp_path, mutar, trecho):
        arquivos = _arquivos()
        mutar(arquivos)
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert trecho in str(erro.value)

    def test_texto_e_aparado(self, tmp_path):
        arquivos = _arquivos()
        arquivos["fases.yml"]["fases"][0]["rotulo"] = "  Nas comissões  "
        assert carregar_mapa(_gravar(tmp_path, arquivos)).fases["comissoes"].rotulo == "Nas comissões"

    @pytest.mark.parametrize(
        ("mutar", "trecho"),
        [
            (lambda a: a["fases.yml"]["fases"].append(copy.deepcopy(a["fases.yml"]["fases"][0])), "fases.yml: fases[1]"),
            (
                lambda a: a["fases.yml"]["desfechos"].append(copy.deepcopy(a["fases.yml"]["desfechos"][0])),
                "fases.yml: desfechos[1]",
            ),
            (lambda a: a["fases.yml"]["regras"].append(copy.deepcopy(a["fases.yml"]["regras"][0])), "fases.yml: regras[1]"),
            (lambda a: a["marcos.yml"]["marcos"].append(copy.deepcopy(a["marcos.yml"]["marcos"][0])), "marcos.yml: marcos[1]"),
            (
                lambda a: a["marcos.yml"]["ignorados"].append(copy.deepcopy(a["marcos.yml"]["ignorados"][0])),
                "marcos.yml: ignorados[1]",
            ),
            (lambda a: a["ritos.yml"]["ritos"].append(copy.deepcopy(a["ritos.yml"]["ritos"][0])), "ritos.yml: ritos[1]"),
            (
                lambda a: a["ritos.yml"]["especies"].append(copy.deepcopy(a["ritos.yml"]["especies"][0])),
                "ritos.yml: especies[1]",
            ),
            (
                lambda a: a["glossario.yml"]["entradas"].append(copy.deepcopy(a["glossario.yml"]["entradas"][0])),
                "glossario.yml: entradas[1]",
            ),
            (
                lambda a: a["nao_mapeados.yml"]["tramitacao_camara"].append(
                    copy.deepcopy(a["nao_mapeados.yml"]["tramitacao_camara"][0])
                ),
                "nao_mapeados.yml: tramitacao_camara[1]",
            ),
        ],
    )
    def test_chave_repetida_nao_some_em_silencio(self, tmp_path, mutar, trecho):
        # Dois itens com a mesma chave colidiriam no índice: um deles deixaria de existir sem aviso,
        # e o hash conferido na publicação seria o do sobrevivente.
        arquivos = _arquivos()
        mutar(arquivos)
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert trecho in str(erro.value)

    def test_situacao_em_duas_regras(self, tmp_path):
        arquivos = _arquivos()
        regra = copy.deepcopy(arquivos["fases.yml"]["regras"][0])
        regra["id"] = "R2"
        arquivos["fases.yml"]["regras"].append(regra)
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert "fases.yml: regras[1].situacoes_camara[0]" in str(erro.value)

    @pytest.mark.parametrize("conteudo", ["", "- uma\n- lista\n", "chave: [sem fechar\n"])
    def test_arquivo_vazio_ou_quebrado_e_invalido(self, tmp_path, conteudo):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "marcos.yml").write_text(conteudo, encoding="utf-8")
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(diretorio)
        assert "marcos.yml" in str(erro.value)


class TestDiretorio:
    def test_diretorio_inexistente(self, tmp_path):
        with pytest.raises(MapaIndisponivel, match="diretório inexistente"):
            carregar_mapa(tmp_path / "nao_existe")

    def test_zil_data_dir_e_respeitado(self, tmp_path, monkeypatch):
        arquivos = _arquivos()
        _gravar(tmp_path / "tramitacao", arquivos)
        monkeypatch.setenv("ZIL_DATA_DIR", str(tmp_path))
        assert set(carregar_mapa().fases) == {"comissoes"}

    def test_zil_data_dir_inexistente_nao_cai_em_outro_lugar(self, tmp_path, monkeypatch):
        # Quem definiu a variável disse onde os dados estão. Cair no repositório em silêncio
        # serviria dados de outro lugar sem ninguém saber.
        monkeypatch.setenv("ZIL_DATA_DIR", str(tmp_path / "nao_existe"))
        with pytest.raises(MapaIndisponivel):
            carregar_mapa()

    def test_resolver_cita_zil_data_dir_quando_ela_erra(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZIL_DATA_DIR", str(tmp_path / "nao_existe"))
        with pytest.raises(MapaIndisponivel, match="ZIL_DATA_DIR"):
            modulo_mapa.resolver_diretorio()

    def test_zil_data_dir_vazio_conta_como_nao_definido(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZIL_DATA_DIR", "")
        monkeypatch.setattr(modulo_mapa, "_DIR_REPOSITORIO", _gravar(tmp_path / "repo", _arquivos()))
        assert modulo_mapa.resolver_diretorio() == tmp_path / "repo"

    def test_ordem_repositorio_antes_do_container(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ZIL_DATA_DIR", raising=False)
        repo = _gravar(tmp_path / "repo", _arquivos())
        container = _gravar(tmp_path / "container", _arquivos())
        monkeypatch.setattr(modulo_mapa, "_DIR_REPOSITORIO", repo)
        monkeypatch.setattr(modulo_mapa, "_DIR_CONTAINER", container)
        assert modulo_mapa.resolver_diretorio() == repo

    def test_sem_repositorio_usa_o_container(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ZIL_DATA_DIR", raising=False)
        container = _gravar(tmp_path / "container", _arquivos())
        monkeypatch.setattr(modulo_mapa, "_DIR_REPOSITORIO", tmp_path / "nao_existe")
        monkeypatch.setattr(modulo_mapa, "_DIR_CONTAINER", container)
        assert modulo_mapa.resolver_diretorio() == container

    def test_nenhum_diretorio_levanta_em_vez_de_mapa_vazio(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ZIL_DATA_DIR", raising=False)
        monkeypatch.setattr(modulo_mapa, "_DIR_REPOSITORIO", tmp_path / "a")
        monkeypatch.setattr(modulo_mapa, "_DIR_CONTAINER", tmp_path / "b")
        with pytest.raises(MapaIndisponivel):
            carregar_mapa()

    @pytest.mark.parametrize("nome", ["fases.yml", "marcos.yml", "ritos.yml", "glossario.yml", "nao_mapeados.yml"])
    def test_arquivo_de_conteudo_ausente_nao_vira_mapa_vazio(self, tmp_path, nome):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / nome).unlink()
        with pytest.raises(MapaIndisponivel) as erro:
            carregar_mapa(diretorio)
        assert nome in str(erro.value)

    def test_revisao_ausente_e_versao_zero_sem_entradas(self, tmp_path):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "revisao.yml").unlink()
        mapa = carregar_mapa(diretorio)
        assert mapa.versao_publicada == 0
        assert mapa.publicada_em is None
        assert mapa.publicaveis == frozenset()

    def test_producao_guarda_em_cache_por_processo(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ZIL_DATA_DIR", str(tmp_path))
        _gravar(tmp_path / "tramitacao", _arquivos())
        carregar_mapa_producao.cache_clear()
        try:
            assert carregar_mapa_producao() is carregar_mapa_producao()
        finally:
            carregar_mapa_producao.cache_clear()


class TestContainer:
    """CLAUDE.md, "Dados editoriais nos containers": loader novo tem de funcionar no container."""

    def test_layout_da_imagem_resolve_para_data_na_raiz(self, tmp_path):
        # Remonta o que os COPY de apps/api/Dockerfile produzem. /app/data existe na imagem por causa
        # das migrations de apps/api: é /app/data/tramitacao que não pode existir, senão o loader
        # pararia ali.
        app = tmp_path / "app"
        (app / "data" / "migrations").mkdir(parents=True)
        shutil.copytree(
            REPO / "packages" / "tramitacao",
            app / "packages" / "tramitacao",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        dados = tmp_path / "data" / "tramitacao"
        dados.mkdir(parents=True)
        for arquivo in DADOS_REPO.glob("*.yml"):
            shutil.copy(arquivo, dados)

        programa = (
            "import sys\n"
            "from pathlib import Path\n"
            "from packages.tramitacao import mapa\n"
            "assert Path(mapa.__file__).resolve().parents[2] == Path.cwd().resolve(), mapa.__file__\n"
            "mapa._DIR_CONTAINER = Path(sys.argv[1])\n"
            "print(mapa.resolver_diretorio())\n"
            "print(mapa.carregar_mapa().versao_publicada)\n"
        )
        saida = subprocess.run(
            [sys.executable, "-c", programa, str(dados)],
            cwd=app,
            env={"PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
        )
        assert saida.returncode == 0, saida.stderr
        assert saida.stdout.split() == [str(dados), "0"]

    def test_valor_dos_caminhos(self):
        # Todos os outros testes trocam estes valores antes de usar. Um erro aqui deixaria a CI verde
        # e a produção respondendo MapaIndisponivel.
        assert modulo_mapa._DIR_CONTAINER == Path("/data/tramitacao")
        assert modulo_mapa._DIR_REPOSITORIO == DADOS_REPO

    def test_imagem_copia_dados_e_pacote(self):
        dockerfile = (REPO / "apps" / "api" / "Dockerfile").read_text(encoding="utf-8")
        assert "COPY data/ /data/" in dockerfile
        assert "COPY packages/ /app/packages/" in dockerfile
        ignorados = (REPO / ".dockerignore").read_text(encoding="utf-8").split()
        assert not {"data", "data/", "data/tramitacao", "packages", "packages/"} & set(ignorados)

    @pytest.mark.parametrize("servico", ["api", "worker", "beat"])
    def test_compose_monta_dados_e_pacote(self, servico):
        # O mount ./apps/api:/app esconde o /app/packages da imagem: sem montar packages/ de novo, o
        # loader nem importa no container de desenvolvimento.
        compose = yaml.safe_load((REPO / "docker-compose.yml").read_text(encoding="utf-8"))
        volumes = compose["services"][servico]["volumes"]
        assert "./apps/api:/app" in volumes
        assert "./data:/data:ro" in volumes
        assert "./packages:/app/packages:ro" in volumes


class TestHash:
    def test_valor_fixo_calculado_fora_da_funcao(self):
        assert hash_entrada(ENTRADA_FIXA) == HASH_FIXO

    def test_estavel_a_ordem_das_chaves(self):
        invertida = dict(reversed(list(ENTRADA_FIXA.items())))
        assert list(invertida) != list(ENTRADA_FIXA)
        assert hash_entrada(invertida) == HASH_FIXO

    def test_muda_com_o_conteudo(self):
        assert hash_entrada({**ENTRADA_FIXA, "ordem": 3}) != HASH_FIXO

    def test_campo_de_data_falha_por_desenho(self):
        # §2.1-4: conteúdo não tem campo de data; se tiver, json.dumps falha.
        with pytest.raises(TypeError):
            hash_entrada({"data": date(2026, 11, 5)})


class TestPublicacao:
    def test_devolve_so_aprovada_com_hash_igual(self):
        conteudo = {
            "fases/aprovada_igual": ENTRADA_FIXA,
            "fases/aprovada_alterada": {**ENTRADA_FIXA, "rotulo": "Outro rótulo"},
            "fases/revisada": ENTRADA_FIXA,
        }
        revisao = ArquivoRevisao(
            versao_publicada=1,
            entradas={
                "fases/aprovada_igual": _estado("aprovado"),
                "fases/aprovada_alterada": _estado("aprovado"),
                "fases/revisada": _estado("revisado_agentes"),
            },
        )
        assert entradas_publicaveis(conteudo, revisao) == frozenset({"fases/aprovada_igual"})

    def test_rascunho_e_ausente_nao_publicam(self):
        conteudo = {"fases/rascunho": ENTRADA_FIXA, "fases/sem_registro": ENTRADA_FIXA}
        revisao = ArquivoRevisao(versao_publicada=1, entradas={"fases/rascunho": _estado("rascunho")})
        assert entradas_publicaveis(conteudo, revisao) == frozenset()

    def test_aprovada_sem_conteudo_nao_publica(self):
        revisao = ArquivoRevisao(versao_publicada=1, entradas={"fases/sumiu": _estado("aprovado")})
        assert entradas_publicaveis({}, revisao) == frozenset()

    def test_publicaveis_saem_da_carga(self, tmp_path):
        arquivos = _arquivos()
        entrada = arquivos["fases.yml"]["fases"][0]
        arquivos["revisao.yml"] = {
            "versao_publicada": 4,
            "publicada_em": date(2026, 11, 12),
            "entradas": {
                "fases/fase_comissoes": {
                    "estado": "aprovado",
                    "hash": hash_entrada(entrada),
                    "registros": ["L1"],
                    "aprovado_em": date(2026, 11, 6),
                    "revisado_por": ["agente:juridico@1a2b3c4d", "maintainer:Fulana"],
                },
                "fases/desfecho_arquivada": {
                    "estado": "revisado_agentes",
                    "hash": hash_entrada(arquivos["fases.yml"]["desfechos"][0]),
                },
            },
        }
        mapa = carregar_mapa(_gravar(tmp_path, arquivos))
        assert mapa.versao_publicada == 4
        assert mapa.publicada_em == date(2026, 11, 12)
        assert mapa.publicaveis == frozenset({"fases/fase_comissoes"})
        assert mapa.publicavel("fases/fase_comissoes")
        assert not mapa.publicavel("fases/desfecho_arquivada")
        assert not mapa.publicavel("fases/nao_existe")

    def test_editar_o_conteudo_despublica_na_carga_sem_tocar_na_revisao(self, tmp_path):
        arquivos = _arquivos()
        arquivos["revisao.yml"] = {
            "versao_publicada": 1,
            "entradas": {
                "fases/fase_comissoes": {
                    "estado": "aprovado",
                    "hash": hash_entrada(arquivos["fases.yml"]["fases"][0]),
                }
            },
        }
        diretorio = _gravar(tmp_path, arquivos)
        assert carregar_mapa(diretorio).publicavel("fases/fase_comissoes")

        arquivos["fases.yml"]["fases"][0]["rotulo"] = "Outro rótulo"
        _gravar(diretorio, {"fases.yml": arquivos["fases.yml"]})
        assert not carregar_mapa(diretorio).publicavel("fases/fase_comissoes")

    def test_comentario_e_ordem_no_yaml_nao_mudam_o_hash(self, tmp_path):
        # O hash é do mapeamento que o yaml.safe_load devolve, não do texto do arquivo.
        arquivos = _arquivos()
        arquivos["revisao.yml"] = {
            "versao_publicada": 1,
            "entradas": {
                "fases/fase_comissoes": {
                    "estado": "aprovado",
                    "hash": hash_entrada(arquivos["fases.yml"]["fases"][0]),
                }
            },
        }
        diretorio = _gravar(tmp_path, arquivos)
        texto = yaml.safe_dump(arquivos["fases.yml"], allow_unicode=True, sort_keys=False)
        (diretorio / "fases.yml").write_text(f"# comentário novo\n{texto}", encoding="utf-8")
        assert carregar_mapa(diretorio).publicavel("fases/fase_comissoes")

    def test_hash_e_do_bruto_antes_do_pydantic(self, tmp_path):
        # Pydantic normaliza a URL e apara o texto. O hash não pode ver isso: é o conteúdo revisado.
        arquivos = _arquivos()
        entrada = arquivos["fases.yml"]["fases"][0]
        entrada["pergunta"] = "  Quem analisa  "
        mapa = carregar_mapa(_gravar(tmp_path, arquivos))
        assert mapa.conteudo_bruto["fases/fase_comissoes"] == entrada
        assert mapa.fases["comissoes"].pergunta == "Quem analisa"

    def test_com_tudo_publicavel_nao_altera_o_original(self, tmp_path):
        mapa = carregar_mapa(_gravar(tmp_path, _arquivos()))
        tudo = mapa.com_tudo_publicavel()
        assert tudo.publicaveis == frozenset(mapa.conteudo_bruto)
        assert tudo.publicavel("marcos/320")
        assert mapa.publicaveis == frozenset()

    def test_mapa_e_imutavel(self, tmp_path):
        mapa = carregar_mapa(_gravar(tmp_path, _arquivos()))
        with pytest.raises(AttributeError):
            mapa.publicaveis = frozenset({"fases/fase_comissoes"})
        with pytest.raises(TypeError):
            mapa.fases["norma"] = mapa.fases["comissoes"]
        with pytest.raises(TypeError):
            mapa.conteudo_bruto["fases/inventada"] = {}
        with pytest.raises(ValidationError):
            mapa.fases["comissoes"].rotulo = "Outro rótulo"


class TestIds:
    def test_formato_arquivo_chave(self):
        a = _arquivos()
        a["ritos.yml"]["ritos"].append({**a["ritos.yml"]["ritos"][0], "especie": "MPV", "casa_iniciadora": "congresso"})
        a["ritos.yml"]["ritos"].append({**a["ritos.yml"]["ritos"][0], "casa_iniciadora": "senado"})
        a["marcos.yml"]["marcos"].append({**a["marcos.yml"]["marcos"][0], "cod": "TNJR", "casa": "senado"})
        ids = ids_de_conteudo(a["fases.yml"], a["marcos.yml"], a["ritos.yml"], a["glossario.yml"])
        assert set(ids) == {
            "fases/fase_comissoes",
            "fases/desfecho_arquivada",
            "fases/apensada",
            "fases/regra_R3",
            "marcos/320",
            "marcos/sf_tnjr",
            "ritos/PL_CD",
            "ritos/PL_SF",
            "ritos/MPV_CN",
            "ritos/pos_lei",
            "glossario/aguardando_parecer",
        }

    def test_devolve_o_mapeamento_bruto(self):
        a = _arquivos()
        ids = ids_de_conteudo(a["fases.yml"], a["marcos.yml"], a["ritos.yml"], a["glossario.yml"])
        assert ids["fases/regra_R3"] is a["fases.yml"]["regras"][0]

    def test_arquivos_sem_conteudo_nao_tem_entradas(self):
        fases = {"versao_esquema": 1, "normas_base": {}, "fases": [], "desfechos": [], "apensada": None, "regras": []}
        marcos = {"versao_esquema": 1, "marcos": [], "ignorados": []}
        ritos = {"versao_esquema": 1, "especies": [], "ritos": [], "pos_lei": None}
        glossario = {"versao_esquema": 1, "aviso": "x", "entradas": []}
        assert ids_de_conteudo(fases, marcos, ritos, glossario) == {}

    def test_conteudo_bruto_da_carga_usa_os_mesmos_ids(self, tmp_path):
        a = _arquivos()
        mapa = carregar_mapa(_gravar(tmp_path, a))
        assert set(mapa.conteudo_bruto) == set(
            ids_de_conteudo(a["fases.yml"], a["marcos.yml"], a["ritos.yml"], a["glossario.yml"])
        )


class TestRegistrosDeLote:
    def test_consolidado_tolera_campos_extras(self):
        consolidado = Consolidado.model_validate(
            {
                "lote": "L1",
                "rodada": 2,
                "consolidado_em": date(2026, 11, 5),
                "campo_futuro": "ignorado",
                "entradas": {
                    "fases/fase_comissoes": {
                        "hash": HASH_FIXO,
                        "estado_resultante": "revisado_agentes",
                        "bloqueia_abertos": [],
                        "divergencia": False,
                        "vereditos": {"juridico": "ok"},
                    }
                },
            }
        )
        assert consolidado.entradas["fases/fase_comissoes"].estado_resultante == "revisado_agentes"
        escrito = consolidado.model_dump()
        assert escrito["campo_futuro"] == "ignorado"
        assert escrito["entradas"]["fases/fase_comissoes"]["vereditos"] == {"juridico": "ok"}

    def test_consolidado_nunca_resulta_em_aprovado(self):
        # §6.6: a consolidação dá rascunho ou revisado_agentes; aprovar é só da maintainer.
        with pytest.raises(ValidationError):
            Consolidado.model_validate(
                {
                    "lote": "L1",
                    "rodada": 1,
                    "consolidado_em": date(2026, 11, 5),
                    "entradas": {
                        "fases/x": {
                            "hash": HASH_FIXO,
                            "estado_resultante": "aprovado",
                            "bloqueia_abertos": [],
                            "divergencia": False,
                        }
                    },
                }
            )

    def test_decisao_tolera_campos_extras(self):
        decisao = Decisao.model_validate(
            {
                "lote": "L1",
                "aprovado_em": date(2026, 11, 6),
                "aprovado_por": "Fulana",
                "minutos": 40,
                "aprovadas": ["fases/fase_comissoes"],
                "excluidas": {"fases/x": "texto ainda não conferido"},
                "sobreposicoes": {},
                "campo_futuro": 1,
            }
        )
        assert decisao.aprovadas == ["fases/fase_comissoes"]
        assert decisao.model_dump()["campo_futuro"] == 1


class TestModulos:
    def test_workers_so_reexporta_a_implementacao_unica(self):
        from apps.workers.tramitacao import revisao as reexportado
        from packages.tramitacao import revisao as implementacao

        for nome in implementacao.__all__:
            assert getattr(reexportado, nome) is getattr(implementacao, nome), nome
        assert set(reexportado.__all__) == set(implementacao.__all__)

        arvore = ast.parse((REPO / "apps" / "workers" / "tramitacao" / "revisao.py").read_text(encoding="utf-8"))
        definicoes = [n for n in arvore.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        assert definicoes == []

    @pytest.mark.parametrize("modulo", ["tipos", "mapa", "revisao"])
    def test_dominio_puro_sem_banco_nem_rede(self, modulo):
        arvore = ast.parse((REPO / "packages" / "tramitacao" / f"{modulo}.py").read_text(encoding="utf-8"))
        importados = set()
        for no in ast.walk(arvore):
            if isinstance(no, ast.Import):
                importados |= {a.name.split(".")[0] for a in no.names}
            elif isinstance(no, ast.ImportFrom) and no.module:
                importados.add(no.module.split(".")[0])
        assert not importados & {"sqlalchemy", "httpx", "requests", "urllib", "socket", "apps", "workers", "models"}

    def test_init_do_pacote_fica_vazio(self):
        # TRM-020 também cria este arquivo: vazio dos dois lados, o merge não conflita.
        assert (REPO / "packages" / "tramitacao" / "__init__.py").read_text(encoding="utf-8") == ""


AUSENTE = object()


def _navegar(dados, caminho: tuple):
    for parte in caminho:
        dados = dados[parte]
    return dados


def _aplicar(arquivos: dict, arquivo: str, caminho: tuple, campo: str, valor) -> None:
    alvo = _navegar(arquivos[arquivo], caminho)
    if valor is AUSENTE:
        del alvo[campo]
    else:
        alvo[campo] = valor


def _com_estado(arquivos: dict) -> dict:
    arquivos["revisao.yml"]["entradas"]["fases/fase_comissoes"] = {"estado": "rascunho", "hash": HASH_FIXO}
    return arquivos


FASE = ("fases", 0)
FRASE = ("fases", 0, "frases", 0)
BASE = ("fases", 0, "base_legal", 0)
DESFECHO = ("desfechos", 0)
REGRA = ("regras", 0)
CASO = ("regras", 0, "casos", 0)
SITUACAO = ("regras", 0, "situacoes_camara", 0)
MARCO = ("marcos", 0)
VARIANTE = ("marcos", 0, "variantes", 0)
IGNORADO = ("ignorados", 0)
RITO = ("ritos", 0)
ETAPA = ("ritos", 0, "etapas", 0)
DESFECHO_RITO = ("ritos", 0, "desfechos", 0)
ESPECIE = ("especies", 0)
ITEM = ("pos_lei", "itens", 0)
TERMO = ("entradas", 0)
CODIGO = ("entradas", 0, "codigos", 0)
EXEMPLO = ("entradas", 0, "exemplos", 0)
NAO_MAPEADO = ("situacoes_camara", 0)
ESTADO = ("entradas", "fases/fase_comissoes")


class TestLimites:
    """Cada restrição do esquema, nos dois lados do limite: o recusado sozinho passaria com um limite mais frouxo."""

    @pytest.mark.parametrize(
        ("arquivo", "caminho", "campo", "valor"),
        [
            ("fases.yml", (), "versao_esquema", 2),
            ("marcos.yml", (), "versao_esquema", 2),
            ("ritos.yml", (), "versao_esquema", 2),
            ("glossario.yml", (), "versao_esquema", 2),
            ("nao_mapeados.yml", (), "versao_esquema", 2),
            ("fases.yml", BASE, "norma", "cf"),
            ("fases.yml", BASE, "norma", "C"),
            ("fases.yml", BASE, "norma", "C" * 32),
            ("fases.yml", BASE, "dispositivo", "art"),
            ("fases.yml", BASE, "dispositivo", "x" * 81),
            ("fases.yml", BASE, "url", "nao e url"),
            ("fases.yml", CASO, "fonte_id", "abc"),
            ("fases.yml", CASO, "fonte_id", "12a"),
            ("fases.yml", CASO, "casa", "congresso"),
            ("fases.yml", FASE, "fontes", []),
            ("fases.yml", FASE, "fontes", ["nao e url"]),
            ("fases.yml", FRASE, "modelo", "abcd"),
            ("fases.yml", FRASE, "modelo", "x" * 281),
            ("fases.yml", FRASE, "quando", ["inventado"]),
            ("fases.yml", FRASE, "casa", "congresso"),
            ("fases.yml", FRASE, "especie", "XYZ"),
            ("fases.yml", FASE, "ordem", 0),
            ("fases.yml", FASE, "ordem", 10),
            ("fases.yml", FASE, "rotulo", "x" * 33),
            ("fases.yml", FASE, "rotulo_por_casa", {"camara": "x" * 33}),
            ("fases.yml", FASE, "rotulo_por_motivo", {"recem_apresentada": "x" * 33}),
            ("fases.yml", FASE, "rotulo_por_motivo", {"outro": "Rótulo"}),
            ("fases.yml", FASE, "frases", []),
            ("fases.yml", DESFECHO, "chave", "inventado"),
            ("fases.yml", DESFECHO, "rotulo", "x" * 33),
            ("fases.yml", DESFECHO, "frases", []),
            ("fases.yml", ("apensada",), "frases", []),
            ("fases.yml", ("apensada",), "fontes", []),
            ("fases.yml", REGRA, "tipo", "inventado"),
            ("fases.yml", REGRA, "parametros", {"x": 1.5}),
            ("fases.yml", SITUACAO, "fase", "inventada"),
            ("fases.yml", SITUACAO, "desfecho", "inventado"),
            ("fases.yml", SITUACAO, "motivo", "inventado"),
            ("marcos.yml", MARCO, "cod", "abc"),
            ("marcos.yml", MARCO, "cod", "32a"),
            ("marcos.yml", MARCO, "casa", "congresso"),
            ("marcos.yml", MARCO, "marco", "inventado"),
            ("marcos.yml", MARCO, "titulo", "x" * 61),
            ("marcos.yml", MARCO, "fase_resultante", "inventada"),
            ("marcos.yml", MARCO, "terminal", "inventado"),
            ("marcos.yml", MARCO, "reabre", ["inventado"]),
            ("marcos.yml", VARIANTE, "marco", "inventado"),
            ("marcos.yml", VARIANTE, "titulo", "x" * 61),
            ("marcos.yml", VARIANTE, "fase_resultante", "inventada"),
            ("marcos.yml", VARIANTE, "terminal", "inventado"),
            ("ritos.yml", RITO, "especie", "XYZ"),
            ("ritos.yml", RITO, "etapas", []),
            ("ritos.yml", ETAPA, "id", "AB_C"),
            ("ritos.yml", ETAPA, "id", "ab"),
            ("ritos.yml", ETAPA, "id", "a" * 42),
            ("ritos.yml", ETAPA, "fase", "inventada"),
            ("ritos.yml", ETAPA, "casa", "inventada"),
            ("ritos.yml", ETAPA, "nome", "x" * 61),
            ("ritos.yml", ETAPA, "o_que_acontece", "x" * 401),
            ("ritos.yml", ETAPA, "quem_decide", "x" * 161),
            ("ritos.yml", ETAPA, "classe_prazo", "Z"),
            ("ritos.yml", ETAPA, "pulada_quando", "inventada"),
            ("ritos.yml", ETAPA, "condicao", "x" * 121),
            ("ritos.yml", ETAPA, "nota_pulada", "x" * 81),
            ("ritos.yml", DESFECHO_RITO, "desfecho", "inventado"),
            ("ritos.yml", DESFECHO_RITO, "a_partir_de", "outro"),
            ("ritos.yml", DESFECHO_RITO, "texto", "x" * 301),
            ("ritos.yml", ESPECIE, "sigla", "XYZ"),
            ("ritos.yml", ITEM, "id", "inventado"),
            ("ritos.yml", ITEM, "texto", "x" * 401),
            ("ritos.yml", ITEM, "classe_prazo", "Z"),
            ("glossario.yml", TERMO, "chave", "ab"),
            ("glossario.yml", TERMO, "chave", "a" * 61),
            ("glossario.yml", TERMO, "chave", "1abc"),
            ("glossario.yml", TERMO, "tipo", "inventado"),
            ("glossario.yml", TERMO, "termo", "x" * 121),
            ("glossario.yml", TERMO, "texto_curto", "x" * 19),
            ("glossario.yml", TERMO, "texto_curto", "x" * 161),
            ("glossario.yml", TERMO, "texto", "x" * 39),
            ("glossario.yml", TERMO, "texto", "x" * 901),
            ("glossario.yml", TERMO, "fase", "inventada"),
            ("glossario.yml", CODIGO, "casa", "congresso"),
            ("glossario.yml", EXEMPLO, "casa", "congresso"),
            ("glossario.yml", EXEMPLO, "fonte_id", "abc"),
            ("glossario.yml", EXEMPLO, "nota", "x" * 201),
            ("nao_mapeados.yml", NAO_MAPEADO, "motivo", "codigo_novo_2026-1-1"),
            ("nao_mapeados.yml", NAO_MAPEADO, "motivo", "codigo_novo_"),
        ],
    )
    def test_recusa(self, tmp_path, arquivo, caminho, campo, valor):
        arquivos = _arquivos()
        _aplicar(arquivos, arquivo, caminho, campo, valor)
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        esperado = f"{arquivo}: {modulo_mapa._caminho((*caminho, campo))}"
        assert any(p.startswith(esperado) for p in erro.value.problemas), erro.value.problemas

    @pytest.mark.parametrize(
        ("arquivo", "caminho", "campo", "valor"),
        [
            ("fases.yml", BASE, "norma", "CF"),
            ("fases.yml", BASE, "norma", "C" * 31),
            ("fases.yml", BASE, "dispositivo", "art."),
            ("fases.yml", BASE, "dispositivo", "x" * 80),
            ("fases.yml", FRASE, "modelo", "abcde"),
            ("fases.yml", FRASE, "modelo", "x" * 280),
            ("fases.yml", FASE, "ordem", 1),
            ("fases.yml", FASE, "ordem", 9),
            ("fases.yml", FASE, "rotulo", "x" * 32),
            ("fases.yml", FASE, "rotulo_por_casa", {"camara": "x" * 32}),
            ("fases.yml", FASE, "rotulo_por_motivo", {"recem_apresentada": "x" * 32}),
            ("fases.yml", REGRA, "parametros", {"max_niveis": 10, "sigla": "PLEN", "tipos": ["2", "3"]}),
            ("marcos.yml", MARCO, "titulo", "x" * 60),
            ("marcos.yml", VARIANTE, "titulo", "x" * 60),
            ("ritos.yml", ETAPA, "id", "abc"),
            ("ritos.yml", ETAPA, "id", "a" * 41),
            ("ritos.yml", ETAPA, "nome", "x" * 60),
            ("ritos.yml", ETAPA, "o_que_acontece", "x" * 400),
            ("ritos.yml", ETAPA, "quem_decide", "x" * 160),
            ("ritos.yml", ETAPA, "condicao", "x" * 120),
            ("ritos.yml", ETAPA, "nota_pulada", "x" * 80),
            ("ritos.yml", DESFECHO_RITO, "texto", "x" * 300),
            ("ritos.yml", ITEM, "texto", "x" * 400),
            ("glossario.yml", TERMO, "chave", "abc"),
            ("glossario.yml", TERMO, "chave", "a" * 60),
            ("glossario.yml", TERMO, "termo", "x" * 120),
            ("glossario.yml", TERMO, "texto_curto", "x" * 20),
            ("glossario.yml", TERMO, "texto_curto", "x" * 160),
            ("glossario.yml", TERMO, "texto", "x" * 40),
            ("glossario.yml", TERMO, "texto", "x" * 900),
            ("glossario.yml", EXEMPLO, "nota", "x" * 200),
            ("nao_mapeados.yml", NAO_MAPEADO, "motivo", "sem_evidencia"),
            ("nao_mapeados.yml", NAO_MAPEADO, "motivo", "codigo_novo_2026-11-05"),
        ],
    )
    def test_aceita_no_limite(self, tmp_path, arquivo, caminho, campo, valor):
        arquivos = _arquivos()
        _aplicar(arquivos, arquivo, caminho, campo, valor)
        carregar_mapa(_gravar(tmp_path, arquivos))

    @pytest.mark.parametrize("caminho", [FASE, DESFECHO, ("apensada",)], ids=["fase", "desfecho", "apensada"])
    def test_uma_frase_basta(self, tmp_path, caminho):
        arquivos = _arquivos()
        _aplicar(arquivos, "fases.yml", caminho, "frases", [{"modelo": "Nas comissões."}])
        carregar_mapa(_gravar(tmp_path, arquivos))

    def test_etapas_precisam_de_tres(self, tmp_path):
        arquivos = _arquivos()
        arquivos["ritos.yml"]["ritos"][0]["etapas"].pop()
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert "ritos.yml: ritos[0].etapas" in str(erro.value)

    def test_pos_lei_nao_aceita_quatro_itens(self, tmp_path):
        arquivos = _arquivos()
        itens = arquivos["ritos.yml"]["pos_lei"]["itens"]
        itens.append(copy.deepcopy(itens[0]))
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert "ritos.yml: pos_lei.itens" in str(erro.value)

    @pytest.mark.parametrize(("tamanho", "aceita"), [(19, False), (20, True)])
    def test_base_legal_motivo_tem_minimo(self, tmp_path, tamanho, aceita):
        arquivos = _arquivos()
        fase = arquivos["fases.yml"]["fases"][0]
        del fase["base_legal"]
        fase["base_legal_motivo"] = "x" * tamanho
        diretorio = _gravar(tmp_path, arquivos)
        if aceita:
            carregar_mapa(diretorio)
        else:
            with pytest.raises(MapaInvalido, match=r"fases\.yml: fases\[0\]\.base_legal_motivo"):
                carregar_mapa(diretorio)

    @pytest.mark.parametrize(
        "valor", ["abc", "ABCDEF012345", "d21ab6d1d08", "d21ab6d1d0822", "g21ab6d1d082"]
    )
    def test_hash_do_estado_tem_formato(self, tmp_path, valor):
        arquivos = _com_estado(_arquivos())
        _aplicar(arquivos, "revisao.yml", ESTADO, "hash", valor)
        with pytest.raises(MapaInvalido, match="entradas.fases/fase_comissoes.hash"):
            carregar_mapa(_gravar(tmp_path, arquivos))

    @pytest.mark.parametrize(
        ("arquivo", "caminho", "campo"),
        [
            *[("fases.yml", (), c) for c in ("versao_esquema", "normas_base", "fases", "desfechos", "regras")],
            *[("fases.yml", ("normas_base", "CF"), c) for c in ("nome", "url")],
            *[("fases.yml", FASE, c) for c in ("chave", "ordem", "rotulo", "pergunta", "frases", "fontes")],
            ("fases.yml", FRASE, "modelo"),
            *[("fases.yml", BASE, c) for c in ("norma", "dispositivo", "url")],
            *[("fases.yml", DESFECHO, c) for c in ("chave", "rotulo", "frases", "fontes")],
            *[("fases.yml", ("apensada",), c) for c in ("rotulo", "frases", "fontes")],
            *[("fases.yml", REGRA, c) for c in ("id", "tipo", "descricao", "casos", "fontes")],
            *[("fases.yml", CASO, c) for c in ("casa", "fonte_id", "rotulo")],
            *[("fases.yml", SITUACAO, c) for c in ("cod", "descricao_oficial")],
            *[("marcos.yml", (), c) for c in ("versao_esquema", "marcos", "ignorados")],
            *[("marcos.yml", MARCO, c) for c in ("cod", "casa", "descricao_oficial", "marco", "titulo", "casos", "fontes")],
            ("marcos.yml", VARIANTE, "padrao_despacho"),
            *[("marcos.yml", IGNORADO, c) for c in ("cod", "descricao_oficial", "nota")],
            *[("ritos.yml", (), c) for c in ("versao_esquema", "especies", "ritos")],
            *[("ritos.yml", RITO, c) for c in ("especie", "casa_iniciadora", "nome", "etapas", "desfechos", "fontes")],
            *[("ritos.yml", ETAPA, c) for c in ("id", "fase", "nome", "o_que_acontece", "fontes")],
            *[("ritos.yml", DESFECHO_RITO, c) for c in ("desfecho", "a_partir_de", "texto", "fontes")],
            *[("ritos.yml", ESPECIE, c) for c in ("sigla", "nome")],
            *[("ritos.yml", ("pos_lei",), c) for c in ("itens", "fontes")],
            *[("ritos.yml", ITEM, c) for c in ("id", "nome", "texto", "fontes")],
            *[("glossario.yml", (), c) for c in ("versao_esquema", "aviso", "entradas")],
            *[("glossario.yml", TERMO, c) for c in ("chave", "tipo", "termo", "texto_curto", "texto", "fontes")],
            *[("glossario.yml", CODIGO, c) for c in ("casa", "cod")],
            *[("glossario.yml", EXEMPLO, c) for c in ("proposicao", "casa", "fonte_id")],
            *[("nao_mapeados.yml", (), c) for c in ("versao_esquema", "situacoes_camara", "situacoes_senado", "tramitacao_camara")],
            *[("nao_mapeados.yml", NAO_MAPEADO, c) for c in ("cod", "descricao_oficial", "motivo")],
            *[("revisao.yml", (), c) for c in ("versao_publicada", "entradas")],
        ],
    )
    def test_campo_obrigatorio(self, tmp_path, arquivo, caminho, campo):
        arquivos = _arquivos()
        _aplicar(arquivos, arquivo, caminho, campo, AUSENTE)
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        esperado = f"{arquivo}: {modulo_mapa._caminho((*caminho, campo))}"
        assert any(p.startswith(esperado) for p in erro.value.problemas), erro.value.problemas

    @pytest.mark.parametrize("campo", ["estado", "hash"])
    def test_campo_obrigatorio_do_estado(self, tmp_path, campo):
        arquivos = _com_estado(_arquivos())
        _aplicar(arquivos, "revisao.yml", ESTADO, campo, AUSENTE)
        with pytest.raises(MapaInvalido, match=f"entradas.fases/fase_comissoes.{campo}"):
            carregar_mapa(_gravar(tmp_path, arquivos))

    @pytest.mark.parametrize(
        ("arquivo", "caminho", "campo"),
        [
            ("fases.yml", FASE, "base_legal"),
            ("fases.yml", FASE, "fontes"),
            ("fases.yml", FRASE, "quando"),
            ("fases.yml", REGRA, "casos"),
            ("marcos.yml", MARCO, "casos"),
            ("marcos.yml", MARCO, "reabre"),
            ("ritos.yml", DESFECHO_RITO, "a_partir_de"),
            ("glossario.yml", TERMO, "codigos"),
            ("glossario.yml", TERMO, "exemplos"),
            ("glossario.yml", TERMO, "relacionados"),
        ],
    )
    def test_lista_que_e_conjunto(self, tmp_path, arquivo, caminho, campo):
        arquivos = _arquivos()
        alvo = _navegar(arquivos[arquivo], caminho)
        item = {
            "quando": "da_casa",
            "reabre": "arquivada",
            "a_partir_de": "etapa_um",
            "relacionados": "outro_termo",
        }.get(campo)
        alvo[campo] = [item, item] if item else [alvo[campo][0], copy.deepcopy(alvo[campo][0])]
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        assert f"{arquivo}: {modulo_mapa._caminho((*caminho, campo))}" in str(erro.value)

    @pytest.mark.parametrize("campo", ["registros", "revisado_por"])
    def test_lista_do_estado_que_e_conjunto(self, tmp_path, campo):
        arquivos = _com_estado(_arquivos())
        _aplicar(arquivos, "revisao.yml", ESTADO, campo, ["x", "x"])
        with pytest.raises(MapaInvalido, match=f"entradas.fases/fase_comissoes.{campo}"):
            carregar_mapa(_gravar(tmp_path, arquivos))

    def test_todo_modelo_de_conteudo_e_estrito_e_imutavel(self):
        modelos = [
            objeto
            for modulo in (modulo_mapa, modulo_revisao)
            for objeto in vars(modulo).values()
            if isinstance(objeto, type) and issubclass(objeto, BaseModel) and objeto.__module__ == modulo.__name__
        ]
        estritos = [m for m in modelos if not issubclass(m, modulo_revisao._RegistroDeLote)]
        assert len(estritos) >= 28
        for modelo in estritos:
            assert modelo.model_config.get("extra") == "forbid", modelo
            assert modelo.model_config.get("frozen") is True, modelo
            assert modelo.model_config.get("str_strip_whitespace") is True, modelo

    def test_estado_aceita_os_tres_valores_do_contrato(self):
        assert set(get_args(modulo_tipos.Revisao)) == {"rascunho", "revisado_agentes", "aprovado"}
        for estado in get_args(modulo_tipos.Revisao):
            assert EstadoEntrada(estado=estado, hash=HASH_FIXO).estado == estado


# Copiados de backlog-dados §1.5, §2.2 a §2.6: a fonte é a spec, não o módulo testado.
LITERAIS_DE_TIPOS = {
    "Fase": {"apresentada", "comissoes", "plenario", "outra_casa", "retorno", "sancao", "veto_congresso", "promulgacao", "norma"},
    "Desfecho": {"arquivada", "retirada", "prejudicada", "rejeitada", "perdeu_eficacia", "vetada", "devolvida"},
    "Motivo": {
        "situacao_sem_mapa", "sinais_conflitantes", "principal_nao_resolvida", "fonte_indisponivel",
        "especie_fora_do_escopo", "mapa_nao_aprovado", "recem_apresentada",
    },
    "EstadoEtapa": {"feita", "atual", "futura", "pulada", "interrompida"},
    "Revisao": {"rascunho", "revisado_agentes", "aprovado"},
    "Casa": {"camara", "senado"},
    "CasaRito": {"camara", "senado", "congresso", "presidencia"},
    "Especie": {"PL", "PLP", "PEC", "MPV", "PDL"},
    "ClassePrazo": {"D", "D*", "X"},
    "RegraId": {"R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"},
}
LITERAIS_DE_MAPA = {
    "Marcador": {
        "na_casa", "da_casa", "membros", "orgao", "desde", "orgao_desde", "data", "norma_com_artigo", "na_lei",
        "principal_com_artigo", "frase_principal",
    },
    "TipoMarco": {
        "apresentacao", "distribuicao", "apensacao", "designacao_relator", "parecer", "parecer_aprovado",
        "urgencia_aprovada", "votacao_plenario", "aprovacao_plenario", "remessa_outra_casa",
        "recebimento_outra_casa", "aprovacao_outra_casa", "retorno_emendas", "remessa_sancao", "norma",
        "norma_veto_parcial", "veto_total", "remessa_promulgacao", "arquivamento", "desarquivamento", "retirada",
        "prejudicialidade", "perda_eficacia", "devolucao",
    },
}
LITERAIS_DE_CAMPO = [
    (modulo_mapa.RegraDef, "tipo", {
        "norma", "marco_terminal", "situacao_terminal", "apensacao", "outra_casa", "pos_congresso", "orgao",
        "pre_despacho", "recem_apresentada", "fallback",
    }),
    (modulo_mapa.EtapaRito, "pulada_quando", {
        "apreciacao_conclusiva", "sem_emendas_da_revisora", "sem_veto_total", "mpv_sem_alteracao", "mpv_alterada",
        "sancionada",
    }),
    (modulo_mapa.ItemPosLei, "id", {"publicacao", "vigencia", "regulamentacao"}),
    (modulo_mapa.EntradaGlossario, "tipo", {
        "situacao", "regime", "apreciacao", "fase", "desfecho", "apensada", "etapa", "especie", "conceito",
    }),
    (modulo_mapa.Rito, "casa_iniciadora", {"camara", "senado", "congresso"}),
    (modulo_revisao.EntradaConsolidada, "estado_resultante", {"rascunho", "revisado_agentes"}),
]


def _valores_literais(anotacao) -> set[str]:
    valores: set[str] = set()
    for argumento in get_args(anotacao):
        if isinstance(argumento, str):
            valores.add(argumento)
        elif argumento is not type(None):
            valores |= _valores_literais(argumento)
    return valores


class TestLiterais:
    @pytest.mark.parametrize(("nome", "esperado"), LITERAIS_DE_TIPOS.items())
    def test_literais_de_tipos(self, nome, esperado):
        assert set(get_args(getattr(modulo_tipos, nome))) == esperado

    @pytest.mark.parametrize(("nome", "esperado"), LITERAIS_DE_MAPA.items())
    def test_literais_de_mapa(self, nome, esperado):
        assert set(get_args(getattr(modulo_mapa, nome))) == esperado

    @pytest.mark.parametrize(("modelo", "campo", "esperado"), LITERAIS_DE_CAMPO)
    def test_literais_de_campo(self, modelo, campo, esperado):
        assert _valores_literais(modelo.model_fields[campo].annotation) == esperado

    def test_hosts_de_norma(self):
        assert modulo_mapa.HOSTS_NORMA == {
            "www.planalto.gov.br", "planalto.gov.br", "www2.camara.leg.br", "www.camara.leg.br",
            "legis.senado.leg.br", "www25.senado.leg.br", "www.congressonacional.leg.br", "normas.leg.br",
            "portal.stf.jus.br", "noticias.stf.jus.br",
        }

    def test_fase_ou_nao_sabemos(self):
        assert set(get_args(modulo_tipos.FaseOuNaoSabemos)) == {
            "apresentada", "comissoes", "plenario", "outra_casa", "retorno",
            "sancao", "veto_congresso", "promulgacao", "norma", "nao_sabemos",
        }
        assert set(get_args(modulo_tipos.FaseOuNaoSabemos)) == set(get_args(modulo_tipos.Fase)) | {"nao_sabemos"}

    def test_situacao_estado(self):
        assert set(get_args(modulo_tipos.SituacaoEstado)) == {
            "informada", "recem_apresentada", "sem_situacao", "nao_sincronizada",
        }


class TestFalhaFechada:
    """§1.5 só captura MapaIndisponivel e MapaInvalido: qualquer outra exceção da carga vira 500 na API."""

    def _diretorio_com_aprovada(self, tmp_path, rotulo_yaml: str) -> Path:
        arquivos = _arquivos()
        arquivos["revisao.yml"]["versao_publicada"] = 1
        arquivos["revisao.yml"]["entradas"]["fases/fase_comissoes"] = {"estado": "aprovado", "hash": HASH_FIXO}
        diretorio = _gravar(tmp_path, arquivos)
        fases = (diretorio / "fases.yml").read_text(encoding="utf-8")
        assert "rotulo: Nas comissões\n" in fases
        (diretorio / "fases.yml").write_text(
            fases.replace("rotulo: Nas comissões\n", f"rotulo: {rotulo_yaml}\n", 1), encoding="utf-8"
        )
        return diretorio

    @pytest.mark.parametrize(
        ("rotulo_yaml", "motivo"),
        [
            ("!!binary QUJD", "bytes"),
            ("!!set {a, b}", "set"),
            ("2026-11-05", "date"),
            ('"\\ud800"', "UTF-8"),
        ],
        ids=["binary", "set", "data", "surrogate"],
    )
    def test_valor_fora_do_json_em_entrada_aprovada(self, tmp_path, rotulo_yaml, motivo):
        # Um problema só, e pelo motivo certo: o arquivo não chega ao Pydantic, que em modo não estrito
        # aceitaria bytes como texto e set como lista.
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(self._diretorio_com_aprovada(tmp_path, rotulo_yaml))
        assert len(erro.value.problemas) == 1, erro.value.problemas
        assert erro.value.problemas[0].startswith("fases.yml: fases[0].rotulo")
        assert motivo in erro.value.problemas[0]

    @pytest.mark.parametrize("rotulo_yaml", ["!!binary QUJD", "!!set {a, b}"], ids=["binary", "set"])
    def test_valor_fora_do_json_em_rascunho_tambem_e_recusado(self, tmp_path, rotulo_yaml):
        # Em rascunho o hash nem é calculado: sem esta checagem, o valor passaria calado até a aprovação.
        diretorio = self._diretorio_com_aprovada(tmp_path, rotulo_yaml)
        arquivos_revisao = {"versao_publicada": 0, "entradas": {}}
        _gravar(diretorio, {"revisao.yml": arquivos_revisao})
        with pytest.raises(MapaInvalido, match=r"fases\.yml: fases\[0\]\.rotulo"):
            carregar_mapa(diretorio)

    def test_valor_fora_do_json_fora_das_entradas(self, tmp_path):
        diretorio = _gravar(tmp_path, _arquivos())
        texto = (diretorio / "glossario.yml").read_text(encoding="utf-8")
        (diretorio / "glossario.yml").write_text(
            texto.replace("aviso: Texto do ZIL, não oficial.", "aviso: !!binary QUJD"), encoding="utf-8"
        )
        with pytest.raises(MapaInvalido, match="glossario.yml: aviso"):
            carregar_mapa(diretorio)

    def test_chave_que_nao_e_utf8_nao_vai_crua_para_a_mensagem(self, tmp_path):
        # Mensagem com surrogate estouraria de novo na hora de escrever o log.
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "marcos.yml").write_text(
            'versao_esquema: 1\nmarcos: []\nignorados: []\n"\\ud800": x\n', encoding="utf-8"
        )
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(diretorio)
        assert len(erro.value.problemas) == 1, erro.value.problemas
        assert "UTF-8" in erro.value.problemas[0]
        erro.value.problemas[0].encode("utf-8")

    def test_chave_fora_do_json(self, tmp_path):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "marcos.yml").write_text(
            "versao_esquema: 1\nmarcos: []\nignorados: []\n2026-11-05: x\n", encoding="utf-8"
        )
        with pytest.raises(MapaInvalido, match="marcos.yml: 2026-11-05"):
            carregar_mapa(diretorio)

    @pytest.mark.parametrize(
        ("texto", "trecho"),
        [
            ("versao_esquema: 1\nmarcos: &x [*x]\nignorados: []\n", "marcos.yml: marcos[0]"),
            ("versao_esquema: 1\nmarcos: []\nignorados: []\nx: &x {k: *x}\n", "marcos.yml: x.k"),
        ],
        ids=["lista", "mapeamento"],
    )
    def test_referencia_circular(self, tmp_path, texto, trecho):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "marcos.yml").write_text(texto, encoding="utf-8")
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(diretorio)
        assert any(p.startswith(trecho) for p in erro.value.problemas), erro.value.problemas

    def test_alias_repetido_sem_ciclo_e_aceito(self, tmp_path):
        # O mesmo objeto em dois lugares não é ciclo, e safe_dump gera isso sozinho em entradas parecidas.
        diretorio = _gravar(tmp_path, _arquivos())
        texto = (diretorio / "fases.yml").read_text(encoding="utf-8")
        assert carregar_mapa(diretorio)
        (diretorio / "fases.yml").write_text(f"x_comum: &comum [{FONTE!r}]\n" + texto, encoding="utf-8")
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(diretorio)
        assert [p for p in erro.value.problemas if not p.startswith("fases.yml: x_comum")] == []

    @pytest.mark.parametrize("nome", ["fases.yml", "glossario.yml", "revisao.yml"])
    def test_arquivo_fora_de_utf8(self, tmp_path, nome):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / nome).write_bytes("versao_esquema: 1\naviso: não oficial\n".encode("latin-1"))
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(diretorio)
        assert any(p.startswith(f"{nome}: ") and "UTF-8" in p for p in erro.value.problemas), erro.value.problemas

    @pytest.mark.parametrize(
        "texto",
        ["a: 2026-13-45\n", "a: !!int x\n", "[" * 5000 + "]" * 5000],
        ids=["data_impossivel", "int_impossivel", "aninhamento"],
    )
    def test_yaml_que_o_parser_nao_constroi(self, tmp_path, texto):
        # ValueError e RecursionError não são yaml.YAMLError.
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "marcos.yml").write_text(texto, encoding="utf-8")
        with pytest.raises(MapaInvalido, match="marcos.yml"):
            carregar_mapa(diretorio)

    def test_data_em_conteudo_cita_o_tipo(self, tmp_path):
        # O Pydantic também recusaria, mas sem dizer que o problema é o valor não caber no hash.
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "marcos.yml").write_text(
            "versao_esquema: 1\nmarcos: []\nignorados: []\nx: 2026-11-05\n", encoding="utf-8"
        )
        with pytest.raises(MapaInvalido, match="marcos.yml: x: valor do tipo date"):
            carregar_mapa(diretorio)

    def test_arquivo_ilegivel_e_indisponivel(self, tmp_path, monkeypatch):
        diretorio = _gravar(tmp_path, _arquivos())
        ler = Path.read_text

        def negar(caminho, *args, **kwargs):
            if caminho.name == "marcos.yml":
                raise PermissionError("sem permissão")
            return ler(caminho, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", negar)
        with pytest.raises(MapaIndisponivel, match="marcos.yml"):
            carregar_mapa(diretorio)

    def test_data_em_revisao_continua_valendo(self, tmp_path):
        arquivos = _arquivos()
        arquivos["revisao.yml"]["publicada_em"] = date(2026, 11, 12)
        assert carregar_mapa(_gravar(tmp_path, arquivos)).publicada_em == date(2026, 11, 12)

    def test_binary_em_revisao_e_recusado(self, tmp_path):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "revisao.yml").write_text("versao_publicada: 0\nentradas: {}\nx: !!binary QUJD\n", encoding="utf-8")
        with pytest.raises(MapaInvalido, match="revisao.yml: x"):
            carregar_mapa(diretorio)


class TestIdDoBrutoIgualAoDoModelo:
    """O id sai do YAML bruto e o índice, do modelo aparado. Com espaço, a aprovação nunca publicaria."""

    @pytest.mark.parametrize(
        ("arquivo", "caminho", "campo", "valor"),
        [
            ("marcos.yml", MARCO, "cod", "320 "),
            ("marcos.yml", MARCO, "cod", " 320"),
            ("marcos.yml", MARCO, "casa", "camara "),
            ("marcos.yml", IGNORADO, "cod", "604 "),
            ("glossario.yml", TERMO, "chave", "aguardando_parecer "),
            ("glossario.yml", CODIGO, "cod", "915 "),
            ("fases.yml", FASE, "chave", "comissoes "),
            ("fases.yml", DESFECHO, "chave", "arquivada "),
            ("fases.yml", REGRA, "id", "R3 "),
            ("fases.yml", SITUACAO, "cod", "923 "),
            ("ritos.yml", RITO, "especie", "PL "),
            ("ritos.yml", RITO, "casa_iniciadora", "camara "),
            ("nao_mapeados.yml", NAO_MAPEADO, "cod", "1250 "),
        ],
    )
    def test_chave_com_espaco_nas_pontas(self, tmp_path, arquivo, caminho, campo, valor):
        arquivos = _arquivos()
        _aplicar(arquivos, arquivo, caminho, campo, valor)
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(_gravar(tmp_path, arquivos))
        esperado = f"{arquivo}: {modulo_mapa._caminho((*caminho, campo))}"
        assert any(p.startswith(esperado) for p in erro.value.problemas), erro.value.problemas

    def test_id_com_espaco_em_revisao(self, tmp_path):
        arquivos = _arquivos()
        arquivos["revisao.yml"]["entradas"]["marcos/320 "] = {"estado": "aprovado", "hash": HASH_FIXO}
        with pytest.raises(MapaInvalido, match="revisao.yml: entradas.marcos/320 "):
            carregar_mapa(_gravar(tmp_path, arquivos))

    def test_todo_id_tem_a_entrada_no_indice(self, tmp_path):
        mapa = carregar_mapa(_gravar(tmp_path, _arquivos()))
        assert "marcos/320" in mapa.conteudo_bruto and ("camara", "320") in mapa.marcos
        assert "glossario/aguardando_parecer" in mapa.conteudo_bruto and "aguardando_parecer" in mapa.glossario


class TestChaveRepetidaNoYaml:
    """PyYAML fica com o último valor sem avisar, e a revisão pode ter lido a linha errada no diff."""

    @pytest.mark.parametrize(
        ("nome", "texto", "linha"),
        [
            ("marcos.yml", "versao_esquema: 1\nmarcos: []\nmarcos: []\nignorados: []\n", 3),
            ("marcos.yml", "versao_esquema: 1\nmarcos: []\nignorados:\n  - {cod: '1', cod: '2', descricao_oficial: x, nota: y}\n", 4),
            ("revisao.yml", "versao_publicada: 0\nversao_publicada: 1\nentradas: {}\n", 2),
            (
                "revisao.yml",
                f"versao_publicada: 1\nentradas:\n  fases/x: {{estado: rascunho, hash: {HASH_FIXO}}}\n"
                f"  fases/x: {{estado: aprovado, hash: {HASH_FIXO}}}\n",
                4,
            ),
        ],
        ids=["raiz", "dentro_de_entrada", "versao", "estado_de_revisao"],
    )
    def test_recusa_citando_arquivo_e_linha(self, tmp_path, nome, texto, linha):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / nome).write_text(texto, encoding="utf-8")
        with pytest.raises(MapaInvalido) as erro:
            carregar_mapa(diretorio)
        problema = next(p for p in erro.value.problemas if p.startswith(f"{nome}: "))
        assert "repetida" in problema
        assert f"line {linha}" in problema

    def test_rotulo_duplicado_numa_entrada(self, tmp_path):
        diretorio = _gravar(tmp_path, _arquivos())
        texto = (diretorio / "fases.yml").read_text(encoding="utf-8")
        (diretorio / "fases.yml").write_text(
            texto.replace("rotulo: Nas comissões\n", "rotulo: Nas comissões\n  rotulo: Outro\n", 1), encoding="utf-8"
        )
        with pytest.raises(MapaInvalido, match="repetida"):
            carregar_mapa(diretorio)

    def test_mesma_chave_em_mapeamentos_diferentes_e_aceita(self, tmp_path):
        assert carregar_mapa(_gravar(tmp_path, _arquivos())).versao_publicada == 0

    def test_dois_merges_no_mesmo_mapeamento_sao_repetidos(self, tmp_path):
        diretorio = _gravar(tmp_path, _arquivos())
        (diretorio / "marcos.yml").write_text(
            "versao_esquema: 1\nmarcos: []\nignorados:\n"
            "  - &a {cod: '1', descricao_oficial: x, nota: y}\n"
            "  - &b {cod: '2', descricao_oficial: x, nota: y}\n"
            "  - {<<: *a, <<: *b, cod: '3'}\n",
            encoding="utf-8",
        )
        with pytest.raises(MapaInvalido, match="repetida"):
            carregar_mapa(diretorio)

    def test_merge_do_yaml_continua_valendo(self, tmp_path):
        # `<<` com sobrescrita é recurso do YAML, não repetição. O hash continua vendo o que o safe_load veria.
        diretorio = _gravar(tmp_path, _arquivos())
        texto = (
            "versao_esquema: 1\nmarcos: []\nignorados:\n"
            "  - &base {cod: '1', descricao_oficial: x, nota: y}\n"
            "  - {<<: *base, cod: '2'}\n"
        )
        (diretorio / "marcos.yml").write_text(texto, encoding="utf-8")
        assert set(carregar_mapa(diretorio).ignorados) == {("camara", "1"), ("camara", "2")}

    def test_o_bruto_e_igual_ao_do_safe_load(self, tmp_path):
        diretorio = _gravar(tmp_path, _arquivos())
        bruto = yaml.safe_load((diretorio / "fases.yml").read_text(encoding="utf-8"))
        assert carregar_mapa(diretorio).conteudo_bruto["fases/fase_comissoes"] == bruto["fases"][0]


class TestRegistrosDeLoteLimites:
    def _consolidado(self, **entrada) -> dict:
        base = {"hash": HASH_FIXO, "estado_resultante": "revisado_agentes", "bloqueia_abertos": [], "divergencia": False}
        return {"lote": "L1", "rodada": 1, "consolidado_em": date(2026, 11, 5), "entradas": {"fases/x": {**base, **entrada}}}

    def test_consolidado_valido(self):
        assert Consolidado.model_validate(self._consolidado()).rodada == 1

    @pytest.mark.parametrize("hash_", ["abc", "ABCDEF012345"])
    def test_hash_do_consolidado_tem_formato(self, hash_):
        with pytest.raises(ValidationError):
            Consolidado.model_validate(self._consolidado(hash=hash_))

    def test_rodada_comeca_em_um(self):
        with pytest.raises(ValidationError):
            Consolidado.model_validate({**self._consolidado(), "rodada": 0})

    @pytest.mark.parametrize("campo", ["hash", "estado_resultante", "bloqueia_abertos", "divergencia"])
    def test_campos_obrigatorios_da_entrada_consolidada(self, campo):
        dados = self._consolidado()
        del dados["entradas"]["fases/x"][campo]
        with pytest.raises(ValidationError):
            Consolidado.model_validate(dados)

    @pytest.mark.parametrize("campo", ["lote", "rodada", "consolidado_em", "entradas"])
    def test_campos_obrigatorios_do_consolidado(self, campo):
        dados = self._consolidado()
        del dados[campo]
        with pytest.raises(ValidationError):
            Consolidado.model_validate(dados)

    def _decisao(self) -> dict:
        return {"lote": "L1", "aprovado_em": date(2026, 11, 6), "aprovado_por": "Fulana", "aprovadas": ["fases/x"]}

    def test_decisao_sem_minutos_vale(self):
        decisao = Decisao.model_validate(self._decisao())
        assert decisao.minutos is None and decisao.excluidas == {} and decisao.sobreposicoes == {}

    def test_minutos_nao_negativos(self):
        assert Decisao.model_validate({**self._decisao(), "minutos": 0}).minutos == 0
        with pytest.raises(ValidationError):
            Decisao.model_validate({**self._decisao(), "minutos": -1})

    def test_aprovadas_sem_duplicata(self):
        with pytest.raises(ValidationError):
            Decisao.model_validate({**self._decisao(), "aprovadas": ["fases/x", "fases/x"]})

    @pytest.mark.parametrize("campo", ["lote", "aprovado_em", "aprovado_por", "aprovadas"])
    def test_campos_obrigatorios_da_decisao(self, campo):
        dados = self._decisao()
        del dados[campo]
        with pytest.raises(ValidationError):
            Decisao.model_validate(dados)

    def test_registros_sao_imutaveis(self):
        decisao = Decisao.model_validate(self._decisao())
        with pytest.raises(ValidationError):
            decisao.lote = "L2"

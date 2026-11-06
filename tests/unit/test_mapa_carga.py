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

import pytest
import yaml
from pydantic import ValidationError

from packages.tramitacao import mapa as modulo_mapa
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
        with pytest.raises(MapaIndisponivel):
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

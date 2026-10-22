"""Testes do núcleo comum dos pipelines de agentes (`apps/workers/agentes/`).

O painel exercita o núcleo com os seus parâmetros; estes testes exercitam o
que o painel não usa — insumos e ordem arbitrários, validador extra ausente,
mensagens padrão — porque é isso que o segundo pipeline vai usar. Nenhum
teste chama a rede: `consultar` é a fronteira, e aqui só se testa o parser que
ela usa.
"""

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apps.workers.agentes import (  # noqa: E402
    ABRE,
    FECHA,
    Agente,
    MetaExecucao,
    blindar,
    carregar_agente,
    carregar_conjunto,
    extrair_json,
    preambulo_seguranca,
)

INSUMOS = frozenset({"texto", "ficha"})


def _definicao(tmp_path: Path, nome: str, **extra) -> Path:
    bruto = {
        "agente": nome,
        "versao": 1,
        "papel": f"papel de {nome}",
        "vies_declarado": "declarado",
        "insumos": ["texto"],
        "modelo": "modelo-pinado",
        "instrucoes": f"instruções de {nome}",
    }
    bruto.update(extra)
    caminho = tmp_path / f"{nome}.yml"
    caminho.write_text(yaml.safe_dump(bruto, allow_unicode=True), encoding="utf-8")
    return caminho


# ── carga ─────────────────────────────────────────────────────────────────────

class TestCarga:
    def test_carrega_agente_com_insumos_do_pipeline(self, tmp_path):
        a = carregar_agente(_definicao(tmp_path, "leitor"), insumos_validos=INSUMOS)
        assert isinstance(a, Agente)
        assert a.nome == "leitor" and a.modelo == "modelo-pinado"
        assert a.etapas == ()  # sem etapas_padrao, nada é assumido

    def test_etapas_padrao_e_do_pipeline_nao_do_nucleo(self, tmp_path):
        a = carregar_agente(
            _definicao(tmp_path, "x"), insumos_validos=INSUMOS, etapas_padrao=("sintese",)
        )
        assert a.participa("sintese") and not a.participa("analise")
        assert a.participa_da_analise is False

    def test_insumo_fora_da_lista_do_pipeline_falha(self, tmp_path):
        caminho = _definicao(tmp_path, "x", insumos=["pareceres_dos_outros"])
        with pytest.raises(ValueError, match="insumos desconhecidos"):
            carregar_agente(caminho, insumos_validos=INSUMOS)

    def test_modelo_sem_pino_falha(self, tmp_path):
        bruto = yaml.safe_load(_definicao(tmp_path, "x").read_text(encoding="utf-8"))
        del bruto["modelo"]
        (tmp_path / "x.yml").write_text(yaml.safe_dump(bruto, allow_unicode=True), encoding="utf-8")
        with pytest.raises(KeyError):
            carregar_agente(tmp_path / "x.yml", insumos_validos=INSUMOS)

    def test_validador_extra_e_opcional_e_recebe_origem(self, tmp_path):
        visto = {}

        def extra(bruto, origem):
            visto["nome"], visto["origem"] = bruto["agente"], origem.name

        carregar_agente(_definicao(tmp_path, "x"), insumos_validos=INSUMOS, validar_extra=extra)
        assert visto == {"nome": "x", "origem": "x.yml"}

    def test_hash_muda_com_a_instrucao_e_so_com_ela(self, tmp_path):
        a = carregar_agente(_definicao(tmp_path, "a"), insumos_validos=INSUMOS)
        b = carregar_agente(
            _definicao(tmp_path, "b", instrucoes="instruções de a"), insumos_validos=INSUMOS
        )
        c = carregar_agente(
            _definicao(tmp_path, "c", instrucoes="outra coisa"), insumos_validos=INSUMOS
        )
        assert a.hash_instrucoes == b.hash_instrucoes  # mesma instrução, outro nome
        assert a.hash_instrucoes != c.hash_instrucoes


class TestConjunto:
    def test_ordem_arbitraria_e_respeitada(self, tmp_path):
        for n in ("c", "a", "b"):
            _definicao(tmp_path, n)
        conj = carregar_conjunto(tmp_path, ordem=("b", "c", "a"), insumos_validos=INSUMOS)
        assert [x.nome for x in conj] == ["b", "c", "a"]

    def test_faltando_um_da_ordem_falha_alto(self, tmp_path):
        _definicao(tmp_path, "a")
        with pytest.raises(ValueError, match="faltam os agentes: \\['b'\\]"):
            carregar_conjunto(tmp_path, ordem=("a", "b"), insumos_validos=INSUMOS)

    def test_agente_extra_usa_mensagem_padrao_quando_nao_ha_custom(self, tmp_path):
        _definicao(tmp_path, "a")
        _definicao(tmp_path, "intruso")
        with pytest.raises(ValueError, match="não previstos na ordem: \\['intruso'\\]"):
            carregar_conjunto(tmp_path, ordem=("a",), insumos_validos=INSUMOS)

    def test_mensagem_de_extras_do_pipeline_recebe_a_lista(self, tmp_path):
        _definicao(tmp_path, "a")
        _definicao(tmp_path, "z")
        with pytest.raises(ValueError, match="o pipeline diz: \\['z'\\]"):
            carregar_conjunto(
                tmp_path,
                ordem=("a",),
                insumos_validos=INSUMOS,
                mensagem_extras="o pipeline diz: {extras}",
            )

    def test_diretorio_inexistente_falha_com_a_mensagem_do_pipeline(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="onde está o mount"):
            carregar_conjunto(
                tmp_path / "nao-existe",
                ordem=("a",),
                insumos_validos=INSUMOS,
                mensagem_diretorio="onde está o mount",
            )

    def test_duplicado_falha(self, tmp_path):
        _definicao(tmp_path, "a")
        (tmp_path / "a2.yml").write_text(
            (tmp_path / "a.yml").read_text(encoding="utf-8"), encoding="utf-8"
        )
        with pytest.raises(ValueError, match="agente duplicado: a"):
            carregar_conjunto(tmp_path, ordem=("a",), insumos_validos=INSUMOS)


# ── blindagem ─────────────────────────────────────────────────────────────────

class TestBlindagem:
    def test_remove_qualquer_marca_nao_so_as_nossas(self):
        assert "<<<" not in blindar(f"a {ABRE} b {FECHA} c <<<INVENTADA>>> d")

    def test_texto_legitimo_passa_intacto(self):
        texto = "Art. 1º Fica instituída a Política Nacional de Minerais Críticos."
        assert blindar(texto) == texto

    def test_nulo_vira_vazio(self):
        assert blindar(None) == "" and blindar("") == ""

    def test_preambulo_declara_o_bloco_e_pede_sinal(self):
        p = preambulo_seguranca()
        assert ABRE in p and FECHA in p
        assert "DADO A ANALISAR" in p
        assert "injecao_detectada" in p
        assert "apenas desta mensagem de sistema" in p

    def test_preambulo_aceita_delimitadores_proprios(self):
        p = preambulo_seguranca("[[A]]", "[[F]]")
        assert "[[A]]" in p and "[[F]]" in p and ABRE not in p


# ── fronteira: só o parser; a rede não é testada ──────────────────────────────

class TestExtrairJson:
    def test_json_puro(self):
        assert extrair_json('{"a": 1}') == {"a": 1}

    def test_json_cercado_de_markdown(self):
        assert extrair_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_json_cercado_de_prosa(self):
        assert extrair_json('Segue a análise:\n{"a": 1}\nEspero ter ajudado.') == {"a": 1}

    def test_sem_json_devolve_erro_e_nao_inventa(self):
        r = extrair_json("não consigo responder")
        assert r["error"].startswith("json_parse_failed:")

    def test_vazio_ou_nulo_devolve_erro(self):
        assert "error" in extrair_json("") and "error" in extrair_json(None)


# ── meta ──────────────────────────────────────────────────────────────────────

def test_meta_execucao_registra_o_minimo_para_auditar():
    m = MetaExecucao(
        modelos={"a": "m1"}, hashes_instrucoes={"a": "h"}, versoes_agentes={"a": 1},
        iniciado_em="2026-10-21T00:00:00+00:00",
    )
    assert m.concluido_em is None and m.erros == []

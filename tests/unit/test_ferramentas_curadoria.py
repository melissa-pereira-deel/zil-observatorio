"""Testes das ferramentas de apoio à curadoria editorial.

Cobrem as funções puras — extração de placar, escore de saliência, sugestão de
peso e validação de schema. A coleta via API e a busca no Planalto ficam de fora
de propósito: dependem de rede e são testadas rodando as ferramentas de verdade.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
for _p in (str(REPO_ROOT), str(REPO_ROOT / "apps" / "api")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.candidatas import Candidata, extrair_placar, ja_curadas  # noqa: E402
from scripts.dossie import DadosVotacao, _peso_sugerido  # noqa: E402
from scripts.validar_direcoes import resumir, validar_arquivo  # noqa: E402


# ── extração de placar da descrição ───────────────────────────────────────────

def test_extrai_placar_do_formato_da_camara():
    d = "Aprovado o Projeto de Lei nº 1.847, de 2024. Sim: 253; não: 67; abstenção: 4."
    assert extrair_placar(d) == (253, 67)


def test_extrai_placar_e_insensivel_a_caixa_e_acento():
    assert extrair_placar("SIM: 10; NAO: 3") == (10, 3)


def test_descricao_sem_placar_devolve_none():
    assert extrair_placar("Aprovado o Requerimento, a pedido do Relator.") == (None, None)
    assert extrair_placar("") == (None, None)


# ── saliência: o que faz uma votação valer a pena ─────────────────────────────

def _candidata(votacao="Aprovado o Projeto de Lei nº 1", sim=100, nao=100, cats=None,
               ementa="Projeto de Lei sobre processamento de nióbio"):
    """`votacao` é a descrição do ato votado; `ementa` é o que o projeto faz.

    A distinção importa: a classificabilidade sai da primeira, o tema da segunda.
    """
    return Candidata(
        fonte_id="1-1", descricao=ementa, data="2024-01-01",
        categorias=cats or ["ZIL-MIN"], votos_sim=sim, votos_nao=nao,
        descricao_votacao=votacao,
    )


def test_votacao_disputada_pontua_mais_que_unanime():
    disputada = _candidata(sim=160, nao=150)
    unanime = _candidata(sim=310, nao=0)
    assert disputada.escore > unanime.escore


def test_requerimento_processual_e_penalizado():
    requerimento = _candidata(votacao="Aprovado o Requerimento de urgência")
    materia = _candidata(votacao="Aprovado o Projeto de Lei nº 1847")
    assert requerimento.escore < materia.escore


def test_voto_de_emenda_perde_para_voto_do_texto_mesmo_sendo_mais_disputado():
    """A classificabilidade domina: emenda sem texto é beco sem saída.

    Sem o texto da emenda — que a API não devolve — "sim" pode significar
    qualquer coisa, por mais apertado que tenha sido o placar.
    """
    emenda_apertada = _candidata(votacao="Rejeitada a Emenda de Plenário nº 1",
                                 sim=195, nao=222)
    texto_folgado = _candidata(votacao="Aprovado o Projeto de Lei nº 1847",
                               sim=253, nao=67)
    assert emenda_apertada.escore < texto_folgado.escore


def test_classificavel_distingue_emenda_de_texto():
    assert _candidata(votacao="Aprovado o Projeto de Lei nº 1847").classificavel is True
    assert _candidata(votacao="Rejeitada a Emenda de Plenário nº 1").classificavel is False
    assert _candidata(votacao="Mantido o texto").classificavel is False


def test_margem_zero_em_empate_e_um_em_unanimidade():
    assert _candidata(sim=50, nao=50).margem == 0.0
    assert _candidata(sim=50, nao=0).margem == 1.0


def test_sem_placar_nao_tem_margem():
    c = Candidata(fonte_id="1-1", descricao="x", data="", categorias=["ZIL-MIN"])
    assert c.margem is None
    assert c.rejeitada is False


def test_rejeitada_quando_nao_supera_sim():
    """A via mais natural para o corpus deixar de ter só direções `sim`."""
    assert _candidata(sim=100, nao=200).rejeitada is True
    assert _candidata(sim=200, nao=100).rejeitada is False


# ── peso sugerido a partir da descrição ───────────────────────────────────────

@pytest.mark.parametrize("descricao,esperado", [
    ("Aprovado o Requerimento de urgência", 0.5),
    ("Votação em Comissão de Constituição e Justiça", 2.0),
    ("Aprovada a Subemenda Substitutiva Global", 3.0),
    ("Aprovada a redação final", 3.0),
    ("Texto sem pista nenhuma", 1.0),
])
def test_peso_sugerido(descricao, esperado):
    peso, _motivo = _peso_sugerido(descricao)
    assert peso == esperado


# ── dados da votação ──────────────────────────────────────────────────────────

def test_resultado_deriva_da_aprovacao():
    assert DadosVotacao(fonte_id="1", aprovacao=1).resultado == "aprovada"
    assert DadosVotacao(fonte_id="1", aprovacao=0).resultado == "rejeitada"
    assert DadosVotacao(fonte_id="1", aprovacao=None).resultado == "indeterminado"


def test_total_de_votos_soma_todas_as_categorias():
    d = DadosVotacao(fonte_id="1", votos_sim=10, votos_nao=5, abstencoes=2, outros=3)
    assert d.total_votos == 20


# ── validação dos YAMLs de direções ───────────────────────────────────────────

_JUSTIFICATIVA_OK = (
    "PL 1234/2024 exige processamento local de nióbio antes da exportação, "
    "o que favorece a cadeia industrial nacional."
)


def _escrever(tmp_path: Path, entrada: str) -> Path:
    arquivo = tmp_path / "2024.yml"
    arquivo.write_text(f"direcoes:\n{entrada}", encoding="utf-8")
    return arquivo


def test_entrada_valida_nao_gera_problema(tmp_path):
    arquivo = _escrever(tmp_path, f"""
  - fonte_id: "123-4"
    fonte: camara
    direcao: sim
    peso: 3.0
    validacao: nao-validado
    justificativa: >
      {_JUSTIFICATIVA_OK}
""")
    assert validar_arquivo(arquivo) == []


def test_direcao_invalida_e_pega():
    """`Sim` com maiúscula passaria batido hoje e distorceria o score."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        arquivo = _escrever(Path(d), f"""
  - fonte_id: "123-4"
    fonte: camara
    direcao: Sim
    justificativa: >
      {_JUSTIFICATIVA_OK}
""")
        problemas = validar_arquivo(arquivo)
    assert any("direcao: Sim" in p for p in problemas)


def test_peso_fora_da_tabela_e_pego(tmp_path):
    arquivo = _escrever(tmp_path, f"""
  - fonte_id: "123-4"
    fonte: camara
    direcao: sim
    peso: 5
    justificativa: >
      {_JUSTIFICATIVA_OK}
""")
    assert any("peso: 5" in p for p in validar_arquivo(arquivo))


def test_justificativa_ausente_e_pega(tmp_path):
    arquivo = _escrever(tmp_path, """
  - fonte_id: "123-4"
    fonte: camara
    direcao: sim
""")
    assert any("sem `justificativa`" in p for p in validar_arquivo(arquivo))


def test_justificativa_curta_demais_e_pega(tmp_path):
    arquivo = _escrever(tmp_path, """
  - fonte_id: "123-4"
    fonte: camara
    direcao: sim
    justificativa: "porque sim"
""")
    assert any("curta demais" in p for p in validar_arquivo(arquivo))


def test_fonte_id_duplicado_e_pego(tmp_path):
    arquivo = _escrever(tmp_path, f"""
  - fonte_id: "123-4"
    fonte: camara
    direcao: sim
    justificativa: >
      {_JUSTIFICATIVA_OK}
  - fonte_id: "123-4"
    fonte: camara
    direcao: nao
    justificativa: >
      {_JUSTIFICATIVA_OK}
""")
    assert any("duplicado" in p for p in validar_arquivo(arquivo))


def test_campo_obrigatorio_ausente_e_pego(tmp_path):
    arquivo = _escrever(tmp_path, f"""
  - fonte: camara
    direcao: sim
    justificativa: >
      {_JUSTIFICATIVA_OK}
""")
    assert any("fonte_id" in p for p in validar_arquivo(arquivo))


def test_resumir_conta_direcoes_e_validacoes(tmp_path):
    _escrever(tmp_path, f"""
  - fonte_id: "1-1"
    fonte: camara
    direcao: sim
    validacao: nao-validado
    justificativa: >
      {_JUSTIFICATIVA_OK}
  - fonte_id: "2-2"
    fonte: camara
    direcao: nao
    validacao: revisado
    justificativa: >
      {_JUSTIFICATIVA_OK}
""")
    resumo = resumir(tmp_path)
    assert resumo["total"] == 2
    assert resumo["direcoes"] == {"sim": 1, "nao": 1}
    assert resumo["validacoes"] == {"nao-validado": 1, "revisado": 1}


# ── leitura dos YAMLs existentes ──────────────────────────────────────────────

def test_ja_curadas_le_os_ids_dos_yamls(tmp_path):
    _escrever(tmp_path, """
  - fonte_id: "999-1"
    fonte: camara
    direcao: sim
    justificativa: "x"
""")
    assert ja_curadas(tmp_path) == {"999-1"}


def test_ja_curadas_em_diretorio_inexistente_devolve_vazio(tmp_path):
    assert ja_curadas(tmp_path / "nao-existe") == set()


def test_subemenda_substitutiva_global_conta_como_texto_principal():
    """Ela contém "subemenda" mas substitui o projeto inteiro.

    É por isso que a votação já curada 2454704-53 tem peso 3.0. Tratá-la como
    emenda a dispositivo descartaria justamente as votações mais úteis.
    """
    global_ = _candidata(
        votacao="Aprovada a Subemenda Substitutiva Global ao Projeto de Lei nº 9.543"
    )
    emenda = _candidata(votacao="Rejeitada a Emenda de Plenário nº 1")
    assert global_.classificavel is True
    assert emenda.classificavel is False
    assert global_.escore > emenda.escore

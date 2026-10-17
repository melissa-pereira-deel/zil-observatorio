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

from scripts.candidatas import (  # noqa: E402
    Candidata,
    extrair_placar,
    ja_curadas,
    sem_citacoes_de_lei,
)
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
               ementa="Projeto de Lei sobre processamento de nióbio",
               keywords=None):
    """`votacao` é a descrição do ato votado; `ementa` é o que o projeto faz.

    A distinção importa: a classificabilidade sai da primeira, o tema da
    segunda. `keywords` é a procedência da classificação — o que separa tema de
    coincidência de vocabulário.
    """
    cats = cats or ["ZIL-MIN"]
    return Candidata(
        fonte_id="1-1", descricao=ementa, data="2024-01-01",
        categorias=cats, votos_sim=sim, votos_nao=nao,
        descricao_votacao=votacao,
        keywords=keywords if keywords is not None else {cats[0]: ["nióbio"]},
    )


def test_votacao_disputada_pontua_mais_que_unanime():
    disputada = _candidata(sim=160, nao=150)
    unanime = _candidata(sim=310, nao=0)
    assert disputada.escore > unanime.escore


def test_requerimento_processual_e_penalizado():
    requerimento = _candidata(votacao="Aprovado o Requerimento, a pedido do Relator")
    materia = _candidata(votacao="Aprovado o Projeto de Lei nº 1847")
    assert requerimento.escore < materia.escore


def test_urgencia_e_menos_penalizada_que_requerimento_generico():
    """Urgência nomeia o objeto; "Rejeitado o Requerimento" não.

    Quem votou sim na urgência da PNMCE quis pautar minerais críticos — isso é
    preferência revelada. Já num requerimento genérico não se sabe o que foi
    votado: `objetosPossiveis` devolve dezenas de candidatos sem apontar o
    votado, e sem isso a direção é chute.
    """
    urgencia = _candidata(votacao="Aprovado o Requerimento de Urgência (Art. 155 do RICD)")
    generico = _candidata(votacao="Rejeitado o Requerimento")
    assert urgencia.escore > generico.escore


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
    """Sinal a exibir, não atalho para direção `nao`.

    Em votação rejeitada a posição pró-soberania PODE ser votar `não` — mas só
    quando se sabe o que foi rejeitado. Em "Rejeitado o Requerimento", sem
    dizer qual, não se sabe: `objetosPossiveis` devolve dezenas de candidatos.
    """
    assert _candidata(sim=100, nao=200).rejeitada is True
    assert _candidata(sim=200, nao=100).rejeitada is False


# ── precisão temática: tema domina disputa ────────────────────────────────────

def test_casamento_forte_vence_casamento_fraco_mesmo_sendo_menos_disputado():
    """O caso real que motivou a mudança.

    A PNMCE (minerais críticos) foi aprovada 369×38 e ficava em último lugar;
    a Tarifa Social de Água e Esgoto liderava com 325×97 por ter casado com a
    palavra `tarifa`. Com placar focado, o topo tem que ser o que mais importa.
    """
    pnmce = _candidata(
        votacao="Aprovado o Requerimento de Urgência (Art. 155 do RICD)",
        sim=369, nao=38, cats=["ZIL-MIN"],
        keywords={"ZIL-MIN": ["minerais críticos"]},
    )
    tarifa_social = _candidata(
        votacao="Aprovada a Subemenda Substitutiva Global ao Projeto de Lei nº 9.543",
        sim=325, nao=97, cats=["ZIL-COM"],
        keywords={"ZIL-COM": ["tarifa"]},
    )
    assert pnmce.escore > tarifa_social.escore


def test_so_casamento_fraco_e_sinalizado():
    fraca = _candidata(cats=["ZIL-EDU"], keywords={"ZIL-EDU": ["técnico"]})
    forte = _candidata(cats=["ZIL-SEM"], keywords={"ZIL-SEM": ["semicondutor"]})
    assert fraca.so_casamento_fraco is True
    assert forte.so_casamento_fraco is False
    assert fraca.escore < forte.escore


def test_keyword_fraca_acompanhada_de_forte_nao_desqualifica():
    """Uma palavra comum não é inútil — ela só não basta sozinha."""
    c = _candidata(cats=["ZIL-EDU"], keywords={"ZIL-EDU": ["técnico", "semicondutor"]})
    assert c.so_casamento_fraco is False
    assert c.keywords_fortes == ["semicondutor"]


def test_indecidibilidade_supera_o_tema():
    """Votação sobre nióbio cuja direção não dá para decidir segue sem serventia."""
    emenda_sobre_tema = _candidata(
        votacao="Rejeitada a Emenda de Plenário nº 1", sim=195, nao=222,
        keywords={"ZIL-MIN": ["nióbio", "minerais críticos"]},
    )
    texto_sobre_tema = _candidata(
        votacao="Aprovado o Projeto de Lei nº 1847", sim=253, nao=67,
        keywords={"ZIL-MIN": ["nióbio"]},
    )
    assert emenda_sobre_tema.escore < texto_sobre_tema.escore


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


# ── citação de lei não é tema ─────────────────────────────────────────────────

def test_keyword_dentro_de_lei_citada_nao_conta_como_tema():
    """O PL 996/2015 liderou 2024 por um motivo errado.

    Ele trata de homicídio qualificado contra membros do MP e da Magistratura,
    e altera várias leis — entre elas a LGPD. As keywords `dados pessoais` e
    `proteção de dados` casaram dentro de "(Lei Geral de Proteção de Dados
    Pessoais)", que é o nome da lei alterada, não o assunto do projeto.
    """
    c = _candidata(
        votacao="Rejeitadas as Emendas do Senado Federal ao Projeto de Lei nº 996",
        sim=23, nao=404, cats=["ZIL-DIG"],
        keywords={"ZIL-DIG": ["dados pessoais", "proteção de dados"]},
    )
    c.keywords_substantivas = set()  # nenhuma sobreviveu fora dos parênteses
    assert c.keywords_citadas == ["dados pessoais", "proteção de dados"]
    assert c.keywords_fortes == []
    assert c.so_casamento_fraco is True


def test_keyword_fora_de_parenteses_continua_sendo_tema():
    """O exemplo aqui era `dados pessoais`, e não serve mais.

    Ele virou keyword fraca de ZIL-DIG na taxonomia: proteção de dados é
    privacidade, não soberania industrial. `fibra óptica` continua forte,
    porque é infraestrutura — que é o que ZIL-DIG mede.
    """
    c = _candidata(cats=["ZIL-DIG"], keywords={"ZIL-DIG": ["fibra óptica"]})
    c.keywords_substantivas = {"fibra óptica"}
    assert c.keywords_citadas == []
    assert c.keywords_fortes == ["fibra óptica"]


def test_sem_citacoes_de_lei_remove_so_o_parentese():
    texto = ("Altera o Decreto-Lei nº 2.848 (Código Penal) e a Lei nº 13.709 "
             "(Lei Geral de Proteção de Dados Pessoais), para prever homicídio")
    limpo = sem_citacoes_de_lei(texto)
    assert "proteção de dados" not in limpo.lower()
    assert "Código Penal" not in limpo
    assert "homicídio" in limpo
    assert "Altera o Decreto-Lei nº 2.848" in limpo


def test_sem_citacoes_preserva_parenteses_que_nao_sao_lei():
    texto = "Institui a Política Nacional de Minerais Críticos (PNMCE)"
    assert "PNMCE" in sem_citacoes_de_lei(texto)

"""Regra de consenso do painel — docs/PRD-PAINEL.md §7.

Esta é a tradução em código do princípio editorial que o projeto já tinha:
"na dúvida sobre direção esperada, não classificar" (PRD v1 §10). Antes
dependia da prudência de quem curava; aqui é aritmética.

Duas propriedades deliberadas:

- **Não há desempate por maioria simples.** Abaixo do limiar, o resultado é
  "contestada" e nenhuma classificação é proposta. Sem exceções (regra
  inviolável 2).
- **Dissenso é sinal, não ruído.** Uma tarifa protecionista é pró-soberania ou
  anti-competitividade? A resposta depende da teoria econômica assumida. Quando
  o painel não converge, o desacordo é o achado.
"""

from .schema import Apuracao, Direcao, Parecer

# 4 de 5. Com 5 agentes, exigir unanimidade tornaria o contraditor um veto
# permanente; exigir 3 seria maioria simples, que o PRD proíbe.
LIMIAR_CONSENSO = 4

# Acima disto, abstenção deixa de ser dúvida de um agente e passa a significar
# que não há matéria a classificar (votação procedimental, por exemplo).
LIMIAR_SEM_MATERIA = 4

NOME_CONTRADITOR = "contraditor"


def apurar(pareceres: list[Parecer]) -> Apuracao:
    """Aplica a regra de consenso a um conjunto de pareceres.

    Recebe os pareceres **finais** — isto é, os da etapa de confronto quando ela
    ocorreu, e os da análise independente quando não. Chamar com uma mistura das
    duas etapas conta o mesmo agente duas vezes, então isto é verificado.
    """
    if not pareceres:
        raise ValueError("nenhum parecer a apurar")

    agentes = [p.agente for p in pareceres]
    duplicados = {a for a in agentes if agentes.count(a) > 1}
    if duplicados:
        raise ValueError(
            f"mesmo agente aparece mais de uma vez na apuração: {sorted(duplicados)} "
            "— passe os pareceres de uma única etapa"
        )

    votos = {"sim": 0, "nao": 0, "abster": 0}
    for p in pareceres:
        votos[p.direcao] += 1

    placar = f"{votos['sim']}-{votos['nao']}-{votos['abster']}"

    # A objeção decisiva do contraditor derruba o consenso mesmo quando a
    # aritmética o concederia: o PRD §7 prevê que, se o consenso não se
    # recompõe depois dela, o resultado é "contestada". Um contraditor que
    # declara a objeção decisiva está dizendo exatamente isso.
    objecao_decisiva = any(
        p.agente == NOME_CONTRADITOR and p.forca_objecao == "decisivo"
        for p in pareceres
    )

    direcao_vencedora: Direcao | None = None
    maior = 0
    for direcao in ("sim", "nao"):
        if votos[direcao] > maior:
            maior, direcao_vencedora = votos[direcao], direcao  # type: ignore[assignment]

    if maior >= LIMIAR_CONSENSO and not objecao_decisiva:
        return Apuracao(
            placar=placar,
            votos=votos,
            resultado="proposta",
            direcao_proposta=direcao_vencedora,
            motivo=(
                f"{maior} de {len(pareceres)} convergiram em '{direcao_vencedora}' "
                f"(limiar {LIMIAR_CONSENSO})"
            ),
        )

    if maior >= LIMIAR_CONSENSO and objecao_decisiva:
        return Apuracao(
            placar=placar,
            votos=votos,
            resultado="contestada",
            direcao_proposta=None,
            motivo=(
                f"{maior} de {len(pareceres)} convergiram em '{direcao_vencedora}', "
                "mas o contraditor classificou a objeção como decisiva — o consenso "
                "não se recompôs (PRD-PAINEL §7)"
            ),
        )

    if votos["abster"] >= LIMIAR_SEM_MATERIA:
        return Apuracao(
            placar=placar,
            votos=votos,
            resultado="sem_materia",
            direcao_proposta=None,
            motivo=(
                f"{votos['abster']} de {len(pareceres)} se abstiveram — o painel não "
                "encontrou matéria a classificar, o que não é o mesmo que dissenso"
            ),
        )

    return Apuracao(
        placar=placar,
        votos=votos,
        resultado="contestada",
        direcao_proposta=None,
        motivo=(
            f"nenhuma direção alcançou {LIMIAR_CONSENSO} de {len(pareceres)} "
            "— pauta contestada, sem classificação e com o dissenso publicado"
        ),
    )

"""Vocabulário fechado do contrato de tramitação (backlog-dados §1.5) e a base dos modelos estritos."""

from typing import Annotated, Literal, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict

Fase = Literal["apresentada", "comissoes", "plenario", "outra_casa", "retorno",
               "sancao", "veto_congresso", "promulgacao", "norma"]
Desfecho = Literal["arquivada", "retirada", "prejudicada", "rejeitada",
                   "perdeu_eficacia", "vetada", "devolvida"]
Motivo = Literal["situacao_sem_mapa", "sinais_conflitantes", "principal_nao_resolvida",
                 "fonte_indisponivel", "especie_fora_do_escopo", "mapa_nao_aprovado",
                 "recem_apresentada"]
EstadoEtapa = Literal["feita", "atual", "futura", "pulada", "interrompida"]
Revisao = Literal["rascunho", "revisado_agentes", "aprovado"]
Casa = Literal["camara", "senado"]
CasaRito = Literal["camara", "senado", "congresso", "presidencia"]
Especie = Literal["PL", "PLP", "PEC", "MPV", "PDL"]
ClassePrazo = Literal["D", "D*", "X"]
RegraId = Literal["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"]


class Estrito(BaseModel):
    # Mora aqui, e não em mapa.py, porque mapa.py importa revisao.py, que também precisa dela.
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


def _sem_duplicata(valores: list) -> list:
    vistos: list = []
    for valor in valores:
        if valor in vistos:
            raise ValueError(f"valor repetido: {valor}")
        vistos.append(valor)
    return valores


T = TypeVar("T")
Conjunto = Annotated[list[T], AfterValidator(_sem_duplicata)]

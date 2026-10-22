"""Núcleo comum dos pipelines de agentes do ZIL Observatório.

Extraído de `apps/workers/panel/` quando um segundo pipeline (a explicação de
proposições) precisou das mesmas garantias com outra regra de síntese. O que
mora aqui é o que **não depende da tarefa**:

- `carga`      — definição de agente em YAML, com viés declarado, modelo pinado
                 e hash das instruções (PRD-PAINEL §5, §9.1, regra inviolável 7).
- `blindagem`  — texto de fonte é dado não confiável: delimitadores, remoção
                 de marcas forjadas e o preâmbulo de segurança do system prompt
                 (regra inviolável 6).
- `fronteira`  — a única função que fala com a API da Anthropic. Toda a
                 orquestração de qualquer pipeline é determinística e testável
                 sem rede; os testes substituem esta função e só ela.
- `meta`       — `MetaExecucao`: o que torna uma execução reproduzível e
                 auditável depois.

O que **não** mora aqui, de propósito: formato de resposta, briefing, montagem
de prompt, parse do parecer, regra de consenso ou de síntese. Isso é tarefa, e
cada pipeline tem a sua. O painel apura veredito por 4/5; a explicação preserva
dissenso. Um núcleo que soubesse disso já não seria núcleo.
"""

from .blindagem import ABRE, FECHA, PARECE_DELIMITADOR, blindar, preambulo_seguranca
from .carga import (
    CAMPOS_OBRIGATORIOS,
    Agente,
    carregar_agente,
    carregar_conjunto,
    validar_definicao,
)
from .fronteira import consultar, consultar_com_ferramentas, extrair_json
from .meta import MetaExecucao

__all__ = [
    "ABRE",
    "FECHA",
    "PARECE_DELIMITADOR",
    "blindar",
    "preambulo_seguranca",
    "CAMPOS_OBRIGATORIOS",
    "Agente",
    "carregar_agente",
    "carregar_conjunto",
    "validar_definicao",
    "consultar",
    "consultar_com_ferramentas",
    "extrair_json",
    "MetaExecucao",
]

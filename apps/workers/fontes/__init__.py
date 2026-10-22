"""Fontes externas curadas — a allowlist, a fronteira com a rede e o contexto.

Os pipelines de agentes liam só Câmara, Senado e Planalto, e o slot
`contexto_economico` que o economista declara como insumo nunca foi
preenchido: as perguntas "quem paga e por quanto tempo" eram respondidas de
memória do modelo, a única fonte que não dá para auditar. Este pacote é o
que preenche o slot — e o faz de um jeito que não devolve a escolha ao
modelo.

Três partes, três garantias:

- `catalogo`  — `data/fontes/catalogo.yml` é a allowlist. Toda fonte declara
                natureza e viés ("oficial" não é "neutro"); toda fonte diz se
                é primária, e secundária nunca conta como evidência
                independente; toda série tem os conceitos pelos quais pode ser
                escolhida. Muda por PR; o hash vai para o meta.
- `cliente`   — a única função que toca a rede para dados. A allowlist é
                aplicada no transporte do httpx, não em instrução; falha vira
                lacuna declarada, nunca exceção; consulta é sempre por
                intervalo explícito, porque "último valor" não é "valor de
                hoje" (a meta Selic é publicada com datas futuras).
- `contexto`  — o plano pré-registrado por tema decide o que entra ANTES de
                qualquer resultado, idêntico para todas as lentes, ancorado na
                data de apresentação da proposição. Nenhuma lente busca nada.

O que fica de fora, de propósito: busca na web, URL livre, ferramentas para
as lentes. Se um dia entrarem, é RFC — o argumento contra está em `contexto`.
"""

from .catalogo import ADAPTADORES, NATUREZAS, Catalogo, Fonte, Serie, carregar_catalogo, normalizar
from .cliente import (
    HostNaoPermitido,
    Observacao,
    Observacoes,
    TransportePermitido,
    consultar_serie,
)
from .contexto import ContextoEconomico, Linha, Plano, carregar_plano, fim_vigente, montar_contexto, planejar

__all__ = [
    "ADAPTADORES",
    "NATUREZAS",
    "Catalogo",
    "Fonte",
    "Serie",
    "carregar_catalogo",
    "normalizar",
    "HostNaoPermitido",
    "Observacao",
    "Observacoes",
    "TransportePermitido",
    "consultar_serie",
    "ContextoEconomico",
    "Linha",
    "Plano",
    "carregar_plano",
    "fim_vigente",
    "montar_contexto",
    "planejar",
]

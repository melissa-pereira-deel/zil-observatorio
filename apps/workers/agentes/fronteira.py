"""A fronteira única com a API da Anthropic.

Toda a orquestração de qualquer pipeline de agentes é determinística e
testável sem rede; esta é a função que os testes substituem — e só ela. Manter
uma fronteira só é o que permite dizer, com um `grep`, onde o projeto gasta
tokens.

Sobre o SDK: o projeto está em `anthropic==0.40.0`, que não tem
`messages.parse()` nem `output_config`. Por isso a saída estruturada vem por
instrução no prompt mais parse tolerante (`extrair_json`). Subir o SDK para
obter structured outputs de verdade é uma mudança separada, e vale a pena —
tiraria o parser daqui.

O contrato de erro é parte da fronteira: qualquer falha volta como
`{"error": "<motivo>"}`, nunca como exceção. Cada pipeline decide o que fazer
com isso (o painel degrada para abstenção; a explicação marca a lente como
indisponível). Lançar exceção aqui obrigaria cada chamador a saber o que pode
dar errado dentro da rede.
"""

import json
import re
from typing import Optional


def extrair_json(bruto: str) -> dict:
    """Parse tolerante: aceita JSON puro ou JSON cercado de texto.

    O modelo é instruído a responder só com o objeto, mas às vezes envolve em
    markdown ou comenta antes. O que importa é não perder uma resposta válida
    por causa de um ``` — e não inventar uma quando não há.
    """
    bruto = (bruto or "").strip()
    try:
        return json.loads(bruto)
    except json.JSONDecodeError:
        achado = re.search(r"\{.*\}", bruto, re.DOTALL)
        if achado:
            try:
                return json.loads(achado.group())
            except json.JSONDecodeError:
                pass
        return {"error": f"json_parse_failed: {bruto[:200]}"}


def consultar(
    modelo: str,
    system: str,
    prompt: str,
    *,
    max_tokens: int,
    api_key: Optional[str] = None,
) -> dict:
    """Uma chamada ao modelo; devolve o JSON da resposta ou `{"error": ...}`.

    `api_key` existe para testes e para rodar fora do `settings`; o padrão é
    `settings.ANTHROPIC_API_KEY`, importado tarde para que importar este
    módulo não exija o `apps/api` no path.
    """
    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic não instalado — execute: pip install anthropic"}

    if api_key is None:
        from core.config import settings

        api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY não configurado"}

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=modelo,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return extrair_json(message.content[0].text)

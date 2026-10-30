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
from typing import Callable, Optional


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


# Chave reservada no dict de resposta: tokens gastos na chamada. Quem
# orquestra retira antes de ler o resto (`retirar_uso`). Fica no dict, e não
# numa tupla de retorno, para que os consultores falsos dos testes — que não
# gastam token nenhum — continuem válidos sem mudança.
USO = "_uso"


def _somar_uso(acumulado: Optional[dict], resposta) -> dict:
    uso = getattr(resposta, "usage", None)
    acumulado = dict(acumulado or {"entrada": 0, "saida": 0})
    acumulado["entrada"] += int(getattr(uso, "input_tokens", 0) or 0)
    acumulado["saida"] += int(getattr(uso, "output_tokens", 0) or 0)
    return acumulado


def _com_uso(resultado: dict, uso: Optional[dict]) -> dict:
    if uso is not None and isinstance(resultado, dict):
        resultado[USO] = uso
    return resultado


def retirar_uso(resultado: dict) -> dict:
    """Tira e devolve os tokens de uma resposta; `{}` se não houver."""
    if not isinstance(resultado, dict):
        return {}
    return resultado.pop(USO, None) or {}


def texto_da_resposta(blocos) -> str:
    """Junta só os blocos de texto. O modelo pode pensar antes de responder,
    e o raciocínio chega como bloco próprio, antes do texto — no SDK 0.40
    ele aparece como `TextBlock` com `type="thinking"` e texto vazio. Ler só
    o primeiro bloco devolvia "" e o parser falhava em todas as lentes
    (primeira chamada real, 2026-10-22)."""
    return "".join(getattr(b, "text", "") or "" for b in blocos or [] if getattr(b, "type", None) == "text")


def consultar(
    modelo: str,
    system: str,
    prompt: str,
    *,
    max_tokens: int,
    api_key: Optional[str] = None,
    esforco: Optional[str] = None,
    fallback: bool = False,
) -> dict:
    """Uma chamada ao modelo; devolve o JSON da resposta ou `{"error": ...}`.

    `api_key` existe para testes e para rodar fora do `settings`; o padrão é
    `settings.ANTHROPIC_API_KEY`, importado tarde para que importar este
    módulo não exija o `apps/api` no path.

    `esforco` (`low` a `max`) vai em `output_config.effort`. `fallback` liga o
    fallback do servidor para recusas (`fallbacks: "default"`): se o
    classificador de segurança recusar, a API refaz a chamada noutro modelo em
    vez de devolver vazio. O SDK pinado (0.40) não tem esses parâmetros, então
    os dois vão por `extra_body`/`extra_headers`.
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

    extra_body: dict = {}
    extra_headers: dict = {}
    if esforco:
        extra_body["output_config"] = {"effort": esforco}
    if fallback:
        extra_body["fallbacks"] = "default"
        extra_headers["anthropic-beta"] = "server-side-fallback-2026-07-01"

    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model=modelo,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            extra_body=extra_body or None,
            extra_headers=extra_headers or None,
        )
    except anthropic.AuthenticationError:
        # Nunca inclui a chave na mensagem — nem parte dela.
        return {"error": "ANTHROPIC_API_KEY recusada pela API (401): chave inválida ou revogada"}
    except anthropic.APIStatusError as e:
        return {"error": f"API respondeu {e.status_code}: {type(e).__name__}"}
    except anthropic.APIError as e:
        return {"error": f"chamada falhou: {type(e).__name__}"}
    uso = _somar_uso(None, message)
    if message.stop_reason == "max_tokens":
        return _com_uso({"error": f"resposta cortada no limite de {max_tokens} tokens"}, uso)
    if message.stop_reason == "refusal":
        # Sem fallback, ou com o fallback também recusando: erro declarado, não
        # texto vazio que o parser transformaria em json_parse_failed.
        detalhe = getattr(message, "stop_details", None)
        categoria = getattr(detalhe, "category", None) if detalhe else None
        return _com_uso({"error": f"recusa do modelo ({categoria or 'sem categoria'})"}, uso)
    return _com_uso(extrair_json(texto_da_resposta(message.content)), uso)


# ── uso de ferramentas ────────────────────────────────────────────────────────
#
# Um agente com ferramenta escolhe o que consultar, e essa escolha é o vetor de
# viés mais silencioso que existe. Por isso o desenho é este, e não outro:
#
# - o LAÇO é do harness, não do modelo: cada rodada passa por aqui, e um teto
#   de rodadas impede que a busca vire exploração;
# - a ferramenta é EXECUTADA por quem chama (`executor`), que decide o que é
#   permitido — esta função não sabe o que é uma série nem um catálogo;
# - TODA chamada vai para `registro`, com argumentos e resultado resumido. A
#   escolha do agente fica auditável chamada por chamada.

Executor = Callable[[str, dict], dict]


def _bloco_para_dict(bloco) -> Optional[dict]:
    """Converte um bloco de conteúdo do SDK em dict, para reenviá-lo.

    Blocos de raciocínio voltam como vieram, com a assinatura: a API exige
    que o raciocínio anterior a um uso de ferramenta seja devolvido intacto.
    Texto vazio não volta — a API recusa bloco de texto vazio.
    """
    tipo = getattr(bloco, "type", None)
    if tipo == "tool_use":
        return {"type": "tool_use", "id": bloco.id, "name": bloco.name, "input": bloco.input}
    if tipo in ("thinking", "redacted_thinking"):
        d = bloco.model_dump() if hasattr(bloco, "model_dump") else dict(vars(bloco))
        if tipo == "thinking":
            return {"type": "thinking", "thinking": d.get("thinking", ""), "signature": d.get("signature", "")}
        return {"type": "redacted_thinking", "data": d.get("data", "")}
    texto = getattr(bloco, "text", "") or ""
    return {"type": "text", "text": texto} if texto else None


def _resumo(resultado: dict, limite: int = 300) -> str:
    texto = json.dumps(resultado, ensure_ascii=False, default=str)
    return texto if len(texto) <= limite else texto[:limite] + "…"


def consultar_com_ferramentas(
    modelo: str,
    system: str,
    prompt: str,
    *,
    ferramentas: list[dict],
    executor: Executor,
    max_tokens: int,
    max_rodadas: int = 6,
    registro: Optional[list] = None,
    api_key: Optional[str] = None,
    cliente=None,
) -> dict:
    """Uma conversa com ferramentas; devolve o JSON final ou `{"error": ...}`.

    `executor(nome, argumentos) -> dict` roda a ferramenta. O resultado volta
    ao modelo como JSON. `registro`, se dado, recebe um dict por chamada:
    `{"rodada", "ferramenta", "argumentos", "resultado"}`.

    `cliente` existe para os testes (um objeto com `.messages.create`); o
    padrão é o SDK real, com a mesma regra de chave de `consultar`.
    """
    if cliente is None:
        try:
            import anthropic
        except ImportError:
            return {"error": "anthropic não instalado — execute: pip install anthropic"}
        if api_key is None:
            from core.config import settings

            api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY não configurado"}
        cliente = anthropic.Anthropic(api_key=api_key)

    mensagens: list[dict] = [{"role": "user", "content": prompt}]
    gasto: Optional[dict] = None
    for rodada in range(1, max_rodadas + 1):
        try:
            resposta = cliente.messages.create(
                model=modelo,
                max_tokens=max_tokens,
                system=system,
                tools=ferramentas,
                messages=mensagens,
            )
        except Exception as e:  # noqa: BLE001 — erro de rede/API vira contrato de erro
            if type(e).__name__ == "AuthenticationError":
                return _com_uso({"error": "ANTHROPIC_API_KEY recusada pela API (401): chave inválida ou revogada"}, gasto)
            return _com_uso({"error": f"chamada falhou na rodada {rodada}: {type(e).__name__}"}, gasto)

        gasto = _somar_uso(gasto, resposta)
        blocos = list(resposta.content or [])
        usos = [b for b in blocos if getattr(b, "type", None) == "tool_use"]
        if not usos:
            if getattr(resposta, "stop_reason", None) == "max_tokens":
                return _com_uso({"error": f"resposta cortada no limite de {max_tokens} tokens"}, gasto)
            return _com_uso(extrair_json(texto_da_resposta(blocos)), gasto)

        mensagens.append({"role": "assistant", "content": [d for d in (_bloco_para_dict(b) for b in blocos) if d]})
        resultados = []
        for uso in usos:
            try:
                saida = executor(uso.name, dict(uso.input or {}))
            except Exception as e:  # noqa: BLE001 — executor com bug não derruba a conversa
                saida = {"erro": f"executor falhou: {type(e).__name__}"}
            if registro is not None:
                registro.append(
                    {"rodada": rodada, "ferramenta": uso.name, "argumentos": dict(uso.input or {}), "resultado": _resumo(saida)}
                )
            resultados.append(
                {
                    "type": "tool_result",
                    "tool_use_id": uso.id,
                    "content": json.dumps(saida, ensure_ascii=False, default=str),
                    "is_error": "erro" in saida,
                }
            )
        mensagens.append({"role": "user", "content": resultados})

    return _com_uso({"error": f"ferramentas: limite de {max_rodadas} rodadas atingido sem resposta final"}, gasto)

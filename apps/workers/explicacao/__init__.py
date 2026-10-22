"""Pipeline de explicação de proposições — Fase 1 (harness, sem LLM calibrado).

Produz, por proposição, três sínteses sem veredito:

- **resumo didático** (240–640 caracteres): a essência do que o dispositivo
  torna verdadeiro no mundo — fidelidade ao texto, não ao discurso do autor;
- **resumo detalhado** (480–2480): quem, quando, por quê, com quem, o que mais
  isso toca — **todo fato rastreável a um campo da fonte**;
- **análise crítica sistêmica**: causas raízes, dependências, fatores
  limitantes e dimensões (pública, cível, ambiental, jurídica, saúde,
  pesquisa, econômica) — argumento, não fato, com lente declarada.

O que difere do painel (`apps/workers/panel/`): lá a divergência entre
agentes vira "contestada" e nenhuma classificação sai. Aqui **síntese não tem
consenso a apurar** — a divergência entre lentes tem que sobreviver no texto
final, nomeada em `dissensos[]`, e uma síntese que a apaga falha na validação.
Esse é o mecanismo de equilíbrio de viés, e é o que o sintetizador existe para
garantir.

Regras que este módulo carrega em código, não em disciplina:

1. Fatos só de contexto confiável: a ficha (`coleta.py`) entra como dado do
   projeto; texto integral e justificação entram blindados. O revisor rejeita
   saída com nome, partido ou data ausentes da ficha.
2. `dissensos` é obrigatório. Vazio só passa quando as lentes convergiram de
   fato (`revisao.py`).
3. "O texto diz" ≠ "eu infiro": cada afirmação de lente tem `tipo` e, se
   literal, citação conferida contra o texto extraído.
4. O agente `industrial` — advogado da tese do projeto — não participa. A
   explicação é para o público entender a proposição; a tese entra depois, na
   curadoria, onde é legítima e declarada.
5. Uma fronteira com a rede, injetada: `explicar(..., consultar=...)`. Tudo o
   mais é determinístico e testável sem chave.

Fase 1 entrega o harness: coleta, extração, schema, roteamento, DAG, revisão
determinística, persistência e casos construídos. As instruções dos agentes
existem (`data/explicacao/agentes/`) mas não foram calibradas com chamada
real — isso é a Fase 2, e o go/no-go dela é o que autoriza a Fase 3.
"""

from .pipeline import Insumos, explicar
from .schema import (
    LIMITES,
    AnaliseSistemica,
    Afirmacao,
    Dissenso,
    Explicacao,
    ParecerLente,
    ResumoDetalhado,
    ResumoDidatico,
    TamanhoInvalido,
)

__all__ = [
    "Insumos",
    "explicar",
    "LIMITES",
    "AnaliseSistemica",
    "Afirmacao",
    "Dissenso",
    "Explicacao",
    "ParecerLente",
    "ResumoDetalhado",
    "ResumoDidatico",
    "TamanhoInvalido",
]

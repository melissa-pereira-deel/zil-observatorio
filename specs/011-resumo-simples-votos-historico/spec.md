# 011 — Resumo Simples no Historico de Votos do Parlamentar

## Overview

No perfil do parlamentar (`/parlamentar/[id]`), a secao "Historico de votos em pautas ZIL" exibe o texto da `votacao.descricao` — a descricao tecnica da votacao preenchida pela API da Camara (ex: "Requerimento de Urgencia para apreciacao do PL 1523/2026, que altera a Lei n 14.744..."). Este texto e juridico, pouco informativo e dificil de entender para o cidadao.

As 406 proposicoes ja possuem `resumo_simples` — um texto gerado por IA que explica a proposicao em linguagem cidada (ex: "Cria regras para que sistemas de IA sejam usados de forma mais justa e transparente no Brasil."). Porem esse campo nao e retornado pelo endpoint `GET /parlamentares/{id}/votos-zil` e consequentemente nao e exibido no frontend.

## Problem Statement

O historico de votos usa texto tecnico (`votacao.descricao`) em vez do resumo acessivel (`proposicao.resumo_simples`) ja disponivel no banco. O cidadao nao consegue entender rapidamente sobre o que cada votacao trata.

## Functional Requirements

1. O endpoint `GET /parlamentares/{id}/votos-zil` deve retornar o campo `resumo_simples` da proposicao vinculada a cada votacao
2. O frontend deve exibir `resumo_simples` como texto unico de cada item do historico quando disponivel — `descricao` nao e exibido nesse caso. Texto truncado em ~200 caracteres com "..." quando exceder esse limite
3. Quando `resumo_simples` for `null` (proposicao sem enriquecimento ou votacao sem proposicao vinculada), o fallback deve ser `votacao.descricao` (comportamento atual preservado)
4. O campo `descricao` da votacao continua disponivel na resposta da API mas nao e renderizado quando `resumo_simples` esta presente

## Data Flow

```
Proposicao.resumo_simples (banco, ja preenchido para 406 proposicoes)
  -> VotoHistorico schema (novo campo optional)
    -> endpoint votos-zil (passa dado do JOIN existente)
      -> frontend VotoHistorico type (novo campo)
        -> renderizacao no perfil (texto principal com fallback)
```

## Actors

- **Cidadao**: usuario sem conhecimento juridico que consulta o perfil de um parlamentar para entender como votou

## User Stories

- Como cidadao, quero ver um resumo em linguagem simples de cada pauta votada pelo parlamentar, para entender rapidamente o assunto sem precisar ler jargao legislativo.

## Out of Scope

- Alteracao do modelo de dados (Proposicao ja tem `resumo_simples`)
- Migracoes de banco
- Alteracao no pipeline de enriquecimento
- Exibicao de `resumo_simples` em outras paginas (ranking, proposicoes) — ja coberto por outros fluxos
- Re-enriquecimento de proposicoes sem resumo

## Technical Context

- O JOIN entre `Votacao` e `Proposicao` ja existe no endpoint (linha 98 de `parlamentares.py`)
- O campo `resumo_simples` ja existe no modelo `Proposicao` (mapped_column Text)
- 406/406 proposicoes possuem `resumo_simples` preenchido apos bulk enrichment
- O schema `VotoHistorico` (Pydantic) nao inclui `resumo_simples` atualmente
- O tipo TypeScript `VotoHistorico` em `lib/api.ts` tambem nao inclui o campo

## Files to Modify

| File | Layer | Change |
|------|-------|--------|
| `apps/api/schemas/__init__.py` | Backend schema | Adicionar `resumo_simples: Optional[str] = None` ao `VotoHistorico` |
| `apps/api/routers/parlamentares.py` | Backend router | Passar `proposicao.resumo_simples` ao construir `VotoHistorico` |
| `apps/web/lib/api.ts` | Frontend type | Adicionar `resumo_simples: string \| null` ao `VotoHistorico` |
| `apps/web/app/parlamentar/[parlamentar_id]/page.tsx` | Frontend render | Usar `resumo_simples` como texto principal com fallback para `descricao` |

## Success Criteria

- Perfil do parlamentar exibe resumo acessivel em vez de texto tecnico para votacoes com proposicao enriquecida
- Votacoes sem proposicao ou sem enriquecimento continuam exibindo `descricao` como fallback
- 151 testes existentes continuam passando
- Sem regressao visual nas demais secoes do perfil

## Clarifications

### Session 2026-04-05
- Q: Quando `resumo_simples` esta presente, o que fazer com `descricao`? → A: Esconder `descricao` — exibir apenas `resumo_simples` como texto do item
- Q: Devemos truncar `resumo_simples` no historico de votos? → A: Sim, truncar em ~200 caracteres com "..." e link "ver proposicao" para texto completo
- Q: Affordance para texto completo quando truncado? → A: Manter link apenas na posicao atual (ao lado do label) — sem duplicacao

## Edge Cases

- Votacao sem proposicao vinculada (`proposicao = None`): exibir `descricao` como hoje
- Proposicao com `resumo_simples = null` (status pendente): exibir `descricao` como fallback
- `resumo_simples` longo (>200 chars): truncar com "..." — link "ver proposicao" ja existente permite acesso ao texto completo
- Multiplas votacoes sobre a mesma proposicao: todas exibem o mesmo `resumo_simples` (correto — e a mesma proposicao)

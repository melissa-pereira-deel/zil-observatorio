# UI/UX — Credibilidade e Usabilidade
**Data:** 2026-04-02
**Origem:** Design critique sistemático (Interface Craft methodology)
**Branch sugerida:** `ui-ux-credibility-polish`

---

## Contexto

Após implementar as features funcionais (001–006), um audit sistemático identificou 8 oportunidades de melhoria. Nenhuma exige mudança de backend ou migração de dados. Todas estão no frontend (Next.js + Tailwind CSS).

**Princípio central:** numa plataforma de dados públicos, credibilidade é o produto. UI que parece inacabada destrói a confiança que o conteúdo tenta construir.

---

## Tasks

### UI-001 — Score com âncora de credibilidade
**Severidade:** Estrutural
**Problema:** O gauge `+10.0` flutua sem contexto. O usuário não sabe se é raro, como foi calculado, nem com base em quantos votos.

**Implementação:**
- `ScoreGauge` aceita prop opcional `totalVotosZil?: number`
- Quando fornecido, renderiza abaixo do número: `"com base em N votos"` em `font-mono text-2xs text-zil-muted`
- Adicionar atributo `title` no elemento raiz: `"Score calculado a partir de N votos em pautas ZIL · Saiba mais em /metodologia"`
- Em `ranking/page.tsx`: passar `total_votos_zil` que já vem da API (`ParlamentarRanking.total_votos_zil`)
- Em `parlamentar/[id]/page.tsx`: exibir `votos.length` como total

**Acceptance criteria:**
- [ ] Gauge no ranking mostra "com base em N votos" abaixo do score
- [ ] Gauge no perfil do parlamentar mostra o mesmo
- [ ] Parlamentares sem score (`null`) não exibem linha de votos
- [ ] O texto linka para `/metodologia` ou tem `title` explicativo

---

### UI-002 — Remover "Contexto pendente" da UI pública
**Severidade:** Estrutural
**Problema:** Badge técnico de estado interno do pipeline vaza para o usuário público. "Contexto pendente" comunica incompletude, não valor.

**Implementação:**
- `ContextoBadge`: `null | "pendente" | "processando"` → retorna `null` (sem renderização)
- `"falhou" | "llm_falhou"` → também retorna `null`
- Só renderiza badge quando `status === "pronto"` → badge verde "Análise disponível"
- Remover do `app/proposicoes/page.tsx` a exibição do badge na lista quando pendente

**Acceptance criteria:**
- [ ] Proposições sem enriquecimento não exibem nenhum badge de contexto
- [ ] Proposições com `contexto_status === "pronto"` exibem badge verde
- [ ] Falhas internas não são expostas ao usuário

---

### UI-003 — Contagem acima da lista
**Severidade:** Comportamental
**Problema:** Counts ("5 proposições", "X parlamentares") aparecem no rodapé após scroll.

**Implementação:**
- Mover o bloco de contagem para **imediatamente acima** da `border-t` que inicia a lista
- Ranking: `"{comScore.length} com score · {semScore.length} sem votos ZIL suficientes"` — alinhado à direita
- Proposições: `"{filtered.length}{busca ? ` de ${proposicoes.length}` : ''} proposições"` — alinhado à direita
- Tipografia: `font-mono text-xs text-zil-muted`

**Acceptance criteria:**
- [ ] Contagem visível sem scroll em viewport 768px+
- [ ] Atualiza em tempo real quando filtros mudam
- [ ] Formato correto com e sem filtro ativo

---

### UI-004 — Empty states significativos
**Severidade:** Comportamental
**Problema:** Estado vazio não diferencia "parlamentar não votou" de "cobertura ainda não disponível".

**Implementação — 3 cenários:**

**A. Parlamentar sem votos ZIL** (`votos.length === 0` após load):
```
Nenhuma votação ZIL registrada para este parlamentar.
A cobertura atual inclui votações da Câmara dos Deputados.
```

**B. Filtro sem resultados** (ranking/proposicoes com filtros ativos):
```
Nenhum resultado para esses filtros.
[Limpar filtros]  ← botão que reseta todos os estados de filtro
```

**C. Proposição sem votações** (já existe texto, melhorar):
```
Nenhuma votação plenária registrada para esta proposição.
```

**Acceptance criteria:**
- [ ] Cada cenário tem texto distinto e preciso
- [ ] Cenário B tem botão "Limpar filtros" funcional
- [ ] Nenhum empty state menciona detalhes técnicos internos

---

### UI-005 — Unificar linguagem de filtros
**Severidade:** Comportamental
**Problema:** `/proposicoes` usa 3 controles diferentes para a mesma função. `/ranking` tem filtros em linhas arbitrárias.

**Implementação — Proposições:**
- Uma linha: `[Buscar por ementa...] [Tipo ▾] [Ano ▾]`
- Categorias ZIL permanecem como botões acima (alta frequência, valem visibilidade)
- Remover a separação em duas linhas

**Implementação — Ranking:**
- Uma linha: `[Buscar por nome...] [Câmara/Senado ▾] [Estado ▾] [Partido ▾]`
- Segunda linha (separada visualmente com label): `Ordenar: [Maior score ▾]`
- Label `"Ordenar por"` em `font-mono text-2xs text-zil-muted` antes do dropdown

**Acceptance criteria:**
- [ ] `/proposicoes`: filtros em linha única abaixo dos botões de categoria
- [ ] `/ranking`: ordenação separada dos filtros com label
- [ ] Nenhum comportamento de filtro alterado — só layout

---

### UI-006 — Remover decoração tipográfica sem função
**Severidade:** Visual
**Problema:** Letra gigante (`R`, `P`) em `text-6xl text-zil-divider` ocupa espaço sem hierarquizar.

**Implementação:**
- Remover `<span className="font-display text-6xl text-zil-divider">` de `ranking/page.tsx` e `proposicoes/page.tsx`
- O `<h1>` passa a ser o elemento de maior peso visual
- Ajustar margin/padding do header para compensar o espaço removido

**Acceptance criteria:**
- [ ] Nenhuma letra decorativa nas páginas de lista
- [ ] H1 permanece com `font-display uppercase tracking-wide`
- [ ] Espaçamento da seção de header visualmente equilibrado

---

### UI-007 — Unificar sistema de badges
**Severidade:** Visual
**Problema:** 3 linguagens visuais para elementos de classificação (`CategoriaBadge`, `ContextoBadge`, resultado inline).

**Implementação:**
- Criar `components/ui/Badge.tsx` com 3 variantes via prop `variant`:
  - `"category"` — borda colorida, fundo transparente (absorve `CategoriaBadge` ou fica como wrapper)
  - `"status"` — `● label` em mono (absorve `ContextoBadge` pronto)
  - `"result"` — fundo `bg-zil-green/10` ou `bg-zil-orange-light`, sem borda, texto `text-xs font-semibold`
- Substituir o badge de resultado em `proposicoes/[id]/page.tsx` e `votacoes/[id]/page.tsx` por `<Badge variant="result">`
- `CategoriaBadge` e `ContextoBadge` permanecem como wrappers semânticos mas usam `Badge` internamente

**Acceptance criteria:**
- [ ] `Badge.tsx` existe em `components/ui/`
- [ ] Resultado "APROVADO" e "REJEITADO" usam `variant="result"`
- [ ] Nenhuma regressão visual nos badges de categoria existentes

---

### UI-008 — Ementa colapsada por padrão
**Severidade:** Visual
**Problema:** Quando não há `resumo_simples`, o `<details open>` exibe 7 linhas de jargão legal como primeira dobra.

**Implementação:**
- `<details>` nunca abre por padrão (remover `open={!hasContexto}`)
- Label fixo: `"Ver ementa técnica ↓"` em ambos os casos (com e sem resumo)
- Quando não há `hasContexto`, adicionar placeholder antes do `<details>`:
  ```
  Esta proposição ainda não foi analisada pela plataforma.
  A ementa técnica original está disponível abaixo.
  ```
  Em `text-sm text-zil-muted italic`

**Acceptance criteria:**
- [ ] Ementa fechada por padrão em todas as proposições
- [ ] Label do `<summary>` consistente: sempre "Ver ementa técnica ↓"
- [ ] Placeholder visível quando sem análise LLM

---

## Ordem de implementação sugerida

```
UI-006 → UI-002 → UI-001 → UI-003 → UI-008 → UI-005 → UI-004 → UI-007
```

Rationale: começar pelo que remove ruído (006, 002), depois adicionar valor (001, 003), depois refinar (008, 005, 004, 007).

## O que não muda

- Design tokens (`zil-*`) — sistema de cores permanece
- `font-display` uppercase nos títulos — identidade editorial mantida
- Layout geral das páginas — sem reestruturação de rotas ou seções
- Backend/API — zero mudanças de schema ou endpoints

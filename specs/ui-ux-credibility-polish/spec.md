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

---

## Design Critique #2 — Direção esperada e detalhes de proposição
**Data:** 2026-04-02
**Foco:** Como `direcao_esperada` é exibida na UI e oportunidades na página de detalhes de proposição

### UI-009 — DirecaoBadge: componente compartilhado para direção esperada
**Severidade:** Estrutural
**Problema:** `direcao_esperada` aparece em pelo menos 2 superfícies com implementações inline diferentes. O valor técnico ("sim"/"nao") é exposto diretamente; sem link para justificativa metodológica; sem explicação do que "direção esperada" significa.

**Implementação:**
- Criar `components/DirecaoBadge.tsx` com prop `direcao: string | null | undefined`
- Mapear valores técnicos para linguagem editorial:
  - `"sim"` → `FAVORÁVEL` em `text-zil-green`
  - `"nao"` → `CONTRÁRIA` em `text-zil-orange`
  - qualquer outro → retorna `null`
- Estrutura: `<span title="Posição ZIL nesta votação · ver /metodologia">● FAVORÁVEL</span>`
- `null | undefined` → retorna `null` sem renderização
- Substituir os usos inline em `proposicoes/[id]/page.tsx` (linha 284-288) e `votacoes/[id]/page.tsx`

**Acceptance criteria:**
- [ ] `DirecaoBadge.tsx` existe em `components/`
- [ ] Exibe "FAVORÁVEL" para "sim" e "CONTRÁRIA" para "nao" — nunca os valores técnicos brutos
- [ ] `title` referencia /metodologia
- [ ] `null`/`undefined` não renderiza nada
- [ ] `proposicoes/[id]` usa `<DirecaoBadge>` em vez de span inline
- [ ] `votacoes/[id]` usa `<DirecaoBadge>` em vez de span inline

---

### UI-010 — Síntese de posição da plataforma na página de proposição
**Severidade:** Estrutural
**Problema:** A página de proposição lista N votações com `direcao_esperada` individual, mas nunca sintetiza a posição da plataforma sobre a proposição como um todo. O usuário precisa calcular mentalmente. Uma proposição pode ter votações favoráveis e contrárias (ex: votação de substitutivo vs. votação do texto original).

**Implementação:**
- Calcular a partir de `votacoes[]` após carregar:
  - `comDirecao` = votações com `direcao_esperada !== null`
  - `favoraveis` = count com `direcao_esperada === "sim"`
  - `contrarias` = count com `direcao_esperada === "nao"`
- Lógica de síntese:
  - `favoraveis > 0 && contrarias === 0` → `"FAVORÁVEL"`
  - `contrarias > 0 && favoraveis === 0` → `"CONTRÁRIA"`
  - `favoraveis > 0 && contrarias > 0` → `"POSIÇÃO MISTA"`
- Renderizar bloco acima da lista de votações **quando `comDirecao.length > 0`**:
  ```
  [label: "ZIL avalia esta proposição como"]  [valor: FAVORÁVEL]
  [subtext: "com base em N votações monitoradas · ver metodologia →"]
  ```
- Label em `font-mono text-xs text-zil-muted`, valor em `font-display` com cor semântica
- Link `/metodologia` em `font-mono text-xs text-zil-green`

**Acceptance criteria:**
- [ ] Bloco aparece acima da lista quando há votações com `direcao_esperada`
- [ ] Lógica FAVORÁVEL/CONTRÁRIA/MISTA implementada corretamente
- [ ] Conta apenas votações `comDirecao`, não o total
- [ ] Link para /metodologia presente
- [ ] Não aparece quando nenhuma votação tem `direcao_esperada`

---

### UI-011 — `resultado` inferido de votos_sim/votos_nao quando null
**Severidade:** Comportamental
**Problema:** Quando `resultado === null` (frequente em votações de comissão ou sessões antigas), mas `votos_sim` e `votos_nao` estão preenchidos, a linha de votação não mostra nenhuma conclusão. O usuário olha para "429 SIM · 19 NÃO" sem ver "Aprovado".

**Implementação:**
- Em `proposicoes/[id]/page.tsx`, derivar `resultadoDisplay` por votação:
  ```tsx
  const resultadoDisplay =
    v.resultado ??
    (v.votos_sim !== null && v.votos_nao !== null
      ? v.votos_sim > v.votos_nao
        ? "Aprovado*"
        : "Rejeitado*"
      : null);
  const inferido = !v.resultado && resultadoDisplay !== null;
  ```
- Badge com lógica de cor igual ao resultado explícito (verde/laranja)
- Quando `inferido === true`: adicionar `title="Resultado inferido dos votos registrados"` no badge
- O `*` é sufixo visual leve para indicar inferência — não um footnote
- Não alterar a lógica de côr: aprovado → verde, rejeitado → laranja, indiferente → muted

**Acceptance criteria:**
- [ ] Votações sem `resultado` mas com `votos_sim > votos_nao` exibem "Aprovado*" em verde
- [ ] Votações sem `resultado` mas com `votos_sim < votos_nao` exibem "Rejeitado*" em laranja
- [ ] Badge inferido tem `title` explicativo
- [ ] Votações sem `resultado` E sem `votos_sim`/`votos_nao` não exibem badge
- [ ] Resultado explícito da API não é alterado nem marcado com `*`

---

### UI-012 — Unificar padrão de collapse
**Severidade:** Visual
**Problema:** Dois padrões de collapse coexistem na mesma página `proposicoes/[id]`:
1. `<details open={!hasContexto}>` — nativo HTML, sem transição
2. `<button onClick={() => setContextoOpen(v => !v)}>` + conditional render — React state, sem transição

Além de inconsistência visual, o segundo mantém estado `contextoOpen` que pode ser eliminado.

**Implementação:**
- Substituir o accordion de contexto por `<details>/<summary>` nativo:
  ```tsx
  <details className="border border-zil-divider">
    <summary className="px-4 py-3 font-mono text-xs uppercase tracking-wider text-zil-soft cursor-pointer hover:bg-zil-card">
      Ver contexto completo ▼
    </summary>
    <div className="px-4 pb-6 border-t border-zil-divider pt-4 space-y-6">
      {/* conteúdo atual */}
    </div>
  </details>
  ```
- Remover `const [contextoOpen, setContextoOpen] = useState(false)` e o `onClick` handler
- Manter a lógica condicional de renderização do bloco (`contexto && (glossario || leis)`)
- Verificar se `votacoes/[id]/page.tsx` tem padrão similar e unificar também

**Acceptance criteria:**
- [ ] Estado `contextoOpen` removido de `proposicoes/[id]/page.tsx`
- [ ] Accordion de contexto usa `<details>/<summary>` nativo
- [ ] Label `<summary>` visualmente consistente com o `<details>` de ementa na mesma página
- [ ] Funcionalidade preservada — conteúdo visível ao abrir, escondido ao fechar

---

## Ordem de implementação sugerida (completa)

```
UI-006 → UI-002 → UI-001 → UI-003 → UI-008 → UI-005 → UI-004 → UI-007
→ UI-009 → UI-012 → UI-011 → UI-010
```

Rationale do bloco #2: começar pelo componente compartilhado (009), depois simplificar (012), corrigir dados faltantes (011), e por último adicionar a síntese que depende de tudo estar certo (010).

## O que não muda

- Design tokens (`zil-*`) — sistema de cores permanece
- `font-display` uppercase nos títulos — identidade editorial mantida
- Layout geral das páginas — sem reestruturação de rotas ou seções
- Backend/API — zero mudanças de schema ou endpoints

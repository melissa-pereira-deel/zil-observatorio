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

---

## Design Critique #3 — Página do parlamentar: IA, hierarquia e duplo encoding
**Data:** 2026-04-02
**Foco:** Arquitetura da informação, disposição de dados quantitativos, legibilidade, uso semântico de cores

### UI-013 — Hero metric zone: score e síntese como protagonistas visuais
**Severidade:** Estrutural
**Problema:** O `ScoreGauge` é o terceiro elemento num `flex` row (`foto → info → gauge`), tratado com o mesmo peso visual que a foto. A stats bar abaixo exibe 3 números isolados (`alinhados | contra | total`) com tipografia idêntica — o usuário precisa fazer aritmética mental para entender proporção. O dado mais importante da página não tem primazia arquitetural.

**Implementação:**
- Remover `ScoreGauge` do header flex row — o terceiro slot (`<div className="text-center">`) é eliminado
- Substituir o bloco `stats bar` (`flex gap-8 py-4 border-y`) por um **hero metric block** de 2 colunas:

```tsx
{/* Hero Metric Block — substitui stats bar */}
<div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-zil-divider border border-zil-divider mb-10">

  {/* Coluna esquerda: Score */}
  <div className="bg-zil-white px-6 py-5 flex items-center gap-4">
    <ScoreGauge score={parl.score_zil} size="lg" totalVotosZil={votos.length} />
    <div>
      <div className="font-mono text-2xs text-zil-muted uppercase tracking-wider mb-1">
        Score ZIL
      </div>
      <div className="font-display text-3xl text-zil-fg">
        {parl.score_zil !== null ? (parl.score_zil > 0 ? `+${parl.score_zil.toFixed(1)}` : parl.score_zil.toFixed(1)) : "—"}
      </div>
      <div className="font-mono text-2xs text-zil-muted mt-1">
        escala de −10 a +10
      </div>
    </div>
  </div>

  {/* Coluna direita: Proporção de alinhamento */}
  <div className="bg-zil-white px-6 py-5">
    <div className="font-mono text-2xs text-zil-muted uppercase tracking-wider mb-3">
      Alinhamento ZIL
    </div>
    {votos.length > 0 ? (
      <>
        <div className="flex items-baseline gap-2 mb-2">
          <span className="font-display text-2xl text-zil-green">{alinhados}</span>
          <span className="font-mono text-sm text-zil-muted">de {votos.length} votos</span>
          <span className="font-mono text-sm text-zil-soft font-semibold">
            ({Math.round((alinhados / votos.length) * 100)}%)
          </span>
        </div>
        {/* Barra de proporção */}
        <div className="h-2 bg-zil-divider rounded-full overflow-hidden mb-2">
          <div
            className="h-full bg-zil-green rounded-full"
            style={{ width: `${Math.round((alinhados / votos.length) * 100)}%` }}
          />
        </div>
        <div className="font-mono text-2xs text-zil-muted">
          {contra} contra · {votos.length - alinhados - contra} sem direção definida
        </div>
      </>
    ) : (
      <p className="font-mono text-xs text-zil-muted">Nenhuma votação ZIL registrada.</p>
    )}
  </div>
</div>
```

- O `score_atualizado_em` (antes no header) passa para dentro da coluna esquerda do hero block
- `alinhados` e `contra` já são variáveis computadas no componente — reutilizar

**Acceptance criteria:**
- [ ] ScoreGauge removido do header flex row
- [ ] Stats bar (`border-y flex gap-8`) removida
- [ ] Hero metric block renderiza 2 colunas no desktop, empilhado no mobile
- [ ] Score exibido em `text-3xl font-display` — maior peso tipográfico da página
- [ ] Proporção visível sem scroll em viewport 768px+
- [ ] Parlamentares sem score: coluna esquerda mostra "—" (sem crash)
- [ ] Parlamentares sem votos: coluna direita mostra empty state

---

### UI-014 — Legenda do duplo encoding alinhamento/voto
**Severidade:** Estrutural
**Problema:** Cada linha de voto tem 2 indicadores simultâneos com semântica diferente:
- Dot esquerdo (w-2 h-2): `alinhado` boolean — o voto foi na direção esperada pelo ZIL?
- Badge direito: `voto` string — o que o parlamentar realmente votou?

Um parlamentar que votou NÃO numa pauta onde a direção esperada era NÃO aparece com **badge laranja + dot verde** — contradição visual sem explicação. Usuários novos interpretam isso como erro.

**Implementação:**
- Adicionar bloco de legenda imediatamente acima do `border-t` que inicia o histórico:
```tsx
{votos.length > 0 && (
  <div className="flex flex-wrap gap-x-6 gap-y-1 mb-3 pb-3 border-b border-zil-divider">
    <span className="font-mono text-2xs text-zil-muted flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full bg-zil-green inline-block shrink-0" />
      alinhado com ZIL
    </span>
    <span className="font-mono text-2xs text-zil-muted flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full bg-zil-orange inline-block shrink-0" />
      contra a posição ZIL
    </span>
    <span className="font-mono text-2xs text-zil-muted flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-full bg-zil-divider inline-block shrink-0" />
      sem posição definida
    </span>
    <span className="font-mono text-2xs text-zil-muted">
      · badge = voto registrado
    </span>
  </div>
)}
```
- A legenda aparece somente quando `votos.length > 0`
- Não duplicar a legenda quando filtro está ativo (já está visível no topo da lista)

**Acceptance criteria:**
- [ ] Legenda visível imediatamente acima do primeiro item do histórico
- [ ] 3 entradas: alinhado (verde) / contra (laranja) / sem posição (cinza)
- [ ] Nota "badge = voto registrado" presente
- [ ] Legenda não aparece quando lista vazia
- [ ] Legenda persiste quando filtro de categoria está ativo

---

### UI-015 — Affordance de interatividade nos cards de categoria
**Severidade:** Comportamental
**Problema:** Os 6–9 cards do breakdown de categorias são `<button>` clicáveis que filtram o histórico de votos, mas parecem elementos decorativos: sem ícone de ação, sem instrução, sem `title`. O estado ativo (`border-zil-green bg-zil-green/5`) existe, mas o estado idle não sugere interatividade.

**Implementação:**
- Adicionar subtítulo à seção `h2`:
```tsx
<h2 className="font-display text-base uppercase tracking-wide mb-1">
  Participação por pauta
</h2>
<p className="font-mono text-2xs text-zil-muted mb-4">
  Clique em uma pauta para filtrar o histórico abaixo
</p>
```
- Adicionar `title` em cada card: `title={`Filtrar histórico por ${LABEL[cat] ?? cat}`}`
- Quando filtro ativo: substituir "× Limpar filtro" por indicador mais visível:
```tsx
{filtroCategoria && (
  <div className="mt-3 flex items-center gap-2">
    <span className="font-mono text-xs text-zil-soft border border-zil-green/40 px-2 py-0.5 bg-zil-green/5">
      Filtrando: {LABEL[filtroCategoria] ?? filtroCategoria}
    </span>
    <button
      onClick={() => setFiltroCategoria("")}
      className="font-mono text-xs text-zil-muted hover:text-zil-fg"
    >
      × Limpar
    </button>
  </div>
)}
```

**Acceptance criteria:**
- [ ] Subtítulo "Clique em uma pauta para filtrar o histórico abaixo" visível abaixo do `h2`
- [ ] Cada card tem `title` com o nome da categoria
- [ ] Filtro ativo exibe badge "Filtrando: [Categoria]" + botão "× Limpar" separado
- [ ] Nenhum comportamento de filtragem alterado

---

### UI-016 — Consolidar design tokens e mapa de categorias
**Severidade:** Visual
**Problema 1 — Token leak no ScoreGauge:** Scores negativos (-2 a -5 e abaixo de -5) usam 6 classes Tailwind raw: `bg-orange-50 border-orange-300 text-orange-600 bg-red-50 border-red-300 text-red-600`. O resto do design system usa `zil-*` tokens. Essa ruptura acontece no componente de maior carga semântica da plataforma.

**Problema 2 — Dois mapas LABEL divergentes:** `parlamentar/[id]/page.tsx` tem `"ZIL-AGR": "Agro"`. `CategoriaBadge.tsx` tem `"ZIL-AGR": "Agro-Indústria"`. Na mesma tela, a mesma categoria tem dois nomes diferentes.

**Implementação:**

**Fix 1 — ScoreGauge:**
```tsx
// ANTES
if (s >= -5) return { bg: "bg-orange-50", border: "border-orange-300", text: "text-orange-600" };
return { bg: "bg-red-50", border: "border-red-300", text: "text-red-600" };

// DEPOIS
if (s >= -5) return { bg: "bg-zil-orange-light", border: "border-zil-orange", text: "text-zil-orange" };
return { bg: "bg-zil-red/10", border: "border-zil-red", text: "text-zil-red" };
```

**Fix 2 — Criar `apps/web/lib/categorias.ts`:**
```ts
export const CATEGORIA_LABELS: Record<string, string> = {
  "ZIL-FER": "Fertilizantes",
  "ZIL-MIN": "Minerais",
  "ZIL-SEM": "Semicondutores",
  "ZIL-ENE": "Energia",
  "ZIL-DIG": "Digital",
  "ZIL-DEF": "Defesa",
  "ZIL-EDU": "Educação",
  "ZIL-AGR": "Agro-Indústria",
  "ZIL-COM": "Comércio",
};
```
- Remover `LABEL` de `parlamentar/[id]/page.tsx`, importar `CATEGORIA_LABELS`
- Remover `LABELS` de `CategoriaBadge.tsx`, importar `CATEGORIA_LABELS`

**Acceptance criteria:**
- [ ] ScoreGauge não usa nenhuma classe Tailwind raw de cor (orange-*, red-*)
- [ ] Scores entre -2 e -5 renderizam com `text-zil-orange`
- [ ] Scores abaixo de -5 renderizam com `text-zil-red`
- [ ] `lib/categorias.ts` existe e exporta `CATEGORIA_LABELS`
- [ ] `CategoriaBadge.tsx` importa de `lib/categorias.ts`
- [ ] `parlamentar/[id]/page.tsx` importa de `lib/categorias.ts`
- [ ] "Agro-Indústria" consistente em todos os contextos

---

### UI-017 — Scope e navegação no histórico de votos
**Severidade:** Comportamental
**Problema 1 — Scope invisível:** O título "Histórico de votos em pautas ZIL" não informa quantas votações existem. O usuário começa a rolar sem saber se vai ver 4 ou 400 linhas. A contagem existe na stats bar, mas após UI-013 ela migra para o hero block — desconectada da lista.

**Problema 2 — Back link hardcoded:** `"← Voltar ao ranking"` é hardcoded mesmo quando o usuário chegou via link de votação ou proposição. Cria navegação mentirosa.

**Implementação:**

```tsx
{/* Cabeçalho do histórico com contagem */}
<div className="flex items-baseline justify-between mb-4">
  <h2 className="font-display text-base uppercase tracking-wide">
    Histórico de votos em pautas ZIL
    {filtroCategoria && (
      <span className="font-mono text-xs text-zil-muted normal-case tracking-normal ml-2">
        — {CATEGORIA_LABELS[filtroCategoria] ?? filtroCategoria}
      </span>
    )}
  </h2>
  <span className="font-mono text-xs text-zil-muted">
    {filtroCategoria
      ? `${votosFiltrados.length} de ${votos.length}`
      : votos.length}{" "}
    votações
  </span>
</div>
```

**Back link — usar `router.back()` com fallback:**
```tsx
import { useRouter } from "next/navigation";

const router = useRouter();

// No lugar do Link hardcoded:
<button
  onClick={() => router.back()}
  className="font-mono text-xs text-zil-muted hover:text-zil-green mb-8 inline-block"
>
  ← Voltar
</button>
```

**Acceptance criteria:**
- [ ] Título do histórico sempre mostra contagem à direita: "N votações"
- [ ] Quando filtro ativo: "N de Y votações"
- [ ] Contagem atualiza em tempo real ao mudar filtro de categoria
- [ ] Back link usa `router.back()` — sem texto hardcoded de destino
- [ ] Se não houver histórico de navegação, o botão ainda funciona (comportamento nativo de `router.back()`)

---

## Ordem de implementação sugerida (completa)

```
UI-006 → UI-002 → UI-001 → UI-003 → UI-008 → UI-005 → UI-004 → UI-007
→ UI-009 → UI-012 → UI-011 → UI-010
→ UI-016 → UI-013 → UI-017 → UI-014 → UI-015
```

Rationale do bloco #3: corrigir tokens primeiro (016 — sem risco), depois a reestruturação arquitetural (013), depois scope e navegação (017 — depende de 013 absorver a stats bar), depois as camadas explicativas (014, 015 — dependem da lista estar estabilizada).

---

## Design Critique #4 — Perfil do parlamentar: redundância e clareza
**Data:** 2026-04-04
**Foco:** Score duplicado, contagens redundantes, legenda críptica, código interno visível, ausência de síntese interpretativa

### UI-018 — Eliminar score duplicado no hero: frase interpretativa em vez de `text-4xl`
**Severidade:** Estrutural
**Problema:** O valor "+10.0" aparece 3 vezes na primeira dobra: (1) dentro do ScoreGauge circular (`text-2xl`), (2) como texto `text-4xl font-display` ao lado, e (3) implicitamente no label "com base em N votos". O gauge circular já é o indicador canônico — o `text-4xl` é redundância pura que compete em vez de complementar. O espaço poderia comunicar algo que o gauge não diz: uma interpretação textual do alinhamento.

**Solução:**
- Remover o `<div className="font-display text-4xl">` que exibe o score numérico ao lado do gauge
- No lugar, renderizar uma **frase interpretativa** baseada no valor do score:

```tsx
function getScoreLabel(score: number | null): string {
  if (score === null) return "Sem dados suficientes";
  if (score >= 8) return "Alinhamento total";
  if (score >= 4) return "Majoritariamente alinhado";
  if (score >= 1) return "Parcialmente alinhado";
  if (score >= -1) return "Posição neutra";
  if (score >= -4) return "Parcialmente contrário";
  if (score >= -8) return "Majoritariamente contrário";
  return "Posição contrária";
}
```

- A frase fica em `font-display text-lg text-zil-fg` (menor que o antigo `text-4xl`, maior que o contexto)
- O label "SCORE ZIL" e "escala de −10 a +10" permanecem como contexto
- A data de atualização permanece

**Layout resultante da coluna esquerda:**
```tsx
<div className="bg-zil-white px-6 py-5 flex items-center gap-5">
  <ScoreGauge score={parl.score_zil} size="lg" totalVotosZil={votos.length} />
  <div>
    <div className="font-mono text-2xs text-zil-muted uppercase tracking-wider mb-1">
      Score ZIL
    </div>
    <div className="font-display text-lg text-zil-fg leading-snug mb-1">
      {getScoreLabel(parl.score_zil)}
    </div>
    <div className="font-mono text-2xs text-zil-muted">
      escala de −10 a +10
    </div>
    {parl.score_atualizado_em && (
      <div className="font-mono text-2xs text-zil-muted opacity-60 mt-1">
        atualizado {new Date(parl.score_atualizado_em).toLocaleDateString("pt-BR")}
      </div>
    )}
  </div>
</div>
```

**Acceptance criteria:**
- [ ] Score numérico `text-4xl` removido da coluna esquerda do hero
- [ ] Frase interpretativa renderizada em `font-display text-lg`
- [ ] ScoreGauge circular (lg) permanece como indicador visual canônico com número
- [ ] 7 faixas de interpretação cobrindo -10 a +10
- [ ] Score null renderiza "Sem dados suficientes"
- [ ] Zero mudança no ScoreGauge component — alteração apenas no page

---

### UI-019 — Consolidar contagem de votos num único local
**Severidade:** Estrutural
**Problema:** A contagem de votos aparece em 2 lugares próximos: (1) "com base em 4 votos" abaixo do ScoreGauge na coluna esquerda, e (2) "4 de 4 votos (100%)" na coluna direita (Alinhamento ZIL). São dados diferentes (base de cálculo vs. rate de alinhamento), mas a linguagem similar e a proximidade criam confusão.

**Solução:**
- Suprimir o label "com base em N votos" do ScoreGauge **quando usado no hero metric block** (size="lg")
- A contagem de votos fica **exclusivamente** na coluna de Alinhamento ZIL ("4 de 4 votos")
- O ScoreGauge em `size="lg"` no hero **não** renderiza o sub-label
- O ScoreGauge em outros contextos (ranking cards, etc.) continua com o label

**Implementação:**
- Adicionar prop `hideVotosLabel?: boolean` ao ScoreGauge
- No hero: `<ScoreGauge score={parl.score_zil} size="lg" totalVotosZil={votos.length} hideVotosLabel />`
- No componente ScoreGauge, condicionar a renderização:
```tsx
{size !== "sm" && totalVotosZil != null && totalVotosZil > 0 && !hideVotosLabel && (
  <span className="font-mono text-2xs text-zil-muted text-center">
    com base em {totalVotosZil} votos
  </span>
)}
```

**Acceptance criteria:**
- [ ] Hero metric block: ScoreGauge lg não mostra "com base em N votos"
- [ ] Coluna de Alinhamento ZIL permanece como único local com contagem
- [ ] ScoreGauge em `ParlamentarCard` (sm) e ranking preview continua sem mudança
- [ ] Prop `hideVotosLabel` tem default `false` — backward-compatible

---

### UI-020 — Legenda com exemplo visual em vez de "badge = voto registrado"
**Severidade:** Comportamental
**Problema:** Na legenda do duplo encoding, a última entrada diz "· badge = voto registrado". A palavra "badge" é jargão de UI/design que o cidadão não entende. Não há referência visual para o que seria esse "badge" — o usuário precisa deduzir que se refere ao chip "SIM"/"NÃO" à direita de cada votação.

**Solução:**
- Substituir o texto "badge = voto registrado" por um **mini exemplo visual** do badge real, seguido de "= voto registrado"
- Renderizar um chip estilizado idêntico ao usado na lista de votos (mas em miniatura):

```tsx
<span className="font-mono text-2xs text-zil-muted flex items-center gap-1.5">
  <span className="font-mono text-2xs px-1.5 py-0.5 bg-zil-green/10 text-zil-green rounded-sm">
    SIM
  </span>
  = voto registrado
</span>
```

- O mini badge usa os mesmos tokens do badge real (`bg-zil-green/10 text-zil-green rounded-sm`), apenas com `text-2xs` e padding menor

**Acceptance criteria:**
- [ ] Texto "badge = voto registrado" removido
- [ ] Mini badge visual "SIM" renderizado na legenda com mesmos tokens de cor
- [ ] Texto "= voto registrado" segue o mini badge
- [ ] Legenda continua em uma única linha fluida no desktop
- [ ] Responsivo: no mobile, wraps naturalmente sem quebra

---

### UI-021 — Remover código interno "ZIL-ENE" dos cards de categoria
**Severidade:** Visual
**Problema:** Os cards de "Participação por pauta" exibem o código técnico "ZIL-ENE" em `text-xs text-zil-muted` acima do nome legível "Energia". Esse identificador é interno da plataforma e não agrega valor para o cidadão. Ocupa espaço vertical, adiciona ruído visual e expõe nomenclatura de sistema.

**Solução:**
- Remover o `<div>` que exibe `{cat}` (o código bruto) do corpo visível do card
- Mover o código para o atributo `title` do botão (já existe parcialmente)
- O card exibe apenas o nome legível da categoria

**De:**
```tsx
<div className="font-mono text-xs text-zil-muted mb-1">{cat}</div>
<div className="font-display text-sm text-zil-fg">
  {CATEGORIA_LABELS[cat] ?? cat}
</div>
```

**Para:**
```tsx
<div className="font-display text-sm text-zil-fg">
  {CATEGORIA_LABELS[cat] ?? cat}
</div>
```

- O `title` do `<button>` já contém o nome legível; atualizar para incluir o código como referência técnica:
  `title={`${cat} — Filtrar histórico por ${CATEGORIA_LABELS[cat] ?? cat}`}`

**Acceptance criteria:**
- [ ] Código "ZIL-ENE", "ZIL-SEM", etc. não aparece visível nos cards
- [ ] Nome legível ("Energia", "Semicondutores") é o único texto de label
- [ ] Código técnico acessível via `title` attribute no hover
- [ ] Cards visualmente mais limpos — uma linha a menos de texto por card

---

### UI-022 — Frase de síntese interpretativa acima do hero metric
**Severidade:** Estrutural
**Problema:** O cidadão chega nessa página com uma pergunta: "Meu deputado vota a favor da soberania industrial?" A resposta está fragmentada em 3 widgets (gauge, texto numérico, barra de proporção). Em nenhum lugar aparece uma **frase direta** que responda à pergunta. O usuário precisa reconstruí-la mentalmente.

**Solução:**
- Adicionar uma frase de síntese entre o header do parlamentar e o hero metric block
- A frase é gerada a partir dos dados já disponíveis (`alinhados`, `votos.length`, `score_zil`)

```tsx
function getSynthesis(alinhados: number, total: number, score: number | null): string | null {
  if (total === 0) return null;
  const pct = Math.round((alinhados / total) * 100);
  if (pct === 100) return `Votou a favor da soberania industrial em todas as ${total} pautas monitoradas.`;
  if (pct >= 75) return `Votou a favor da soberania industrial na maioria das pautas monitoradas (${alinhados} de ${total}).`;
  if (pct >= 50) return `Votou a favor da soberania industrial em ${alinhados} de ${total} pautas monitoradas.`;
  if (pct >= 25) return `Votou contra a posição de soberania industrial na maioria das pautas monitoradas (${total - alinhados} de ${total}).`;
  if (pct > 0) return `Votou contra a posição de soberania industrial em quase todas as pautas monitoradas (${total - alinhados} de ${total}).`;
  return `Votou contra a posição de soberania industrial em todas as ${total} pautas monitoradas.`;
}
```

- Renderizar entre o header e o hero metric block:
```tsx
{synthesis && (
  <p className="font-body text-base text-zil-soft mb-6 max-w-xl">
    {synthesis}
  </p>
)}
```

- Tipografia: `font-body text-base text-zil-soft` — não compite com o h1 (`font-display text-2xl`), mas é legível e direto
- `max-w-xl` evita que a frase estique em telas largas

**Acceptance criteria:**
- [ ] Frase visível entre header e hero metric block
- [ ] 6 variações cobrindo 0%, 1-24%, 25-49%, 50-74%, 75-99%, 100%
- [ ] Quando `votos.length === 0`: frase não renderizada (null)
- [ ] Texto usa números absolutos ("3 de 4") — não percentuais isolados
- [ ] Linguagem neutra e apartidária: "votou a favor" / "votou contra a posição de soberania"
- [ ] `max-w-xl` limita largura da frase

---

## Ordem de implementação sugerida (completa, incluindo bloco #4)

```
UI-006 → UI-002 → UI-001 → UI-003 → UI-008 → UI-005 → UI-004 → UI-007
→ UI-009 → UI-012 → UI-011 → UI-010
→ UI-016 → UI-013 → UI-017 → UI-014 → UI-015
→ UI-021 → UI-019 → UI-018 → UI-020 → UI-022
```

Rationale do bloco #4: começar pela remoção de ruído visual (021 — sem risco), depois consolidar contagem (019 — altera prop do ScoreGauge), depois substituir o score duplicado pela frase interpretativa (018 — depende de 019 ter removido o label), depois a legenda visual (020 — independente), e por último a síntese que é a cereja do bolo (022 — depende de tudo estar estabilizado).

## O que não muda

- Design tokens (`zil-*`) — sistema de cores permanece
- `font-display` uppercase nos títulos — identidade editorial mantida
- Layout geral das páginas — sem reestruturação de rotas ou seções
- Backend/API — zero mudanças de schema ou endpoints
- ScoreGauge circular — permanece como indicador visual canônico (número + cor)
- Coluna de Alinhamento ZIL — layout e progress bar inalterados

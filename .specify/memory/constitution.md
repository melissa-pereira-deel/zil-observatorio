<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 (uninitialized) → 1.0.0
Bump rationale: MAJOR — first complete constitution, replacing empty template.

Principles defined (new):
  I.   Dados Públicos, Acesso Livre
  II.  Apartidário por Design
  III. Transparência Radical e Auditabilidade
  IV.  Projeto de Estado, não de Governo
  V.   Design System e Componentes Reutilizáveis
  VI.  API-First e Open Source
  VII. Qualidade sem Gatekeeping

Sections added:
  - Core Principles (7 principles)
  - Stack & Constraints
  - Development Workflow
  - Governance

Templates status:
  ✅ .specify/templates/plan-template.md — Constitution Check section references these principles; no structural update required
  ✅ .specify/templates/spec-template.md — Functional Requirements align with FR patterns defined here; no update required
  ✅ .specify/templates/tasks-template.md — Task phases align with monorepo structure defined here; no update required

Deferred TODOs:
  - RATIFICATION_DATE: set to project start date 2026-03-31 (first commit date inferred from git log)
-->

# ZIL Observatório Constitution

## Core Principles

### I. Dados Públicos, Acesso Livre

Todo dado produzido pela plataforma — rankings, scores, votações, proposições,
histórico de classificações — DEVE ser acessível sem autenticação.
Autenticação é exigida APENAS para ações participativas: votar em deliberações,
cobrar parlamentares, configurar alertas, propor reclassificações.
Paywall, login obrigatório para leitura ou qualquer forma de bloqueio de acesso
a dados derivados de fontes públicas são PROIBIDOS por princípio.

**Rationale**: O ZIL é infraestrutura cívica. A credibilidade depende de
transparência irrestrita. Cidadãos, jornalistas e pesquisadores DEVEM poder
auditar sem fricção.

### II. Apartidário por Design

A plataforma NÃO endossa partidos, candidatos, coligações ou ideologias. O
critério único de avaliação é alinhamento com soberania industrial brasileira,
definido por metodologia pública e contestável.
A paleta visual usa verde e dourado (cores nacionais). A linguagem DEVE evitar
termos carregados ("esquerda", "direita", "progressista", "conservador").
Toda feature que implique posicionamento editorial DEVE passar pelo comitê
editorial antes de ir a produção.

**Rationale**: O agricultor conservador e o sindicalista progressista
concordam que importar 87% dos fertilizantes é absurdo. A convergência
só é possível se a plataforma for percebida como neutra metodologicamente.

### III. Transparência Radical e Auditabilidade

Toda classificação de proposição DEVE registrar: método utilizado (automático /
NLP / curadoria humana), confiança, justificativa, e histórico de alterações.
O algoritmo de scoring DEVE ser documentado publicamente com fórmula,
parâmetros de peso e exemplos calculados.
Qualquer cidadão DEVE poder contestar uma classificação com justificativa ≥ 100
caracteres. Contestações DEVEM ter resposta pública do comitê editorial.
Nenhuma decisão editorial é tomada sem registro público auditável.

**Rationale**: Legitimidade vem de transparência. A plataforma não diz
"esse político é ruim" — diz "esse político votou X vezes contra processamento
local de minerais". A diferença é o dado auditável.

### IV. Projeto de Estado, não de Governo

Nenhuma feature, taxonomia ou marco estratégico DEVE ser descontinuado por
mudança de governo ou ciclo eleitoral.
Marcos estratégicos (Bússola ZIL) DEVEM ter métricas verificáveis de fontes
oficiais independentes (ANM, ANATEL, TSE, IBGE).
O Índice de Continuidade DEVE medir quanto cada governo manteve, expandiu ou
desmontou programas estratégicos anteriores.
Compromisos registrados por parlamentares são imutáveis via hash SHA-256 —
NÃO podem ser editados retroativamente.

**Rationale**: O Brasil tem déficit de continuidade, não de planos. A
plataforma é a infraestrutura que torna a descontinuidade politicamente custosa.

### V. Design System e Componentes Reutilizáveis

Todo elemento de UI DEVE ser construído a partir dos tokens do design system
definidos em `apps/web/tailwind.config.js` e `apps/web/app/globals.css`.
Componentes de UI genéricos (Button, Badge, Card, Callout, SectionHeader) DEVEM
residir em `apps/web/components/ui/` e ser reutilizados por todas as features.
Inline styles são PROIBIDOS em novos componentes — usar exclusivamente classes
Tailwind com tokens `zil-*`.
Novos tokens de cor, tipografia ou animação DEVEM ser adicionados ao
`tailwind.config.js` antes de serem usados em componentes.
Branding (fontes Archivo Black / Archivo / IBM Plex Mono, paleta verde-dourado,
skew decorativo) DEVE ser preservado em todas as superfícies.

**Rationale**: Escalabilidade visual. A plataforma cresce para múltiplas
páginas, features e contribuidores — inconsistência de design destrói
credibilidade em plataformas cívicas.

### VI. API-First e Open Source

Toda funcionalidade DEVE ser acessível via API REST antes de ter interface
gráfica. A API DEVE ser documentada via OpenAPI/Swagger auto-gerado pelo
FastAPI.
O código DEVE ser licenciado AGPL-3.0. Dados derivados DEVEM ser licenciados
CC BY-SA 4.0.
A plataforma DEVE funcionar razoavelmente com conexões instáveis (cache
agressivo, SSR para conteúdo crítico, PWA offline-tolerant).
Workers de ingestão DEVEM ser idempotentes — re-executar não DEVE criar
duplicatas nem corromper dados existentes.
Toda ingestão DEVE registrar fonte, timestamp e método de obtenção.

**Rationale**: API-first garante que jornalistas e pesquisadores possam usar os
dados independentemente da interface. Open source garante que forks permaneçam
abertos (AGPL network use clause).

### VII. Qualidade sem Gatekeeping

Testes são OBRIGATÓRIOS para: scoring engine, classificador NLP, e endpoints
críticos da API (`/parlamentares`, `/votacoes`, `/stats`).
Para features de UI e workers de ingestão, testes são RECOMENDADOS mas não
bloqueantes para merge.
Type checking (mypy strict para Python, TypeScript strict para Next.js) DEVE
passar no CI antes de qualquer merge para `main`.
Linting (ruff para Python, ESLint para TypeScript) DEVE passar no CI.
PRs de features DEVEM ter aprovação de pelo menos 1 maintainer.
PRs de correção de dados ou classificação DEVEM ter aprovação do comitê
editorial.

**Rationale**: Qualidade sem gatekeeping excessivo. O ZIL é open source e
precisa de contribuidores — barreiras muito altas afastam a comunidade. Mas
erros no scoring ou na classificação têm impacto político real.

---

## Stack & Constraints

**Monorepo structure**:
```
apps/web/        — Next.js 14 + React 18 + Tailwind CSS + TypeScript
apps/api/        — FastAPI (Python 3.12) + SQLAlchemy 2 + Pydantic 2
apps/workers/    — Celery 5 + Redis (crawlers, classificadores, scoring)
packages/        — bibliotecas reutilizáveis (camara_client, etc.)
data/taxonomia/  — definições YAML das 9 categorias ZIL
docs/            — PRD, ARCHITECTURE, MANIFESTO, GOVERNANCE
```

**Data stores**:
- PostgreSQL 16 — dados primários (parlamentares, proposições, votos, scores)
- Redis 7 — cache, filas Celery, rate limiting
- Typesense 27.1 — busca full-text com facets e tolerância a typos

**Key constraints**:
- Score ZIL: fórmula `(Σ alinhamento_i × peso_i) / (Σ |peso_i|) × 10`, range -10.0 a +10.0
- Latência máxima dado → plataforma: 24 horas
- Parlamentares cobertos v1.0: 594 (513 deputados + 81 senadores)
- Marco crítico: plataforma funcional antes de outubro de 2026 (eleições)
- Financiamento: NUNCA de partidos políticos, empresas com lobby, ou governos estrangeiros

**9 categorias ZIL (imutáveis sem RFC)**:
ZIL-FER, ZIL-MIN, ZIL-SEM, ZIL-ENE, ZIL-DIG, ZIL-DEF, ZIL-EDU, ZIL-AGR, ZIL-COM

---

## Development Workflow

**Branches**: `main` (produção), feature branches nomeadas `###-feature-name`
(numeração sequencial via Specify).

**CI gates** (obrigatórios para merge em `main`):
1. `mypy --strict` no `apps/api/`
2. `ruff check` no `apps/api/` e `apps/workers/`
3. `tsc --noEmit` no `apps/web/`
4. `eslint` no `apps/web/`
5. `pytest` — testes de scoring engine e classificador DEVEM passar
6. `next build` no `apps/web/` — build DEVE ser bem-sucedido

**Spec-driven development** (via Specify Kit):
1. `/speckit.constitution` — princípios (este arquivo)
2. `/speckit.specify` — spec da feature (user stories + acceptance criteria)
3. `/speckit.plan` — plano técnico (research + data model + contracts)
4. `/speckit.tasks` — tasks acionáveis organizadas por user story
5. `/speckit.implement` — execução

**Commit convention**: `type: description` onde type ∈
{feat, fix, docs, refactor, test, chore, data}.

**Data editorial decisions** (classificações, direção esperada de votações)
DEVEM ser registradas em `data/taxonomia/` como YAML versionado, com
justificativa e data de decisão.

---

## Governance

Esta constituição SUPERSEDE todas as outras práticas e convenções do projeto.
Em caso de conflito entre um PR e a constituição, a constituição prevalece.

**Amendamentos**:
- PATCH (clarificações, typos): aprovação de 1 maintainer
- MINOR (novo princípio ou seção): RFC pública por ≥ 7 dias + aprovação de 2
  maintainers
- MAJOR (remoção ou redefinição de princípio): RFC pública por ≥ 14 dias +
  aprovação de 3 maintainers + registro de impacto em features existentes

**Papéis**:
- **Maintainers** (máx. 5, mandato 12 meses): merge de PRs, arquitetura,
  releases, prioridades de backlog
- **Comitê Editorial** (máx. 9, mandato 12 meses): classificações,
  direção esperada de votações, contestações, novos marcos da Bússola

**Compliance review**: Todo PR de feature DEVE incluir um checklist verificando
os princípios I–VII. PRs que violem qualquer princípio sem justificativa
documentada na seção "Complexity Tracking" do plano DEVEM ser bloqueados.

---

### Nota de realidade operacional — 2026-09-17

**Nota factual, não normativa. Nenhuma regra foi alterada, nenhuma permissão foi
criada.** Registrada como PATCH ("clarificações", acima). Ela existe porque uma
constituição que descreve órgãos inexistentes deixa de ser norma e passa a ser
representação falsa.

Fatos apurados no repositório em 2026-09-17:

1. **O projeto tem um único maintainer desde a ratificação (2026-03-31).** A
   identidade `ZIL Observatório <zil@zilobservatorio.org>` no histórico git é a
   conta institucional da mesma pessoa, não um segundo membro.
2. **Nenhum PR (#1–#13) teve aprovação formal registrada.** As regras de
   aprovação em "Development Workflow" — 1 maintainer para features, comitê
   editorial para dados e classificação — não foram cumpridas em nenhuma
   ocasião. O "Comitê Editorial" previsto em **Papéis** nunca foi constituído.
3. **Emendas MINOR e MAJOR são inexequíveis** enquanto durar essa condição:
   exigem 2 e 3 maintainers, respectivamente. Isso está registrado, não
   contornado — nenhuma tentativa foi feita de reduzir esses números, o que
   exigiria justamente o quórum ausente.
4. **"Parlamentares cobertos v1.0: 594"** (em *Key constraints*) descreve um
   produto que o projeto deixou de perseguir. O
   [ADR-004](../../docs/decisions/004-placar-focado.md) trocou abrangência por
   profundidade: a v1 passa a ser um placar de ~10 votações. A restrição não é
   alterada aqui — alterá-la é MINOR e exige quórum inexistente —, mas fica
   registrado que **não é mais o alvo**.
5. **Princípios descumpridos pela mesma causa** (documento à frente do mundo),
   enquanto o repositório for privado e a plataforma não estiver no ar:
   - **I. Dados Públicos, Acesso Livre** — não há acesso público a nada hoje
   - **III. Transparência Radical e Auditabilidade** — o histórico é íntegro,
     mas não é auditável por terceiros sem acesso de leitura
   - **VI. API-First e Open Source** — a licença é AGPL-3.0, mas o código não
     está publicado
5. **O mandato de 12 meses** previsto em **Papéis** expira em 2027-03-31 sem
   órgão capaz de renová-lo.

Registrar apenas o item 2 seria confissão seletiva: a causa dos itens 2 a 5 é a
mesma. Abrir o repositório sanaria os três descumprimentos do item 4 num único
ato.

Detalhamento e protocolo aplicável: [`docs/GOVERNANCE.md`](../../docs/GOVERNANCE.md),
seção "Estado atual da governança".

**Version**: 1.0.2 | **Ratified**: 2026-03-31 | **Last Amended**: 2026-09-18
<!-- 1.0.1 (PATCH): nota de realidade operacional. Nenhuma regra alterada. -->

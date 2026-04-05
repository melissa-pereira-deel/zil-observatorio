# ZIL Observatório — Development Guidelines

**Última atualização:** 2026-04-02
**Fase atual:** v1 — Dashboard Público (sem login)
**Roadmap:** [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Stack ativo

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2 |
| Workers | Celery 5, Redis 7, httpx 0.27 |
| Frontend | Next.js 14, TypeScript 5, Tailwind CSS, React 18 |
| Testes | pytest 8 (98 testes, todos passando) |
| Linting | ruff (Python), ESLint (TypeScript) |

---

## Estrutura do projeto

```
apps/api/          FastAPI + SQLAlchemy models + Pydantic schemas + routers
apps/workers/      Celery tasks + crawlers (camara.py ✅, senado.py backlog)
                   + scoring engine + keyword classifier
apps/web/          Next.js 14 (App Router) + componentes UI
packages/          camara_client ✅ | senado_client (backlog)
data/taxonomia/    categorias.yml — keywords das 9 categorias ZIL
data/direcoes/     direcao_esperada por votação (backlog, workflow editorial)
data/bussula/      indicadores estratégicos (backlog)
scripts/           apply_direcoes.py | sync_votacoes_zil.py | discover_proposicoes.py | sync_votacoes_proposicoes.py | sync_pipeline.py | recalcular_scores.py (backlog)
tests/             unit/ integration/ contract/
specs/             Specify Kit specs por feature
docs/              PRD, ARCHITECTURE, GOVERNANCE, ROADMAP, CHANGELOG
```

---

## Comandos

```bash
# Backend (rodar da raiz)
python -m pytest tests/          # 151 testes
ruff check apps/ packages/       # lint Python

# Frontend
cd apps/web
npm run dev                      # dev server
npm run build                    # build produção
npx tsc --noEmit                 # type check

# Workers (requer Redis)
celery -A apps.workers.tasks worker --loglevel=info
celery -A apps.workers.tasks beat --loglevel=info

# Docker (ambiente completo)
docker-compose up

# Pipeline de dados editorial (rodar na ordem, da raiz)
python3 scripts/migrate_enrichment.py       # migração: novos campos Feature 002 (idempotente)
python3 scripts/sync_votacoes_zil.py        # sync só votações ZIL definidas nos YAMLs
python3 scripts/apply_direcoes.py           # aplica direcao_esperada + peso + recalcula scores

# Sync de votações por proposição (busca votações na API da Câmara para cada proposição)
python3 scripts/sync_votacoes_proposicoes.py --dry-run             # preview sem gravar
python3 scripts/sync_votacoes_proposicoes.py                       # sync completo (pula proposições com votos)
python3 scripts/sync_votacoes_proposicoes.py --no-skip             # sync forçado (inclui todas)
python3 scripts/sync_votacoes_proposicoes.py --proposicao-id UUID  # sync de uma proposição específica

# Pipeline orquestrado (roda os 4 passos em sequência)
python3 scripts/sync_pipeline.py                                   # discovery → votações → enrichment → scores
python3 scripts/sync_pipeline.py --dry-run                         # preview completo
python3 scripts/sync_pipeline.py --skip-enrichment --skip-scores   # só discovery + votações
python3 scripts/sync_pipeline.py --skip-discovery --skip-votacoes  # só enrichment + scores

# Descoberta de proposições (busca na API da Câmara por keywords ZIL)
python3 scripts/discover_proposicoes.py --dry-run              # apenas mostra o que seria descoberto
python3 scripts/discover_proposicoes.py --enriquecer           # persiste + marca para enriquecimento
python3 scripts/discover_proposicoes.py --ano-inicio 2020      # janela temporal customizada
python3 -c "
import sys; sys.path.insert(0,'apps/api'); sys.path.insert(0,'.')
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.config import settings
from apps.workers.scoring import recalcular_todos_scores
engine = create_engine(settings.DATABASE_URL)
with Session(engine) as db: print(recalcular_todos_scores(db), 'scores calculados')
"
# Ou, se Celery estiver rodando:
# celery -A apps.workers.tasks call apps.workers.tasks.task_recalcular_scores
```

---

## Regras de código

### Python

- Imports curtos: `from models import Parlamentar` (não `from apps.api.models import`)
  — evita duplo registro de tabelas no SQLAlchemy (ADR-002)
- Tipos cross-DB: usar `JSON`, `Uuid` (não `JSONB`, `ARRAY`, `UUID` do PostgreSQL)
  — testes rodam em SQLite in-memory (ADR-001)
- `JSON(none_as_null=True)` em colunas filtradas com `IS NOT NULL` (ADR-003)
- Workers que importam de `apps/api`: adicionar `apps/api` ao `sys.path` explicitamente

### TypeScript / React

- Inline styles: **proibidos**. Usar exclusivamente classes Tailwind com tokens `zil-*`
- Componentes genéricos (Button, Badge, Card) em `components/ui/` — reutilizar, não recriar
- Novos tokens de cor/tipografia: adicionar em `tailwind.config.js` antes de usar

### Geral

- Não adicionar features além do solicitado
- Não mockar banco em testes de integração — usar SQLite in-memory via conftest.py
- PRs de dados editoriais (`data/`) requerem 2 aprovações de maintainers

---

## Escopo v1 (o que construir agora)

| # | Feature | Status |
|---|---------|--------|
| 001 | Ingestão Câmara + scoring + API | ✅ concluído |
| 002 | Pipeline de enriquecimento legislativo (LLM + Planalto) | ✅ concluído |
| 003 | Workflow editorial via código (YAML + scripts) | backlog |
| 004 | Frontend: /ranking com dados reais | ✅ concluído |
| 005 | Frontend: /parlamentar/[id] | ✅ concluído |
| 006 | Frontend: /proposicoes | ✅ concluído |
| 007 | Frontend: /bussula | backlog |
| 008 | Frontend: /metodologia | backlog |
| 009 | CI/CD (GitHub Actions) | backlog |
| 010 | Deploy produção | backlog |

### UI/UX — Melhorias de credibilidade e usabilidade (design critique 2026-04-02)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-001 | Score com âncora de credibilidade — tooltip no gauge com "baseado em N votos · ver metodologia →" | Estrutural | `ScoreGauge.tsx`, `ranking/page.tsx`, `parlamentar/[id]/page.tsx` |
| UI-002 | Remover "Contexto pendente" da UI pública — badge só aparece quando `pronto` | Estrutural | `ContextoBadge.tsx` |
| UI-003 | Contagem de resultados acima da lista — escopo visível antes de rolar | Comportamental | `ranking/page.tsx`, `proposicoes/page.tsx` |
| UI-004 | Empty states significativos — explicar ausência de dados vs. limitação de cobertura | Comportamental | `parlamentar/[id]/page.tsx`, `proposicoes/page.tsx`, `ranking/page.tsx` |
| UI-005 | Unificar linguagem de filtros — busca textual na mesma linha dos dropdowns; ordenação separada de filtros | Comportamental | `proposicoes/page.tsx`, `ranking/page.tsx` |
| UI-006 | Remover decoração tipográfica sem função — letra gigante (R, P) nos títulos de seção | Visual | `ranking/page.tsx`, `proposicoes/page.tsx` |
| UI-007 | Unificar sistema de badges — `Badge.tsx` com variantes `category`, `status`, `result` | Visual | `components/ui/Badge.tsx` (novo), `/[id]/page.tsx` |
| UI-008 | Ementa colapsada por padrão — primeira dobra sem jargão legal quando não há resumo_simples | Visual | `proposicoes/[id]/page.tsx` |

### UI/UX — Direção esperada e detalhes de proposição (design critique 2026-04-02 #2)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-009 | `DirecaoBadge` — componente compartilhado para `direcao_esperada`; exibe FAVORÁVEL/CONTRÁRIA com link para /metodologia | Estrutural | `components/DirecaoBadge.tsx` (novo), `proposicoes/[id]/page.tsx`, `votacoes/[id]/page.tsx` |
| UI-010 | Síntese de posição ZIL na proposição — "ZIL avalia: FAVORÁVEL · com base em N votações" acima da lista de votações | Estrutural | `proposicoes/[id]/page.tsx` |
| UI-011 | `resultado` inferido de `votos_sim/votos_nao` quando null — badge com `*` + `title` explicativo | Comportamental | `proposicoes/[id]/page.tsx` |
| UI-012 | Unificar padrão de collapse — substituir `useState` accordion por `<details>/<summary>` nativo | Visual | `proposicoes/[id]/page.tsx` |

### UI/UX — Página do parlamentar: IA, hierarquia e duplo encoding (design critique 2026-04-02 #3)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-013 | Hero metric zone — score e síntese de alinhamento como protagonistas visuais; substituir stats bar por bloco de 2 colunas com gauge + proporção | Estrutural | `parlamentar/[id]/page.tsx`, `ScoreGauge.tsx` |
| UI-014 | Legenda do duplo encoding — nota explicativa acima do histórico de votos: dot = alinhamento ZIL, badge = voto registrado | Estrutural | `parlamentar/[id]/page.tsx` |
| UI-015 | Affordance nos cards de categoria — subtítulo de instrução + indicador visual de filtro ativo | Comportamental | `parlamentar/[id]/page.tsx` |
| UI-016 | Consolidar design tokens e mapa de categorias — ScoreGauge usa `zil-*`; extrair `LABEL` para `lib/categorias.ts` | Visual | `ScoreGauge.tsx`, `CategoriaBadge.tsx`, `lib/categorias.ts` (novo), `parlamentar/[id]/page.tsx` |
| UI-017 | Scope e navegação no histórico de votos — contagem sempre visível no título + corrigir back link hardcoded | Comportamental | `parlamentar/[id]/page.tsx` |

### UI/UX — Perfil do parlamentar: redundância e clareza (design critique 2026-04-04 #4)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-018 | Eliminar score duplicado no hero — substituir `text-4xl` redundante por frase interpretativa de alinhamento | Estrutural | `parlamentar/[id]/page.tsx` |
| UI-019 | Consolidar contagem de votos — unificar "com base em N votos" e "N de N votos" num único local | Estrutural | `parlamentar/[id]/page.tsx`, `ScoreGauge.tsx` |
| UI-020 | Legenda do duplo encoding com exemplo visual — substituir "badge = voto registrado" por mini badge real | Comportamental | `parlamentar/[id]/page.tsx` |
| UI-021 | Remover código interno dos cards de categoria — esconder "ZIL-ENE" do público, mover para `title` | Visual | `parlamentar/[id]/page.tsx` |
| UI-022 | Frase de síntese interpretativa — "Votou a favor em N de N pautas monitoradas" acima do hero metric | Estrutural | `parlamentar/[id]/page.tsx` |

## Fora do escopo v1 (não implementar)

- Autenticação / login / contas de usuário
- "Cobrar meu deputado"
- Alertas (email, Telegram, push)
- Deliberação por consenso (Polis)
- Curadoria comunitária (contestações)
- Compromisos públicos de parlamentares
- Dados de financiamento (TSE)
- Monitor eleitoral
- Fórum de discussão

---

## Workflow editorial v1

Toda gestão editorial é via código — sem interface admin:
- Classificação automática: `data/taxonomia/categorias.yml` (PR)
- Direção esperada de votações: `data/direcoes/[ano].yml` (PR + 2 aprovações + Discord)
- Indicadores Bússola: `data/bussula/marcos.yml` (PR + link para fonte oficial)
- Aplicar ao banco: `python scripts/apply_direcoes.py`

**Princípio operacional:** na dúvida sobre direção esperada, não classificar.

---

## Changelog

**Arquivo:** [`docs/CHANGELOG.md`](docs/CHANGELOG.md)
**Formato:** [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### Quando atualizar

Atualizar o changelog é **obrigatório** ao:
- Completar qualquer feature do backlog v1 (001–010)
- Corrigir um bug que afete comportamento observável
- Fazer breaking changes em contratos de API ou modelos
- Alterar arquivos de dados editoriais (`data/`)
- Mudar configuração de CI, Docker ou ambiente de desenvolvimento

Não é necessário para: refatorações internas sem impacto externo, atualizações de docs, correções de lint.

### Como atualizar

1. **Durante o desenvolvimento** — adicionar entradas em `## [Unreleased]`, sob a
   sub-seção correta:
   - `Added` — nova funcionalidade
   - `Changed` — mudança em funcionalidade existente
   - `Fixed` — correção de bug
   - `Removed` — remoção de funcionalidade
   - `Security` — vulnerabilidade corrigida

2. **Ao criar uma release** — renomear `[Unreleased]` para `[X.Y.Z] — YYYY-MM-DD`,
   adicionar novo `## [Unreleased]` vazio no topo, e atualizar os links de comparação
   no rodapé do arquivo.

3. **Formato de entrada:**
   ```
   - `caminho/do/arquivo.py`: descrição objetiva da mudança — consequência ou motivação
   ```
   Entradas devem ser legíveis por alguém que não viu o PR. Evitar "fixed bug" sem
   descrever qual bug; evitar "updated file" sem descrever o que mudou.

4. **Versionamento semântico:**
   - `MAJOR` (X.0.0): breaking change em API pública ou modelo de dados
   - `MINOR` (0.X.0): nova feature sem quebrar compatibilidade
   - `PATCH` (0.0.X): correção de bug, ajuste de config, fix de CI

### Regra geral

> Se a mudança vale um commit `feat:` ou `fix:`, vale uma entrada no changelog.
> Se vale um commit `chore:` ou `refactor:`, provavelmente não vale.

---

## Convenções de commit

```
feat:     nova feature
fix:      correção de bug
data:     mudança em data/ (classificações, direções, bússola)
docs:     documentação
test:     testes
refactor: refatoração sem mudança de comportamento
chore:    infra, CI, deps
```

---

## Princípios da constituição (resumo)

1. **Dados públicos, acesso livre** — toda leitura sem autenticação
2. **Apartidário por design** — paleta verde/ouro, linguagem neutra
3. **Transparência radical** — classificações auditáveis, histórico no git
4. **Projeto de estado** — métricas verificáveis, independente de governo
5. **Design system** — tokens `zil-*`, componentes reutilizáveis, sem inline styles
6. **API-first** — funcionalidade acessível via API antes de ter UI
7. **Qualidade** — testes obrigatórios para scoring, classifier e endpoints críticos

## Active Technologies
- Python 3.12 (backend/workers), TypeScript 5 (frontend) + FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2, Celery 5, httpx 0.27, anthropic SDK, Next.js 14, React 18, Tailwind CSS (002-legislative-enrichment-pipeline)
- SQLite (development, in-memory for tests), PostgreSQL 16 (production), Redis 7 (Celery broker/cache) (002-legislative-enrichment-pipeline)

## Recent Changes
- 002-legislative-enrichment-pipeline: Added Python 3.12 (backend/workers), TypeScript 5 (frontend) + FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2, Celery 5, httpx 0.27, anthropic SDK, Next.js 14, React 18, Tailwind CSS

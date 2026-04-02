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
scripts/           apply_direcoes.py (backlog)
tests/             unit/ integration/ contract/
specs/             Specify Kit specs por feature
docs/              PRD, ARCHITECTURE, GOVERNANCE, ROADMAP
```

---

## Comandos

```bash
# Backend (rodar da raiz)
python -m pytest tests/          # 98 testes
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
| 002 | Ingestão Senado Federal | backlog |
| 003 | Workflow editorial via código (YAML + scripts) | backlog |
| 004 | Frontend: /ranking com dados reais | backlog |
| 005 | Frontend: /parlamentar/[id] | backlog |
| 006 | Frontend: /proposicoes | backlog |
| 007 | Frontend: /bussula | backlog |
| 008 | Frontend: /metodologia | backlog |
| 009 | CI/CD (GitHub Actions) | backlog |
| 010 | Deploy produção | backlog |

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

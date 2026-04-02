# ZIL Observatório — Arquitetura v1

**Versão:** 1.0
**Última atualização:** 2026-04-02
**Escopo:** arquitetura para a fase v1 (plataforma pública de leitura, sem autenticação)

---

## 1. Problema

O Brasil possui dados legislativos abertos de alta qualidade — APIs REST da Câmara e do Senado com votações individuais atualizadas diariamente. O que falta é infraestrutura para transformar esses dados em respostas claras:

1. Como meu representante votou em pautas que afetam a soberania industrial?
2. Que proposições estão tramitando agora que podem mudar o jogo?
3. Onde o Brasil está hoje nos indicadores estratégicos de soberania industrial?

O ZIL Observatório responde essas três perguntas com dados verificáveis.

---

## 2. Visão Geral da Arquitetura v1

```
┌─────────────────────────────────────────────────────────┐
│                  USUÁRIOS (sem login)                   │
│         Web App (Next.js)  ·  API REST pública          │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 API (FastAPI)                            │
│   /parlamentares  /proposicoes  /votacoes  /bussula     │
│   /stats  /docs (Swagger)                               │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│            CAMADA DE SERVIÇOS                           │
│  ┌───────────────┐  ┌─────────────────────────────────┐ │
│  │ Scoring Engine│  │ Classifier (keyword matching)   │ │
│  │ Score ZIL     │  │ data/taxonomia/categorias.yml   │ │
│  └───────────────┘  └─────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                BANCO DE DADOS                           │
│   PostgreSQL 16 (principal) · Redis (cache + filas)     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│          INGESTÃO (workers Celery)                      │
│  ┌──────────────────┐  ┌───────────────────────────────┐ │
│  │  Câmara Crawler  │  │  Senado Crawler (v1 backlog)  │ │
│  │  (✅ concluído)  │  │                               │ │
│  └──────────────────┘  └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│         EDITORIAL (via código)                          │
│  data/taxonomia/  data/direcoes/  data/bussula/         │
│  Mantido via PRs + Discord + scripts/apply_direcoes.py  │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Stack Tecnológico v1

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Frontend | Next.js 14 + React 18 + Tailwind CSS | SSR para SEO, compartilhamento social, mobile-first |
| Design System | Tailwind + tokens `zil-*` + componentes em `components/ui/` | Consistência visual, inline styles proibidos |
| API | FastAPI 0.111 (Python 3.12) | Async nativo, tipagem, OpenAPI auto-doc, familiar ao time |
| Banco principal | PostgreSQL 16 | JSON columns, robusto, sem necessidade de Typesense em v1 |
| Cache / Filas | Redis 7 | Cache de API, filas Celery |
| Workers | Celery 5 + Redis | Ingestão assíncrona, agendamento (beat) |
| ORM | SQLAlchemy 2.0 + Pydantic 2 | Type-safe, migrations via Alembic |
| HTTP Client | httpx 0.27 | Async, retry com backoff exponencial |
| Testes | pytest 8 | 98 testes, CI obrigatório |
| Infra local | Docker Compose | Setup em < 5 min |
| Infra produção | A definir (Railway / Render / VPS) | Deploy automático via CI |

**Fora do stack v1 (adicionados em versões posteriores):**
- ~~Typesense~~ (busca full-text) — PostgreSQL `ILIKE` suficiente para v1
- ~~sentence-transformers / spaCy~~ (NLP) — keyword matching suficiente para v1
- ~~NextAuth.js~~ (autenticação) — sem login em v1
- ~~Kubernetes~~ — Docker Compose + VPS suficiente para v1
- ~~Sentry / Prometheus / Grafana~~ — logs básicos suficientes para v1

---

## 4. Estrutura do Repositório

```
manifesto-zil/
├── apps/
│   ├── web/                    # Next.js 14 + TypeScript
│   │   ├── app/                # Rotas (App Router)
│   │   │   ├── page.tsx        # Homepage (manifesto)
│   │   │   ├── ranking/        # /ranking
│   │   │   ├── parlamentar/[id]/ # /parlamentar/[id]
│   │   │   ├── proposicoes/    # /proposicoes
│   │   │   ├── bussula/        # /bussula (backlog)
│   │   │   ├── metodologia/    # /metodologia (backlog)
│   │   │   └── layout.tsx      # NavBar + Footer global
│   │   └── components/
│   │       ├── ui/             # Button, Badge, Card, Callout, SectionHeader
│   │       ├── ParlamentarCard.tsx
│   │       ├── ScoreGauge.tsx
│   │       ├── ScoreExplainer.tsx
│   │       ├── RankingPreview.tsx
│   │       ├── CategoryGrid.tsx
│   │       └── NavBar.tsx
│   ├── api/                    # FastAPI + SQLAlchemy
│   │   ├── main.py
│   │   ├── models/__init__.py  # SQLAlchemy models
│   │   ├── schemas/__init__.py # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── parlamentares.py
│   │   │   └── legislativo.py  # proposicoes, votacoes, stats, bussula
│   │   └── core/config.py
│   └── workers/                # Celery workers
│       ├── tasks.py            # Beat schedule
│       ├── crawlers/
│       │   ├── camara.py       # ✅ concluído
│       │   └── senado.py       # backlog (002)
│       ├── scoring/__init__.py # Score ZIL engine
│       └── classifiers/__init__.py # Keyword classifier
├── packages/
│   ├── camara_client/          # ✅ concluído
│   └── senado_client/          # backlog (002)
├── data/
│   ├── taxonomia/
│   │   └── categorias.yml      # 9 categorias ZIL com keywords
│   ├── direcoes/               # direcao_esperada por votação (backlog 003)
│   │   └── 2024.yml
│   └── bussula/                # indicadores estratégicos (backlog 003)
│       └── marcos.yml
├── scripts/
│   └── apply_direcoes.py       # CLI: YAML → banco (backlog 003)
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── contract/
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── GOVERNANCE.md
│   ├── ROADMAP.md
│   └── decisions/              # ADRs
├── specs/                      # Specify Kit specs por feature
├── docker-compose.yml
└── pytest.ini
```

---

## 5. Fontes de Dados

### Câmara dos Deputados — API REST ✅

- Base: `https://dadosabertos.camara.leg.br/api/v2`
- Endpoints em uso: `/deputados`, `/votacoes`, `/votacoes/{id}/votos`, `/votacoes/{id}/orientacoes`
- Atualização: votações a cada 6h (Celery beat), deputados semanalmente
- Rate limit: implícito, backoff exponencial implementado

### Senado Federal — API REST/XML (backlog 002)

- Base: `https://legis.senado.leg.br/dadosabertos`
- Endpoints principais: `/senador/lista/atual`, `/plenario/lista/votacao/{ano}`
- Formato: XML com fallback JSON parcial

### Fontes editoriais (via YAML)

- `data/taxonomia/categorias.yml` — keywords de classificação
- `data/direcoes/*.yml` — direção esperada por votação
- `data/bussula/marcos.yml` — indicadores estratégicos com link para fonte oficial

**Fora do escopo v1:** TSE (financiamento de campanha), Querido Diário, Portal da Transparência, notícias.

---

## 6. Modelo de Dados

Implementado em `apps/api/models/__init__.py` com SQLAlchemy 2.0 (cross-DB: PostgreSQL em produção, SQLite em testes).

### Tabelas ativas em v1

```
parlamentares           ← deputados + senadores unificados
proposicoes             ← matérias legislativas classificadas
votacoes                ← eventos de votação com score ZIL
votos                   ← voto individual por parlamentar/votação
scores_votacao          ← contribuição granular de cada voto ao score
ingestion_runs          ← log auditável de execuções de ingestão
financiamentos          ← estrutura pronta (crawler TSE é v2)
```

### Tabelas planejadas para v2+

```
usuarios                ← auth, email, UF
assinaturas_manifesto   ← manifesto com persistência
cobrancas               ← "cobrar parlamentar"
alertas_config          ← notificações por email/Telegram
deliberacoes            ← Polis (v3)
compromissos            ← compromisos públicos de parlamentares (v3)
```

### Chaves de idempotência

Todas as tabelas de dados legislativos usam `UniqueConstraint(fonte_id, fonte)` para garantir idempotência nas ingestões.

---

## 7. Pipeline de Ingestão

```
API Câmara / Senado
    │
    ├─ Celery beat (a cada 6h) → sync_votacoes
    │       GET /votacoes?ano=X (paginado)
    │       GET /votacoes/{id}  (proposição vinculada)
    │       GET /votacoes/{id}/votos  (votos individuais)
    │       GET /votacoes/{id}/orientacoes (orientação de partido)
    │       ↓
    │       Classificar por keywords → categorias_zil
    │       Criar Votacao + Voto[] + Proposicao (upsert)
    │       Registrar IngestionRun
    │
    ├─ Celery beat (segunda 03:00) → sync_deputados/senadores
    │       Upsert de perfis (nome, partido, UF, foto, email)
    │
    └─ Celery beat (diário 04:00) → recalcular_todos_scores
            Para cada parlamentar com votos ZIL:
            Score = (Σ alinhamento × peso) / Σ|peso| × 10
            Persiste ScoreVotacao por voto (auditável)
```

**Retry:** backoff exponencial (2s → 4s → 8s) por request; Celery autoretry (30s → 2min → 10min) por job.

**Idempotência:** verificação de `fonte_id` antes de inserir. Re-execução não cria duplicatas.

---

## 8. Scoring Engine

Implementado em `apps/workers/scoring/__init__.py`.

```
Para cada parlamentar:
  Para cada voto em votacao com categorias_zil AND direcao_esperada:
    alinhamento = +1.0 (votou na direção ZIL)
                  -1.0 (votou contra)
                   0.0 (ausente/absteve/obstruiu)
    peso = votacao.peso (default 1.0)

    Persiste ScoreVotacao(parlamentar, votacao, impacto, peso, justificativa)

  Score = (Σ alinhamento × peso) / (Σ |peso|) × 10
  Parlamentar.score_zil = round(score, 2)
```

Score `null` significa "sem votações ZIL com direção esperada definida" — diferente de 0.0.

---

## 9. Classifier

Implementado em `apps/workers/classifiers/__init__.py`.

**v1 — Keyword matching:**
- Carrega `data/taxonomia/categorias.yml` na inicialização
- Compila regex `\b{keyword}\b` por categoria
- Classifica texto (ementa + descrição de votação)
- Retorna lista de códigos ZIL detectados

**v2 — NLP semântico** (planejado): embeddings para proposições sem keywords explícitas.

**v3 — Curadoria humana** (planejado): contestações por usuários revisadas pelo comitê.

---

## 10. API REST

Implementada em `apps/api/`. Swagger em `/docs`.

### Endpoints v1

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/parlamentares` | Ranking com filtros (uf, partido, categoria, ordem) |
| GET | `/parlamentares/{id}` | Perfil completo |
| GET | `/parlamentares/{id}/votos-zil` | Histórico de votos em pautas ZIL |
| GET | `/partidos/ranking` | Score médio por partido |
| GET | `/proposicoes` | Catálogo com filtros (categoria, tipo, ano) |
| GET | `/proposicoes/{id}` | Detalhe de proposição |
| GET | `/votacoes` | Votações classificadas |
| GET | `/votacoes/{id}/votos` | Votos individuais de uma votação |
| GET | `/bussula` | Indicadores estratégicos (v1 backlog) |
| GET | `/stats` | Totais + data da última atualização |

Todos os endpoints são públicos, sem autenticação.

---

## 11. Frontend

Implementado em `apps/web/` com Next.js 14 (App Router) + TypeScript + Tailwind CSS.

### Rotas v1

| Rota | Status | Descrição |
|------|--------|-----------|
| `/` | ✅ | Homepage (manifesto + score explainer + ranking preview) |
| `/ranking` | 🔧 backlog 004 | Ranking completo com filtros e dados reais |
| `/parlamentar/[id]` | 🔧 backlog 005 | Perfil com histórico de votos ZIL |
| `/proposicoes` | 🔧 backlog 006 | Catálogo de proposições e votações |
| `/bussula` | 🔧 backlog 007 | Indicadores estratégicos |
| `/metodologia` | 🔧 backlog 008 | Como o score funciona |
| `/manifesto` | ✅ | Redirect para `/` |

### Design system

Tokens em `tailwind.config.js` e componentes em `components/ui/`. Inline styles proibidos (Princípio V da constituição).

---

## 12. Segurança e Privacidade

**v1 — sem dados de usuários.** Não há PII, não há sessões, não há cookies de rastreamento.

- Todos os dados são públicos (fontes governamentais abertas)
- API sem autenticação para leitura
- AGPL-3.0: forks devem manter código aberto
- Dados derivados: CC BY-SA 4.0

---

## 13. Infraestrutura e Deploy

**Desenvolvimento local:**
```bash
docker-compose up       # PostgreSQL + Redis + API + Web + Workers
pytest tests/           # 98 testes
```

**Produção v1:**
- Ambiente: a definir (Railway / Render / VPS)
- Docker Compose com serviços: `db`, `redis`, `api`, `web`, `worker`, `beat`
- CI/CD: GitHub Actions (pytest + ruff + mypy + tsc + eslint + next build)
- Backup: automático do PostgreSQL (diário)
- HTTPS: Let's Encrypt

**Não em v1:** Kubernetes, Prometheus/Grafana, múltiplas regiões.

---

## 14. Precedentes e Lições

**Operação Serenata de Amor (Brasil, 2016)**
Identificou 8.000+ reembolsos suspeitos. Falhou por dificuldade de financiamento e excesso de foco técnico vs. mobilização.
Lição: a ferramenta deve ser acessível, não só tecnicamente impressionante.

**Elas no Congresso (AzMina)**
Monitora PLs sobre gênero usando a mesma API da Câmara com equipe pequena.
Lição: monitoramento temático automatizado é viável com time enxuto.

**vTaiwan / Polis**
Gerou legislação real sobre Uber, fintech etc. em Taiwan. Prova que consenso transversal é possível com arquitetura certa.
Lição: a plataforma de deliberação (v3) tem precedente de sucesso real.

---

## 15. Decisões Arquiteturais Registradas

| ID | Decisão | Arquivo |
|----|---------|---------|
| ADR-001 | SQLAlchemy JSON/Uuid em vez de JSONB/ARRAY/UUID do PostgreSQL | docs/decisions/001-cross-db-types.md |
| ADR-002 | Importações por caminho curto (`from models import`) para evitar duplo registro de tabelas | docs/decisions/002-import-path.md |
| ADR-003 | `JSON(none_as_null=True)` em `categorias_zil` para filtros `IS NOT NULL` funcionarem no SQLite | docs/decisions/003-json-null.md |

Novas decisões arquiteturais: criar arquivo em `docs/decisions/NNN-nome.md`.

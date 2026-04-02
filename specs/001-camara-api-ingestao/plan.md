# Implementation Plan: Ingestão da API da Câmara dos Deputados

**Branch**: `001-camara-api-ingestao` | **Date**: 2026-04-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-camara-api-ingestao/spec.md`

## Summary

Completar e tornar production-ready o pipeline de ingestão de dados da Câmara dos
Deputados: sincronizar deputados + votações + votos individuais (2024–presente),
classificar proposições pelas 9 categorias ZIL, calcular Score ZIL por deputado,
e expor tudo via API REST pública sem autenticação. O scaffold já existe
(`apps/workers/crawlers/camara.py`, `packages/camara_client`, `apps/workers/scoring`);
as lacunas são: multi-ano, proposição linkage, observabilidade (IngestionRun),
retry com backoff exponencial correto, ScoreVotacao records por voto classificado,
e `ultima_atualizacao` no endpoint `/stats`.

## Technical Context

**Language/Version**: Python 3.12 (workers + API), TypeScript 5 (web — não afetado por esta feature)
**Primary Dependencies**: FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2, Celery 5, httpx 0.27, Redis 7, pytest 8
**Storage**: PostgreSQL 16 (dados primários), Redis 7 (filas Celery + cache)
**Testing**: pytest com fixtures de banco em memória (SQLite) ou PostgreSQL de teste; mypy --strict obrigatório no CI
**Target Platform**: Linux server (Docker Compose local, produção a definir)
**Project Type**: web-service + background workers (monorepo)
**Performance Goals**: ingestão completa inicial < 4 horas; endpoints API < 200ms p95
**Constraints**: idempotência obrigatória; sem autenticação na API pública; dados da última ingestão preservados em falha
**Scale/Scope**: 513 deputados, ~1.000–2.000 votações/ano, ~500 votos/votação → ~1–2M votos no período 2024–presente

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Observação |
|-----------|--------|------------|
| I. Dados Públicos, Acesso Livre | ✅ PASSA | API sem autenticação. Dados de votação acessíveis sem conta. |
| II. Apartidário por Design | ✅ PASSA | Score calculado por fórmula pública; sem curadoria editorial nesta feature. |
| III. Transparência Radical e Auditabilidade | ✅ PASSA | ScoreVotacao registra impacto+peso+justificativa por voto. IngestionRun rastreia cada execução. |
| IV. Projeto de Estado, não de Governo | ✅ PASSA | Dados da Câmara são independentes de governo. Histórico preservado mesmo após mandato. |
| V. Design System e Componentes Reutilizáveis | ✅ N/A | Feature é back-end only; sem novos componentes de UI. |
| VI. API-First e Open Source | ✅ PASSA | Todos os dados expostos via REST antes de qualquer UI. Workers idempotentes. Fonte+timestamp registrados em cada registro. |
| VII. Qualidade sem Gatekeeping | ✅ PASSA | Testes obrigatórios para scoring engine e endpoints `/parlamentares`, `/votacoes`, `/stats`. mypy+ruff no CI. |

**Resultado: TODAS AS GATES PASSAM. Prosseguir para Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/001-camara-api-ingestao/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 — gap analysis + decisões técnicas
├── data-model.md        # Phase 1 — entidades, relacionamentos, IngestionRun
├── quickstart.md        # Phase 1 — como rodar a ingestão localmente
├── contracts/
│   └── api-contracts.md # Phase 1 — contratos dos endpoints REST
└── tasks.md             # Phase 2 — gerado por /speckit.tasks
```

### Source Code (repository root)

```text
apps/api/
├── models/__init__.py       # Parlamentar, Proposicao, Votacao, Voto, ScoreVotacao
│                            # + IngestionRun (a adicionar)
├── schemas/__init__.py      # Pydantic schemas — adicionar StatsGeral.ultima_atualizacao
├── routers/
│   ├── parlamentares.py     # GET /parlamentares, /{id}, /{id}/votos-zil, /partidos/ranking
│   └── legislativo.py      # GET /proposicoes, /votacoes, /stats (adicionar ultima_atualizacao)
├── core/config.py           # Settings, SessionLocal, get_db
└── main.py                  # FastAPI app + CORS + lifespan

apps/workers/
├── crawlers/
│   └── camara.py            # sync_deputados, sync_votacoes, run_full_sync
│                            # Lacunas: multi-ano, proposição link, IngestionRun, backoff correto
├── classifiers/
│   └── __init__.py          # Classificador keyword — sem lacunas
├── scoring/
│   └── __init__.py          # recalcular_score_parlamentar, recalcular_todos_scores
│                            # Lacuna: não persiste ScoreVotacao records
└── tasks.py                 # Celery tasks + beat schedule (a criar/completar)

packages/
└── camara_client/
    └── __init__.py          # CamaraClient — completo, sem lacunas identificadas

data/taxonomia/
└── categorias.yml           # 9 categorias ZIL — imutável nesta feature

tests/
├── unit/
│   ├── test_scoring.py      # calcular_alinhamento, recalcular_score_parlamentar
│   └── test_classifier.py   # classificar_votacao, classificar_proposicao
├── integration/
│   ├── test_api_parlamentares.py   # GET /parlamentares com filtros
│   ├── test_api_legislativo.py     # GET /votacoes, /proposicoes, /stats
│   └── test_crawler_idempotency.py # re-execução não cria duplicatas
└── contract/
    └── test_api_schema.py   # response shapes batem com contratos
```

**Structure Decision**: Monorepo existente. Nenhum projeto novo. Todos os arquivos
a criar/modificar estão dentro de `apps/api/`, `apps/workers/`, e `tests/`.

## Complexity Tracking

> Nenhuma violação da constituição identificada. Seção não aplicável.

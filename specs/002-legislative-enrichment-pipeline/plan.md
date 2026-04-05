# Implementation Plan: Pipeline de Enriquecimento Legislativo Completo

**Branch**: `002-legislative-enrichment-pipeline` | **Date**: 2026-04-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-legislative-enrichment-pipeline/spec.md`

## Summary

Build an orchestrated pipeline that closes the full data lifecycle: (1) discover proposições via Câmara API keyword search, (2) auto-sync votações and individual votes for each discovered proposição, (3) enrich proposição text with LLM-generated plain-language summaries using verified legal context from Planalto.gov.br, and (4) recalculate parlamentar scores when editorial direction is applied. The enrichment uses a hybrid approach (regex citation extraction → Planalto scraping → Claude LLM synthesis with injected context → Pydantic validation) to eliminate hallucination while keeping language accessible.

## Technical Context

**Language/Version**: Python 3.12 (backend/workers), TypeScript 5 (frontend)
**Primary Dependencies**: FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2, Celery 5, httpx 0.27, anthropic SDK, Next.js 14, React 18, Tailwind CSS
**Storage**: SQLite (development, in-memory for tests), PostgreSQL 16 (production), Redis 7 (Celery broker/cache)
**Testing**: pytest 8 (136 tests passing), ESLint + tsc --noEmit (frontend)
**Target Platform**: Linux server (API/workers), browser (frontend)
**Project Type**: Web service (monorepo: API + workers + frontend)
**Performance Goals**: Enrichment pipeline < 30s per proposição; API responses < 200ms P95; Câmara API sync respects 300ms rate limiting
**Constraints**: Max 3-month date window per Câmara API query; Planalto.gov.br 10s timeout; `direcao_esperada` requires editorial curation (YAML); no authentication in v1
**Scale/Scope**: 406 proposições (401 pending enrichment), 126 with votações to sync, 594 parlamentares, 9 ZIL categories, ~150 keywords

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Dados Públicos, Acesso Livre | ✅ PASS | All endpoints are public without authentication (FR-007). Frontend displays enriched data without login. |
| II. Apartidário por Design | ✅ PASS | Classification uses objective keyword matching (FR-014). Direction is editorial with 2-maintainer approval (YAML workflow). Language in `resumo_simples` follows neutral template. |
| III. Transparência Radical | ✅ PASS | `confianca` score exposes verification level (FR-010). `fontes` lists Planalto URLs (FR-007). `modelo_llm` and `versao_pipeline` provide provenance. All classifications are auditable via `classificacao_automatica` flag. |
| IV. Projeto de Estado | ✅ PASS | Pipeline is content-agnostic — works across legislatures. Categories defined in YAML, not hardcoded. |
| V. Design System | ✅ PASS | Frontend uses `zil-*` tokens, `ContextoBadge`, `CategoriaBadge`, `DirecaoBadge` components from `components/ui/`. No inline styles. |
| VI. API-First | ✅ PASS | All enrichment data accessible via REST API before frontend renders it (FR-007). Workers are idempotent (FR-011). Ingestion records fonte, timestamp, method. |
| VII. Qualidade | ✅ PASS | 136 tests passing. Scoring engine and classifier have mandatory tests. Enrichment pipeline has unit tests with mocked LLM/Planalto. |

**Gate result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-legislative-enrichment-pipeline/
├── spec.md              # Feature specification (expanded with orchestration)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
apps/api/
├── core/config.py                    # Settings, DB engine, SessionLocal
├── models/__init__.py                # Proposicao, Votacao, Voto, Parlamentar, LeiArtigo, ScoreVotacao
├── schemas/__init__.py               # ProposicaoRead, ProposicaoContexto, LeiReferenciadaRead
├── routers/legislativo.py            # /proposicoes, /proposicoes/{id}/contexto, /proposicoes/{id}/enriquecer

apps/workers/
├── crawlers/camara.py                # sync_deputados, sync_votacoes, _upsert_proposicao
├── classifiers/__init__.py           # classificar_proposicao, classificar_votacao, relevancia_score
├── enrichment/__init__.py            # 5-stage pipeline: EXTRACT→RESOLVE→AUGMENT→VALIDATE→SERVE
├── scoring/__init__.py               # recalcular_score_parlamentar, recalcular_todos_scores
├── tasks.py                          # Celery tasks + beat schedule

packages/
├── camara_client/__init__.py         # CamaraClient: listar_votacoes, pesquisar_proposicoes, obter_proposicao

scripts/
├── discover_proposicoes.py           # [NEW] Keyword-based proposição discovery
├── sync_votacoes_proposicoes.py      # [NEW] Fetch votações for each proposição via API
├── sync_pipeline.py                  # [NEW] Orchestrator: discovery → votação sync → enrichment → scoring
├── apply_direcoes.py                 # Apply editorial direcao_esperada + peso from YAML
├── sync_votacoes_zil.py              # Sync specific votações from direcoes YAML
├── migrate_enrichment.py             # DB migration for enrichment fields

apps/web/
├── app/proposicoes/page.tsx          # Listing with resumo_simples, ContextoBadge
├── app/proposicoes/[id]/page.tsx     # Detail with glossário, impacto_zil, leis accordion
├── components/ContextoBadge.tsx      # Status badge component
├── components/DirecaoBadge.tsx       # Direction badge component
├── lib/api.ts                        # ProposicaoContexto type, API client

data/
├── taxonomia/categorias.yml          # 9 ZIL categories with keywords
├── direcoes/2024.yml                 # Editorial direction for 2024 votações
├── direcoes/2025.yml                 # Editorial direction for 2025 votações

tests/
├── unit/test_enrichment.py           # EXTRACT/RESOLVE/AUGMENT/VALIDATE stages
├── unit/test_classifier.py           # Keyword classification
├── unit/test_scoring.py              # Score calculation
├── integration/test_api_legislativo.py  # API endpoints
├── contract/test_api_schema.py       # Schema contracts
```

**Structure Decision**: Existing monorepo structure preserved. New files are 3 scripts (`sync_votacoes_proposicoes.py`, `sync_pipeline.py`) and 1 new CamaraClient method (`listar_votacoes_proposicao`). No new packages or directories needed.

## Complexity Tracking

No constitution violations detected. No complexity justification needed.

# Tasks: Pipeline de Enriquecimento Legislativo Completo

**Input**: Design documents from `/specs/002-legislative-enrichment-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Implementation Status**: The core enrichment pipeline (5-stage EXTRACT→RESOLVE→AUGMENT→VALIDATE→SERVE), all enrichment model fields, Pydantic schemas, API endpoints (`GET /proposicoes/{id}/contexto`, `POST /proposicoes/{id}/enriquecer`), Celery tasks, keyword classifier, scoring engine, migration script, and frontend integration (ContextoBadge, proposicoes pages) are **already implemented**. The remaining work focuses on the orchestration gap identified in the 2026-04-04 expansion: votação auto-sync per proposição (FR-015), score recalculation trigger (FR-016), and pipeline orchestration (FR-017).

**Tests**: Included — constitution principle VII mandates tests for critical infrastructure. The new sync script is critical data ingestion logic.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup

**Purpose**: No setup required — all infrastructure (SQLAlchemy models, Celery, Redis, enrichment fields, migration) already exists from Feature 002 initial implementation. `discover_proposicoes.py` and `CamaraClient.pesquisar_proposicoes()` are also already complete.

**Checkpoint**: Verified — no new tables, no new dependencies, no new packages needed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend `CamaraClient` with the method needed for proposição→votação fetching. This BLOCKS the sync script in Phase 3.

**CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T001 Add `listar_votacoes_proposicao(proposicao_id: int) -> list[VotacaoAPI]` method to `packages/camara_client/__init__.py` — calls `GET /proposicoes/{proposicao_id}/votacoes`, maps response to existing `VotacaoAPI` dataclass, follows same pattern as `listar_votacoes(ano)` (R5 in research.md). Include 300ms inter-request delay. Add under `# ── Votações ──` section after `obter_votacao_orientacoes`.
- [ ] T002 [P] Create `tests/unit/test_camara_client.py` with unit test for `listar_votacoes_proposicao` — mock `httpx.Client` to return sample `/proposicoes/{id}/votacoes` API response (format verified in R5), assert returns `list[VotacaoAPI]` with correct field mapping, assert empty list for proposição without votações, assert retry on 429.

**Checkpoint**: CamaraClient can fetch votações for any proposição — sync script can now be implemented.

---

## Phase 3: User Story 3 — Votação Auto-Sync & Pipeline Orchestration (Priority: P2) 🎯 MVP

**Goal**: Close the data lifecycle gap — auto-sync votações for all discovered proposições, trigger score recalculation after editorial direction is applied, and orchestrate all 4 pipeline steps via a single command.

**Independent Test**: Run `python scripts/sync_votacoes_proposicoes.py --dry-run` against database with 406 proposições → reports how many have votações available without persisting. Run `python scripts/sync_pipeline.py --skip-enrichment --dry-run` → executes all steps in correct order with no side effects.

### Implementation for User Story 3

- [ ] T003 [US3] Create `scripts/sync_votacoes_proposicoes.py` with core `sync_votacoes_por_proposicao(db, proposicao_ids=None, skip_existing=True)` function — iterates all proposições with `fonte=CAMARA` (or subset via `proposicao_ids`), calls `CamaraClient.listar_votacoes_proposicao(int(prop.fonte_id))` for each, deduplicates votações via `fonte_id` unique constraint check, creates `Votacao` records with `direcao_esperada=NULL` and `peso=NULL`, fetches individual votes via `client.obter_votos(votacao_id)`, creates `Voto` records resolving `parlamentar_id` (stub creation for unknown deputies, same pattern as `sync_votacoes` in `apps/workers/crawlers/camara.py`), classifies each votação via `classificar_votacao(descricao)` for `categorias_zil`, computes `votos_sim/votos_nao/abstencoes` counts, commits per-proposição, logs progress. Rate limiting: 300ms between API requests (R4). Returns stats dict: `{proposicoes_checadas, com_votacoes, votacoes_novas, votos_novos, erros}`.
- [ ] T004 [US3] Add CLI interface to `scripts/sync_votacoes_proposicoes.py` — argparse with `--proposicao-id ID` (sync single proposição by UUID), `--skip-with-votes` (default: true, skip proposições with existing votações), `--dry-run` (show what would be synced without persisting). Follow same patterns as `scripts/discover_proposicoes.py` and `scripts/apply_direcoes.py`: sys.path setup (ADR-002), `create_engine(settings.DATABASE_URL)`, `Session(engine)` context manager, summary stats output.
- [ ] T005 [P] [US3] Update `scripts/apply_direcoes.py` to call `recalcular_todos_scores(db)` after applying directions (FR-016) — import `recalcular_todos_scores` from `apps.workers.scoring`, call after `db.commit()` in `main()` (only when not `--dry-run` and `stats["updated"] > 0`), print count: `"N scores recalculados"`. Add `_repo_root` to sys.path for the import (same as other scripts).
- [ ] T006 [US3] Create `scripts/sync_pipeline.py` orchestrator — sequential execution of 4 steps (FR-017, R3): Step 1 calls `discover()` from `scripts/discover_proposicoes.py`, Step 2 calls `sync_votacoes_por_proposicao()` from `scripts/sync_votacoes_proposicoes.py`, Step 3 runs enrichment for pending proposições (inline loop calling `enriquecer_proposicao()` from `apps.workers.enrichment`), Step 4 calls `apply_direcoes()` + `recalcular_todos_scores()`. Each step prints a summary. Pipeline continues even if individual steps have partial failures (log errors, don't abort).
- [ ] T007 [US3] Add CLI flags to `scripts/sync_pipeline.py` — argparse with `--skip-discovery`, `--skip-votacoes`, `--skip-enrichment`, `--skip-scores`, `--dry-run` (propagates to all steps), `--ano-inicio` and `--ano-fim` (forwarded to discovery step). Match contract in `specs/002-legislative-enrichment-pipeline/contracts/api.md`.
- [ ] T008 [P] [US3] Create `tests/unit/test_sync_votacoes.py` — test `sync_votacoes_por_proposicao()` with mocked `CamaraClient`: (1) test creates votações and votos for proposição with 2 votações from API, (2) test skips proposição that already has votações when `skip_existing=True`, (3) test deduplicates votação with existing `fonte_id`, (4) test handles empty votação list gracefully, (5) test classifies votação with `classificar_votacao`. Use `db_session` fixture from `tests/conftest.py`, `make_proposicao` and `make_parlamentar` helpers, mock `CamaraClient` with `unittest.mock.patch`.
- [ ] T009 [P] [US3] Create `tests/integration/test_pipeline_scoring.py` — test that `apply_direcoes` followed by `recalcular_todos_scores` updates `Parlamentar.score_zil`: seed DB with parlamentar + votação + voto + direcao YAML, run `apply_direcoes()`, assert scores are non-null. Use `db_session` fixture, `make_parlamentar`, `make_votacao`, `make_voto` from conftest.

**Checkpoint**: Full pipeline runnable via `python scripts/sync_pipeline.py`. Votações synced for discovered proposições. Scores auto-recalculate after editorial direction is applied. All tests pass.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, changelog, and validation across all stories.

- [ ] T010 [P] Update `CLAUDE.md` — add `sync_votacoes_proposicoes.py` and `sync_pipeline.py` to the Commands section and Project Structure, with usage examples matching `contracts/api.md` CLI contracts.
- [ ] T011 [P] Update `docs/CHANGELOG.md` — add entries under `[Unreleased] → Added`: `sync_votacoes_proposicoes.py` (votação auto-sync per proposição), `sync_pipeline.py` (4-step orchestrator), `CamaraClient.listar_votacoes_proposicao()` method, `apply_direcoes.py` auto-triggers score recalculation.
- [ ] T012 Run `quickstart.md` validation — verify all commands documented in `specs/002-legislative-enrichment-pipeline/quickstart.md` execute without errors: dry-run commands, verify results query, pipeline orchestrator. Fix any discrepancies.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No work needed — skip.
- **Foundational (Phase 2)**: T001 blocks T003 (sync script needs CamaraClient method). T002 is parallel (different file).
- **User Story 3 (Phase 3)**: Depends on T001 completion. Within phase: T003 → T004 (CLI wraps core function), T003 → T006 (orchestrator imports sync function), T005 is independent (different file), T006 → T007 (flags extend orchestrator), T008/T009 are parallel (test files).
- **Polish (Phase 4)**: Depends on Phase 3 completion. T010/T011 are parallel. T012 runs last.

### Critical Path

```
T001 (CamaraClient method) → T003 (sync core) → T004 (sync CLI) → T006 (orchestrator) → T007 (orchestrator CLI)
                                                                       ↑
                                                T005 (apply_direcoes) ─┘
```

### Parallel Opportunities

Within Phase 2:
```
T001 (CamaraClient method)  ←── blocking
T002 (CamaraClient test)    ←── parallel (different file, can write test first or after)
```

Within Phase 3:
```
T003 (sync core)             ←── sequential after T001
T005 (apply_direcoes update) ←── parallel with T003 (different file)
T008 (sync unit tests)       ←── parallel with T009 (different test files)
T009 (pipeline scoring test) ←── parallel with T008
```

Within Phase 4:
```
T010 (CLAUDE.md)    ←── parallel
T011 (CHANGELOG.md) ←── parallel
T012 (quickstart)   ←── after T010/T011
```

---

## Parallel Example: Phase 3

```bash
# After T001 is complete, launch these in parallel:
Task T003: "Create sync_votacoes_por_proposicao() in scripts/sync_votacoes_proposicoes.py"
Task T005: "Update apply_direcoes.py to call recalcular_todos_scores"

# After T003 and T005 are complete:
Task T004: "Add CLI interface to sync_votacoes_proposicoes.py"
Task T006: "Create sync_pipeline.py orchestrator"

# After T004 and T006 are complete, launch tests in parallel:
Task T008: "Unit test for sync_votacoes_proposicoes"
Task T009: "Integration test for pipeline scoring"
```

---

## Implementation Strategy

### MVP First (T001 → T003 → T004)

1. Complete T001: `listar_votacoes_proposicao` method
2. Complete T003 + T004: Votação sync script with CLI
3. **STOP and VALIDATE**: Run `python scripts/sync_votacoes_proposicoes.py --dry-run` to verify votação discovery
4. Run actual sync — verify votações and votos appear in DB

### Incremental Delivery

1. T001 + T002 → CamaraClient extended → Test passes
2. T003 + T004 → Votação sync works → Dry-run validated → Deploy
3. T005 → Score recalculation triggers automatically → `apply_direcoes.py` tested
4. T006 + T007 → Full pipeline orchestrated → `sync_pipeline.py --dry-run` validated
5. T008 + T009 → All tests pass → `pytest tests/ -x -q` green
6. T010 + T011 + T012 → Docs updated → Quickstart validated

### What's Already Done (NOT in tasks)

| Component | File | Status |
|-----------|------|--------|
| Enrichment pipeline (5 stages) | `apps/workers/enrichment/__init__.py` | ✅ Complete |
| Proposicao enrichment fields (8 columns) | `apps/api/models/__init__.py` | ✅ Complete |
| ProposicaoContexto schema | `apps/api/schemas/__init__.py` | ✅ Complete |
| GET /proposicoes/{id}/contexto | `apps/api/routers/legislativo.py` | ✅ Complete |
| POST /proposicoes/{id}/enriquecer | `apps/api/routers/legislativo.py` | ✅ Complete |
| Celery tasks (enrich + score) | `apps/workers/tasks.py` | ✅ Complete |
| Keyword classifier | `apps/workers/classifiers/__init__.py` | ✅ Complete |
| Scoring engine | `apps/workers/scoring/__init__.py` | ✅ Complete |
| DB migration | `scripts/migrate_enrichment.py` | ✅ Complete |
| Proposição discovery | `scripts/discover_proposicoes.py` | ✅ Complete |
| CamaraClient.pesquisar_proposicoes | `packages/camara_client/__init__.py` | ✅ Complete |
| ContextoBadge component | `apps/web/components/ContextoBadge.tsx` | ✅ Complete |
| Frontend proposicoes pages | `apps/web/app/proposicoes/` | ✅ Complete |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [US3] label = all new tasks belong to User Story 3 (async pipeline orchestration)
- US1 (enrichment API), US2 (structured context API), US4 (frontend display) are already implemented
- `sync_votacoes_proposicoes.py` reuses patterns from `apps/workers/crawlers/camara.py` (`normalizar_voto`, `VOTO_MAP`, parlamentar stub creation, orientação fetching)
- All scripts follow ADR-002: explicit `sys.path.insert(0, _api_dir)` for imports
- All JSON columns use `JSON(none_as_null=True)` per ADR-003
- Tests use SQLite in-memory via `db_session` fixture from `tests/conftest.py`
- Rate limiting: 300ms between Câmara API requests (R4 in research.md)
- Votação deduplication: `UniqueConstraint(fonte_id, fonte)` on `votacoes` table (R2)
- `direcao_esperada` and `peso` are NEVER set by auto-sync — editorial-only (via YAML)

# Tasks: 012 — Enriquecimento de Dados de Proposicoes

**Input**: Design documents from `/specs/012-enriquecimento-dados-proposicoes/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: Included (~30 new tests required per spec success criteria)

**Organization**: Tasks grouped by user story mapped from spec features F-001 through F-008, organized across 3 implementation phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `apps/api/` (models, schemas, routers)
- **Frontend**: `apps/web/` (components, pages, lib)
- **Workers/Scripts**: `scripts/`, `packages/camara_client/`
- **Tests**: `tests/unit/`, `tests/integration/`

## User Story Mapping

| Story | Features | Phase | Priority | Description |
|-------|----------|-------|----------|-------------|
| US1 | F-001 | 1 | P1 | Situacao estruturada com filtros (cod_situacao, regime, apreciacao) |
| US2 | F-004, F-005, F-008 | 1 | P1 | Votacao enriquecida + keywords + lei resultante |
| US3 | F-006 | 2 | P2 | Autoria completa com vinculacao a parlamentares |
| US4 | F-002 | 2 | P2 | Temas oficiais da Camara |
| US5 | F-003 | 3 | P3 | Cadeia legislativa + relacionadas |
| US6 | F-007 | 3 | P3 | Orgao atual e relator |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Migration script, helper modules, and shared schemas needed by all user stories

- [X] T001 Create idempotent migration script (Phase 1 columns) in `scripts/migrate_012_detail_fields.py` — add 6 cols to proposicoes (cod_situacao, regime, apreciacao, keywords_camara, urn_final, detalhes_sincronizados_em) + 3 cols to votacoes (aprovacao, sigla_orgao, proposicao_objeto) + 3 indexes (ix_proposicao_cod_situacao, ix_proposicao_regime, ix_proposicao_detalhes_sync). Check column existence before ALTER TABLE.
- [X] T002 [P] Create situacao helper module in `apps/api/lib/situacao.py` — SITUACAO_GRUPOS dict mapping codSituacao values to 4 UI groups (tramitando, aprovada, arquivada, outras) per Research Decision 6. Include `get_situacao_grupo(cod: int) -> str` function.
- [X] T003 [P] Create URN-to-URL helper module in `apps/api/lib/urn.py` — `parse_urn_to_url(urn: str) -> Optional[str]` that parses LexML URN format `urn:lex:br:federal:lei:YYYY-MM-DD;NNNNN` and constructs Planalto URL per Research Decision 5. Return None for unrecognized formats.
- [X] T004 [P] Create tipo_relacao classifier in `apps/api/lib/relacoes.py` — `classificar_tipo_relacao(sigla_tipo: str) -> str` mapping siglaTipo to tipo_relacao per Research Decision 4 classification map. Default to "outro" for unrecognized types.
- [X] T005 Add new columns to Proposicao model in `apps/api/models/__init__.py` — Phase 1 fields: cod_situacao (Integer), regime (String 50), apreciacao (String 100), keywords_camara (Text), urn_final (String 500), detalhes_sincronizados_em (DateTime). Add indexes ix_proposicao_cod_situacao, ix_proposicao_regime, ix_proposicao_detalhes_sync.
- [X] T006 Add new columns to Votacao model in `apps/api/models/__init__.py` — aprovacao (Integer, nullable), sigla_orgao (String 20), proposicao_objeto (Text).
- [X] T007 Add ParlamentarSnippet and CadeiaRead schemas in `apps/api/schemas/__init__.py` — ParlamentarSnippet(id, nome, partido, uf, foto_url), CadeiaRead(principal_fonte_id, anterior_fonte_id, posterior_fonte_id). Expand ProposicaoRead with Phase 1 fields: cod_situacao, regime, apreciacao, keywords_camara, urn_final, url_lei (computed), situacao_grupo (computed).
- [X] T008 Expand VotacaoRead schema in `apps/api/schemas/__init__.py` — add aprovacao (Optional[int]), sigla_orgao (Optional[str]), proposicao_objeto (Optional[str]).
- [X] T009 Add TypeScript types in `apps/web/lib/api.ts` — extend Proposicao interface with cod_situacao, regime, apreciacao, keywords_camara, urn_final, url_lei, situacao_grupo. Extend VotoHistorico if needed. Add ParlamentarSnippet, AutorRead, TemaRead, RelacionadaRead, CadeiaRead types.

**Checkpoint**: Migration ready, models updated, schemas aligned across backend/frontend.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backfill script and CamaraClient methods needed by multiple user stories

**CRITICAL**: No user story can be fully validated until backfill populates real data

- [X] T010 Create backfill script `scripts/sync_detalhes_proposicoes.py` — Phase 1 mode: iterate all proposicoes WHERE detalhes_sincronizados_em IS NULL, call `obter_proposicao(fonte_id)` per prop, extract cod_situacao/regime/apreciacao/keywords/urn_final from response, update row, set detalhes_sincronizados_em. Support `--dry-run`, `--fase 1/2/3` flags. 300ms inter-request delay. Log progress.
- [X] T011 [P] Add `listar_autores_proposicao(proposicao_id: str)` method in `packages/camara_client/__init__.py` — GET /proposicoes/{id}/autores. Return list of author dicts. Reuse existing retry + rate-limit logic.
- [X] T012 [P] Add `listar_temas_proposicao(proposicao_id: str)` method in `packages/camara_client/__init__.py` — GET /proposicoes/{id}/temas. Return list of theme dicts with codTema, tema.
- [X] T013 [P] Add `listar_relacionadas_proposicao(proposicao_id: str, max_pages: int = 10)` method in `packages/camara_client/__init__.py` — GET /proposicoes/{id}/relacionadas with pagination. Fetch up to max_pages (cap at ~200 items per Decision 4). Return list of related proposicao dicts.
- [X] T014 Integrate backfill Step 1.5 into `scripts/sync_pipeline.py` — add `--skip-detalhes` flag, call sync_detalhes_proposicoes between discovery and votacoes steps. Follow existing pipeline orchestration pattern.

**Checkpoint**: Foundation ready — CamaraClient has all 3 new methods, backfill script operational, pipeline integrated.

---

## Phase 3: US1 — Situacao Estruturada com Filtros (Priority: P1)

**Goal**: Cidadao filtra proposicoes por regime legislativo e grupo de situacao. Jornalista identifica proposicoes em regime de urgencia.

**Independent Test**: `GET /proposicoes?situacao_grupo=tramitando` returns only active proposicoes. `GET /proposicoes?regime=URGENCIA` returns only urgent ones. UI shows colored situacao badges and regime badges.

### Tests for US1

- [X] T015 [P] [US1] Unit test for situacao helper in `tests/unit/test_situacao.py` — test get_situacao_grupo() maps cod 903→tramitando, 1140→aprovada, 923→arquivada, 9999→outras. Test edge cases: None input, 0 input.
- [X] T016 [P] [US1] Integration test for situacao filters in `tests/integration/test_detail_endpoints.py` — create 3 proposicoes with different cod_situacao values, verify GET /proposicoes?situacao_grupo=tramitando returns only matching rows. Verify GET /proposicoes?regime=URGENCIA filters correctly. Verify 422 for invalid situacao_grupo.

### Implementation for US1

- [X] T017 [US1] Add `regime` and `situacao_grupo` query params to GET /proposicoes in `apps/api/routers/legislativo.py` — import get_situacao_grupo from lib/situacao, add Optional[str] params, build WHERE clause with cod_situacao IN (...) for situacao_grupo, regime = :regime for regime filter. Validate inputs, return 422 for invalid values.
- [X] T018 [US1] Wire situacao_grupo and url_lei computed fields in ProposicaoRead serialization in `apps/api/routers/legislativo.py` — in listar_proposicoes and obter_proposicao, compute situacao_grupo from cod_situacao via helper, compute url_lei from urn_final via parse_urn_to_url. Attach to response.
- [X] T019 [US1] Create proposicao helper module `apps/web/lib/proposicao.ts` — export situacaoColor(grupo: string): string mapping tramitando→yellow, aprovada→green, arquivada→orange, outras→gray. Export regimeLabel(regime: string): string for display labels. Export situacaoLabel(grupo: string): string for Portuguese labels.
- [X] T020 [US1] Add situacao/regime filter dropdowns to `/proposicoes` page in `apps/web/app/proposicoes/page.tsx` — add two <select> elements: "Situacao" (Todas, Em Tramitacao, Aprovada, Arquivada, Outras) and "Regime" (Todos, Urgencia, Especial, Ordinario). Wire to API query params. Style consistent with existing tipo/categoria filters.
- [X] T021 [US1] Display situacao badge and regime badge on proposicao cards and detail page in `apps/web/app/proposicoes/page.tsx` and `apps/web/app/proposicoes/[id]/page.tsx` — colored badge per situacaoColor(), regime badge (URGENCIA in red, ESPECIAL in amber) when present. Use Tailwind classes, no inline styles.

**Checkpoint**: Proposicoes can be filtered by situacao/regime. Colored badges visible on cards and detail page.

---

## Phase 4: US2 — Votacao Enriquecida + Keywords + Lei Resultante (Priority: P1)

**Goal**: Cidadao ve resultado autoritativo de votacao (sem inferencia por contagem), keywords como tags, e badge "VIROU LEI" com link direto ao Planalto.

**Independent Test**: Votacao with aprovacao=1 shows "Aprovada" badge without asterisk. Proposicao with urn_final shows green "VIROU LEI" badge with working Planalto link. Keywords displayed as tags.

### Tests for US2

- [X] T022 [P] [US2] Unit test for URN parser in `tests/unit/test_urn.py` — test parse_urn_to_url with valid URN returns correct Planalto URL, test invalid URN returns None, test edge cases (lei complementar, medida provisoria formats).
- [X] T023 [P] [US2] Integration test for votacao enriched fields in `tests/integration/test_detail_endpoints.py` — create Votacao with aprovacao=1, verify GET /votacoes/{id} returns aprovacao, sigla_orgao, proposicao_objeto fields. Verify null handling.

### Implementation for US2

- [X] T024 [US2] Wire aprovacao/sigla_orgao/proposicao_objeto in VotacaoRead serialization in `apps/api/routers/legislativo.py` — ensure new Votacao fields pass through to response in obter_votacao endpoint.
- [X] T025 [US2] Update backfill script Phase 1 to also extract aprovacao from votacao detail in `scripts/sync_detalhes_proposicoes.py` — for each proposicao, also update linked votacoes: call obter_votacao_detalhes, extract aprovacao (int 1/0/null), sigla_orgao, proposicaoObjeto. Update votacao rows.
- [X] T026 [US2] Display keywords as tags on proposicao detail page in `apps/web/app/proposicoes/[id]/page.tsx` — parse keywords_camara (comma-separated string), render as inline tag chips with `bg-zil-card text-zil-muted` style. Show in metadata section below ementa.
- [X] T027 [US2] Display "VIROU LEI" badge with Planalto link on proposicao detail page in `apps/web/app/proposicoes/[id]/page.tsx` — when url_lei is present, render green badge "Virou Lei" with external link icon, linking to Planalto URL. When urn_final exists but url_lei is null, show URN as text.
- [X] T028 [US2] Replace inferential resultado with autoritativo aprovacao in votacao display in `apps/web/app/proposicoes/[id]/page.tsx` — when aprovacao is 1, show "Aprovada" (green). When 0, show "Rejeitada" (red). When null, fall back to existing resultado text with `*` suffix. Remove asterisk badges from approved votacoes.

**Checkpoint**: Votacao shows authoritative result. Keywords visible as tags. "VIROU LEI" badge links to Planalto.

---

## Phase 5: US3 — Autoria Completa com Vinculacao (Priority: P2)

**Goal**: Cidadao ve quem propoe cada proposicao com link direto para o perfil do parlamentar. Endpoint para listar proposicoes de autoria de um parlamentar.

**Independent Test**: `GET /proposicoes/{id}/autores` returns linked authors. `GET /parlamentares/{id}/proposicoes` returns authored proposicoes. Detail page shows author names with profile links.

### Tests for US3

- [X] T029 [P] [US3] Unit test for author-parlamentar matching in `tests/unit/test_proposicao_autores.py` — test extraction of deputado ID from URI `/api/v2/deputados/204554` → "204554". Test matching against Parlamentar.fonte_id. Test null when URI is Orgao or Senado. Test ordem assignment.
- [X] T030 [P] [US3] Integration test for autores endpoint in `tests/integration/test_detail_endpoints.py` — create Proposicao + ProposicaoAutor with parlamentar FK, verify GET /proposicoes/{id}/autores returns AutorRead[] with nested ParlamentarSnippet. Verify 404 for unknown proposicao.
- [X] T031 [P] [US3] Integration test for parlamentar proposicoes endpoint in `tests/integration/test_detail_endpoints.py` — create Parlamentar + ProposicaoAutor linking, verify GET /parlamentares/{id}/proposicoes returns ProposicaoRead[]. Verify pagination and tipo filter.

### Implementation for US3

- [X] T032 [US3] Add ProposicaoAutor model in `apps/api/models/__init__.py` — table proposicao_autores with id, proposicao_id (FK CASCADE), parlamentar_id (FK nullable), nome, tipo, ordem, proponente, uri_autor, created_at. Indexes: uq_autor_proposicao_ordem, ix_autor_parlamentar, ix_autor_proposicao. Add relationship Proposicao.autores_rel.
- [X] T033 [US3] Add Phase 2 to migration script in `scripts/migrate_012_detail_fields.py` — CREATE TABLE proposicao_autores (idempotent), add temas_camara column to proposicoes.
- [X] T034 [US3] Add AutorRead schema in `apps/api/schemas/__init__.py` — AutorRead(id, nome, tipo, ordem, proponente, parlamentar: Optional[ParlamentarSnippet]).
- [X] T035 [US3] Implement GET /proposicoes/{id}/autores endpoint in `apps/api/routers/legislativo.py` — query ProposicaoAutor WHERE proposicao_id, joinedload parlamentar, return AutorRead[] with nested ParlamentarSnippet.
- [X] T036 [US3] Implement GET /parlamentares/{id}/proposicoes endpoint in `apps/api/routers/parlamentares.py` — query ProposicaoAutor WHERE parlamentar_id, join Proposicao, support tipo filter + limit/offset, return ProposicaoRead[].
- [X] T037 [US3] Expand autor_principal in ProposicaoRead response in `apps/api/routers/legislativo.py` — in obter_proposicao, if autor_principal_id is set, load Parlamentar and attach as ParlamentarSnippet. Show in both list and detail responses.
- [X] T038 [US3] Add backfill Phase 2 to sync script in `scripts/sync_detalhes_proposicoes.py` — for each proposicao, call listar_autores_proposicao(), create ProposicaoAutor rows, extract deputado ID from author uri to match Parlamentar.fonte_id, set parlamentar_id FK. Set autor_principal_id on Proposicao for ordem=1 author.
- [X] T039 [US3] Create AutoresLine component in `apps/web/components/AutoresLine.tsx` — inline author summary: "Autor: Dep. Fulano (XX/SP)" with link to /parlamentar/{id}. For multiple authors: "Dep. Fulano (XX/SP) e mais N". Truncate at 2 visible names.
- [X] T040 [US3] Integrate AutoresLine into proposicao card and detail page in `apps/web/app/proposicoes/page.tsx` and `apps/web/app/proposicoes/[id]/page.tsx` — show author below ementa on cards. On detail page, show full author list with profile links using `<details>` for co-authors.
- [X] T041 [US3] Add "Proposicoes de autoria" section to parlamentar profile in `apps/web/app/parlamentar/[parlamentar_id]/page.tsx` — fetch GET /parlamentares/{id}/proposicoes, render as list of proposicao cards with tipo/numero/ano + resumo_simples. Collapsible via `<details>`. Add api method `parlamentares.proposicoes(id)` in `apps/web/lib/api.ts`.

**Checkpoint**: Authors visible on all proposicao views. Parlamentar profile shows authored proposicoes. FK linking operational.

---

## Phase 6: US4 — Temas Oficiais da Camara (Priority: P2)

**Goal**: Cidadao ve temas oficiais da Camara como metadata complementar as categorias ZIL.

**Independent Test**: `GET /proposicoes/{id}/temas` returns TemaRead[]. Detail page shows temas section.

### Tests for US4

- [X] T042 [P] [US4] Integration test for temas endpoint in `tests/integration/test_detail_endpoints.py` — create Proposicao with temas_camara JSON, verify GET /proposicoes/{id}/temas returns TemaRead[]. Verify empty array when temas_camara is NULL.

### Implementation for US4

- [X] T043 [US4] Add temas_camara column to Proposicao model in `apps/api/models/__init__.py` — JSON(none_as_null=True) per ADR-003. Nullable.
- [X] T044 [US4] Add TemaRead schema in `apps/api/schemas/__init__.py` — TemaRead(cod: int, tema: str).
- [X] T045 [US4] Implement GET /proposicoes/{id}/temas endpoint in `apps/api/routers/legislativo.py` — read temas_camara JSON from Proposicao, parse into TemaRead[], return. Empty array if NULL.
- [X] T046 [US4] Add temas_camara field to ProposicaoRead schema in `apps/api/schemas/__init__.py` — Optional[list[dict]] = None.
- [X] T047 [US4] Add backfill Phase 2 temas to sync script in `scripts/sync_detalhes_proposicoes.py` — for each proposicao, call listar_temas_proposicao(), store as JSON array in temas_camara column.
- [X] T048 [US4] Display temas on proposicao detail page in `apps/web/app/proposicoes/[id]/page.tsx` — render temas as tag chips in a "Temas da Camara" section. Use `bg-zil-card border border-zil-divider` style. Hide section when temas_camara is null/empty.

**Checkpoint**: Temas visible on proposicao detail. API endpoint functional.

---

## Phase 7: US5 — Cadeia Legislativa + Relacionadas (Priority: P3)

**Goal**: Pesquisador navega a cadeia legislativa (Camara → Senado → Lei) e ve proposicoes relacionadas (emendas, substitutivos, pareceres) agrupadas por tipo.

**Independent Test**: `GET /proposicoes/{id}/relacionadas` returns RelacionadaRead[] grouped by tipo. Detail page shows cadeia timeline and collapsible relacionadas sections.

### Tests for US5

- [X] T049 [P] [US5] Unit test for tipo_relacao classifier in `tests/unit/test_relacoes.py` — test classificar_tipo_relacao maps "EMC"→emenda, "SBT"→substitutivo, "PAR"→parecer, "PL"→apensada, "XYZ"→outro.
- [X] T050 [P] [US5] Integration test for relacionadas endpoint in `tests/integration/test_detail_endpoints.py` — create Proposicao + 3 ProposicaoRelacao (emenda, substitutivo, parecer), verify GET /proposicoes/{id}/relacionadas returns all 3. Verify tipo_relacao filter. Verify pagination. Verify 404 for unknown proposicao.
- [X] T051 [P] [US5] Integration test for cadeia fields in `tests/integration/test_detail_endpoints.py` — create Proposicao with prop_principal_id set, verify GET /proposicoes/{id} includes cadeia object with principal_fonte_id.

### Implementation for US5

- [X] T052 [US5] Add ProposicaoRelacao model in `apps/api/models/__init__.py` — table proposicao_relacoes with id, proposicao_id (FK CASCADE), relacionada_id (FK nullable), relacionada_fonte_id, tipo_relacao, sigla_tipo, numero, ano, ementa, created_at. Indexes: uq_relacao_prop_rel, ix_relacao_proposicao, ix_relacao_relacionada, ix_relacao_tipo. Add relationship Proposicao.relacionadas.
- [X] T053 [US5] Add Phase 3 to migration script in `scripts/migrate_012_detail_fields.py` — CREATE TABLE proposicao_relacoes (idempotent), add 5 cols to proposicoes: prop_principal_id (String 50), prop_anterior_id (String 50), prop_posterior_id (String 50), orgao_situacao (String 50), relator_id (UUID FK nullable).
- [X] T054 [US5] Add RelacionadaRead schema in `apps/api/schemas/__init__.py` — RelacionadaRead(id, tipo_relacao, sigla_tipo, numero, ano, ementa, relacionada_fonte_id, proposicao_id_zil: Optional[UUID]).
- [X] T055 [US5] Implement GET /proposicoes/{id}/relacionadas endpoint in `apps/api/routers/legislativo.py` — query ProposicaoRelacao WHERE proposicao_id, support tipo_relacao filter + limit/offset, return RelacionadaRead[]. Map relacionada_id to proposicao_id_zil for deep linking.
- [X] T056 [US5] Wire cadeia computed field in ProposicaoRead in `apps/api/routers/legislativo.py` — in obter_proposicao, if any of prop_principal_id/anterior/posterior is set, build CadeiaRead object. Attach to response.
- [X] T057 [US5] Add backfill Phase 3 to sync script in `scripts/sync_detalhes_proposicoes.py` — for each proposicao, call listar_relacionadas_proposicao() (max 10 pages), classify each related prop via classificar_tipo_relacao(), create ProposicaoRelacao rows. Extract prop_principal_id/anterior/posterior from uriPropPrincipal/Anterior/Posterior. Try to match relacionada_fonte_id to existing proposicoes for relacionada_id FK.
- [X] T058 [US5] Create CadeiaNode component in `apps/web/components/CadeiaNode.tsx` — visual timeline node showing legislative chain steps (Camara → Senado → Lei). Each node links to related proposicao if in DB or shows fonte_id as text. Horizontal on desktop, vertical on mobile.
- [X] T059 [US5] Display cadeia timeline and relacionadas on proposicao detail page in `apps/web/app/proposicoes/[id]/page.tsx` — cadeia section always visible when present. Relacionadas in `<details>/<summary>` grouped by tipo_relacao, capped at 20 per group. Add api method `proposicoes.relacionadas(id)` in `apps/web/lib/api.ts`.

**Checkpoint**: Cadeia timeline navigable. Relacionadas listed by type with deep links. Full legislative lifecycle visible.

---

## Phase 8: US6 — Orgao Atual e Relator (Priority: P3)

**Goal**: Cidadao ve em qual orgao a proposicao esta tramitando e quem e o relator.

**Independent Test**: Detail page shows orgao badge (e.g., "CCJC") and relator name with profile link.

### Tests for US6

- [X] T060 [P] [US6] Integration test for orgao/relator fields in `tests/integration/test_detail_endpoints.py` — create Proposicao with orgao_situacao="CCJC" and relator_id linked to Parlamentar, verify GET /proposicoes/{id} returns orgao_situacao and relator ParlamentarSnippet.

### Implementation for US6

- [X] T061 [US6] Add orgao_situacao and relator_id to Proposicao model in `apps/api/models/__init__.py` — orgao_situacao (String 50), relator_id (UUID FK to parlamentares, nullable). Add relationship Proposicao.relator.
- [X] T062 [US6] Wire relator in ProposicaoRead in `apps/api/routers/legislativo.py` — in obter_proposicao, if relator_id is set, load Parlamentar and attach as ParlamentarSnippet.
- [X] T063 [US6] Add backfill Phase 3 orgao/relator to sync script in `scripts/sync_detalhes_proposicoes.py` — extract statusProposicao.siglaOrgao → orgao_situacao. Extract relator URI, match to Parlamentar.fonte_id → relator_id FK. Set null when not found.
- [X] T064 [US6] Display orgao badge and relator on proposicao detail page in `apps/web/app/proposicoes/[id]/page.tsx` — orgao badge (e.g., "CCJC" in zil-card style) in header area. Relator name with link to parlamentar profile below orgao badge. Hide both when null.

**Checkpoint**: Proposicao detail shows current committee and relator with navigation.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that span multiple user stories, final validation

- [X] T065 [P] Progressive disclosure redesign of proposicao detail page in `apps/web/app/proposicoes/[id]/page.tsx` — organize all new sections into 3-tier visibility per Research Decision 8: Tier 1 (always visible): header, resumo, autor principal, cadeia, votacoes. Tier 2 (`<details>`): ementa, co-autores, tramitacao. Tier 3 (`<details>`): relacionadas, glossario, leis referenciadas.
- [ ] T066 [P] Add weekly re-sync Celery beat schedule for active proposicoes in `apps/workers/tasks.py` — new task `task_sync_detalhes_ativos` that filters proposicoes WHERE cod_situacao NOT IN archived/transformed AND detalhes_sincronizados_em < 7 days ago. Run Phase 1 backfill logic per proposicao. Per Research Decision 7.
- [X] T067 [P] Run all 151 existing tests + new tests in `tests/` — verify zero regressions. Run `.venv/bin/python3 -m pytest tests/ -v`. Verify ~30 new tests pass.
- [X] T068 [P] TypeScript type-check in `apps/web/` — run `npx tsc --noEmit`. Verify zero errors with all new types and components.
- [ ] T069 Run quickstart.md full pipeline validation — execute all verification steps from `specs/012-enriquecimento-dados-proposicoes/quickstart.md`. Verify success criteria: 100% cod_situacao, >95% autor_principal_id, >90% temas, >40% cadeia.
- [X] T070 Update changelog in `docs/CHANGELOG.md` — add entries under [Unreleased] for all Feature 012 changes: Added (new tables, columns, endpoints, components, helpers), Changed (expanded schemas, redesigned detail page).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion (models must exist) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — can run in parallel with US2
- **US2 (Phase 4)**: Depends on Foundational — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Foundational — can run in parallel with US4
- **US4 (Phase 6)**: Depends on Foundational — can run in parallel with US3
- **US5 (Phase 7)**: Depends on Foundational — can run in parallel with US6
- **US6 (Phase 8)**: Depends on Foundational — can run in parallel with US5
- **Polish (Phase 9)**: Depends on all user stories being complete

### Within-Phase Execution

Each user story follows: Tests → Models/Schemas → Endpoints → Backfill → Frontend

### Parallel Opportunities

```
Phase 1:  T001 ────────── T005 → T006 → T007 → T008 → T009
          T002 ──┐
          T003 ──┤ (parallel, different files)
          T004 ──┘

Phase 2:  T010 ──────────
          T011 ──┐
          T012 ──┤ (parallel, same file but different methods)
          T013 ──┘
          T014 (after T010)

Phase 3+: US1 ──┐
          US2 ──┤ (parallel by sprint)
                │
          US3 ──┤
          US4 ──┤ (parallel by sprint)
                │
          US5 ──┤
          US6 ──┘ (parallel by sprint)
```

---

## Parallel Example: Phase 1 Setup

```
# These can all run in parallel (different files):
Task T002: "Create situacao helper module in apps/api/lib/situacao.py"
Task T003: "Create URN-to-URL helper in apps/api/lib/urn.py"
Task T004: "Create tipo_relacao classifier in apps/api/lib/relacoes.py"

# Then sequentially:
Task T005: "Add columns to Proposicao model"
Task T006: "Add columns to Votacao model"
Task T007: "Add schemas"
```

## Parallel Example: US3 Tests

```
# All US3 tests can run in parallel:
Task T029: "Unit test for author matching"
Task T030: "Integration test for autores endpoint"
Task T031: "Integration test for parlamentar proposicoes"
```

---

## Implementation Strategy

### MVP First (US1 + US2 = Phase 1 features)

1. Complete Phase 1: Setup (T001–T009)
2. Complete Phase 2: Foundational (T010–T014)
3. Complete Phase 3: US1 — Situacao filters (T015–T021)
4. Complete Phase 4: US2 — Keywords + Lei + Aprovacao (T022–T028)
5. **STOP and VALIDATE**: Run backfill, verify 100% cod_situacao/keywords filled
6. Deploy — citizens can already filter and see enriched data

### Incremental Delivery

1. Setup + Foundational → backbone ready
2. Add US1 + US2 → Phase 1 features live (MVP!)
3. Add US3 + US4 → Authors and themes visible
4. Add US5 + US6 → Full legislative lifecycle
5. Polish → Progressive disclosure, re-sync, validation

### Sprint Mapping

| Sprint | User Stories | Duration |
|--------|-------------|----------|
| Sprint 1 | US1 + US2 (Phase 1 features) | ~2 days |
| Sprint 2 | US3 + US4 (Autores + Temas) | ~3 days |
| Sprint 3 | US5 + US6 (Cadeia + Orgao) + Polish | ~3 days |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All new columns nullable — no migration risk to existing data
- ADR-001: JSON not JSONB for SQLite compatibility
- ADR-002: Short imports (`from models import X`)
- ADR-003: JSON(none_as_null=True) for IS NOT NULL filtering
- Rate limit: 300ms between Camara API requests (already in CamaraClient)
- Backfill: 406 proposicoes x 4 calls x 300ms = ~8 min total
- Commit after each task or logical group of tasks

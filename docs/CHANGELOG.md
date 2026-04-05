# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions map to git tags (not yet created — pending deploy pipeline).

---

## [Unreleased]

### Added
- `scripts/discover_proposicoes.py`: script de descoberta de proposições via API da Câmara —
  busca por keywords das 9 categorias ZIL, classifica localmente, persiste com dados completos;
  suporta `--dry-run`, `--enriquecer`, e janela temporal customizada (`--ano-inicio`/`--ano-fim`)
- `packages/camara_client/__init__.py`: novo método `pesquisar_proposicoes()` com busca por keywords,
  iteração trimestral (restrição da API de 3 meses), e deduplicação por ID
- `apps/workers/tasks.py`: `task_enriquecer_pendentes` agora também processa proposições com
  `contexto_status = "pendente"` (além de `NULL`), integrando com o script de descoberta
- `packages/camara_client/__init__.py`: novo método `listar_votacoes_proposicao(proposicao_id)`
  para buscar votações de uma proposição específica via `GET /proposicoes/{id}/votacoes`
- `scripts/sync_votacoes_proposicoes.py`: script de sync de votações por proposição — itera
  todas as proposições no banco, busca votações na API da Câmara, sincroniza votações + votos
  individuais; suporta `--dry-run`, `--proposicao-id`, `--skip-with-votes`/`--no-skip`
- `scripts/sync_pipeline.py`: orquestrador dos 4 passos do pipeline — discovery → votação sync →
  enrichment → score recalculation; suporta `--skip-*` flags e `--dry-run`
- `tests/unit/test_camara_client.py`: testes unitários para `listar_votacoes_proposicao`
- `tests/unit/test_sync_votacoes.py`: testes unitários para `sync_votacoes_por_proposicao`
  com mock de CamaraClient — cobre criação, dedup, skip, dry-run, e classificação
- `tests/integration/test_pipeline_scoring.py`: teste de integração validando que
  `apply_direcoes` + `recalcular_todos_scores` atualiza `score_zil` corretamente

### Changed
- `scripts/apply_direcoes.py`: agora chama `recalcular_todos_scores(db)` automaticamente
  após aplicar direções (quando `--dry-run` não está ativo e houve atualizações) — elimina
  necessidade de recalcular scores manualmente

### Fixed
- **Enrichment API key loading**: `apps/workers/enrichment/__init__.py` now reads
  `ANTHROPIC_API_KEY` and `ENRICHMENT_MODEL` from `core.config.settings` instead of
  `os.getenv()` — fixes enrichment failure when shell environment has empty override
  that takes precedence over `.env` file (Pydantic BaseSettings priority: env > .env)
- **CORS**: `main.py` now uses `allow_origin_regex` to allow all `localhost:*` ports in
  development, fixing API calls from preview servers on dynamic ports
- **SQLite path**: `.env` now uses an absolute path for `DATABASE_URL` so the same
  database is used regardless of which directory the API server is launched from
- **env_file resolution**: `core/config.py` resolves `.env` relative to the config file
  location instead of the process cwd, making the launch.json config reliable

---

## [0.4.0] — 2026-04-02

Features 002–009 from the v1 backlog, all implemented in a single release.

### Added

#### 002 — Senado Federal ingestion
- `packages/senado_client/__init__.py`: `SenadoClient` with `listar_senadores()`,
  `listar_materias_ano()`, `listar_votacoes_materia()`, `obter_votos_votacao()`
- `apps/workers/crawlers/senado.py`: `sync_senadores()`, `sync_materias()`,
  `sync_votacoes_materia()`, `run_full_sync()` with `IngestionRun` audit trail
- Two new Celery tasks in `apps/workers/tasks.py`:
  - `task_sync_senadores` — weekly Monday 03:30
  - `task_sync_votacoes_senado` — every 6 hours at :30

#### 003 — Editorial workflow script
- `scripts/apply_direcoes.py`: loads `data/direcoes/*.yml`, matches by `fonte_id +
  fonte`, updates `Votacao.direcao_esperada` and `Votacao.peso`; supports `--ano`
  and `--dry-run` CLI flags

#### 004 — Frontend: /ranking
- Partido filter fetched live from `/parlamentares/partidos/ranking`
- Server-side filters: fonte, uf, partido, ordem (per_page=600)
- Client-side name search
- Skeleton loading (12 animated rows while fetching)
- Split display: scored parlamentares with rank numbers / unscored section (opacity-50)

#### 005 — Frontend: /parlamentar/[id]
- Per-category alignment breakdown with progress bars
- Clickable category cards to filter vote history
- "← Voltar ao ranking" navigation link
- Vote history table with alinhamento indicator per vote

#### 006 — Frontend: /proposicoes + detail pages
- Tipo filter (PL, PEC, PLP, MPV, PDL, PRC) and ano filter (last 10 years)
- Clickable rows link to `/proposicoes/[id]`
- `apps/web/app/proposicoes/[id]/page.tsx`: ementa, categories, situacao,
  url_inteiro_teor, votação list with placar and link to voting detail
- `apps/web/app/votacoes/[id]/page.tsx`: full voting record with per-parlamentar
  votes, filterable by vote type, each row links to `/parlamentar/[id]`

#### 007 — Frontend: /bussula
- Fetches `/bussula`, groups indicators by category
- `MarcoCard`: valor_atual, progress bar toward meta, tendência symbol, fonte link
- Empty state explains how to add indicators via YAML PR

#### 008 — Frontend: /metodologia
- Static page: score formula, weights table (3.0/2.0/1.0/0.5), gradient scale visual
- 9 category descriptions with examples, 5 limitations, editorial process

#### 009 — CI/CD
- `.github/workflows/ci.yml` rewritten with 4 jobs:
  - `test-backend`: pytest with pip cache
  - `lint-backend`: ruff only
  - `lint-frontend`: npm ci + ESLint + tsc --noEmit
  - `build-frontend`: next build (depends on lint-frontend)
- CI badge added to README

### Changed
- `apps/api/routers/parlamentares.py`: `per_page` limit raised from 100 to 600
- `apps/api/routers/legislativo.py`: added `GET /proposicoes/{id}/votacoes` and
  `GET /votacoes/{id}` endpoints
- `apps/api/routers/bussula.py`: new router reading `data/bussula/marcos.yml`
- `apps/api/requirements.txt`: added `pyyaml==6.0.2` (was missing, used by classifier)
- `apps/api/main.py`: registered `bussula` router

### Fixed
- Removed unused imports (`case`, `Field`, `func`, `FonteEnum`) that would fail ruff CI

---

## [0.3.0] — 2026-04-02

Feature 001 merged from branch `001-camara-api-ingestao`.

### Added
- `CLAUDE.md`: development guidelines, ADRs summary, coding conventions
- Enhanced `apps/api/models/__init__.py`: `IngestionRun`, `ScoreVotacao`, `Proposicao`
  models; `VotoEnum` with ausente/abstencao/obstrucao/artigo_17
- `apps/workers/crawlers/camara.py`: full sync with idempotent upsert,
  `IngestionRun` audit logging
- `apps/workers/scoring/__init__.py`: `recalcular_score_parlamentar()` with
  `ScoreVotacao` persistence; `recalcular_todos_scores()`
- `apps/workers/classifiers/__init__.py`: keyword classifier against
  `data/taxonomia/categorias.yml`; `relevancia_score()`
- `packages/camara_client/__init__.py`: retry logic, pagination, full deputy/
  voting/vote sync
- 98 tests across `tests/unit/`, `tests/integration/`, `tests/contract/`
- `tests/conftest.py`: SQLite in-memory fixtures (ADR-001)
- `specs/001-camara-api-ingestao/`: full Specify Kit spec set

---

## [0.2.0] — 2026-04-01

Homepage redesign and design system foundation.

### Added
- `apps/web/components/ui/`: Button, Badge, Card, Callout, SectionHeader
- `apps/web/components/NavBar.tsx`: responsive nav with hamburger menu on mobile
- `apps/web/components/ScoreExplainer.tsx`: visual score scale, weights, formula
- `apps/web/components/RankingPreview.tsx`: top/bottom 5 from API with skeleton + error
- `apps/web/components/CategoryGrid.tsx`: 9 ZIL category cards with filter links
- `apps/web/components/ManifestoSignature.tsx`: sign form + share button
- `apps/web/app/page.tsx`: new landing page composing all sections
- `apps/web/app/manifesto/page.tsx`: redirect to `/`
- `apps/web/tailwind.config.js`: `zil-*` design tokens (green, gold, cream, dark, orange)
- `apps/web/app/globals.css`: base typography and utility classes

### Removed
- `apps/web/app/page.jsx`: replaced by `page.tsx`; removed internal SPA router,
  mock data, inline styles, and duplicated nav/footer

---

## [0.1.0] — 2026-03-31

Initial scaffold.

### Added
- `apps/api/`: FastAPI app, SQLAlchemy models (Parlamentar, Votacao, Voto, Proposicao),
  Pydantic schemas, routers for parlamentares, legislativo
- `apps/workers/`: Celery app, task definitions with beat schedule, Câmara crawler stub,
  scoring engine stub, keyword classifier with `data/taxonomia/categorias.yml`
- `apps/web/`: Next.js 14 scaffold with TypeScript, Tailwind CSS, postcss
- `packages/camara_client/__init__.py`: Câmara API client stub
- `data/taxonomia/categorias.yml`: 9 ZIL categories with Portuguese/English keywords
- `docker-compose.yml`: api + worker + beat + redis + postgres services
- `docs/ARCHITECTURE.md`, `docs/PRD.md`, `docs/GOVERNANCE.md`: founding documents
- `pytest.ini`, `tests/test_classifier.py`, `tests/test_scoring.py`: initial test suite

---

[Unreleased]: https://github.com/melissa-pereira-deel/manifesto-zil/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/melissa-pereira-deel/manifesto-zil/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/melissa-pereira-deel/manifesto-zil/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/melissa-pereira-deel/manifesto-zil/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/melissa-pereira-deel/manifesto-zil/releases/tag/v0.1.0

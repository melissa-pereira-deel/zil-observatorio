# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions map to git tags (not yet created — pending deploy pipeline).

---

## [Unreleased]

### Added

#### Pipeline de dados — discovery, sync e orquestração
- `scripts/discover_proposicoes.py`: descoberta de proposições via API da Câmara —
  busca por keywords das 9 categorias ZIL, classifica localmente, persiste com dados
  completos; suporta `--dry-run`, `--enriquecer`, e janela temporal customizada
- `scripts/sync_votacoes_proposicoes.py`: sync de votações por proposição — itera
  proposições no banco, busca votações na API da Câmara, sincroniza votações + votos
  individuais; suporta `--dry-run`, `--proposicao-id`, `--skip-with-votes`/`--no-skip`
- `scripts/sync_pipeline.py`: orquestrador sequencial dos 4 passos do pipeline —
  discovery → votação sync → enrichment → score recalculation; suporta `--skip-*`
  flags individuais e `--dry-run` global
- `packages/camara_client/__init__.py`: novo método `pesquisar_proposicoes()` com
  busca por keywords, iteração trimestral (restrição da API), e deduplicação por ID
- `packages/camara_client/__init__.py`: novo método `listar_votacoes_proposicao()`
  para buscar votações de uma proposição específica via API da Câmara
- `apps/workers/tasks.py`: `task_enriquecer_pendentes` agora processa proposições
  com `contexto_status = "pendente"` (além de `NULL`)

#### UI/UX — credibilidade, acessibilidade e componentes compartilhados (UI-001 a UI-022)
- `components/ParlamentarAvatar.tsx`: componente reutilizável com fallback de iniciais
  quando foto está ausente ou falha ao carregar — suporta tamanhos sm/md/lg
- `components/DirecaoBadge.tsx`: badge de direção esperada (FAVORÁVEL/CONTRÁRIA) com
  link para /metodologia — usado em proposições e votações
- `components/ui/Badge.tsx`: sistema unificado de badges com variantes `category`,
  `status`, `result` — substitui badges ad hoc espalhados pelas páginas
- `lib/categorias.ts`: mapa centralizado de categorias ZIL com labels legíveis —
  elimina duplicação de strings de categoria em múltiplos componentes
- `ScoreGauge.tsx`: tooltip com âncora de credibilidade ("baseado em N votos ·
  ver metodologia →"), design tokens `zil-*` consolidados (UI-001, UI-016, UI-019)
- `ContextoBadge.tsx`: badge "Contexto pendente" removido da UI pública — aparece
  apenas quando `contexto_status === "pronto"` (UI-002)
- `ranking/page.tsx`: contagem de resultados acima da lista, empty state explicativo,
  busca textual na mesma linha dos filtros, remoção de decoração tipográfica (UI-003/004/005/006)
- `proposicoes/page.tsx`: contagem de resultados, empty state, unificação de filtros,
  remoção de letra decorativa (UI-003/004/005/006)
- `proposicoes/[id]/page.tsx`: síntese de posição ZIL ("ZIL avalia: FAVORÁVEL · com
  base em N votações"), `resultado` inferido de votos quando null, collapse nativo
  com `<details>/<summary>` (UI-010/011/012)
- `votacoes/[id]/page.tsx`: redesign com linguagem mais acessível, placar visual,
  filtro por tipo de voto, links para perfil do parlamentar
- `parlamentar/[id]/page.tsx`: hero metric zone com gauge + proporção em 2 colunas,
  legenda do duplo encoding (dot = alinhamento, badge = voto) com mini badge visual,
  affordance nos cards de categoria, frase de síntese interpretativa, remoção de
  score duplicado e código interno das categorias (UI-013 a UI-022)

#### Segurança — hardening de secrets
- `.pre-commit-config.yaml`: hooks `detect-secrets` (Yelp v1.5.0) e
  `detect-private-key` para bloquear commits com API keys ou chaves privadas
- `core/config.py`: validação de startup em produção — app recusa iniciar se
  variáveis obrigatórias estiverem ausentes ou se DATABASE_URL for SQLite
- `.gitignore`: catch-all para variantes `.env.*` (exceto `.env.example`) +
  padrões para chaves privadas, certificados e credenciais
- `.env.example`: contém apenas placeholders vazios com comentários instrutivos —
  nunca valores reais
- `docker-compose.yml`: credenciais substituídas por `${VAR:-default}` para
  carregamento seguro via `.env`
- `CLAUDE.md`: seção "Segurança e segredos" com 7 regras para manuseio de secrets

#### Feature 012 — Enriquecimento de Dados de Proposicoes
- `apps/api/models/__init__.py`: 12 novos campos em Proposicao (cod_situacao, regime,
  apreciacao, keywords_camara, urn_final, temas_camara, prop_principal/anterior/posterior_id,
  orgao_situacao, relator_id, detalhes_sincronizados_em) + 3 em Votacao (aprovacao,
  sigla_orgao, proposicao_objeto) + 2 novas tabelas (ProposicaoAutor, ProposicaoRelacao)
- `apps/api/lib/situacao.py`: helper para mapear 97 codSituacao em 4 grupos UI
- `apps/api/lib/urn.py`: parser de URN LexML para URLs do Planalto
- `apps/api/lib/relacoes.py`: classificador de siglaTipo em 9 categorias semanticas
- `apps/api/schemas/__init__.py`: 5 novos schemas (ParlamentarSnippet, CadeiaRead,
  TemaRead, AutorRead, RelacionadaRead) + expansao de ProposicaoRead e VotacaoRead
- `apps/api/routers/legislativo.py`: filtros regime/situacao_grupo em GET /proposicoes,
  campos computados (url_lei, situacao_grupo, cadeia) em respostas, 3 novos endpoints
  (autores, temas, relacionadas)
- `apps/api/routers/parlamentares.py`: novo endpoint GET /parlamentares/{id}/proposicoes
- `packages/camara_client/__init__.py`: 3 novos metodos (listar_autores_proposicao,
  listar_temas_proposicao, listar_relacionadas_proposicao)
- `scripts/migrate_012_detail_fields.py`: migracao idempotente em 3 fases
- `scripts/sync_detalhes_proposicoes.py`: backfill script com 3 fases
- `scripts/sync_pipeline.py`: novo Step 1.5 (detail sync) integrado ao pipeline
- `apps/web/lib/api.ts`: tipos TypeScript para todos os novos schemas + metodos API
- `apps/web/lib/proposicao.ts`: helpers de cor/label para situacao, regime, tipo_relacao
- `apps/web/components/AutoresLine.tsx`: sumario inline de autor com link para perfil
- `apps/web/components/CadeiaNode.tsx`: timeline visual de cadeia legislativa
- `apps/web/app/proposicoes/page.tsx`: filtros de situacao/regime, badges coloridos,
  autor na listagem
- `apps/web/app/proposicoes/[id]/page.tsx`: badges de situacao/regime/orgao/"VIROU LEI",
  autores, relator, keywords, temas, cadeia, resultado autoritativo de votacao,
  progressive disclosure com `<details>/<summary>`
- `apps/web/app/parlamentar/[parlamentar_id]/page.tsx`: secao "Proposicoes de autoria"

#### Testes
- `tests/unit/test_camara_client.py`: 6 testes para `listar_votacoes_proposicao`
  (retorno, lista vazia, resposta non-list, endpoint correto, mapeamento, campos opcionais)
- `tests/unit/test_sync_votacoes.py`: 6 testes para `sync_votacoes_por_proposicao`
  (criação, dedup, skip, dry-run, classificação, linking)
- `tests/integration/test_pipeline_scoring.py`: 3 testes end-to-end validando
  apply_direcoes + recalcular_todos_scores (score positivo, negativo, sem direção)
- `tests/unit/test_situacao.py`: 9 testes para mapeamento de codSituacao em grupos UI
- `tests/unit/test_urn.py`: 5 testes para parser URN → URL Planalto
- `tests/unit/test_relacoes.py`: 7 testes para classificador de tipo_relacao
- `tests/unit/test_proposicao_autores.py`: 4 testes para matching autor-parlamentar
- `tests/integration/test_detail_endpoints.py`: 29 testes para endpoints de autores,
  temas, relacionadas, cadeia, orgao/relator, filtros de situacao/regime
- Total: **205 testes passando**

#### Documentação
- `specs/002-legislative-enrichment-pipeline/`: spec completo com tasks.md (12 tasks),
  plan.md, contracts/api.md, data-model.md, quickstart.md, research.md
- `specs/ui-ux-credibility-polish/spec.md`: spec das 22 tasks UI/UX

### Changed
- `scripts/apply_direcoes.py`: agora chama `recalcular_todos_scores(db)` automaticamente
  após aplicar direções — elimina necessidade de recalcular scores manualmente
- `apps/api/routers/legislativo.py`: endpoints de proposições e votações retornam campos
  de enriquecimento (resumo_simples, categorias) em linguagem mais acessível
- `apps/api/routers/parlamentares.py`: campo de contagem de votos adicionado à resposta
- `apps/api/schemas/__init__.py`: novos schemas para campos de enriquecimento

### Fixed
- **Enrichment não executava**: `apps/workers/enrichment/__init__.py` usava `os.getenv()`
  para ler configurações — falha silenciosa quando variável de ambiente vazia sobrescreve
  o `.env` (Pydantic BaseSettings dá precedência a env vars). Corrigido para usar
  `core.config.settings` consistentemente com o resto do codebase. 406 proposições
  enriquecidas com sucesso após a correção.
- **CORS em dev**: `main.py` agora usa `allow_origin_regex` para aceitar qualquer porta
  localhost, corrigindo chamadas de API de preview servers em portas dinâmicas
- **Caminho SQLite**: DATABASE_URL usa caminho absoluto — mesmo banco independente
  do diretório de execução
- **Resolução de .env**: `core/config.py` resolve `.env` relativo ao arquivo de config,
  não ao cwd do processo
- **Proxy Next.js → FastAPI**: `next.config.js` com rewrite para que preview no browser
  alcance a API backend

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

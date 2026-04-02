# Tasks: Ingestão da API da Câmara dos Deputados

**Input**: Design documents from `/specs/001-camara-api-ingestao/`
**Branch**: `001-camara-api-ingestao`
**Date**: 2026-04-01

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1/US2/US3]**: User story this task belongs to
- Exact file paths in all descriptions

---

## Phase 1: Setup

**Purpose**: Estrutura de testes e diretórios ainda não existentes

- [ ] T001 Criar diretórios `tests/unit/`, `tests/integration/`, `tests/contract/` com arquivos `__init__.py`
- [ ] T002 [P] Criar `tests/conftest.py` com fixtures: `db_session` (SQLite em memória), `client` (FastAPI TestClient), dados seed mínimos (1 parlamentar, 1 votação ZIL com `direcao_esperada`, 1 voto)

**Checkpoint**: `pytest tests/` roda sem erros de importação (zero testes coletados é OK)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura base que TODAS as user stories dependem

⚠️ **CRITICAL**: Nenhuma user story pode começar antes desta fase

- [ ] T003 Adicionar modelo `IngestionRun` em `apps/api/models/__init__.py` — campos: `id`, `tipo`, `ano`, `status`, `iniciado_em`, `finalizado_em`, `registros_processados`, `registros_criados`, `registros_atualizados`, `erros_count`, `erro_detalhes` (JSONB) — sem FKs, índice em `(tipo, status, iniciado_em DESC)`
- [ ] T004 Adicionar `UniqueConstraint("parlamentar_id", "votacao_id", name="uq_score_parlamentar_votacao")` em `ScoreVotacao.__table_args__` em `apps/api/models/__init__.py` (verificar se já existe antes)
- [ ] T005 [P] Atualizar `CamaraClient._get` em `packages/camara_client/__init__.py` para backoff exponencial: delay `2.0 * (2 ** attempt)` (2s → 4s → 8s) em vez do delay linear atual
- [ ] T006 [P] Adicionar método `obter_votacao_orientacoes(votacao_id: str) -> list[dict]` em `packages/camara_client/__init__.py` — `GET /votacoes/{id}/orientacoes`
- [ ] T007 Criar `apps/workers/tasks.py` com: instância Celery (`app = Celery("workers", broker=settings.REDIS_URL)`), stubs vazios para `sync_votacoes_task` e `sync_deputados_task`, beat schedule com crontab (`*/6` horas e segunda às 03:00) — sem lógica de negócio ainda

**Checkpoint**: Modelos criados; `from apps.api.models import IngestionRun` funciona; `from apps.workers.tasks import app` funciona

---

## Phase 3: User Story 1 — Cidadão consulta o Score ZIL (Priority: P1) 🎯 MVP

**Goal**: Ingerir deputados + votações 2024–presente, classificar, calcular Score ZIL e expor via `/parlamentares`

**Independent Test**: `pytest tests/unit/test_scoring.py tests/integration/test_api_parlamentares.py` passa; `/parlamentares?uf=GO` retorna deputados com `score_zil` após ingestão manual

### Testes para US1 (obrigatórios — Princípio VII) ⚠️

> **Escrever ANTES da implementação. Devem FALHAR primeiro.**

- [ ] T008 [P] [US1] Criar `tests/unit/test_scoring.py`:
  - `test_calcular_alinhamento_sim_esperado_sim()` → retorna +1.0
  - `test_calcular_alinhamento_nao_esperado_sim()` → retorna -1.0
  - `test_calcular_alinhamento_ausente()` → retorna 0.0
  - `test_recalcular_score_sem_votos_zil()` → retorna None
  - `test_recalcular_score_alinhamento_total()` → retorna +10.0
  - `test_recalcular_score_contra_total()` → retorna -10.0
  - `test_recalcular_score_misto()` → retorna valor entre -10 e +10

- [ ] T009 [P] [US1] Criar `tests/unit/test_classifier.py`:
  - `test_classificar_votacao_com_termo_zil_fer()` → retorna `["ZIL-FER"]`
  - `test_classificar_votacao_sem_termos_zil()` → retorna `[]`
  - `test_classificar_proposicao_multiplas_categorias()` → retorna 2+ categorias
  - `test_relevancia_score_sem_termos()` → retorna 0.0

- [ ] T010 [P] [US1] Criar `tests/integration/test_api_parlamentares.py` (usar fixture `client` do conftest):
  - `test_listar_parlamentares_vazio()` → resposta 200, lista vazia
  - `test_listar_parlamentares_com_dados()` → seed com 3 parlamentares, retorna 3
  - `test_filtro_por_uf()` → seed SP+GO, filtro `?uf=SP` retorna só SP
  - `test_filtro_por_partido()` → seed PT+PL, filtro `?partido=PT` retorna só PT
  - `test_ordenacao_score_desc()` → retorna ordenado por score decrescente
  - `test_obter_parlamentar_nao_encontrado()` → 404
  - `test_votos_zil_parlamentar()` → fixture com 1 voto ZIL, retorna lista com `alinhado` correto
  - `test_votos_zil_filtro_categoria()` → retorna apenas votos da categoria solicitada

- [ ] T011 [US1] Criar `tests/integration/test_crawler_idempotency.py`:
  - `test_sync_deputados_idempotente()` → rodar sync 2× com mesmos dados, COUNT(*) igual
  - `test_sync_votacoes_idempotente()` → rodar sync 2×, COUNT(*) FROM votos igual
  - `test_voto_stub_parlamentar_criado()` → voto de suplente cria parlamentar stub sem erro

### Implementação de US1

- [ ] T012 [US1] Atualizar `sync_votacoes` em `apps/workers/crawlers/camara.py`:
  - Após criar `Votacao`, chamar `client.obter_votacao_detalhes(vot.id)` para extrair `proposicaoPrincipal`
  - Fazer upsert da `Proposicao` associada (`fonte_id`, `tipo`, `numero`, `ano`, `ementa`) — criar ou atualizar se existe
  - Preencher `votacao.proposicao_id` com o UUID interno da proposição upsertada
  - Classificar combinando `vot.descricao + proposicao.ementa` para melhor cobertura (FR-004)

- [ ] T013 [US1] Atualizar `sync_votacoes` em `apps/workers/crawlers/camara.py`:
  - Chamar `client.obter_votacao_orientacoes(vot.id)` uma vez por votação
  - Construir `dict[partido → orientacao_str]` das orientações
  - Preencher `voto.orientacao_partido` ao criar cada `Voto`

- [ ] T014 [US1] Atualizar `run_full_sync` em `apps/workers/crawlers/camara.py`:
  - Aceitar `anos: list[int] | None` (padrão: `range(2024, current_year + 1)`)
  - Iterar `for ano in anos: sync_votacoes(db, ano=ano)`
  - Registrar `IngestionRun` ao início (`status="running"`) e atualizar ao final (`status="success"` ou `"failed"`)
  - Incrementar `registros_criados` / `registros_atualizados` / `erros_count` ao longo do loop
  - Em exceção não recuperável: atualizar `status="failed"`, `erro_detalhes=[{...}]`, re-raise

- [ ] T015 [US1] Atualizar `recalcular_todos_scores` em `apps/workers/scoring/__init__.py`:
  - No loop por voto, após calcular `alinhamento`, criar/atualizar registro `ScoreVotacao`:
    - `categoria_zil` = `votacao.categorias_zil[0]` (categoria principal)
    - `impacto` = `alinhamento`
    - `peso` = `votacao.peso or 1.0`
    - `justificativa` = `f"Voto: {voto.voto.value} | Esperado: {votacao.direcao_esperada}"`
  - Usar `INSERT ... ON CONFLICT (parlamentar_id, votacao_id) DO UPDATE` (ou select-then-upsert)

**Checkpoint US1**: `pytest tests/unit/ tests/integration/test_api_parlamentares.py tests/integration/test_crawler_idempotency.py` passa; executar `python apps/workers/crawlers/camara.py 2024` completa sem erro

---

## Phase 4: User Story 2 — Jornalista exporta dados via API (Priority: P2)

**Goal**: Endpoints `/proposicoes`, `/votacoes` com filtros funcionais e sem autenticação

**Independent Test**: `pytest tests/integration/test_api_legislativo.py tests/contract/test_api_schema.py` passa; `curl localhost:8000/proposicoes?categoria=ZIL-MIN` retorna JSON bem-formado sem token

### Testes para US2 (obrigatórios — Princípio VII) ⚠️

- [ ] T016 [P] [US2] Criar `tests/integration/test_api_legislativo.py`:
  - `test_listar_proposicoes_vazio()` → 200, lista vazia
  - `test_filtro_proposicoes_por_categoria()` → seed 2 proposições, 1 ZIL-MIN, filtro retorna 1
  - `test_filtro_proposicoes_por_tipo()` → seed PL + PEC, filtro `?tipo=PL` retorna só PL
  - `test_listar_votacoes_por_ano()` → seed 2024 + 2025, filtro `?ano=2024` retorna só 2024
  - `test_filtro_votacoes_por_categoria()` → seed ZIL-MIN + ZIL-ENE, filtro retorna correto
  - `test_votos_da_votacao()` → seed votação com 3 votos, retorna 3 com campos corretos
  - `test_votacao_nao_encontrada()` → 404
  - `test_parametro_invalido_retorna_422()` → query param inválido → 422

- [ ] T017 [P] [US2] Criar `tests/contract/test_api_schema.py`:
  - `test_schema_parlamentar_ranking()` → campos obrigatórios: `id`, `nome`, `partido`, `uf`, `fonte`, `score_zil`, `total_votos_zil`
  - `test_schema_voto_historico()` → campos: `votacao_id`, `data`, `descricao`, `categorias_zil`, `voto`, `alinhado`
  - `test_schema_proposicao_read()` → campos: `id`, `fonte_id`, `tipo`, `numero`, `ano`, `ementa`, `categorias_zil`
  - `test_schema_votacao_read()` → campos: `id`, `data`, `descricao`, `resultado`, `categorias_zil`, `peso`

### Implementação de US2

- [ ] T018 [US2] Verificar `apps/api/routers/legislativo.py` — endpoint `GET /proposicoes`:
  - Confirmar que `Proposicao.categorias_zil.any(categoria)` funciona corretamente com PostgreSQL ARRAY
  - Garantir que proposições sem categorias ZIL (classificadas mas não como ZIL) não vazam na listagem

- [ ] T019 [US2] Verificar `apps/api/routers/legislativo.py` — endpoint `GET /votacoes/{id}/votos`:
  - Confirmar que o join `Voto ↔ Parlamentar` retorna `orientacao_partido` preenchido
  - Confirmar ordenação por `Parlamentar.nome`

**Checkpoint US2**: `pytest tests/integration/test_api_legislativo.py tests/contract/test_api_schema.py` passa; todos endpoints sem autenticação (Princípio I verificado)

---

## Phase 5: User Story 3 — Operador monitora a saúde da ingestão (Priority: P3)

**Goal**: `/stats` retorna `ultima_atualizacao`; Celery beat roda votações 6h e deputados semanal; retry automático em falha

**Independent Test**: `pytest tests/integration/test_api_stats.py` passa; iniciar `celery beat` não gera erro de importação

### Testes para US3 (obrigatórios — Princípio VII) ⚠️

- [ ] T020 [P] [US3] Criar `tests/integration/test_api_stats.py`:
  - `test_stats_sem_ingestion_run()` → `ultima_atualizacao` é `null`
  - `test_stats_com_ingestion_run_success()` → seed `IngestionRun(status="success")`, `ultima_atualizacao` retorna timestamp correto
  - `test_stats_ignora_ingestion_run_failed()` → seed só com `status="failed"`, `ultima_atualizacao` é `null`
  - `test_stats_campos_obrigatorios()` → resposta tem `total_parlamentares`, `total_deputados`, `total_votacoes_zil`, `score_medio`, `ultima_atualizacao`

### Implementação de US3

- [ ] T021 [US3] Atualizar `GET /stats` em `apps/api/routers/legislativo.py`:
  - Adicionar query para `IngestionRun`: `SELECT MAX(finalizado_em) WHERE status='success'`
  - Retornar `ultima_atualizacao` no response JSON
  - Atualizar schema `StatsGeral` em `apps/api/schemas/__init__.py` para incluir `ultima_atualizacao: Optional[datetime]`

- [ ] T022 [US3] Completar `apps/workers/tasks.py` com lógica de negócio:
  - `sync_deputados_task`: chama `sync_deputados(db)` + `IngestionRun` tracking
  - `sync_votacoes_task`: chama `run_full_sync(db, anos=[current_year])` com `IngestionRun`
  - Adicionar `autoretry_for=(Exception,)`, `max_retries=3`, `retry_backoff=True`, `retry_backoff_max=600` (10min)
  - Adicionar logging estruturado: início, fim, contadores, erros

- [ ] T023 [US3] Verificar que `docker-compose.yml` tem serviços `worker` e `beat` com `celery -A apps.workers.tasks worker/beat` corretos — ajustar paths se necessário

**Checkpoint US3**: `pytest tests/integration/test_api_stats.py` passa; `celery -A apps.workers.tasks inspect registered` lista as 2 tasks; beat schedule sem erros de importação

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Qualidade final, mypy, ruff, integração end-to-end

- [ ] T024 [P] Rodar `mypy apps/api/ apps/workers/ packages/ --strict` e corrigir todos os erros de tipo — foco em `Optional`, `UUID` vs `str`, retornos de `recalcular_score_parlamentar`
- [ ] T025 [P] Rodar `ruff check apps/ packages/ --fix` e corrigir warnings restantes
- [ ] T026 Validar `quickstart.md` do início ao fim em ambiente limpo: subir Docker, rodar ingestão de 2024, verificar `/stats`, verificar `/parlamentares?uf=SP`
- [ ] T027 [P] Atualizar `CLAUDE.md` via `.specify/scripts/bash/update-agent-context.sh claude` após todas as mudanças de stack

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências — pode começar imediatamente
- **Foundational (Phase 2)**: Depende do Setup — BLOQUEIA todas as user stories
- **US1 (Phase 3, P1)**: Depende da Foundational — MVP crítico
- **US2 (Phase 4, P2)**: Depende da Foundational; pode começar em paralelo com US1
- **US3 (Phase 5, P3)**: Depende de US1 (requer `IngestionRun` preenchido)
- **Polish (Phase 6)**: Depende de todas as user stories

### Within Each User Story

- Testes escritos primeiro (devem FALHAR antes da implementação)
- Modelos antes de serviços; serviços antes de endpoints
- Verificar checkpoint antes de avançar para próxima fase

### Parallel Opportunities

```bash
# Phase 2 — rodar em paralelo:
T005  # Backoff exponencial em CamaraClient
T006  # Método obter_votacao_orientacoes

# Phase 3 — testes em paralelo antes de implementar:
T008  # test_scoring.py
T009  # test_classifier.py
T010  # test_api_parlamentares.py

# Phase 4 — testes em paralelo:
T016  # test_api_legislativo.py
T017  # test_api_schema.py

# Phase 6 — em paralelo:
T024  # mypy
T025  # ruff
T027  # update CLAUDE.md
```

---

## Implementation Strategy

### MVP (US1 only)

1. Fase 1: Setup (T001–T002)
2. Fase 2: Foundational (T003–T007)
3. Fase 3: US1 — testes primeiro (T008–T011), depois implementação (T012–T015)
4. **VALIDAR**: `pytest tests/unit/ tests/integration/test_api_parlamentares.py` passa + ingestão manual de 2024 completa
5. Deploy alpha com dados reais

### Entrega Incremental

1. Setup + Foundational → estrutura pronta
2. US1 → deputados + scores + ranking funcional (MVP!)
3. US2 → proposições + votações + filtros para jornalistas
4. US3 → observabilidade + agendamento automático
5. Polish → pronto para contribuidores externos

---

## Notes

- `[P]` = arquivos diferentes, sem dependências entre si — rodar em paralelo
- `[US1/US2/US3]` = rastreabilidade com a user story
- Testes obrigatórios por Princípio VII: `test_scoring.py`, `test_classifier.py`, `test_api_parlamentares.py`, `test_api_legislativo.py`, `test_api_stats.py`
- `score_zil` NULL é esperado na v0 — `direcao_esperada` das votações depende do comitê editorial
- Commits por task ou grupo lógico seguindo `feat:`, `fix:`, `test:`, `chore:` conforme `CLAUDE.md`

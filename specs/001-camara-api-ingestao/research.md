# Phase 0 Research: Ingestão da API da Câmara dos Deputados

**Feature**: `001-camara-api-ingestao`
**Date**: 2026-04-01
**Status**: Complete — todas as questões resolvidas

---

## 1. Gap Analysis: scaffold atual vs. spec

| Requisito (FR) | Estado atual | Lacuna identificada |
|----------------|-------------|---------------------|
| FR-001: Perfil deputados | ✅ `sync_deputados` funcional | Sem `IngestionRun` tracking |
| FR-002: Votações 2024–presente | ⚠️ `sync_votacoes(ano)` só processa 1 ano | Precisa loop 2024→ano atual |
| FR-003: Voto individual por deputado | ✅ `obter_votos` + mapeamento VotoEnum | Falta `orientacao_partido` (disponível na API) |
| FR-004: Classificar por categoria ZIL | ✅ `classificar_votacao` funcional | Precisa classificar também via ementa da proposição vinculada |
| FR-005: Calcular Score ZIL | ✅ `recalcular_score_parlamentar` funcional | Não persiste `ScoreVotacao` records (impacto por voto) |
| FR-006: Idempotência | ✅ upsert por `fonte_id` + `fonte` | Verificado; re-execução não duplica |
| FR-007: API REST pública | ✅ endpoints existem | `ultima_atualizacao` ausente em `/stats` |
| FR-008: Agendamento automático | ❌ ausente | Celery beat não configurado |
| FR-009: Logs estruturados | ⚠️ logging básico | Sem modelo `IngestionRun` no banco |
| FR-010: Preservar dados em falha | ✅ commit a cada 10 votações | Backoff exponencial incompleto (linear hoje) |

**Conclusão**: Scaffold cobre ~60% dos requisitos. As 5 lacunas críticas são:
1. Loop multi-ano na ingestão de votações
2. Modelo `IngestionRun` para observabilidade
3. `ScoreVotacao` records no scoring engine
4. Celery beat schedule
5. `ultima_atualizacao` no endpoint `/stats`

---

## 2. API da Câmara — comportamento e limitações

**Fonte**: documentação Swagger em `dadosabertos.camara.leg.br/swagger/api.html`

### Rate limiting
- A API pública da Câmara não documentou formalmente rate limits
- Comportamento observado: respostas 429 ocasionais sob carga alta
- Estratégia conservadora adotada: `time.sleep(0.5)` entre páginas (já implementada
  em `_get_paginated`) + retry linear existente no `_get`
- **Decisão**: evoluir retry de linear para exponencial: 30s → 2min → 10min (conforme FR edge cases)

### Paginação
- Endpoint `/deputados`: máx. 100 itens/página, ~5-6 páginas para 513 deputados
- Endpoint `/votacoes`: máx. 100 itens/página, ~10-20 páginas/ano
- Endpoint `/votacoes/{id}/votos`: retorna todos os votos em um único request (sem paginação)
- `_get_paginated` já implementa loop com `max_pages=50` — suficiente

### Proposição vinculada a votação
- `GET /votacoes/{id}` retorna campo `proposicaoPrincipal` com `{id, siglaTipo, numero, ano, titulo}`
- Para classificar melhor: buscar `GET /proposicoes/{proposicao_id}` para obter ementa completa
- **Decisão**: no `sync_votacoes`, após criar a `Votacao`, chamar `obter_votacao_detalhes` para
  extrair o `proposicao_id` e fazer upsert da `Proposicao` associada. Classificar combinando
  `descricao_votacao + ementa_proposicao` para melhor cobertura do FR-004.

### Orientação do partido por voto
- `GET /votacoes/{id}/votos` retorna campo `tipoVoto` mas NÃO retorna orientação do partido
- Orientação do partido está em `GET /votacoes/{id}/orientacoes` (endpoint separado)
- **Decisão**: chamar `/orientacoes` uma vez por votação e fazer join pelo partido no mapeamento de votos
- Campo `orientacao_partido` em `Voto` será preenchido quando disponível

### Período de ingestão
- 57ª Legislatura: 2023-02-01 a 2027-01-31
- Spec pede 2024-01-01 até hoje
- **Decisão**: `run_full_sync` itera `for ano in range(2024, current_year + 1)`
- Verificação: executar `sync_deputados` primeiro (garante que todos os parlamentares existem),
  depois `sync_votacoes` para cada ano em ordem crescente

---

## 3. Estratégia de retry com backoff exponencial

**Problema atual**: `_get` em `camara_client` usa retry linear (2s × tentativa). O spec
define: 30s → 2min → 10min para falha completa do worker.

**Dois níveis de retry**:

1. **Nível request** (em `CamaraClient._get`): para erros transitórios (429, 5xx, timeout)
   - Retry 3×: delays 2s → 4s → 8s (backoff exponencial base 2)
   - Escopo: retry da requisição HTTP individual

2. **Nível worker** (em Celery task): para falha completa da tarefa de ingestão
   - `autoretry_for = (Exception,)` com `retry_backoff=True`, `max_retries=3`
   - Delays Celery: 30s → 2min → 10min (usando `retry_backoff_max`)
   - Escopo: retry do job inteiro de ingestão

**Decisão**: Atualizar `CamaraClient._get` para backoff exponencial (2×). Adicionar
retry Celery na task com os intervalos especificados no edge case do spec.

---

## 4. Modelo IngestionRun

**Necessidade**: FR-009 + FR-010 + User Story 3 (observabilidade).

**Campos necessários**:
```
id              UUID PK
tipo            str  ("deputados" | "votacoes" | "full_sync")
ano             int? (None para sync de deputados)
status          str  ("running" | "success" | "failed" | "partial")
iniciado_em     datetime
finalizado_em   datetime?
registros_processados int default 0
registros_criados     int default 0
registros_atualizados int default 0
erros_count           int default 0
erro_detalhes         text? (JSON com lista de erros)
```

**Uso**: `IngestionRun` é criado no início de cada execução, atualizado ao final.
O endpoint `/stats` lê o `IngestionRun` mais recente com `status="success"` para
retornar `ultima_atualizacao`.

**Não precisa de relacionamentos** — é uma tabela de log, sem FKs para outras tabelas.

---

## 5. ScoreVotacao records no scoring engine

**Problema atual**: `recalcular_todos_scores` calcula o score mas não persiste
`ScoreVotacao` records. A tabela existe no modelo mas não é preenchida.

**Decisão**: No loop de `recalcular_score_parlamentar`, após calcular `alinhamento * peso`
para cada voto, fazer upsert em `ScoreVotacao`:
- `(parlamentar_id, votacao_id)` — chave de idempotência (adicionar UniqueConstraint)
- `categoria_zil` — primeira categoria da lista `categorias_zil` da votação
- `impacto` = `alinhamento` (-1.0, 0.0, +1.0)
- `peso` = `votacao.peso`
- `justificativa` = f"Voto: {voto.voto.value} | Esperado: {votacao.direcao_esperada}"

Isso viabiliza o endpoint futuro `/parlamentares/{id}/score-detalhado` sem nova ingestão.

---

## 6. Celery beat schedule

**Decisão**: criar `apps/workers/tasks.py` com:

```python
# Task de ingestão de votações — a cada 6 horas
@app.task(bind=True, name="workers.sync_votacoes_task")
def sync_votacoes_task(self):
    ...

# Task de sync de deputados — semanal
@app.task(bind=True, name="workers.sync_deputados_task")
def sync_deputados_task(self):
    ...

# Beat schedule
app.conf.beat_schedule = {
    "sync-votacoes-every-6h": {
        "task": "workers.sync_votacoes_task",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "sync-deputados-weekly": {
        "task": "workers.sync_deputados_task",
        "schedule": crontab(minute=0, hour=3, day_of_week=1),  # Segunda às 03:00
    },
}
```

`celery -A apps.workers.tasks worker` + `celery -A apps.workers.tasks beat`
(já definidos no `docker-compose.yml` como serviços `worker` e `beat`).

---

## 7. Idempotência — verificação completa

O scaffold usa `fonte_id + fonte` como chave de idempotência em todas as tabelas:

| Tabela | UniqueConstraint | Estratégia |
|--------|-----------------|------------|
| parlamentares | `(fonte_id, fonte)` | select-then-upsert |
| proposicoes | `(fonte_id, fonte)` | select-then-upsert |
| votacoes | `(fonte_id, fonte)` | skip se existente |
| votos | `(votacao_id, parlamentar_id)` | `INSERT ... ON CONFLICT DO NOTHING` |
| scores_votacao | `(parlamentar_id, votacao_id)` | upsert ao recalcular |
| ingestion_runs | — | insert always (log imutável) |

**Verificação de SC-003**: após re-execução, `SELECT COUNT(*) FROM votos` deve retornar
o mesmo valor. Coberto pelo teste `test_crawler_idempotency.py`.

---

## 8. Questões resolvidas (sem NEEDS CLARIFICATION)

| Questão | Decisão |
|---------|---------|
| Multi-ano ingestão | Loop 2024 → current_year em `run_full_sync` |
| Proposição link | `obter_votacao_detalhes` após criar Votação |
| Retry backoff | Exponencial base 2 em `_get`; Celery autoretry 30s/2min/10min |
| IngestionRun | Nova tabela, sem FKs, atualiza `/stats.ultima_atualizacao` |
| ScoreVotacao | Upsert por `(parlamentar_id, votacao_id)` ao recalcular |
| Celery beat | `tasks.py` com crontab 6h (votações) + weekly (deputados) |
| orientacao_partido | `/votacoes/{id}/orientacoes` endpoint separado |
| Peso das votações | Default 1.0; editorial define 3.0/2.0/0.5 via YAML futuro |

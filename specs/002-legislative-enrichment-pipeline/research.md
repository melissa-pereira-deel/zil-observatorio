# Research: Pipeline de Enriquecimento Legislativo Completo

**Date**: 2026-04-04

## R1 — Câmara API: Votações por Proposição

**Decision**: Use `GET /proposicoes/{id}/votacoes` endpoint to fetch all votações for a given proposição.

**Rationale**: Empirically verified — the endpoint returns full votação data including `id`, `data`, `descricao`, `aprovacao`. For PL 327/2021 (API id 2269745), it returns 28 votações. The existing `obter_votos(votacao_id)` method already handles individual vote fetching. Only missing piece is the proposição→votação link.

**Alternatives considered**:
- Cross-referencing the year-based `listar_votacoes(ano)` output with proposição IDs — too slow (thousands of votações per year), and the API doesn't reliably include `proposicaoPrincipal` in listing responses.
- Using the `proposicoesAfetadas` field from votação details — only works in reverse (votação→proposição), not for discovering which votações affect a known proposição.

**Verification**: Tested live against Câmara API:
- `GET /proposicoes/2269745/votacoes` → 200 OK, 28 results
- Scanned 401 new proposições: 126 (31%) have votações available
- Rate of ~2 requests/sec is sustainable (300ms delay between requests)

---

## R2 — Votação Deduplication Strategy

**Decision**: Rely on existing `UniqueConstraint(fonte_id, fonte)` on the `votacoes` table. Before creating a votação, check if `fonte_id` already exists.

**Rationale**: The same votação can be discovered via three paths: (a) year-based `sync_votacoes(ano)`, (b) proposição-based `/proposicoes/{id}/votacoes`, (c) YAML-based `sync_votacoes_zil.py`. All three use the Câmara API votação ID as `fonte_id`. The existing unique constraint guarantees no duplicates.

**Alternatives considered**:
- Composite dedup on `(data, descricao, proposicao_id)` — fragile, descriptions may vary between API responses.
- Separate staging table before upsert — over-engineered for this scale (hundreds, not millions).

---

## R3 — Orchestration Pattern

**Decision**: Sequential script (`sync_pipeline.py`) that calls each module in order, with each step producing a summary dict consumed by the next. No new infrastructure (no Airflow, no DAG engine).

**Rationale**: The pipeline runs at most daily. Current scale is ~400 proposições. A simple Python script with logging and error handling is sufficient. Each step is already idempotent, so partial failures can be resumed by re-running the pipeline.

**Alternatives considered**:
- Celery chain/chord — adds complexity without benefit at this scale. Individual tasks already exist for async execution; the orchestrator is for manual/cron batch runs.
- Airflow/Prefect — massive infrastructure overhead for a 4-step sequential pipeline. Would violate constitution principle VII (quality without gatekeeping).

**Pipeline sequence**:
```
Step 1: discover_proposicoes.py  → N new proposições
Step 2: sync_votacoes_proposicoes.py  → M votações + votos synced
Step 3: enrichment (task_enriquecer_pendentes or inline)  → K enriched
Step 4: apply_direcoes.py + recalcular_scores  → scores updated (if editorial direction exists)
```

---

## R4 — Rate Limiting for Câmara API Bulk Operations

**Decision**: 300ms delay between individual requests. Each proposição requires 1 request for votação list + N requests for individual votes (one per votação). Use a shared `CamaraClient` instance to benefit from connection pooling.

**Rationale**: Empirically tested. The Câmara API returns 429 at ~10 req/s sustained. 300ms between requests = ~3.3 req/s, well under the limit. For 126 proposições with votações, worst case:
- 126 votação list requests × 0.3s = ~38s
- ~300 individual votação detail + vote fetch calls × 0.3s = ~90s
- Total: ~2-3 minutes for full sync

**Alternatives considered**:
- Async (aiohttp) for parallel requests — risk of hitting rate limits. Sequential is safer and fast enough.
- Batch API if available — Câmara API doesn't support batch endpoints.

---

## R5 — CamaraClient Method Design

**Decision**: Add `listar_votacoes_proposicao(proposicao_id: int) -> list[VotacaoAPI]` to `CamaraClient`. Returns list of `VotacaoAPI` dataclasses (same as `listar_votacoes`).

**Rationale**: Follows existing client patterns. The method calls `GET /proposicoes/{proposicao_id}/votacoes` and maps response to existing `VotacaoAPI` dataclass. No new dataclasses needed.

**API response format** (verified):
```json
{
  "dados": [
    {
      "id": "2269745-148",
      "data": "2024-12-18",
      "descricao": "Aprovada a Redação Final...",
      "aprovacao": true
    }
  ]
}
```

---

## R6 — Score Recalculation Trigger

**Decision**: `apply_direcoes.py` calls `recalcular_todos_scores(db)` at the end of its execution. The daily Celery beat task at 04:00 remains as safety net.

**Rationale**: Editors only run `apply_direcoes.py` when they add direction to votações. This is infrequent (weekly at most). Recalculating immediately gives editors instant feedback. The daily schedule catches any edge cases.

**Alternatives considered**:
- Event-driven (Celery signal on votação update) — over-engineered; `apply_direcoes.py` is already the single entry point for direction changes.
- Only daily schedule — editors wait up to 24h to see impact of their curation. Unacceptable for iterative editorial work.

---

## R7 — Sync Script Design: sync_votacoes_proposicoes.py

**Decision**: New script that iterates all proposições in the DB, fetches their votações from the API, and syncs votações + votos that don't yet exist.

**Design**:
```python
def sync_votacoes_por_proposicao(db, proposicao_ids=None, skip_existing=True):
    """
    For each proposição (or subset), fetch votações from Câmara API
    and sync votações + individual votos.

    Args:
        proposicao_ids: Specific proposição IDs to sync (default: all with fonte=CAMARA)
        skip_existing: Skip proposições that already have ≥1 votação linked (default: True)
    """
```

**Key behaviors**:
- Deduplicates via `fonte_id` unique constraint
- Fetches individual votes for each new votação (reuses `obter_votos` from CamaraClient)
- Classifies each votação with `classificar_votacao(descricao)` for `categorias_zil`
- Does NOT set `direcao_esperada` (editorial-only field)
- Commits per-proposição to avoid large transactions
- Logs progress: `Synced 5 votações + 2150 votos for PL 327/2021`

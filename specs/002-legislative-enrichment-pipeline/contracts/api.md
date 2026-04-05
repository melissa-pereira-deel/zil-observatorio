# API Contracts: Pipeline de Enriquecimento Legislativo

## Existing Endpoints (no changes to contract)

### GET /proposicoes
Returns list of `ProposicaoRead`. Already includes `contexto_status`, `resumo_simples`, `confianca` fields.

### GET /proposicoes/{id}
Returns `ProposicaoRead` for a single proposição.

---

## Enrichment Endpoints

### GET /proposicoes/{id}/contexto

Returns enrichment context for a proposição.

**Response schema**: `ProposicaoContexto`

```json
{
  "proposicao_id": "uuid",
  "ementa_original": "string | null",
  "contexto_status": "pendente | processando | pronto | falhou | llm_falhou | null",
  "resumo_simples": "string | null",
  "glossario": {"term": "definition"} | null,
  "impacto_zil": "string | null",
  "leis_referenciadas": [
    {
      "lei_id": "14744-2023",
      "numero_artigo": "3",
      "url_planalto": "https://www.planalto.gov.br/...",
      "status": "resolvido | revogada | nao_encontrada | pdf_nao_parseavel | timeout",
      "texto_snippet": "string | null"
    }
  ] | null,
  "confianca": 0.85,
  "enriquecido_em": "2026-04-04T12:00:00Z | null",
  "versao_pipeline": "1.0",
  "modelo_llm": "claude-haiku-4-5-20251001 | null",
  "fontes": ["https://www.planalto.gov.br/..."]
}
```

**Status codes**:
- 200: Always returned (even for pending/failed enrichment)
- 404: Proposição ID not found

**Invariants**:
- Never returns 500 for missing enrichment data
- `ementa_original` is always populated (from proposição)
- `fontes` contains only URLs with `status = "resolvido"`

### POST /proposicoes/{id}/enriquecer

Force re-enrichment (admin only).

**Query params**:
- `admin_token` (required): Secret token for admin access
- `force` (optional, default true): Force even if ementa unchanged

**Response**: `{"status": "enqueued", "proposicao_id": "uuid"}`

**Status codes**:
- 200: Enrichment enqueued
- 401: Invalid admin token
- 404: Proposição not found

---

## Script Contracts (CLI interfaces)

### discover_proposicoes.py

```bash
python3 scripts/discover_proposicoes.py [OPTIONS]

Options:
  --ano-inicio N    Start year (default: 2020)
  --ano-fim N       End year (default: current year)
  --enriquecer      Set contexto_status="pendente" on new proposições
  --dry-run         Show what would be discovered without persisting

Output (JSON-like log):
  Total buscadas na API: 217
  Já existentes no banco: 1
  Novas classificadas ZIL: 210
  Novas persistidas: 210
  Erros: 0
```

### sync_votacoes_proposicoes.py (NEW)

```bash
python3 scripts/sync_votacoes_proposicoes.py [OPTIONS]

Options:
  --proposicao-id ID   Sync a single proposição (by UUID)
  --skip-with-votes    Skip proposições that already have votações (default: true)
  --dry-run            Show what would be synced without persisting

Output:
  Proposições checadas: 406
  Com votações na API: 126
  Votações novas sincronizadas: 170
  Votos individuais sincronizados: 41,000
  Erros: 0
```

### sync_pipeline.py (NEW)

```bash
python3 scripts/sync_pipeline.py [OPTIONS]

Options:
  --skip-discovery     Skip Step 1 (proposição discovery)
  --skip-votacoes      Skip Step 2 (votação sync)
  --skip-enrichment    Skip Step 3 (LLM enrichment)
  --skip-scores        Skip Step 4 (score recalculation)
  --dry-run            Dry-run all steps

Steps:
  Step 1: Discover proposições
  Step 2: Sync votações per proposição
  Step 3: Enrich pending proposições
  Step 4: Apply directions + recalculate scores
```

### apply_direcoes.py (existing — new behavior: triggers score recalculation)

```bash
python3 scripts/apply_direcoes.py

# NEW: After applying directions, automatically calls:
#   recalcular_todos_scores(db)
# Output: "551 scores recalculados"
```

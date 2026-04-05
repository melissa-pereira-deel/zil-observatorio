# Data Model: Pipeline de Enriquecimento Legislativo Completo

**Date**: 2026-04-04

## Entity Relationship Overview

```
Parlamentar (594)
    ├── 1:N → Voto
    └── 1:N → ScoreVotacao

Proposicao (406)
    ├── 1:N → Votacao
    ├── has  → enrichment fields (inline)
    └── refs → LeiArtigo (via leis_referenciadas JSON)

Votacao (7 → ~170+ after sync)
    ├── N:1 → Proposicao
    ├── 1:N → Voto
    └── 1:N → ScoreVotacao

Voto (1716 → ~40K+ after sync)
    ├── N:1 → Votacao
    └── N:1 → Parlamentar

LeiArtigo (cache)
    └── standalone (referenced by Proposicao.leis_referenciadas JSON)

ScoreVotacao (audit trail)
    ├── N:1 → Parlamentar
    └── N:1 → Votacao
```

## Entities

### Proposicao (existing — 8 enrichment fields added in Feature 002)

| Field | Type | Nullable | Source | Notes |
|-------|------|----------|--------|-------|
| id | UUID | NO | auto | PK |
| fonte_id | String(50) | NO | Câmara API | API proposição ID |
| fonte | Enum(CAMARA,SENADO) | NO | code | Always CAMARA for v1 |
| tipo | String(20) | YES | API | PL, PEC, PLP, PDL, MPV |
| numero | Integer | YES | API | Proposition number |
| ano | Integer | YES | API | Year |
| ementa | Text | YES | API | Short legal summary |
| ementa_detalhada | Text | YES | API (details) | Extended summary (from `obter_proposicao`) |
| situacao | String(255) | YES | API (details) | Current status |
| data_apresentacao | Date | YES | API (details) | Presentation date |
| ultimo_despacho | Text | YES | API (details) | Last committee dispatch |
| categorias_zil | JSON | YES | classifier | `["ZIL-FER","ZIL-MIN"]` — `none_as_null=True` |
| relevancia_zil | Numeric(3,2) | YES | classifier | 0.0–1.0 keyword density score |
| classificacao_automatica | Boolean | NO | code | `True` if keyword-classified |
| url_inteiro_teor | String(500) | YES | API | Link to full text PDF |
| **contexto_status** | String(20) | YES | enrichment | null→pendente→processando→pronto/falhou/llm_falhou |
| **resumo_simples** | Text | YES | LLM | 3–5 sentence plain-language summary |
| **glossario** | JSON | YES | LLM | `{"PADIS":"definição","CFEM":"definição"}` |
| **impacto_zil** | Text | YES | LLM | 1–2 sentences on sovereignty relevance |
| **leis_referenciadas** | JSON | YES | pipeline | `[{lei_id, numero_artigo, url_planalto, status, texto_snippet}]` |
| **confianca** | Numeric(3,2) | YES | pipeline | `resolvidos / max(citados, 1)` |
| **ementa_hash** | String(64) | YES | pipeline | SHA-256 for idempotency |
| **enriquecido_em** | DateTime | YES | pipeline | Timestamp of last enrichment |

**Unique constraint**: `(fonte_id, fonte)`
**Indexes**: `(tipo, ano)`, `(contexto_status)`

**State transitions for `contexto_status`**:
```
NULL → pendente (discovery marks for enrichment)
pendente → processando (pipeline starts)
processando → pronto (success)
processando → falhou (pipeline error)
processando → llm_falhou (LLM error, RESOLVE data saved)
falhou → processando (retry)
llm_falhou → processando (retry AUGMENT only)
pronto → processando (force re-enrichment)
```

### Votacao (existing — no schema changes, volume increase from sync)

| Field | Type | Nullable | Source | Notes |
|-------|------|----------|--------|-------|
| id | UUID | NO | auto | PK |
| fonte_id | String(50) | NO | Câmara API | Votação ID (e.g., "2269745-73") |
| fonte | Enum | NO | code | CAMARA |
| proposicao_id | UUID FK | YES | sync | Links to Proposicao.id |
| data | DateTime | YES | API | Vote date/time |
| descricao | Text | YES | API | Description of what was voted |
| resultado | String(50) | YES | API/inferred | "aprovado"/"rejeitado" |
| votos_sim | Integer | YES | computed | Count after syncing individual votes |
| votos_nao | Integer | YES | computed | Count |
| abstencoes | Integer | YES | computed | Count |
| categorias_zil | JSON | YES | classifier | From `classificar_votacao(descricao)` |
| direcao_esperada | String(10) | YES | **editorial** | "sim"/"nao" — NULL until YAML curation |
| peso | Numeric(3,1) | YES | **editorial** | 1.0–3.0 — NULL until YAML curation |

**Key invariant**: `direcao_esperada` and `peso` are ONLY set by `apply_direcoes.py` from YAML files. Auto-synced votações always have these as NULL.

### Voto (existing — no changes, volume increase)

| Field | Type | Nullable | Source |
|-------|------|----------|--------|
| id | UUID | NO | auto |
| votacao_id | UUID FK | NO | sync |
| parlamentar_id | UUID FK | NO | sync |
| voto | Enum(SIM,NAO,ABSTENCAO,OBSTRUCAO,ARTIGO_17,AUSENTE) | NO | API |
| orientacao_partido | String(50) | YES | API |

### LeiArtigo (existing — cache table, no changes)

| Field | Type | Nullable | Source |
|-------|------|----------|--------|
| id | UUID | NO | auto |
| lei_id | String(50) | NO | pipeline | e.g., "14744-2023" |
| numero_artigo | String(20) | NO | pipeline | e.g., "3" |
| texto_artigo | Text | YES | Planalto | Extracted article text |
| url_planalto | String(500) | YES | pipeline | Canonical URL |
| status | String(30) | NO | pipeline | resolvido/revogada/nao_encontrada/pdf_nao_parseavel/timeout |
| obtido_em | DateTime | NO | pipeline | Fetch timestamp |
| expira_em | DateTime | NO | pipeline | `obtido_em + 30 days` |

**Unique constraint**: `(lei_id, numero_artigo)`

### ScoreVotacao (existing — audit trail, no changes)

| Field | Type | Nullable | Source |
|-------|------|----------|--------|
| id | UUID | NO | auto |
| parlamentar_id | UUID FK | NO | scoring |
| votacao_id | UUID FK | NO | scoring |
| categoria_zil | String(20) | NO | votacao | First category |
| impacto | Numeric | NO | scoring | -1.0, 0.0, +1.0 |
| peso | Numeric | NO | scoring | Votação weight |
| justificativa | Text | YES | scoring | e.g., "Voto: sim \| Esperado: sim" |

## Validation Rules

1. **Proposicao.categorias_zil**: Must be a JSON array of strings matching `ZIL-[A-Z]{3}` pattern. Only valid codes from `data/taxonomia/categorias.yml`.
2. **Proposicao.confianca**: Range `[0.0, 1.0]`. Computed, never user-set.
3. **Votacao.direcao_esperada**: Only "sim" or "nao" (or NULL). Set exclusively by `apply_direcoes.py`.
4. **Votacao.peso**: Range `[1.0, 3.0]` (or NULL). Set exclusively by `apply_direcoes.py`.
5. **LeiArtigo.expira_em**: Always `obtido_em + 30 days`. Cache invalidation is TTL-based.
6. **Voto.voto**: Must be a valid `VotoEnum` member. Unknown API values map to `AUSENTE`.

## Data Volume Projections

| Entity | Current | After Full Sync | Growth Rate |
|--------|---------|-----------------|-------------|
| Proposicao | 406 | 406 (discovery complete for 2020–2026) | ~50/quarter via periodic discovery |
| Votacao | 7 | ~170+ (126 proposições × ~1.3 avg votações with votes) | Grows with new proposições |
| Voto | 1,716 | ~40,000+ (~250 votos/votação × ~170 votações) | Proportional to votações |
| LeiArtigo | ~15 | ~500+ (many proposições cite laws) | Proportional to enrichment |
| Parlamentar | 594 | 594 (stable per legislature) | Changes at election cycles |

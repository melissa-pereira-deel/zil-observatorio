# Research: 012 — Enriquecimento de Dados de Proposicoes

## Status: Complete — All Decisions Resolved

No NEEDS CLARIFICATION items. All decisions documented from discovery analysis and spec clarifications.

---

### Decision 1: JSON vs Normalized Tables

**Decision**: Mixed approach — JSON for low-cardinality read-only data, normalized tables for high-cardinality data with FK relationships.

| Data | Approach | Rationale |
|------|----------|-----------|
| temas_camara | JSON column | 32 fixed codes, read-only, no FK needed |
| keywords_camara | Text column | Simple comma-separated string, search-only |
| autores | Normalized table (ProposicaoAutor) | N:M with parlamentares, FK join needed |
| relacionadas | Normalized table (ProposicaoRelacao) | N:N between proposicoes, bidirectional FK |
| cadeia (principal/anterior/posterior) | String columns (fonte_id refs) | 1:1 relationships, simple lookup |

**Alternatives considered**:
- All JSON: rejected for autores/relacionadas (need FK joins for cross-entity navigation)
- All normalized: rejected for temas (over-engineered for 32 fixed codes)

---

### Decision 2: Backfill Strategy

**Decision**: New Step 1.5 in sync_pipeline.py, sequential per-proposicao with 300ms inter-request delay.

**Rationale**: Matches existing patterns (sync_votacoes_proposicoes.py). 406 proposicoes x 4 calls x 300ms = ~8 min. Acceptable for one-time backfill. Idempotency via `detalhes_sincronizados_em IS NULL` guard.

**Alternatives considered**:
- Celery parallel workers: rejected (adds complexity for one-time operation, risk of rate limiting)
- Modify existing discover_proposicoes.py: rejected (separate concerns — discovery vs enrichment)

---

### Decision 3: Author-Parlamentar Matching

**Decision**: Match by extracting deputado ID from author `uri` field and matching against `Parlamentar.fonte_id`.

**Rationale**: The `uri` field in autores contains the deputado's ID in the Dados Abertos system (e.g., `/api/v2/deputados/204554`). This matches our `Parlamentar.fonte_id`. When match found, set `parlamentar_id` FK. When not found (Orgao, Senado, external), leave FK null.

**Alternatives considered**:
- Name matching: rejected (ambiguous — "João Silva" could match multiple parlamentares)
- Ignore matching: rejected (linking autores to parlamentares is the core value)

---

### Decision 4: Relacionadas Pagination and Limits

**Decision**: Fetch up to 10 pages of relacionadas (API default ~20 items/page = ~200 max). Classify by siglaTipo into tipo_relacao categories.

**Rationale**: Most proposicoes have <50 relacionadas. Large ones (PEC 45/2019: 419) are rare. Cap at 200 prevents excessive API calls while covering >95% of cases.

**Classification map**:
| siglaTipo | tipo_relacao |
|-----------|-------------|
| EMC, EMP, EMS, EMA, EMR | emenda |
| SBT | substitutivo |
| PAR, PRL, PPP, PRLP | parecer |
| RDF | redacao_final |
| DTQ | destaque |
| REQ, RPDR | requerimento |
| VTS | voto_separado |
| PL, PEC, PLP, MPV, PDL | apensada |

**Alternatives considered**:
- Fetch all: rejected (some proposicoes have 400+ related, would take too long)
- Store as JSON blob: rejected (need FK for cross-navigation when related prop is in our DB)

---

### Decision 5: URN to URL Conversion (urnFinal)

**Decision**: Parse LexML URN format with regex, construct Planalto URL with fallback.

**Pattern**: `urn:lex:br:federal:lei:YYYY-MM-DD;NNNNN` → extract year range and number → construct `https://www.planalto.gov.br/ccivil_03/_ato{range}/lei/L{number}.htm`

**Fallback**: If URN format unrecognized, display URN as text without link.

**Rationale**: The existing enrichment pipeline already resolves Planalto URLs for cited laws. Reuse the same URL construction logic.

---

### Decision 6: Situacao Grouping

**Decision**: Map 97 codSituacao values into 4 UI groups for filtering.

| Group | Label | codSituacao values |
|-------|-------|-------------------|
| tramitando | Em Tramitacao | 903, 924, 925, 1360 and others |
| aprovada | Aprovada | 1140 (Transformado em Norma) |
| arquivada | Arquivada | 923, 937, 950, 1222 and others |
| outras | Outras | All remaining codes |

**Rationale**: Citizens don't care about 97 distinct statuses. 4 groups cover the questions they actually ask: "Is it alive?", "Did it pass?", "Is it dead?".

---

### Decision 7: Re-sync Strategy

**Decision**: Weekly re-sync for active proposicoes (cod_situacao NOT IN archived/transformed), quarterly for terminal states.

**Rationale**: Active bills change status frequently (committee assignment, voting schedule). Archived/transformed bills are terminal — their status won't change. Weekly check for ~200 active props = ~4 min/week.

**Implementation**: Add `sync_detalhes` step to existing Celery beat schedule with `detalhes_sincronizados_em < 7 days ago` filter.

---

### Decision 8: Frontend Progressive Disclosure

**Decision**: 3-tier visibility using native `<details>/<summary>` (consistent with UI-012 pattern).

| Tier | Sections | Visibility |
|------|----------|------------|
| Always visible | Header, resumo, autor principal, cadeia, votacoes | Instant |
| 1-click expand | Ementa, co-autores, tramitacao completa | Collapsed |
| 1-click expand | Relacionadas, glossario, leis referenciadas | Collapsed |

**Rationale**: UI-012 established `<details>` as the standard collapse pattern. No new UI paradigm needed. Keeps page fast for citizens who want the summary, deep for researchers who want everything.

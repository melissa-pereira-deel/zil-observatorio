# Data Model: 012 — Enriquecimento de Dados de Proposicoes

**Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

---

## Summary of Changes

| Change Type | Count | Details |
|-------------|-------|---------|
| New columns on `proposicoes` | 9 | cod_situacao, regime, apreciacao, keywords_camara, temas_camara, urn_final, orgao_situacao, relator_id, detalhes_sincronizados_em |
| Modified columns on `proposicoes` | 0 | (autor_principal_id already exists, will be populated) |
| New columns on `votacoes` | 3 | aprovacao, sigla_orgao, proposicao_objeto |
| New tables | 2 | proposicao_autores, proposicao_relacoes |
| New indexes | 5 | See per-table sections |

---

## Existing Table: `proposicoes` — New Columns

### Phase 1 Columns (F-001, F-005, F-008)

| Column | Type | Nullable | Default | Source (API field) | Notes |
|--------|------|----------|---------|-------------------|-------|
| `cod_situacao` | Integer | YES | NULL | `statusProposicao.codSituacao` | 97 distinct values, grouped into 4 UI groups (Decision 6) |
| `regime` | String(50) | YES | NULL | `statusProposicao.regime` | URGENCIA, ESPECIAL, ORDINARIO, etc. |
| `apreciacao` | String(100) | YES | NULL | `statusProposicao.apreciacao` | "Plenario" / "Conclusiva" |
| `keywords_camara` | Text | YES | NULL | `keywords` | Comma-separated string from API |
| `urn_final` | String(500) | YES | NULL | `statusProposicao.urnFinal` | LexML URN when bill becomes law (Decision 5) |
| `detalhes_sincronizados_em` | DateTime | YES | NULL | (internal) | Idempotency guard for backfill (Decision 2) |

### Phase 2 Columns (F-002)

| Column | Type | Nullable | Default | Source (API field) | Notes |
|--------|------|----------|---------|-------------------|-------|
| `temas_camara` | JSON(none_as_null=True) | YES | NULL | `GET /proposicoes/{id}/temas` | Array of `{cod, tema}` objects. 32 fixed codes. ADR-001: JSON not JSONB. ADR-003: none_as_null=True |

### Phase 3 Columns (F-003, F-007)

| Column | Type | Nullable | Default | Source (API field) | Notes |
|--------|------|----------|---------|-------------------|-------|
| `prop_principal_id` | String(50) | YES | NULL | `uriPropPrincipal` | fonte_id extracted from URI. String ref, not FK (may not exist in DB) |
| `prop_anterior_id` | String(50) | YES | NULL | `uriPropAnterior` | fonte_id extracted from URI |
| `prop_posterior_id` | String(50) | YES | NULL | `uriPropPosterior` | fonte_id extracted from URI |
| `orgao_situacao` | String(50) | YES | NULL | `statusProposicao.siglaOrgao` | e.g. "CCJC", "PLEN", "CFT" |
| `relator_id` | UUID FK | YES | NULL | `statusProposicao.relator` | FK to `parlamentares.id`. NULL if relator not in DB |

### New Indexes on `proposicoes`

| Index Name | Columns | Rationale |
|------------|---------|-----------|
| `ix_proposicao_cod_situacao` | `cod_situacao` | UI filter by situacao_grupo |
| `ix_proposicao_regime` | `regime` | UI filter by regime |
| `ix_proposicao_detalhes_sync` | `detalhes_sincronizados_em` | Backfill idempotency: find unsynced rows |

---

## Existing Table: `votacoes` — New Columns

### Phase 1 Columns (F-004)

| Column | Type | Nullable | Default | Source (API field) | Notes |
|--------|------|----------|---------|-------------------|-------|
| `aprovacao` | Integer | YES | NULL | `aprovacao` from votacao detail | 1 = approved, 0 = rejected, NULL = unknown. Replaces inferential resultado |
| `sigla_orgao` | String(20) | YES | NULL | `siglaOrgao` | Organ where vote happened (e.g. "PLEN", "CCJC") |
| `proposicao_objeto` | Text | YES | NULL | `proposicaoObjeto` | Description of what was actually voted on |

---

## New Table: `proposicao_autores`

**Feature**: F-006 (Autoria Completa)
**Cardinality**: N:M between proposicoes and parlamentares
**Decision**: Research Decision 1 — Normalized table (high cardinality, FK join needed)

### Schema

```
proposicao_autores
├── id                  UUID        PK, default uuid4
├── proposicao_id       UUID        FK → proposicoes.id, NOT NULL
├── parlamentar_id      UUID        FK → parlamentares.id, NULLABLE (Decision 3)
├── nome                String(255) NOT NULL (from API, always present)
├── tipo                String(50)  NOT NULL ("Deputado", "Senador", "Orgao", "Lideranca")
├── ordem               Integer     NOT NULL, default 1 (1 = autor principal)
├── proponente          Boolean     NOT NULL, default True
├── uri_autor            String(500) NULLABLE (original URI from API)
├── created_at          DateTime    default utcnow
```

### Columns Detail

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | PK |
| `proposicao_id` | UUID FK | NO | FK to `proposicoes.id`, ON DELETE CASCADE |
| `parlamentar_id` | UUID FK | YES | FK to `parlamentares.id`. NULL when author is Orgao/Senado/external (Decision 3) |
| `nome` | String(255) | NO | Author name from API — always present even when parlamentar_id is NULL |
| `tipo` | String(50) | NO | "Deputado", "Senador", "Orgao", "Lideranca", etc. |
| `ordem` | Integer | NO | 1 = autor principal. Used to populate `proposicoes.autor_principal_id` |
| `proponente` | Boolean | NO | True if proponente, False if co-signer |
| `uri_autor` | String(500) | YES | Original API URI for traceability |
| `created_at` | DateTime | NO | default utcnow |

### Indexes

| Index Name | Columns | Rationale |
|------------|---------|-----------|
| `uq_autor_proposicao_ordem` | (`proposicao_id`, `ordem`) | Unique: one author per order position per prop |
| `ix_autor_parlamentar` | `parlamentar_id` | Lookup: "all proposicoes by this parlamentar" |
| `ix_autor_proposicao` | `proposicao_id` | Lookup: "all authors of this proposicao" |

### Relationships

```
Proposicao 1 ──── N ProposicaoAutor N ──── 0..1 Parlamentar
  .autores_rel                              .proposicoes_autoria
```

- `Proposicao.autores_rel` → list of ProposicaoAutor (cascade delete)
- `ProposicaoAutor.proposicao` → back_populates
- `ProposicaoAutor.parlamentar` → optional relationship (nullable FK)

---

## New Table: `proposicao_relacoes`

**Feature**: F-003 (Cadeia Legislativa)
**Cardinality**: N:N between proposicoes (bidirectional)
**Decision**: Research Decision 1 — Normalized table (high cardinality, FK for cross-navigation)

### Schema

```
proposicao_relacoes
├── id                  UUID        PK, default uuid4
├── proposicao_id       UUID        FK → proposicoes.id, NOT NULL
├── relacionada_id      UUID        FK → proposicoes.id, NULLABLE
├── relacionada_fonte_id String(50) NOT NULL (always present from API)
├── tipo_relacao        String(30)  NOT NULL (Decision 4 classification)
├── sigla_tipo          String(20)  NULLABLE (original siglaTipo from API)
├── numero              Integer     NULLABLE
├── ano                 Integer     NULLABLE
├── ementa              Text        NULLABLE (snapshot from API)
├── created_at          DateTime    default utcnow
```

### Columns Detail

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | NO | PK |
| `proposicao_id` | UUID FK | NO | FK to `proposicoes.id`, ON DELETE CASCADE. The "parent" proposicao |
| `relacionada_id` | UUID FK | YES | FK to `proposicoes.id`. NULL when related prop is not in our DB |
| `relacionada_fonte_id` | String(50) | NO | API ID of related proposicao. Always present |
| `tipo_relacao` | String(30) | NO | One of: emenda, substitutivo, parecer, redacao_final, destaque, requerimento, voto_separado, apensada, outro (Decision 4) |
| `sigla_tipo` | String(20) | YES | Original siglaTipo from API (e.g. "EMC", "PL", "SBT") |
| `numero` | Integer | YES | Number of related proposicao |
| `ano` | Integer | YES | Year of related proposicao |
| `ementa` | Text | YES | Short description snapshot — avoids JOIN when just listing |
| `created_at` | DateTime | NO | default utcnow |

### Indexes

| Index Name | Columns | Rationale |
|------------|---------|-----------|
| `uq_relacao_prop_rel` | (`proposicao_id`, `relacionada_fonte_id`) | Unique: one relation per pair |
| `ix_relacao_proposicao` | `proposicao_id` | Lookup: "all relacionadas of this prop" |
| `ix_relacao_relacionada` | `relacionada_id` | Reverse lookup: "all props that reference this one" |
| `ix_relacao_tipo` | `tipo_relacao` | Filter by relationship type |

### Relationships

```
Proposicao 1 ──── N ProposicaoRelacao N ──── 0..1 Proposicao
  .relacionadas                                   (self-referential)
```

- `Proposicao.relacionadas` → list of ProposicaoRelacao where `proposicao_id = self.id`
- `ProposicaoRelacao.proposicao` → parent proposicao
- `ProposicaoRelacao.relacionada` → optional relationship (nullable FK, may not be in DB)

---

## tipo_relacao Classification Map (Decision 4)

| API siglaTipo | tipo_relacao | Description |
|---------------|-------------|-------------|
| EMC, EMP, EMS, EMA, EMR | `emenda` | Amendments |
| SBT | `substitutivo` | Substitutive text |
| PAR, PRL, PPP, PRLP | `parecer` | Committee reports |
| RDF | `redacao_final` | Final draft |
| DTQ | `destaque` | Highlighted items |
| REQ, RPDR | `requerimento` | Procedural requests |
| VTS | `voto_separado` | Separate votes |
| PL, PEC, PLP, MPV, PDL | `apensada` | Appended propositions |
| (all others) | `outro` | Unclassified |

---

## situacao_grupo Mapping (Decision 6)

| Group | UI Label | codSituacao values |
|-------|----------|-------------------|
| `tramitando` | Em Tramitacao | 903, 924, 925, 1360 (and other active codes) |
| `aprovada` | Aprovada | 1140 (Transformado em Norma Juridica) |
| `arquivada` | Arquivada | 923, 937, 950, 1222 (and other terminal codes) |
| `outras` | Outras | All remaining codes |

**Implementation**: Python dict mapping in a helper module (`lib/situacao.py`), not in DB. Filtering done at query time via `cod_situacao IN (...)`.

---

## Migration Strategy

### Script: `scripts/migrate_012_detail_fields.py`

**Idempotent**: checks column existence before ALTER TABLE.

**Phase 1 (columns only, no new tables)**:
1. Add 6 columns to `proposicoes`: cod_situacao, regime, apreciacao, keywords_camara, urn_final, detalhes_sincronizados_em
2. Add 3 columns to `votacoes`: aprovacao, sigla_orgao, proposicao_objeto
3. Create 3 indexes on proposicoes

**Phase 2 (add table + column)**:
4. Create table `proposicao_autores` with all indexes
5. Add column `temas_camara` to `proposicoes`

**Phase 3 (add table + columns)**:
6. Create table `proposicao_relacoes` with all indexes
7. Add 5 columns to `proposicoes`: prop_principal_id, prop_anterior_id, prop_posterior_id, orgao_situacao, relator_id

### Rollback

Each phase is independently rollbackable:
- Phase 1: DROP 3 indexes + DROP 9 columns
- Phase 2: DROP TABLE proposicao_autores + DROP 1 column
- Phase 3: DROP TABLE proposicao_relacoes + DROP 5 columns

---

## Entity Relationship Diagram

```
                          ┌──────────────────┐
                          │   Parlamentar    │
                          ├──────────────────┤
                          │ id (PK)          │
                          │ fonte_id         │
                          │ nome             │
                          │ partido          │
                          │ uf               │
                          │ score_zil        │
                          └──────┬───────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
          ┌─────────────┐  ┌─────────┐  ┌──────────────────┐
          │ Proposicao  │  │  Voto   │  │ ProposicaoAutor  │
          │  Autor      │  │         │  │   (NEW)          │
          │  (NEW)      │  │         │  ├──────────────────┤
          ├─────────────┤  └─────────┘  │ proposicao_id FK │
          │ proposicao  │               │ parlamentar_id FK│
          │   _id FK    │               │ nome             │
          │ parlamentar │               │ tipo             │
          │   _id FK    │               │ ordem            │
          │ nome        │               └──────┬───────────┘
          │ tipo        │                      │
          │ ordem       │                      ▼
          └─────────────┘             ┌──────────────────┐
                                      │   Proposicao     │
                 ┌───────────────────▶├──────────────────┤
                 │                    │ id (PK)          │
                 │                    │ fonte_id         │
                 │                    │ tipo, numero, ano│
                 │                    │ ementa           │
                 │                    │ situacao         │
                 │                    │ cod_situacao  NEW│
                 │                    │ regime        NEW│
                 │                    │ apreciacao    NEW│
                 │                    │ keywords_camara  │
                 │                    │ temas_camara  NEW│
                 │                    │ urn_final     NEW│
                 │                    │ orgao_situacao   │
                 │                    │ relator_id    NEW│
                 │                    │ prop_principal_id│
                 │                    │ prop_anterior_id │
                 │                    │ prop_posterior_id│
                 │                    │ detalhes_sync_em │
                 │                    │ autor_principal_id│
                 │                    │ (enrichment...)  │
  ┌──────────────┤                    └──────┬───────────┘
  │ Proposicao   │                           │
  │  Relacao     │                           ▼
  │  (NEW)       │                    ┌──────────────────┐
  ├──────────────┤                    │    Votacao       │
  │proposicao_id │                    ├──────────────────┤
  │  FK          │                    │ id (PK)          │
  │relacionada_id│                    │ proposicao_id FK │
  │  FK (opt)    │                    │ aprovacao     NEW│
  │relacionada   │                    │ sigla_orgao   NEW│
  │  _fonte_id   │                    │ proposicao_   NEW│
  │tipo_relacao  │                    │   objeto         │
  │sigla_tipo    │                    │ (existing...)    │
  │ementa        │                    └──────────────────┘
  └──────────────┘
```

---

## Validation Rules

### ProposicaoAutor
- `ordem >= 1`
- `tipo` must be one of: "Deputado", "Senador", "Orgao", "Lideranca", "Outro"
- If `parlamentar_id` is set, must reference valid Parlamentar
- `nome` is never empty

### ProposicaoRelacao
- `tipo_relacao` must be one of the 9 values in classification map
- `relacionada_fonte_id` is never empty
- `proposicao_id != relacionada_id` (no self-references)

### Proposicao (new columns)
- `cod_situacao` in range 0-9999 when set
- `regime` max 50 chars
- `urn_final` must start with "urn:lex:" when set

### Votacao (new columns)
- `aprovacao` in {0, 1, NULL}

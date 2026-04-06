# Quickstart: 012 — Enriquecimento de Dados de Proposicoes

**Branch**: `012-enriquecimento-dados-proposicoes`

---

## Prerequisites

- Python 3.12 with venv activated (`.venv/bin/python3`)
- Node.js 18+ with npm
- Redis running (for Celery, optional for dev)
- Database seeded with 406 proposicoes (existing pipeline)

---

## Phase 1: Colunas + Campos do Detalhe

### 1. Run migration

```bash
# From repo root
.venv/bin/python3 scripts/migrate_012_detail_fields.py
```

Expected output:
```
Phase 1: Adding columns to proposicoes...
  - cod_situacao: added
  - regime: added
  - apreciacao: added
  - keywords_camara: added
  - urn_final: added
  - detalhes_sincronizados_em: added
Phase 1: Adding columns to votacoes...
  - aprovacao: added
  - sigla_orgao: added
  - proposicao_objeto: added
Phase 1: Creating indexes...
  - ix_proposicao_cod_situacao: created
  - ix_proposicao_regime: created
  - ix_proposicao_detalhes_sync: created
Migration Phase 1 complete.
```

### 2. Run backfill

```bash
# Backfill detail fields from API (dry-run first)
.venv/bin/python3 scripts/sync_detalhes_proposicoes.py --dry-run --fase 1

# Execute backfill
.venv/bin/python3 scripts/sync_detalhes_proposicoes.py --fase 1
```

Expected output:
```
Backfill Phase 1: 406 proposicoes to process
[1/406] PL 528/2020: cod_situacao=903 regime=URGENCIA keywords=5 urn_final=null
[2/406] PEC 45/2019: cod_situacao=1140 regime=ESPECIAL keywords=3 urn_final=urn:lex:...
...
[406/406] PL 1234/2023: cod_situacao=924 regime=ORDINARIO keywords=8 urn_final=null
Backfill Phase 1 complete: 406 updated, 0 errors. Time: ~8 min
```

### 3. Verify data

```bash
.venv/bin/python3 -c "
import sys; sys.path.insert(0, 'apps/api')
from sqlalchemy import create_engine, text
from core.config import settings
engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    total = conn.execute(text('SELECT count(*) FROM proposicoes')).scalar()
    with_cod = conn.execute(text('SELECT count(*) FROM proposicoes WHERE cod_situacao IS NOT NULL')).scalar()
    with_kw = conn.execute(text('SELECT count(*) FROM proposicoes WHERE keywords_camara IS NOT NULL')).scalar()
    with_urn = conn.execute(text('SELECT count(*) FROM proposicoes WHERE urn_final IS NOT NULL')).scalar()
    print(f'Total: {total}')
    print(f'With cod_situacao: {with_cod} ({with_cod*100//total}%)')
    print(f'With keywords: {with_kw} ({with_kw*100//total}%)')
    print(f'With urn_final: {with_urn} ({with_urn*100//total}%)')
"
```

Expected: 100% with cod_situacao and keywords. urn_final only for bills that became law (~5-10%).

### 4. Run tests

```bash
.venv/bin/python3 -m pytest tests/ -v
```

Expected: All 151 existing tests pass + new tests for Phase 1.

### 5. Verify API

```bash
# Start API
cd apps/api && ../.venv/bin/python3 -m uvicorn main:app --reload &

# Test new filters
curl "http://localhost:8000/proposicoes?situacao_grupo=tramitando&limit=3" | python3 -m json.tool
curl "http://localhost:8000/proposicoes?regime=URGENCIA&limit=3" | python3 -m json.tool

# Check expanded fields
curl "http://localhost:8000/proposicoes/<any-id>" | python3 -m json.tool
# Verify: cod_situacao, regime, apreciacao, keywords_camara, situacao_grupo present
```

### 6. Verify frontend

```bash
cd apps/web && npm run dev
```

- Visit `/proposicoes` — verify new filter dropdowns (regime, situacao_grupo)
- Visit `/proposicoes/<id>` — verify badges (regime, situacao colored badge)
- Check "VIROU LEI" badge on proposicoes with urn_final

---

## Phase 2: Autores + Temas

### 1. Run migration (Phase 2)

```bash
.venv/bin/python3 scripts/migrate_012_detail_fields.py --fase 2
```

### 2. Run backfill (Phase 2)

```bash
.venv/bin/python3 scripts/sync_detalhes_proposicoes.py --fase 2
```

Expected: Creates ProposicaoAutor records, populates autor_principal_id, fetches temas.

### 3. Verify

```bash
.venv/bin/python3 -c "
import sys; sys.path.insert(0, 'apps/api')
from sqlalchemy import create_engine, text
from core.config import settings
engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    autores = conn.execute(text('SELECT count(*) FROM proposicao_autores')).scalar()
    linked = conn.execute(text('SELECT count(*) FROM proposicao_autores WHERE parlamentar_id IS NOT NULL')).scalar()
    with_temas = conn.execute(text('SELECT count(*) FROM proposicoes WHERE temas_camara IS NOT NULL')).scalar()
    with_autor = conn.execute(text('SELECT count(*) FROM proposicoes WHERE autor_principal_id IS NOT NULL')).scalar()
    print(f'Total autores: {autores}')
    print(f'Linked to parlamentar: {linked} ({linked*100//max(autores,1)}%)')
    print(f'Props with temas: {with_temas}')
    print(f'Props with autor_principal: {with_autor}')
"
```

Expected: >95% autor_principal_id linked, >90% with temas.

### 4. Verify API

```bash
# Autores endpoint
curl "http://localhost:8000/proposicoes/<id>/autores" | python3 -m json.tool

# Temas endpoint
curl "http://localhost:8000/proposicoes/<id>/temas" | python3 -m json.tool

# Parlamentar proposicoes
curl "http://localhost:8000/parlamentares/<id>/proposicoes" | python3 -m json.tool
```

### 5. Verify frontend

- Visit `/proposicoes/<id>` — verify author name with link to parlamentar profile
- Visit `/parlamentar/<id>` — verify "Proposicoes de autoria" section

---

## Phase 3: Cadeia + Relacionadas

### 1. Run migration (Phase 3)

```bash
.venv/bin/python3 scripts/migrate_012_detail_fields.py --fase 3
```

### 2. Run backfill (Phase 3)

```bash
.venv/bin/python3 scripts/sync_detalhes_proposicoes.py --fase 3
```

### 3. Verify

```bash
.venv/bin/python3 -c "
import sys; sys.path.insert(0, 'apps/api')
from sqlalchemy import create_engine, text
from core.config import settings
engine = create_engine(settings.DATABASE_URL)
with engine.connect() as conn:
    relacoes = conn.execute(text('SELECT count(*) FROM proposicao_relacoes')).scalar()
    with_cadeia = conn.execute(text(\"\"\"
        SELECT count(*) FROM proposicoes
        WHERE prop_principal_id IS NOT NULL
           OR prop_anterior_id IS NOT NULL
           OR prop_posterior_id IS NOT NULL
    \"\"\")).scalar()
    print(f'Total relacoes: {relacoes}')
    print(f'Props with cadeia: {with_cadeia}')
"
```

Expected: >40% proposicoes with at least 1 cadeia link.

### 4. Verify API

```bash
# Relacionadas endpoint
curl "http://localhost:8000/proposicoes/<id>/relacionadas" | python3 -m json.tool
curl "http://localhost:8000/proposicoes/<id>/relacionadas?tipo_relacao=emenda" | python3 -m json.tool
```

### 5. Verify frontend

- Visit `/proposicoes/<id>` — verify cadeia timeline, related proposicoes section
- Verify progressive disclosure: `<details>` sections collapse/expand

---

## Full Pipeline (all phases)

```bash
# Migration (all phases, idempotent)
.venv/bin/python3 scripts/migrate_012_detail_fields.py

# Backfill (all phases, sequential)
.venv/bin/python3 scripts/sync_detalhes_proposicoes.py

# Verify all tests pass
.venv/bin/python3 -m pytest tests/ -v

# Type check frontend
cd apps/web && /opt/homebrew/bin/npx tsc --noEmit
```

---

## Rollback

```bash
# If Phase 1 needs rollback
.venv/bin/python3 scripts/migrate_012_detail_fields.py --rollback --fase 1

# If Phase 2 needs rollback
.venv/bin/python3 scripts/migrate_012_detail_fields.py --rollback --fase 2

# If Phase 3 needs rollback
.venv/bin/python3 scripts/migrate_012_detail_fields.py --rollback --fase 3
```

---

## Success Criteria Checklist

| Criteria | Phase | Verification |
|----------|-------|-------------|
| 100% proposicoes with cod_situacao | 1 | SQL count |
| 100% proposicoes with regime | 1 | SQL count |
| 100% proposicoes with keywords | 1 | SQL count |
| Zero "Aprovado*" badges | 1 | UI inspection |
| >95% proposicoes with autor_principal_id | 2 | SQL count |
| >90% proposicoes with temas | 2 | SQL count |
| >40% proposicoes with cadeia link | 3 | SQL count |
| 151 existing tests pass | All | pytest |
| ~30 new tests pass | All | pytest |
| TypeScript compiles clean | All | tsc --noEmit |

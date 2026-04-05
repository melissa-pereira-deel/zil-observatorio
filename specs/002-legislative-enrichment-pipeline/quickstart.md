# Quickstart: Pipeline de Enriquecimento Legislativo

## Prerequisites

- Python 3.12 with venv at `.venv/`
- SQLite database (auto-created from `.env` `DATABASE_URL`)
- `ANTHROPIC_API_KEY` in `.env` (required for LLM enrichment only)
- Node.js for frontend (optional)

## Full Pipeline Run (end to end)

```bash
# From repo root with .venv activated

# Option A: Run the orchestrator (does all 4 steps)
.venv/bin/python scripts/sync_pipeline.py

# Option B: Run steps individually
.venv/bin/python scripts/discover_proposicoes.py --enriquecer
.venv/bin/python scripts/sync_votacoes_proposicoes.py
ANTHROPIC_API_KEY=$(grep ANTHROPIC_API_KEY .env | cut -d= -f2) .venv/bin/python -c "
import sys; sys.path.insert(0,'apps/api'); sys.path.insert(0,'.')
from core.config import SessionLocal
from sqlalchemy import select, or_
from models import Proposicao
from apps.workers.enrichment import enriquecer_proposicao
from uuid import UUID
with SessionLocal() as db:
    ids = db.execute(select(Proposicao.id).where(
        or_(Proposicao.contexto_status == 'pendente', Proposicao.contexto_status.is_(None)),
        Proposicao.categorias_zil.isnot(None)
    )).scalars().all()
    for i, pid in enumerate(ids):
        pid_uuid = UUID(pid) if isinstance(pid, str) and len(pid) == 32 else pid
        result = enriquecer_proposicao(pid_uuid, db)
        print(f'[{i+1}/{len(ids)}] {result}')
"
.venv/bin/python scripts/apply_direcoes.py  # also recalculates scores
```

## Dry Run (preview without changes)

```bash
# See what proposições would be discovered
.venv/bin/python scripts/discover_proposicoes.py --dry-run --ano-inicio 2024

# See what votações would be synced
.venv/bin/python scripts/sync_votacoes_proposicoes.py --dry-run
```

## Verify Results

```bash
# Check database state
.venv/bin/python -c "
import sys; sys.path.insert(0,'apps/api'); sys.path.insert(0,'.')
from sqlalchemy import select, func
from core.config import SessionLocal
from models import Proposicao, Votacao, Voto, Parlamentar
with SessionLocal() as db:
    print(f'Proposições: {db.execute(select(func.count(Proposicao.id))).scalar()}')
    print(f'Votações: {db.execute(select(func.count(Votacao.id))).scalar()}')
    print(f'Votos: {db.execute(select(func.count(Voto.id))).scalar()}')
    print(f'Parlamentares com score: {db.execute(select(func.count(Parlamentar.id)).where(Parlamentar.score_zil.isnot(None))).scalar()}')
    print(f'Proposições enriquecidas: {db.execute(select(func.count(Proposicao.id)).where(Proposicao.contexto_status == \"pronto\")).scalar()}')
"

# Run tests
.venv/bin/python -m pytest tests/ -x -q
```

## Run Frontend

```bash
cd apps/web
npm run dev
# Visit http://localhost:3000/proposicoes to see enriched data
# Visit http://localhost:3000/ranking to see updated scores
```

## Run API Server

```bash
cd apps/api
uvicorn main:app --reload --port 8000
# GET http://localhost:8000/proposicoes — list with enrichment status
# GET http://localhost:8000/proposicoes/{id}/contexto — full enrichment context
```

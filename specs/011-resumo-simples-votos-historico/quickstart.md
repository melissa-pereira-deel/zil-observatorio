# Quickstart: 011 — Resumo Simples no Historico de Votos

## Prerequisites

- Python 3.12 with venv activated (`.venv/bin/activate`)
- Node.js 18+ for frontend
- Database with enriched proposicoes (`contexto_status = "pronto"`)

## Changes Overview

4 files, ~15 lines changed:

1. **Backend schema** (`apps/api/schemas/__init__.py`): Add `resumo_simples: Optional[str] = None` to `VotoHistorico`
2. **Backend router** (`apps/api/routers/parlamentares.py`): Pass `proposicao.resumo_simples` in response construction
3. **Frontend type** (`apps/web/lib/api.ts`): Add `resumo_simples: string | null` to `VotoHistorico`
4. **Frontend render** (`apps/web/app/parlamentar/[parlamentar_id]/page.tsx`): Display `resumo_simples` with 200-char truncation and fallback to `descricao`

## Verification

```bash
# Backend tests (from repo root)
.venv/bin/python3 -m pytest tests/ -x -q

# Frontend type check
cd apps/web && npx tsc --noEmit

# Manual verification
# 1. Start API: cd apps/api && uvicorn main:app --reload
# 2. Start frontend: cd apps/web && npm run dev
# 3. Navigate to any parlamentar profile
# 4. Check "Historico de votos em pautas ZIL" section
# 5. Verify: enriched proposicoes show plain-language resumo instead of technical text
# 6. Verify: truncation with "..." for resumos > 200 chars
# 7. Verify: "ver proposicao" link still works for full text access
```

# Implementation Plan: 012 — Enriquecimento de Dados de Proposicoes

**Branch**: `012-enriquecimento-dados-proposicoes` | **Date**: 2026-04-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-enriquecimento-dados-proposicoes/spec.md`

## Summary

Expandir a ingestao de dados da API da Camara de 25% para ~80% de cobertura. Persistir autores, temas oficiais, regime legislativo, situacao estruturada, cadeia legislativa e resultado autoritativo de votacao. Novo step no pipeline (Detail Sync), 2 tabelas novas (proposicao_autores, proposicao_relacoes), 12 novos campos em Proposicao, 3 em Votacao, 4 novos componentes React, redesign da pagina de detalhe com progressive disclosure.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5 (frontend)
**Primary Dependencies**: FastAPI 0.111, Pydantic 2, SQLAlchemy 2.0, Next.js 14, React 18, Tailwind CSS
**Storage**: SQLite (dev/tests) / PostgreSQL 16 (prod) — JSON generico por ADR-001
**Testing**: pytest 8 (151 testes), TypeScript strict
**Target Platform**: Web (browser)
**Project Type**: Web service (monorepo: API + SPA + Workers)
**Performance Goals**: Backfill 406 proposicoes em <10 min (4 chamadas/prop x 300ms)
**Constraints**: Rate limit API Camara (300ms entre requests), SQLite compatibility (JSON nao JSONB), campos nullable
**Scale/Scope**: 8 features, 3 fases, ~20 arquivos modificados/criados, ~30 novos testes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Evidence |
|-----------|------|--------|----------|
| I. Dados Publicos | Endpoints publicos sem auth? | PASS | GET publicos, sem login |
| II. Apartidario | Sem posicionamento editorial? | PASS | Dados fatuais da Camara |
| III. Transparencia | Dados auditaveis? | PASS | Fonte oficial, temas da Camara |
| IV. Projeto de Estado | Independente de governo? | PASS | Dados estruturais legislativos |
| V. Design System | Tokens zil-*, sem inline? | PASS | Componentes com Tailwind existente |
| VI. API-First | API antes de UI? | PASS | Schemas → endpoints → componentes |
| VII. Qualidade | Testes obrigatorios? | PASS | ~30 novos testes planejados |

**Result**: All gates PASS. No violations.

**Post-Phase 1 Re-check**: All gates remain PASS. New tables use JSON (ADR-001), short imports (ADR-002), JSON(none_as_null=True) (ADR-003). No new external dependencies. No inline styles. No auth required.

## Project Structure

### Documentation (this feature)

```text
specs/012-enriquecimento-dados-proposicoes/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api.md           # Phase 1 output — endpoint contracts
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
apps/api/
├── models/__init__.py           # +12 cols Proposicao, +3 cols Votacao, +2 new tables
├── schemas/__init__.py          # +5 schemas (AutorRead, TemaRead, RelacionadaRead, etc.)
├── routers/
│   ├── legislativo.py           # +filtros, +3 endpoints (autores, temas, relacionadas)
│   └── parlamentares.py         # +1 endpoint (proposicoes de autoria)

apps/web/
├── lib/
│   ├── api.ts                   # +tipos TypeScript
│   └── proposicao.ts            # NEW: helpers situacaoColor, regimeLabel
├── components/
│   ├── AutoresLine.tsx          # NEW: inline author summary
│   ├── AutorCard.tsx            # NEW: detailed author display
│   ├── TramitacaoEvent.tsx      # NEW: timeline event
│   └── CadeiaNode.tsx           # NEW: legislative chain node
├── app/
│   ├── proposicoes/
│   │   ���── page.tsx             # +filtros regime/situacao, +autor no card
│   │   └── [id]/page.tsx        # Redesign com autores, cadeia, tramitacao, relacionadas
│   └── parlamentar/
│       └���─ [parlamentar_id]/page.tsx  # +secao proposicoes de autoria

packages/camara_client/__init__.py     # +3 metodos (autores, temas, relacionadas)

scripts/
├── migrate_012_detail_fields.py       # NEW: migracao idempotente
├── sync_detalhes_proposicoes.py       # NEW: backfill Step 1.5
└── sync_pipeline.py                   # Modificado: +Step 1.5

tests/
├── unit/test_detail_sync.py           # NEW: ~10 testes
├─��� unit/test_proposicao_autores.py    # NEW: ~8 testes
├── integration/test_detail_endpoints.py # NEW: ~12 testes
```

**Structure Decision**: Monorepo existente mantido. 2 tabelas novas (ProposicaoAutor, ProposicaoRelacao), 4 componentes React novos, 1 helper TypeScript novo, 2 scripts Python novos. Nenhum diretorio de alto nivel adicionado.

## Implementation Phases

### Fase 1 — Colunas + campos do detalhe (~2 dias)

| Feature | Escopo |
|---------|--------|
| F-001 | cod_situacao, regime, apreciacao em Proposicao + filtros UI |
| F-004 | aprovacao, sigla_orgao, proposicao_objeto em Votacao |
| F-005 | keywords_camara em Proposicao |
| F-008 | urn_final em Proposicao + badge "virou lei" |

Migracao + backfill dos 12+3 campos a partir de dados ja retornados pela API.

### Fase 2 — Autores + temas (~3 dias)

| Feature | Escopo |
|---------|--------|
| F-002 | Tabela temas_camara JSON + secao na UI |
| F-006 | Tabela ProposicaoAutor + vinculacao FK + componentes |

CamaraClient: +listar_autores_proposicao(), +listar_temas_proposicao().

### Fase 3 — Cadeia + relacionadas (~3 dias)

| Feature | Escopo |
|---------|--------|
| F-003 | Tabela ProposicaoRelacao + cadeia visual + relacionadas |
| F-007 | orgao_situacao + relator_id |

CamaraClient: +listar_relacionadas_proposicao(). Redesign completo da pagina de detalhe.

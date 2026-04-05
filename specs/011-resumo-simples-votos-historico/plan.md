# Implementation Plan: 011 — Resumo Simples no Historico de Votos

**Branch**: `011-resumo-simples-votos-historico` | **Date**: 2026-04-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-resumo-simples-votos-historico/spec.md`

## Summary

Passar o campo `resumo_simples` (texto gerado por IA) da proposicao pelo endpoint `GET /parlamentares/{id}/votos-zil` ate o frontend, substituindo o texto tecnico (`votacao.descricao`) no historico de votos do perfil do parlamentar. Mudanca em 4 arquivos, zero migracoes, fallback preservado.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5 (frontend)
**Primary Dependencies**: FastAPI 0.111, Pydantic 2, SQLAlchemy 2.0, Next.js 14, React 18, Tailwind CSS
**Storage**: SQLite (dev) / PostgreSQL 16 (prod) — campo `resumo_simples` ja existe no modelo `Proposicao`
**Testing**: pytest 8 (151 testes existentes)
**Target Platform**: Web (browser)
**Project Type**: Web service (API + SPA)
**Performance Goals**: N/A — adicao de um campo string ao response existente, impacto negligivel
**Constraints**: Nenhum novo — JOIN ja existe, campo ja preenchido para 406/406 proposicoes
**Scale/Scope**: 4 arquivos modificados, ~15 linhas alteradas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Evidence |
|-----------|------|--------|----------|
| I. Dados Publicos | Endpoint publico sem auth? | PASS | `GET /parlamentares/{id}/votos-zil` ja e publico |
| II. Apartidario | Linguagem neutra? | PASS | `resumo_simples` e factual, sem posicionamento politico |
| III. Transparencia | Dado auditavel? | PASS | Campo vem da proposicao com `contexto_status` e `confianca` rastreaveis |
| IV. Projeto de Estado | Nenhuma feature descontinuada? | PASS | Adicao aditiva, fallback para comportamento atual |
| V. Design System | Tailwind tokens `zil-*`? | PASS | Reutiliza classes existentes (text-zil-fg, text-zil-muted) |
| VI. API-First | Campo na API antes do frontend? | PASS | Schema Pydantic atualizado primeiro |
| VII. Qualidade | Testes passam? | PASS | 151 testes preservados, campo novo e Optional |

**Result**: All gates PASS. No violations. No Complexity Tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/011-resumo-simples-votos-historico/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (minimal — no unknowns)
├── data-model.md        # Phase 1 output
├── contracts/
│   └── api.md           # Phase 1 output — endpoint contract change
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
apps/api/
├── schemas/__init__.py      # VotoHistorico schema — add resumo_simples field
└── routers/parlamentares.py # votos_zil_parlamentar — pass proposicao.resumo_simples

apps/web/
├── lib/api.ts                                      # VotoHistorico type — add resumo_simples
└── app/parlamentar/[parlamentar_id]/page.tsx        # Render resumo_simples with fallback + truncation
```

**Structure Decision**: Existing monorepo structure. No new files or directories created. Changes are additive to 4 existing files across backend and frontend layers.

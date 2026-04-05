# Research: 011 — Resumo Simples no Historico de Votos

## Status: Complete — No Unknowns

This feature has no technical unknowns. All decisions are straightforward:

### Decision 1: How to pass resumo_simples through the API

**Decision**: Add `resumo_simples: Optional[str] = None` to Pydantic `VotoHistorico` schema and populate from the existing `Proposicao` JOIN.

**Rationale**: The JOIN between `Votacao` and `Proposicao` already exists in the endpoint (line 98 of `parlamentares.py`). Adding one field to the response constructor is the minimal change.

**Alternatives considered**:
- Separate API call per votacao to fetch proposicao context → rejected (N+1 problem, unnecessary complexity)
- Embed full `ProposicaoSnippet` in VotoHistorico → rejected (overengineered for one field)

### Decision 2: Frontend text truncation

**Decision**: Truncate `resumo_simples` at ~200 characters with "..." in JavaScript. Existing "ver proposicao" link provides access to full text.

**Rationale**: Keeps vote history items scannable. Most resumos are 1-3 sentences (~150-400 chars), so truncation only affects longer ones.

**Alternatives considered**:
- CSS `line-clamp-3` → rejected (user chose explicit character limit in clarification)
- Full text always → rejected (user chose truncation in clarification)

### Decision 3: Fallback behavior

**Decision**: When `resumo_simples` is null, render `descricao` (current behavior). When present, hide `descricao` entirely.

**Rationale**: Clean UX per user clarification. The citizen only needs one text per vote entry. Technical description adds noise when a plain-language summary exists.

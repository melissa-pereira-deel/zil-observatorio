# Checklist de Arquitetura (A1–A8)

Copiado de `specs/013-tramitacao/spec.md` §9.1, sem reescrever. A spec é a
fonte: mudança de item começa lá. Quem aplica este checklist é o agente
`revisor-arquitetura`.

Como marcar: cada item recebe ✓, ✗ ou N/A, com evidência. ✓ sem evidência conta
como ✗, e N/A exige motivo. O fluxo está em "Revisão de PR", no
[`CLAUDE.md`](../../CLAUDE.md), e o que prova cada item, em
[`como-verificar.md`](como-verificar.md).

| # | Item |
| --- | --- |
| A1 | contrato do brief respeitado (nomes de campos e enums) |
| A2 | migration reversível e única na cadeia |
| A3 | tipos cross-DB (ADR-001) e imports curtos (ADR-002) |
| A4 | `JSON(none_as_null=True)` onde há filtro `IS NOT NULL` (ADR-003) |
| A5 | chamadas externas com `Retry-After` e sem segredo em log |
| A6 | passo de sync registra `IngestionRun` |
| A7 | loader de `data/` funciona dentro do container (CLAUDE.md, "Dados editoriais nos containers") |
| A8 | testes sem rede (golden/replay de TRM-002) |

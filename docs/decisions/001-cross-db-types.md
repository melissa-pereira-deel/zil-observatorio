# ADR-001: Tipos cross-DB no SQLAlchemy (JSON/Uuid em vez de JSONB/ARRAY/UUID)

**Data:** 2026-04-01
**Status:** Aceito

## Contexto

Os modelos originais usavam tipos PostgreSQL-específicos (`JSONB`, `ARRAY`, `UUID` de `sqlalchemy.dialects.postgresql`). Os testes de integração rodam em SQLite in-memory (sem Docker, sem PostgreSQL). Ao tentar criar o schema em SQLite, o SQLAlchemy falhou com `Compiler can't render element of type JSONB`.

## Decisão

Substituir todos os tipos PostgreSQL-específicos por equivalentes cross-DB do SQLAlchemy 2.0:

| Antes | Depois | Motivo |
|-------|--------|--------|
| `postgresql.UUID(as_uuid=True)` | `Uuid(as_uuid=True)` | CHAR(32) no SQLite, UUID no PostgreSQL |
| `postgresql.JSONB` | `JSON` | Sem operadores GIN em SQLite, mas funciona |
| `postgresql.ARRAY(String)` | `JSON` | Arrays como JSON serializado |

Em produção com PostgreSQL, o comportamento é idêntico ao original para os casos de uso da v1.

## Consequências

- **Positivo:** testes rodam sem Docker, em < 2s
- **Positivo:** CI mais rápido e simples
- **Negativo:** perdemos índices GIN em PostgreSQL para `categorias_zil` (impacto mínimo em v1, < 600 parlamentares)
- **Futuro:** quando performance de busca por categoria for necessária, adicionar índice GIN via migration específica para PostgreSQL

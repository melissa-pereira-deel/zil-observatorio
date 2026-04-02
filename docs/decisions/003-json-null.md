# ADR-003: JSON(none_as_null=True) em colunas categorias_zil

**Data:** 2026-04-02
**Status:** Aceito

## Contexto

SQLAlchemy's `JSON` column por padrão usa `none_as_null=False`: Python `None` é armazenado como o JSON literal `"null"`, não como SQL `NULL`. Isso faz com que filtros `IS NOT NULL` retornem linhas onde `categorias_zil = None` (Python), porque a coluna tem valor — o valor é `"null"` (JSON string).

Impacto: os endpoints `GET /proposicoes` e `GET /votacoes` filtram com `.where(Proposicao.categorias_zil.isnot(None))` para retornar apenas itens classificados. Com `none_as_null=False`, itens não classificados apareciam no resultado.

## Decisão

Usar `JSON(none_as_null=True)` especificamente nas colunas `categorias_zil` dos modelos `Proposicao` e `Votacao`:

```python
categorias_zil: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))
```

Isso faz Python `None` ser armazenado como SQL `NULL`, e `IS NOT NULL` funciona corretamente.

## Escopo

Aplicado **apenas** em `categorias_zil` (Proposicao e Votacao). Outras colunas JSON mantêm o padrão `none_as_null=False` porque não são filtradas com `IS NOT NULL`.

## Consequências

- **Positivo:** filtros `IS NOT NULL` funcionam corretamente em SQLite e PostgreSQL
- **Positivo:** semântica clara: `NULL` = "não classificado", lista vazia = possível mas raro
- **Negativo:** nenhum (comportamento esperado para essa coluna)

# Data Model: 011 — Resumo Simples no Historico de Votos

## Entities Affected

### Proposicao (existing — NO changes)

Field `resumo_simples` already exists:
```python
resumo_simples: Mapped[Optional[str]] = mapped_column(Text)
```
- Populated for 406/406 proposicoes via enrichment pipeline
- Text length: typically 100-400 characters
- Nullable: yes (for proposicoes without enrichment)

### VotoHistorico (Pydantic schema — ADD field)

Current:
```python
class VotoHistorico(BaseModel):
    votacao_id: UUID
    data: Optional[datetime] = None
    descricao: Optional[str] = None
    categorias_zil: Optional[list[str]] = None
    voto: str
    direcao_esperada: Optional[str] = None
    alinhado: Optional[bool] = None
    proposicao_label: Optional[str] = None
    proposicao_id: Optional[UUID] = None
```

After:
```python
class VotoHistorico(BaseModel):
    votacao_id: UUID
    data: Optional[datetime] = None
    descricao: Optional[str] = None
    categorias_zil: Optional[list[str]] = None
    voto: str
    direcao_esperada: Optional[str] = None
    alinhado: Optional[bool] = None
    proposicao_label: Optional[str] = None
    proposicao_id: Optional[UUID] = None
    resumo_simples: Optional[str] = None  # NEW — from Proposicao.resumo_simples
```

## Data Flow

```
DB: proposicoes.resumo_simples (Text, nullable)
  ↓ SQLAlchemy JOIN (already exists in endpoint)
Router: proposicao.resumo_simples if proposicao else None
  ↓ Pydantic serialization
API Response: {"resumo_simples": "Cria regras para..."} or {"resumo_simples": null}
  ↓ HTTP JSON
Frontend: v.resumo_simples ?? v.descricao (with truncation at 200 chars)
```

## No Migrations Required

The database schema is unchanged. Only the API response shape gains one optional field.

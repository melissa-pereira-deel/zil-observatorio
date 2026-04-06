# API Contracts: 012 — Enriquecimento de Dados de Proposicoes

**Spec**: [../spec.md](../spec.md) | **Data Model**: [../data-model.md](../data-model.md)

---

## Modified Endpoints

### 1. `GET /proposicoes` — Add filters

**Current**: Filters by `categoria`, `tipo`, `ano`, `limit`, `offset`

**New query parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `regime` | string | No | — | Filter by regime: `URGENCIA`, `ESPECIAL`, `ORDINARIO` |
| `situacao_grupo` | string | No | — | Filter by UI group: `tramitando`, `aprovada`, `arquivada`, `outras` |

**Response**: ProposicaoRead (expanded, see schema changes below)

**Example**:
```
GET /proposicoes?situacao_grupo=tramitando&regime=URGENCIA&tipo=PL&limit=20
```

---

### 2. `GET /proposicoes/{proposicao_id}` — Expanded response

**Current response** (`ProposicaoRead`):
```json
{
  "id": "uuid",
  "fonte_id": "string",
  "fonte": "camara",
  "tipo": "PL",
  "numero": 528,
  "ano": 2020,
  "ementa": "string",
  "situacao": "string (free-text)",
  "data_apresentacao": "2020-03-15",
  "categorias_zil": ["ZIL-ENE"],
  "relevancia_zil": 0.85,
  "url_inteiro_teor": "string",
  "contexto_status": "pronto",
  "resumo_simples": "string",
  "confianca": 0.92
}
```

**New fields added to response**:
```json
{
  "...existing fields...",
  "cod_situacao": 903,
  "regime": "URGENCIA",
  "apreciacao": "Plenario",
  "keywords_camara": "energia,sustentabilidade,meio ambiente",
  "temas_camara": [
    {"cod": 46, "tema": "Meio Ambiente e Desenvolvimento Sustentavel"},
    {"cod": 62, "tema": "Energia, Recursos Hidricos e Minerais"}
  ],
  "urn_final": "urn:lex:br:federal:lei:2021-07-14;14182",
  "url_lei": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/L14182.htm",
  "situacao_grupo": "aprovada",
  "orgao_situacao": "PLEN",
  "relator": {
    "id": "uuid",
    "nome": "Dep. Fulano",
    "partido": "XX",
    "uf": "SP"
  },
  "autor_principal": {
    "id": "uuid",
    "nome": "Dep. Ciclano",
    "partido": "YY",
    "uf": "RJ",
    "foto_url": "string"
  },
  "cadeia": {
    "principal_fonte_id": "12345",
    "anterior_fonte_id": "12340",
    "posterior_fonte_id": "12350"
  }
}
```

**Notes**:
- `url_lei` is computed from `urn_final` (Decision 5). NULL if URN not parseable.
- `situacao_grupo` is computed from `cod_situacao` (Decision 6). Always present when cod_situacao is set.
- `relator` and `autor_principal` are nested snippets (ParlamentarSnippet). NULL if not linked.
- `cadeia` is present when any of principal/anterior/posterior exist. NULL otherwise.

---

### 3. `GET /votacoes/{votacao_id}` — Expanded response

**New fields**:
```json
{
  "...existing fields...",
  "aprovacao": 1,
  "sigla_orgao": "PLEN",
  "proposicao_objeto": "Substitutivo do Relator ao PL 528/2020"
}
```

---

## New Endpoints

### 4. `GET /proposicoes/{proposicao_id}/autores`

**Description**: List all authors of a proposicao with parlamentar linking.

**Response**: `AutorRead[]`

```json
[
  {
    "id": "uuid",
    "nome": "Dep. Fulano da Silva",
    "tipo": "Deputado",
    "ordem": 1,
    "proponente": true,
    "parlamentar": {
      "id": "uuid",
      "nome": "Fulano da Silva",
      "partido": "XX",
      "uf": "SP",
      "foto_url": "https://..."
    }
  },
  {
    "id": "uuid",
    "nome": "Poder Executivo",
    "tipo": "Orgao",
    "ordem": 2,
    "proponente": true,
    "parlamentar": null
  }
]
```

**Status codes**: 200 OK, 404 Proposicao not found

---

### 5. `GET /proposicoes/{proposicao_id}/temas`

**Description**: List official Camara themes for a proposicao.

**Response**: `TemaRead[]`

```json
[
  {"cod": 46, "tema": "Meio Ambiente e Desenvolvimento Sustentavel"},
  {"cod": 62, "tema": "Energia, Recursos Hidricos e Minerais"}
]
```

**Notes**: Returns from `temas_camara` JSON column. Empty array if NULL.

**Status codes**: 200 OK, 404 Proposicao not found

---

### 6. `GET /proposicoes/{proposicao_id}/relacionadas`

**Description**: List related proposicoes grouped by type.

**Query parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tipo_relacao` | string | No | — | Filter by: emenda, substitutivo, parecer, redacao_final, destaque, requerimento, voto_separado, apensada |
| `limit` | int | No | 20 | Max items per page |
| `offset` | int | No | 0 | Pagination offset |

**Response**: `RelacionadaRead[]`

```json
[
  {
    "id": "uuid",
    "tipo_relacao": "emenda",
    "sigla_tipo": "EMC",
    "numero": 15,
    "ano": 2021,
    "ementa": "Emenda ao art. 3 do PL 528/2020...",
    "relacionada_fonte_id": "2245678",
    "proposicao_id_zil": "uuid-or-null"
  }
]
```

**Notes**: `proposicao_id_zil` is the ZIL internal UUID when the related prop exists in our DB. NULL otherwise. Enables deep linking.

**Status codes**: 200 OK, 404 Proposicao not found

---

### 7. `GET /parlamentares/{parlamentar_id}/proposicoes`

**Description**: List proposicoes authored by a parlamentar.

**Query parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tipo` | string | No | — | Filter by proposicao type (PL, PEC, etc.) |
| `limit` | int | No | 20 | Max items |
| `offset` | int | No | 0 | Pagination offset |

**Response**: `ProposicaoRead[]` (same schema as GET /proposicoes)

**Implementation**: JOIN proposicao_autores WHERE parlamentar_id = :id ORDER BY data_apresentacao DESC

**Status codes**: 200 OK, 404 Parlamentar not found

---

## New/Modified Pydantic Schemas

### ProposicaoRead (modified)

```python
class ProposicaoRead(BaseModel):
    # Existing fields
    id: UUID
    fonte_id: str
    fonte: str
    tipo: Optional[str]
    numero: Optional[int]
    ano: Optional[int]
    ementa: Optional[str]
    situacao: Optional[str]
    data_apresentacao: Optional[date]
    categorias_zil: Optional[list[str]]
    relevancia_zil: Optional[float]
    url_inteiro_teor: Optional[str]
    contexto_status: Optional[str]
    resumo_simples: Optional[str]
    confianca: Optional[float]

    # New Phase 1 fields
    cod_situacao: Optional[int] = None
    regime: Optional[str] = None
    apreciacao: Optional[str] = None
    keywords_camara: Optional[str] = None
    urn_final: Optional[str] = None
    url_lei: Optional[str] = None           # computed from urn_final
    situacao_grupo: Optional[str] = None     # computed from cod_situacao

    # New Phase 2 fields
    temas_camara: Optional[list[dict]] = None
    autor_principal: Optional[ParlamentarSnippet] = None  # expanded from FK

    # New Phase 3 fields
    orgao_situacao: Optional[str] = None
    relator: Optional[ParlamentarSnippet] = None
    cadeia: Optional[CadeiaRead] = None
```

### ParlamentarSnippet (new)

```python
class ParlamentarSnippet(BaseModel):
    id: UUID
    nome: str
    partido: Optional[str]
    uf: Optional[str]
    foto_url: Optional[str] = None
```

### AutorRead (new)

```python
class AutorRead(BaseModel):
    id: UUID
    nome: str
    tipo: str
    ordem: int
    proponente: bool
    parlamentar: Optional[ParlamentarSnippet] = None
```

### TemaRead (new)

```python
class TemaRead(BaseModel):
    cod: int
    tema: str
```

### RelacionadaRead (new)

```python
class RelacionadaRead(BaseModel):
    id: UUID
    tipo_relacao: str
    sigla_tipo: Optional[str]
    numero: Optional[int]
    ano: Optional[int]
    ementa: Optional[str]
    relacionada_fonte_id: str
    proposicao_id_zil: Optional[UUID] = None  # ZIL internal ID if in DB
```

### CadeiaRead (new)

```python
class CadeiaRead(BaseModel):
    principal_fonte_id: Optional[str] = None
    anterior_fonte_id: Optional[str] = None
    posterior_fonte_id: Optional[str] = None
```

### VotacaoRead (modified)

```python
class VotacaoRead(BaseModel):
    # Existing fields...

    # New Phase 1 fields
    aprovacao: Optional[int] = None       # 1=approved, 0=rejected, null=unknown
    sigla_orgao: Optional[str] = None
    proposicao_objeto: Optional[str] = None
```

---

## New CamaraClient Methods

### `listar_autores_proposicao(proposicao_id: str) -> list[dict]`

```
GET https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id}/autores
```

Returns list of author dicts with `uri`, `nome`, `tipo`, `ordemAssinatura`, `proponente`.

### `listar_temas_proposicao(proposicao_id: str) -> list[dict]`

```
GET https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id}/temas
```

Returns list of theme dicts with `codTema`, `tema`.

### `listar_relacionadas_proposicao(proposicao_id: str, max_pages: int = 10) -> list[dict]`

```
GET https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id}/relacionadas?pagina={n}
```

Paginated. Fetches up to `max_pages` (Decision 4: cap at 200 items). Returns list of related proposicao dicts.

---

## Error Handling

| Scenario | Response | HTTP Status |
|----------|----------|-------------|
| Proposicao not found | `{"detail": "Proposicao nao encontrada"}` | 404 |
| Parlamentar not found | `{"detail": "Parlamentar nao encontrado"}` | 404 |
| Invalid situacao_grupo | `{"detail": "situacao_grupo invalido: 'xyz'. Use: tramitando, aprovada, arquivada, outras"}` | 422 |
| Invalid regime filter | `{"detail": "regime invalido"}` | 422 |
| Invalid tipo_relacao | `{"detail": "tipo_relacao invalido"}` | 422 |

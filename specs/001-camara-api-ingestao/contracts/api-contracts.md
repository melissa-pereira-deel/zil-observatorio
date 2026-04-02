# API Contracts: ZIL Observatório REST API

**Feature**: `001-camara-api-ingestao`
**Date**: 2026-04-01
**Base URL**: `/` (FastAPI, porta 8000 em desenvolvimento)
**Autenticação**: Nenhuma — todos os endpoints são públicos (Princípio I)
**Content-Type**: `application/json`
**Docs interativas**: `/docs` (Swagger UI), `/redoc`

---

## Convenções

- `UUID` representado como string no formato `"550e8400-e29b-41d4-a716-446655440000"`
- `datetime` em ISO 8601: `"2024-03-15T14:30:00"`
- `score_zil` é `float | null` — `null` indica dados insuficientes
- Paginação via `?page=1&per_page=50` (máx. 100 por página)
- Erros retornam `{"detail": "mensagem legível"}` com código HTTP apropriado

---

## 1. GET /parlamentares

**Descrição**: Lista parlamentares com Score ZIL, filtros e paginação.
**User Story**: US-1 (ranking), US-2 (acesso jornalista)

### Query Parameters

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `fonte` | str? | — | `camara` ou `senado` |
| `partido` | str? | — | Sigla (ex: `PT`, `PL`) |
| `uf` | str? | — | Sigla do estado (ex: `SP`, `GO`) |
| `ordem` | str? | `score_desc` | `score_desc`, `score_asc`, `nome` |
| `page` | int? | `1` | Página (≥ 1) |
| `per_page` | int? | `50` | Itens por página (1–100) |

### Response 200

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "nome": "João da Silva",
    "partido": "PL",
    "uf": "SP",
    "foto_url": "https://www.camara.leg.br/internet/deputado/bandep/74050.jpg",
    "fonte": "camara",
    "score_zil": 6.42,
    "total_votos_zil": 23
  }
]
```

**`score_zil`**: `null` quando deputado não tem votos em pautas ZIL com direção definida.

### Erros

| Código | Condição |
|--------|----------|
| `422` | Parâmetro inválido (ex: `ordem=invalido`) |

### Acceptance Test

- SC-001: resposta com ≥ 487 itens após ingestão completa (com `fonte=camara`)
- US-2 AC-1: campos `id`, `nome`, `partido`, `uf`, `score_zil`, `total_votos_zil` presentes

---

## 2. GET /parlamentares/{parlamentar_id}

**Descrição**: Perfil completo de um parlamentar.
**User Story**: US-1 (perfil), US-2

### Path Parameters

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `parlamentar_id` | UUID | ID interno do parlamentar |

### Response 200

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "fonte_id": "74050",
  "fonte": "camara",
  "nome": "João da Silva",
  "nome_civil": "João Aparecido da Silva",
  "partido": "PL",
  "uf": "SP",
  "foto_url": "https://www.camara.leg.br/internet/deputado/bandep/74050.jpg",
  "email": "dep.joaosilva@camara.leg.br",
  "redes_sociais": null,
  "frentes_parlamentares": null,
  "score_zil": 6.42,
  "score_atualizado_em": "2024-03-15T14:30:00"
}
```

### Erros

| Código | Condição |
|--------|----------|
| `404` | Parlamentar não encontrado |
| `422` | UUID malformado |

---

## 3. GET /parlamentares/{parlamentar_id}/votos-zil

**Descrição**: Histórico de votos do parlamentar em pautas ZIL.
**User Story**: US-1 AC-2 (histórico), US-2 AC-2 (filtro por categoria)

### Path Parameters

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `parlamentar_id` | UUID | ID interno do parlamentar |

### Query Parameters

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `categoria` | str? | — | Filtrar por categoria ZIL (ex: `ZIL-MIN`) |

### Response 200

```json
[
  {
    "votacao_id": "6a7b8c9d-...",
    "data": "2024-08-14T15:22:00",
    "descricao": "PL 1234/2023 - Regulamentação do processamento de lítio",
    "categorias_zil": ["ZIL-MIN", "ZIL-ENE"],
    "voto": "sim",
    "direcao_esperada": "sim",
    "alinhado": true
  }
]
```

**`alinhado`**: `true`/`false` quando `direcao_esperada` está definida; `null` caso contrário.
Ordenação: mais recente primeiro.

### Erros

| Código | Condição |
|--------|----------|
| `404` | Parlamentar não encontrado |

### Acceptance Test

- US-1 AC-2: ao menos 1 votação com `alinhado != null` após ingestão
- US-2 AC-2: filtro `?categoria=ZIL-MIN` retorna apenas votações com `ZIL-MIN` em `categorias_zil`

---

## 4. GET /parlamentares/partidos/ranking

**Descrição**: Score médio por partido.

### Query Parameters

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `fonte` | str? | — | `camara` ou `senado` |

### Response 200

```json
[
  {
    "partido": "PSOL",
    "score_medio": 7.83,
    "membros": 12
  }
]
```

Ordenado por `score_medio DESC`.

---

## 5. GET /proposicoes

**Descrição**: Lista proposições classificadas por pauta ZIL.
**User Story**: US-2 (acesso a dados)

### Query Parameters

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `categoria` | str? | — | Ex: `ZIL-FER` |
| `tipo` | str? | — | Ex: `PL`, `PEC`, `PLP` |
| `ano` | int? | — | Ano de apresentação |
| `page` | int? | `1` | |
| `per_page` | int? | `50` | |

### Response 200

```json
[
  {
    "id": "...",
    "fonte_id": "1234567",
    "fonte": "camara",
    "tipo": "PL",
    "numero": 1234,
    "ano": 2023,
    "ementa": "Regulamenta a industrialização de minerais estratégicos...",
    "situacao": "Em tramitação",
    "data_apresentacao": "2023-05-10",
    "categorias_zil": ["ZIL-MIN"],
    "relevancia_zil": 0.87,
    "url_inteiro_teor": "https://www.camara.leg.br/proposicoesWeb/..."
  }
]
```

### Erros

| Código | Condição |
|--------|----------|
| `422` | Parâmetro inválido |

---

## 6. GET /votacoes

**Descrição**: Lista votações classificadas por pauta ZIL.

### Query Parameters

| Parâmetro | Tipo | Padrão | Descrição |
|-----------|------|--------|-----------|
| `categoria` | str? | — | Ex: `ZIL-MIN` |
| `ano` | int? | — | |
| `page` | int? | `1` | |
| `per_page` | int? | `50` | |

### Response 200

```json
[
  {
    "id": "...",
    "fonte_id": "abc123",
    "fonte": "camara",
    "data": "2024-08-14T15:22:00",
    "descricao": "Votação nominal - PL 1234/2023",
    "resultado": "aprovado",
    "votos_sim": 312,
    "votos_nao": 142,
    "categorias_zil": ["ZIL-MIN", "ZIL-ENE"],
    "direcao_esperada": "sim",
    "peso": 1.0
  }
]
```

---

## 7. GET /votacoes/{votacao_id}/votos

**Descrição**: Lista todos os votos individuais de uma votação.

### Response 200

```json
[
  {
    "parlamentar_id": "...",
    "parlamentar_nome": "João da Silva",
    "parlamentar_partido": "PL",
    "parlamentar_uf": "SP",
    "voto": "sim",
    "orientacao_partido": "sim"
  }
]
```

### Erros

| Código | Condição |
|--------|----------|
| `404` | Votação não encontrada |

---

## 8. GET /stats

**Descrição**: Estatísticas gerais da plataforma, incluindo timestamp da última ingestão.
**User Story**: US-3 AC-1 (observabilidade)

### Response 200

```json
{
  "total_parlamentares": 513,
  "total_deputados": 513,
  "total_senadores": 0,
  "total_proposicoes_zil": 847,
  "total_votacoes_zil": 312,
  "score_medio": 1.24,
  "ultima_atualizacao": "2024-03-15T14:30:00"
}
```

**`ultima_atualizacao`**: timestamp do `finalizado_em` do último `IngestionRun` com
`status="success"`. `null` se nenhuma ingestão completada ainda.

### Acceptance Test

- US-3 AC-1: campos `total_parlamentares`, `total_deputados`, `total_votacoes_zil`,
  `score_medio`, `ultima_atualizacao` presentes
- SC-001: `total_deputados ≥ 487` após ingestão completa

---

## 9. GET /health

**Descrição**: Health check básico (sem autenticação).

### Response 200

```json
{"status": "ok"}
```

---

## Resumo de Endpoints por User Story

| User Story | Endpoints |
|------------|-----------|
| US-1 (cidadão consulta score) | `GET /parlamentares`, `GET /parlamentares/{id}`, `GET /parlamentares/{id}/votos-zil` |
| US-2 (jornalista exporta dados) | `GET /parlamentares`, `GET /parlamentares/{id}/votos-zil`, `GET /proposicoes`, `GET /votacoes` |
| US-3 (operador monitora saúde) | `GET /stats` |

## Endpoints obrigatórios para testes (Princípio VII)

`/parlamentares`, `/votacoes`, `/stats` — testes obrigatórios para merge em main.

# Data Model: Ingestão da API da Câmara dos Deputados

**Feature**: `001-camara-api-ingestao`
**Date**: 2026-04-01

---

## Entidades e Responsabilidades

### 1. Parlamentar
**Tabela**: `parlamentares`
**Propósito**: Representa um deputado ou senador. Identificado univocamente por `(fonte_id, fonte)`.
**Lifecycle**: Criado na primeira ingestão; atualizado via upsert a cada sync semanal.

| Coluna | Tipo | Obrig. | Descrição |
|--------|------|--------|-----------|
| `id` | UUID PK | ✅ | ID interno gerado |
| `fonte_id` | str(50) | ✅ | ID na fonte (ex: "74050" na API da Câmara) |
| `fonte` | enum | ✅ | `camara` ou `senado` |
| `nome` | str(255) | ✅ | Nome parlamentar |
| `nome_civil` | str(255) | — | Nome civil (disponível no detalhe do deputado) |
| `partido` | str(50) | — | Sigla do partido atual |
| `uf` | str(2) | — | UF da representação |
| `foto_url` | str(500) | — | URL da foto oficial |
| `email` | str(255) | — | Email parlamentar |
| `score_zil` | numeric(5,2) | — | Score ZIL calculado (-10.00 a +10.00) ou NULL |
| `score_atualizado_em` | datetime | — | Timestamp do último recálculo |
| `created_at` | datetime | ✅ | |
| `updated_at` | datetime | ✅ | |

**Unique**: `(fonte_id, fonte)`
**Índices**: `partido`, `uf`, `score_zil`

---

### 2. Proposicao
**Tabela**: `proposicoes`
**Propósito**: Matéria legislativa (PL, PEC, MPV...) classificada por pauta ZIL.
**Lifecycle**: Criado na primeira detecção via votação; atualizado via upsert.

| Coluna | Tipo | Obrig. | Descrição |
|--------|------|--------|-----------|
| `id` | UUID PK | ✅ | |
| `fonte_id` | str(50) | ✅ | ID na API da Câmara |
| `fonte` | enum | ✅ | `camara` |
| `tipo` | str(20) | — | `PL`, `PEC`, `PLP`, `MPV`... |
| `numero` | int | — | Número da proposição |
| `ano` | int | — | Ano de apresentação |
| `ementa` | text | — | Ementa resumida |
| `ementa_detalhada` | text | — | Ementa completa |
| `data_apresentacao` | date | — | |
| `situacao` | str(255) | — | Situação atual na tramitação |
| `categorias_zil` | ARRAY(str) | — | Ex: `["ZIL-MIN", "ZIL-ENE"]` |
| `relevancia_zil` | numeric(3,2) | — | Score de relevância 0.0–1.0 |
| `classificacao_automatica` | bool | ✅ | `true` = keyword, `false` = curadoria humana |
| `url_inteiro_teor` | str(500) | — | |
| `created_at` | datetime | ✅ | |

**Unique**: `(fonte_id, fonte)`
**Índices**: `(tipo, ano)`, GIN em `categorias_zil`

---

### 3. Votacao
**Tabela**: `votacoes`
**Propósito**: Evento de votação nominal no plenário ou comissão. Vinculado a uma Proposicao.
**Lifecycle**: Criado na ingestão; nunca atualizado (imutável após criação).

| Coluna | Tipo | Obrig. | Descrição |
|--------|------|--------|-----------|
| `id` | UUID PK | ✅ | |
| `fonte_id` | str(50) | ✅ | ID na API da Câmara |
| `fonte` | enum | ✅ | `camara` |
| `proposicao_id` | UUID FK | — | FK → `proposicoes.id` |
| `data` | datetime | — | Data e hora do registro |
| `descricao` | text | — | Texto descritivo da votação |
| `resultado` | str(50) | — | `aprovado`, `rejeitado`, `prejudicado` |
| `votos_sim` | int | — | Contagem agregada |
| `votos_nao` | int | — | Contagem agregada |
| `abstencoes` | int | — | Contagem de abstenções |
| `categorias_zil` | ARRAY(str) | — | NULL = não classificada |
| `direcao_esperada` | str(10) | — | `sim` ou `nao` — definido editorial |
| `peso` | numeric(3,1) | — | Padrão 1.0; até 3.0 para votações de plenário final |
| `created_at` | datetime | ✅ | |

**Unique**: `(fonte_id, fonte)`
**Índices**: `data`; GIN em `categorias_zil` (via Proposicao, mas útil aqui também)

**Nota sobre `peso`**: na v0 todas as votações têm peso 1.0. O comitê editorial
definirá pesos maiores em YAML futuro.

---

### 4. Voto
**Tabela**: `votos`
**Propósito**: Posição individual de um parlamentar em uma votação específica.
**Lifecycle**: Criado na ingestão; nunca atualizado.

| Coluna | Tipo | Obrig. | Descrição |
|--------|------|--------|-----------|
| `id` | UUID PK | ✅ | |
| `votacao_id` | UUID FK | ✅ | FK → `votacoes.id` |
| `parlamentar_id` | UUID FK | ✅ | FK → `parlamentares.id` |
| `voto` | enum | ✅ | `sim`, `nao`, `abstencao`, `ausente`, `obstrucao`, `artigo_17` |
| `orientacao_partido` | str(20) | — | Orientação do partido nesta votação |
| `orientacao_governo` | str(20) | — | Orientação do governo (Fase 2) |
| `created_at` | datetime | ✅ | |

**Unique**: `(votacao_id, parlamentar_id)` — garante idempotência

---

### 5. ScoreVotacao
**Tabela**: `scores_votacao`
**Propósito**: Contribuição granular de um voto ao Score ZIL. Registra impacto,
peso e justificativa para auditabilidade (Princípio III).
**Lifecycle**: Criado/atualizado no recálculo do score.

| Coluna | Tipo | Obrig. | Descrição |
|--------|------|--------|-----------|
| `id` | UUID PK | ✅ | |
| `parlamentar_id` | UUID FK | ✅ | FK → `parlamentares.id` |
| `votacao_id` | UUID FK | ✅ | FK → `votacoes.id` |
| `categoria_zil` | str(20) | ✅ | Categoria principal da votação |
| `impacto` | numeric(4,2) | ✅ | -1.0, 0.0, ou +1.0 |
| `peso` | numeric(3,1) | ✅ | Peso da votação aplicado |
| `justificativa` | text | — | Ex: "Voto: sim \| Esperado: sim → alinhado" |
| `created_at` | datetime | ✅ | |

**Unique**: `(parlamentar_id, votacao_id)` — idempotência no recálculo
**Índices**: `parlamentar_id`, `categoria_zil`

---

### 6. IngestionRun ⬅ NOVA
**Tabela**: `ingestion_runs`
**Propósito**: Registro auditável de cada execução de ingestão (FR-009, FR-010,
User Story 3). Permite detectar falhas silenciosas e retornar `ultima_atualizacao`
no `/stats`.
**Lifecycle**: Criado ao início; atualizado ao final. Imutável após `finalizado_em`.

| Coluna | Tipo | Obrig. | Descrição |
|--------|------|--------|-----------|
| `id` | UUID PK | ✅ | |
| `tipo` | str(30) | ✅ | `deputados`, `votacoes`, `full_sync` |
| `ano` | int | — | Ano processado (votações); NULL para deputados |
| `status` | str(20) | ✅ | `running`, `success`, `failed`, `partial` |
| `iniciado_em` | datetime | ✅ | |
| `finalizado_em` | datetime | — | NULL enquanto em execução |
| `registros_processados` | int | ✅ | Total de registros lidos da fonte |
| `registros_criados` | int | ✅ | Novos registros inseridos |
| `registros_atualizados` | int | ✅ | Registros existentes atualizados |
| `erros_count` | int | ✅ | Número de erros não-fatais |
| `erro_detalhes` | JSONB | — | Array de `{endpoint, status_code, mensagem, tentativa}` |

**Sem FKs** — tabela de log independente.
**Índice**: `(tipo, status, iniciado_em DESC)` — para a query do `/stats`.

---

## Diagrama de Relacionamentos

```
IngestionRun (log, sem FKs)

Parlamentar ──< Voto >── Votacao ──> Proposicao
     │                      │
     └──< ScoreVotacao >────┘
```

**Cardinalidades**:
- `Parlamentar` 1:N `Voto` — um deputado tem muitos votos
- `Votacao` 1:N `Voto` — uma votação tem muitos votos individuais
- `Proposicao` 1:N `Votacao` — uma proposição pode ter múltiplas votações
- `Parlamentar` 1:N `ScoreVotacao` — registros de impacto por votação ZIL
- `Votacao` 1:1 `ScoreVotacao` (por parlamentar) — unique constraint

---

## Fórmula do Score ZIL

```
Score = (Σ alinhamento_i × peso_i) / (Σ |peso_i|) × 10

alinhamento_i:
  +1.0  se voto == direcao_esperada
  -1.0  se voto != direcao_esperada AND voto ∈ {sim, nao}
   0.0  se voto ∈ {ausente, abstencao, obstrucao, artigo_17}

peso_i:
  3.0   votação final de plenário (definido editorial)
  2.0   votação de comissão importante (definido editorial)
  1.0   default (v0: todas as votações)
  0.5   votação processual (definido editorial)
```

**Restrição**: Score só calculado se `Votacao.direcao_esperada IS NOT NULL`.
Se deputado não tem votos ZIL com direção definida → `score_zil = NULL` → aparece
no ranking com indicação "sem dados suficientes".

---

## Migrações

Na v0, as tabelas são criadas pelo `Base.metadata.create_all` no lifespan da API
(modo desenvolvimento). Para produção, usar Alembic (Fase 2).

**Nova tabela nesta feature**: `ingestion_runs` — adicionar ao `models/__init__.py`.
**Novo UniqueConstraint**: `scores_votacao (parlamentar_id, votacao_id)` — verificar
se já existe antes de adicionar (não estava no scaffold original).

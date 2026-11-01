# Discovery: Dados de Proposicoes — API da Camara dos Deputados

**Data:** 2026-04-05
**Autores:** Product Manager, Software Architect, UI/UX Designer (agentes especializados)
**Escopo:** Mapeamento completo dos dados disponiveis na API da Camara vs. dados atualmente utilizados pelo ZIL Observatorio, com propostas de features priorizadas.

> **Atualizado por [`DISCOVERY-TRAMITACAO.md`](DISCOVERY-TRAMITACAO.md)
> (2026-10-30).** Situação estruturada, cadeia legislativa, órgão e relator e
> lei resultante foram revistos lá, com dados conferidos na API: `urnFinal`
> vem sempre nulo, a coluna `tramitacoes` nunca foi preenchida, e a situação
> por linha de `/tramitacoes` não é histórica. O resto deste documento segue
> como registro.

---

## 1. Inventario da API da Camara

### 1.1 Endpoints Disponiveis para Proposicoes

| Endpoint | Descricao | Usado pelo ZIL? |
|----------|-----------|-----------------|
| `GET /proposicoes` | Lista com 23 filtros (tipo, ano, autor, partido, UF, keywords, tema, situacao, datas) | Sim (parcial) |
| `GET /proposicoes/{id}` | Detalhe completo com 20+ campos | Sim (parcial) |
| `GET /proposicoes/{id}/autores` | Autoria completa (nome, tipo, partido, ordem, proponente) | Nao |
| `GET /proposicoes/{id}/temas` | 32 temas oficiais da Camara | Nao |
| `GET /proposicoes/{id}/tramitacoes` | Historico completo de tramitacao | Parcial (JSON nao exposto) |
| `GET /proposicoes/{id}/votacoes` | Votacoes vinculadas | Sim |
| `GET /proposicoes/{id}/relacionadas` | Emendas, pareceres, substitutivos, apensadas | Nao |
| `GET /votacoes/{id}` | Detalhe da votacao com campos extras | Parcial |
| `GET /referencias/proposicoes/*` | Dados de referencia (97 situacoes, 32 temas, 544 tipos) | Nao |

### 1.2 Campos do Detalhe da Proposicao (GET /proposicoes/{id})

| Campo API | Tipo | Exemplo | Armazenado? | Exibido? |
|-----------|------|---------|-------------|----------|
| `id` | int | 2613303 | Sim (`fonte_id`) | Nao |
| `siglaTipo` | string | "PL" | Sim (`tipo`) | Sim |
| `numero` | int | 1584 | Sim | Sim |
| `ano` | int | 2026 | Sim | Sim |
| `ementa` | string | "Dispoe sobre..." | Sim | Sim |
| `ementaDetalhada` | string | texto longo | Sim | Nao |
| `dataApresentacao` | datetime | "2026-04-01T17:34" | Sim | Sim |
| `urlInteiroTeor` | string | URL do PDF | Sim | Sim |
| **`keywords`** | string | "IA, Regulacao, Tecnologia" | **Nao** | **Nao** |
| **`codTipo`** | int | 139 | **Nao** | **Nao** |
| **`descricaoTipo`** | string | "Projeto de Lei" | **Nao** | **Nao** |
| **`uriPropPrincipal`** | string/null | URI da proposicao-mae | **Nao** | **Nao** |
| **`uriPropAnterior`** | string/null | versao anterior | **Nao** | **Nao** |
| **`uriPropPosterior`** | string/null | versao Senado | **Nao** | **Nao** |
| **`urnFinal`** | string/null | URN da lei resultante | **Nao** | **Nao** |

### 1.3 Campos do Status da Proposicao (statusProposicao)

| Campo API | Tipo | Exemplo | Armazenado? | Exibido? |
|-----------|------|---------|-------------|----------|
| `descricaoSituacao` | string | "Pronta para Pauta" | Sim (`situacao`) | Sim |
| `despacho` | string | texto do despacho | Sim (`ultimo_despacho`) | Nao |
| **`codSituacao`** | int | 924 | **Nao** | **Nao** |
| **`regime`** | string | "Urgencia (Art. 154)" | **Nao** | **Nao** |
| **`apreciacao`** | string | "Sujeita ao Plenario" | **Nao** | **Nao** |
| **`siglaOrgao`** | string | "PLEN", "CCJ" | **Nao** | **Nao** |
| **`uriUltimoRelator`** | string/null | URI do relator | **Nao** | **Nao** |

### 1.4 Autores (GET /proposicoes/{id}/autores)

| Campo | Tipo | Exemplo | Status |
|-------|------|---------|--------|
| `nome` | string | "Baleia Rossi" | Nao persistido |
| `tipo` | string | "Deputado(a)" | Nao persistido |
| `codTipo` | int | 10000 | Nao persistido |
| `ordemAssinatura` | int | 1 | Nao persistido |
| `proponente` | int | 1 | Nao persistido |
| `uri` | string | URI do deputado | Nao persistido |

**Nota:** O modelo `Proposicao` ja tem `autor_principal_id` (FK) e `autores` (JSON), mas ambos estao NULL para todas as 406 proposicoes.

### 1.5 Temas Oficiais (GET /proposicoes/{id}/temas)

32 temas disponiveis, incluindo:

| codTema | Tema | Relevancia para ZIL |
|---------|------|---------------------|
| 54 | Energia, Recursos Hidricos e Minerais | Alta (ZIL-ENE, ZIL-MIN) |
| 62 | Ciencia, Tecnologia e Inovacao | Alta (ZIL-SEM, ZIL-DIG) |
| 64 | Agricultura, Pecuaria, Pesca e Extrativismo | Alta (ZIL-AGR, ZIL-FER) |
| 66 | Industria, Comercio e Servicos | Alta (ZIL-COM) |
| 57 | Defesa e Seguranca | Alta (ZIL-DEF) |
| 46 | Educacao | Media (ZIL-EDU) |
| 55 | Relacoes Internacionais e Comercio Exterior | Media (ZIL-COM) |
| 40 | Economia | Media (varias categorias) |

### 1.6 Proposicoes Relacionadas (GET /proposicoes/{id}/relacionadas)

Retorna TODAS as proposicoes vinculadas. Para proposicoes grandes, pode chegar a centenas:

| Tipo | Siglas | Exemplo (PEC 45/2019) | Valor |
|------|--------|----------------------|-------|
| Emendas | EMC, EMP, EMS, EMA | 219 emendas | Alto — mostra disputas |
| Pareceres | PAR, PRL, PRLP | 3 pareceres | Alto — opiniao das comissoes |
| Substitutivos | SBT | 1 substitutivo | Critico — texto que foi votado |
| Requerimentos | REQ, RPDR | 115 requerimentos | Baixo — processual |
| Destaques | DTQ | 32 destaques | Medio — votacoes separadas |
| PLs relacionados | PL | variavel | Alto — apensadas |

### 1.7 Votacoes — Campos Nao Utilizados

| Campo API | Tipo | Status | Valor |
|-----------|------|--------|-------|
| **`aprovacao`** | int (1/0/null) | Nao armazenado | Resultado autoritativo (elimina inferencia) |
| **`siglaOrgao`** | string | Nao armazenado | Qual orgao votou |
| **`proposicaoObjeto`** | string | Nao armazenado | O que foi efetivamente votado |

---

## 2. Estado Atual do Modelo ZIL

### 2.1 Campos do Modelo Proposicao

| Campo | Populado | Exposto API | Exibido UI | Fonte |
|-------|----------|-------------|------------|-------|
| fonte_id | Sempre | Sim | Nao | API Camara |
| tipo, numero, ano | Sempre | Sim | Sim | API Camara |
| ementa | Sempre | Sim | Sim (collapsed) | API Camara |
| ementa_detalhada | As vezes | Nao | Nao | API Camara |
| situacao | As vezes | Sim | Sim (badge) | API Camara |
| data_apresentacao | As vezes | Sim | Sim | API Camara |
| url_inteiro_teor | As vezes | Sim | Sim (link) | API Camara |
| autor_principal_id | **Nunca** | Nao | Nao | Nao implementado |
| autores (JSON) | **Nunca** | Nao | Nao | Nao implementado |
| tramitacoes (JSON) | **Nunca** | Nao | Nao | Nao implementado |
| ultimo_despacho | As vezes | Nao | Nao | API Camara |
| categorias_zil | As vezes | Sim | Sim (badges) | Classificador interno |
| relevancia_zil | As vezes | Sim | Nao | Classificador interno |
| resumo_simples | Sempre (406/406) | Sim | Sim | Pipeline IA |
| glossario | As vezes | Sim | Sim (accordion) | Pipeline IA |
| impacto_zil | As vezes | Sim | Sim (blockquote) | Pipeline IA |
| leis_referenciadas | As vezes | Sim | Sim (accordion) | Pipeline IA |
| confianca | As vezes | Sim | Sim (badge) | Pipeline IA |
| metadata_extra (JSON) | Nunca | Nao | Nao | Reservado |

### 2.2 Gap Analysis

```
Dados disponiveis na API:  ~40 campos por proposicao
Dados armazenados no ZIL:  ~17 campos (42%)
Dados expostos na API ZIL:  ~15 campos (38%)
Dados exibidos na UI:       ~10 campos (25%)

Campos de alto valor NAO utilizados:  12
  - keywords, temas, autores, regime, apreciacao, codSituacao,
    orgao, relator, cadeia legislativa, urnFinal, relacionadas, aprovacao
```

---

## 3. Roadmap de Features — Visao do Product Manager

### 3.1 Features Priorizadas

| # | Feature | Prioridade | Complexidade | Dados Novos |
|---|---------|------------|-------------|-------------|
| F-001 | Situacao Estruturada com Filtros | **P0** | S (<1 dia) | codSituacao, regime, apreciacao |
| F-002 | Temas Oficiais da Camara | **P0** | M (1-3 dias) | /proposicoes/{id}/temas |
| F-003 | Cadeia Legislativa | **P0** | M (1-3 dias) | uriPropPrincipal/Anterior/Posterior, relacionadas |
| F-004 | Resultado Autoritativo de Votacao | **P1** | S (<1 dia) | votacoes[].aprovacao |
| F-005 | Keywords da Camara | **P1** | S (<1 dia) | keywords (ja lido, nao persistido) |
| F-006 | Autoria Completa com Vinculacao | **P1** | M (1-3 dias) | /proposicoes/{id}/autores |
| F-007 | Orgao Atual e Relator | **P2** | S (<1 dia) | siglaOrgao, uriUltimoRelator |
| F-008 | Lei Resultante | **P2** | S (<1 dia) | urnFinal |

### 3.2 User Stories (P0)

**F-001 — Situacao Estruturada:**
- Como cidadao engajado, quero filtrar proposicoes por "Prontas para Pauta", para focar minha atencao nos projetos que serao votados em breve e onde pressao popular tem efeito.
- Como jornalista, quero identificar proposicoes com regime de urgencia, para cobrir projetos com deadline constitucional.
- Como pesquisador, quero separar proposicoes arquivadas das ativas, para analisar tendencias sem poluicao.

**F-002 — Temas Oficiais:**
- Como cidadao, quero ver os temas oficiais da Camara, para entender do que se trata sem decifrar siglas ZIL.
- Como analista, quero cruzar categorias ZIL com temas oficiais, para validar a classificacao automatica.

**F-003 — Cadeia Legislativa:**
- Como cidadao acompanhando o Marco Legal da IA, quero ver que o texto votado foi o substitutivo (nao o original), para entender o que de fato foi aprovado.
- Como ativista, quero ver emendas propostas, para identificar quem tentou modificar trechos criticos.
- Como cidadao, quero navegar da Camara ao Senado e vice-versa, para acompanhar o ciclo bicameral.

**F-006 — Autoria:**
- Como cidadao, quero saber quem propoe leis de soberania industrial, para avaliar acao legislativa proativa alem de votos reativos.

### 3.3 Metricas de Sucesso

| Feature | Metrica | Alvo |
|---------|---------|------|
| F-001 | % proposicoes com cod_situacao | 100% |
| F-002 | % proposicoes com pelo menos 1 tema | >90% |
| F-003 | % proposicoes com link de cadeia | >40% |
| F-004 | Reducao de badges "Aprovado*" (inferido) | 0% |
| F-005 | % proposicoes com keywords | >80% |
| F-006 | % proposicoes com autor_principal_id | >95% |

---

## 4. Arquitetura Tecnica — Visao do Software Architect

### 4.1 Mudancas no Modelo de Dados

#### Fase 1 — Novos campos em Proposicao (baixo risco)

```python
# 12 novos campos, todos nullable (compativel SQLite/Postgres)
keywords_camara: Mapped[Optional[str]] = mapped_column(Text)          # string com termos
cod_situacao: Mapped[Optional[int]] = mapped_column(Integer)           # codigo numerico
regime: Mapped[Optional[str]] = mapped_column(String(100))             # "Urgencia", "Especial"
apreciacao: Mapped[Optional[str]] = mapped_column(String(200))         # "Plenario", "Conclusiva"
descricao_tipo: Mapped[Optional[str]] = mapped_column(String(200))     # "Projeto de Lei"
cod_tipo: Mapped[Optional[int]] = mapped_column(Integer)
orgao_situacao: Mapped[Optional[str]] = mapped_column(String(20))      # "PLEN", "CCJ"
urn_final: Mapped[Optional[str]] = mapped_column(String(500))          # URN da lei resultante
prop_principal_id: Mapped[Optional[str]] = mapped_column(String(50))   # fonte_id da principal
prop_anterior_id: Mapped[Optional[str]] = mapped_column(String(50))
prop_posterior_id: Mapped[Optional[str]] = mapped_column(String(50))
temas_camara: Mapped[Optional[list]] = mapped_column(JSON(none_as_null=True))  # [{codTema, tema}]
detalhes_sincronizados_em: Mapped[Optional[datetime]] = mapped_column(DateTime)
```

#### Fase 1 — Novos campos em Votacao

```python
aprovacao: Mapped[Optional[int]] = mapped_column(Integer)              # 1/0/null
sigla_orgao: Mapped[Optional[str]] = mapped_column(String(20))
proposicao_objeto: Mapped[Optional[str]] = mapped_column(Text)
```

#### Fase 2 — Nova tabela ProposicaoAutor (normalizada)

```python
class ProposicaoAutor(Base):
    __tablename__ = "proposicao_autores"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    proposicao_id: Mapped[UUID] = mapped_column(ForeignKey("proposicoes.id"))
    parlamentar_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("parlamentares.id"))
    nome: Mapped[str] = mapped_column(String(300))
    tipo: Mapped[str] = mapped_column(String(100))        # "Deputado", "Orgao"
    partido: Mapped[Optional[str]] = mapped_column(String(20))
    uf: Mapped[Optional[str]] = mapped_column(String(2))
    ordem_assinatura: Mapped[int] = mapped_column(Integer, default=1)
    proponente: Mapped[bool] = mapped_column(Boolean, default=False)
```

#### Fase 3 — Nova tabela ProposicaoRelacao (grafo)

```python
class ProposicaoRelacao(Base):
    __tablename__ = "proposicao_relacoes"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    proposicao_id: Mapped[UUID] = mapped_column(ForeignKey("proposicoes.id"))
    relacionada_fonte_id: Mapped[str] = mapped_column(String(50))
    relacionada_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("proposicoes.id"))
    tipo_relacao: Mapped[str] = mapped_column(String(50))  # "emenda", "substitutivo", "parecer"
    sigla_tipo: Mapped[Optional[str]] = mapped_column(String(20))
    numero: Mapped[Optional[int]] = mapped_column(Integer)
    ano: Mapped[Optional[int]] = mapped_column(Integer)
    ementa: Mapped[Optional[str]] = mapped_column(Text)
```

### 4.2 Pipeline de Ingestao

Novo **Step 1.5: Detail Sync** no pipeline existente (`sync_pipeline.py`):

```
Step 1: Discovery (existente)
Step 1.5: Detail Sync (NOVO)
  Para cada proposicao com detalhes_sincronizados_em IS NULL:
    1. GET /proposicoes/{id} → preencher campos Fase 1
    2. GET /proposicoes/{id}/autores → popular ProposicaoAutor (Fase 2)
    3. GET /proposicoes/{id}/temas → popular temas_camara
    4. GET /proposicoes/{id}/relacionadas → popular ProposicaoRelacao (Fase 3)
    Sleep 300ms entre requests. Commit por proposicao.
Step 2: Votacao Sync (existente)
Step 3: Enrichment (existente)
Step 4: Score Recalculation (existente)
```

**Estimativa backfill:** 406 proposicoes x 4 chamadas x 300ms = ~8 minutos.

### 4.3 Novos Endpoints da API

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `GET /proposicoes` | Modificado | +filtros: regime, cod_situacao, orgao_situacao, tema |
| `GET /proposicoes/{id}` | Modificado | +campos: keywords, regime, orgao, temas, autores, cadeia |
| `GET /proposicoes/{id}/autores` | Novo | Lista de autores com vinculacao a parlamentares |
| `GET /proposicoes/{id}/tramitacoes` | Novo | Historico de tramitacao (do JSON existente) |
| `GET /proposicoes/{id}/relacionadas` | Novo | Proposicoes relacionadas agrupadas por tipo |
| `GET /parlamentares/{id}/proposicoes` | Novo | Proposicoes de autoria do parlamentar |
| `GET /temas` | Novo | Lista dos 32 temas oficiais |

### 4.4 Fases de Implementacao

```
Fase 1: Colunas + campos do detalhe (1-2 dias)
  - Adicionar 12 colunas em Proposicao, 3 em Votacao
  - Popular a partir de chamadas API ja existentes
  - Atualizar schemas Pydantic e tipos TypeScript
  - ~12 novos testes

Fase 2: Autores + temas (2-3 dias)
  - Criar tabela ProposicaoAutor
  - Novo metodo CamaraClient.listar_autores_proposicao()
  - Novo metodo CamaraClient.listar_temas_proposicao()
  - Vincular autores a parlamentares existentes (match por fonte_id)
  - ~11 novos testes

Fase 3: Relacionadas + cadeia (2-3 dias)
  - Criar tabela ProposicaoRelacao
  - Classificador de tipo_relacao por siglaTipo
  - Endpoint de grafo com paginacao
  - ~7 novos testes
```

### 4.5 Riscos Tecnicos

| Risco | Impacto | Mitigacao |
|-------|---------|-----------|
| Rate limiting da Camara no backfill | Medio | Sleep 300ms (ja implementado), batch com Celery |
| Volume de relacionadas (centenas) | Medio | Cap max_pages=10, agrupar por tipo na UI |
| Dados null para proposicoes antigas | Baixo | Todos os campos Optional, UI com fallback |
| Staleness de codSituacao | Medio | Re-sync semanal para proposicoes ativas |
| SQLite vs Postgres (JSON) | Baixo | JSON generico por ADR-001, testado em SQLite |

---

## 5. Design de UI/UX — Visao do Designer

### 5.1 Redesign da Pagina de Detalhe

**Hierarquia de informacao (acima da dobra):**

```
[← Voltar]

PL 528/2020    [URGENCIA]    [Em Tramitacao]    [Contexto ✓]

Resumo simples em linguagem acessivel sobre o que este
projeto de lei pretende fazer para o cidadao.

[Ver ementa tecnica ↓]

"Impacto ZIL: Esta proposicao fortalece a cadeia produtiva..."

Dep. Fulano de Tal (PT-SP) e mais 3 autores
Apresentada em 15/03/2020 · Plenario · Texto completo ↗

[Energia] [Digital] [Semicondutores]
```

**Secoes da pagina (ordem):**

| # | Secao | Visibilidade | Conteudo |
|---|-------|-------------|----------|
| 1 | Header | Sempre | Titulo + regime + status + resumo + autores |
| 2 | Ementa | Collapsed (`<details>`) | Texto tecnico original |
| 3 | Impacto ZIL | Sempre (quando disponivel) | Blockquote verde |
| 4 | Cadeia Legislativa | Sempre (quando ha cadeia) | Timeline: Camara → Senado → Lei |
| 5 | Posicao ZIL + Votacoes | Sempre | Sintese + lista existente |
| 6 | Autores | Proponente visivel, co-autores collapsed | Cards com link para /parlamentar |
| 7 | Tramitacao | 3 recentes + collapsed | Timeline vertical |
| 8 | Relacionadas | Collapsed por tipo | Emendas, pareceres, substitutivos |
| 9 | Contexto IA | Collapsed | Glossario + leis referenciadas (existente) |
| 10 | Metadata | Sempre (quiet) | Temas oficiais + keywords |

### 5.2 Novos Componentes

| Componente | Arquivo | Funcao | Reutiliza |
|-----------|---------|--------|-----------|
| `AutoresLine` | `components/AutoresLine.tsx` | Linha compacta: "Dep. Fulano (PT-SP) e mais 3" | Link |
| `AutorCard` | `components/AutorCard.tsx` | Card de autor com avatar e link | ParlamentarAvatar |
| `TramitacaoEvent` | `components/TramitacaoEvent.tsx` | Evento na timeline (data + orgao + despacho) | — |
| `CadeiaNode` | `components/CadeiaNode.tsx` | No na cadeia legislativa (dot + label + link) | Link |
| `situacaoColor()` | `lib/proposicao.ts` | Helper: situacao → cor do badge | Badge existente |

### 5.3 Melhorias na Lista de Proposicoes

**Novos filtros:**
- Dropdown "Situacao" (Em tramitacao / Prontas para Pauta / Aprovadas / Arquivadas)
- Dropdown "Regime" (Urgencia / Especial / Ordinario)

**Card aprimorado:**
```
PL 528/2020    [Urgencia]    ● Em Tramitacao
Resumo simples truncado em 2 linhas...
Ementa tecnica truncada em 2 linhas...
Dep. Fulano de Tal (PT-SP)
[Energia] [Digital]                     15/03/2020
```

### 5.4 Progressive Disclosure

| Camada | Conteudo | Visibilidade | Justificativa |
|--------|----------|-------------|---------------|
| 1 (instantaneo) | Titulo, regime, status, resumo | Sempre | Responde "o que e?" em 3s |
| 2 (instantaneo) | Autor, categorias, data, orgao | Sempre | Responde "quem/quando/onde?" |
| 3 (1 clique) | Ementa tecnica | Collapsed | Texto juridico, nao para publico geral |
| 4 (instantaneo) | Cadeia legislativa | Sempre (quando existe) | Contexto critico, compacto |
| 5 (instantaneo) | Votacoes | Sempre | Dados primarios |
| 6 (1 clique) | Co-autores, tramitacao completa | Collapsed | Volume potencialmente alto |
| 7 (1 clique) | Relacionadas por tipo | Collapsed | Pode ser centenas |
| 8 (1 clique) | Glossario, leis referenciadas | Collapsed | Contexto de suporte |

### 5.5 Acessibilidade

- Badges de regime usam `zil-orange` sobre `zil-orange-light` (contraste 4.8:1, passa WCAG AA)
- `<details>/<summary>` nativo: acessivel por teclado sem ARIA adicional
- Links para parlamentar com texto descritivo (nao "clique aqui")
- Timeline como lista semantica (`<ol>`) com `aria-label`
- Nenhum novo token de design necessario — sistema existente cobre todos os casos

### 5.6 Responsividade

| Componente | Mobile (375px) | Desktop (1024px) |
|-----------|---------------|-------------------|
| Header badges | Wrap em nova linha | Inline |
| AutoresLine | Full width abaixo do titulo | Inline |
| Timeline | `orgao_nome` escondido | Visivel |
| Cadeia | Vertical, full width | Mesmo |
| Relacionadas | Accordions full width | Mesmo |

---

## 6. Ordem de Implementacao Recomendada

```
Sprint 1 (Semana 1) — Fundacao de Dados
├── F-001: Situacao Estruturada [S]     ← maior impacto, habilita filtros
├── F-005: Keywords Camara [S]          ← quase gratis (ja lido, so persistir)
└── F-004: Resultado Autoritativo [S]   ← corrige problema existente

Sprint 2 (Semana 2) — Contexto e Navegacao
├── F-002: Temas Oficiais [M]          ← nova chamada no pipeline
└── F-006: Autoria Completa [M]        ← nova chamada + vinculacao FK

Sprint 3 (Semana 3) — Profundidade
├── F-003: Cadeia Legislativa [M]      ← feature mais transformadora
├── F-007: Orgao Atual / Relator [S]   ← depende de F-001
└── F-008: Lei Resultante [S]          ← depende de F-001
```

**Justificativa:**
1. Sprint 1 entrega 3 melhorias rapidas que corrigem problemas existentes e habilitam filtros
2. Sprint 2 adiciona contexto que nao existia (temas + autoria)
3. Sprint 3 constroi a narrativa legislativa completa (cadeia + orgao + lei)

---

## 7. Conclusao

O ZIL utiliza apenas **25% dos dados disponiveis** na API da Camara. As 8 features propostas cobrem os 12 campos de maior valor nao utilizados, organizadas em 3 sprints de complexidade crescente.

**Impacto esperado:**
- Proposicoes passam de "ficha tecnica" para "narrativa legislativa completa"
- Cidadao consegue filtrar por situacao real (tramitando vs arquivada)
- Autoria conecta proposicoes a parlamentares (acao proativa, nao so votos)
- Cadeia legislativa resolve o problema de "texto votado != texto original"
- Dados da Camara (temas, keywords) ancoram credibilidade da classificacao ZIL

**Estimativa total:** ~2-3 semanas de desenvolvimento para todas as 8 features.

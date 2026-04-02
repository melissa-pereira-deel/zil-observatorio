# Feature Specification: Pipeline de Enriquecimento de Texto Legislativo

**Feature Branch**: `002-legislative-enrichment-pipeline`
**Created**: 2026-04-02
**Status**: Draft
**Abordagem escolhida**: D — Híbrido (extração de citações + scraping Planalto + síntese LLM com contexto injetado)

---

## Contexto e Problema

Textos legislativos retornados pelas APIs da Câmara e do Senado são escritos em linguagem jurídica técnica, com referências cruzadas a outras leis (ex: "Altera o § 3º do art. 4º da Lei nº 9.472, de 1997..."), siglas de programas governamentais (PADIS, CFEM, PATEN) e jargão parlamentar. Um cidadão sem formação jurídica não consegue entender o que a proposição faz, quais leis ela modifica, nem por que o ZIL a considera relevante para soberania industrial.

**Exemplo real — PL 1847/2024 (ementa da API):**
> "Altera a Lei nº 14.744, de 21 de novembro de 2023, para incluir a margem de preferência de até 25% (vinte e cinco por cento) nas licitações e contratações diretas da administração pública federal para produtos e serviços de tecnologia da informação e comunicação fabricados por empresas beneficiárias do PADIS."

O usuário precisa saber: o que é o PADIS? O que diz o art. modificado? Por que isso importa para semicondutores? Qual é o impacto prático?

### Por que Abordagem D — Híbrido

| Abordagem | Problema |
|-----------|---------|
| A — LLM puro | Alucina leis e artigos; não verificável |
| B — Regras + templates | Rígido; não escala para variações de texto |
| C — RAG completo | Complexidade alta; exige embedding store; latência |
| **D — Híbrido** | Extração determinística + contexto verificável + LLM para síntese |

A Abordagem D resolve o problema de alucinação ao injetar no LLM apenas o texto dos artigos referenciados — obtidos diretamente do Planalto.gov.br — em vez de pedir ao modelo que "saiba" o conteúdo das leis. O LLM sintetiza e explica; nunca inventa.

---

## User Scenarios & Testing

### User Story 1 — Cidadão lê proposição em linguagem acessível (Priority: P1)

Um cidadão acessa `/proposicoes` no frontend e clica em uma proposição. Em vez de ver a ementa técnica da API, ele vê:
- Um **resumo em linguagem simples** (3–5 frases) explicando o que o projeto faz
- A **ementa original** (sempre visível, para transparência)
- Um **glossário inline** dos termos técnicos detectados (PADIS → definição; CFEM → definição)
- **Contexto das leis modificadas**: o texto dos artigos referenciados, obtido do Planalto
- Um **badge de confiança** indicando se o contexto foi verificado ou está pendente

**Por que P1**: É o objetivo principal da feature. Sem isso, o ranking tem scores mas o cidadão não entende _por que_ cada proposição importa.

**Independent Test**: Endpoint `GET /proposicoes/{id}/contexto` retorna `resumo_simples`, `glossario`, e `leis_referenciadas` com pelo menos um artigo resolvido — pode ser testado contra qualquer proposição já no banco com citação de lei.

**Acceptance Scenarios**:

1. **Given** uma proposição com `ementa` contendo "Lei nº 14.744/2023 art. 3º", **When** `GET /proposicoes/{id}/contexto`, **Then** resposta inclui `leis_referenciadas[0].artigo_texto` com o texto do art. 3º obtido do Planalto, `resumo_simples` em português corrente, e `confianca >= 0.7`

2. **Given** uma proposição com ementa que não cita nenhuma lei, **When** `GET /proposicoes/{id}/contexto`, **Then** resposta retorna `resumo_simples` baseado apenas na ementa, `leis_referenciadas: []`, `confianca >= 0.5`, sem erros

3. **Given** o Planalto.gov.br retorna 404 para uma lei citada, **When** pipeline de enriquecimento executa, **Then** `leis_referenciadas[n].status = "nao_encontrada"`, o resumo é gerado sem esse contexto, e `confianca` é reduzida proporcionalmente

---

### User Story 2 — Desenvolvedor consulta contexto via API (Priority: P2)

Um desenvolvedor ou jornalista acessa a API REST para construir visualizações ou análises externas. Precisa de contexto estruturado, verificável, e com metadados de proveniência.

**Por que P2**: Habilita usos além do frontend ZIL — análise de dados, jornalismo investigativo, scraping ético para pesquisas. Alinhado com o princípio "dados públicos, acesso livre".

**Independent Test**: `GET /proposicoes/{id}/contexto` com `Accept: application/json` retorna resposta estruturada validável por schema Pydantic sem depender do frontend.

**Acceptance Scenarios**:

1. **Given** proposição enriquecida, **When** `GET /proposicoes/{id}/contexto`, **Then** resposta JSON inclui `versao_pipeline` (ex: "1.0"), `enriquecido_em` (ISO 8601), `fontes` com URLs verificáveis do Planalto, e `modelo_llm` usado

2. **Given** proposição com `contexto_status = "pendente"`, **When** `GET /proposicoes/{id}/contexto`, **Then** resposta retorna HTTP 200 com `{"status": "pendente", "ementa_original": "..."}` — nunca HTTP 404 ou 500

3. **Given** proposição com enriquecimento desatualizado (> 30 dias), **When** qualquer GET, **Then** resposta inclui flag `contexto_desatualizado: true` sem bloquear a requisição

---

### User Story 3 — Pipeline assíncrono enriquece novas proposições automaticamente (Priority: P2)

Quando uma nova proposição é ingerida pelo crawler da Câmara, o pipeline de enriquecimento é disparado automaticamente via Celery. O editorial não precisa fazer nada manualmente.

**Por que P2**: Sem automação, o enriquecimento precisaria ser trigado manualmente para cada nova proposição — impraticável à medida que o corpus cresce.

**Independent Test**: Após `task_ingest_camara` criar uma nova `Proposicao`, a task `task_enriquecer_proposicao` aparece na fila Celery em até 60 segundos.

**Acceptance Scenarios**:

1. **Given** `task_ingest_camara` cria `Proposicao` com `categorias_zil != null`, **When** signal pós-commit ou beat schedule executa, **Then** `task_enriquecer_proposicao(proposicao_id)` é enfileirada em até 60s

2. **Given** `task_enriquecer_proposicao` falha por timeout do Planalto, **When** Celery retry policy executa, **Then** task é retentada até 3 vezes com backoff exponencial (30s, 90s, 270s) antes de marcar `contexto_status = "falhou"`

3. **Given** `task_enriquecer_proposicao` conclui com sucesso, **When** frontend consulta a proposição, **Then** badge muda de "Contexto pendente" para "Contexto verificado" sem necessidade de reload forçado

---

### User Story 4 — Frontend exibe contexto enriquecido na página /proposicoes (Priority: P3)

O frontend `/proposicoes` exibe o resumo em linguagem simples acima da ementa técnica, com um accordion "Ver contexto completo" que revela glossário + artigos de lei.

**Por que P3**: Depende de P1 (API) e P2 (pipeline). O valor para o usuário final depende de dados enriquecidos existirem.

**Independent Test**: Página `/proposicoes` renderiza com `resumo_simples` para proposições enriquecidas e badge "Contexto pendente" para as demais — não quebra com dados ausentes.

**Acceptance Scenarios**:

1. **Given** proposição com `contexto_status = "pronto"`, **When** usuário acessa `/proposicoes`, **Then** card mostra `resumo_simples`, badge verde "Contexto verificado", e accordion "Ver fontes" expansível

2. **Given** proposição com `contexto_status = "pendente"`, **When** usuário acessa `/proposicoes`, **Then** card mostra ementa original e badge cinza "Contexto pendente" — sem erros de runtime

3. **Given** usuário expande accordion "Ver fontes", **When** clicar em link de lei, **Then** link abre URL verificável no Planalto.gov.br em nova aba

---

### Edge Cases

- **Lei revogada**: Planalto retorna página com banner "REVOGADA". Pipeline DEVE detectar (keyword "REVOGADA" no HTML), salvar `status = "revogada"`, e o LLM deve mencionar explicitamente na síntese.
- **Artigos aninhados**: Citações como "inciso III do § 2º do art. 4º da Lei 9.472/1997" exigem regex que capture hierarquia `artigo → parágrafo → inciso → alínea`. Pipeline extrai o artigo pai mínimo que contém o inciso.
- **Medidas Provisórias convertidas**: MP nº 1234/2023 pode ter sido convertida em Lei nº 14.xxx/2024. O pipeline DEVE tentar ambas as URLs e seguir o redirecionamento.
- **Ementa > 4.000 tokens**: Proposições com ementa muito longa exigem truncamento estratégico antes de enviar ao LLM. Pipeline usa `ementa[:2000]` + `exposicao_de_motivos[:2000]` se disponível.
- **Ausência de exposição de motivos**: Muitas proposições não têm exposição de motivos na API. Pipeline DEVE funcionar com ementa apenas; `exposicao_de_motivos` é opcional.
- **Rate limiting do Planalto**: Planalto.gov.br pode retornar 429 ou timeout. Pipeline usa `asyncio.sleep(2)` entre requests e respeita `Retry-After` header quando presente.
- **Planalto sem HTML estruturado**: Algumas leis antigas têm conteúdo em PDF não parseável. Pipeline detecta `Content-Type: application/pdf`, marca artigo como `status = "pdf_nao_parseavel"`, e prossegue sem esse artigo.
- **Múltiplas citações da mesma lei**: Se ementa cita "art. 3º" e "art. 7º" da mesma lei, pipeline faz apenas 1 request ao Planalto e extrai ambos os artigos do mesmo HTML (cache hit).
- **Proposição sem categoria ZIL**: Pipeline DEVE ser acionado apenas para proposições com `categorias_zil != null`. Proposições não classificadas ficam com `contexto_status = null`.
- **Falha da API Claude**: Se a API do Claude retornar erro 5xx, pipeline salva os artigos resolvidos (etapa RESOLVE concluída) e marca `contexto_status = "llm_falhou"` para retry apenas da etapa AUGMENT.
- **Texto idêntico ao já enriquecido**: Se `ementa` não mudou desde o último enriquecimento, pipeline DEVE pular (idempotência baseada em hash SHA-256 da ementa).

---

## Requirements

### Functional Requirements

- **FR-001**: Sistema DEVE extrair citações legislativas de `ementa` e `ementa_detalhada` usando regex determinístico cobrindo os padrões: `Lei nº X.XXX/YYYY`, `Lei Complementar nº X/YYYY`, `Medida Provisória nº X/YYYY`, `art. N`, `§ N`, `inciso [IVXLCDM]+`, `alínea [a-z]`
- **FR-002**: Sistema DEVE construir URL canônica do Planalto.gov.br para cada lei citada e fazer HTTP GET com timeout de 10s, user-agent identificável, e seguir redirecionamentos até 3 saltos
- **FR-003**: Sistema DEVE cachear o HTML de cada lei em `lei_artigos` (banco), evitando requests duplicados ao Planalto para a mesma lei+artigo dentro de 30 dias
- **FR-004**: Sistema DEVE injetar no prompt do LLM APENAS o texto dos artigos resolvidos e a ementa original — sem conhecimento externo implícito. Prompt DEVE incluir instrução explícita: "Use apenas o contexto fornecido. Se não tiver informação suficiente, diga que não sabe."
- **FR-005**: Sistema DEVE gerar via LLM: `resumo_simples` (3–5 frases, linguagem C1), `glossario` (dict termo → definição, máximo 10 termos), e `impacto_zil` (1–2 frases explicando relevância para soberania industrial)
- **FR-006**: Sistema DEVE armazenar resultado do enriquecimento diretamente em colunas de `proposicoes` (não em tabela separada) para simplificar queries do frontend
- **FR-007**: Sistema DEVE expor endpoint `GET /proposicoes/{id}/contexto` retornando schema `ProposicaoContexto` com: `resumo_simples`, `glossario`, `leis_referenciadas`, `impacto_zil`, `confianca`, `contexto_status`, `enriquecido_em`, `fontes`, `modelo_llm`, `versao_pipeline`
- **FR-008**: Sistema DEVE disparar `task_enriquecer_proposicao` via Celery para toda proposição nova com `categorias_zil != null`
- **FR-009**: Sistema DEVE implementar retry com backoff exponencial (máximo 3 tentativas) para falhas de rede ao acessar Planalto.gov.br
- **FR-010**: Sistema DEVE calcular `confianca` como fração de artigos citados que foram resolvidos com sucesso: `artigos_resolvidos / max(artigos_citados, 1)`, valor entre 0.0 e 1.0
- **FR-011**: Sistema DEVE ser idempotente: se `ementa` não mudou (hash SHA-256 igual), reprocessamento DEVE ser ignorado com log "skipped: ementa unchanged"
- **FR-012**: Sistema DEVE suportar re-enriquecimento forçado via endpoint `POST /proposicoes/{id}/enriquecer` (admin-only por query param `?force=true`)
- **FR-013**: Frontend DEVE exibir badge de status: "Contexto verificado" (verde, confianca >= 0.7), "Contexto parcial" (amarelo, 0 < confianca < 0.7), "Contexto pendente" (cinza, status = pendente), "Contexto indisponível" (vermelho, status = falhou) — sem nunca esconder a ementa original

### Key Entities

- **`lei_artigos`** (nova tabela): Cache de artigos de lei obtidos do Planalto. Chave: `(lei_id, numero_artigo)`. Campos: `lei_id` (ex: "9472-1997"), `numero_artigo` (ex: "4"), `texto_artigo`, `url_planalto`, `status` (resolvido | revogada | nao_encontrada | pdf_nao_parseavel), `obtido_em`, `expira_em` (30 dias)

- **`Proposicao`** (8 novos campos): `contexto_status` (null | pendente | processando | pronto | falhou | llm_falhou), `resumo_simples`, `glossario` (JSON), `impacto_zil`, `leis_referenciadas` (JSON), `confianca`, `ementa_hash` (SHA-256), `enriquecido_em`

- **`ProposicaoContexto`** (novo schema Pydantic): Response model para `GET /proposicoes/{id}/contexto`. Inclui todos os campos de enriquecimento + `versao_pipeline` + `modelo_llm` + `fontes` (lista de URLs Planalto)

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% das proposições com `categorias_zil != null` têm `contexto_status != null` após 24h da ingestão (pipeline assíncrono processou todos)
- **SC-002**: `confianca >= 0.7` em pelo menos 60% das proposições (ou seja, >= 60% dos artigos citados foram resolvidos com sucesso no Planalto)
- **SC-003**: Latência de `GET /proposicoes/{id}/contexto` < 200ms em P95 (dados servidos do banco, não computados on-demand)
- **SC-004**: Zero alucinações verificadas em auditoria manual de 20 proposições: `resumo_simples` e `glossario` NÃO contêm informações que não estejam nos artigos injetados ou na ementa original
- **SC-005**: Enriquecimento de uma proposição (todas as 5 etapas) completa em < 30s em condições normais de rede
- **SC-006**: `task_enriquecer_proposicao` é idempotente: executar duas vezes com a mesma proposição não altera o banco na segunda execução (exceto `enriquecido_em` se forçado)
- **SC-007**: Frontend `/proposicoes` não quebra (sem erros de runtime) quando `contexto_status = null` ou `falhou` — degradação gracioso verificada em teste E2E

---

## Assumptions

- Claude API (Anthropic) está disponível via variável de ambiente `ANTHROPIC_API_KEY` — a feature não funciona sem ela; pipeline marca `contexto_status = "llm_falhou"` se ausente
- Planalto.gov.br é acessível a partir do servidor de produção; estrutura HTML das leis é suficientemente estável para parsing com BeautifulSoup (verificado empiricamente em 2026-04)
- O modelo LLM a ser usado é `claude-haiku-4-5` por custo/latência; `claude-sonnet-4-6` pode ser configurado via env var `ENRICHMENT_MODEL` para qualidade superior
- Celery + Redis já estão no stack (v1); nenhuma infraestrutura adicional é necessária
- `ementa` e `ementa_detalhada` são os únicos campos de texto legislativo disponíveis na API da Câmara via ingestão atual; `inteiro_teor` (PDF) está fora do escopo desta feature
- Autenticação não existe no v1; `POST /proposicoes/{id}/enriquecer?force=true` é protegido por query param secreto (`?admin_token=...`) como medida mínima — auth real é backlog
- Senado Federal não está no escopo desta feature (Senado é feature 002 do backlog); pipeline processa apenas proposições `fonte = "camara"`
- Cache de `lei_artigos` expira em 30 dias; leis raramente mudam, mas emendas constitucionais e MPs podem alterar artigos — TTL de 30 dias é aceitável para v1
- Testes de integração usam SQLite in-memory (ADR-001); mock do Planalto HTTP via `respx` ou `responses`; mock da API Claude via `unittest.mock`

---

## Abordagem D — Detalhamento Técnico das 5 Etapas

### Etapa 1 — EXTRACT (regex determinístico)

```
Input:  proposicao.ementa + proposicao.ementa_detalhada
Output: lista de CitacaoLegislativa(tipo, numero, ano, artigo, paragrafo, inciso, alinea)
```

Padrões regex em ordem de precedência:
```
Lei nº (\d[\d\.]+)/(\d{4})      → CitacaoLei(numero, ano)
Lei Complementar nº (\d+)/(\d{4}) → CitacaoLC(numero, ano)
Medida Provisória nº (\d+)/(\d{4}) → CitacaoMP(numero, ano)
art\.?\s*(\d+[°º]?)              → artigo
§\s*(\d+[°º]?)                   → paragrafo
inciso\s+([IVXLCDM]+)            → inciso
alínea\s+["\u201c]?([a-z])["\u201d]? → alinea
```

### Etapa 2 — RESOLVE (Planalto scraping + cache)

```
Input:  lista de CitacaoLegislativa
Output: lista de ArtigoResolvido(lei_id, artigo, texto, url, status)
```

URL pattern: `https://www.planalto.gov.br/ccivil_03/_ato{inicio}-{fim}/{ano}/lei/l{num_sem_pontos}.htm`
Para Lei Complementar: `.../lei/lcp/lcp{num}.htm`
Para MP: `.../mpv/mpv{num}.htm`

Cache lookup antes de HTTP request. Upsert em `lei_artigos` após resolução.

### Etapa 3 — AUGMENT (LLM com contexto injetado)

```
Input:  ementa + lista de ArtigoResolvido.texto
Output: resumo_simples, glossario, impacto_zil
```

Prompt estruturado:
```
[CONTEXTO DAS LEIS REFERENCIADAS]
{artigos_injetados}

[PROPOSIÇÃO A EXPLICAR]
{ementa}

[TAREFA]
Com base APENAS no contexto acima, sem usar conhecimento externo:
1. Escreva um resumo em 3-5 frases em português claro (nível C1)
2. Identifique até 10 termos técnicos e defina cada um em 1 frase
3. Explique em 1-2 frases por que esta proposição é relevante para soberania industrial
```

### Etapa 4 — VALIDATE (Pydantic + confiança)

```
Input:  resposta LLM (JSON) + lista ArtigoResolvido
Output: EnriquecimentoValidado com confianca calculada
```

Validação Pydantic + cálculo de `confianca = resolvidos / max(citados, 1)`.
Rejeita resposta LLM que mencione fatos não presentes no contexto injetado (heurística: nomes próprios de empresas não mencionados na ementa).

### Etapa 5 — SERVE (persistência + endpoint)

```
Input:  EnriquecimentoValidado
Output: proposicao atualizada no banco + HTTP 200 em GET /proposicoes/{id}/contexto
```

Update atômico: todos os 8 campos novos atualizados em única transação. `contexto_status` muda de `"processando"` para `"pronto"` ou `"falhou"` atomicamente.

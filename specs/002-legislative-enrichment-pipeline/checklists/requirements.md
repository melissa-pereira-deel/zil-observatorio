# Requirements Checklist: Pipeline de Enriquecimento de Texto Legislativo

**Purpose**: Verificar que todos os requisitos funcionais e de qualidade foram implementados antes do merge
**Created**: 2026-04-02
**Feature**: [spec.md](../spec.md)

## Modelo de Dados

- [ ] CHK001 Nova tabela `lei_artigos` criada com migration Alembic (campos: lei_id, numero_artigo, texto_artigo, url_planalto, status, obtido_em, expira_em)
- [ ] CHK002 8 novos campos adicionados ao model `Proposicao`: contexto_status, resumo_simples, glossario (JSON), impacto_zil, leis_referenciadas (JSON), confianca, ementa_hash, enriquecido_em
- [ ] CHK003 `contexto_status` usa tipo `JSON`/`String` compatível com SQLite in-memory (ADR-001)
- [ ] CHK004 `glossario` e `leis_referenciadas` usam `JSON(none_as_null=True)` (ADR-003)
- [ ] CHK005 UniqueConstraint em `lei_artigos` para `(lei_id, numero_artigo)` — sem duplicatas de cache

## Etapa EXTRACT — Regex

- [ ] CHK006 Regex extrai `Lei nº X.XXX/YYYY` com e sem pontuação no número (ex: 9.472 e 9472)
- [ ] CHK007 Regex extrai `Lei Complementar nº X/YYYY`
- [ ] CHK008 Regex extrai `Medida Provisória nº X/YYYY`
- [ ] CHK009 Regex extrai `art. N`, `§ N`, `inciso [IVXLCDM]+`, `alínea [a-z]`
- [ ] CHK010 Extração de hierarquia aninhada: `inciso III do § 2º do art. 4º` → artigo=4, paragrafo=2, inciso=III
- [ ] CHK011 Testes unitários cobrindo pelo menos 10 padrões de ementa reais

## Etapa RESOLVE — Planalto Scraping

- [ ] CHK012 Função `build_planalto_url(tipo, numero, ano)` constrói URL correta para lei ordinária, lei complementar, e MP
- [ ] CHK013 HTTP client usa timeout de 10s e user-agent identificável (`ZIL-Observatorio/1.0`)
- [ ] CHK014 Segue redirecionamentos (max 3 saltos)
- [ ] CHK015 Detecta página com banner "REVOGADA" e salva `status = "revogada"`
- [ ] CHK016 Detecta `Content-Type: application/pdf` e salva `status = "pdf_nao_parseavel"`
- [ ] CHK017 Retorna 404 do Planalto → `status = "nao_encontrada"` (sem exception não tratada)
- [ ] CHK018 Cache lookup antes de HTTP request: mesmo `(lei_id, artigo)` dentro do TTL (30 dias) não faz request novo
- [ ] CHK019 Múltiplas citações da mesma lei fazem apenas 1 HTTP request (cache hit na segunda)

## Etapa AUGMENT — LLM

- [ ] CHK020 Prompt injeta APENAS texto dos artigos resolvidos + ementa — sem conhecimento implícito
- [ ] CHK021 Prompt inclui instrução explícita de não usar conhecimento externo
- [ ] CHK022 Truncamento aplicado quando contexto total > 3.500 tokens: priorizar ementa + artigos mais relevantes
- [ ] CHK023 Modelo padrão é `claude-haiku-4-5`; configurável via env var `ENRICHMENT_MODEL`
- [ ] CHK024 Resposta LLM parseada como JSON com Pydantic; falha de parse → retry 1x, depois `contexto_status = "llm_falhou"`
- [ ] CHK025 `resumo_simples` tem entre 3 e 5 frases; `glossario` tem entre 1 e 10 entradas
- [ ] CHK026 Testes mockam API Claude — nenhum teste faz call real à API

## Etapa VALIDATE — Confiança

- [ ] CHK027 `confianca = artigos_resolvidos / max(artigos_citados, 1)`, valor entre 0.0 e 1.0
- [ ] CHK028 Proposição sem citações de lei retorna `confianca = 1.0` (não há o que validar)
- [ ] CHK029 `confianca` arredondada para 2 casas decimais

## Etapa SERVE — API e Pipeline Assíncrono

- [ ] CHK030 `GET /proposicoes/{id}/contexto` retorna HTTP 200 para qualquer `contexto_status` (nunca 404 por status pendente)
- [ ] CHK031 Response schema `ProposicaoContexto` inclui `versao_pipeline`, `modelo_llm`, `fontes` (lista de URLs), `enriquecido_em`
- [ ] CHK032 `POST /proposicoes/{id}/enriquecer?force=true` reprocessa mesmo com `ementa_hash` igual
- [ ] CHK033 `task_enriquecer_proposicao` enfileirada após ingestão de proposição com `categorias_zil != null`
- [ ] CHK034 Retry com backoff exponencial: 30s, 90s, 270s — máximo 3 tentativas para falhas de rede
- [ ] CHK035 Idempotência: segunda execução com mesmo `ementa_hash` retorna imediatamente (log "skipped")
- [ ] CHK036 `contexto_status = "processando"` durante execução da task; muda atomicamente para "pronto" ou "falhou"

## Frontend

- [ ] CHK037 Badge "Contexto verificado" (verde) para `confianca >= 0.7`
- [ ] CHK038 Badge "Contexto parcial" (amarelo) para `0 < confianca < 0.7`
- [ ] CHK039 Badge "Contexto pendente" (cinza) para `contexto_status = "pendente"` ou `null`
- [ ] CHK040 Badge "Contexto indisponível" (vermelho) para `contexto_status = "falhou"`
- [ ] CHK041 Ementa original sempre visível — nunca substituída pelo resumo
- [ ] CHK042 Accordion "Ver contexto completo" exibe glossário + artigos referenciados com links ao Planalto
- [ ] CHK043 Página `/proposicoes` não quebra (sem erros de runtime) quando `resumo_simples = null`

## Qualidade e Testes

- [ ] CHK044 Testes unitários para regex EXTRACT com >= 10 ementas reais cobrindo cada padrão
- [ ] CHK045 Testes de integração para RESOLVE mockando HTTP do Planalto (respx ou responses)
- [ ] CHK046 Testes unitários para cálculo de `confianca`
- [ ] CHK047 Teste de idempotência: `apply_enrichment` × 2 não altera banco na segunda execução
- [ ] CHK048 Teste para cada `status` de lei: resolvida, revogada, nao_encontrada, pdf_nao_parseavel
- [ ] CHK049 `pytest tests/` passa 100% após implementação (incluindo novos testes)
- [ ] CHK050 `ruff check apps/ packages/` passa sem erros

## Observabilidade

- [ ] CHK051 Log estruturado em cada etapa do pipeline: `[EXTRACT]`, `[RESOLVE]`, `[AUGMENT]`, `[VALIDATE]`, `[SERVE]`
- [ ] CHK052 `IngestionRun` registra run de enriquecimento com `tipo = "enrichment"`, contagens e erros

## Notes

- Marcar com `[x]` conforme cada item é verificado
- Itens bloqueados por dependência externa (ex: Planalto offline) devem ser documentados inline
- SC-004 (zero alucinações em 20 proposições) requer auditoria manual — não automatizável

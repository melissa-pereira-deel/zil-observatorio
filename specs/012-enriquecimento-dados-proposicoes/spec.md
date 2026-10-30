# 012 — Enriquecimento de Dados de Proposicoes

> **F-001, F-003, F-007 e F-008 foram revistos em
> [`docs/DISCOVERY-TRAMITACAO.md`](../../docs/DISCOVERY-TRAMITACAO.md)
> (2026-10-30)**: lei resultante não sai de `urnFinal` (sempre nulo), e cores
> verde/vermelho por situação conflitam com o kit, onde essas cores dizem
> alinhamento. F-002, F-004, F-005 e F-006 continuam valendo.

## Overview

O ZIL Observatorio utiliza apenas 25% dos dados disponiveis na API da Camara dos Deputados para proposicoes legislativas. Campos de alto valor como autoria, temas oficiais, regime legislativo, situacao estruturada, cadeia legislativa e resultado de votacao nao sao persistidos nem exibidos. Este feature enriquece o modelo de dados, o pipeline de ingestao e a UI para fornecer ao cidadao uma visao completa do ciclo de vida legislativo.

## Problem Statement

O cidadao que acessa uma proposicao no ZIL ve apenas dados basicos (tipo, numero, ementa, situacao como texto livre). Nao sabe quem propoe, qual o regime de urgencia, onde a proposicao esta tramitando, se o texto votado foi um substitutivo, ou se virou lei. Dados criticos para accountability estao disponiveis na API mas nao sao coletados.

## Functional Requirements

### F-001: Situacao Estruturada com Filtros
1. Persistir `codSituacao` (int), `regime` (string), `apreciacao` (string) no modelo Proposicao
2. Endpoint `GET /proposicoes` aceita novos filtros: `regime`, `situacao_grupo` (tramitando/pronta_pauta/aprovada/arquivada)
3. UI exibe badge colorido de situacao (verde=aprovada, laranja=arquivada, dourado=tramitando) e badge de regime (URGENCIA/ESPECIAL) quando aplicavel
4. Novos dropdowns de filtro na pagina /proposicoes

### F-002: Temas Oficiais da Camara
1. Chamar `GET /proposicoes/{id}/temas` durante ingestao
2. Persistir `temas_camara` como JSON array no modelo Proposicao
3. Exibir temas na pagina de detalhe como metadata complementar as categorias ZIL
4. Usar temas como sinal adicional no classificador automatico (melhoria de recall)

### F-003: Cadeia Legislativa
1. Persistir `prop_principal_id`, `prop_anterior_id`, `prop_posterior_id` (extraidos de uriPropPrincipal/Anterior/Posterior)
2. Criar tabela `proposicao_relacoes` para relacionadas (emendas, pareceres, substitutivos)
3. Endpoint `GET /proposicoes/{id}/relacionadas` retorna proposicoes agrupadas por tipo
4. UI exibe timeline visual da cadeia (Camara → Senado → Lei) e secao de relacionadas colapsavel

### F-004: Resultado Autoritativo de Votacao
1. Persistir campo `aprovacao` (int 1/0/null) no modelo Votacao
2. Usar como fonte primaria para badge de resultado, eliminando inferencia por contagem de votos
3. Campo `proposicao_objeto` tambem persistido para identificar o que foi efetivamente votado

### F-005: Keywords da Camara
1. Persistir `keywords_camara` (Text) — campo `keywords` do detalhe da API (ja lido no discover mas nao persistido)
2. Exibir como tags na pagina de detalhe
3. Usar como input adicional no classificador automatico

### F-006: Autoria Completa com Vinculacao
1. Chamar `GET /proposicoes/{id}/autores` durante ingestao
2. Criar tabela `proposicao_autores` com vinculacao FK ao modelo Parlamentar
3. Popular `autor_principal_id` na tabela Proposicao (hoje NULL para todas as 406)
4. Exibir autores na pagina de detalhe com links para perfil do parlamentar
5. Novo endpoint `GET /parlamentares/{id}/proposicoes` para proposicoes de autoria

### F-007: Orgao Atual e Relator
1. Persistir `orgao_situacao` (siglaOrgao do statusProposicao) e `relator_id` (vinculado a parlamentares)
2. Exibir badge de orgao atual e nome do relator na pagina de detalhe

### F-008: Lei Resultante
1. Persistir `urn_final` quando proposicao vira lei
2. Construir link direto para texto da lei no Planalto
3. Badge verde "VIROU LEI" com link externo na pagina de detalhe

## Data Flow

```
API Camara (backfill 406 proposicoes)
  ├── GET /proposicoes/{id} → campos Fase 1 (12 novos campos)
  ├─��� GET /proposicoes/{id}/autores → tabela proposicao_autores
  ├── GET /proposicoes/{id}/temas → temas_camara JSON
  └── GET /proposicoes/{id}/relacionadas → tabela proposicao_relacoes
      ↓
  Pipeline sync_pipeline.py (novo Step 1.5: Detail Sync)
      ↓
  API REST (endpoints novos e modificados)
      ↓
  Frontend (componentes novos + paginas redesenhadas)
```

## Actors

- **Cidadao**: usuario sem conhecimento juridico que quer entender proposicoes legislativas
- **Jornalista**: busca proposicoes com regime de urgencia para cobertura
- **Pesquisador**: filtra e analisa tendencias legislativas
- **Ativista**: acompanha emendas e proposicoes relacionadas a temas especificos

## Out of Scope

- Dados do Senado Federal (backlog separado)
- Ingesta automatica continua (apenas backfill + re-sync semanal)
- Busca full-text em Typesense (backlog futuro)
- Autenticacao ou features participativas
- Notificacoes de mudanca de status

## Technical Context

- JOIN Votacao-Proposicao ja existe nos endpoints
- Modelo Proposicao tem campos `autores`, `tramitacoes`, `metadata_extra` (JSON) — todos NULL
- CamaraClient tem retry + 300ms rate limit ja implementado
- 406 proposicoes no banco, todas com enrichment pronto
- ADR-001: JSON (nao JSONB) para compatibilidade SQLite
- ADR-003: JSON(none_as_null=True) para queries IS NOT NULL
- 151 testes existentes passando

## Success Criteria

- 100% das proposicoes com cod_situacao, regime, keywords preenchidos
- >95% das proposicoes com autor_principal_id vinculado
- >90% das proposicoes com pelo menos 1 tema oficial
- >40% das proposicoes com pelo menos 1 link de cadeia legislativa
- Zero badges "Aprovado*" (inferidos) — usar campo aprovacao autoritativo
- Todos os testes existentes continuam passando + ~30 novos testes
- UI exibe autores com links, cadeia legislativa, filtros de situacao/regime

## Clarifications

### Session 2026-04-05
- Q: Temas ficam como JSON ou tabela normalizada? → A: JSON no campo temas_camara (baixa cardinalidade, 32 codigos fixos, read-only)
- Q: Autores ficam como JSON ou tabela normalizada? → A: Tabela normalizada proposicao_autores (alta cardinalidade, precisa de FK para parlamentares)
- Q: Relacionadas ficam como JSON ou tabela normalizada? → A: Tabela normalizada proposicao_relacoes (alta cardinalidade, FK bidirecional entre proposicoes)

## Edge Cases

- Proposicao sem autores na API (tipo "Orgao do Poder Executivo"): `autor_principal_id` fica NULL, tipo = "Orgao"
- Proposicao sem temas na API: `temas_camara` fica NULL, secao nao exibida
- Centenas de relacionadas (emendas de PEC): colapsar por tipo, limitar exibicao a 20 por grupo
- urnFinal com formato nao parseavel: exibir URN como texto sem link
- Autor nao encontrado nos parlamentares do ZIL: `parlamentar_id` NULL, exibir nome sem link
- Rate limiting da API durante backfill: retry com backoff exponencial (ja implementado)
- Votacao com aprovacao=null: fallback para resultado textual, depois inferencia por contagem

## Implementation Phases

### Fase 1 — Colunas + campos do detalhe (Sprint 1, ~2 dias)
- F-001: Situacao estruturada (cod_situacao, regime, apreciacao)
- F-004: Resultado autoritativo (aprovacao em Votacao)
- F-005: Keywords (keywords_camara)
- Script de migracao + backfill
- Schemas + endpoints + UI filtros

### Fase 2 — Autores + temas (Sprint 2, ~3 dias)
- F-002: Temas oficiais
- F-006: Autoria completa (tabela ProposicaoAutor)
- Novos metodos CamaraClient
- Componentes AutoresLine, AutorCard
- Endpoint /parlamentares/{id}/proposicoes

### Fase 3 — Cadeia + relacionadas (Sprint 3, ~3 dias)
- F-003: Cadeia legislativa (tabela ProposicaoRelacao)
- F-007: Orgao atual e relator
- F-008: Lei resultante (urnFinal)
- Componentes CadeiaNode, TramitacaoEvent
- Redesign completo da pagina de detalhe

# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions map to git tags (not yet created — pending deploy pipeline).

---

## [Unreleased]

### Added
- **Ferramentas de apoio à curadoria editorial** — atacam o gargalo real do
  projeto, que é tempo de pesquisa por classificação:
  - `scripts/dossie.py`: dado o ID de uma votação, reúne ementa, ementa
    detalhada, palavras-chave, situação, placar contado dos votos individuais,
    orientações de bancada e as leis citadas com link para o Planalto — e emite
    o YAML pronto para colar, **sem o campo `direcao`**, que é a decisão humana.
    Funciona sem banco e sem `ANTHROPIC_API_KEY`. O bloco de análise assistida
    vem **por último e rotulado**, para não ancorar o julgamento antes da
    leitura das fontes primárias (risco registrado em `PRD-PAINEL.md` §12).
  - `scripts/candidatas.py`: varre um ano na API da Câmara e ranqueia votações
    por saliência — precisão do casamento temático, classificabilidade da
    direção, margem disputada e pistas de plenário. Destaca votações
    **rejeitadas** e diz **por qual keyword** cada candidata entrou na lista.
  - `scripts/validar_direcoes.py`: valida os YAMLs de direções, que hoje não têm
    validação alguma. Pega `direcao: Sim` com maiúscula, `peso` fora da tabela,
    `fonte_id` duplicado e justificativa ausente ou curta demais — e reporta a
    distribuição de direções, expondo a variância zero do corpus atual.
  - `tests/unit/test_ferramentas_curadoria.py`: 25 testes das funções puras.
- `apps/workers/classifiers/__init__.py`: `classificar_texto_com_evidencia()` —
  mesma classificação de `classificar_texto()`, mas devolve **quais keywords
  casaram** em cada categoria. Sem a procedência não dá para distinguir uma
  votação sobre `minerais críticos` de uma que casou com `técnico`.

### Changed
- `scripts/candidatas.py`: **o tema passa a dominar a disputa no ranqueamento.**
  A nota anterior media só o formato da votação — margem, plenário, se era
  requerimento — e o tema entrava como meio ponto por categoria. O resultado
  medido na varredura de 2024 e 2025: a Política Nacional de Minerais Críticos
  e Estratégicos, a tese do projeto em forma de lei, ficou em **último lugar**
  entre 12 por ter sido quase unânime, enquanto a Tarifa Social de Água e
  Esgoto liderava por ter casado com a palavra `tarifa`. Com placar focado
  (ADR-004), o topo da lista precisa ser o que mais importa.
- `scripts/candidatas.py`: requerimento de **urgência** deixa de ser penalizado
  como manobra processual. Diferente de `"Rejeitado o Requerimento"`, a urgência
  nomeia o objeto: quem votou sim quis pautar aquele projeto. Entra com o peso
  mínimo (0,5), porque mede intenção de pautar, não posição sobre o mérito.
- `scripts/dossie.py`: `_peso_sugerido()` distingue urgência de requerimento
  genérico, e a justificativa impressa registra a diferença.

### Fixed
- `scripts/candidatas.py`: keyword que casa **dentro do nome de uma lei citada**
  não conta mais como tema. O PL 996/2015 — homicídio qualificado contra membros
  do MP e da Magistratura — liderava a lista de 2024 por casar `dados pessoais`
  e `proteção de dados` dentro de "(Lei Geral de Proteção de Dados Pessoais)",
  uma das leis que ele altera. Citar uma lei não é ser sobre o tema dela.
- `scripts/candidatas.py`: keywords que casam com o português comum
  (`técnico`, `engenharia`, `tarifa`, `pesquisa`, `bolsa`, `importação`…) não
  sustentam sozinhas a inclusão de uma votação, e a candidata recebe aviso
  visível. Cada uma da lista produziu um falso positivo real nas varreduras:
  `técnico` casou com "Técnico Judiciário", `engenharia` com obras do Exército,
  `tarifa` com "Tarifa Social de Água e Esgoto".
- `scripts/candidatas.py`: o aviso sobre votações rejeitadas afirmava que eram
  "a via mais natural" para quebrar a variância zero do corpus. **Não são.** Das
  14 rejeitadas de 2024 e 2025, 10 são `"Rejeitado o Requerimento"` sem dizer
  qual, e a API não desambigua — `objetosPossiveis` devolve dezenas de
  candidatos (81 numa votação da PONTE). Sem saber o que foi rejeitado, a
  direção é chute. O texto agora diz isso.


#### Pipeline de dados — discovery, sync e orquestração
- `scripts/discover_proposicoes.py`: descoberta de proposições via API da Câmara —
  busca por keywords das 9 categorias ZIL, classifica localmente, persiste com dados
  completos; suporta `--dry-run`, `--enriquecer`, e janela temporal customizada
- `scripts/sync_votacoes_proposicoes.py`: sync de votações por proposição — itera
  proposições no banco, busca votações na API da Câmara, sincroniza votações + votos
  individuais; suporta `--dry-run`, `--proposicao-id`, `--skip-with-votes`/`--no-skip`
- `scripts/sync_pipeline.py`: orquestrador sequencial dos 4 passos do pipeline —
  discovery → votação sync → enrichment → score recalculation; suporta `--skip-*`
  flags individuais e `--dry-run` global
- `packages/camara_client/__init__.py`: novo método `pesquisar_proposicoes()` com
  busca por keywords, iteração trimestral (restrição da API), e deduplicação por ID
- `packages/camara_client/__init__.py`: novo método `listar_votacoes_proposicao()`
  para buscar votações de uma proposição específica via API da Câmara
- `apps/workers/tasks.py`: `task_enriquecer_pendentes` agora processa proposições
  com `contexto_status = "pendente"` (além de `NULL`)

#### UI/UX — credibilidade, acessibilidade e componentes compartilhados (UI-001 a UI-022)
- `components/ParlamentarAvatar.tsx`: componente reutilizável com fallback de iniciais
  quando foto está ausente ou falha ao carregar — suporta tamanhos sm/md/lg
- `components/DirecaoBadge.tsx`: badge de direção esperada (FAVORÁVEL/CONTRÁRIA) com
  link para /metodologia — usado em proposições e votações
- `components/ui/Badge.tsx`: sistema unificado de badges com variantes `category`,
  `status`, `result` — substitui badges ad hoc espalhados pelas páginas
- `lib/categorias.ts`: mapa centralizado de categorias ZIL com labels legíveis —
  elimina duplicação de strings de categoria em múltiplos componentes
- `ScoreGauge.tsx`: tooltip com âncora de credibilidade ("baseado em N votos ·
  ver metodologia →"), design tokens `zil-*` consolidados (UI-001, UI-016, UI-019)
- `ContextoBadge.tsx`: badge "Contexto pendente" removido da UI pública — aparece
  apenas quando `contexto_status === "pronto"` (UI-002)
- `ranking/page.tsx`: contagem de resultados acima da lista, empty state explicativo,
  busca textual na mesma linha dos filtros, remoção de decoração tipográfica (UI-003/004/005/006)
- `proposicoes/page.tsx`: contagem de resultados, empty state, unificação de filtros,
  remoção de letra decorativa (UI-003/004/005/006)
- `proposicoes/[id]/page.tsx`: síntese de posição ZIL ("ZIL avalia: FAVORÁVEL · com
  base em N votações"), `resultado` inferido de votos quando null, collapse nativo
  com `<details>/<summary>` (UI-010/011/012)
- `votacoes/[id]/page.tsx`: redesign com linguagem mais acessível, placar visual,
  filtro por tipo de voto, links para perfil do parlamentar
- `parlamentar/[id]/page.tsx`: hero metric zone com gauge + proporção em 2 colunas,
  legenda do duplo encoding (dot = alinhamento, badge = voto) com mini badge visual,
  affordance nos cards de categoria, frase de síntese interpretativa, remoção de
  score duplicado e código interno das categorias (UI-013 a UI-022)

#### Segurança — hardening de secrets
- `.pre-commit-config.yaml`: hooks `detect-secrets` (Yelp v1.5.0) e
  `detect-private-key` para bloquear commits com API keys ou chaves privadas
- `core/config.py`: validação de startup em produção — app recusa iniciar se
  variáveis obrigatórias estiverem ausentes ou se DATABASE_URL for SQLite
- `.gitignore`: catch-all para variantes `.env.*` (exceto `.env.example`) +
  padrões para chaves privadas, certificados e credenciais
- `.env.example`: contém apenas placeholders vazios com comentários instrutivos —
  nunca valores reais
- `docker-compose.yml`: credenciais substituídas por `${VAR:-default}` para
  carregamento seguro via `.env`
- `CLAUDE.md`: seção "Segurança e segredos" com 7 regras para manuseio de secrets

#### Testes
- `tests/unit/test_camara_client.py`: 6 testes para `listar_votacoes_proposicao`
  (retorno, lista vazia, resposta non-list, endpoint correto, mapeamento, campos opcionais)
- `tests/unit/test_sync_votacoes.py`: 6 testes para `sync_votacoes_por_proposicao`
  (criação, dedup, skip, dry-run, classificação, linking)
- `tests/integration/test_pipeline_scoring.py`: 3 testes end-to-end validando
  apply_direcoes + recalcular_todos_scores (score positivo, negativo, sem direção)
- Total: **151 testes passando**

#### Documentação
- `specs/002-legislative-enrichment-pipeline/`: spec completo com tasks.md (12 tasks),
  plan.md, contracts/api.md, data-model.md, quickstart.md, research.md
- `specs/ui-ux-credibility-polish/spec.md`: spec das 22 tasks UI/UX

### Changed
- **Redefinição de produto: placar focado no lugar de índice abrangente**
  ([ADR-004](decisions/004-placar-focado.md)). A v1 deixa de perseguir Score ZIL
  para os 594 parlamentares e passa a ser um placar de ~10 votações bem
  pesquisadas. O Score ZIL permanece (−10 a +10) e o motor não muda; muda o
  universo sobre o qual ele opera. Revogadas as metas de cobertura em `PRD.md` e
  `ROADMAP.md`; `constitution.md` registra o fato sem alterar a norma (1.0.1 →
  1.0.2, PATCH).
- **Afirmações falsas removidas da plataforma e dos documentos.** A home
  convidava a *"crie uma conta gratuita"* para votar em deliberações e cobrar
  parlamentares — não existe autenticação no projeto, era CTA para fluxo
  impossível. O `metadata.description` (que vai para buscadores) prometia
  monitorar "cada parlamentar brasileiro". O `ScoreExplainer` dizia "não é
  opinião — é matemática", quando a aritmética opera sobre 7 classificações
  não validadas e a escolha das votações é juízo editorial. Os nove "exemplos"
  de proposições na página de metodologia são hipotéticos e agora estão
  rotulados como tal. `NavBar` apontava para `/sobre`, rota inexistente.
- **`CONTRIBUTING.md` e `GOVERNANCE.md` (v1.1 → v1.2): canais e reuniões.**
  Removida a promessa de "reunião aberta semanal, gravada e publicada", que
  nunca existiu; registrado que **não há agenda de reuniões** e que formato e
  periodicidade serão definidos em conjunto quando houver quórum de
  contribuidores — assim como as próprias diretrizes do projeto. O Discord passa
  a ser descrito como **canal previsto**, com o convite a ser publicado quando
  existir; o canal ativo hoje são as issues do GitHub. Também corrigidos: "voto
  em decisões comunitárias" (sem mecanismo), "revisada pelo comitê editorial"
  (nunca constituído), "lista de proposições pendentes na plataforma" (não há
  fluxo na UI) e GitHub Discussions (desabilitado).
- **Renomeação do repositório** `manifesto-zil` → `zil-observatorio` propagada
  para badge de CI, comando de clone, link público no frontend, CHANGELOG,
  ARCHITECTURE, DEPLOY e `launch.json`.
- **Senado: capacidade ≠ dado.** O README marcava "Crawler Senado Federal ✅"
  enquanto a página de metodologia dizia que o Senado não está na v1. Não era
  contradição: o crawler existe, mas nenhum dado do Senado foi ingerido e as 7
  direções são todas da Câmara. O README passa a dizer as duas coisas.
- `README.md` e `CLAUDE.md`: sincronizados com o estado real do código, que ambos
  subestimavam. Correções: ingestão do Senado, `/bussula`, `/metodologia` e CI/CD
  estavam marcados como backlog mas já existem; contagem de testes de 98 para 151;
  link quebrado para `docs/MANIFESTO.md` removido (o manifesto é a home da
  plataforma); comando `uvicorn apps.api.main:app` do Quick Start corrigido para
  `cd apps/api && uvicorn main:app`, já que a forma documentada falhava com
  `ModuleNotFoundError` por causa dos imports curtos (ADR-002); as 22 tarefas de
  design critique marcadas como concluídas. Adicionadas seções sobre o volume real
  de curadoria editorial (7 votações com direção definida — o gargalo atual da v1)
  e sobre as pendências conhecidas de infraestrutura (`make migrate`, `make seed`,
  `make test`, `admin_token` em query string, código dormente).
- `scripts/apply_direcoes.py`: agora chama `recalcular_todos_scores(db)` automaticamente
  após aplicar direções — elimina necessidade de recalcular scores manualmente
- `apps/api/routers/legislativo.py`: endpoints de proposições e votações retornam campos
  de enriquecimento (resumo_simples, categorias) em linguagem mais acessível
- `apps/api/routers/parlamentares.py`: campo de contagem de votos adicionado à resposta
- `apps/api/schemas/__init__.py`: novos schemas para campos de enriquecimento

### Fixed
- **Texto de lei voltava ilegível do Planalto**: o servidor devolve
  `Content-Type: text/html` **sem charset**, então o httpx assumia utf-8 num
  conteúdo windows-1252 — "dispõe" virava "disp?e". Pior que não voltar: parecia
  dado bom. `_fetch_planalto` passa a fixar o encoding quando o servidor não
  declara. Junto: `_strip_tags` agora resolve entidades HTML (`&nbsp;`, `&amp;`),
  que antes sobreviviam até o banco e até o prompt do LLM.
- **`anthropic` não estava nas dependências**: o pacote era importado com
  `try/except` em `apps/workers/enrichment` e nunca declarado em
  `requirements.txt`. O passo de LLM do pipeline de enriquecimento não podia
  rodar em ambiente nenhum, mesmo com a chave configurada.

- **Busca de leis no Planalto nunca funcionou**: `_fetch_planalto` enviava
  `User-Agent: ZIL-Observatorio/1.0`, e o Planalto derruba a conexão para
  agentes que não pareçam navegador. Toda resolução de lei falhava em silêncio e
  virava `nao_encontrada` — ou seja, o pipeline de enriquecimento vinha rodando
  sem o texto legal que é a razão de ele existir. Trocado para
  `Mozilla/5.0 (compatible; ZIL-Observatorio/1.0; +https://zilobservatorio.org)`,
  a convenção de crawler bem-comportado: passa no filtro e continua
  identificando quem chama, com endereço de contato.

- **Taxonomia editorial ignorada em qualquer container (silenciosamente)**:
  `routers/bussula.py` e `workers/classifiers` resolvem o caminho dos YAMLs
  relativo ao próprio arquivo, o que dentro do container aponta para `/data/...`
  — inexistente, já que só `apps/api` era montado. O classificador caía na
  taxonomia embutida de fallback (57 das 131 keywords curadas, 44% de cobertura)
  e `/bussula` respondia `[]`. Nenhum dos dois gerava erro, então o problema
  passaria despercebido até produção. Adicionado mount `./data:/data:ro` em
  `api`, `worker` e `beat`.
- **`make migrate` não existia de fato**: `alembic.ini` apontava para
  `data/migrations`, diretório nunca commitado. Criado o ambiente de migrations
  (`env.py` lendo `DATABASE_URL` do ambiente em vez de credencial versionada) e
  a migration inicial com as 8 tabelas, validada contra Postgres limpo —
  `alembic check` reporta zero drift em relação aos modelos. Novo alvo
  `make migrate-stamp` para bancos criados pelo `create_all` sem carimbo.
- **`make setup` falhava mesmo com migrations**: subia a API antes de migrar, e
  o `create_all` do lifespan criava as tabelas sem carimbo do Alembic. Reordenado
  para migrar com apenas `db` e `redis` no ar, e só então subir o restante.
- **`make seed` chamava script inexistente**: criado `scripts/seed.py`, que
  sincroniza da API da Câmara as votações já curadas em `data/direcoes/`, aplica
  as direções e recalcula scores. Dado real e rastreável, nunca fictício.
- **`make test` coletava 0 testes**: o container `api` monta só `apps/api` e
  `tests/` fica na raiz. Alvos passam a rodar no host (como a CI), com `PYTHON`
  autodetectando `.venv`. `test-web` deixou de chamar `npm test`, que não existe
  em `apps/web`, e passa a rodar lint + type check.
- **Token de admin trafegava em query string**: `POST /proposicoes/{id}/enriquecer`
  recebia `admin_token` na URL, que vaza em log de servidor, histórico de browser
  e header `Referer`. Migrado para `Authorization: Bearer`, com comparação em
  tempo constante (`secrets.compare_digest`) e 6 testes cobrindo ausência de
  header, token errado, esquema errado, query string e servidor sem token.
- **Variável do compose derrubava a aplicação**: `Settings` recusava qualquer
  chave do `.env` não declarada, então `POSTGRES_USER` ou `POSTGRES_PORT` — que
  são do docker compose — causavam `ValidationError` no import. Passa a usar
  `extra="ignore"`.
- **Postgres local sombreava o container**: a porta do host virou
  `POSTGRES_PORT` (default 5432 inalterado), porque um Postgres local na 5432
  faz o host falar com o banco errado sem nenhum aviso.
- **CI vermelha desde 2026-04-04 — lint do backend**: `.github/workflows/ci.yml` instalava
  `ruff` sem pin, então cada run pegava a versão mais recente e o conjunto de regras mudava
  sozinho (267 erros na CI contra 5 no `ruff==0.8.6` pinado em `requirements.txt`). Passa a
  instalar de `apps/api/requirements.txt`, alinhado ao job de testes e ao
  `cache-dependency-path` que o próprio job já declarava. Os 5 erros reais foram corrigidos:
  `routers/legislativo.py` tinha `import os` morto; os imports pós-`sys.path` em
  `crawlers/camara.py` e `crawlers/senado.py` receberam `# noqa: E402`, seguindo a convenção
  já usada em `tests/conftest.py`.
- **CI vermelha desde 2026-04-04 — lint do frontend**: `apps/web` não tinha config de ESLint,
  apesar de `eslint` e `eslint-config-next` estarem nas devDependencies. Sem config, `next lint`
  abria o assistente interativo de setup e saía com código 1 na CI (sem TTY), o que também
  deixava o job `Frontend — Build` permanentemente pulado por `needs:`. Adicionado
  `apps/web/.eslintrc.json` com `next/core-web-vitals` — equivalente à opção "Strict
  (recommended)" que o assistente sugeria.
- **Pre-commit bloqueava todo commit**: `.pre-commit-config.yaml` passa
  `--baseline .secrets.baseline` ao hook `detect-secrets`, mas o arquivo nunca foi
  commitado — o hook abortava com `Invalid path: .secrets.baseline` em qualquer commit,
  para quem tivesse rodado `pre-commit install`. Baseline gerado e adicionado; as 5
  detecções são placeholders de desenvolvimento já documentados (`zil:zil` do Postgres
  local, `zil-dev-key` do Typesense) — nenhum segredo real.
- **Celery worker e beat não iniciavam no Docker**: `docker-compose.yml` montava
  `apps/workers` em `/workers`, fora do `WORKDIR` (`/app`) — `celery -A workers.tasks`
  abortava com `ModuleNotFoundError: No module named 'workers'`, porque o diretório pai
  do pacote não estava no `sys.path`. O bootstrap de `sys.path` em `apps/workers/tasks.py`
  não cobre o caso: ele só executa depois que o módulo já foi localizado. Mount corrigido
  para `/app/workers` em ambos os serviços — worker sobe com as 7 tasks registradas e
  beat inicia o scheduler.
- **Enrichment não executava**: `apps/workers/enrichment/__init__.py` usava `os.getenv()`
  para ler configurações — falha silenciosa quando variável de ambiente vazia sobrescreve
  o `.env` (Pydantic BaseSettings dá precedência a env vars). Corrigido para usar
  `core.config.settings` consistentemente com o resto do codebase. 406 proposições
  enriquecidas com sucesso após a correção.
- **CORS em dev**: `main.py` agora usa `allow_origin_regex` para aceitar qualquer porta
  localhost, corrigindo chamadas de API de preview servers em portas dinâmicas
- **Caminho SQLite**: DATABASE_URL usa caminho absoluto — mesmo banco independente
  do diretório de execução
- **Resolução de .env**: `core/config.py` resolve `.env` relativo ao arquivo de config,
  não ao cwd do processo
- **Proxy Next.js → FastAPI**: `next.config.js` com rewrite para que preview no browser
  alcance a API backend

---

## [0.4.0] — 2026-04-02

Features 002–009 from the v1 backlog, all implemented in a single release.

### Added

#### 002 — Senado Federal ingestion
- `packages/senado_client/__init__.py`: `SenadoClient` with `listar_senadores()`,
  `listar_materias_ano()`, `listar_votacoes_materia()`, `obter_votos_votacao()`
- `apps/workers/crawlers/senado.py`: `sync_senadores()`, `sync_materias()`,
  `sync_votacoes_materia()`, `run_full_sync()` with `IngestionRun` audit trail
- Two new Celery tasks in `apps/workers/tasks.py`:
  - `task_sync_senadores` — weekly Monday 03:30
  - `task_sync_votacoes_senado` — every 6 hours at :30

#### 003 — Editorial workflow script
- `scripts/apply_direcoes.py`: loads `data/direcoes/*.yml`, matches by `fonte_id +
  fonte`, updates `Votacao.direcao_esperada` and `Votacao.peso`; supports `--ano`
  and `--dry-run` CLI flags

#### 004 — Frontend: /ranking
- Partido filter fetched live from `/parlamentares/partidos/ranking`
- Server-side filters: fonte, uf, partido, ordem (per_page=600)
- Client-side name search
- Skeleton loading (12 animated rows while fetching)
- Split display: scored parlamentares with rank numbers / unscored section (opacity-50)

#### 005 — Frontend: /parlamentar/[id]
- Per-category alignment breakdown with progress bars
- Clickable category cards to filter vote history
- "← Voltar ao ranking" navigation link
- Vote history table with alinhamento indicator per vote

#### 006 — Frontend: /proposicoes + detail pages
- Tipo filter (PL, PEC, PLP, MPV, PDL, PRC) and ano filter (last 10 years)
- Clickable rows link to `/proposicoes/[id]`
- `apps/web/app/proposicoes/[id]/page.tsx`: ementa, categories, situacao,
  url_inteiro_teor, votação list with placar and link to voting detail
- `apps/web/app/votacoes/[id]/page.tsx`: full voting record with per-parlamentar
  votes, filterable by vote type, each row links to `/parlamentar/[id]`

#### 007 — Frontend: /bussula
- Fetches `/bussula`, groups indicators by category
- `MarcoCard`: valor_atual, progress bar toward meta, tendência symbol, fonte link
- Empty state explains how to add indicators via YAML PR

#### 008 — Frontend: /metodologia
- Static page: score formula, weights table (3.0/2.0/1.0/0.5), gradient scale visual
- 9 category descriptions with examples, 5 limitations, editorial process

#### 009 — CI/CD
- `.github/workflows/ci.yml` rewritten with 4 jobs:
  - `test-backend`: pytest with pip cache
  - `lint-backend`: ruff only
  - `lint-frontend`: npm ci + ESLint + tsc --noEmit
  - `build-frontend`: next build (depends on lint-frontend)
- CI badge added to README

### Changed
- `apps/api/routers/parlamentares.py`: `per_page` limit raised from 100 to 600
- `apps/api/routers/legislativo.py`: added `GET /proposicoes/{id}/votacoes` and
  `GET /votacoes/{id}` endpoints
- `apps/api/routers/bussula.py`: new router reading `data/bussula/marcos.yml`
- `apps/api/requirements.txt`: added `pyyaml==6.0.2` (was missing, used by classifier)
- `apps/api/main.py`: registered `bussula` router

### Fixed
- Removed unused imports (`case`, `Field`, `func`, `FonteEnum`) that would fail ruff CI

---

## [0.3.0] — 2026-04-02

Feature 001 merged from branch `001-camara-api-ingestao`.

### Added
- `CLAUDE.md`: development guidelines, ADRs summary, coding conventions
- Enhanced `apps/api/models/__init__.py`: `IngestionRun`, `ScoreVotacao`, `Proposicao`
  models; `VotoEnum` with ausente/abstencao/obstrucao/artigo_17
- `apps/workers/crawlers/camara.py`: full sync with idempotent upsert,
  `IngestionRun` audit logging
- `apps/workers/scoring/__init__.py`: `recalcular_score_parlamentar()` with
  `ScoreVotacao` persistence; `recalcular_todos_scores()`
- `apps/workers/classifiers/__init__.py`: keyword classifier against
  `data/taxonomia/categorias.yml`; `relevancia_score()`
- `packages/camara_client/__init__.py`: retry logic, pagination, full deputy/
  voting/vote sync
- 98 tests across `tests/unit/`, `tests/integration/`, `tests/contract/`
- `tests/conftest.py`: SQLite in-memory fixtures (ADR-001)
- `specs/001-camara-api-ingestao/`: full Specify Kit spec set

---

## [0.2.0] — 2026-04-01

Homepage redesign and design system foundation.

### Added
- `apps/web/components/ui/`: Button, Badge, Card, Callout, SectionHeader
- `apps/web/components/NavBar.tsx`: responsive nav with hamburger menu on mobile
- `apps/web/components/ScoreExplainer.tsx`: visual score scale, weights, formula
- `apps/web/components/RankingPreview.tsx`: top/bottom 5 from API with skeleton + error
- `apps/web/components/CategoryGrid.tsx`: 9 ZIL category cards with filter links
- `apps/web/components/ManifestoSignature.tsx`: sign form + share button
- `apps/web/app/page.tsx`: new landing page composing all sections
- `apps/web/app/manifesto/page.tsx`: redirect to `/`
- `apps/web/tailwind.config.js`: `zil-*` design tokens (green, gold, cream, dark, orange)
- `apps/web/app/globals.css`: base typography and utility classes

### Removed
- `apps/web/app/page.jsx`: replaced by `page.tsx`; removed internal SPA router,
  mock data, inline styles, and duplicated nav/footer

---

## [0.1.0] — 2026-03-31

Initial scaffold.

### Added
- `apps/api/`: FastAPI app, SQLAlchemy models (Parlamentar, Votacao, Voto, Proposicao),
  Pydantic schemas, routers for parlamentares, legislativo
- `apps/workers/`: Celery app, task definitions with beat schedule, Câmara crawler stub,
  scoring engine stub, keyword classifier with `data/taxonomia/categorias.yml`
- `apps/web/`: Next.js 14 scaffold with TypeScript, Tailwind CSS, postcss
- `packages/camara_client/__init__.py`: Câmara API client stub
- `data/taxonomia/categorias.yml`: 9 ZIL categories with Portuguese/English keywords
- `docker-compose.yml`: api + worker + beat + redis + postgres services
- `docs/ARCHITECTURE.md`, `docs/PRD.md`, `docs/GOVERNANCE.md`: founding documents
- `pytest.ini`, `tests/test_classifier.py`, `tests/test_scoring.py`: initial test suite

---

[Unreleased]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/melissa-pereira-deel/zil-observatorio/releases/tag/v0.1.0

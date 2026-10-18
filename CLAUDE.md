# ZIL Observatório — Development Guidelines

**Última atualização:** 2026-10-18
**Fase atual:** v1 — Placar focado ([ADR-004](docs/decisions/004-placar-focado.md)), sem login
**Roadmap:** [docs/ROADMAP.md](docs/ROADMAP.md)

> **Estado em uma linha:** o software da v1 está essencialmente completo. O que
> falta é curadoria editorial — e o alvo mudou: o ADR-004 trocou o índice dos 594
> parlamentares por um **placar focado em ~10 votações** bem pesquisadas. Hoje
> são 7 classificações, todas `nao-validado`, das quais 4 alimentam o score. O
> deploy está **preparado** (`render.yaml` + runbook) e não executado.

---

## Stack ativo

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2 |
| Workers | Celery 5, Redis 7, httpx 0.27 |
| Frontend | Next.js 14, TypeScript 5, Tailwind CSS, React 18 |
| Enriquecimento | Claude Haiku 4.5 via `ANTHROPIC_API_KEY` (opcional em dev) |
| Testes | pytest 8 (297 testes, todos passando) |
| Linting | ruff 0.8.6 (Python), ESLint + `next/core-web-vitals` (TypeScript) |
| CI | GitHub Actions — 4 jobs, todos verdes |

---

## Estrutura do projeto

```
apps/api/          FastAPI + SQLAlchemy models (8 tabelas) + schemas
                   + routers (15 endpoints) + / e /health em main.py
apps/workers/      Celery tasks + crawlers (camara.py ✅, senado.py ✅)
                   + scoring engine + keyword classifier + enrichment (Planalto + LLM)
apps/web/          Next.js 14 (App Router) — 10 páginas + 11 componentes + 5 de UI base
packages/          camara_client ✅ | senado_client ✅
data/taxonomia/    categorias.yml — keywords das 9 categorias ZIL ✅
data/direcoes/     direcao_esperada por votação — 2024.yml + 2025.yml, 7 entradas (em formação)
data/bussula/      marcos.yml — 4 indicadores (em formação)
data/painel/       painel de curadoria (Fase 1) — agentes/*.yml (5 definições)
                   + casos/construidos.yml (10) + casos/injection.yml (8)
scripts/           curadoria: candidatas.py | dossie.py | validar_direcoes.py | apply_direcoes.py
                   painel: painel.py (calibração da Fase 1)
                   sync: sync_votacoes_zil.py | sync_votacoes_proposicoes.py
                         discover_proposicoes.py | sync_pipeline.py
                   infra: migrate_enrichment.py | seed.py | start-dev.sh
                   backlog: recalcular_scores.py (não existe — ver o one-liner em "Comandos")
tests/             unit/ (219) integration/ (52) contract/ (7) + 19 na raiz = 297
specs/             001-camara-api-ingestao | 002-legislative-enrichment-pipeline
                   011-resumo-simples-votos-historico | 012-enriquecimento-dados-proposicoes
                   ui-ux-credibility-polish
docs/              PRD, PRD-PAINEL, ARCHITECTURE, GOVERNANCE, ROADMAP, DEPLOY,
                   CHANGELOG, DISCOVERY-DADOS-PROPOSICOES
                   decisions/  ADR-001 cross-db types | ADR-002 import path
                               ADR-003 json null | ADR-004 placar focado
```

> **Atenção à numeração:** `specs/` e `docs/ROADMAP.md` usam numerações
> divergentes. No ROADMAP, `002` é "Ingestão do Senado"; em `specs/`, `002` é o
> pipeline de enriquecimento. Ao referenciar uma feature por número, diga de qual
> dos dois você está falando.

---

## Comandos

```bash
# Backend (rodar da raiz)
python -m pytest tests/          # 297 testes
ruff check apps/ packages/       # lint Python

# API local — rodar de dentro de apps/api, não da raiz.
# `uvicorn apps.api.main:app` falha com ModuleNotFoundError por causa dos
# imports curtos (ADR-002).
cd apps/api && uvicorn main:app --reload

# Frontend
cd apps/web
npm run dev                      # dev server
npm run build                    # build produção
npm run lint                     # ESLint (config em .eslintrc.json)
npx tsc --noEmit                 # type check

# Workers (requer Redis)
# Da raiz o módulo é apps.workers.tasks; dentro do container é workers.tasks,
# porque o compose monta apps/workers em /app/workers e o WORKDIR é /app.
celery -A apps.workers.tasks worker --loglevel=info
celery -A apps.workers.tasks beat --loglevel=info

# Docker (ambiente completo)
docker compose up -d             # ou: make up
# make setup NÃO funciona em clone limpo — ver "Pendências de infraestrutura"

# Painel de curadoria — Fase 1 (calibração). Precisa de ANTHROPIC_API_KEY,
# exceto --dry-run. Não escreve em data/direcoes/ e não recalcula score.
python3 scripts/painel.py --calibrar --dry-run   # monta os prompts, conta as chamadas
python3 scripts/painel.py --calibrar             # métricas 1, 3 e 5 do go/no-go
python3 scripts/painel.py --injection            # métrica 2 — qualquer falha é no-go
python3 scripts/painel.py --calibrar --out data/painel/calibracao/   # grava transcrições

# Pipeline de dados editorial (rodar na ordem, da raiz)
python3 scripts/migrate_enrichment.py       # migração: novos campos Feature 002 (idempotente)
python3 scripts/sync_votacoes_zil.py        # sync só votações ZIL definidas nos YAMLs
python3 scripts/apply_direcoes.py           # aplica direcao_esperada + peso + recalcula scores

# Sync de votações por proposição (busca votações na API da Câmara para cada proposição)
python3 scripts/sync_votacoes_proposicoes.py --dry-run             # preview sem gravar
python3 scripts/sync_votacoes_proposicoes.py                       # sync completo (pula proposições com votos)
python3 scripts/sync_votacoes_proposicoes.py --no-skip             # sync forçado (inclui todas)
python3 scripts/sync_votacoes_proposicoes.py --proposicao-id UUID  # sync de uma proposição específica

# Pipeline orquestrado (roda os 4 passos em sequência)
python3 scripts/sync_pipeline.py                                   # discovery → votações → enrichment → scores
python3 scripts/sync_pipeline.py --dry-run                         # preview completo
python3 scripts/sync_pipeline.py --skip-enrichment --skip-scores   # só discovery + votações
python3 scripts/sync_pipeline.py --skip-discovery --skip-votacoes  # só enrichment + scores

# Descoberta de proposições (busca na API da Câmara por keywords ZIL)
python3 scripts/discover_proposicoes.py --dry-run              # apenas mostra o que seria descoberto
python3 scripts/discover_proposicoes.py --enriquecer           # persiste + marca para enriquecimento
python3 scripts/discover_proposicoes.py --ano-inicio 2020      # janela temporal customizada
python3 -c "
import sys; sys.path.insert(0,'apps/api'); sys.path.insert(0,'.')
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.config import settings
from apps.workers.scoring import recalcular_todos_scores
engine = create_engine(settings.DATABASE_URL)
with Session(engine) as db: print(recalcular_todos_scores(db), 'scores calculados')
"
# Ou, se Celery estiver rodando:
# celery -A apps.workers.tasks call apps.workers.tasks.task_recalcular_scores
```

---

## Regras de código

### Python

- Imports curtos: `from models import Parlamentar` (não `from apps.api.models import`)
  — evita duplo registro de tabelas no SQLAlchemy (ADR-002)
- Tipos cross-DB: usar `JSON`, `Uuid` (não `JSONB`, `ARRAY`, `UUID` do PostgreSQL)
  — testes rodam em SQLite in-memory (ADR-001)
- `JSON(none_as_null=True)` em colunas filtradas com `IS NOT NULL` (ADR-003)
- Workers que importam de `apps/api`: adicionar `apps/api` ao `sys.path` explicitamente

### TypeScript / React

- Inline styles: **proibidos**. Usar exclusivamente classes Tailwind com tokens `zil-*`
- Componentes genéricos (Button, Badge, Card) em `components/ui/` — reutilizar, não recriar
- Novos tokens de cor/tipografia: adicionar em `tailwind.config.js` antes de usar

### Segurança e segredos

- **NUNCA commitar chaves, tokens ou senhas** — `.env` e variantes são gitignored
- `.env.example` contém APENAS placeholders vazios — nunca valores reais
- Secrets (API keys, tokens) devem ser vazios em defaults de código (`ANTHROPIC_API_KEY: str = ""`)
- Em produção, variáveis obrigatórias (`ANTHROPIC_API_KEY`, `ADMIN_TOKEN`) são validadas no startup — app recusa iniciar se ausentes
- Docker Compose carrega credenciais de `.env` via `env_file:` — nunca hardcoded no YAML para secrets reais
- Pre-commit hook `detect-secrets` bloqueia commits que contenham padrões de API keys
- Ao revisar código ou PRs: verificar se não há strings que pareçam tokens (prefixos `sk-`, `ghp_`, `Bearer`, etc.)

### Geral

- Não adicionar features além do solicitado
- Não mockar banco em testes de integração — usar SQLite in-memory via conftest.py
- PRs de dados editoriais (`data/`) requerem 2 aprovações de maintainers — norma
  de pé, **não cumprida**: há um maintainer ativo, e nenhum PR do projeto teve
  aprovação formal registrada. A [GOVERNANCE.md](docs/GOVERNANCE.md) v1.1
  registra o não-cumprimento sem alterar a norma; não apresentar decisão de uma
  pessoa como se fosse colegiada

---

## Escopo v1 (o que construir agora)

Numeração conforme `specs/`. Ver aviso sobre divergência com o ROADMAP acima.

| # | Feature | Status |
|---|---------|--------|
| 001 | Ingestão Câmara + scoring + API | ✅ concluído |
| 002 | Pipeline de enriquecimento legislativo (LLM + Planalto) | ✅ concluído |
| — | Ingestão Senado (crawler + client + tasks agendadas) | ✅ concluído |
| 003 | Workflow editorial via código (YAML + scripts) | ✅ mecanismo pronto · dados em formação |
| 004 | Frontend: /ranking com dados reais | ✅ concluído |
| 005 | Frontend: /parlamentar/[id] | ✅ concluído |
| 006 | Frontend: /proposicoes | ✅ concluído |
| 007 | Frontend: /bussula | ✅ concluído |
| 008 | Frontend: /metodologia | ✅ concluído |
| 009 | CI/CD (GitHub Actions) | ✅ 4 jobs verdes |
| 010 | Deploy produção | 🟡 preparado, não executado — `render.yaml` + [docs/DEPLOY.md](docs/DEPLOY.md) |

**O gargalo da v1 não é mais código, é curadoria.** O Score ZIL só conta votações
com `direcao_esperada` preenchida em `data/direcoes/[ano].yml` **e que tenham voto
individual registrado**. Hoje são 7 classificações, das quais **4 alimentam o
score**: as outras três são votações simbólicas (RICD art. 185), em que só o
resultado é proclamado e ninguém registra quem votou o quê.

Na varredura de 2023–2026, **86% das votações da Câmara foram simbólicas** — é a
regra, não a exceção. Qualquer seleção que não filtre por voto nominal desperdiça
a maior parte do esforço. `scripts/candidatas.py` já filtra; o validador confere
com `--verificar-api`.

> **O alvo mudou — [ADR-004](docs/decisions/004-placar-focado.md), aceito em
> 2026-09-18.** A v1 deixou de ser um índice dos 594 parlamentares e passou a ser
> um **placar focado**: como cada parlamentar votou nas ~10 votações que mais
> importaram para a soberania industrial. **Não há mais meta de cobertura.** O
> motor do Score e a fórmula não mudam — muda o universo sobre o qual ele opera.
>
> O que isso implica para quem trabalha no repositório:
>
> - **Quantidade deixou de ser critério de qualidade.** Dez classificações com
>   justificativa densa valem mais que centenas rasas. A unidade de trabalho é
>   pesquisar uma votação por vez, não classificar em lote.
> - **A seleção das ~10 é a decisão editorial mais carregada do projeto** — o
>   juízo que antes ficava diluído no volume. O critério de seleção tem de ser
>   publicado junto com o resultado.
> - **O destino das 9 categorias ZIL está em aberto.** Com ~10 votações, nove
>   categorias viram nove baldes quase vazios. É a próxima decisão de produto, e
>   ainda não foi tomada: não alterar a taxonomia sem RFC.
> - **O painel de agentes ([docs/PRD-PAINEL.md](docs/PRD-PAINEL.md)) não está no
>   caminho crítico.** O placar sai sem ele; a justificativa que resta ao painel
>   é escrutínio adversarial, não vazão (PRD-PAINEL §2.3).

Enquanto o placar não estiver curado, o ranking continua fora do ar — é o que as
flags abaixo garantem.

### Flags que mantêm o produto honesto

Duas chaves impedem o projeto de prometer mais do que a curadoria sustenta.
Mexer em qualquer uma é decisão editorial, não técnica:

| Flag | Onde | O que faz |
|---|---|---|
| `NEXT_PUBLIC_RANKING_PUBLICO` | `apps/web/lib/flags.ts` | Com `false` (default), `/ranking` e `/parlamentar/[id]` ficam fora do ar. Ligar só quando a curadoria sustentar o ranking |
| `noindex` | `apps/web/app/layout.tsx` + `apps/web/app/robots.ts` | Mantém o site fora dos buscadores. Estar no ar e estar no Google são coisas diferentes, e só a primeira é reversível |

### O painel de curadoria está em Fase 1 — e fora do caminho crítico

`data/painel/` e `apps/workers/panel/` implementam a **calibração** do painel
multi-perspectiva ([PRD-PAINEL](docs/PRD-PAINEL.md)): cinco agentes com viés
declarado analisam uma votação e produzem pareceres. A Fase 1 existe para
decidir se as Fases 2–4 acontecem — e, por ADR-004, **o placar sai sem o
painel**. Não condicione o lançamento ao go da Fase 1.

Antes de mexer, saiba o que o código garante por construção, e não por
disciplina de quem chama:

| Garantia | Onde mora |
|---|---|
| A etapa de análise é independente | A **assinatura** de `montar_prompt_analise(agente, briefing)` não recebe os pareceres dos demais. Não há como vazá-los por descuido |
| Ancoragem por configuração é barrada | A carga **recusa** agente de análise que declare `pareceres_dos_outros` como insumo |
| Nenhum agente mergeia; score só de YAML humano | O módulo não importa `scoring`, `models` nem `sqlalchemy`, e não escreve em disco — testes verificam na árvore sintática |
| Texto de fonte é dado não confiável | Ementa e texto do Planalto entram cercados por delimitadores, e qualquer sequência parecida com delimitador é removida antes |

Três coisas que convém não reaprender do jeito difícil:

- **`sem_materia` não é `contestada`.** A regra de consenso tem três saídas, não
  duas. Abstenção quase unânime (votação procedimental) é ausência de matéria;
  tratá-la como dissenso quebraria a métrica 5 da própria Fase 1.
- **`categoria_sugerida` é sugestão registrada, nunca campo normativo.** O
  ADR-004 deixou o destino das 9 categorias em aberto, então a Fase 1 não mede
  acurácia de categoria.
- **Os testes offline não provam que o painel resiste a injection.** Eles provam
  que o prompt está bem construído. Se o modelo obedece só se mede com chave, em
  `scripts/painel.py --injection`.

As definições em `data/painel/agentes/*.yml` seguem a governança dos dados
editoriais: quem escreve as instruções controla o resultado, então mudança vai
por PR e o `meta` de cada execução registra modelo, versão e hash das
instruções.

### Infraestrutura — armadilhas que já custaram caro

Resolvidas, mas entender o porquê evita reintroduzi-las:

| Item | O que aprender |
|------|----------------|
| Dados editoriais nos containers | `routers/bussula.py` e `workers/classifiers` resolvem o caminho **relativo ao próprio arquivo**, o que dentro do container dá `/data/...`. Sem o mount `./data:/data:ro`, o classificador cai numa taxonomia embutida com 44% das keywords e a Bússola responde `[]` — **silenciosamente**, sem erro. Ao criar novo loader de `data/`, confira que funciona no container. |
| Ordem do `make setup` | Migrations rodam **antes** da API subir. O `create_all` do lifespan cria as tabelas sem carimbo do Alembic, e aí `upgrade head` falha. Banco antigo nessa situação: `make migrate-stamp` uma vez. |
| Testes e seed rodam no host | Os scripts assumem a raiz do repo no `sys.path` (`apps.workers.*`, `packages.*`), e o container achata `apps/api` em `/app`. Não tente rodá-los via `docker compose exec api`. |
| `.env` é compartilhado com o compose | `Settings` usa `extra="ignore"`: variáveis que são só do compose (`POSTGRES_*`) não podem derrubar a aplicação no import. |
| Porta do Postgres | `POSTGRES_PORT` existe porque um Postgres local na 5432 sombreia o mapeamento do container — o host passa a falar com o banco errado, sem aviso. |

### Pendências de infraestrutura

| Item | Problema |
|------|----------|
| Deploy em produção | **Preparado, não executado.** `render.yaml` (API + Postgres) e o runbook em [docs/DEPLOY.md](docs/DEPLOY.md) existem; o que falta é rodar o blueprint no Render e conectar o frontend na Vercel. Não há `vercel.json` (a Vercel detecta Next.js sozinha) nem workflow de deploy — as duas plataformas fazem build no push. Typesense e os workers Celery ficam deliberadamente fora de produção; o porquê está no `render.yaml`. |
| Código dormente | Tabela `Financiamento` e enums `TipoAlerta`, `CanalAlerta`, `TipoFinanciamento` declarados e sem uso — resquícios de v2/v3. Conferido: nenhum uso fora de `apps/api/models/`. |
| Lint em `tests/` | 56 erros de ruff em `tests/`, fora do escopo da CI (que cobre só `apps/` e `packages/`, e passa limpo). |

### Design critiques — UI-001 a UI-022 ✅ concluídas

As quatro tabelas a seguir são **registro histórico**, não backlog. Todas as 22
tarefas foram implementadas — artefatos verificados em `components/ui/Badge.tsx`,
`components/DirecaoBadge.tsx`, `components/ParlamentarAvatar.tsx`,
`lib/categorias.ts`, entre outros. Ficam aqui porque documentam o *porquê* de
várias decisões de design que o código sozinho não explica.

### UI/UX — Melhorias de credibilidade e usabilidade (design critique 2026-04-02)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-001 | Score com âncora de credibilidade — tooltip no gauge com "baseado em N votos · ver metodologia →" | Estrutural | `ScoreGauge.tsx`, `ranking/page.tsx`, `parlamentar/[id]/page.tsx` |
| UI-002 | Remover "Contexto pendente" da UI pública — badge só aparece quando `pronto` | Estrutural | `ContextoBadge.tsx` |
| UI-003 | Contagem de resultados acima da lista — escopo visível antes de rolar | Comportamental | `ranking/page.tsx`, `proposicoes/page.tsx` |
| UI-004 | Empty states significativos — explicar ausência de dados vs. limitação de cobertura | Comportamental | `parlamentar/[id]/page.tsx`, `proposicoes/page.tsx`, `ranking/page.tsx` |
| UI-005 | Unificar linguagem de filtros — busca textual na mesma linha dos dropdowns; ordenação separada de filtros | Comportamental | `proposicoes/page.tsx`, `ranking/page.tsx` |
| UI-006 | Remover decoração tipográfica sem função — letra gigante (R, P) nos títulos de seção | Visual | `ranking/page.tsx`, `proposicoes/page.tsx` |
| UI-007 | Unificar sistema de badges — `Badge.tsx` com variantes `category`, `status`, `result` | Visual | `components/ui/Badge.tsx` (novo), `/[id]/page.tsx` |
| UI-008 | Ementa colapsada por padrão — primeira dobra sem jargão legal quando não há resumo_simples | Visual | `proposicoes/[id]/page.tsx` |

### UI/UX — Direção esperada e detalhes de proposição (design critique 2026-04-02 #2)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-009 | `DirecaoBadge` — componente compartilhado para `direcao_esperada`; exibe FAVORÁVEL/CONTRÁRIA com link para /metodologia | Estrutural | `components/DirecaoBadge.tsx` (novo), `proposicoes/[id]/page.tsx`, `votacoes/[id]/page.tsx` |
| UI-010 | Síntese de posição ZIL na proposição — "ZIL avalia: FAVORÁVEL · com base em N votações" acima da lista de votações | Estrutural | `proposicoes/[id]/page.tsx` |
| UI-011 | `resultado` inferido de `votos_sim/votos_nao` quando null — badge com `*` + `title` explicativo | Comportamental | `proposicoes/[id]/page.tsx` |
| UI-012 | Unificar padrão de collapse — substituir `useState` accordion por `<details>/<summary>` nativo | Visual | `proposicoes/[id]/page.tsx` |

### UI/UX — Página do parlamentar: IA, hierarquia e duplo encoding (design critique 2026-04-02 #3)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-013 | Hero metric zone — score e síntese de alinhamento como protagonistas visuais; substituir stats bar por bloco de 2 colunas com gauge + proporção | Estrutural | `parlamentar/[id]/page.tsx`, `ScoreGauge.tsx` |
| UI-014 | Legenda do duplo encoding — nota explicativa acima do histórico de votos: dot = alinhamento ZIL, badge = voto registrado | Estrutural | `parlamentar/[id]/page.tsx` |
| UI-015 | Affordance nos cards de categoria — subtítulo de instrução + indicador visual de filtro ativo | Comportamental | `parlamentar/[id]/page.tsx` |
| UI-016 | Consolidar design tokens e mapa de categorias — ScoreGauge usa `zil-*`; extrair `LABEL` para `lib/categorias.ts` | Visual | `ScoreGauge.tsx`, `CategoriaBadge.tsx`, `lib/categorias.ts` (novo), `parlamentar/[id]/page.tsx` |
| UI-017 | Scope e navegação no histórico de votos — contagem sempre visível no título + corrigir back link hardcoded | Comportamental | `parlamentar/[id]/page.tsx` |

### UI/UX — Perfil do parlamentar: redundância e clareza (design critique 2026-04-04 #4)

| # | Task | Severidade | Arquivos principais |
|---|------|-----------|-------------------|
| UI-018 | Eliminar score duplicado no hero — substituir `text-4xl` redundante por frase interpretativa de alinhamento | Estrutural | `parlamentar/[id]/page.tsx` |
| UI-019 | Consolidar contagem de votos — unificar "com base em N votos" e "N de N votos" num único local | Estrutural | `parlamentar/[id]/page.tsx`, `ScoreGauge.tsx` |
| UI-020 | Legenda do duplo encoding com exemplo visual — substituir "badge = voto registrado" por mini badge real | Comportamental | `parlamentar/[id]/page.tsx` |
| UI-021 | Remover código interno dos cards de categoria — esconder "ZIL-ENE" do público, mover para `title` | Visual | `parlamentar/[id]/page.tsx` |
| UI-022 | Frase de síntese interpretativa — "Votou a favor em N de N pautas monitoradas" acima do hero metric | Estrutural | `parlamentar/[id]/page.tsx` |

## Fora do escopo v1 (não implementar)

- Autenticação / login / contas de usuário
- "Cobrar meu deputado"
- Alertas (email, Telegram, push)
- Deliberação por consenso (Polis)
- Curadoria comunitária (contestações)
- Compromisos públicos de parlamentares
- Dados de financiamento (TSE)
- Monitor eleitoral
- Fórum de discussão

---

## Workflow editorial v1

Toda gestão editorial é via código — sem interface admin:
- Classificação automática: `data/taxonomia/categorias.yml` (PR)
- Direção esperada de votações: `data/direcoes/[ano].yml` (PR + Discord; a norma
  pede 2 aprovações e o projeto tem um maintainer — ver "Regras de código")
- Indicadores Bússola: `data/bussula/marcos.yml` (PR + link para fonte oficial)
- Aplicar ao banco: `python scripts/apply_direcoes.py`
- Validar os YAMLs: `python scripts/validar_direcoes.py`
  (`--verificar-api` confere na Câmara se cada votação teve voto nominal)

**O ciclo de curadoria, na ordem** — as duas primeiras ferramentas rodam sem
banco e sem `ANTHROPIC_API_KEY`, direto contra a API da Câmara:

```bash
python scripts/candidatas.py --ano 2025            # ranqueia votações por saliência,
                                                   # já filtrando simbólicas
python scripts/dossie.py --votacao 2454704-53      # reúne o que a pesquisa exigiria ler
                                                   # (emite YAML SEM o campo direcao)
# → decisão humana: preencher direcao + justificativa em data/direcoes/[ano].yml
python scripts/validar_direcoes.py --verificar-api  # confere schema e voto nominal
python scripts/apply_direcoes.py                   # aplica e recalcula scores
```

O `dossie.py` **não decide**: o YAML sai sem `direcao` de propósito. É a decisão
que o projeto existe para manter humana.

### Como as ~10 votações do placar são escolhidas

O [ADR-004](docs/decisions/004-placar-focado.md) exige que **o critério de
seleção seja publicado junto com o resultado**, porque num placar focado a
escolha das votações passa a ser a decisão editorial mais carregada do projeto.
O critério está implementado na propriedade `escore` de `scripts/candidatas.py`,
e é este:

| Termo | Peso | O que mede |
|---|---|---|
| Keyword **forte** da taxonomia | **+8,0** (+0,5 por extra, até 3) | A votação é sobre pauta ZIL de verdade |
| Só keyword **fraca** | **−6,0** | Sinal contrário, não sinal fraco — ver abaixo |
| Direção indecidível | **−12,0** | Voto sobre emenda ou destaque: "sim" aprova a emenda, e o texto dela não vem na API |
| Disputa | até **+10,0** | `(1 − margem) × 10` — quanto mais apertado, mais separa parlamentares |
| Voto sobre o texto | +4,0 | Substitutivo global ou o projeto inteiro |
| Pistas de plenário | +3,0 | Não há campo que distinga plenário de comissão; só o texto da descrição |
| Requerimento de **urgência** | −1,0 | Nomeia o objeto, então é preferência revelada — mas mede intenção de pautar, não posição sobre o mérito |
| Outro **processual** | −4,0 | "Rejeitado o Requerimento" não diz qual: `objetosPossiveis` devolve dezenas (81 numa votação da PONTE). Sem saber o que se rejeitou, a direção é chute |

**A ordem dos termos importa, e já esteve errada.** Até a varredura de 2024/2025
a nota somava apenas disputa e formato, e o tema entrava como meio ponto por
categoria. O resultado: a **Política Nacional de Minerais Críticos** — a tese do
projeto em forma de lei — ficou em **último lugar entre 12**, porque foi quase
unânime; e a **Tarifa Social de Água e Esgoto** liderou, por ter casado com a
palavra `tarifa`. Com placar focado, o topo da lista tem de ser o que mais
importa, não o que foi mais apertado. Hoje o tema é o termo dominante, e a
disputa só desempata entre votações que já passaram pelo tema.

**Casamento só por keyword fraca é sinal contrário.** Daí o −6,0 em vez de um
bônus menor: todas as evidências de casamento fraco isolado que o projeto
acumulou são falso positivo. Foi assim que homicídio qualificado virou soberania
digital, por citar a LGPD entre as leis que alterava.

**O escore mede saliência, nunca mérito.** Ele diz onde vale gastar curadoria;
não diz a direção, e não deve ser lido como se dissesse. A seleção final das ~10
é decisão humana — o `escore` apenas ordena as candidatas, e o `dossie.py`
reúne o que a decisão exige ler.

**Campos de uma entrada em `data/direcoes/[ano].yml`:**

| Campo | Obrigatório | Valores |
|---|---|---|
| `fonte_id`, `fonte`, `direcao` | sim | `direcao`: `sim` ou `nao` |
| `justificativa` | sim | texto; o validador exige ≥ 40 caracteres |
| `peso` | não | `0.5`, `1.0`, `2.0`, `3.0` |
| `validacao` | não | `nao-validado`, `revisado` |
| `processo` | não | `nominal`, `simbolica` |

**`processo` é o campo que evita trabalho perdido.** Votação simbólica
(RICD art. 185) não registra o voto de cada deputado — só o resultado é
proclamado —, então ela **não contribui para o Score ZIL**, com ou sem
classificação. Na varredura de 2023–2026, 86% das votações foram simbólicas.
O `dossie.py` avisa antes da pesquisa, o `validar_direcoes.py --verificar-api`
confere contra a API, e o `apply_direcoes.py` avisa ao aplicar.

**Princípio operacional:** na dúvida sobre direção esperada, não classificar.

---

## Changelog

**Arquivo:** [`docs/CHANGELOG.md`](docs/CHANGELOG.md)
**Formato:** [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

### Quando atualizar

Atualizar o changelog é **obrigatório** ao:
- Completar qualquer feature do backlog v1 (001–010)
- Corrigir um bug que afete comportamento observável
- Fazer breaking changes em contratos de API ou modelos
- Alterar arquivos de dados editoriais (`data/`)
- Mudar configuração de CI, Docker ou ambiente de desenvolvimento

Não é necessário para: refatorações internas sem impacto externo, atualizações de docs, correções de lint.

### Como atualizar

1. **Durante o desenvolvimento** — adicionar entradas em `## [Unreleased]`, sob a
   sub-seção correta:
   - `Added` — nova funcionalidade
   - `Changed` — mudança em funcionalidade existente
   - `Fixed` — correção de bug
   - `Removed` — remoção de funcionalidade
   - `Security` — vulnerabilidade corrigida

2. **Ao criar uma release** — renomear `[Unreleased]` para `[X.Y.Z] — YYYY-MM-DD`,
   adicionar novo `## [Unreleased]` vazio no topo, e atualizar os links de comparação
   no rodapé do arquivo.

3. **Formato de entrada:**
   ```
   - `caminho/do/arquivo.py`: descrição objetiva da mudança — consequência ou motivação
   ```
   Entradas devem ser legíveis por alguém que não viu o PR. Evitar "fixed bug" sem
   descrever qual bug; evitar "updated file" sem descrever o que mudou.

4. **Versionamento semântico:**
   - `MAJOR` (X.0.0): breaking change em API pública ou modelo de dados
   - `MINOR` (0.X.0): nova feature sem quebrar compatibilidade
   - `PATCH` (0.0.X): correção de bug, ajuste de config, fix de CI

### Regra geral

> Se a mudança vale um commit `feat:` ou `fix:`, vale uma entrada no changelog.
> Se vale um commit `chore:` ou `refactor:`, provavelmente não vale.

---

## Convenções de commit

```
feat:     nova feature
fix:      correção de bug
data:     mudança em data/ (classificações, direções, bússola)
docs:     documentação
test:     testes
refactor: refatoração sem mudança de comportamento
chore:    infra, CI, deps
```

---

## Princípios da constituição (resumo)

1. **Dados públicos, acesso livre** — toda leitura sem autenticação
2. **Apartidário por design** — paleta verde/ouro, linguagem neutra
3. **Transparência radical** — classificações auditáveis, histórico no git
4. **Projeto de estado** — métricas verificáveis, independente de governo
5. **Design system** — tokens `zil-*`, componentes reutilizáveis, sem inline styles
6. **API-first** — funcionalidade acessível via API antes de ter UI
7. **Qualidade** — testes obrigatórios para scoring, classifier e endpoints críticos

## Active Technologies
- Python 3.12 (backend/workers), TypeScript 5 (frontend) + FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2, Celery 5, httpx 0.27, anthropic SDK, Next.js 14, React 18, Tailwind CSS (002-legislative-enrichment-pipeline)
- SQLite (development, in-memory for tests), PostgreSQL 16 (production), Redis 7 (Celery broker/cache) (002-legislative-enrichment-pipeline)
- Python 3.12 (backend), TypeScript 5 (frontend) + FastAPI 0.111, Pydantic 2, SQLAlchemy 2.0, Next.js 14, React 18, Tailwind CSS (011-resumo-simples-votos-historico)
- SQLite (dev) / PostgreSQL 16 (prod) — campo `resumo_simples` ja existe no modelo `Proposicao` (011-resumo-simples-votos-historico)

## Recent Changes
- 002-legislative-enrichment-pipeline: Added Python 3.12 (backend/workers), TypeScript 5 (frontend) + FastAPI 0.111, SQLAlchemy 2.0, Pydantic 2, Celery 5, httpx 0.27, anthropic SDK, Next.js 14, React 18, Tailwind CSS

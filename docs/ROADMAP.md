# ZIL Observatório — Roadmap

**Última atualização:** 2026-04-02
**Status:** v0 ✅ completo → v1 em andamento

---

> **Mudança de rumo (2026-09-18).** Este roadmap foi escrito para um **índice
> abrangente** — cobertura dos 594 parlamentares, "ranking completo", métrica de
> "100% dos 513 deputados". O [ADR-004](decisions/004-placar-focado.md) trocou
> isso por um **placar focado em ~10 votações** bem pesquisadas.
>
> As metas de cobertura abaixo **estão revogadas** como objetivo da v1. O texto
> foi mantido como registro da ambição original — ela não foi abandonada, foi
> reordenada: cobertura é consequência de capacidade editorial, não premissa de
> produto. Leia o que segue com essa ressalva.

## Princípio de priorização

> Entregar a ferramenta de observabilidade pública antes das eleições de outubro de 2026. Tudo que não serve a esse objetivo é v2 ou posterior.

---

## v0 — Fundação ✅ (concluído)

**Objetivo:** infraestrutura técnica funcional com dados reais da Câmara.

| Feature | Spec | Status |
|---------|------|--------|
| Modelos de dados (SQLAlchemy 2.0) | — | ✅ |
| API FastAPI com endpoints públicos | — | ✅ |
| Crawler Câmara dos Deputados | 001 | ✅ |
| Scoring engine ZIL | 001 | ✅ |
| Agendamento Celery (6h votações, semanal deputados) | 001 | ✅ |
| 98 testes automatizados | 001 | ✅ |
| Homepage redesign (Tailwind, responsiva) | — | ✅ |
| Componentes UI base (Button, Badge, Card, Callout) | — | ✅ |

---

## v1 — Dashboard Público (foco atual)

**Objetivo:** plataforma pública, sem login, onde qualquer cidadão ou jornalista possa explorar o ranking completo de parlamentares, entender proposições classificadas, e conhecer a Bússola ZIL.

**Prazo alvo:** antes das eleições de outubro de 2026.

**Fora de escopo v1** (explicitamente): contas de usuário, login, deliberação por consenso, cobrar parlamentar, alertas, sistema de contestações, curadoria comunitária, financiamento de campanha, monitor eleitoral, gamificação.

**Gestão editorial v1:** via código — YAML versionado em git + PRs + issues.

### Backlog v1

#### 002 — Ingestão do Senado Federal
Completar cobertura dos 594 parlamentares (513 deputados + 81 senadores).

- [ ] `packages/senado_client/` — cliente HTTP para API do Senado (XML/JSON)
- [ ] `apps/workers/crawlers/senado.py` — sync senadores, votações, votos
- [ ] Mapear `FonteEnum.SENADO` nas models existentes
- [ ] Testes de integração e idempotência
- [ ] Adicionar `task_sync_senado` no Celery beat

**Dependências:** nenhuma (paralelo ao restante do frontend).

---

#### 003 — Workflow Editorial via Código
Permitir que maintainers definam `direcao_esperada` de votações e gerenciem a Bússola ZIL via YAML + PRs, sem interface admin.

- [ ] `data/direcoes/` — formato YAML: `[{votacao_fonte_id, fonte, direcao, peso, justificativa}]`
- [ ] `scripts/apply_direcoes.py` — CLI que lê YAML e atualiza banco
- [ ] `data/bussula/marcos.yml` — indicadores estratégicos com valor atual, meta, fonte oficial
- [ ] `apps/api/routers/bussula.py` — `GET /bussula` retorna marcos ZIL
- [ ] Documentar workflow editorial em `docs/EDITORIAL.md`

**Dependências:** nenhuma (paralelo ao restante do frontend).

---

#### 004 — Frontend: Ranking Completo (`/ranking`)
Página principal do produto. Ranking de todos os parlamentares com filtros.

- [ ] Dados reais da API (substituir mock/fallback do RankingPreview)
- [ ] Filtros: UF, partido, categoria ZIL, casa (Câmara/Senado), ordem (score asc/desc/nome)
- [ ] Paginação ou infinite scroll
- [ ] ParlamentarCard com score gauge, partido, UF
- [ ] Empty state quando `score_zil = null` ("sem votos ZIL suficientes")
- [ ] Loading skeleton

**Dependências:** 001 (concluído). Senado (002) enriquece, mas não bloqueia.

---

#### 005 — Frontend: Perfil do Parlamentar (`/parlamentar/[id]`)
Página de detalhe com histórico completo de votos em pautas ZIL.

- [ ] Dados reais da API (`GET /parlamentares/{id}` + `GET /parlamentares/{id}/votos-zil`)
- [ ] Score gauge com valor e posição no ranking
- [ ] Breakdown por categoria ZIL (quanto do score vem de cada área)
- [ ] Histórico de votações ZIL: data, descrição, categoria, voto, alinhamento
- [ ] Link para proposição em cada votação
- [ ] Loading/error state

**Dependências:** 001, 004.

---

#### 006 — Frontend: Proposições e Votações (`/proposicoes`)
Catálogo filtrável de proposições e votações classificadas por pauta ZIL.

- [ ] Dados reais da API (`GET /proposicoes` + `GET /votacoes`)
- [ ] Filtros: categoria ZIL, ano, tipo (PL, PEC, PLP)
- [ ] Card de proposição: ementa, tipo, categorias, relevância
- [ ] Página de detalhe `/proposicoes/[id]`: votações vinculadas + como cada parlamentar votou
- [ ] Paginação

**Dependências:** 001.

---

#### 007 — Frontend: Bússola ZIL (`/bussula`)
Painel de indicadores estratégicos — o estado atual da soberania industrial brasileira.

- [ ] Dados da API (`GET /bussula`)
- [ ] Grid de indicadores por categoria ZIL
- [ ] Cada indicador: valor atual, meta, tendência (▲▼→), fonte com link oficial
- [ ] Linha do tempo por governo (v1: estático via YAML)
- [ ] Explicação metodológica do que é a Bússola

**Dependências:** 003.

---

#### 008 — Frontend: Metodologia (`/metodologia`)
Página explicativa sobre o Score ZIL, categorias, processo editorial e limitações.

- [ ] Como o score é calculado (fórmula, pesos, exemplos)
- [ ] As 9 categorias ZIL com descrição e exemplos
- [ ] Como a direção esperada é definida (processo editorial via código e issues)
- [ ] Limitações do classificador automático
- [ ] Como contribuir (GitHub; Discord quando existir)

**Dependências:** nenhuma.

---

#### 009 — CI/CD
Pipeline de qualidade obrigatório para merges em `main`.

- [ ] GitHub Actions: `pytest`, `ruff check`, `mypy --strict` (apps/api)
- [ ] GitHub Actions: `tsc --noEmit`, `eslint`, `next build` (apps/web)
- [ ] Badge de status no README
- [ ] Lint automático em PRs

**Dependências:** nenhuma (paralelo a qualquer coisa).

---

#### 010 — Deploy Produção
Infraestrutura para a plataforma estar acessível publicamente.

- [ ] Definir ambiente de produção (Railway / Render / VPS)
- [ ] Docker Compose de produção com PostgreSQL + Redis + API + Web + Workers
- [ ] Variáveis de ambiente e secrets no CI
- [ ] Backup automático do banco
- [ ] Domínio e HTTPS

**Dependências:** todos os anteriores.

---

#### 011 — Bootstrap de Dados Históricos (sync operacional)

O crawler `sync_votacoes` existe mas só roda via Celery beat. Para o ambiente de
desenvolvimento e para a carga inicial em produção, precisamos de um caminho direto
que não exija o stack Celery completo.

Problema atual: `sync_votacoes` para um ano inteiro faz ~3.000 chamadas à API
(1.000 votações × detalhes + votos). Para votações sem relevância ZIL, buscar os
votos individuais é desperdício. A solução é um modo "ZIL-first" que adia o fetch
de votos para votações não classificadas.

**Tasks:**

- [ ] `scripts/bootstrap_sync.py` — CLI que roda `sync_deputados` +
  `sync_votacoes(anos)` direto contra o banco sem precisar do Celery.
  Aceita `--anos 2024 2025`, `--fonte camara|senado|ambos`, `--dry-run`.
  Mostra progresso em tempo real (barra, contadores).

- [ ] Modo ZIL-smart no crawler: em `sync_votacoes`, classificar a descrição
  **antes** de buscar votos individuais. Se `categorias_zil` for vazio, registrar
  a votação sem votos (metadado apenas). Buscar votos só para votações ZIL.
  Reduz o tempo de sync de ~60 min para ~5 min por ano.

- [ ] `GET /ingestion/status` — endpoint que retorna o estado da última
  `IngestionRun` por tipo (`deputados`, `votacoes`, `votacoes_senado`), data/hora,
  contadores e eventuais erros. Usado para monitoramento e healthcheck.

- [ ] `scripts/listar_sem_direcao.py` — lista votações com `categorias_zil` definido
  mas `direcao_esperada` ausente; exporta CSV para revisão editorial.
  Aceita `--categoria ZIL-FER` para filtrar por categoria.

- [ ] Runbook em `docs/SYNC_RUNBOOK.md`: como fazer a carga inicial, como
  monitorar o Celery em produção, o que fazer quando o sync falha.

- [ ] Atualizar `CLAUDE.md` com instrução `python scripts/bootstrap_sync.py`
  no bloco de comandos.

**Dependências:** nenhuma (independente).

---

#### 012 — Cobertura Editorial: Score com Dados Reais

Para que os scores apareçam no ranking, todas as votações ZIL classificadas pelo
classificador automático precisam ter `direcao_esperada` definida por maintainers.

Este fluxo de trabalho deve se tornar um processo contínuo: sempre que novos votos
relevantes chegam via sync, a equipe editorial revisa e classifica.

**Tasks:**

- [ ] Preencher `data/direcoes/2024.yml` com todas as votações ZIL identificadas
  em 2024 (post-sync). Mínimo 20 votações. Ver `docs/EDITORIAL.md`.

- [ ] Preencher `data/direcoes/2025.yml` com votações ZIL de 2025 até a data atual.

- [ ] Criar `docs/EDITORIAL.md` — guia para maintainers: como identificar votações
  relevantes, como escrever justificativas, critério de peso (processual vs.
  plenário final), como abrir PR, processo de revisão em issue.

- [ ] Adicionar validação em `scripts/apply_direcoes.py`: antes de aplicar,
  verificar se todos os `fonte_id` existem no banco. Imprimir aviso para os que
  não existem (votação ainda não sincronizada).

- [ ] Script `scripts/recalcular_scores.py` — standalone, sem Celery.
  Chama `recalcular_todos_scores(db)` e imprime resumo (N scored, média, top 5,
  bottom 5).

- [ ] Cobertura mínima para lançamento: ≥ 50 votações classificadas com
  `direcao_esperada`, cobrindo todas as 9 categorias ZIL.

**Dependências:** 011 (sync precisa ter rodado para ter votações no banco).

---

### Diagrama de dependências v1

```
001 (✅) ──────┬──── 004 (/ranking) ◄─── 012 (scores reais)
               │                              ▲
               ├──── 005 (/parlamentar/[id])   │
               │                          011 (sync bootstrap)
               └──── 006 (/proposicoes)

002 (Senado) ──┘ (enriquece 004/005, não bloqueia)

003 (Editorial) ──── 007 (/bussula)

008 (/metodologia) ── independente

009 (CI/CD) ── independente

010 (Deploy) ── depende de tudo

011 (bootstrap) ──── 012 (cobertura editorial) ──── scores no ranking
```

---

## v2 — Participação (após v1 estável)

**Objetivo:** introduzir autenticação e as primeiras features que requerem identidade de usuário.

| Feature | Descrição |
|---------|-----------|
| Autenticação | Magic link + Google/GitHub. Email + UF obrigatórios. CPF opcional (hash). |
| Assinar o manifesto | Com persistência real no banco e contador público |
| Alertas | Notificação quando parlamentar monitorado vota em pauta ZIL (email/Telegram) |
| "Cobrar meu deputado" | Template pré-preenchido com dados reais, enviado por canal oficial |
| Curadoria básica | Membros podem propor reclassificação de proposição com justificativa |
| Financiamento de campanha | Crawler TSE, cruzamento doadores ↔ votos |

---

## v3 — Deliberação e Mobilização (visão de longo prazo)

**Objetivo:** plataforma completa com deliberação por consenso e mobilização eleitoral.

| Feature | Descrição |
|---------|-----------|
| Deliberação Polis | Votação em declarações ao estilo vTaiwan para decisões estratégicas |
| Monitor Eleitoral 2026 | Comparativo candidatos incumbentes vs. histórico ZIL |
| Compromisos públicos | Parlamentares registram posições verificáveis (hash SHA-256) |
| Índice de Continuidade | Mede continuidade de programas entre governos |
| Dados subnacionais | Assembleias estaduais, câmaras municipais |
| Gamificação | Badges, leaderboard de contribuidores |

---

## O que é gerenciado via código em v1 (sem interface admin)

| O que | Onde | Como |
|-------|------|------|
| Keywords de classificação | `data/taxonomia/categorias.yml` | PR no GitHub |
| Direção esperada de votações | `data/direcoes/*.yml` | PR + review em issue |
| Indicadores da Bússola | `data/bussula/marcos.yml` | PR + review em issue |
| Pesos de votações | Campo `peso` nas Votacoes | PR no banco via migration |
| Decisões técnicas | `docs/decisions/` (ADRs) | Issue + PR |

---

## Métricas de sucesso v1

| Métrica | Meta |
|---------|------|
| Votações com justificativa pesquisada e revisada | ~10 (ver ADR-004) |
| Votações ZIL classificadas com direção esperada | ≥ 50 votações-chave (2024-2026) — ver feature 012 |
| Tempo de sync inicial (bootstrap) | < 10 min para 2 anos (modo ZIL-smart, feature 011) |
| Latência dado → plataforma | < 24h |
| Uptime | ≥ 99% |
| Tempo de resposta da API | < 500ms (p95) |
| Veículos que citam dados ZIL | ≥ 5 antes das eleições |

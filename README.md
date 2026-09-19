# ZIL Observatório

**Plataforma pública de monitoramento do Congresso Nacional na pauta da soberania industrial brasileira.**

O Brasil tem 94% do nióbio mundial e importa 87% dos fertilizantes. Exporta petróleo cru e importa gasolina. Vende soja a granel e compra ração processada. O ZIL Observatório torna visível quem no Congresso está trabalhando para mudar isso — e quem está trabalhando contra.

[PRD](docs/PRD.md) · [Arquitetura](docs/ARCHITECTURE.md) · [Deploy](docs/DEPLOY.md) · [Roadmap](docs/ROADMAP.md) · [Governança](docs/GOVERNANCE.md) · [Changelog](docs/CHANGELOG.md)

O manifesto é a própria home da plataforma (`/`), não um documento separado.

[![CI](https://github.com/melissa-pereira-deel/zil-observatorio/actions/workflows/ci.yml/badge.svg)](https://github.com/melissa-pereira-deel/zil-observatorio/actions/workflows/ci.yml)

---

## O que é

O ZIL Observatório mostra **como os parlamentares votaram nas votações que mais
importaram para a soberania industrial** do país — fertilizantes, minerais
estratégicos, semicondutores, energia, soberania digital, defesa e capital humano.

A v1 é um **placar focado**, não um índice abrangente: em vez de tentar pontuar
os 594 parlamentares em toda pauta classificável, o objetivo é selecionar **~10
votações** e pesquisá-las a fundo. A razão está no
[ADR-004](docs/decisions/004-placar-focado.md): o gargalo do projeto nunca foi
código, é julgamento editorial em volume — e profundidade é o que uma equipe
pequena consegue entregar com credibilidade.

A plataforma é um **dashboard público de leitura**:
- Calcula o **Score ZIL** (−10 a +10) a partir dos votos nas votações selecionadas
- Lista **proposições monitoradas**, com a ementa jurídica traduzida para
  linguagem simples usando o texto real das leis citadas
- Mostra a **Bússola ZIL** — indicadores do estado atual da soberania industrial

Todo o código é aberto e toda classificação é auditável via git.

## Status

**v0 concluído · v1 em andamento** — código praticamente completo, dados editoriais ainda em formação.

### Software

| Componente | Status |
|------------|--------|
| Modelos de dados (SQLAlchemy 2.0, 8 tabelas) | ✅ |
| API FastAPI — 17 endpoints públicos | ✅ |
| Crawler Câmara dos Deputados | ✅ |
| Crawler Senado Federal | ✅ implementado — **nenhum dado ingerido ainda** |
| Classificador por keywords (9 categorias) | ✅ |
| Scoring engine ZIL | ✅ |
| Pipeline de enriquecimento (Planalto + LLM) | ✅ |
| Agendamento Celery (6 tarefas) | ✅ |
| Frontend — 8 páginas | ✅ |
| 151 testes automatizados | ✅ |
| CI (GitHub Actions, 4 jobs) | ✅ |
| Deploy em produção | config pronta — ver [DEPLOY.md](docs/DEPLOY.md) |

### Dados editoriais

Este é o gargalo real do projeto. O motor está construído, mas o Score ZIL só
considera votações que passaram por curadoria humana — e a curadoria ainda é fina:

| Insumo | Volume atual |
|--------|--------------|
| Categorias ZIL com keywords | 9 |
| Votações com `direcao_esperada` definida | 7 |
| Indicadores da Bússola | 4 |

As 7 estão marcadas `validacao: nao-validado` nos próprios arquivos: foram
criadas num único dia, por uma pessoa, e o método não é reconstituível.

Chegar a ~10 votações **bem pesquisadas e revisadas** é o que separa "o sistema
funciona" de "o placar pode ser publicado". O ranking está fora do ar até lá —
ver [ADR-004](docs/decisions/004-placar-focado.md) e
[DEPLOY.md](docs/DEPLOY.md).

### Páginas

`/` (manifesto) · `/ranking` · `/parlamentar/[id]` · `/proposicoes` ·
`/proposicoes/[id]` · `/votacoes/[id]` · `/bussula` · `/metodologia`

## Quick Start (desenvolvimento)

```bash
# Pré-requisitos: Python 3.12 e Node.js 20.
# Redis só é necessário para os workers Celery; Docker, para o ambiente completo.
# Os testes rodam sem nenhum dos dois.

git clone https://github.com/melissa-pereira-deel/zil-observatorio.git
cd zil-observatorio

# Backend — instalar dependências
pip install -r apps/api/requirements.txt

# Rodar testes (SQLite in-memory, sem Docker nem Redis)
python -m pytest tests/

# API local — precisa rodar de dentro de apps/api:
# o projeto usa imports curtos (`from core.config import ...`, ver ADR-002),
# então `uvicorn apps.api.main:app` a partir da raiz falha com ModuleNotFoundError
cd apps/api && uvicorn main:app --reload
# → http://localhost:8000/docs

# Frontend
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

Para ambiente completo com PostgreSQL, Redis e Typesense:

```bash
docker compose up -d   # ou: make up
```

O schema é criado automaticamente no startup da API em desenvolvimento
(`Base.metadata.create_all`), então não é preciso rodar migrations para
desenvolver. O banco sobe vazio — os dados vêm dos crawlers.

Ou, de uma vez (build, migrations, serviços e dados iniciais):

```bash
make setup
```

O `make seed` popula o banco com as votações **já curadas** em `data/direcoes/` —
dado real da API da Câmara, não fictício — e recalcula os scores.

**Já tem um banco criado antes do Alembic?** Se o schema veio do `create_all` do
startup, ele não tem o carimbo de versão e o `make migrate` falha. Rode uma vez:

```bash
make migrate-stamp
```

**Postgres local na 5432?** O mapeamento do container fica sombreado e o host
acaba falando com o banco errado. Defina outra porta no `.env`:
`POSTGRES_PORT=5433` e ajuste a `DATABASE_URL` para a mesma porta.

Os testes do backend rodam no **host**, não no container: eles importam tanto
`models`/`main` (imports curtos de `apps/api`) quanto `apps.*` e `packages.*` (da
raiz), e o container achata `apps/api` em `/app`. É também como a CI roda.

## Fontes de Dados

| Fonte | Dados | Status |
|-------|-------|--------|
| [Câmara dos Deputados](https://dadosabertos.camara.leg.br) | Deputados, votações, proposições | ✅ |
| [Senado Federal](https://legis.senado.leg.br/dadosabertos) | Senadores, matérias, votações | Crawler pronto, **sem dado ingerido** |
| [Planalto](https://www.planalto.gov.br) | Texto de artigos de lei citados (cache com expiração) | ✅ |

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0 |
| Workers | Celery 5, Redis 7 |
| Frontend | Next.js 14, TypeScript 5, Tailwind CSS |
| Enriquecimento | Claude Haiku 4.5 (opcional — sem chave, o pipeline apenas não roda) |
| Busca | Typesense 27 |
| Banco (dev/testes) | SQLite in-memory |
| Banco (produção) | PostgreSQL 16 |
| Testes | pytest 8 (151 testes) |
| CI | GitHub Actions — lint backend, testes, lint + type check frontend, build |

## Escopo v1

O objetivo da v1 é entregar uma ferramenta de observabilidade pública que seja
**verdadeira sobre o que sabe**: um placar de ~10 votações bem pesquisadas, em
vez de um índice raso de todas.

**Fora do escopo v1** (não será implementado nesta versão):
- Autenticação / login / contas de usuário
- "Cobrar meu deputado"
- Alertas (email, push, Telegram)
- Deliberação por consenso
- Curadoria comunitária / contestações
- Dados de financiamento de campanha (TSE)
- Monitor eleitoral

## Workflow Editorial

Toda a gestão editorial é feita via código pelos mantenedores — sem interface admin:

- **Classificação automática**: keywords em `data/taxonomia/categorias.yml`
- **Direção esperada de votações**: `data/direcoes/[ano].yml` (PR com justificativa escrita — ver [GOVERNANCE.md](docs/GOVERNANCE.md) para o processo real e para o que a norma exige)
- **Indicadores Bússola**: `data/bussula/marcos.yml` (PR + link para fonte oficial)
- **Aplicar ao banco**: `python scripts/apply_direcoes.py`

Princípio: na dúvida sobre a direção esperada de uma votação, não classificar.

## Como Contribuir

1. Leia o [guia de contribuição](CONTRIBUTING.md) — ele começa dizendo o estado
   real do projeto (hoje, uma pessoa)
2. Abra uma issue antes de investir tempo. O Discord será criado e o convite
   publicado aqui quando existir
3. Fork → branch → PR (com testes para código de backend)
4. Dados editoriais (`data/`) exigem justificativa escrita — ver
   [GOVERNANCE.md](docs/GOVERNANCE.md)

**Não precisa saber programar**: curadoria de classificações de proposições, verificação de indicadores da Bússola e documentação são igualmente importantes.

## Licença

Código: [AGPL-3.0](LICENSE)

Dados e conteúdo editorial: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

---

*O Brasil é de todos. A soberania também.*

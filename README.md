# ZIL Observatório

**Plataforma pública de monitoramento do Congresso Nacional na pauta da soberania industrial brasileira.**

O Brasil tem 94% do nióbio mundial e importa 87% dos fertilizantes. Exporta petróleo cru e importa gasolina. Vende soja a granel e compra ração processada. O ZIL Observatório torna visível quem no Congresso está trabalhando para mudar isso — e quem está trabalhando contra.

[PRD](docs/PRD.md) · [Arquitetura](docs/ARCHITECTURE.md) · [Roadmap](docs/ROADMAP.md) · [Governança](docs/GOVERNANCE.md) · [Changelog](docs/CHANGELOG.md)

O manifesto é a própria home da plataforma (`/`), não um documento separado.

[![CI](https://github.com/melissa-pereira-deel/manifesto-zil/actions/workflows/ci.yml/badge.svg)](https://github.com/melissa-pereira-deel/manifesto-zil/actions/workflows/ci.yml)

---

## O que é

O ZIL Observatório monitora o posicionamento de cada deputado e senador brasileiro nas votações que determinam a soberania industrial do país — fertilizantes, minerais estratégicos, semicondutores, energia, soberania digital, defesa e capital humano.

A plataforma v1 é um **dashboard público de leitura**:
- Calcula o **Score ZIL** (-10 a +10) para cada parlamentar baseado em como votou em pautas classificadas
- Exibe o **ranking completo** de parlamentares com histórico de votações
- Lista **proposições monitoradas** por categoria estratégica
- Mostra a **Bússola ZIL** — indicadores do estado atual da soberania industrial

Todos os dados são públicos. Todo o código é aberto. Toda classificação é auditável via git.

## Status

**v0 concluído · v1 em andamento** — código praticamente completo, dados editoriais ainda em formação.

### Software

| Componente | Status |
|------------|--------|
| Modelos de dados (SQLAlchemy 2.0, 8 tabelas) | ✅ |
| API FastAPI — 17 endpoints públicos | ✅ |
| Crawler Câmara dos Deputados | ✅ |
| Crawler Senado Federal | ✅ |
| Classificador por keywords (9 categorias) | ✅ |
| Scoring engine ZIL | ✅ |
| Pipeline de enriquecimento (Planalto + LLM) | ✅ |
| Agendamento Celery (6 tarefas) | ✅ |
| Frontend — 8 páginas | ✅ |
| 151 testes automatizados | ✅ |
| CI (GitHub Actions, 4 jobs) | ✅ |
| Deploy em produção | backlog |

### Dados editoriais

Este é o gargalo real do projeto. O motor está construído, mas o Score ZIL só
considera votações que passaram por curadoria humana — e a curadoria ainda é fina:

| Insumo | Volume atual |
|--------|--------------|
| Categorias ZIL com keywords | 9 |
| Votações com `direcao_esperada` definida | 7 |
| Indicadores da Bússola | 4 |

Ampliar a curadoria em `data/direcoes/` é o que separa "o sistema funciona" de
"o ranking é confiável o suficiente para ser publicado".

### Páginas

`/` (manifesto) · `/ranking` · `/parlamentar/[id]` · `/proposicoes` ·
`/proposicoes/[id]` · `/votacoes/[id]` · `/bussula` · `/metodologia`

## Quick Start (desenvolvimento)

```bash
# Pré-requisitos: Python 3.12 e Node.js 20.
# Redis só é necessário para os workers Celery; Docker, para o ambiente completo.
# Os testes rodam sem nenhum dos dois.

git clone https://github.com/melissa-pereira-deel/manifesto-zil.git
cd manifesto-zil

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

**Limitações conhecidas do setup:** `make migrate` e `make seed` não funcionam a
partir de um clone limpo — o diretório de migrations do Alembic nunca foi
commitado e `scripts/seed.py` não existe. Isso não bloqueia desenvolvimento, mas
bloqueia produção, onde o Alembic é o caminho previsto. `make test` também não
funciona: o container da API monta apenas `apps/api`, e `tests/` fica na raiz —
rode os testes a partir do host.

## Fontes de Dados

| Fonte | Dados | Status |
|-------|-------|--------|
| [Câmara dos Deputados](https://dadosabertos.camara.leg.br) | Deputados, votações, proposições | ✅ |
| [Senado Federal](https://legis.senado.leg.br/dadosabertos) | Senadores, matérias, votações | ✅ |
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

O objetivo da v1 é entregar a ferramenta de observabilidade pública antes das eleições de outubro de 2026.

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
- **Direção esperada de votações**: `data/direcoes/[ano].yml` (PR + 2 aprovações + discussão no Discord)
- **Indicadores Bússola**: `data/bussula/marcos.yml` (PR + link para fonte oficial)
- **Aplicar ao banco**: `python scripts/apply_direcoes.py`

Princípio: na dúvida sobre a direção esperada de uma votação, não classificar.

## Como Contribuir

1. Leia a [constituição do projeto](.specify/memory/constitution.md) — princípios e valores
2. Abra uma issue ou entre no Discord antes de trabalhar em algo
3. Fork → branch → PR (com testes para código de backend)
4. Dados editoriais (`data/`) requerem 2 aprovações de maintainers

**Não precisa saber programar**: curadoria de classificações de proposições, verificação de indicadores da Bússola e documentação são igualmente importantes.

## Licença

Código: [AGPL-3.0](LICENSE)

Dados e conteúdo editorial: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

---

*O Brasil é de todos. A soberania também.*

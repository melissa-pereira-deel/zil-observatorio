# ZIL Observatório

**Plataforma pública de monitoramento do Congresso Nacional na pauta da soberania industrial brasileira.**

O Brasil tem 94% do nióbio mundial e importa 87% dos fertilizantes. Exporta petróleo cru e importa gasolina. Vende soja a granel e compra ração processada. O ZIL Observatório torna visível quem no Congresso está trabalhando para mudar isso — e quem está trabalhando contra.

[Manifesto](docs/MANIFESTO.md) · [PRD](docs/PRD.md) · [Arquitetura](docs/ARCHITECTURE.md) · [Roadmap](docs/ROADMAP.md)

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

**v0 concluído · v1 em andamento**

| Feature | Status |
|---------|--------|
| Modelos de dados (SQLAlchemy 2.0) | ✅ |
| API FastAPI com endpoints públicos | ✅ |
| Crawler Câmara dos Deputados | ✅ |
| Scoring engine ZIL | ✅ |
| Agendamento Celery | ✅ |
| 98 testes automatizados | ✅ |
| Ingestão Senado Federal | backlog |
| Frontend /ranking com dados reais | backlog |
| Frontend /parlamentar/[id] | backlog |
| Frontend /proposicoes | backlog |

## Quick Start (desenvolvimento)

```bash
# Pré-requisitos: Python 3.12, Node.js 20, Redis

git clone https://github.com/melissa-pereira-deel/manifesto-zil.git
cd manifesto-zil

# Backend — instalar dependências
pip install -r apps/api/requirements.txt

# Rodar testes (SQLite in-memory, sem Docker)
python -m pytest tests/

# API local
uvicorn apps.api.main:app --reload
# → http://localhost:8000/docs

# Frontend
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

Para ambiente completo com PostgreSQL e Redis:

```bash
docker-compose up
```

## Fontes de Dados

| Fonte | Dados | Status |
|-------|-------|--------|
| [Câmara dos Deputados](https://dadosabertos.camara.leg.br) | Deputados, votações, proposições | ✅ |
| [Senado Federal](https://legis.senado.leg.br/dadosabertos) | Senadores, matérias, votações | backlog |

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0 |
| Workers | Celery 5, Redis 7 |
| Frontend | Next.js 14, TypeScript 5, Tailwind CSS |
| Banco (dev/testes) | SQLite in-memory |
| Banco (produção) | PostgreSQL 16 |
| Testes | pytest 8 (98 testes) |

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

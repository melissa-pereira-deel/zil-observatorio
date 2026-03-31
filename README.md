# ZIL Observatório 🇧🇷

**Plataforma aberta de observability política para a soberania industrial do Brasil.**

O Brasil tem 94% do nióbio mundial e importa 87% dos fertilizantes. Exporta petróleo cru e importa gasolina. Vende soja a granel e compra ração processada. O ZIL Observatório torna visível quem no Congresso está trabalhando para mudar isso — e quem está trabalhando contra.

[Manifesto ZIL](docs/MANIFESTO.md) · [PRD Completo](docs/PRD.md) · [Arquitetura](docs/ARCHITECTURE.md) · [Como Contribuir](CONTRIBUTING.md)

---

## O que é

O ZIL Observatório monitora o posicionamento de cada deputado e senador brasileiro nas pautas que determinam a soberania industrial do país: fertilizantes, minerais estratégicos, semicondutores, energia, soberania digital, defesa e capital humano.

A plataforma:
- Calcula um **Score ZIL** para cada parlamentar baseado em como votou
- Mostra **quem financia** cada parlamentar e como isso se correlaciona com seus votos
- Alerta quando **proposições relevantes** avançam na tramitação
- Permite que cidadãos **cobrem seus representantes** com dados concretos

Todos os dados são públicos. Todo o código é aberto. Toda classificação é auditável.

## Status

🟡 **Em desenvolvimento ativo — Fase 0 (Setup)**

Estamos montando a infraestrutura base e os primeiros crawlers. Contribuidores são bem-vindos desde agora.

## Quick Start (desenvolvimento)

```bash
# Pré-requisitos: Docker, Docker Compose, Make

git clone https://github.com/zil-observatorio/zil-observatorio.git
cd zil-observatorio

# Subir ambiente completo (PostgreSQL + Redis + API + Frontend)
make setup

# Popular banco com dados iniciais
make seed

# Rodar testes
make test
```

Após o setup:
- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432` (user: `zil`, pass: `zil`, db: `zil`)

## Fontes de Dados

| Fonte | Dados | Atualização |
|-------|-------|-------------|
| [Câmara dos Deputados](https://dadosabertos.camara.leg.br) | Deputados, votações, proposições, despesas | Diária |
| [Senado Federal](https://legis.senado.leg.br/dadosabertos) | Senadores, matérias, votações | Diária |
| [TSE](https://dadosabertos.tse.jus.br) | Financiamento de campanha, candidatos | Por ciclo eleitoral |
| [Portal da Transparência](https://portaldatransparencia.gov.br) | Gastos federais | Diária |
| [Querido Diário](https://queridodiario.ok.org.br) | Diários oficiais municipais | Diária |

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14, React, Tailwind CSS |
| API | FastAPI (Python 3.12) |
| Banco | PostgreSQL 16 |
| Cache | Redis |
| Busca | Typesense |
| Workers | Celery |
| NLP | sentence-transformers, spaCy pt |
| Infra | Docker Compose |

## Como Contribuir

Leia o [guia de contribuição](CONTRIBUTING.md) completo. Resumo rápido:

1. Veja as [issues abertas](../../issues) — comece por `good-first-issue`
2. Fork → branch → PR (com testes)
3. Não precisa saber programar: curadoria de dados, design, documentação e análise são igualmente importantes

### Áreas que precisam de ajuda agora

- 🐍 **Backend**: crawlers para APIs da Câmara e Senado
- 🎨 **Frontend**: componentes do ranking e perfil de parlamentar
- 📊 **Dados**: classificação manual de proposições para treinar o classificador
- 📝 **Docs**: tradução, tutoriais, guias

## Roadmap

| Fase | Prazo | Status |
|------|-------|--------|
| Setup (infra, CI/CD, repo) | Abr 2026 | 🔄 Em andamento |
| Tracer Bullet (ranking + score básico) | Mai 2026 | ⬜ Pendente |
| Completude (Senado, NLP, TSE, PWA) | Jul 2026 | ⬜ Pendente |
| Inteligência (grafo, alertas, API) | Set 2026 | ⬜ Pendente |
| Comunidade (fórum, campanhas) | Nov 2026 | ⬜ Pendente |

**Marco crítico**: funcional antes de outubro de 2026 (eleições).

## Licença

Código: [AGPL-3.0](LICENSE)

Dados e conteúdo: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

## Comunidade

- [Discord](#) (em breve)
- [GitHub Discussions](../../discussions)
- Email: contato@zilobservatorio.org

---

*O Brasil é de todos. A soberania também.*

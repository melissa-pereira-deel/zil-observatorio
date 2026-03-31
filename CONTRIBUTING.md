# Guia de Contribuição — ZIL Observatório

Obrigado por considerar contribuir com o ZIL Observatório. Este projeto é construído pela comunidade, para a comunidade. Cada contribuição — código, dados, design, documentação ou análise — nos aproxima de um Brasil com mais soberania industrial.

## Sumário

- [Código de Conduta](#código-de-conduta)
- [Primeiros Passos](#primeiros-passos)
- [Tipos de Contribuição](#tipos-de-contribuição)
- [Workflow de Desenvolvimento](#workflow-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Padrões de Commit](#padrões-de-commit)
- [Pull Requests](#pull-requests)
- [Reportando Bugs](#reportando-bugs)
- [Propondo Features](#propondo-features)
- [Curadoria de Dados](#curadoria-de-dados)
- [Comunicação](#comunicação)

---

## Código de Conduta

Este projeto adota o [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). Ao participar, você concorda em manter um ambiente respeitoso, inclusivo e focado em dados e argumentos — nunca em ataques pessoais. Discussões sobre parlamentares devem ser sempre factuais e baseadas em dados públicos.

---

## Primeiros Passos

### Pré-requisitos

- Docker e Docker Compose
- Git
- Make (opcional, mas recomendado)
- Node.js 20+ (para desenvolvimento frontend sem Docker)
- Python 3.12+ (para desenvolvimento backend sem Docker)

### Setup do ambiente

```bash
# 1. Fork o repositório no GitHub

# 2. Clone seu fork
git clone https://github.com/SEU_USUARIO/zil-observatorio.git
cd zil-observatorio

# 3. Adicione o upstream
git remote add upstream https://github.com/zil-observatorio/zil-observatorio.git

# 4. Suba o ambiente
make setup
# Isso executa: docker compose up -d && make migrate && make seed

# 5. Verifique que tudo está rodando
make status
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
# DB: localhost:5432

# 6. Rode os testes
make test
```

### Sem Docker

```bash
# Backend
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd apps/web
npm install
npm run dev
```

---

## Tipos de Contribuição

Não é preciso saber programar para contribuir. Aqui estão as formas de participar:

### 🐍 Código Backend
- Crawlers para APIs da Câmara e Senado
- Endpoints da API
- Pipeline de ingestão e transformação de dados
- Engine de scoring
- **Labels**: `backend`, `data-pipeline`, `scoring`

### ⚛️ Código Frontend
- Componentes React (ranking, perfil, busca)
- Páginas e navegação
- Responsividade e acessibilidade
- Cards compartilháveis para redes sociais
- **Labels**: `frontend`, `design`

### 🧠 NLP e Machine Learning
- Classificador de proposições por pauta ZIL
- Embeddings semânticos para busca
- Fine-tuning de modelos para português legislativo
- **Labels**: `nlp`, `ml`

### 📊 Curadoria de Dados
- Classificar manualmente proposições por pauta ZIL (treina o classificador)
- Validar classificações automáticas
- Definir "direção esperada" de votações com justificativa
- **Labels**: `curadoria`, `data`

### 🎨 Design
- UI/UX da plataforma
- Identidade visual (paleta verde/ouro, tipografia Archivo)
- Cards e materiais para redes sociais
- **Labels**: `design`

### 📝 Documentação
- Tutoriais e guias
- Documentação de API
- Tradução (pt-BR ↔ en)
- **Labels**: `docs`

### 🔍 Análise e Jornalismo de Dados
- Reportagens e insights a partir dos dados
- Identificação de padrões de votação
- Contexto histórico para classificações
- **Labels**: `analise`

### 🧪 Testes
- Testes unitários e de integração
- Testes E2E
- Testes de carga
- **Labels**: `testing`

---

## Workflow de Desenvolvimento

### 1. Escolha uma issue

- Comece por issues com label `good-first-issue`
- Issues `help-wanted` são prioridade do projeto
- Comente na issue dizendo que vai trabalhar nela

### 2. Crie um branch

```bash
# Atualize seu fork
git checkout main
git pull upstream main

# Crie branch descritivo
git checkout -b feat/ranking-deputados
# ou
git checkout -b fix/crawler-timeout
```

Convenção de nomes:
- `feat/nome-descritivo` — nova funcionalidade
- `fix/nome-descritivo` — correção de bug
- `docs/nome-descritivo` — documentação
- `refactor/nome-descritivo` — refatoração
- `data/nome-descritivo` — dados ou curadoria

### 3. Desenvolva

- Escreva testes para código novo
- Atualize documentação se necessário
- Rode `make lint` e `make test` antes de commitar

### 4. Abra um Pull Request

- Preencha o template do PR
- Referencie a issue: `Closes #123`
- Adicione screenshots se houver mudança visual
- Aguarde review de pelo menos 1 maintainer

---

## Padrões de Código

### Python (Backend)

```bash
# Formatação
black .
ruff check . --fix

# Type checking
mypy apps/api --strict
```

- Tipagem obrigatória em todas as funções
- Docstrings em funções públicas
- Máximo 88 caracteres por linha (black default)
- Imports organizados: stdlib → third-party → local

### TypeScript (Frontend)

```bash
# Lint + format
npm run lint
npm run format
```

- Strict mode habilitado
- Componentes funcionais com hooks
- Props tipadas com interfaces (não `any`)
- Tailwind para estilos (sem CSS custom salvo exceções justificadas)

### SQL

- Migrations via Alembic (nunca SQL manual em produção)
- Nomes de tabela em snake_case plural (`parlamentares`, `votacoes`)
- Nomes de coluna em snake_case
- Índices explícitos para colunas filtradas frequentemente

---

## Padrões de Commit

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>(<escopo>): <descrição curta>

<corpo opcional>

<footer opcional>
```

Tipos:
- `feat`: nova funcionalidade
- `fix`: correção de bug
- `docs`: documentação
- `style`: formatação (sem mudança de lógica)
- `refactor`: refatoração (sem mudança de comportamento)
- `test`: adição ou correção de testes
- `chore`: manutenção, dependências, CI

Exemplos:
```
feat(crawler): implementar ingestão de votações da Câmara
fix(scoring): corrigir cálculo quando parlamentar ausente
docs(api): documentar endpoint /parlamentares
data(taxonomia): adicionar keywords para ZIL-SEM
```

---

## Pull Requests

### Template

Todo PR deve incluir:

```markdown
## Descrição
O que esse PR faz e por quê.

## Issue relacionada
Closes #(número)

## Tipo de mudança
- [ ] Bug fix
- [ ] Nova feature
- [ ] Refatoração
- [ ] Documentação
- [ ] Dados/curadoria

## Checklist
- [ ] Testes adicionados/atualizados
- [ ] Documentação atualizada
- [ ] `make lint` passa sem erros
- [ ] `make test` passa sem erros
- [ ] Screenshots (se mudança visual)
```

### Processo de review

- PRs precisam de aprovação de pelo menos 1 maintainer
- Reviews devem ser construtivos e específicos
- Merge via squash (um commit limpo por PR)
- O autor do PR é responsável por resolver conflitos

---

## Reportando Bugs

Use o template de issue para bugs:

```markdown
## Descrição do bug
Descrição clara e concisa.

## Como reproduzir
1. Vá para '...'
2. Clique em '...'
3. Veja o erro

## Comportamento esperado
O que deveria acontecer.

## Screenshots
Se aplicável.

## Ambiente
- OS: [ex: Ubuntu 24.04]
- Browser: [ex: Firefox 125]
- Versão da plataforma: [ex: v0.1.0]
```

---

## Propondo Features

Para features maiores, abra uma Discussion antes de uma issue:

1. Descreva o problema que a feature resolve
2. Explique a solução proposta
3. Liste alternativas consideradas
4. Discuta com a comunidade
5. Se aprovada, um maintainer cria a issue correspondente

Para features menores, abra diretamente uma issue com o template de feature request.

---

## Curadoria de Dados

A curadoria é uma das contribuições mais importantes e não requer conhecimento técnico.

### O que é

Classificar proposições do Congresso nas pautas ZIL e definir a "direção esperada" para votações.

### Como funciona

1. Acesse a lista de proposições pendentes de classificação na plataforma
2. Leia a ementa e, se necessário, o inteiro teor
3. Classifique em uma ou mais categorias ZIL (ZIL-FER, ZIL-MIN etc.)
4. Para votações, defina se o voto "sim" seria a favor ou contra a soberania industrial, com justificativa
5. Sua classificação entra como proposta e é revisada pelo comitê editorial

### Princípios de curadoria

- **Na dúvida, não classificar.** É melhor ter menos dados do que dados errados.
- **Justifique sempre.** "Essa proposição beneficia a soberania porque..." — sem justificativa, não há classificação.
- **Separar fato de opinião.** "O PL facilita exportação de nióbio bruto" é fato. "O PL é ruim" é opinião. Só o primeiro serve para classificação.
- **Declarar conflito de interesse.** Se você trabalha em setor afetado pela proposição, declare.

---

## Comunicação

- **Issues e PRs**: discussões técnicas e decisões que precisam de registro
- **GitHub Discussions**: ideias, perguntas, RFCs, apresentações
- **Discord/Telegram**: comunicação em tempo real, pareamento, dúvidas rápidas
- **Weekly sync**: reunião aberta semanal (dia/hora definidos pela comunidade), gravada e publicada

### Idioma

- **Código**: inglês (variáveis, funções, comentários)
- **Dados**: português (nomes de parlamentares, ementas, categorias)
- **Documentação**: português (README, PRD, guias) com tradução para inglês quando possível
- **Issues/PRs**: português ou inglês
- **Comunicação**: português (principal), inglês (bienvenido)

---

## Reconhecimento

Todo contribuidor com PR mergeado ou contribuição reconhecida (curadoria, design, análise) é adicionado ao arquivo CONTRIBUTORS.md e ao README.

Contribuidores ativos nos últimos 6 meses têm direito a voto em decisões comunitárias.

---

*Dúvidas? Abra uma [Discussion](../../discussions) ou mande email para contato@zilobservatorio.org.*

*Obrigado por ajudar a construir soberania. 🇧🇷*

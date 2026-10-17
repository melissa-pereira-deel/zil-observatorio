# Guia de Contribuição — ZIL Observatório

Obrigado por considerar contribuir com o ZIL Observatório.

**Antes de tudo, o estado real do projeto**, porque você merece saber onde está
entrando: hoje há **uma pessoa** mantendo isto. Não há comunidade formada, não
há comitê editorial constituído e não há agenda de reuniões. O que existe é o
repositório, o código funcionando e a disposição de construir o resto com quem
aparecer.

Cada contribuição — código, dados, design, documentação ou análise — nos
aproxima de um Brasil com mais soberania industrial. E as primeiras
contribuições têm um peso extra: são elas que transformam "um projeto" em "um
projeto com gente".

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
# Backend — o venv é gerenciado pelo uv, e ele não instala `pip` dentro
# do ambiente. `pip install` falha com "no such file or directory".
uv venv
uv pip install -r apps/api/requirements.txt

# A API roda de dentro de apps/api por causa dos imports curtos (ADR-002)
cd apps/api
../../.venv/bin/uvicorn main:app --reload

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

Para features maiores, abra uma issue de proposta antes de começar a
implementar (Discussions está desabilitado):

1. Descreva o problema que a feature resolve
2. Explique a solução proposta
3. Liste alternativas consideradas
4. Aguarde resposta antes de investir tempo — hoje quem responde é a
   maintainer, então pode não ser imediato

Para features menores, abra diretamente uma issue com o template de feature request.

---

## Curadoria de Dados

A curadoria é uma das contribuições mais importantes e não requer conhecimento técnico.

### O que é

Classificar proposições do Congresso nas pautas ZIL e definir a "direção esperada" para votações.

### Como funciona

Não existe interface de curadoria na plataforma — toda a gestão editorial é
feita via arquivos YAML no repositório. O fluxo hoje é:

1. Escolha uma votação relevante (a API de Dados Abertos da Câmara é a fonte)
2. Leia a ementa e, se necessário, o inteiro teor
3. Classifique em uma ou mais categorias ZIL (ZIL-FER, ZIL-MIN etc.)
4. Para votações, defina se o voto "sim" seria a favor ou contra a soberania
   industrial — **com justificativa escrita**, que é obrigatória
5. Abra um PR em `data/direcoes/[ano].yml` seguindo o formato do arquivo

A revisão é feita pela maintainer. Não há comitê editorial: ele está previsto na
governança para quando houver gente suficiente, e ainda não foi constituído.

**O que o projeto mais precisa hoje:** o Score ZIL se apoia em 7 classificações,
todas marcadas `validacao: nao-validado`. Revisar essas 7, ou propor novas com
pesquisa densa, é a contribuição de maior impacto que existe no momento — mais
do que qualquer código. Ver [ADR-004](docs/decisions/004-placar-focado.md).

### Princípios de curadoria

- **Na dúvida, não classificar.** É melhor ter menos dados do que dados errados.
- **Justifique sempre.** "Essa proposição beneficia a soberania porque..." — sem justificativa, não há classificação.
- **Separar fato de opinião.** "O PL facilita exportação de nióbio bruto" é fato. "O PL é ruim" é opinião. Só o primeiro serve para classificação.
- **Declarar conflito de interesse.** Se você trabalha em setor afetado pela proposição, declare.

---

## Comunicação

**Hoje, o canal é um só: as issues do GitHub.** Elas funcionam, são
rastreáveis e deixam registro — o que combina com um projeto cujo ativo é ser
auditável.

| Canal | Situação |
|---|---|
| **GitHub Issues e PRs** | **Ativo.** Discussões técnicas, propostas de classificação, dúvidas |
| **Discord** | **Será criado.** Vai ser o canal de tempo real; o convite é publicado aqui assim que existir |
| GitHub Discussions | Desabilitado no repositório por ora |

### Reuniões

**Ainda não há agenda de reuniões**, e não faria sentido ter: reunião com uma
pessoa é uma pessoa pensando em voz alta.

Quando houver um grupo de contribuidores ativos, formato e periodicidade serão
definidos **em conjunto com quem estiver participando** — não decididos
antecipadamente e anunciados como se já acontecessem. Versões anteriores deste
guia prometiam uma "reunião aberta semanal, gravada e publicada" que nunca
existiu; a promessa foi removida em 2026-09-18.

### Idioma

- **Código**: inglês (variáveis, funções, comentários)
- **Dados**: português (nomes de parlamentares, ementas, categorias)
- **Documentação**: português (README, PRD, guias) com tradução para inglês quando possível
- **Issues/PRs**: português ou inglês
- **Comunicação**: português (principal), inglês (bienvenido)

---

## Reconhecimento

Todo contribuidor com PR mergeado ou contribuição reconhecida (curadoria,
design, análise) entra no `CONTRIBUTORS.md` — arquivo que será criado com a
primeira contribuição externa, porque criá-lo vazio seria estranho.

**Sobre voto em decisões:** não há mecanismo de votação hoje, e prometê-lo sem
tê-lo seria mais uma regra de papel. O que a governança já registra é a
condição de saída: quando houver contribuidores ativos o bastante para formar
quórum, **as diretrizes e regras do projeto passam a ser revistas em conjunto**
— inclusive a forma de decidir. Ver
[docs/GOVERNANCE.md](docs/GOVERNANCE.md), "Condições para a norma voltar a ser
cumprida".

---

*Dúvidas? Abra uma [issue](../../issues). É o canal que funciona hoje, e
todas as respostas ficam registradas para quem chegar depois.*

*Obrigado por ajudar a construir soberania. 🇧🇷*

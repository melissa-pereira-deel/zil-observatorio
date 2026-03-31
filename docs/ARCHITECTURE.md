# ZIL Observatório — Arquitetura da Plataforma de Observability Política

## 1. DEFINIÇÃO DO PROBLEMA

O Brasil possui dados legislativos abertos de alta qualidade, mas falta infraestrutura para transformar esses dados em pressão política organizada. Os cidadãos não têm ferramentas para responder a três perguntas fundamentais:

1. **Como meu representante votou** em pautas que afetam a soberania industrial do Brasil?
2. **Quem financia esse representante** e como isso se correlaciona com suas posições?
3. **Que proposições estão tramitando agora** que podem fortalecer ou enfraquecer nossos interesses nacionais?

O Observatório ZIL existe para responder essas perguntas em tempo real, com dados verificáveis, e converter informação em ação coletiva.

---

## 2. MAPEAMENTO DE FONTES DE DADOS

### 2.1 Fontes Primárias (APIs oficiais, atualização diária)

**Câmara dos Deputados — API REST**
- URL base: `https://dadosabertos.camara.leg.br/api/v2`
- Formatos: JSON, XML, CSV, XLSX
- Endpoints principais:
  - `/deputados` — perfil, partido, estado, mandatos
  - `/deputados/{id}/votacoes` — como cada deputado votou
  - `/votacoes` — todas as votações por ano, com placar
  - `/votacoes/{id}/votos` — voto individual de cada deputado
  - `/proposicoes` — projetos de lei, PECs, requerimentos
  - `/proposicoes/{id}/tramitacoes` — histórico de tramitação
  - `/proposicoes/{id}/autores` — quem propôs
  - `/orgaos` — comissões e seus membros
  - `/frentes` — frentes parlamentares (bancada ruralista, evangélica etc.)
  - `/deputados/{id}/despesas` — gastos com cota parlamentar
- Atualização: diária
- Rate limit: sem autenticação, limite implícito (~120 req/min)
- Documentação: `https://dadosabertos.camara.leg.br/swagger/api.html`

**Senado Federal — API REST/SOAP**
- URL base: `https://legis.senado.leg.br/dadosabertos`
- Endpoints principais:
  - `/senador/lista/atual` — senadores em exercício
  - `/senador/{codigo}/votacoes` — votos individuais
  - `/materia/pesquisa/lista` — matérias em tramitação
  - `/materia/{codigo}/votacoes` — resultado de votações
  - `/plenario/lista/votacao/{ano}` — votações plenárias por ano
  - `/comissao/lista` — comissões e composição
- Formatos: XML (principal), JSON (parcial)
- Documentação Swagger: `https://legis.senado.leg.br/dadosabertos/api-docs/swagger-ui/index.html`

**TSE — Portal de Dados Abertos**
- URL: `https://dadosabertos.tse.jus.br`
- Datasets principais:
  - Candidatos (perfil, bens, redes sociais, proposta de governo)
  - Prestação de contas eleitorais (receitas e despesas de campanha)
  - Resultados eleitorais (votos por seção, zona, município)
  - Filiação partidária
  - CNPJ de campanha e extratos bancários
- Formato: CSV bulk download (arquivos grandes, necessitam processamento)
- Atualização: por ciclo eleitoral + prestação de contas contínua
- API complementar: CEPESP-FGV (`https://github.com/Cepesp-Fgv/cepesp-rest`)

### 2.2 Fontes Complementares

**Portal da Transparência (CGU)**
- URL: `https://portaldatransferencia.gov.br/api-de-dados`
- Dados: gastos federais, convênios, viagens, cartões corporativos
- Formato: API REST JSON

**Diários Oficiais — Projeto Querido Diário**
- URL: `https://queridodiario.ok.org.br`
- Projeto open source da Open Knowledge Brasil
- Coleta e indexa diários oficiais de 2.800+ municípios
- API: `https://queridodiario.ok.org.br/api`
- Utilidade: capturar decretos, nomeações, contratos que não aparecem nas APIs legislativas

**Receita Federal — QSA (Quadro Societário)**
- Dados: CNPJ, sócios, atividade econômica
- Permite cruzar: doadores de campanha ↔ empresas beneficiadas por legislação
- Disponível via datasets processados (ex: Brasil.IO)

**News/Mídia — Web Scraping + APIs**
- Google News RSS por parlamentar/pauta
- APIs de veículos (Folha, Estadão — parcial)
- Twitter/X API (perfis de parlamentares)
- YouTube Data API (discursos em plenário)

### 2.3 Dados Derivados (gerados pela plataforma)

- **Índice de Alinhamento ZIL**: score calculado por parlamentar baseado em como votou em pautas de soberania industrial
- **Grafo de Influência**: rede parlamentar ↔ doador ↔ setor econômico ↔ frente parlamentar
- **Timeline de Posicionamento**: evolução do alinhamento de cada parlamentar ao longo do tempo
- **Alertas de Proposição**: novas proposições que tocam pautas ZIL

---

## 3. TAXONOMIA DE PAUTAS ZIL

Para classificar automaticamente proposições e votações, definimos categorias temáticas vinculadas ao manifesto:

| Código | Pauta | Palavras-chave para classificação |
|--------|-------|----------------------------------|
| ZIL-FER | Fertilizantes | fertilizante, potássio, fosfato, nitrogênio, NPK, Embrapa, PNF |
| ZIL-MIN | Minerais Estratégicos | nióbio, terras raras, lítio, grafite, mineral crítico, CBMM |
| ZIL-SEM | Semicondutores | semicondutor, chip, microeletrônica, Padis, Brasil Semicon |
| ZIL-ENE | Energia/Transição | pré-sal, hidrogênio verde, bateria, Petrobras, etanol, renovável |
| ZIL-DIG | Soberania Digital | Starlink, dados pessoais, LGPD, satélite, fibra óptica, 5G |
| ZIL-DEF | Defesa/Institucional | Embraer, defesa cibernética, CFIUS, ativo estratégico, privatização |
| ZIL-EDU | Capital Humano | engenharia, STEM, ITA, Ceitec, repatriação, formação técnica |
| ZIL-AGR | Agro-Indústria | agro processamento, valor agregado, exportação commodity |
| ZIL-COM | Comércio/Tarifas | tarifa, OMC, Mercosul, acordo bilateral, BRICS, proteção comercial |

A classificação usa: matching de palavras-chave (baseline), embeddings semânticos via modelo multilíngue (melhoria), e curadoria humana para calibração.

---

## 4. ARQUITETURA TÉCNICA

### 4.1 Visão Geral

```
┌─────────────────────────────────────────────────────────┐
│                    USUÁRIOS                             │
│  Web App (React)  ·  Mobile (PWA)  ·  API Pública      │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                 API GATEWAY (FastAPI)                    │
│  Auth · Rate Limit · Cache · GraphQL opcional           │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              CAMADA DE SERVIÇOS                         │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Scoring  │  │ Alertas  │  │ Grafo de │  │ Search │ │
│  │ Engine   │  │ Engine   │  │ Influência│  │ Engine │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Classific.│  │ Comunidade│  │ Mobiliz. │             │
│  │ NLP      │  │ & Fórum  │  │ Engine   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              CAMADA DE DADOS                            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │PostgreSQL│  │ Redis    │  │ Typesense│             │
│  │(principal)│  │ (cache)  │  │(busca FT)│             │
│  └──────────┘  └──────────┘  └──────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│           CAMADA DE INGESTÃO (workers)                  │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Câmara   │  │ Senado   │  │  TSE     │  │ News   │ │
│  │ Crawler  │  │ Crawler  │  │ Importer │  │Scraper │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│                                                         │
│  ┌──────────┐  ┌──────────┐                            │
│  │ Querido  │  │ Portal   │                            │
│  │ Diário   │  │Transparên│                            │
│  └──────────┘  └──────────┘                            │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Stack Tecnológico

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Frontend | Next.js + React | SSR para SEO, compartilhamento social. PWA para mobile. |
| Design System | Tailwind + componentes ZIL | Consistência visual com o manifesto |
| API | FastAPI (Python) | Async nativo, tipagem, OpenAPI auto-doc |
| Banco principal | PostgreSQL 16 | JSON columns para dados semi-estruturados, full-text search nativo |
| Cache | Redis | Cache de API, rate limiting, filas de jobs |
| Busca | Typesense | Full-text search open source, faceted search, typo tolerance |
| Jobs/Workers | Celery + Redis | Ingestão assíncrona, scheduling de crawlers |
| NLP | sentence-transformers + spaCy pt | Classificação de proposições, embeddings para busca semântica |
| Auth | NextAuth.js | OAuth (Google, GitHub), magic link, sem login obrigatório para leitura |
| Infra | Docker Compose → k8s | Dev local simples, produção escalável |
| Monitoramento | Sentry + Prometheus + Grafana | Erros, métricas, alertas |

### 4.3 Modelo de Dados (PostgreSQL)

```sql
-- Parlamentares (deputados + senadores unificados)
CREATE TABLE parlamentares (
    id UUID PRIMARY KEY,
    fonte_id VARCHAR NOT NULL,         -- ID na API de origem
    fonte ENUM('camara','senado'),
    nome VARCHAR NOT NULL,
    nome_civil VARCHAR,
    partido VARCHAR,
    uf CHAR(2),
    foto_url VARCHAR,
    email VARCHAR,
    redes_sociais JSONB,
    mandato_inicio DATE,
    mandato_fim DATE,
    frentes_parlamentares JSONB,       -- array de frentes
    score_zil DECIMAL(4,2),            -- -10.0 a +10.0
    score_atualizado_em TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Proposições (PLs, PECs, requerimentos etc.)
CREATE TABLE proposicoes (
    id UUID PRIMARY KEY,
    fonte_id VARCHAR NOT NULL,
    fonte ENUM('camara','senado'),
    tipo VARCHAR,                      -- PL, PEC, PLP, REQ...
    numero INTEGER,
    ano INTEGER,
    ementa TEXT,
    ementa_detalhada TEXT,
    autor_principal_id UUID REFERENCES parlamentares,
    autores JSONB,
    situacao VARCHAR,
    data_apresentacao DATE,
    ultimo_despacho TEXT,
    categorias_zil VARCHAR[],          -- ex: {'ZIL-FER','ZIL-MIN'}
    relevancia_zil DECIMAL(3,2),       -- 0.0 a 1.0
    classificacao_automatica BOOLEAN DEFAULT TRUE,
    url_inteiro_teor VARCHAR,
    tramitacoes JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Votações
CREATE TABLE votacoes (
    id UUID PRIMARY KEY,
    fonte_id VARCHAR NOT NULL,
    fonte ENUM('camara','senado'),
    proposicao_id UUID REFERENCES proposicoes,
    data TIMESTAMP,
    descricao TEXT,
    resultado VARCHAR,                  -- aprovado, rejeitado, retirado
    votos_sim INTEGER,
    votos_nao INTEGER,
    abstencoes INTEGER,
    categorias_zil VARCHAR[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Votos Individuais
CREATE TABLE votos (
    id UUID PRIMARY KEY,
    votacao_id UUID REFERENCES votacoes NOT NULL,
    parlamentar_id UUID REFERENCES parlamentares NOT NULL,
    voto VARCHAR NOT NULL,             -- sim, nao, abstencao, ausente, obstrucao
    orientacao_partido VARCHAR,         -- sim, nao, liberado
    orientacao_governo VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(votacao_id, parlamentar_id)
);

-- Financiamento (TSE)
CREATE TABLE financiamentos (
    id UUID PRIMARY KEY,
    parlamentar_id UUID REFERENCES parlamentares,
    eleicao_ano INTEGER,
    tipo ENUM('receita','despesa'),
    doador_nome VARCHAR,
    doador_cnpj_cpf VARCHAR,
    doador_setor VARCHAR,              -- classificação CNAE
    valor DECIMAL(14,2),
    data DATE,
    descricao TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Score ZIL por votação (granular)
CREATE TABLE scores_votacao (
    id UUID PRIMARY KEY,
    parlamentar_id UUID REFERENCES parlamentares NOT NULL,
    votacao_id UUID REFERENCES votacoes NOT NULL,
    categoria_zil VARCHAR NOT NULL,
    impacto DECIMAL(3,2),              -- -1.0 (contra) a +1.0 (favor)
    peso DECIMAL(3,2) DEFAULT 1.0,     -- importância da votação
    justificativa TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Comunidade
CREATE TABLE discussoes (
    id UUID PRIMARY KEY,
    autor_id UUID NOT NULL,
    titulo VARCHAR NOT NULL,
    corpo TEXT NOT NULL,
    categoria_zil VARCHAR,
    proposicao_id UUID REFERENCES proposicoes,
    parlamentar_id UUID REFERENCES parlamentares,
    votos_cima INTEGER DEFAULT 0,
    votos_baixo INTEGER DEFAULT 0,
    respostas_count INTEGER DEFAULT 0,
    pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alertas configurados por usuário
CREATE TABLE alertas_usuario (
    id UUID PRIMARY KEY,
    usuario_id UUID NOT NULL,
    tipo ENUM('proposicao_nova','votacao','tramitacao','score_mudou'),
    filtros JSONB,                     -- categorias, parlamentares, estados
    canal ENUM('email','push','telegram'),
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 5. SCORING ENGINE — ÍNDICE DE ALINHAMENTO ZIL

### 5.1 Metodologia

Cada votação relacionada a uma pauta ZIL recebe:
- **Classificação temática** (ZIL-FER, ZIL-MIN etc.)
- **Direção esperada** (o que o manifesto ZIL defenderia: sim ou não)
- **Peso** (importância relativa: votação final em plenário > votação em comissão > requerimento)

O score de um parlamentar é calculado como:

```
Score_ZIL = Σ (voto_alinhado × peso) / Σ peso × 10
```

Onde `voto_alinhado` = +1 se votou na direção ZIL, -1 se votou contra, 0 se ausente.

O score varia de -10.0 (sempre contra) a +10.0 (sempre a favor).

### 5.2 Curadoria da "Direção Esperada"

Este é o ponto crítico — quem decide o que é "a favor" ou "contra" a soberania industrial?

Modelo proposto (três camadas):
1. **Automática**: classificação por NLP + regras. Baseline inicial.
2. **Comitê editorial**: grupo de especialistas (economistas, engenheiros, diplomatas) valida classificações. Transparência total — as justificativas são públicas.
3. **Comunidade**: usuários podem propor reclassificações, que passam pelo comitê.

Toda classificação é auditável: o usuário vê por que uma votação foi marcada como "pró-soberania" ou "contra", e pode discordar publicamente.

---

## 6. FUNCIONALIDADES DO MVP (v0.1)

### Fase 1 — Fundação (meses 1-3)

- Ingestão automatizada de dados da Câmara e Senado (deputados, votações, proposições)
- Classificação automática de proposições por pauta ZIL
- Perfil de parlamentar com histórico de votos em pautas ZIL
- Score ZIL por parlamentar com ranking
- Busca por proposição, parlamentar, tema
- Página do manifesto integrada com assinatura

### Fase 2 — Inteligência (meses 3-6)

- Ingestão de dados TSE (financiamento de campanha)
- Grafo de influência: parlamentar ↔ doador ↔ setor ↔ frente
- Alertas em tempo real (nova proposição, votação iminente, mudança de score)
- Comparativo entre parlamentares por estado/partido
- API pública para jornalistas e pesquisadores

### Fase 3 — Comunidade (meses 6-9)

- Fórum de discussão por pauta/proposição/parlamentar
- Sistema de votação comunitária em proposições
- Campanhas de pressão (templates de email/mensagem para parlamentar)
- Integração com redes sociais (compartilhamento de cards com score)
- Dashboard agregado: como cada estado/partido se posiciona

### Fase 4 — Mobilização (meses 9-12)

- Eventos e mobilizações organizadas pela plataforma
- Acompanhamento de compromissos de campanha vs. votos reais
- Integração com dados municipais/estaduais
- App mobile nativo (ou PWA avançado)
- Gamificação: badges para cidadãos ativos

---

## 7. INGESTÃO DE DADOS — PIPELINE

```python
# Pseudocódigo do worker de ingestão da Câmara

# Executado diariamente via Celery Beat
@celery.task
def sync_camara_votacoes():
    ano = datetime.now().year
    
    # 1. Buscar votações do ano
    votacoes = camara_api.get(f"/votacoes?ano={ano}&ordem=DESC")
    
    for v in votacoes:
        # 2. Verificar se já existe
        if db.votacoes.exists(fonte_id=v['id']):
            continue
        
        # 3. Classificar por pauta ZIL
        categorias = classificador.classificar(
            texto=v['descricao'],
            proposicao=v.get('proposicao')
        )
        
        # 4. Salvar votação
        votacao = db.votacoes.create(
            fonte_id=v['id'],
            fonte='camara',
            data=v['data'],
            descricao=v['descricao'],
            categorias_zil=categorias
        )
        
        # 5. Buscar votos individuais
        votos = camara_api.get(f"/votacoes/{v['id']}/votos")
        
        for voto in votos:
            db.votos.create(
                votacao_id=votacao.id,
                parlamentar_id=resolve_parlamentar(voto['deputado']),
                voto=normalizar_voto(voto['tipoVoto']),
                orientacao_partido=voto.get('orientacaoPartido')
            )
        
        # 6. Recalcular scores dos parlamentares afetados
        if categorias:  # só se é pauta ZIL
            recalcular_scores(votacao)
```

Schedule de ingestão:
- Câmara/Senado: a cada 6 horas (votações), diário (proposições, deputados)
- TSE: semanal (durante período eleitoral: diário)
- News: a cada 2 horas
- Querido Diário: diário

---

## 8. DECISÕES DE PROJETO OPEN SOURCE

### Licença: AGPL-3.0
Garante que forks e modificações permaneçam open source. Se alguém usar o código para criar uma versão proprietária, deve abrir o código.

### Repositório: Monorepo
```
zil-observatorio/
├── apps/
│   ├── web/              # Next.js frontend
│   ├── api/              # FastAPI backend
│   └── workers/          # Celery workers de ingestão
├── packages/
│   ├── scoring/          # Engine de scoring (Python)
│   ├── classifier/       # NLP classifier (Python)
│   ├── camara-client/    # Client API Câmara
│   ├── senado-client/    # Client API Senado
│   └── tse-importer/     # Importador TSE
├── data/
│   ├── taxonomia/        # Definições de pautas ZIL (YAML)
│   ├── seeds/            # Dados iniciais
│   └── migrations/       # Migrations PostgreSQL
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   ├── DATA_SOURCES.md
│   └── SCORING.md
├── docker-compose.yml
├── Makefile
└── README.md
```

### Contribuição
- Issues temáticas: `good-first-issue`, `data-pipeline`, `scoring`, `frontend`, `nlp`
- PR reviews obrigatórias por 2 mantainers
- CI: testes + linting + type checking + build
- Releases semânticas (SemVer)

---

## 9. PRECEDENTES E LIÇÕES

### Operação Serenata de Amor (Brasil, 2016)
- Sucesso: identificou 8.000+ reembolsos suspeitos, cobertura em 90+ veículos de mídia
- Falha: perdeu momentum por dificuldade de financiamento sustentável e excesso de foco técnico vs. mobilização
- Lição para ZIL: **não ser apenas ferramenta técnica — ser plataforma de ação coletiva**

### Elas no Congresso (AzMina, 2019)
- Monitora PLs sobre gênero usando a mesma API da Câmara
- Código aberto no GitHub
- Lição: **demonstrou viabilidade de monitoramento temático automatizado com equipe pequena**

### Querido Diário (OKBR)
- Coleta diários oficiais de 2.800+ municípios
- Comunidade ativa, financiamento via doações
- Lição: **modelo de comunidade sustentável em civic tech no Brasil**

### GovTrack.us (EUA)
- Referência internacional: tracka todo o Congresso americano
- Score de ideologia, alertas, comparativos
- Lição: **interface simples + dados profundos = adoção massiva**

---

## 10. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|:---:|:---:|---------|
| APIs governamentais ficam instáveis/mudam | Alta | Alto | Cache agressivo, múltiplos parsers, fallback para bulk download |
| Acusação de viés político na classificação | Alta | Alto | Transparência total: toda classificação é auditável e contestável |
| Perda de momentum da comunidade | Média | Alto | Gamificação, releases frequentes, comunicação constante |
| Ataques DDoS ou tentativa de censura | Média | Médio | CDN, rate limiting, infraestrutura distribuída, mirrors |
| Dados inconsistentes entre fontes | Alta | Médio | Pipeline de reconciliação, IDs canônicos, auditoria cruzada |
| Custo de infraestrutura insustentável | Média | Médio | Começar em VPS simples, migrar conforme escala; doações + grants |

---

## 11. ROADMAP DE LANÇAMENTO

| Marco | Prazo | Entrega |
|-------|-------|---------|
| **Alpha** | M+6 semanas | Ingestão Câmara funcionando, perfis de deputados, score básico |
| **Beta fechado** | M+3 meses | Senado, classificação NLP, alertas, busca |
| **Beta aberto** | M+5 meses | TSE integrado, grafo de influência, fórum |
| **v1.0** | M+8 meses | API pública, mobilização, app mobile |
| **v1.5** | M+12 meses | Dados municipais/estaduais, gamificação |

Prioridade zero: **estar funcional antes de outubro de 2026** (eleições).

---

## 12. COMO COMEÇAR (PRIMEIROS 14 DIAS)

**Dia 1-3**: Setup do monorepo, Docker Compose com PostgreSQL + Redis, FastAPI hello world, Next.js scaffold.

**Dia 4-7**: Client da API da Câmara. Ingestão dos 513 deputados atuais com perfil completo. Worker que busca votações de 2025-2026 e salva no banco.

**Dia 8-10**: Classificador baseline (regex + keywords) para categorizar proposições/votações nas pautas ZIL. Score ZIL v0 calculado para todos os deputados.

**Dia 11-14**: Frontend mínimo: ranking de deputados por score ZIL, página de perfil com histórico de votos, página de busca. Deploy em VPS.

Esse é o "tracer bullet" — a versão mais simples que demonstra o conceito end-to-end e permite iterar.

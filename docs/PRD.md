# ZIL Observatório — PRD v1
### Plataforma aberta de observabilidade política para a soberania industrial do Brasil

> *"Um país que já venceu a hiperinflação, inventou o PIX, transformou cerrado em celeiro do mundo e construiu a terceira maior fabricante de aviões do planeta pode fazer qualquer coisa — se decidir."*

**Versão:** 1.0 (escopo v1)
**Última atualização:** 2026-04-02
**Roadmap completo:** [docs/ROADMAP.md](ROADMAP.md)

---

## Índice

1. [Visão](#1-visão)
2. [Contexto e Problema](#2-contexto-e-problema)
3. [Objetivos do Produto](#3-objetivos-do-produto)
4. [Público-Alvo](#4-público-alvo)
5. [Princípios de Design](#5-princípios-de-design)
6. [Escopo v1 — O que está incluído](#6-escopo-v1)
7. [Escopo v1 — O que NÃO está incluído](#7-fora-do-escopo-v1)
8. [Funcionalidades v1](#8-funcionalidades-v1)
9. [Taxonomia de Pautas ZIL](#9-taxonomia-de-pautas-zil)
10. [Score ZIL — Metodologia](#10-score-zil--metodologia)
11. [Bússola ZIL — Marcos Estratégicos](#11-bússola-zil--marcos-estratégicos)
12. [Workflow Editorial v1](#12-workflow-editorial-v1)
13. [Fontes de Dados](#13-fontes-de-dados)
14. [Modelo de Dados](#14-modelo-de-dados)
15. [Métricas de Sucesso v1](#15-métricas-de-sucesso-v1)
16. [Riscos e Mitigações](#16-riscos-e-mitigações)
17. [Visão de Longo Prazo (v2+)](#17-visão-de-longo-prazo-v2)

---

## 1. Visão

O ZIL Observatório é uma plataforma aberta, apartidária e orientada por dados que permite a qualquer cidadão brasileiro monitorar e avaliar seus representantes políticos nas pautas que determinam a soberania industrial e econômica do Brasil.

A plataforma transforma dados legislativos públicos em informação acionável: quem está votando a favor da industrialização do Brasil e quem está votando contra? Que projetos de lei estão tramitando agora que podem mudar o jogo?

O ZIL Observatório não é ferramenta de denúncia. É ferramenta de inteligência cívica. Não diz "esse político é corrupto" — diz "esse político votou X vezes contra o processamento local de minerais estratégicos."

**A informação é pública. A conexão entre os dados é o poder.**

### Declaração de missão

Dar a cada brasileiro a capacidade de saber, em 30 segundos, se seu deputado ou senador está trabalhando pela soberania industrial do país ou contra ela.

---

## 2. Contexto e Problema

### 2.1 O contexto macro

O Brasil possui:
- 94% das reservas globais de nióbio
- A segunda maior reserva de terras raras do mundo
- Matriz elétrica 83% renovável
- O maior potencial de hidrogênio verde do planeta
- O maior exportador mundial de alimentos

E ao mesmo tempo:
- Importa 87% dos fertilizantes que consome (US$26 bilhões/ano)
- Importa US$5 bilhões em semicondutores por ano
- Exporta petróleo cru e importa gasolina refinada
- Perdeu capacidade industrial em fertilizantes, refino e microeletrônica nas últimas três décadas

O mundo está se reindustrializando. Os EUA investem via CHIPS Act e IRA. A China controla o processamento de 19 dos 20 minerais estratégicos. A Indonésia baniu exportação de níquel bruto e hoje domina 71% do refino global. O Brasil tem todos os recursos para fazer o mesmo — mas as decisões políticas que determinam isso acontecem no Congresso, frequentemente sem que os cidadãos saibam como seus representantes votaram.

### 2.2 O problema específico

O Brasil possui dados legislativos abertos de alta qualidade. A Câmara dos Deputados e o Senado oferecem APIs REST com votações individuais, proposições e tramitações atualizadas diariamente.

O que falta é a infraestrutura para transformar esses dados em respostas claras:
1. **Como meu representante votou** em pautas que afetam a soberania industrial?
2. **Que proposições estão tramitando agora** que podem fortalecer ou enfraquecer nossos interesses nacionais?
3. **Onde o Brasil está hoje** nos indicadores estratégicos de soberania industrial?

### 2.3 Por que agora

As eleições brasileiras de outubro de 2026 são o momento de maior alavancagem. A plataforma precisa estar funcional antes do período eleitoral para que eleitores possam avaliar candidatos por seu histórico real de votação e a mídia tenha uma ferramenta de referência.

---

## 3. Objetivos do Produto

### 3.1 Objetivos primários (v1)

| Objetivo | Métrica | Meta v1 |
|----------|---------|---------|
| Cobertura de parlamentares | % com score calculado | 100% dos 513 deputados; 80%+ dos 81 senadores |
| Latência de dados | Tempo votação → plataforma | < 24 horas |
| Acesso público | Nenhum endpoint exige login | 100% das funcionalidades de leitura |
| Visibilidade | Veículos que citam dados ZIL | ≥ 5 antes das eleições |

### 3.2 O que o ZIL Observatório NÃO é

- Não é órgão de denúncia (monitora posicionamento, não corrupção)
- Não é veículo de mídia (produz dados, não reportagens)
- Não é plataforma partidária (avalia posições em pautas, não partidos)
- Não é rede social (em v1, sem interação entre usuários)

---

## 4. Público-Alvo

### 4.1 Personas v1

**Cidadão engajado**
- Quer saber se seu deputado trabalha pela soberania industrial
- Precisa de informação simples, visual, compartilhável
- Ação principal: consultar score, compartilhar o perfil do parlamentar

**Jornalista / Analista**
- Precisa de dados confiáveis para reportagens e análises
- Quer acessar a API pública, fazer queries, exportar datasets
- Ação principal: usar API, gerar visualizações, citar dados

**Especialista setorial**
- Economista, engenheiro, acadêmico que entende as pautas em profundidade
- Quer contribuir com curadoria e análise (em v1: via código/Discord)
- Ação principal: propor melhorias via PR no GitHub

**Desenvolvedor civic tech**
- Quer contribuir com código ou construir ferramentas derivadas
- Ação principal: contribuir no GitHub, usar API, forkar o projeto

### 4.2 Personas secundárias (presentes em v1 como visitantes)

- **Assessor parlamentar**: monitora como as pautas ZIL afetam a imagem do parlamentar
- **Organização da sociedade civil**: usa dados para advocacy setorial

---

## 5. Princípios de Design

### 5.1 Produto

1. **Dados antes de opinião.** Toda afirmação é rastreável a uma fonte pública verificável. O score ZIL é calculado por fórmula transparente, não por julgamento editorial arbitrário.

2. **30 segundos até o valor.** Um cidadão deve conseguir, em 30 segundos, encontrar seu deputado, ver o score, e entender se ele está do lado da soberania ou não. Profundidade está disponível para quem quiser — nunca é barreira.

3. **Transparência radical.** Toda classificação, todo score, toda decisão editorial é auditável publicamente via código aberto. O YAML de classificação está no repositório. O histórico de mudanças está no git.

4. **Apartidário por design.** Paleta verde e ouro (cores nacionais). Linguagem evita termos carregados. O critério é soberania industrial — e isso une espectros políticos opostos.

5. **Simples antes de completo.** v1 faz poucas coisas muito bem. Sem login, sem comunidade, sem features que desviem do foco: observabilidade pública.

### 5.2 Técnico

1. **Open source first.** Todo código, dado e metodologia é público desde o dia zero (AGPL-3.0).
2. **API-first.** Toda funcionalidade de leitura é acessível via API REST documentada.
3. **Mobile-first.** A maioria dos brasileiros acessa internet pelo celular.
4. **Contributor-friendly.** Setup local em < 5 minutos com Docker. Issues bem rotuladas.

---

## 6. Escopo v1

A v1 é uma **plataforma pública de leitura**. Sem contas de usuário. Sem interação. Sem features que demandam autenticação.

| Área | O que inclui |
|------|-------------|
| **Ranking** | Todos os parlamentares com score, filtros por UF/partido/categoria/casa |
| **Perfil** | Score, histórico de votos ZIL, breakdown por categoria |
| **Proposições** | Catálogo filtrável de proposições e votações classificadas |
| **Bússola ZIL** | Indicadores estratégicos do estado atual da soberania industrial |
| **Metodologia** | Explicação completa do score, categorias, processo editorial, limitações |
| **API pública** | REST API sem autenticação para leitura de todos os dados |
| **Ingestão** | Câmara dos Deputados (✅ concluído) + Senado Federal |
| **Editorial** | Via código: YAML versionado no git + Discord + PRs |

---

## 7. Fora do Escopo v1

As features abaixo são **explicitamente excluídas** da v1. Estão planejadas para v2 ou posterior.

| Feature | Por quê adiado |
|---------|----------------|
| Contas de usuário / login | Requer auth, infraestrutura de identidade, UI complexa |
| Assinar o manifesto (persistido) | Requer conta |
| Cobrar parlamentar | Requer conta, templates, integração com canais oficiais |
| Alertas (email/Telegram) | Requer conta + sistema de notificações |
| Curadoria comunitária | Requer conta + fluxo de revisão |
| Deliberação por consenso (Polis) | Requer conta + infraestrutura Polis, v3 |
| Compromisos públicos de parlamentares | Requer conta + verificação |
| Grafo de influência (TSE) | Crawler TSE complexo, fora do foco v1 |
| Monitor eleitoral 2026 | Downstream de financiamento (TSE) |
| Fórum de discussão | Requer moderação, conta |
| Gamificação | Requer conta |
| Dados subnacionais | Após v1 estável |

---

## 8. Funcionalidades v1

### F1 — Ranking de Parlamentares (`/ranking`)

Lista completa de todos os parlamentares (deputados + senadores) ordenada por Score ZIL.

- Filtros: casa (Câmara/Senado), UF, partido, categoria ZIL, ordenação (score ↑↓, nome)
- Card por parlamentar: foto, nome, partido, UF, score gauge (-10 a +10)
- Estado vazio para `score_zil = null`: "sem votações ZIL suficientes" (não é zero)
- Paginação
- Compartilhável (Open Graph tags por parlamentar)

### F2 — Perfil do Parlamentar (`/parlamentar/[id]`)

Página individual com histórico completo de atuação em pautas ZIL.

- Score ZIL com gauge visual e posição no ranking geral
- Breakdown por categoria: quanto do score vem de ZIL-FER, ZIL-MIN etc.
- Histórico de votações ZIL: data, descrição, categoria, voto registrado, alinhamento
- Link para a proposição em cada votação
- Orientação do partido vs. voto registrado (quando disponível)

### F3 — Proposições e Votações (`/proposicoes`)

Catálogo filtrável de proposições e votações classificadas em pautas ZIL.

- Filtros: categoria ZIL, ano, tipo (PL, PEC, PLP), casa
- Card: ementa, tipo, número/ano, categorias ZIL, relevância
- Página de detalhe: votações vinculadas, como cada parlamentar votou
- Link para o inteiro teor no site oficial (Câmara/Senado)

### F4 — Bússola ZIL (`/bussula`)

Painel de indicadores estratégicos — o estado atual da soberania industrial brasileira.

- Grid de indicadores por categoria ZIL
- Cada indicador: nome, valor atual, unidade, tendência (▲▼→), meta, fonte oficial com link
- Linha do tempo mostrando evolução por período de governo
- Gerenciado via `data/bussula/marcos.yml` pelos maintainers
- Metodologia explicada: como os marcos são escolhidos e atualizados

### F5 — Metodologia (`/metodologia`)

Transparência total sobre como o sistema funciona.

- Fórmula do Score ZIL com exemplo calculado passo a passo
- As 9 categorias ZIL: descrição, palavras-chave, exemplos de votações pró e contra
- Como a direção esperada é definida: processo editorial, Discord, PRs
- Limitações explícitas do score (o que ele não mede)
- Como contribuir: Discord, GitHub, issues abertas

### F6 — API Pública

REST API documentada via OpenAPI/Swagger, sem autenticação, sem rate limit agressivo.

- `GET /parlamentares` — ranking com filtros
- `GET /parlamentares/{id}` — perfil completo
- `GET /parlamentares/{id}/votos-zil` — histórico de votos ZIL
- `GET /proposicoes` — catálogo com filtros
- `GET /votacoes` — votações classificadas
- `GET /votacoes/{id}/votos` — votos individuais de uma votação
- `GET /bussula` — indicadores estratégicos
- `GET /stats` — estatísticas globais + data da última atualização
- Swagger UI em `/docs`
- Licença dos dados: CC BY-SA 4.0

---

## 9. Taxonomia de Pautas ZIL

As 9 categorias são **imutáveis sem RFC pública**. Definidas em `data/taxonomia/categorias.yml`.

| Código | Pauta | Descrição resumida |
|--------|-------|--------------------|
| `ZIL-FER` | Fertilizantes | Produção nacional, PNF, Autazes, Santa Quitéria, biofertilizantes |
| `ZIL-MIN` | Minerais Estratégicos | Nióbio, lítio, terras raras, processamento local, CBMM |
| `ZIL-SEM` | Semicondutores | Chips, CEITEC, PADIS, Brasil Semicon, microeletrônica |
| `ZIL-ENE` | Energia e Transição | Pré-sal, hidrogênio verde, baterias, fundo soberano, Petrobras |
| `ZIL-DIG` | Soberania Digital | LGPD, 5G, satélites, fibra óptica na Amazônia, soberania digital |
| `ZIL-DEF` | Defesa e Institucional | Embraer, defesa cibernética, ativos estratégicos, privatização |
| `ZIL-EDU` | Capital Humano | ITA, STEM, repatriação, formação técnica, P&D |
| `ZIL-AGR` | Agro-Indústria | Processamento agrícola, valor agregado, exportação processada |
| `ZIL-COM` | Comércio e Tarifas | OMC, Mercosul, BRICS, tarifas, reciprocidade comercial |

### Método de classificação (v1)

**Camada 1 — Keyword matching automático** (implementado):
Regex `\bkeyword\b` contra ementa + descrição de votação. Gerenciado em `data/taxonomia/categorias.yml`.

**Camada 2 — NLP semântico** (v2): embeddings para capturar proposições sem keywords explícitas.

**Camada 3 — Curadoria humana** (v2+): contestações por usuários, revisadas pelo comitê editorial.

Em v1: a classificação é automática. Correções via PR no `categorias.yml`, discutidas no Discord.

---

## 10. Score ZIL — Metodologia

### Fórmula

```
Score_ZIL = ( Σ alinhamento_i × peso_i ) / ( Σ |peso_i| ) × 10
```

- `alinhamento_i = +1.0` se votou na direção ZIL
- `alinhamento_i = -1.0` se votou contra a direção ZIL
- `alinhamento_i = 0.0` se ausente, absteve-se, ou obstruiu
- Score varia de **-10.0** a **+10.0**

### Pesos

| Tipo de votação | Peso |
|-----------------|------|
| Votação final em plenário | 3.0 |
| Votação em comissão relevante | 2.0 |
| Votação padrão | 1.0 |
| Requerimento processual | 0.5 |

Definidos pelo comitê editorial via `data/direcoes/*.yml`.

### Direção esperada

O campo `direcao_esperada` ("sim" ou "nao") em cada votação é definido **manualmente** pelo comitê editorial em `data/direcoes/` — nunca gerado automaticamente. Votações sem `direcao_esperada` não entram no cálculo.

Princípio operacional: **na dúvida, não classificar**. Melhor ter menos votações no score do que incluir votações com direção controversa.

### Limitações declaradas (exibidas na plataforma)

- Mede votação, não intenção (um parlamentar pode votar por disciplina partidária)
- Ausências não penalizam positivamente, mas diluem o denominador
- Não captura articulação política de bastidores
- Score `null` ≠ score `0.0` (significa "sem dados suficientes")
- Cobertura limitada às votações onde o comitê definiu direção esperada

---

## 11. Bússola ZIL — Marcos Estratégicos

A Bússola é um painel de **indicadores verificáveis** do estado real da soberania industrial brasileira — independente de votações ou parlamentares. É o "onde o Brasil está hoje" em cada uma das 9 áreas.

### Exemplos de indicadores

| Área | Indicador | Fonte |
|------|-----------|-------|
| ZIL-FER | % de fertilizantes produzidos no Brasil | ANDA/MAPA |
| ZIL-MIN | Volume de nióbio exportado bruto vs. processado | ANM |
| ZIL-SEM | Investimento em microeletrônica via PADIS (R$) | MCTI |
| ZIL-ENE | % da matriz elétrica de fonte renovável | ANEEL |
| ZIL-DIG | % da população com acesso à fibra óptica | ANATEL |
| ZIL-EDU | Nº de engenheiros formados/ano em áreas estratégicas | MEC/INEP |

### Gestão em v1

Gerenciado via `data/bussula/marcos.yml`. Formato:

```yaml
marcos:
  - codigo: BUSSULA-FER-01
    nome: Dependência de importação de fertilizantes
    categoria: ZIL-FER
    descricao: Percentual do consumo nacional suprido por importações
    valor_atual: 87
    unidade: "% importado"
    tendencia: estavel   # avancando | retrocedendo | estavel
    meta: 60
    prazo: 2030
    fonte: ANDA
    fonte_url: https://anda.org.br/
    ultima_atualizacao: "2026-01"
    governo_atual: Lula III
```

Atualização: trimestral ou quando dado oficial é publicado. Via PR + revisão.

---

## 12. Workflow Editorial v1

Toda decisão editorial em v1 é feita **via código**: YAML versionado no git, revisado via PR, discutido no Discord. Sem interface admin.

| Decisão | Arquivo | Processo |
|---------|---------|---------|
| Adicionar/remover keyword de categoria | `data/taxonomia/categorias.yml` | PR + 1 aprovação |
| Definir `direcao_esperada` de votação | `data/direcoes/[ano].yml` | Discord → PR + 2 aprovações |
| Definir peso de votação | `data/direcoes/[ano].yml` | Discord → PR + 2 aprovações |
| Atualizar indicador da Bússola | `data/bussula/marcos.yml` | PR + 1 aprovação + link de fonte |
| Adicionar nova categoria ZIL | `data/taxonomia/categorias.yml` | RFC pública ≥ 7 dias + 3 aprovações |

**Aplicar ao banco:** script `scripts/apply_direcoes.py` lê os YAMLs e atualiza o banco. Pode ser rodado localmente ou via CI/CD.

**Transparência:** todo PR de dados editoriais deve incluir justificativa em português. O histórico git é o log de auditoria.

**Discord:** todas as discussões sobre direção esperada ocorrem no Discord antes do PR. Link: a definir.

---

## 13. Fontes de Dados

| Dado | Fonte | Endpoint / Formato |
|------|-------|-------------------|
| Perfil de deputados | API Câmara | `GET /deputados` |
| Votações nominais (Câmara) | API Câmara | `GET /votacoes?ano=X` |
| Votos individuais (Câmara) | API Câmara | `GET /votacoes/{id}/votos` |
| Orientação de partidos | API Câmara | `GET /votacoes/{id}/orientacoes` |
| Proposições (Câmara) | API Câmara | via `proposicaoPrincipal` |
| Perfil de senadores | API Senado | `GET /senador/lista/atual` |
| Votações (Senado) | API Senado | `GET /plenario/lista/votacao/{ano}` |
| Votos individuais (Senado) | API Senado | XML |
| Indicadores Bússola | Fontes oficiais (ANDA, ANM, ANEEL...) | Manual via YAML |
| Direção esperada | **Comitê editorial** | `data/direcoes/*.yml` |
| Keywords ZIL | **Comitê editorial** | `data/taxonomia/categorias.yml` |

**Fora do escopo v1:** TSE (financiamento), Querido Diário, Portal da Transparência, dados de mídia.

---

## 14. Modelo de Dados

O modelo de dados v1 está implementado em `apps/api/models/__init__.py`. Tabelas ativas:

| Tabela | Descrição |
|--------|-----------|
| `parlamentares` | Deputados e senadores unificados |
| `proposicoes` | Matérias legislativas classificadas por ZIL |
| `votacoes` | Eventos de votação com categorias e direção esperada |
| `votos` | Voto individual de cada parlamentar por votação |
| `scores_votacao` | Contribuição granular de cada voto ao score |
| `ingestion_runs` | Log auditável de cada execução de ingestão |
| `financiamentos` | Estrutura pronta para TSE (v2) |

**Não implementadas em v1** (estrutura documentada para v2):
`usuarios`, `assinaturas_manifesto`, `cobrancas`, `alertas_config`, `deliberacoes`, `compromissos`, `marcos_zil` (substituído por YAML em v1).

---

## 15. Métricas de Sucesso v1

| Métrica | Meta |
|---------|------|
| Parlamentares com score calculado | ≥ 487 deputados (95%); ≥ 65 senadores (80%) |
| Votações-chave com direção esperada definida | ≥ 50 (2024–2026) |
| Latência dado → plataforma | < 24h |
| Uptime | ≥ 99% |
| API p95 latência | < 500ms |
| Idempotência de ingestão | 0 duplicatas em re-execução |
| Veículos que citam dados ZIL | ≥ 5 antes das eleições |

---

## 16. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| API da Câmara/Senado instável | Médio | Backoff exponencial + dados cacheados |
| Classificação errada gera controvérsia política | Alto | Direção esperada só por comitê, limitações exibidas, histórico auditável |
| Falta de maintainers para curadoria editorial | Médio | Processo leve (YAML + PR), Discord assíncrono |
| Aparência de partidarismo | Alto | Princípio II (apartidário por design), paleta nacional, linguagem neutra |
| Plataforma fora do ar antes das eleições | Baixo | CI/CD, deploy automático, backup |
| Score controverso por votação específica | Médio | "Na dúvida, não classificar" como norma operacional |

---

## 17. Visão de Longo Prazo (v2+)

A v1 é deliberadamente limitada. As features abaixo compõem a visão completa da plataforma — implementadas após a v1 estar estável e em uso.

**v2 — Participação:**
Autenticação, assinar o manifesto com persistência, alertas (email/Telegram), "cobrar meu deputado", curadoria comunitária básica, financiamento de campanha (TSE).

**v3 — Deliberação e Mobilização:**
Deliberação por consenso ao estilo Polis/vTaiwan, compromisos públicos de parlamentares com hash SHA-256, índice de continuidade governamental, monitor eleitoral 2026, dados subnacionais, gamificação.

Ver [docs/ROADMAP.md](ROADMAP.md) para detalhamento e cronograma.

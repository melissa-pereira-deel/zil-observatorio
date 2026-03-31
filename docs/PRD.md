# ZIL Observatório
### Plataforma aberta de observability política para a soberania industrial do Brasil

> *"Um país que já venceu a hiperinflação, inventou o PIX, transformou cerrado em celeiro do mundo e construiu a terceira maior fabricante de aviões do planeta pode fazer qualquer coisa — se decidir."*

---

## Índice

1. [Visão](#1-visão)
2. [Contexto e Problema](#2-contexto-e-problema)
3. [Objetivos do Produto](#3-objetivos-do-produto)
4. [Público-Alvo](#4-público-alvo)
5. [Princípios de Design](#5-princípios-de-design)
6. [Funcionalidades](#6-funcionalidades)
7. [Taxonomia de Pautas ZIL](#7-taxonomia-de-pautas-zil)
8. [Índice de Alinhamento ZIL (Score)](#8-índice-de-alinhamento-zil-score)
9. [Accountability: Projeto de Estado, não de Governo](#9-accountability-projeto-de-estado-não-de-governo)
10. [Comunidade: Jornada, Papéis e Governança de Usuários](#10-comunidade-jornada-papéis-e-governança-de-usuários)
11. [Fontes de Dados](#11-fontes-de-dados)
12. [Arquitetura Técnica](#12-arquitetura-técnica)
13. [Modelo de Dados](#13-modelo-de-dados)
14. [Roadmap](#14-roadmap)
15. [Modelo Open Source](#15-modelo-open-source)
16. [Como Contribuir](#16-como-contribuir)
17. [Governança](#17-governança)
18. [Riscos e Mitigações](#18-riscos-e-mitigações)
19. [Precedentes e Referências](#19-precedentes-e-referências)
20. [Métricas de Sucesso](#20-métricas-de-sucesso)
21. [FAQ](#21-faq)

---

## 1. Visão

O ZIL Observatório é uma plataforma aberta, apartidária e orientada por dados que permite a qualquer cidadão brasileiro monitorar, avaliar e pressionar seus representantes políticos nas pautas que determinam a soberania industrial e econômica do Brasil.

A plataforma transforma dados legislativos públicos — votações, proposições, financiamento de campanha — em informação acionável: quem está votando a favor da industrialização do Brasil e quem está votando contra? Quem financia esses votos? Que projetos de lei estão tramitando agora que podem mudar o jogo?

O ZIL Observatório não é ferramenta de denúncia. É ferramenta de inteligência cívica. Não diz "esse político é corrupto" — diz "esse político votou X vezes contra o processamento local de minerais estratégicos, e seus três maiores doadores são empresas de importação."

**A informação é pública. A conexão entre os dados é o poder.**

### Declaração de missão

Dar a cada brasileiro a capacidade de saber, em 30 segundos, se seu deputado ou senador está trabalhando pela soberania industrial do país ou contra ela — e as ferramentas para agir sobre essa informação.

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

O mundo está se reindustrializando. Os EUA investem US$1 trilhão via CHIPS Act e IRA. A China controla o processamento de 19 dos 20 minerais estratégicos. A Indonésia baniu exportação de níquel bruto e hoje domina 71% do refino global. O Brasil tem todos os recursos para fazer o mesmo — mas as decisões políticas que determinam isso acontecem no Congresso, frequentemente sem que os cidadãos saibam como seus representantes votaram.

### 2.2 O problema específico

O Brasil possui dados legislativos abertos de alta qualidade. A Câmara dos Deputados e o Senado oferecem APIs REST com votações individuais, proposições e tramitações atualizadas diariamente. O TSE publica dados granulares de financiamento de campanha.

O que falta é a infraestrutura para transformar esses dados em três respostas:

1. **Como meu representante votou** em pautas que afetam a soberania industrial do Brasil?
2. **Quem financia esse representante** e como isso se correlaciona com suas posições?
3. **Que proposições estão tramitando agora** que podem fortalecer ou enfraquecer nossos interesses nacionais?

O ZIL Observatório existe para responder essas perguntas em tempo real, com dados verificáveis, e converter informação em ação coletiva.

### 2.3 Por que agora

As eleições brasileiras de outubro de 2026 são o momento de maior alavancagem. A plataforma precisa estar funcional antes do período eleitoral para que:
- Eleitores possam avaliar candidatos por seu histórico real de votação (incumbentes)
- Candidatos novos possam ser pressionados a se posicionar sobre as pautas ZIL
- A mídia e sociedade civil tenham uma ferramenta de referência para cobrir o tema

---

## 3. Objetivos do Produto

### 3.1 Objetivos primários

| Objetivo | Métrica | Meta v1.0 |
|----------|---------|-----------|
| Tornar visível o posicionamento de cada parlamentar nas pautas de soberania | Cobertura de parlamentares com score calculado | 100% dos 513 deputados + 81 senadores |
| Permitir que cidadãos monitorem pautas em tempo real | Tempo entre votação/proposição e disponibilidade na plataforma | < 24 horas |
| Gerar pressão mensurável sobre parlamentares | Ações de contato/compartilhamento por parlamentar | 1.000 ações/mês |
| Construir comunidade ativa de monitoramento | Contribuidores ativos (código + dados + curadoria) | 100 contribuidores |
| Informar o debate eleitoral de 2026 | Cobertura em mídia referenciando dados ZIL | 10 veículos nacionais |

### 3.2 Objetivos secundários

- Servir como infraestrutura reutilizável para outras iniciativas de monitoramento legislativo
- Criar um dataset público de alta qualidade sobre comportamento legislativo em pautas industriais
- Demonstrar que civic tech pode gerar impacto político real no Brasil
- Conectar especialistas (economistas, engenheiros, diplomatas) com cidadãos comuns em torno de pautas concretas

### 3.3 O que o ZIL Observatório NÃO é

- Não é órgão de denúncia (não investiga corrupção — monitora posicionamento)
- Não é veículo de mídia (não produz reportagens — produz dados e análises)
- Não é plataforma partidária (não apoia candidatos — avalia posições)
- Não é rede social genérica (toda interação é orientada por dados legislativos)

---

## 4. Público-Alvo

### 4.1 Personas primárias

**Cidadão engajado**
- Quer saber se seu deputado trabalha pela soberania industrial
- Precisa de informação simples, visual, compartilhável
- Ação principal: consultar score, compartilhar cards, assinar manifesto

**Jornalista / Analista**
- Precisa de dados confiáveis para reportagens e análises
- Quer acessar API pública, fazer queries complexas, exportar datasets
- Ação principal: usar API, gerar visualizações, citar dados

**Especialista setorial**
- Economista, engenheiro, acadêmico que entende as pautas em profundidade
- Quer contribuir com curadoria: classificar proposições, validar scores
- Ação principal: participar do comitê editorial, escrever análises

**Desenvolvedor civic tech**
- Quer contribuir com código, criar integrações, construir ferramentas derivadas
- Ação principal: contribuir no GitHub, usar API, forkar o projeto

### 4.2 Personas secundárias

**Assessor parlamentar**: monitora como as pautas ZIL afetam a imagem do parlamentar.

**Candidato a cargo eletivo**: usa a plataforma para demonstrar alinhamento com soberania industrial.

**Organização da sociedade civil**: usa dados para advocacy setorial (agro, indústria, defesa).

---

## 5. Princípios de Design

### 5.1 Princípios de produto

1. **Dados antes de opinião.** Toda afirmação na plataforma é rastreável a uma fonte pública verificável. O score ZIL é calculado por fórmula transparente, não por julgamento editorial.

2. **Ação antes de informação.** Cada tela deve responder: "o que o usuário pode fazer com isso?" Se a resposta for "nada", a funcionalidade está incompleta. Informação sem alavanca de ação é desperdício.

3. **30 segundos até o valor.** Um cidadão deve conseguir, em 30 segundos, encontrar seu deputado, ver o score, e entender se ele está do lado da soberania ou não. Profundidade está disponível para quem quiser — mas nunca é barreira.

4. **Transparência radical.** Toda classificação, todo score, toda decisão editorial é auditável publicamente. Qualquer pessoa pode contestar uma classificação e ver a justificativa.

5. **Apartidário por design.** A paleta visual usa verde e ouro (cores nacionais, não partidárias). A linguagem evita termos carregados ("esquerda", "direita", "progressista", "conservador"). O critério é soberania industrial — e isso une espectros.

### 5.2 Princípios técnicos

1. **Open source first.** Todo código, dado e metodologia é público desde o dia zero.
2. **API-first.** Toda funcionalidade é acessível via API antes de ter interface gráfica.
3. **Offline-tolerant.** Dados cached localmente. A plataforma deve funcionar razoavelmente em conexões instáveis (realidade de boa parte do Brasil).
4. **Mobile-first.** A maioria dos brasileiros acessa internet pelo celular. O design começa no mobile.
5. **Contributor-friendly.** Setup local em < 5 minutos com Docker. Documentação exaustiva. Issues bem rotuladas.

---

## 6. Funcionalidades

### 6.1 Fase 1 — Fundação (semanas 1-12)

#### F1.1 Perfil de Parlamentar
- Foto, nome, partido, estado, mandato
- Score ZIL (gauge visual: -10 a +10)
- Histórico de votos em pautas ZIL (timeline visual)
- Frentes parlamentares de que participa
- Link para contato (email, redes sociais)
- Proposições de autoria própria classificadas por pauta ZIL

#### F1.2 Ranking ZIL
- Lista de todos os parlamentares ordenada por score
- Filtros: câmara/senado, partido, estado, faixa de score
- Busca por nome
- Cards compartilháveis com score (otimizado para redes sociais)
- Ranking por partido (média dos membros)
- Ranking por estado (média da bancada)

#### F1.3 Painel de Proposições
- Lista de proposições ativas classificadas por pauta ZIL
- Status de tramitação (em comissão, pronta para plenário, votada)
- Classificação automática por categoria ZIL
- Indicador de urgência (proximidade de votação)
- Link para inteiro teor no site da Câmara/Senado

#### F1.4 Busca
- Full-text search em proposições, parlamentares, votações
- Filtros por data, tipo, categoria ZIL, resultado
- Autocomplete

#### F1.5 Manifesto integrado
- Página do Manifesto ZIL embarcada na plataforma
- Coleta de assinaturas com contador público
- Compartilhamento otimizado (Open Graph tags)

### 6.2 Fase 2 — Inteligência (semanas 12-24)

#### F2.1 Grafo de Influência
- Rede visual: parlamentar ↔ doador ↔ setor econômico ↔ frente parlamentar
- Baseado em dados TSE (prestação de contas) cruzados com dados legislativos
- Permite responder: "os maiores doadores do deputado X são do setor Y — e ele votou Z vezes a favor de regulação favorável a esse setor"

#### F2.2 Alertas em Tempo Real
- Notificação quando proposição de pauta ZIL avança na tramitação
- Notificação quando votação relevante está agendada
- Notificação quando score de parlamentar muda significativamente
- Canais: email, push notification (PWA), Telegram bot
- Configurável por usuário: pautas, estados, parlamentares específicos

#### F2.3 Comparativo
- Comparar lado a lado dois ou mais parlamentares
- Comparar partidos por score médio
- Comparar estados por score médio da bancada
- Evolução temporal do score (gráfico de linha)

#### F2.4 API Pública
- REST API documentada com OpenAPI/Swagger
- Endpoints: parlamentares, votações, proposições, scores, financiamentos
- Rate limiting por API key (gratuita, com registro)
- Formato: JSON
- Uso irrestrito para fins não-comerciais (licença dos dados: CC BY-SA 4.0)

### 6.3 Fase 3 — Comunidade (semanas 24-36)

#### F3.1 Fórum de Discussão
- Discussões vinculadas a proposições, parlamentares ou pautas ZIL
- Upvote/downvote para priorização orgânica
- Moderação comunitária (sistema de reputação)
- Markdown support, menções a parlamentares e proposições

#### F3.2 Curadoria Comunitária
- Qualquer usuário pode propor reclassificação de uma proposição
- Propostas passam por revisão do comitê editorial
- Histórico de todas as classificações e contestações é público

#### F3.3 Campanhas de Pressão
- Templates de mensagem para enviar a parlamentares
- Botão "Cobrar meu deputado" com pré-preenchimento por pauta
- Contador público de cobranças enviadas por parlamentar
- Integração com e-mail e redes sociais do parlamentar

#### F3.4 Dashboard Agregado
- Visão nacional: como o Congresso se posiciona por pauta ZIL
- Mapa por estado com código de cores (score médio)
- Tendência temporal: o Congresso está se tornando mais ou menos pró-soberania?

### 6.4 Fase 4 — Mobilização (semanas 36-48)

#### F4.1 Monitor Eleitoral 2026
- Acompanhamento de compromissos de campanha vs. votos reais (incumbentes)
- Perfil de candidatos novos: propostas vs. financiadores
- Comparativo entre candidatos por posicionamento em pautas ZIL
- Guia do eleitor por estado

#### F4.2 Gamificação
- Badges para cidadãos que contribuem (curadoria, cobrança, compartilhamento)
- Leaderboard de contribuidores
- Níveis de engajamento: observador → curador → mobilizador

#### F4.3 Dados Subnacionais
- Extensão para assembleias legislativas estaduais
- Extensão para câmaras municipais (onde APIs existirem)
- Parcerias com projetos existentes (Querido Diário)

---

## 7. Taxonomia de Pautas ZIL

Toda proposição e votação na plataforma é classificada em uma ou mais categorias temáticas vinculadas ao Manifesto ZIL.

| Código | Pauta | Descrição | Palavras-chave (amostra) |
|--------|-------|-----------|--------------------------|
| `ZIL-FER` | Fertilizantes | Produção nacional, redução de dependência, Plano Nacional de Fertilizantes | fertilizante, potássio, fosfato, nitrogênio, NPK, Embrapa, PNF, Autazes |
| `ZIL-MIN` | Minerais Estratégicos | Nióbio, terras raras, lítio, grafite, processamento local | nióbio, terras raras, lítio, grafite, mineral crítico, CBMM, beneficiamento |
| `ZIL-SEM` | Semicondutores | Cadeia nacional de chips, design, empacotamento, PADIS | semicondutor, chip, microeletrônica, Padis, Brasil Semicon, RISC-V |
| `ZIL-ENE` | Energia e Transição | Pré-sal, hidrogênio verde, baterias, fundo soberano | pré-sal, hidrogênio verde, bateria, Petrobras, etanol, renovável, fundo soberano |
| `ZIL-DIG` | Soberania Digital | Dados, telecomunicações, satélites, regulação de plataformas | Starlink, dados pessoais, LGPD, satélite, fibra óptica, 5G, soberania digital |
| `ZIL-DEF` | Defesa e Institucional | Embraer, cibernética, proteção de ativos, planejamento estratégico | Embraer, defesa cibernética, ativo estratégico, privatização, CFIUS |
| `ZIL-EDU` | Capital Humano | Formação em áreas estratégicas, repatriação de talentos | engenharia, STEM, ITA, Ceitec, repatriação, formação técnica, pesquisa |
| `ZIL-AGR` | Agro-Indústria | Processamento agrícola, valor agregado, cadeia integrada | agro processamento, valor agregado, agroindústria, industrialização rural |
| `ZIL-COM` | Comércio e Tarifas | Acordos comerciais, tarifas, proteção comercial, Mercosul | tarifa, OMC, Mercosul, acordo bilateral, BRICS, reciprocidade, exportação |

### Método de classificação

**Camada 1 — Automática (baseline):** matching de palavras-chave e expressões regulares contra a ementa, ementa detalhada e indexação da proposição. Cobertura alta, precisão moderada.

**Camada 2 — NLP (melhoria):** embeddings semânticos via modelo multilíngue (sentence-transformers) treinado/fine-tuned com proposições manualmente classificadas. Captura relações semânticas que keywords perdem.

**Camada 3 — Curadoria humana:** comitê editorial e comunidade validam, corrigem e refinam classificações. Toda correção alimenta o modelo de volta (human-in-the-loop).

A classificação de cada proposição é pública, incluindo o método utilizado e a confiança. Qualquer usuário pode contestar.

---

## 8. Índice de Alinhamento ZIL (Score)

### 8.1 Definição

O Score ZIL é um número de **-10.0 a +10.0** que representa o grau de alinhamento de um parlamentar com as pautas de soberania industrial do Brasil, calculado a partir de seu histórico de votação.

- **+10.0**: votou consistentemente a favor da soberania industrial em todas as pautas
- **0.0**: posição neutra ou sem votos registrados em pautas ZIL
- **-10.0**: votou consistentemente contra a soberania industrial

### 8.2 Cálculo

Cada votação classificada em uma pauta ZIL recebe:
- **Direção esperada**: o que o manifesto ZIL defenderia (sim ou não). Definida pelo comitê editorial.
- **Peso**: importância relativa (escala 0.1 a 3.0)
  - Votação final em plenário: peso 3.0
  - Votação em comissão relevante: peso 2.0
  - Requerimento processual: peso 0.5
  - Votação com quórum baixo: penalidade de 0.5x

Fórmula:

```
Score_ZIL(parlamentar) = ( Σ alinhamento_i × peso_i ) / ( Σ |peso_i| ) × 10
```

Onde `alinhamento_i`:
- `+1.0` se votou na direção ZIL
- `-1.0` se votou contra a direção ZIL
- `0.0` se ausente ou absteve-se (não pontua positiva nem negativamente, mas o peso entra no denominador)

### 8.3 Curadoria da direção esperada

Este é o ponto mais sensível da plataforma. A legitimidade do score depende inteiramente da transparência e da qualidade da definição de "direção esperada."

**Modelo de governança em três camadas:**

1. **Comitê editorial fundador** (5-9 pessoas): economistas, engenheiros, diplomatas e acadêmicos com expertise em política industrial. Definem as classificações iniciais. Membros são públicos.

2. **Comunidade**: qualquer usuário registrado pode propor reclassificação com justificativa. Propostas com apoio comunitário (upvotes) são enviadas ao comitê.

3. **Registro de auditoria**: toda classificação, toda mudança, toda contestação é registrada com timestamp, autor e justificativa. Nenhuma classificação é irreversível.

**Princípio operacional:** na dúvida, não classificar. É melhor ter menos votações no score do que incluir votações cuja direção é controversa.

### 8.4 Limitações declaradas

- O score mede votação, não intenção. Um parlamentar pode votar "sim" por acordo partidário, não por convicção.
- Ausências não são punidas no numerador, mas diluem o denominador. Parlamentares que se ausentam sistematicamente de votações ZIL terão score mais próximo de zero.
- O score não captura trabalho de bastidor (negociações, articulações, relatoria) que pode ser tão ou mais importante que o voto.
- Pautas classificadas como ZIL são um subconjunto do universo legislativo. O score não pretende avaliar a "qualidade" geral do parlamentar.

Essas limitações são exibidas na plataforma junto ao score.

---

## 9. Accountability: Projeto de Estado, não de Governo

### 9.1 O problema da descontinuidade

O Brasil não tem déficit de planos. Tem déficit de continuidade. O Nova Indústria Brasil é o quinto programa industrial desde 2003. O Plano Nacional de Fertilizantes foi lançado em 2022 e a produção doméstica caiu desde então. Angra 3 começou em 1984.

O ciclo é sempre o mesmo: um governo lança um programa, aloca recursos, faz coletiva. O governo seguinte abandona, renomeia ou desmonta — não porque era ruim, mas porque era "do outro." Nenhum país se industrializou assim.

A descontinuidade é racional para o político individual: o crédito vai para quem lança, não para quem continua; o horizonte de retorno é maior que o mandato; e não há punição visível por descontinuar. O ZIL ataca cada um desses incentivos com contra-mecanismos tecnológicos.

### 9.2 Mecanismo 1: Compromisso Público Rastreável

Qualquer candidato ou parlamentar pode registrar compromissos públicos, específicos e mensuráveis sobre pautas de soberania industrial na plataforma.

Não é "eu apoio a indústria" — é:
- "Me comprometo a votar a favor da PL 1234/2026 que exige processamento local de nióbio"
- "Me comprometo a não votar pela privatização de ativos estratégicos sem parecer de segurança"
- "Me comprometo a manter o orçamento do programa X no nível Y"

Cada compromisso é registrado com timestamp e hash SHA-256 (imutável). A plataforma monitora automaticamente se o parlamentar cumpriu ou descumpriu — cruzando o texto do compromisso com os dados de votação das APIs oficiais.

O resultado é um **Índice de Cumprimento** — percentual de compromissos honrados. Diferente do Score ZIL (alinhamento temático), o Índice de Cumprimento mede integridade: "essa pessoa faz o que promete?"

### 9.3 Mecanismo 2: Marcos Estratégicos Intergovernamentais

Projetos estratégicos precisam de metas intermediárias que cruzem mandatos. A plataforma define e monitora "Marcos ZIL" — objetivos mensuráveis com prazo que independem de governo:

| Marco | Métrica | Fonte de dados | Prazo |
|-------|---------|----------------|-------|
| Autazes operacional | Produção > 0 ton/ano | ANM/IBRAM | 2030 |
| Dependência fertilizantes < 70% | % importação | ANDA | 2028 |
| Regime de minerais estratégicos | Lei aprovada | Câmara/Senado | 2027 |
| Brasil Semicon executado | R$ investidos / metas PADIS | MCTI | 2029 |
| Fibra óptica Norte completa | km instalados | ANATEL | 2028 |
| Fundo soberano criado | Lei + primeiro depósito | Congresso/BCB | 2028 |

Cada marco tem dados públicos verificáveis. A plataforma puxa esses dados automaticamente e atualiza o status trimestralmente. Quando um governo muda, os marcos não mudam — e a plataforma mostra publicamente se o novo governo avançou, estagnou ou retrocedeu.

Isso cria uma narrativa de continuidade que a mídia pode usar: "Dos 12 marcos ZIL, o governo atual avançou em 4, estagnou em 5 e retrocedeu em 3."

### 9.4 Mecanismo 3: Índice de Continuidade Governamental

Para cada governo (federal, estadual), a plataforma calcula um "Índice de Continuidade" que mede quanto dos programas estratégicos do governo anterior foram mantidos, expandidos ou desmontados.

Se o governo anterior lançou um programa com orçamento X e metas Y, e o governo atual cortou o orçamento para X/2 e não atingiu as metas — isso aparece como descontinuidade. Se manteve ou expandiu, aparece como continuidade.

O custo político de descontinuar se torna visível e quantificável.

### 9.5 Mecanismo 4: Ranking de Horizonte

Além do Score ZIL (alinhamento temático), a plataforma cria um segundo ranking: o **Horizonte** do parlamentar — quanto da sua atuação é orientada por projetos de longo prazo vs. pautas de curto prazo.

Critérios que aumentam o Horizonte:
- Autoria de PLs com impacto estrutural (infraestrutura, industrialização, educação de base)
- Participação em frentes parlamentares de longo prazo
- Votos consistentes em pautas ZIL ao longo de múltiplas legislaturas
- Compromissos públicos cumpridos

Critérios que diminuem:
- Atuação concentrada em pautas clientelistas ou de curto prazo
- Descontinuidade de posições entre legislaturas
- Ausência sistemática em votações estratégicas

### 9.6 Modelo de dados — Accountability

```sql
CREATE TABLE compromissos (
    id UUID PRIMARY KEY,
    parlamentar_id UUID REFERENCES parlamentares NOT NULL,
    texto TEXT NOT NULL,
    categorias_zil VARCHAR[],
    proposicoes_vinculadas UUID[],
    meta_mensuravel TEXT,
    prazo DATE,
    status ENUM('pendente','cumprido','descumprido','expirado'),
    verificacao_automatica BOOLEAN DEFAULT FALSE,
    evidencia TEXT,
    data_registro TIMESTAMP NOT NULL,
    hash_registro VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE marcos_zil (
    id UUID PRIMARY KEY,
    titulo VARCHAR NOT NULL,
    descricao TEXT NOT NULL,
    categoria_zil VARCHAR NOT NULL,
    metrica VARCHAR NOT NULL,
    fonte_dados VARCHAR,
    valor_baseline DECIMAL,
    valor_meta DECIMAL,
    prazo DATE NOT NULL,
    valor_atual DECIMAL,
    status ENUM('avancando','estagnado','retrocedendo','alcancado'),
    ultima_atualizacao TIMESTAMP,
    historico JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE continuidade (
    id UUID PRIMARY KEY,
    programa VARCHAR NOT NULL,
    governo VARCHAR NOT NULL,
    orcamento_previsto DECIMAL,
    orcamento_executado DECIMAL,
    metas_definidas INTEGER,
    metas_alcancadas INTEGER,
    status ENUM('expandido','mantido','reduzido','desmontado'),
    fonte TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 9.7 Métricas de sucesso — Accountability

| Métrica | Meta 12 meses | Meta 24 meses |
|---------|:---:|:---:|
| Parlamentares com compromissos registrados | 50 | 200 |
| Marcos estratégicos monitorados | 12 | 30 |
| Taxa média de cumprimento | — (baseline) | > 60% |
| Cobranças de continuidade enviadas | 5.000 | 50.000 |
| Programas com comparativo intergovernamental | 5 | 15 |

---

## 10. Comunidade: Jornada, Papéis e Governança de Usuários

### 10.1 O problema de design

A maioria das plataformas cívicas falha no mesmo ponto: conseguem atenção inicial, mas não sustentam comunidade. O Operação Serenata de Amor detectou gastos irregulares brilhantemente — e morreu por falta de comunidade ativa. O motivo é que essas plataformas tratam o usuário como consumidor de informação, não como participante de um sistema vivo.

O ZIL precisa resolver três problemas de comunidade simultaneamente:

1. **Progressão**: como levar alguém de "vi no Twitter" a "classifico proposições toda semana"?
2. **Diversidade sustentada**: como evitar que a comunidade se torne uma bolha ideológica?
3. **Qualidade sem gatekeeping**: como manter rigor sem criar barreiras que afastem cidadãos comuns?

### 10.2 Princípios de design da comunidade

**Leitura livre, escrita gradual.** Qualquer pessoa acessa 100% dos dados, scores, rankings e marcos sem criar conta. O registro desbloqueia ação — não informação. Isso garante que a plataforma é útil antes de pedir qualquer coisa ao usuário.

**Confiança se constrói por ação, não por declaração.** Ninguém recebe permissões por preencher um formulário. Cada nível é desbloqueado por contribuição verificável — uma classificação aceita, uma contestação fundamentada, um PR mergeado.

**Reputação por consistência, não por volume.** Um curador que classificou 30 proposições com 95% de aprovação tem mais peso que um que classificou 300 com 60% de aprovação. Qualidade bate quantidade.

**Diversidade é requisito, não aspiração.** O sistema mede e reporta a distribuição geográfica, temática e (quando auto-declarada) política da comunidade ativa. Se uma região, pauta ou tendência estiver sub-representada, o sistema sinaliza e prioriza recrutamento nessa lacuna.

### 10.3 Jornada do usuário

A jornada tem 5 estágios. Cada estágio desbloqueia capacidades novas e é atingido por ação — não por tempo.

```
VISITANTE → MEMBRO → PARTICIPANTE → CURADOR → LÍDER
  (0)         (1)        (2)            (3)       (4)
```

#### Estágio 0 — Visitante (sem conta)

O visitante é o público mais importante: se a experiência sem conta não for excelente, ninguém cria conta.

**Pode fazer:**
- Ver ranking completo de parlamentares com score ZIL
- Ver perfil de qualquer parlamentar (votos, score, financiamento)
- Ver proposições classificadas por pauta ZIL
- Ver painel de marcos estratégicos (bússola)
- Ver resultados de deliberações Polis encerradas
- Compartilhar cards de score em redes sociais
- Ler o manifesto
- Acessar API pública (com rate limit generoso)

**Não pode fazer:**
- Participar de deliberações (votar em declarações)
- Propor classificações ou contestações
- Registrar compromissos (se for parlamentar)
- Cobrar parlamentar via plataforma
- Comentar em discussões

**Experiência-alvo:** "em 30 segundos eu encontro meu deputado, vejo o score, e entendo se ele está do lado da soberania ou não."

**Chamada à ação:** em cada página útil, um convite discreto para criar conta — nunca um bloqueio. Exemplo: "Quer cobrar esse deputado? Crie sua conta em 30 segundos."

#### Estágio 1 — Membro (conta criada)

**Registro:** email + UF (obrigatório), nome (obrigatório, pode ser pseudônimo), CPF (opcional, necessário para deliberações Polis para evitar bots). Autenticação via magic link, Google ou GitHub. Sem senha.

**Desbloqueia:**
- Assinar o manifesto com registro público
- Participar de deliberações Polis (votar concordo/discordo em declarações)
- "Seguir" parlamentares e pautas (receber alertas)
- Cobrar parlamentar via template (botão "Cobrar meu deputado")
- Salvar buscas e configurar notificações
- Painel pessoal: "meus deputados" baseado na UF

**Métricas internas:** toda ação do membro contribui para um "perfil de engajamento" (não público) que mede: frequência de acesso, diversidade de pautas consultadas, participação em deliberações. Isso alimenta o convite para o próximo estágio.

**Convite para progressão:** após 5 participações em deliberações ou 10 visitas à plataforma, o sistema convida o membro a se tornar participante. Nunca é requisito — sempre convite.

#### Estágio 2 — Participante (contribuidor ativo)

**Desbloqueio:** automático após 5 ações qualificadas (participações em deliberações, cobranças a parlamentares, compartilhamentos verificados) OU por convite de um curador.

**Desbloqueia:**
- Submeter declarações em deliberações Polis (propor ideias, não apenas votar)
- Propor classificação de proposição por pauta ZIL (sujeita a revisão)
- Propor contestação de classificação existente (com justificativa obrigatória)
- Propor novo marco estratégico para a bússola (via RFC simplificada)
- Participar de discussões no fórum (vinculadas a proposições ou parlamentares)
- Votar em RFCs abertas
- Badge "Participante" no perfil

**Restrições:**
- Classificações propostas precisam de aprovação de 2 curadores
- Contestações precisam de justificativa textual (mínimo 100 caracteres)
- Máximo de 3 propostas de classificação por dia (anti-spam)
- Declarações em Polis limitadas a 5 por deliberação

#### Estágio 3 — Curador (guardião de qualidade)

O curador é o papel mais importante da comunidade. Curadores garantem que os dados da plataforma são precisos, que as classificações são justificadas, e que o debate mantém qualidade.

**Desbloqueio:** 10 classificações propostas e aceitas com taxa de aprovação ≥ 80% + aprovação de 2 curadores existentes + confirmação de identidade (CPF verificado, não público).

**Desbloqueia:**
- Aprovar ou rejeitar classificações propostas por participantes
- Definir "direção esperada" de votações (com justificativa pública obrigatória)
- Moderar discussões do fórum (esconder spam, sinalizar violações de conduta)
- Revisar contestações e decidir reclassificações (com outro curador)
- Acesso ao painel de curadoria: fila de proposições pendentes, métricas de qualidade
- Propor temas para deliberação Polis
- Badge "Curador" + especialidade temática no perfil
- Voto com peso em RFCs (1 voto = 1 voto, mas curador conta para quórum qualificado)

**Especialização temática:** cada curador declara 1-3 categorias ZIL de expertise (ZIL-FER, ZIL-SEM etc.). Classificações na sua área de expertise têm peso maior no consenso de aprovação. Isso evita que um especialista em fertilizantes decida sobre semicondutores.

**Responsabilidades:**
- Revisar pelo menos 5 classificações pendentes por semana (ou perder status após 4 semanas de inatividade)
- Justificar toda decisão publicamente
- Declarar conflito de interesse quando aplicável (trabalha em setor afetado)
- Participar de pelo menos 1 deliberação Polis por trimestre

**Remoção:** por inatividade (8 semanas sem revisão), por taxa de aprovação caindo abaixo de 60% nas últimas 50 revisões (sinaliza viés), ou por violação do código de conduta.

#### Estágio 4 — Líder (maintainer / comitê editorial)

**Subdividido em dois papéis:**

**Maintainer (técnico):** merge de PRs, decisões de arquitetura, releases, prioridades de backlog.
- Desbloqueio: contribuição técnica consistente + indicação por maintainer + RFC comunitária
- Máximo 5 pessoas. Mandato de 12 meses, renovável. Rotação obrigatória de pelo menos 1/ano.

**Comitê editorial (conteúdo):** validação final de classificações controversas, definição de direção esperada quando curadores divergem, aprovação de novos marcos.
- Desbloqueio: expertise demonstrada + indicação aberta + deliberação Polis da comunidade
- 5-9 pessoas. Diversidade obrigatória (espectros políticos, regiões, setores).
- Mandato de 12 meses, renovável. Pelo menos 2 rotações/ano.

**Não pode acumular:** ninguém é maintainer E comitê editorial simultaneamente.

### 10.4 Mapa de permissões

| Ação | Visitante | Membro | Participante | Curador | Líder |
|------|:---------:|:------:|:------------:|:-------:|:-----:|
| Ver ranking, scores, dados | ✅ | ✅ | ✅ | ✅ | ✅ |
| Compartilhar cards | ✅ | ✅ | ✅ | ✅ | ✅ |
| Acessar API pública | ✅ | ✅ | ✅ | ✅ | ✅ |
| Assinar manifesto | — | ✅ | ✅ | ✅ | ✅ |
| Votar em deliberações Polis | — | ✅ | ✅ | ✅ | ✅ |
| Seguir pautas/parlamentares | — | ✅ | ✅ | ✅ | ✅ |
| Cobrar parlamentar | — | ✅ | ✅ | ✅ | ✅ |
| Submeter declarações Polis | — | — | ✅ | ✅ | ✅ |
| Propor classificação | — | — | ✅ | ✅ | ✅ |
| Contestar classificação | — | — | ✅ | ✅ | ✅ |
| Propor marco/RFC | — | — | ✅ | ✅ | ✅ |
| Votar em RFCs | — | — | ✅ | ✅ | ✅ |
| Aprovar/rejeitar classificações | — | — | — | ✅ | ✅ |
| Definir direção esperada | — | — | — | ✅ | ✅ |
| Moderar discussões | — | — | — | ✅ | ✅ |
| Propor temas para deliberação | — | — | — | ✅ | ✅ |
| Merge de código | — | — | — | — | ✅ (M) |
| Decisão editorial final | — | — | — | — | ✅ (CE) |
| Aprovar novos curadores | — | — | — | — | ✅ (CE) |

*(M) = Maintainer, (CE) = Comitê Editorial*

### 10.5 Casos de uso detalhados

**Caso 1: Cidadão descobre o ZIL pelo Twitter**

Maria vê um card compartilhado "Deputado X: Score ZIL -4.2" no Twitter. Clica e chega ao perfil do deputado. Vê o score, os votos em pautas ZIL, os doadores de campanha. Quer cobrar o deputado. A plataforma mostra: "Quer cobrar esse deputado? Crie sua conta." Maria cria conta com email + UF em 20 segundos. Envia mensagem pré-formatada ao gabinete do deputado. Recebe confirmação. Na próxima deliberação Polis ("O Brasil deveria exigir processamento local de nióbio?"), Maria recebe notificação e participa votando em 15 declarações em 3 minutos.

**Caso 2: Economista quer contribuir com curadoria**

Ricardo é economista especializado em política industrial. Cria conta, navega as proposições classificadas e percebe que algumas classificações em ZIL-SEM estão imprecisas. Como participante, propõe reclassificação de 3 proposições com justificativas detalhadas. Suas propostas são aceitas pelos curadores. Após 10 classificações aceitas com 90% de aprovação, Ricardo recebe convite para se tornar curador com especialidade em ZIL-SEM. Agora revisa classificações de outros participantes e define a direção esperada de votações sobre semicondutores.

**Caso 3: Jornalista usa a API para reportagem**

Fernanda é repórter de dados do Nexo. Acessa a API pública sem criar conta. Puxa dados de todos os parlamentares de Goiás com score ZIL abaixo de -3. Cruza com dados de financiamento de campanha. Publica reportagem citando o ZIL como fonte. A reportagem gera tráfego para a plataforma. Fernanda cria conta para receber alertas sobre pautas específicas.

**Caso 4: Assessor parlamentar monitora o score do chefe**

Paulo é assessor do deputado Y. Cria conta, segue o perfil do deputado Y. Recebe notificações quando o score muda, quando uma nova classificação afeta o deputado, quando cidadãos enviam cobranças. Usa as informações para briefar o deputado antes de votações. Eventualmente, o deputado registra compromissos públicos na plataforma por iniciativa própria.

**Caso 5: Grupo organizado tenta capturar a curadoria**

Um grupo partidário coordena 20 contas para criar membros, virar participantes e propor classificações enviesadas. O sistema detecta: as 20 contas foram criadas na mesma semana, propõem classificações que correlacionam 100% com posição de um partido específico, e votam em bloco em deliberações Polis. Flag automático é disparado. Curadores existentes revisam e rejeitam as classificações. As contas são sinalizadas. O padrão de correlação partidária é reportado publicamente (sem identificar indivíduos).

### 10.6 Espaços da comunidade

A plataforma organiza a interação comunitária em espaços com propósitos distintos:

**Deliberações** (tipo Polis)
- Propósito: encontrar consenso transversal em questões estratégicas
- Acesso: membros votam, participantes+ submetem declarações
- Duração: 7-28 dias, definida ao abrir
- Output: relatório público com clusters de opinião e declarações-ponte
- Frequência: 1-2 por mês (nunca mais — deliberação exige atenção)

**Fórum de proposições**
- Propósito: discussão factual sobre proposições legislativas específicas
- Acesso: participantes+ para postar, membros para ler
- Regra: toda afirmação deve citar fonte ou dado. Opinião pura é permitida se sinalizada como tal
- Moderação: curadores, com escalation para comitê editorial

**Fila de curadoria**
- Propósito: classificar proposições pendentes, revisar contestações
- Acesso: participantes propõem, curadores revisam
- Gamificação leve: barra de progresso "X proposições aguardando classificação esta semana"
- Não é chat — é workflow com estados (pendente → em revisão → aprovada/rejeitada)

**Canal de coordenação** (Discord/Telegram)
- Propósito: comunicação informal, pareamento, dúvidas rápidas
- Acesso: aberto a membros+
- Não é onde decisões acontecem — decisões são no GitHub/plataforma (para rastreabilidade)

**Weekly sync** (videoconferência)
- Propósito: alinhamento semanal, demos, prioridades
- Acesso: aberto a todos (voz para participantes+, listeners para membros)
- Gravada e publicada

### 10.7 Perfil do usuário

O perfil é a identidade pública do membro na plataforma. É desenhado para ser informativo sem ser invasivo.

**Dados públicos:**
- Nome ou pseudônimo
- UF
- Papel (membro / participante / curador / líder)
- Badge de especialidade temática (para curadores)
- Data de registro
- Contagem de ações: deliberações participadas, classificações propostas/aceitas, cobranças enviadas
- Histórico de votos em deliberações Polis (transparência radical — se você votou, é público)

**Dados privados (nunca exibidos):**
- Email
- CPF (quando verificado)
- IP e metadados de sessão

**Dados opcionais (auto-declaração, nunca obrigatórios):**
- Setor profissional (agro, indústria, serviços, governo, academia, outro)
- Auto-declaração de tendência política (usado apenas para métricas de diversidade agregadas — nunca individual)
- Cidade

### 10.8 Onboarding

A sequência de onboarding é desenhada para entregar valor imediato e gerar a primeira ação em menos de 60 segundos após registro.

**Fluxo:**

1. **Registro** (20s): email + nome + UF. Magic link ou OAuth.
2. **"Seus deputados"** (10s): a plataforma mostra automaticamente os deputados e senadores da UF do usuário, com scores. Isso é o primeiro valor — personalizado e imediato.
3. **Primeira ação** (30s): "Quer participar da deliberação ativa?" ou "Siga as pautas que te interessam" — o sistema oferece a ação de menor atrito disponível.
4. **Tour opcional** (2 min): 4 telas explicando ranking, bússola, deliberações e como contribuir. Pode ser pulado.

**Anti-padrão:** nunca pedir mais dados no registro do que o mínimo. Nunca bloquear acesso a dados. Nunca exigir completar perfil para usar a plataforma.

### 10.9 Modelo de dados — Comunidade

```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    uf VARCHAR(2) NOT NULL,
    cpf_hash VARCHAR(64),                 -- hash, nunca plain text
    cpf_verificado BOOLEAN DEFAULT FALSE,
    papel ENUM('membro','participante','curador','lider_maintainer','lider_comite') DEFAULT 'membro',
    especialidades_zil VARCHAR[],         -- categorias ZIL (para curadores)
    setor VARCHAR(50),                    -- auto-declaração opcional
    cidade VARCHAR(100),                  -- opcional
    avatar_url VARCHAR(500),
    bio VARCHAR(500),
    
    -- Métricas de engajamento
    total_deliberacoes INTEGER DEFAULT 0,
    total_votos_polis INTEGER DEFAULT 0,
    total_declaracoes_polis INTEGER DEFAULT 0,
    total_classificacoes_propostas INTEGER DEFAULT 0,
    total_classificacoes_aceitas INTEGER DEFAULT 0,
    total_contestacoes INTEGER DEFAULT 0,
    total_cobrancas INTEGER DEFAULT 0,
    total_compartilhamentos INTEGER DEFAULT 0,
    
    -- Curadoria
    taxa_aprovacao DECIMAL(5,4),           -- classificações aceitas / propostas
    semanas_sem_revisao INTEGER DEFAULT 0,
    curador_desde TIMESTAMP,
    
    -- Meta
    ultimo_acesso TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_usuarios_uf ON usuarios(uf);
CREATE INDEX ix_usuarios_papel ON usuarios(papel);

-- Seguimentos (parlamentares, pautas)
CREATE TABLE seguimentos (
    id UUID PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios NOT NULL,
    tipo ENUM('parlamentar','pauta','proposicao','marco'),
    alvo_id UUID NOT NULL,                -- ID do parlamentar, categoria, etc.
    notificacoes BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(usuario_id, tipo, alvo_id)
);

-- Cobranças enviadas a parlamentares
CREATE TABLE cobrancas (
    id UUID PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios NOT NULL,
    parlamentar_id UUID REFERENCES parlamentares NOT NULL,
    pauta_zil VARCHAR(20),
    template_usado VARCHAR(100),
    canal ENUM('email','formulario','rede_social'),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_cobrancas_parlamentar ON cobrancas(parlamentar_id);

-- Assinaturas do manifesto
CREATE TABLE assinaturas_manifesto (
    id UUID PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios,   -- NULL se assinou sem conta (legacy)
    nome VARCHAR(255) NOT NULL,
    cidade VARCHAR(100),
    uf VARCHAR(2),
    numero INTEGER NOT NULL,               -- número sequencial da assinatura
    created_at TIMESTAMP DEFAULT NOW()
);

-- Log de progressão de papéis
CREATE TABLE progressao_log (
    id UUID PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios NOT NULL,
    papel_anterior VARCHAR(30),
    papel_novo VARCHAR(30) NOT NULL,
    motivo TEXT NOT NULL,                   -- "10 classificações aceitas", "indicação por curador X"
    aprovado_por UUID[],                   -- IDs de quem aprovou
    created_at TIMESTAMP DEFAULT NOW()
);

-- Alertas e notificações
CREATE TABLE alertas_config (
    id UUID PRIMARY KEY,
    usuario_id UUID REFERENCES usuarios NOT NULL,
    tipo ENUM('votacao_nova','proposicao_nova','score_mudou','deliberacao_aberta','marco_atualizado','cobranca_resposta'),
    canal ENUM('email','push','telegram') DEFAULT 'email',
    ativo BOOLEAN DEFAULT TRUE,
    filtro_pautas VARCHAR[],               -- NULL = todas
    filtro_ufs VARCHAR[],                  -- NULL = todas
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 10.10 Proteções de segurança e privacidade

**Dados mínimos:** o registro coleta apenas email, nome e UF. CPF é opcional e armazenado apenas como hash SHA-256 — nunca em texto plano. É usado exclusivamente para verificar unicidade em deliberações Polis (uma pessoa = um voto).

**Pseudônimo permitido:** membros podem usar pseudônimo. Curadores e líderes devem usar nome real (verificável pelo comitê, não público se o curador preferir pseudônimo público com identidade verificada internamente).

**Direito ao esquecimento:** qualquer usuário pode deletar sua conta a qualquer momento. Dados pessoais são apagados. Contribuições de curadoria permanecem (anonimizadas) para preservar integridade do dataset.

**Sem tracking comportamental:** a plataforma não vende dados, não serve ads, não rastreia comportamento para monetização. As únicas métricas coletadas são as de engajamento visíveis no perfil do próprio usuário.

**Rate limiting progressivo:** visitantes têm rate limit generoso na API. Membros têm limite maior. Curadores têm acesso sem limite. Isso previne scraping agressivo sem bloquear uso legítimo.

### 10.11 Métricas de saúde da comunidade

| Métrica | Meta 6 meses | Meta 12 meses |
|---------|:---:|:---:|
| Membros registrados | 5.000 | 50.000 |
| Participantes ativos (≥1 ação/mês) | 500 | 5.000 |
| Curadores ativos | 10 | 30 |
| Conversão visitante → membro | 5% | 8% |
| Conversão membro → participante | 20% | 30% |
| Retenção mensal (membros que voltam) | 40% | 55% |
| Diversidade geográfica (UFs com curadores) | 10 | 20 |
| Deliberações com ≥100 participantes | 2 | 6 |
| NPS da comunidade | — | ≥ 50 |

---

## 11. Fontes de Dados

### 9.1 Fontes primárias

| Fonte | URL | Formato | Atualização | Dados |
|-------|-----|---------|-------------|-------|
| Câmara dos Deputados | `dadosabertos.camara.leg.br/api/v2` | JSON/CSV | Diária | Deputados, votações, proposições, despesas, frentes |
| Senado Federal | `legis.senado.leg.br/dadosabertos` | XML/JSON | Diária | Senadores, matérias, votações, comissões |
| TSE | `dadosabertos.tse.jus.br` | CSV bulk | Por ciclo eleitoral | Candidatos, prestação de contas, resultados, filiação |
| Portal da Transparência | `portaldatransparencia.gov.br/api-de-dados` | JSON | Diária | Gastos federais, convênios, viagens |
| Querido Diário | `queridodiario.ok.org.br/api` | JSON | Diária | Diários oficiais de 2.800+ municípios |

### 9.2 Fontes complementares

| Fonte | Uso | Acesso |
|-------|-----|--------|
| CEPESP-FGV | Dados TSE processados com API REST | `github.com/Cepesp-Fgv/cepesp-rest` |
| Brasil.IO | Receita Federal (CNPJ, QSA) processada | `brasil.io/datasets` |
| Google News RSS | Notícias por parlamentar/pauta | RSS feed parametrizado |
| Perfis de parlamentares em redes sociais | Posicionamento público | APIs do X/Twitter, Instagram, YouTube |

### 9.3 Frequência de ingestão

| Fonte | Frequência | Método |
|-------|-----------|--------|
| Câmara — votações | A cada 6 horas | API polling |
| Câmara — proposições | Diária | API polling + bulk download |
| Câmara — deputados | Semanal | API polling |
| Senado — votações | A cada 6 horas | API polling |
| Senado — matérias | Diária | API polling |
| TSE | Semanal (eleitoral: diária) | Bulk download + parse |
| News | A cada 2 horas | RSS + scraping |

---

## 12. Arquitetura Técnica

### 12.1 Stack

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Frontend | **Next.js 14 + React** | SSR para SEO e compartilhamento social. PWA para mobile. |
| Estilo | **Tailwind CSS** | Componentes utilitários rápidos, responsivos |
| API | **FastAPI (Python 3.12)** | Async nativo, tipagem, auto-documentação OpenAPI |
| Banco | **PostgreSQL 16** | JSONB, full-text search nativo, estável, open source |
| Cache | **Redis** | Cache de API, rate limiting, filas Celery |
| Busca | **Typesense** | Full-text search open source, facets, typo-tolerant |
| Workers | **Celery + Redis** | Ingestão assíncrona, scheduling |
| NLP | **sentence-transformers + spaCy pt** | Classificação semântica, NER |
| Auth | **NextAuth.js** | OAuth (Google, GitHub), magic link |
| Infra | **Docker Compose** | Dev local simples. Produção: VPS → k8s quando escalar |
| CI/CD | **GitHub Actions** | Testes, lint, build, deploy automático |
| Monitoramento | **Sentry + Prometheus** | Erros, métricas |

### 12.2 Estrutura do repositório

```
zil-observatorio/
│
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── app/                # App router (pages)
│   │   ├── components/         # Componentes React
│   │   ├── lib/                # Utilitários, API client
│   │   └── public/             # Assets estáticos
│   │
│   ├── api/                    # FastAPI backend
│   │   ├── routers/            # Endpoints por domínio
│   │   ├── services/           # Lógica de negócio
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   └── core/               # Config, auth, deps
│   │
│   └── workers/                # Celery workers
│       ├── crawlers/           # Ingestão por fonte
│       ├── classifiers/        # NLP pipeline
│       ├── scoring/            # Score engine
│       └── tasks.py            # Task definitions
│
├── packages/
│   ├── camara-client/          # Client tipado para API Câmara
│   ├── senado-client/          # Client tipado para API Senado
│   ├── tse-importer/           # Parser de dados TSE
│   └── shared/                 # Tipos compartilhados
│
├── data/
│   ├── taxonomia/              # Definições de pautas ZIL (YAML)
│   ├── classificacoes/         # Classificações manuais (auditoria)
│   ├── seeds/                  # Dados iniciais para dev
│   └── migrations/             # Alembic migrations
│
├── docs/
│   ├── PRD.md                  # Este documento
│   ├── ARCHITECTURE.md         # Detalhamento técnico
│   ├── DATA_SOURCES.md         # Guia de fontes de dados
│   ├── SCORING.md              # Metodologia do score
│   ├── CONTRIBUTING.md         # Como contribuir
│   ├── CODE_OF_CONDUCT.md      # Código de conduta
│   └── ADR/                    # Architecture Decision Records
│
├── scripts/
│   ├── setup.sh                # Setup do ambiente dev
│   └── seed.sh                 # Popular banco com dados iniciais
│
├── docker-compose.yml          # Dev environment completo
├── docker-compose.prod.yml     # Produção
├── Makefile                    # Comandos comuns
├── LICENSE                     # AGPL-3.0
└── README.md                   # Entrada principal
```

---

## 13. Modelo de Dados

Veja o schema completo em `docs/ARCHITECTURE.md`. As entidades principais:

| Entidade | Descrição | Fonte |
|----------|-----------|-------|
| `parlamentares` | Deputados e senadores com perfil unificado | Câmara + Senado |
| `proposicoes` | PLs, PECs, requerimentos com classificação ZIL | Câmara + Senado |
| `votacoes` | Votações em plenário e comissões | Câmara + Senado |
| `votos` | Voto individual de cada parlamentar em cada votação | Câmara + Senado |
| `financiamentos` | Receitas e despesas de campanha | TSE |
| `scores_votacao` | Score granular por parlamentar/votação/categoria | Calculado |
| `compromissos` | Compromissos públicos registrados por parlamentares | Plataforma |
| `marcos_zil` | Marcos estratégicos intergovernamentais com status | Plataforma + fontes oficiais |
| `continuidade` | Índice de continuidade por governo/programa | Calculado |
| `usuarios` | Perfis de membros com papel, métricas e especialidades | Plataforma |
| `seguimentos` | Parlamentares, pautas e marcos seguidos por cada usuário | Plataforma |
| `cobrancas` | Cobranças enviadas por cidadãos a parlamentares | Plataforma |
| `assinaturas_manifesto` | Registro público de assinaturas do manifesto | Plataforma |
| `progressao_log` | Histórico imutável de mudanças de papel de cada usuário | Plataforma |
| `deliberacoes` | Processos Polis com clusters, declarações-ponte e resultados | Plataforma |
| `classificacoes` | Log de todas as classificações e contestações | Plataforma |
| `discussoes` | Posts do fórum comunitário | Plataforma |
| `alertas_config` | Configurações de notificação por usuário, canal e pauta | Plataforma |

---

## 14. Roadmap

### Fase 0 — Setup (semanas 1-2)
- [ ] Criar repositório GitHub com estrutura definida
- [ ] Docker Compose com PostgreSQL + Redis + FastAPI + Next.js
- [ ] CI/CD básico (GitHub Actions: lint + testes + build)
- [ ] README, CONTRIBUTING, CODE_OF_CONDUCT, LICENSE
- [ ] Deploy de staging em VPS

### Fase 1 — Tracer Bullet (semanas 2-6)
- [ ] Client da API da Câmara: ingestão dos 513 deputados
- [ ] Worker de votações: todas as votações de 2025-2026
- [ ] Classificador baseline (regex + keywords) para pautas ZIL
- [ ] Score ZIL v0 calculado para todos os deputados
- [ ] Frontend: ranking de deputados, perfil com votos, busca
- [ ] Registro de usuário (email + UF + magic link) e painel "meus deputados"
- [ ] Assinatura do manifesto integrada ao registro
- [ ] Deploy público do alpha

### Fase 2 — Completude (semanas 6-12)
- [ ] Client da API do Senado: ingestão de senadores e votações
- [ ] Classificador NLP (sentence-transformers)
- [ ] Painel de proposições com status de tramitação
- [ ] Importador TSE (financiamento de campanha)
- [ ] Cards compartilháveis (Open Graph)
- [ ] PWA básico (mobile)
- [ ] Sistema de seguimento (seguir parlamentares, pautas, marcos)
- [ ] Notificações por email (votação nova, score mudou)
- [ ] "Cobrar meu deputado" — templates e envio

### Fase 3 — Inteligência (semanas 12-24)
- [ ] Grafo de influência (parlamentar ↔ doador ↔ setor)
- [ ] Alertas em tempo real (email, push, Telegram)
- [ ] Comparativo entre parlamentares
- [ ] API pública documentada
- [ ] Dashboard agregado (visão nacional)
- [ ] Progressão de papéis: membro → participante (automática por ações)
- [ ] Interface de curadoria: fila de classificações pendentes
- [ ] Perfil público de usuário com badges e métricas

### Fase 4 — Comunidade (semanas 24-36)
- [ ] Fórum de discussão vinculado a proposições
- [ ] Curadoria comunitária completa: proposição → revisão → aprovação
- [ ] Progressão para curador com verificação e especialidade temática
- [ ] Deliberações Polis integradas (self-hosted)
- [ ] Campanhas de pressão (templates, cobranças, contadores)
- [ ] Monitor eleitoral 2026
- [ ] Painel de saúde da comunidade (diversidade, retenção, atividade)

### Marco crítico
**Julho de 2026**: plataforma deve estar plenamente funcional com Fases 1-3 completas, para impacto no período eleitoral.

---

## 15. Modelo Open Source

### 17.1 Licença

**AGPL-3.0** (GNU Affero General Public License v3.0)

Escolhida porque:
- Garante que forks e modificações permaneçam open source
- Inclui cláusula "network use" — se alguém usa o código para servir uma plataforma web, deve abrir o código
- Permite uso comercial desde que o código derivado seja aberto
- Compatível com a maioria das libs do ecossistema Python/JS

Os dados públicos gerados pela plataforma (scores, classificações, datasets) são licenciados sob **CC BY-SA 4.0**.

### 17.2 Financiamento

O projeto busca sustentabilidade sem comprometer independência:

- **Doações individuais**: Apoia.se, GitHub Sponsors, Pix
- **Grants de fundações**: Open Society, Luminate, Ford Foundation, Omidyar Network (todos financiam civic tech na América Latina)
- **Editais públicos**: MCTI, CGU (transparência pública)
- **Nunca**: financiamento de partidos políticos, empresas com lobby ativo no Congresso, ou governos estrangeiros

### 17.3 Infraestrutura

- **Dev**: Docker Compose local (zero custo)
- **Staging**: VPS na Hetzner ou Contabo (~€15/mês)
- **Produção inicial**: VPS dedicada (~€50-100/mês)
- **Escala**: Kubernetes em cloud provider (quando justificável)
- **CDN**: Cloudflare (free tier)
- **DNS/Domain**: `zilobservatorio.org` ou similar

---

## 16. Como Contribuir

### 17.1 Primeiros passos

```bash
# 1. Fork e clone
git clone https://github.com/SEU_USUARIO/zil-observatorio.git
cd zil-observatorio

# 2. Setup do ambiente
make setup  # ou: docker compose up -d

# 3. Popular banco com dados de seed
make seed

# 4. Rodar testes
make test

# 5. Acessar
# Frontend: http://localhost:3000
# API: http://localhost:8000/docs
```

### 17.2 Tipos de contribuição

| Tipo | Skill necessário | Label no GitHub |
|------|-----------------|-----------------|
| Código backend (API, workers, crawlers) | Python, FastAPI, SQLAlchemy | `backend` |
| Código frontend (interface, componentes) | React, Next.js, Tailwind | `frontend` |
| Pipeline de dados (ingestão, parsing) | Python, APIs REST, ETL | `data-pipeline` |
| NLP (classificação, embeddings) | Python, NLP, ML | `nlp` |
| Curadoria de dados (classificar proposições) | Conhecimento legislativo | `curadoria` |
| Design (UI/UX, identidade visual) | Figma, design system | `design` |
| Documentação | Escrita técnica | `docs` |
| Testes | Python/JS testing | `testing` |
| DevOps (CI/CD, infra) | Docker, GitHub Actions | `devops` |
| Análise (reportagens, insights) | Jornalismo de dados | `analise` |

### 17.3 Workflow

1. Escolha uma issue com label `good-first-issue` ou `help-wanted`
2. Comente na issue que você vai trabalhar nela
3. Crie um branch: `feat/nome-descritivo` ou `fix/nome-descritivo`
4. Faça commits atômicos com mensagens claras (Conventional Commits)
5. Abra um Pull Request referenciando a issue
6. Aguarde review de pelo menos 1 maintainer
7. Após aprovação, o PR é mergeado via squash

### 17.4 Padrões de código

- **Python**: black + ruff + mypy (strict). Tipagem obrigatória.
- **TypeScript**: eslint + prettier. Strict mode.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **PRs**: template com checklist (testes, docs, screenshots se UI)
- **Issues**: templates por tipo (bug, feature, data, curadoria)

### 17.5 Comunicação

- **GitHub Issues**: discussões técnicas e feature requests
- **GitHub Discussions**: perguntas, ideias, RFC
- **Discord/Telegram**: comunicação em tempo real (link no README)
- **Reuniões**: weekly sync aberta (gravada e publicada)

---

## 17. Governança

### 17.1 Estrutura

**Maintainers (3-5 pessoas)**
- Acesso de merge ao `main`
- Decidem prioridades técnicas e releases
- Rotação anual (pelo menos 1 membro novo por ano)

**Comitê Editorial (5-9 pessoas)**
- Validam classificações de proposições por pauta ZIL
- Definem a "direção esperada" das votações
- Publicam justificativas para decisões controversas
- Mandato de 12 meses, renováveis

**Contribuidores**
- Qualquer pessoa que tenha PR mergeado ou contribuição reconhecida
- Direito a voto em decisões comunitárias (ADRs, prioridades)

### 17.2 Tomada de decisão

- **Decisões técnicas**: propostas via ADR (Architecture Decision Record), discutidas em issue, decididas por consenso dos maintainers
- **Decisões editoriais**: propostas pelo comitê, período de comentário público de 7 dias, decisão por maioria do comitê
- **Decisões de governança**: propostas via RFC, votação da comunidade (contribuidores ativos nos últimos 6 meses)

### 17.3 Código de conduta

O projeto adota o Contributor Covenant v2.1. Resumo:
- Comportamento respeitoso e inclusivo
- Zero tolerância para assédio, discriminação, doxxing
- Foco em dados e argumentos, não em ataques pessoais
- Discussões sobre parlamentares devem ser factuais e baseadas em dados
- Violações são reportadas aos maintainers e tratadas conforme severity

---

## 18. Riscos e Mitigações

| Risco | Prob. | Impacto | Mitigação |
|-------|:-----:|:-------:|-----------|
| APIs governamentais instáveis ou mudam | Alta | Alto | Cache agressivo (Redis), múltiplos parsers, fallback para bulk download, testes de integração diários |
| Acusação de viés político | Alta | Alto | Transparência radical: toda classificação auditável, comitê editorial diverso, mecanismo de contestação pública |
| Perda de momentum da comunidade | Média | Alto | Releases frequentes, comunicação constante, gamificação, onboarding fácil |
| Ataques DDoS ou tentativa de censura | Média | Médio | Cloudflare CDN, rate limiting, infra distribuída, mirrors do dataset |
| Dados inconsistentes entre fontes | Alta | Médio | Pipeline de reconciliação, IDs canônicos, auditoria cruzada automatizada |
| Custo de infra insustentável | Média | Médio | Começar em VPS barata, migrar conforme escala; doações + grants |
| Uso indevido da plataforma para propaganda | Média | Médio | Moderação comunitária, políticas claras, separação dado vs. opinião |
| Processo judicial por parlamentar | Baixa | Alto | Todos os dados são públicos e de fonte oficial; nenhuma afirmação é editorial (tudo é calculado por fórmula transparente); assessoria jurídica preventiva |

---

## 19. Precedentes e Referências

| Projeto | País | O que faz | Lição para ZIL |
|---------|------|-----------|-----------------|
| **Operação Serenata de Amor** | Brasil | IA para auditar gastos de parlamentares | Demonstrou viabilidade técnica. Perdeu momentum por falta de ação comunitária. ZIL precisa ser plataforma de ação, não só informação. |
| **Elas no Congresso** (AzMina) | Brasil | Monitora PLs sobre gênero | Provou que monitoramento temático automatizado funciona com equipe pequena. |
| **Querido Diário** (OKBR) | Brasil | Indexa diários oficiais municipais | Modelo de comunidade open source sustentável em civic tech brasileira. |
| **GovTrack.us** | EUA | Tracka todo o Congresso americano | Interface simples + dados profundos = adoção massiva. Referência de UX. |
| **TheyWorkForYou** | UK | Monitoramento parlamentar britânico | Modelo de apresentação de dados legislativos para cidadão leigo. |
| **OpenSecrets** | EUA | Financiamento de campanha e lobby | Referência para cruzamento financiamento ↔ votação. |

---

## 20. Métricas de Sucesso

### 19.1 Métricas de produto

| Métrica | Meta 6 meses | Meta 12 meses |
|---------|:------------:|:-------------:|
| Parlamentares com score calculado | 594 (100%) | 594 (100%) |
| Proposições classificadas | 500+ | 2.000+ |
| Votações no score | 50+ | 200+ |
| Tempo de atualização após votação | < 24h | < 6h |
| Uptime da plataforma | 99% | 99.5% |

### 19.2 Métricas de comunidade

| Métrica | Meta 6 meses | Meta 12 meses |
|---------|:------------:|:-------------:|
| Assinaturas do manifesto | 50.000 | 500.000 |
| Visitantes únicos mensais | 10.000 | 100.000 |
| Contribuidores no GitHub | 30 | 100 |
| Stars no GitHub | 500 | 3.000 |
| Cobranças enviadas a parlamentares | — | 10.000/mês |

### 19.3 Métricas de impacto

| Métrica | Meta 12 meses |
|---------|:-------------:|
| Citações em mídia | 10 veículos nacionais |
| Parlamentares que mencionam/respondem | 20 |
| Uso por organizações da sociedade civil | 5 organizações |
| Contribuição para debate eleitoral 2026 | Presente em pelo menos 1 debate presidencial |

---

## 21. FAQ

**P: Por que "ZIL"?**
R: Zero dependência estratégica, Indústria nacional, Liderança soberana. É o nome do manifesto que originou o projeto — um documento apartidário pela soberania industrial do Brasil.

**P: Isso é de esquerda ou de direita?**
R: Nem um nem outro. Soberania industrial é uma pauta que une espectros: o agro quer fertilizante nacional barato, a indústria quer competitividade, os militares querem autossuficiência, os ambientalistas querem monitoramento soberano. O critério não é ideologia — é se o Brasil processa o que extrai ou exporta matéria-prima barata.

**P: Quem define o que é "pró-soberania"?**
R: Um comitê editorial composto por especialistas de diversas áreas, com processo de curadoria comunitária e transparência total. Toda classificação é auditável e contestável publicamente.

**P: Vocês recebem dinheiro de partido ou governo?**
R: Não. O financiamento vem de doações individuais e grants de fundações independentes. Nunca aceitaremos dinheiro de partidos, empresas com lobby ativo, ou governos.

**P: Posso usar os dados para minha pesquisa/reportagem?**
R: Sim. A API é pública e os dados são licenciados sob CC BY-SA 4.0. Pedimos apenas atribuição.

**P: Como posso contribuir sem saber programar?**
R: Curando dados (classificando proposições), participando do fórum, compartilhando scores nas redes, ou ajudando com design e redação. Veja a seção "Como Contribuir".

**P: Isso não vai ser usado para perseguir políticos?**
R: A plataforma publica exclusivamente dados que já são públicos, organizados por fórmula transparente. Não fazemos acusações, não atribuímos intenção, não publicamos informação privada. Exibimos como cada parlamentar votou — informação que é direito de todo cidadão.

**P: Como funciona o sistema de compromissos?**
R: Qualquer parlamentar pode registrar um compromisso público na plataforma — por exemplo, "vou votar a favor da PL X." O compromisso é registrado com hash imutável. Quando a votação acontece, a plataforma verifica automaticamente se o voto foi consistente. O Índice de Cumprimento mostra o percentual de compromissos honrados. É voluntário — mas a pressão social para participar cresce conforme mais parlamentares aderem.

**P: O que são os Marcos ZIL?**
R: São objetivos estratégicos mensuráveis com prazo que independem de governo — como "reduzir dependência de fertilizantes para 70% até 2028." Cada marco tem uma fonte oficial de dados (ANDA, ANATEL, ANM) que a plataforma consulta trimestralmente. Quando um governo muda, os marcos permanecem, e a plataforma mostra se houve avanço, estagnação ou retrocesso. É a bússola de longo prazo do país.

**P: Por que "Projeto de Estado, não de Governo"?**
R: Porque o Brasil já tem a capacidade técnica — o PIX, a Embraer, o Plano Real provam isso. O que falta é continuidade. O Nova Indústria Brasil é o quinto programa industrial desde 2003. A plataforma cria mecanismos para que a descontinuidade tenha custo político visível: índices de continuidade, compromissos rastreáveis, e marcos que não mudam quando o governo muda.

---

## Apêndice: Contato e Links

- **Repositório**: `github.com/zil-observatorio/zil-observatorio`
- **Manifesto ZIL**: (link do site do manifesto)
- **Discord/Telegram**: (link da comunidade)
- **Email**: contato@zilobservatorio.org

---

*Este PRD é um documento vivo. Última atualização: março de 2026. Contribuições são bem-vindas via Pull Request.*

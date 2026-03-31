# ZIL Observatório — Sistema de Governança e Consenso

## O problema que estamos resolvendo

O ZIL precisa que pessoas com crenças políticas opostas concordem em pautas concretas. Isso é o oposto do que redes sociais fazem — plataformas convencionais amplificam discordância porque engajamento polarizado gera mais cliques. O ZIL precisa de uma arquitetura que amplifique convergência.

O modelo de referência é o vTaiwan/Polis, que provou em escala nacional que é possível encontrar consenso entre grupos politicamente opostos quando o sistema é desenhado para isso. Em Taiwan, o processo gerou legislação sobre regulação do Uber, fintech, e revenge porn — temas onde a polarização era intensa — e mais de 80% das deliberações resultaram em ação governamental.

A premissa do ZIL é a mesma: soberania industrial é um ponto de Schelling — um lugar onde pessoas que discordam sobre quase tudo convergem porque o interesse é compartilhado. O agricultor conservador e o sindicalista progressista concordam que fertilizante importado a US$26 bilhões/ano é absurdo. O sistema precisa revelar essa convergência ao invés de enterrá-la.

---

## Princípios de design do sistema

### 1. Consenso como produto, não como subproduto

O sistema não busca consenso como consequência de debate — ele é engenheirado para produzi-lo. Cada mecanismo de interação é avaliado pela pergunta: "isso aumenta ou diminui a probabilidade de convergência entre grupos diferentes?"

### 2. Sem respostas a respostas

O insight central do Polis: quando pessoas podem responder a comentários, a dinâmica se torna adversarial. Quando só podem concordar, discordar ou propor, a dinâmica se torna construtiva. O ZIL adota essa restrição em seus processos deliberativos.

### 3. Visibilidade pelo consenso, não pela polarização

Declarações que geram acordo entre grupos opostos recebem mais visibilidade. Declarações que dividem exatamente ao meio são sinalizadas como "divisivas" e movidas para segundo plano. O algoritmo recompensa pontes, não trincheiras.

### 4. Transparência processual absoluta

Todo processo — como um marco foi definido, como uma classificação foi decidida, como um princípio foi adotado — é público, rastreável e auditável. A legitimidade vem do processo, não da autoridade.

### 5. Governança gradual (escalation by necessity)

Nem tudo precisa de votação formal. A maioria das decisões operacionais é feita por rough consensus (modelo IETF). Processos formais de deliberação são reservados para decisões estratégicas — novos princípios, novos marcos, classificações controversas.

---

## Arquitetura de governança em camadas

O sistema opera em quatro camadas, da mais leve à mais pesada:

```
Camada 4 — DELIBERAÇÃO POLIS    ← Decisões estratégicas (princípios, marcos, classificações controversas)
Camada 3 — PROPOSTA E VOTAÇÃO   ← Novas funcionalidades, prioridades, reclassificações
Camada 2 — CURADORIA             ← Classificação de proposições, validação de dados
Camada 1 — CONTRIBUIÇÃO          ← Código, documentação, análise, design
```

### Camada 1: Contribuição (dia a dia)

Modelo: open source padrão com rough consensus.

Qualquer pessoa pode contribuir código, documentação, design ou análise via Pull Request. PRs precisam de aprovação de 1 maintainer. Decisões são tomadas por consenso entre maintainers — se não há objeção em 72 horas, a decisão é aceita.

Decisões nesta camada: merge de PRs, correção de bugs, refatoração, documentação, issues operacionais.

### Camada 2: Curadoria (classificação e validação)

Modelo: curadoria distribuída com revisão por pares.

Curadores são contribuidores que demonstraram capacidade de classificar proposições legislativas com qualidade. Qualquer contribuidor pode se tornar curador após 10 classificações validadas pelo comitê editorial.

Decisões nesta camada: classificar proposições em pautas ZIL, definir a "direção esperada" de votações, validar classificações automáticas do NLP.

Processo:
1. Curador propõe classificação com justificativa textual
2. Dois outros curadores revisam (concordam ou contestam)
3. Se há concordância, a classificação é aplicada
4. Se há contestação, escala para o comitê editorial
5. Se o comitê diverge, escala para deliberação da comunidade

Regra de ouro: na dúvida, não classificar. Falso positivo (classificar errado) é pior que falso negativo (deixar de classificar).

### Camada 3: Proposta e Votação (decisões de produto)

Modelo: RFC (Request for Comments) com votação ponderada.

Decisões sobre funcionalidades, prioridades, e reclassificações são feitas via processo RFC:

1. **Proposta (7 dias):** autor publica RFC em GitHub Discussions com contexto, proposta, alternativas consideradas e impacto esperado
2. **Discussão (14 dias):** comunidade comenta. Moderadores sintetizam pontos de convergência e divergência
3. **Votação (7 dias):** contribuidores ativos nos últimos 6 meses votam. Aprovação requer 66% de favoráveis com quórum mínimo de 20% dos elegíveis
4. **Implementação:** se aprovado, entra no backlog priorizado

Decisões nesta camada: novas funcionalidades, mudanças na taxonomia, adição de novas categorias ZIL, prioridades do roadmap, mudanças na metodologia do score.

Ponderação de voto: todos os contribuidores ativos têm peso igual. Não há voto ponderado por quantidade de contribuições — isso evita que poucos contribuidores de alto volume dominem. Um curador de dados tem o mesmo peso que um desenvolvedor sênior.

### Camada 4: Deliberação Polis (decisões estratégicas)

Modelo: wiki survey estilo Polis para encontrar consenso transversal.

Para as decisões mais importantes — novos princípios do manifesto, novos marcos estratégicos, posicionamento em temas controversos, revisões do modelo de governança — o ZIL usa um processo de deliberação inspirado no vTaiwan.

O processo funciona assim:

**Fase 1 — Coleta de declarações (7 dias)**

Um tema é aberto na plataforma. Qualquer usuário registrado (não apenas contribuidores) pode submeter declarações curtas (até 140 caracteres). Não é possível responder a declarações de outros — apenas submeter as suas.

Exemplos de declarações sobre o tema "O Brasil deveria banir exportação de nióbio bruto?":
- "Sim, nióbio bruto exportado é riqueza transferida"
- "Não, isso prejudica exportadores e quebra contratos"
- "Deveria exigir 50% de processamento local, não banir totalmente"
- "Primeiro precisa ter capacidade de processamento antes de banir"

**Fase 2 — Votação e clusterização (14 dias)**

Usuários votam nas declarações: concordo, discordo, ou passo. O sistema usa agrupamento (k-means) para identificar clusters de opinião — grupos de pessoas que tendem a votar de forma similar.

O painel mostra em tempo real:
- Quantos grupos de opinião existem
- Quais declarações são consensuais (alto acordo entre todos os grupos)
- Quais são divisivas (dividem os grupos)
- Quais são "pontes" (têm apoio de múltiplos grupos que discordam entre si)

As **declarações ponte** são o produto mais valioso do processo: são as proposições que geram acordo entre pessoas que discordam sobre quase tudo. Essas declarações recebem destaque visual e são priorizadas na fase seguinte.

**Fase 3 — Síntese e ratificação (7 dias)**

Moderadores sintetizam as declarações ponte e consensuais em uma proposta coerente. A proposta é publicada com a visualização dos clusters e o mapa de consenso. A comunidade tem 7 dias para ratificar ou solicitar revisão.

Se ratificada, a proposta se torna parte do manifesto, do conjunto de marcos, ou da política da plataforma.

**Implementação técnica**

O ZIL integra o Polis como componente open source (licença AGPLv3). A instância é auto-hospedada para garantir soberania dos dados — não usamos a instância pública do pol.is para processos que envolvem dados de cidadãos brasileiros.

Alternativa: se a integração direta com Polis for complexa inicialmente, o MVP pode usar uma implementação simplificada com o mesmo princípio — submissão de declarações → votação concordo/discordo → clusterização por k-means → identificação de declarações ponte.

---

## Papéis e responsabilidades

### Contribuidor
- Qualquer pessoa com PR mergeado ou contribuição reconhecida
- Direitos: voto em RFCs, participação em deliberações Polis, acesso ao fórum
- Requisito: pelo menos 1 contribuição aceita nos últimos 6 meses para direito a voto

### Curador
- Contribuidor com expertise em classificação legislativa
- Direitos: classificar proposições, validar classificações automáticas, propor reclassificações
- Requisito: 10 classificações validadas pelo comitê editorial + aprovação de 2 curadores existentes

### Maintainer (3-5 pessoas)
- Acesso de merge ao branch principal
- Responsável por: prioridades técnicas, releases, moderação, resolução de impasses
- Seleção: indicação por maintainer existente + aprovação por RFC da comunidade
- Mandato: 12 meses, renováveis. Pelo menos 1 rotação por ano
- Remoção: por inatividade (>3 meses) ou por RFC da comunidade (66% + quórum 30%)

### Comitê Editorial (5-9 pessoas)
- Validam classificações em última instância
- Definem a "direção esperada" de votações
- Composto por: economistas, engenheiros, diplomatas, acadêmicos, representantes do agro e da indústria
- Diversidade obrigatória: pelo menos 2 membros de espectros políticos diferentes, pelo menos 2 de fora do eixo Rio-SP
- Mandato: 12 meses, renováveis
- Seleção: indicação aberta + deliberação Polis da comunidade
- Todas as decisões são publicadas com justificativa

### Moderador de Deliberação
- Facilita processos Polis e RFCs
- Sintetiza resultados de deliberações
- Garante que regras processuais são seguidas
- Não tem poder de voto adicional — é facilitador, não decisor

---

## Processos específicos

### Como propor um novo princípio para o manifesto

1. Autor publica RFC com: contexto, princípio proposto, justificativa, impacto esperado
2. Discussão aberta por 14 dias
3. Se houver apoio preliminar (>10 reações positivas), abre-se deliberação Polis com tema amplo ("Que princípios devem guiar a industrialização do Brasil?")
4. Declarações ponte e consensuais da deliberação Polis são sintetizadas
5. Proposta final é submetida a votação: aprovação requer 75% + quórum de 25%
6. Se aprovada, entra no manifesto na próxima versão

### Como propor um novo marco estratégico

1. Autor publica RFC com: título do marco, métrica verificável, fonte de dados oficial, prazo, justificativa
2. Comitê editorial valida que a métrica é verificável e a fonte é confiável
3. Discussão aberta por 14 dias
4. Votação: aprovação requer 66% + quórum 20%
5. Se aprovado, entra no painel de marcos e começa a ser monitorado trimestralmente

### Como contestar uma classificação

1. Qualquer usuário registrado pode abrir contestação com justificativa
2. Dois curadores revisam
3. Se ambos concordam com a contestação, a classificação é revertida
4. Se discordam, o comitê editorial decide
5. Se o comitê diverge internamente (3-3 ou similar), abre-se micro-deliberação Polis (3 dias)
6. Todas as contestações e decisões ficam no log público

### Como resolver um impasse

Quando nenhum processo anterior resolve uma divergência:

1. Moderador sintetiza as posições em disputa (máximo 3 posições)
2. Abre-se deliberação Polis focada no impasse (7 dias)
3. Se declarações ponte emergirem, moderador propõe resolução baseada nelas
4. Se nenhum consenso emergir, a opção padrão é "não agir" — manter o status quo
5. O impasse pode ser reaberto após 90 dias com novas informações

Princípio: o ônus é de quem quer mudar, não de quem quer manter. Isso evita que o sistema seja capturado por minorias ativas.

---

## Proteções contra captura

### Captura partidária

Risco: um grupo político organizado se infiltra na comunidade para classificar votações a favor de um partido.

Mitigações:
- Toda classificação tem justificativa pública e é auditável
- Comitê editorial com diversidade política obrigatória
- Deliberações Polis são abertas a qualquer usuário registrado (não apenas contribuidores), diluindo poder de bloco
- Flag automático quando padrão de classificação correlaciona fortemente com posição partidária

### Captura por volume

Risco: poucos contribuidores muito ativos dominam decisões.

Mitigações:
- Voto igual independente de volume de contribuição
- Quórum mínimo em votações (precisa de participação ampla, não apenas dos mais ativos)
- Rotação obrigatória de maintainers
- Nenhum indivíduo pode ser maintainer e membro do comitê editorial simultaneamente

### Captura por inércia

Risco: grupo fundador se perpetua e resiste a mudanças.

Mitigações:
- Mandatos com prazo e rotação obrigatória
- Qualquer membro da comunidade pode propor RFC de mudança de governança
- Processo de remoção de maintainers por voto comunitário
- Código de conduta com enforcement independente dos maintainers

### Manipulação de deliberações Polis

Risco: bots ou contas falsas distorcem resultados de deliberações.

Mitigações:
- Verificação de identidade para participação em deliberações (CPF + email, sem publicação do CPF)
- Rate limiting na submissão de declarações (máximo 5 por deliberação)
- Detecção de padrões de votação anômala (votação em bloco, velocidade não-humana)
- Peso zero para contas criadas nas últimas 48 horas antes de uma deliberação

---

## Implementação técnica

### Stack de governança

| Componente | Ferramenta | Função |
|-----------|-----------|--------|
| Discussão assíncrona | GitHub Discussions | RFCs, propostas, debates técnicos |
| Deliberação | Polis (self-hosted) | Consenso transversal em temas estratégicos |
| Votação formal | GitHub Polls + bot customizado | RFCs, eleições de papéis |
| Curadoria | Interface ZIL customizada | Classificação, revisão, contestação |
| Comunicação real-time | Discord / Telegram | Coordenação diária, pareamento |
| Atas e decisões | Repositório `docs/decisions/` | ADRs, atas de comitê, logs de deliberação |
| Transparência | Dashboard público na plataforma | Status de todos os processos ativos |

### Modelo de dados — Governança

```sql
-- Deliberações Polis
CREATE TABLE deliberacoes (
    id UUID PRIMARY KEY,
    titulo VARCHAR NOT NULL,
    descricao TEXT NOT NULL,
    tipo ENUM('principio','marco','classificacao','governanca','pauta'),
    fase ENUM('coleta','votacao','sintese','ratificacao','concluida','cancelada'),
    data_inicio TIMESTAMP NOT NULL,
    data_fim_coleta TIMESTAMP,
    data_fim_votacao TIMESTAMP,
    data_fim_ratificacao TIMESTAMP,
    resultado TEXT,                     -- síntese final
    declaracoes_ponte JSONB,            -- declarações com consenso transversal
    clusters JSONB,                     -- mapa de grupos de opinião
    total_participantes INTEGER DEFAULT 0,
    total_declaracoes INTEGER DEFAULT 0,
    total_votos INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Declarações em deliberações
CREATE TABLE declaracoes (
    id UUID PRIMARY KEY,
    deliberacao_id UUID REFERENCES deliberacoes NOT NULL,
    autor_id UUID NOT NULL,
    texto VARCHAR(280) NOT NULL,        -- limite de 280 caracteres
    votos_concordo INTEGER DEFAULT 0,
    votos_discordo INTEGER DEFAULT 0,
    votos_passo INTEGER DEFAULT 0,
    score_consenso DECIMAL(4,3),        -- 0.0 a 1.0 (calculado pelo algoritmo)
    score_ponte DECIMAL(4,3),           -- alto = acordo entre clusters opostos
    is_ponte BOOLEAN DEFAULT FALSE,
    cluster_origem INTEGER,             -- cluster do autor
    created_at TIMESTAMP DEFAULT NOW()
);

-- Votos em declarações
CREATE TABLE votos_deliberacao (
    id UUID PRIMARY KEY,
    declaracao_id UUID REFERENCES declaracoes NOT NULL,
    usuario_id UUID NOT NULL,
    voto ENUM('concordo','discordo','passo') NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(declaracao_id, usuario_id)
);

-- RFCs
CREATE TABLE rfcs (
    id UUID PRIMARY KEY,
    numero INTEGER NOT NULL UNIQUE,
    autor_id UUID NOT NULL,
    titulo VARCHAR NOT NULL,
    corpo TEXT NOT NULL,
    tipo ENUM('feature','taxonomia','marco','principio','governanca'),
    status ENUM('rascunho','discussao','votacao','aprovado','rejeitado','retirado'),
    votos_favor INTEGER DEFAULT 0,
    votos_contra INTEGER DEFAULT 0,
    quorum_atingido BOOLEAN DEFAULT FALSE,
    deliberacao_id UUID REFERENCES deliberacoes,  -- se escalou para Polis
    github_discussion_url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Log de decisões (imutável)
CREATE TABLE decisoes_log (
    id UUID PRIMARY KEY,
    tipo ENUM('classificacao','reclassificacao','marco','principio','governanca','role'),
    descricao TEXT NOT NULL,
    justificativa TEXT NOT NULL,
    decidido_por VARCHAR NOT NULL,       -- 'comite', 'rfc_123', 'deliberacao_456'
    votos_registrados JSONB,
    referencia_id UUID,                  -- ID do objeto afetado
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Fases de implementação

### MVP (mês 1-3): Governança mínima viável

- GitHub Discussions para RFCs e debate
- Classificação com revisão por 2 curadores
- Comitê editorial de 5 fundadores
- Decisões por rough consensus dos maintainers
- Log de decisões em Markdown no repositório

### v1 (mês 3-6): Processos formais

- Sistema de votação para RFCs (bot GitHub)
- Interface de curadoria na plataforma
- Dashboard de processos ativos
- Primeiro processo de seleção aberta de novos curadores e membros do comitê

### v2 (mês 6-12): Deliberação Polis

- Instância Polis self-hosted integrada à plataforma
- Primeira deliberação sobre novos marcos estratégicos
- Clusterização visual de opinião em tempo real
- Sistema de identificação de declarações ponte
- Processo completo de propor princípio → deliberar → ratificar

### v3 (mês 12+): Escala

- Deliberações abertas ao público geral (não apenas contribuidores)
- Integração com sistema de compromissos parlamentares
- Deliberações temáticas com parlamentares convidados
- Exportação de resultados de consenso para advocacy direto no Congresso

---

## Métricas de sucesso do sistema de governança

| Métrica | Meta 6 meses | Meta 12 meses |
|---------|:---:|:---:|
| RFCs propostas | 10 | 30 |
| RFCs aprovadas | 5 | 15 |
| Curadores ativos | 10 | 30 |
| Deliberações Polis realizadas | — | 3 |
| Participantes em deliberações | — | 500+ |
| Declarações ponte identificadas | — | 20+ |
| Classificações contestadas e resolvidas | 20 | 100 |
| Rotação de papéis executada | 1 | 2 |
| Diversidade política no comitê editorial | 3 espectros | 4 espectros |

---

## Por que isso funciona

A premissa do sistema é que a soberania industrial brasileira é o que a teoria dos jogos chama de "jogo de coordenação" — um jogo onde todos ganham se cooperarem, mas falham se não se coordenarem. O agricultor quer fertilizante barato. O industrial quer competitividade. O militar quer autossuficiência. O ambientalista quer monitoramento soberano. O engenheiro quer emprego qualificado.

Essas pessoas não precisam concordar sobre Bolsonaro, Lula, aborto, armas, ou qualquer outro tema polarizante. Precisam concordar sobre nióbio, fertilizante, chip, bateria, satélite. O Polis mostrou em Taiwan que quando você remove a capacidade de responder (e portanto atacar), e recompensa declarações que geram acordo entre grupos opostos, as pessoas descobrem que concordam sobre muito mais do que imaginavam.

O ZIL aposta que o mesmo fenômeno se aplica ao Brasil. A única forma de validar essa aposta é construir o sistema e testar.

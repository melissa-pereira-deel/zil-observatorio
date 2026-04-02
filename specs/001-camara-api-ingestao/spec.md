# Feature Specification: Ingestão da API da Câmara dos Deputados

**Feature Branch**: `001-camara-api-ingestao`
**Created**: 2026-04-01
**Status**: Draft

---

## User Scenarios & Testing

### User Story 1 — Cidadão consulta o score ZIL do seu deputado (Priority: P1)

Maria é eleitora de Goiás. Ela acessa o ZIL Observatório, filtra por estado (GO)
e vê o ranking dos seus deputados ordenado por Score ZIL. Cada deputado tem foto,
partido, UF e um score de -10 a +10 calculado a partir de votos reais na Câmara.
Ela clica em um deputado e vê o histórico de votações em pautas ZIL com indicação
de alinhamento (a favor / contra / ausente).

**Why this priority**: É o valor central da plataforma. Sem dados reais de votação
ingeridos, nenhuma outra feature entrega valor. É o "tracer bullet" end-to-end que
valida toda a cadeia: coleta → classificação → score → exibição.

**Independent Test**: Após a ingestão, o ranking retorna ≥ 400 deputados com score
calculado; ao selecionar qualquer deputado, seu histórico de votos em pautas ZIL
está disponível com pelo menos 1 votação classificada.

**Acceptance Scenarios**:

1. **Given** a ingestão foi executada com sucesso, **When** o usuário acessa o
   ranking de parlamentares, **Then** vê ≥ 400 deputados com nome, partido, UF e
   Score ZIL numérico (ou "—" para quem ainda não tem votos ZIL suficientes).
2. **Given** um deputado com votos em pautas ZIL, **When** o usuário acessa o
   perfil, **Then** vê lista de votações com: data, descrição, categoria ZIL e
   indicação de alinhamento para cada voto.
3. **Given** a ingestão é re-executada com os mesmos dados da Câmara, **When** o
   processamento termina, **Then** o número total de deputados e votações não
   aumenta (idempotência verificável por contagem).

---

### User Story 2 — Jornalista exporta dados via API pública (Priority: P2)

Fernanda é repórter de dados do Nexo. Ela acessa a API pública REST do ZIL sem
criar conta, filtra deputados de SP com score abaixo de -3 em pautas de minerais
estratégicos, e obtém os dados em JSON para cruzar com informações de financiamento
de campanha em reportagem.

**Why this priority**: Multiplica o alcance da plataforma via jornalismo de dados.
A API documentada é o produto para pesquisadores e repórteres — independente da
interface web.

**Independent Test**: Os endpoints de listagem com filtros e de histórico de votos
por parlamentar retornam dados corretos, bem-estruturados e sem exigir autenticação.

**Acceptance Scenarios**:

1. **Given** dados ingeridos, **When** Fernanda consulta o endpoint de ranking com
   parâmetros de ordenação e paginação, **Then** recebe JSON com lista de deputados
   contendo: id, nome, partido, uf, score_zil, total_votos_zil.
2. **Given** um deputado específico com votos em ZIL-MIN, **When** Fernanda consulta
   o histórico de votos filtrado por categoria, **Then** recebe lista com: data,
   descrição da votação, categoria ZIL, voto registrado e direção esperada.
3. **Given** parâmetros de filtro inválidos ou inexistentes, **When** Fernanda
   consulta a API, **Then** recebe resposta com código HTTP apropriado (400 ou 404)
   e mensagem de erro legível.

---

### User Story 3 — Operador monitora a saúde da ingestão (Priority: P3)

Carlos é contribuidor técnico do ZIL. Ele quer saber se a ingestão automática está
funcionando: quando foi a última sincronização bem-sucedida, quantos registros foram
processados e se houve falhas silenciosas.

**Why this priority**: Observabilidade básica para manter a confiabilidade da
plataforma. Falhas de ingestão não detectadas resultam em dados desatualizados
apresentados como atuais — erro crítico de credibilidade.

**Independent Test**: O endpoint de estatísticas retorna data da última atualização
e totais; logs estruturados registram início, fim e erros de cada execução.

**Acceptance Scenarios**:

1. **Given** a ingestão foi executada, **When** Carlos consulta as estatísticas
   globais, **Then** vê: total_parlamentares, total_deputados, total_votacoes_zil,
   score_medio e ultima_atualizacao com timestamp ISO 8601.
2. **Given** a API da Câmara retorna erro temporário durante ingestão, **When** o
   worker processa, **Then** registra o erro com contexto (endpoint, código HTTP,
   tentativa), retenta até 3 vezes com intervalo crescente, e falha graciosamente
   sem corromper dados já persistidos.
3. **Given** o agendamento automático está configurado, **When** o horário de
   ingestão chega (a cada 6 horas para votações), **Then** o worker executa sem
   intervenção manual e o timestamp de ultima_atualizacao avança.

---

### Edge Cases

- **API da Câmara indisponível**: Worker retenta com backoff exponencial (3
  tentativas, intervalos de 30s / 2min / 10min); falha registrada em log; próxima
  execução agendada normalmente.
- **Deputado muda de partido ou UF**: Os dados são atualizados via upsert por
  `fonte_id`; o histórico de votos permanece intacto.
- **Votação sem categoria ZIL detectada**: Armazenada sem `categorias_zil`; não
  afeta scores; fica disponível para classificação futura pelo comitê editorial.
- **Score incalculável por falta de votos ZIL**: `score_zil` retorna `null`; deputado
  aparece no ranking com indicação visual "sem dados suficientes".
- **Ingestão parcial interrompida (ex: timeout de servidor)**: Na re-execução, apenas
  os registros ainda ausentes são buscados (verificação por `fonte_id` antes de inserir).
- **Deputado afastado ou que perdeu mandato**: Dados são preservados com marcação de
  status; não aparecem no ranking de "em exercício" mas permanecem acessíveis por ID.

---

## Requirements

### Functional Requirements

- **FR-001**: O sistema DEVE ingerir o perfil completo dos deputados federais em
  exercício: nome, partido, UF, foto, email, informações de mandato.
- **FR-002**: O sistema DEVE ingerir todas as votações nominais da Câmara do período
  2024-01-01 até a data de execução, com resultado, data e descrição.
- **FR-003**: O sistema DEVE ingerir o voto individual de cada deputado por votação,
  registrando: decisão (sim/não/abstenção/ausente/obstrução) e orientação do partido.
- **FR-004**: O sistema DEVE classificar automaticamente votações nas 9 categorias
  ZIL (FER, MIN, SEM, ENE, DIG, DEF, EDU, AGR, COM) usando correspondência de
  palavras-chave definidas em `data/taxonomia/categorias.yml`.
- **FR-005**: O sistema DEVE calcular o Score ZIL para cada deputado com base nos
  votos em votações já classificadas e com direção esperada definida, usando a
  fórmula: `(Σ alinhamento_i × peso_i) / (Σ |peso_i|) × 10`.
- **FR-006**: A ingestão DEVE ser idempotente: re-execução com os mesmos dados da
  fonte NÃO DEVE criar registros duplicados nem recalcular scores de forma incorreta.
- **FR-007**: O sistema DEVE expor dados via API REST pública (sem autenticação) com
  ao menos os endpoints: listagem/ranking de parlamentares com filtros, perfil
  individual, histórico de votos ZIL por parlamentar, e estatísticas globais.
- **FR-008**: A ingestão de votações DEVE ser agendada para execução automática a
  cada 6 horas; a sincronização de perfis de deputados, semanalmente.
- **FR-009**: O sistema DEVE registrar logs estruturados de cada execução de ingestão:
  horário de início/fim, número de registros processados/criados/atualizados e erros.
- **FR-010**: Em caso de falha na fonte de dados, o sistema DEVE reter os dados da
  última ingestão bem-sucedida e não exibir dados vazios ao usuário.

### Key Entities

- **Parlamentar**: Deputado federal identificado de forma única pela combinação
  `fonte_id + fonte`. Possui perfil (nome, partido, UF, foto) e score ZIL calculado.
- **Proposição**: Matéria legislativa (PL, PEC, etc.) associada a votações. Pode
  conter múltiplas categorias ZIL e um nível de relevância.
- **Votação**: Evento de votação nominal vinculado a uma proposição. Contém resultado
  agregado, data, categorias ZIL detectadas e direção esperada pelo manifesto.
- **Voto**: Posição individual de um deputado em uma votação específica. Único por
  par (votação, deputado).
- **Score por Votação**: Contribuição granular de um voto ao score ZIL do deputado.
  Registra impacto (-1.0 a +1.0), peso aplicado e justificativa da classificação.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Após a primeira execução completa, ≥ 95% dos deputados em exercício
  (≥ 487 de 513) têm perfil indexado com nome, partido, UF e foto.
- **SC-002**: Após a primeira execução completa, ≥ 80% dos deputados com votos
  registrados em pautas ZIL têm Score ZIL calculado (valor não nulo).
- **SC-003**: A re-execução completa da ingestão sobre os mesmos dados não cria
  registros duplicados em nenhuma tabela (total de linhas permanece o mesmo).
- **SC-004**: O cidadão consegue encontrar e visualizar o score de qualquer deputado
  em menos de 30 segundos a partir da homepage (inclui carregamento da página de
  ranking e clique no perfil).
- **SC-005**: Em caso de indisponibilidade temporária da API da Câmara, o sistema
  retoma a ingestão automaticamente na próxima janela agendada, sem intervenção manual.
- **SC-006**: A classificação automática por palavras-chave identifica corretamente
  ≥ 60% das votações que contêm termos ZIL na ementa ou descrição (auditável por
  amostragem manual de 50 votações).

---

## Assumptions

- A API pública da Câmara (`dadosabertos.camara.leg.br/api/v2`) está acessível
  sem autenticação e mantém o formato JSON documentado em Swagger.
- O período de ingestão inicial de votações é 2024-01-01 até hoje, cobrindo a
  legislatura atual (57ª Legislatura).
- A "direção esperada" de votações (o que o manifesto ZIL consideraria pró-soberania)
  será definida pelo comitê editorial em etapa separada. Na v0, o Score só é
  calculado para votações onde `direcao_esperada` já estiver explicitamente definida.
- Senadores e dados do TSE (financiamento de campanha) estão fora do escopo desta
  feature — serão tratados na Fase 2.
- Autenticação e cadastro de usuários estão fora do escopo desta feature.
- O ambiente de infraestrutura local (PostgreSQL, Redis, Celery) está operacional
  via Docker Compose conforme `docker-compose.yml` existente no repositório.
- O classificador de palavras-chave usa os termos definidos em
  `data/taxonomia/categorias.yml` sem nenhuma modificação nesta feature.

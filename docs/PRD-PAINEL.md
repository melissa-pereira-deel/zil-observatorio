# ZIL Observatório — PRD: Painel de Curadoria Multi-Perspectiva
### Curadoria editorial assistida por agentes, com decisão humana registrada

> *"A máquina analisa. O humano decide. O git registra."*

**Versão:** 0.1 (proposta — aguardando aprovação dos maintainers)
**Última atualização:** 2026-08-11
**PRD base:** [PRD.md](PRD.md) (v1) — este documento **emenda** as seções 10 e 12
**Governança:** [GOVERNANCE.md](GOVERNANCE.md)

---

## Índice

1. [Sumário Executivo](#1-sumário-executivo)
2. [Contexto e Problema](#2-contexto-e-problema)
3. [Princípio Central: Análise ≠ Legitimidade](#3-princípio-central-análise--legitimidade)
4. [Objetivos e Não-Objetivos](#4-objetivos-e-não-objetivos)
5. [O Painel — Composição](#5-o-painel--composição)
6. [Fluxo de Curadoria](#6-fluxo-de-curadoria)
7. [Regra de Consenso e Pautas Contestadas](#7-regra-de-consenso-e-pautas-contestadas)
8. [Regras Invioláveis](#8-regras-invioláveis)
9. [Artefatos e Formatos](#9-artefatos-e-formatos)
10. [Integração com a Arquitetura Existente](#10-integração-com-a-arquitetura-existente)
11. [Riscos e Mitigações](#11-riscos-e-mitigações)
12. [Fase 1 — Validação Empírica (go/no-go)](#12-fase-1--validação-empírica-gono-go)
13. [Fases de Implantação](#13-fases-de-implantação)
14. [Métricas](#14-métricas)
15. [Custos](#15-custos)
16. [Emendas ao PRD v1](#16-emendas-ao-prd-v1)
17. [Relação com a Visão de Longo Prazo](#17-relação-com-a-visão-de-longo-prazo)
18. [Questões em Aberto](#18-questões-em-aberto)

---

## 1. Sumário Executivo

O gargalo da v1 não é código — é curadoria. O Score ZIL só considera votações
com `direcao_esperada` definida por humanos em `data/direcoes/`, e existem **7**.
Com essa base, o ranking não tem sustentação estatística para ser publicado.

A visão original de resolver isso com participação comunitária (votação de
usuários reais) foi reavaliada por três razões: **cold start** (a plataforma
precisa funcionar antes de existir quórum), **risco de manipulação**
(brigading e captura coordenada em tema político) e **overhead de governança**
que o projeto não quer assumir agora.

Este PRD propõe a alternativa: um **painel de agentes de IA com papéis e
vieses declarados** — jurista, economista, política industrial, políticas
públicas e um contraditor institucional — que analisa cada votação sob
perspectivas distintas e produz **pareceres públicos**. O painel **propõe**;
a decisão registrada é **sempre humana**, através do mecanismo de governança
que já existe (PR + 2 aprovações de maintainers).

Três condições são inegociáveis:

1. **Decisão de registro sempre humana** — o painel nunca mergeia, nunca
   classifica por conta própria; scores fluem apenas de YAML mergeado por humanos.
2. **Dissenso é resultado válido** — desacordo entre agentes não é resolvido
   por maioria simples; vira "pauta contestada", com os argumentos publicados.
3. **Calibração empírica antes de escalar** — o painel só entra em produção se
   demonstrar concordância com o julgamento humano em um conjunto de teste cego.

---

## 2. Contexto e Problema

### 2.1 O gargalo quantificado

| Insumo editorial | Volume atual | Necessário para credibilidade |
|---|---|---|
| Votações com `direcao_esperada` | 7 | 50–100+ |
| Indicadores da Bússola | 4 | 15–20 |
| Categorias com keywords | 9 | ✅ suficiente |

O processo atual — Discord → PR → 2 aprovações — funciona, mas exige que um
humano **pesquise e redija** cada classificação do zero. Pesquisar uma votação
(entender a matéria, ler o texto legal, avaliar o impacto na soberania) custa
horas; revisar uma análise pronta custa minutos. A proposta desloca o humano
de **autor** para **editor**.

### 2.2 Por que não a participação comunitária (agora)

| Problema | Descrição |
|---|---|
| Cold start | Deliberação comunitária exige massa crítica. A plataforma precisa de score confiável **antes** de ter comunidade — é o score que atrai a comunidade. |
| Manipulação | Votação aberta em tema político no Brasil é alvo imediato de brigading, astroturfing e captura por militância organizada. Defender-se disso é um produto em si. |
| Governança | Moderação, identidade, disputas — overhead que o projeto não tem estrutura para assumir em v1. |

A visão de participação **não é abandonada** — ver §17.

---

## 3. Princípio Central: Análise ≠ Legitimidade

A participação comunitária forneceria duas coisas distintas:

- **Análise** — julgamento sobre qual direção de voto favorece a soberania industrial.
- **Legitimidade** — a autoridade de dizer "quem decidiu foi um coletivo de cidadãos".

Agentes de IA produzem análise — possivelmente melhor que uma multidão: mais
profunda, consistente e incansável. Mas **agentes não produzem legitimidade**.
"Um painel de IA decidiu que seu deputado vale −7" não é fonte de autoridade;
é passivo político.

Disso decorre o desenho inteiro:

> O painel é **consultoria legislativa** (produz pareceres técnicos).
> Os maintainers são a **mesa decisora** (a decisão registrada é humana).

A analogia institucional é o próprio Congresso: a consultoria legislativa
produz pareceres; quem vota é o parlamentar. O mecanismo de decisão humana
**já existe no projeto** — dados editoriais entram por PR com 2 aprovações
(GOVERNANCE.md). O painel torna-se um *autor de PRs*, e nada mais.

**Transparência como fosso defensivo:** o uso do painel é divulgado com
destaque na página `/metodologia`. A honestidade sobre o processo é o que o
torna defensável; escondê-lo e ser descoberto seria fatal para o projeto.

---

## 4. Objetivos e Não-Objetivos

### 4.1 Objetivos

| # | Objetivo | Métrica |
|---|---|---|
| O1 | Destravar o gargalo de curadoria | 7 → 50–100 direções definidas em 2 ciclos de produção |
| O2 | Reduzir o custo humano por classificação | Revisão de parecer ≤ 15 min vs. horas de pesquisa |
| O3 | Aumentar a transparência da metodologia | 100% dos pareceres publicados, incluindo dissensos |
| O4 | Detectar pautas genuinamente contestadas | Página pública de pautas contestadas com argumentos |
| O5 | Evoluir a metodologia com evidência | Revisões trimestrais de taxonomia propostas pelo painel |

### 4.2 Não-objetivos

- **Não** substituir a decisão humana — o painel nunca é a autoridade final.
- **Não** automatizar o merge — nenhum agente tem escrita em `main`.
- **Não** resolver desacordo por votação — dissenso vira abstenção pública.
- **Não** alterar a fórmula do Score ZIL — o scoring engine não muda.
- **Não** simular participação popular — o painel não fala "em nome de cidadãos"
  e a plataforma nunca o descreve assim.

---

## 5. O Painel — Composição

Cinco agentes, deliberadamente **adversariais** — como um tribunal, não como um
júri que finge neutralidade. Cada agente tem viés **declarado, versionado e
contestável por PR**.

A diversidade vem de **evidência e tarefa distintas**, não de personas: agentes
que leem insumos diferentes divergem por razões reais; agentes que só vestem
figurinos diferentes sobre o mesmo texto convergem para a mesma resposta com
verniz retórico distinto.

| Agente | Tarefa analítica | Insumo próprio | Viés declarado |
|---|---|---|---|
| **Jurista** | O que o texto *faz* juridicamente: o que muda, revoga, cria; riscos de inconstitucionalidade | Texto integral + leis citadas (cache Planalto, já existente) | Formalista: importa o que está escrito, não a intenção |
| **Economista** | Custos, incentivos, efeitos sobre comércio e cadeias produtivas | Ementa + contexto econômico da categoria | Ortodoxo-cético: desconfia de subsídio sem contrapartida |
| **Política industrial** | Advogado da tese ZIL: impacto direto na soberania industrial | Taxonomia + PRD + Bússola | Desenvolvimentista: defende a tese do projeto |
| **Políticas públicas** | Implementabilidade: capacidade de Estado, execução, histórico de programas similares | Tramitação + situação da proposição | Pragmático: lei que não se implementa é letra morta |
| **Contraditor** | Cargo institucional de dissenso: construir o melhor argumento **contra** a leitura majoritária | Pareceres dos outros 4 | Adversarial por definição |

Definições em `data/painel/agentes/*.yml`, sob a **mesma governança** dos dados
editoriais (PR + 2 aprovações) — porque quem escreve as instruções dos agentes
controla o resultado, as instruções são o novo centro de poder e devem ser
tratadas como tal.

---

## 6. Fluxo de Curadoria

```
┌─────────────┐   ┌──────────────────┐   ┌────────────┐   ┌───────────┐   ┌──────────────┐
│ 1. BRIEFING │ → │ 2. ANÁLISE       │ → │ 3. CONFRONTO│ → │ 4. VEREDITO│ → │ 5. PR + MESA │
│ (enrichment │   │ INDEPENDENTE     │   │ (1 rodada)  │   │ (consenso  │   │ (decisão     │
│ existente)  │   │ (sem ver os      │   │             │   │ ou         │   │ humana)      │
│             │   │ demais)          │   │             │   │ contestada)│   │              │
└─────────────┘   └──────────────────┘   └────────────┘   └───────────┘   └──────────────┘
```

**Etapa 1 — Briefing.** A votação/proposição chega enriquecida pelo pipeline
existente (Feature 002): resumo simples, glossário, leis citadas com texto real
do Planalto. O briefing do painel já está meio construído.

**Etapa 2 — Análise independente.** Cada agente produz parecer estruturado
**sem acesso aos pareceres dos demais**. Isso evita ancoragem e cascata de
conformidade — o vício que invalidaria o painel.

**Etapa 3 — Confronto.** Uma única rodada (controle de custo): cada agente lê
os outros 4 pareceres e pode revisar sua posição, **obrigado a responder ao
contra-argumento mais forte** contra ela. Mudanças de posição são registradas
com justificativa.

**Etapa 4 — Veredito.** Saída estruturada por agente: direção (`sim`/`nao`/
`abster`), confiança (0–1), peso sugerido, categoria principal, justificativa.
Agregação pela regra de consenso (§7).

**Etapa 5 — PR + mesa.** O sistema abre PR contra `data/direcoes/[ano].yml`
com o parecer completo em `data/pareceres/`. Maintainers revisam sob a regra
existente (2 aprovações). **O merge é a decisão.** Rejeição ou alteração
humana também é registrada — e alimenta a calibração contínua (§14).

---

## 7. Regra de Consenso e Pautas Contestadas

Muitas votações são **genuinamente contestadas** — uma tarifa protecionista é
pró-soberania ou anti-competitividade? A resposta depende da teoria econômica
assumida. Nesses casos, o desacordo entre agentes **é o sinal**, não ruído a
eliminar.

| Resultado do painel | Consequência |
|---|---|
| ≥ 4/5 concordam na direção | Proposta de classificação → PR |
| 3/5 ou menos | **"Pauta contestada"** → sem classificação; dissenso publicado |
| Contraditor derruba o consenso na etapa 3 | Reavaliação; se o consenso não se recompõe, contestada |

Isso **operacionaliza** o princípio que o projeto já tem (PRD v1 §10: *"na
dúvida, não classificar"*) — antes dependia da prudência individual do curador;
agora é regra mecânica do processo.

**Subproduto de produto:** a página pública de pautas contestadas — cinco
leituras divergentes de uma mesma votação, em linguagem simples — é um artefato
editorial que nenhum observatório legislativo oferece hoje.

---

## 8. Regras Invioláveis

A "constituição" do painel. Qualquer implementação que viole uma destas regras
está errada por definição:

1. **Nenhum agente mergeia PR.** O painel não tem escrita em `main` — nem
   direta, nem por automação de merge.
2. **Nenhuma classificação sob dissenso.** Abaixo do limiar de consenso, o
   resultado é "contestada". Sem exceções, sem desempate por maioria.
3. **Scores fluem só de YAML mergeado por humanos.** O scoring engine não lê
   pareceres, não lê saída de agente — lê `data/direcoes/`, como hoje.
4. **Metodologia só por proposta.** O painel pode propor mudanças de taxonomia,
   keywords e pesos — em lote, trimestralmente, com evidência. Nunca aplica.
5. **Todo parecer é público.** Incluindo os rejeitados pela mesa e os
   contestados. Não existe parecer privado.
6. **Texto de fonte é dado não confiável.** Ementas e textos legais são
   escritos por terceiros (inclusive gabinetes com interesse no score) —
   tratados como entrada potencialmente adversarial, nunca como instrução.
7. **Reprodutibilidade obrigatória.** Cada parecer registra modelo, versão e
   hash das instruções. Transcrições completas vão para o repositório.

---

## 9. Artefatos e Formatos

### 9.1 Definição de agente — `data/painel/agentes/[nome].yml`

```yaml
agente: jurista
versao: 1
papel: Análise jurídico-formal de proposições legislativas
vies_declarado: >
  Formalista. Analisa o que o texto faz juridicamente — o que cria, altera,
  revoga — independente da intenção declarada dos autores.
insumos:
  - texto_integral
  - leis_referenciadas   # cache Planalto (Feature 002)
instrucoes: |
  [instruções completas do agente — versionadas aqui]
modelo: claude-sonnet-4-5   # pinado por batch
```

### 9.2 Parecer — `data/pareceres/[fonte]-[fonte_id]/`

```
data/pareceres/camara-2454704-53/
├── parecer.md          # síntese: veredito, placar, argumentos principais
├── jurista.md          # parecer individual completo (etapas 2 e 3)
├── economista.md
├── industrial.md
├── publicas.md
├── contraditor.md
└── meta.yml            # modelo, versões, hashes, timestamps, custo
```

### 9.3 Entrada em `data/direcoes/[ano].yml` — campos novos

```yaml
direcoes:
  - fonte_id: "2454704-53"
    fonte: camara
    direcao: sim
    peso: 3.0
    categoria_principal: ZIL-SEM
    # ── novos campos ──
    origem: painel                    # painel | manual
    parecer: data/pareceres/camara-2454704-53/
    placar_painel: "5-0"
    decidido_por: [handle1, handle2]  # quem aprovou o PR
```

Compatibilidade: campos novos são opcionais; as 7 entradas existentes
permanecem válidas (`origem: manual` implícito). `apply_direcoes.py` ignora
campos que não conhece — mudança não quebra nada.

### 9.4 Pauta contestada — `data/pareceres/[id]/CONTESTADA.md`

Registro do dissenso: placar, posições, o melhor argumento de cada lado.
Alimenta a futura página pública. **Não** gera entrada em `data/direcoes/`.

---

## 10. Integração com a Arquitetura Existente

O painel é uma extensão modesta, não uma reconstrução:

| Componente existente | Papel no painel |
|---|---|
| Pipeline de enriquecimento (Feature 002) | **É o briefing** — resumo, glossário, leis citadas já prontos |
| Cache Planalto (`lei_artigos`) | Insumo do agente jurista |
| `data/direcoes/` + `apply_direcoes.py` | Destino das propostas — inalterado |
| Governança de PR (2 aprovações) | **É a mesa decisora** — inalterada |
| Scoring engine | **Não muda uma linha** |
| Celery workers | Novo módulo `apps/workers/panel/` ao lado de `enrichment/` |

Código novo: `apps/workers/panel/` (orquestração das 5 etapas, agregação,
geração de PR) e, na Fase 3, componentes de frontend para exibir pareceres.

---

## 11. Riscos e Mitigações

| # | Risco | Descrição | Mitigação |
|---|---|---|---|
| R1 | **Falsa diversidade** | 5 personas sobre o mesmo modelo compartilham os mesmos pontos cegos; dissenso vira teatro | Diversidade por **evidência e tarefa** (insumos distintos por agente); métrica de concordância inter-agentes monitorada — se > 90% num lote, o painel degenerou em "um modelo com cinco fantasias" e deve ser redesenhado (ou reduzido a um agente, mais barato) |
| R2 | **Captura via instruções** | Quem escreve os prompts controla o resultado | Definições de agente em `data/painel/`, sob PR + 2 aprovações; toda mudança de instrução é diff público |
| R3 | **Prompt injection** | Ementas são escritas por gabinetes com interesse direto no score; o pipeline ingere texto de Câmara, Senado e Planalto | Texto de fonte tratado como dado não confiável (regra 6); suite de testes com instruções adversariais embutidas em ementas sintéticas |
| R4 | **Ataque de legitimidade** | "Robôs dão nota a deputados" como manchete | Enquadramento de consultoria (§3); decisão humana registrada com nomes; disclosure destacado na `/metodologia`; pareceres 100% públicos |
| R5 | **Deriva de modelo** | Atualizações de modelo mudam vereditos silenciosamente; quebra a promessa de auditabilidade | Modelo pinado por batch em `meta.yml`; transcrições no repo; re-runs comparáveis por hash |
| R6 | **Anchoring entre agentes** | Se um agente vê os outros antes de formar posição, o painel vira cascata | Etapa 2 estritamente independente; confronto só na etapa 3, com posições iniciais já registradas |
| R7 | **Custo descontrolado** | Deliberação multi-rodada explode tokens | Uma única rodada de confronto; batches mensais; orçamento por lote (§15) |
| R8 | **Complacência humana** | Revisores passam a aprovar sem ler ("rubber stamping") | Métrica de taxa de alteração/rejeição humana (§14) — se tender a zero, é alerta de complacência, não de qualidade; amostragem periódica de re-revisão cega |

---

## 12. Fase 1 — Validação Empírica (go/no-go)

O painel **não entra em produção por convicção — entra por evidência.**

### Protocolo

1. Maintainers curam **~20 votações novas** às cegas (sem ver saída de agente),
   pelo processo manual atual. Somadas às 7 existentes: **27 casos-teste**.
2. O painel roda sobre os mesmos 27 casos.
3. Comparação:

| Métrica | Meta (go) | Falsificador (no-go) |
|---|---|---|
| Concordância com humanos em casos consensuais | ≥ 85% | Divergência em casos "óbvios" |
| Casos difíceis sinalizados como contestados | Painel abstém onde humanos hesitaram | Painel confiante onde humanos divergiram |
| Concordância inter-agentes | 60–85% (dissenso saudável) | > 90% (painel decorativo) ou < 40% (ruído) |
| Resistência a injection (suite sintética) | 100% dos casos detectados/ignorados | Qualquer instrução embutida obedecida |

### Decisão

- **Go:** métricas dentro das metas → Fase 2.
- **No-go parcial:** concordância alta demais entre agentes → redesenhar
  insumos/tarefas ou reduzir painel a 1 agente forte + revisão humana
  (mais barato, mesma honestidade).
- **No-go total:** divergência dos humanos em casos fáceis → a abordagem não
  serve; o custo terá sido ~30 execuções de painel (desprezível).

---

## 13. Fases de Implantação

| Fase | Entrega | Critério de saída |
|---|---|---|
| **1 — Calibração** | Painel + 27 casos-teste + suite de injection. Sem superfície pública. | Go/no-go da §12 |
| **2 — Produção de curadoria** | Backlog de votações ZIL processado; PRs gerados; mesa revisa | 7 → 50–100 direções mergeadas |
| **3 — Superfície de produto** | Pareceres linkados nas páginas de proposição/votação; página de pautas contestadas; seção na `/metodologia` | Publicado com disclosure |
| **4 — Assistência metodológica** | Revisões trimestrais de taxonomia/pesos propostas com evidência | Primeiro ciclo trimestral completo |

Dependências: Fase 1 não depende de nada externo (enrichment já existe).
Fases 2–4 dependem do go da Fase 1. Deploy em produção (feature 010) é
independente e pode correr em paralelo.

---

## 14. Métricas

### De sucesso (por fase)

- **F1:** métricas da §12.
- **F2:** direções mergeadas/mês; tempo médio de revisão humana por PR;
  taxa de alteração humana sobre propostas (saudável: 5–25%; ~0% = alerta R8;
  > 50% = painel ruim).
- **F3:** % de proposições exibidas com parecer; acessos à página de contestadas.
- **F4:** propostas de metodologia aceitas/rejeitadas por ciclo.

### De integridade (contínuas)

- Concordância inter-agentes por lote (janela saudável: 60–85%).
- % de pautas contestadas (esperado: 15–35%; ~0% = painel homogêneo demais).
- Cobertura de transcrições: 100% dos pareceres com `meta.yml` completo.

---

## 15. Custos

Ordem de grandeza por votação: 5 agentes × 2 etapas × (briefing ~3–5k tokens +
saída ~1–2k tokens) com modelo classe Sonnet ≈ **R$ 0,50–2,00 por votação**.

| Fase | Volume | Custo estimado |
|---|---|---|
| 1 — Calibração | ~30 votações (27 + re-runs) | < R$ 100 |
| 2 — Produção | 100–500 votações | R$ 100–1.000 |
| Regime (mensal) | votações novas do mês | < R$ 100/mês |

Irrelevante frente ao custo da alternativa (horas de pesquisa humana por
votação). A Fase 1 custa menos que um almoço e produz o go/no-go.

---

## 16. Emendas ao PRD v1

Este PRD **emenda** duas passagens do [PRD.md](PRD.md). As mudanças só entram
em vigor com o go da Fase 1.

**§10 — Direção esperada.** Onde se lê:

> O campo `direcao_esperada` (...) é definido **manualmente** pelo comitê
> editorial em `data/direcoes/` — **nunca gerado automaticamente**.

Leia-se:

> O campo `direcao_esperada` é **decidido** exclusivamente por humanos — nunca
> automaticamente. **Propostas** de direção podem ser geradas pelo painel de
> curadoria multi-perspectiva ([PRD-PAINEL.md](PRD-PAINEL.md)); a decisão
> registrada é o merge por 2 maintainers, e o parecer que fundamentou a
> proposta é público.

O espírito da cláusula original — nenhuma classificação automática — é
**preservado e reforçado**: o que muda é quem redige o rascunho, não quem decide.

**§12 — Workflow editorial.** Nova linha na tabela:

| Decisão | Arquivo | Processo |
|---------|---------|---------|
| Proposta de `direcao_esperada` via painel | `data/direcoes/[ano].yml` + `data/pareceres/` | PR gerado pelo painel → revisão da mesa → **2 aprovações humanas** |

---

## 17. Relação com a Visão de Longo Prazo

O painel **não substitui** a visão de participação (v3 no ROADMAP) — é a ponte
até ela. Quando existir comunidade real:

- O painel vira o **corpo técnico** que prepara briefings para deliberação
  humana — o trabalho que qualquer deliberação séria exigiria de qualquer forma.
- Os pareceres acumulados são o **corpus de treinamento cívico**: exemplos de
  como analisar uma votação sob múltiplas perspectivas.
- A página de contestadas é o **backlog natural de deliberação**: as pautas
  onde a comunidade tem mais a contribuir são exatamente as que o painel não
  resolveu.

A decisão de hoje não fecha a porta da visão original — adianta a
infraestrutura que ela precisaria.

---

## 18. Questões em Aberto

| # | Questão | Recomendação inicial |
|---|---|---|
| Q1 | Modelos: um só (pinado) para todos os agentes, ou modelos distintos por agente para reduzir correlação (R1)? | Começar com um (simplicidade na calibração); testar heterogeneidade na Fase 2 se concordância inter-agentes ficar alta |
| Q2 | Os pareceres passam por revisão pública (Discord) antes do merge, como as direções manuais hoje? | Sim na Fase 2 (mantém o rito); reavaliar quando o volume crescer |
| Q3 | Peso sugerido pelo painel ou só direção? | Painel sugere peso com base na tabela do PRD v1 §10; mesa pode alterar |
| Q4 | O contraditor participa do placar ou só provoca? | Participa (5 votos) — abstenção dele conta para "contestada", o que é coerente com o cargo |
| Q5 | Retroatividade: reprocessar as 7 direções manuais pelo painel? | Não — são o gabarito da calibração; reprocessar contaminaria o teste |
| Q6 | Nome público do sistema na `/metodologia` | "Painel de curadoria multi-perspectiva" — nunca "IA vota" ou variantes |

---

*Documento vivo. Mudanças via PR, como tudo neste projeto.*

# ZIL Observatório — PRD: Painel de Curadoria Multi-Perspectiva
### Curadoria editorial assistida por agentes, com decisão humana registrada

> *"A máquina analisa. O humano decide. O git registra."*

**Versão:** 0.2 (proposta — aguardando aprovação dos maintainers)
**Última atualização:** 2026-09-17

> **Emenda 1 (v0.2) — quórum de um.** A v0.1 assumia a regra de governança de
> "PR + 2 aprovações de maintainers" como fundação da decisão humana. Na prática
> o projeto tem **um maintainer ativo**, o que dissolve exatamente a camada que
> torna o painel defensável. Esta versão substitui o quórum por controles
> compensatórios verificáveis (§3.1–3.3) e refaz a Fase 1 para não depender de
> tempo de curadoria que não existe (§12). As mudanças estão marcadas ao longo
> do texto.
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
que já existe (PR revisado e mergeado por humano).

Três condições são inegociáveis:

1. **Decisão de registro sempre humana** — o painel nunca mergeia, nunca
   classifica por conta própria; scores fluem apenas de YAML mergeado por humanos.
   Com um único maintainer, essa decisão é reforçada por uma janela pública de
   objeção antes de a classificação contar no score (§3.2).
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

O processo atual — Discord → PR → revisão — funciona, mas exige que um
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
> A mesa decisora é **humana** (a decisão registrada nunca é do painel).

A analogia institucional é o próprio Congresso: a consultoria legislativa
produz pareceres; quem vota é o parlamentar. O painel torna-se um *autor de
PRs*, e nada mais.

**Transparência como fosso defensivo:** o uso do painel é divulgado com
destaque na página `/metodologia`. A honestidade sobre o processo é o que o
torna defensável; escondê-lo e ser descoberto seria fatal para o projeto.

### 3.1 O problema do quórum de um

A `GOVERNANCE.md` prevê 2–5 maintainers e exige **2 aprovações** para dados
editoriais. Na prática o projeto tem **um maintainer ativo**. A regra existe no
papel e não no mundo — e é justamente ela que a v0.1 deste PRD usava como
fundação da decisão humana.

Sem enfrentar isso, o desenho vira: uma pessoa homologando a saída de uma IA, com
a aparência de governança colegiada. Pior que não ter a regra, porque cria falsa
garantia. Nomear o déficit é pré-requisito para compensá-lo.

As 2 aprovações entregavam três coisas distintas:

| O que entregava | Some com um maintainer? |
|---|---|
| **Captura de erro** — um segundo par de olhos | Sim |
| **Resistência a conluio** — difícil empurrar algo sozinho | Sim |
| **Sinal de legitimidade** — "não foi decisão de uma pessoa só" | Sim |

### 3.2 Controles compensatórios

Nenhum controle isolado substitui um segundo revisor. Os cinco abaixo, juntos,
cobrem as três funções acima — e, ao contrário do quórum de papel, são
**verificáveis**:

| # | Controle | Qual função cobre |
|---|---|---|
| C1 | **Janela pública de objeção** — a classificação aprovada fica visível mas **não conta no score** por 7 dias corridos. Qualquer pessoa pode objetar por issue pública nesse prazo. | Captura de erro + legitimidade: troca um par de olhos por todos os pares, de forma assíncrona |
| C2 | **Separação temporal do julgamento** — não aprovar no mesmo dia em que o painel gerou o parecer | Captura de erro: revisar com cabeça fria, não no embalo da geração |
| C3 | **Proveniência declarada** — cada votação mostra quem decidiu e com base em qual parecer; a `/metodologia` publica a composição (quantas classificações tiveram 1 revisor, quantas tiveram 2) | Legitimidade: não esconde o déficit, declara |
| C4 | **Canal público de contestação** — issue com template próprio para contestar classificação. Sem isso, C1 é decorativo | Captura de erro: dá à janela um mecanismo real |
| C5 | **Taxa de alteração monitorada** — se o maintainer aceitar perto de 100% das propostas, é alarme de complacência, não sinal de qualidade (§11, R8) | Resistência a conluio: torna o rubber-stamping visível |

**C1 e C2 caem quando houver 2+ maintainers ativos.** São compensação para uma
condição temporária, não regra permanente — o caminho de volta ao quórum
continua aberto e é o estado preferido.

### 3.3 Estados de uma classificação

C1 exige que "aprovada" e "contando no score" deixem de ser a mesma coisa:

| Estado | Significado | Conta no score? |
|---|---|---|
| `proposta` | Painel gerou o parecer, PR aberto | Não |
| `em_carencia` | Humano aprovou e mergeou; público, aguardando a janela de 7 dias | **Não** |
| `vigente` | Janela vencida sem objeção | Sim |
| `contestada` | Objeção recebida na janela; volta para revisão | Não |

Implementação: campo `vigente_a_partir_de` na entrada do YAML (§9.3).
`apply_direcoes.py` passa a aplicar **apenas** direções cuja data já passou — o
que torna a carência uma propriedade do dado, verificável por qualquer pessoa
que leia o repositório, e não uma promessa de processo.

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
editoriais (PR revisado, mais a janela de objeção de C1) — porque quem escreve as instruções dos agentes
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
com o parecer completo em `data/pareceres/`. O maintainer revisa e decide.
Rejeição ou alteração humana também é registrada — e alimenta a calibração
contínua (§14).

Com um maintainer, **o merge deixa de ser a decisão final**: ele abre a janela
de objeção de 7 dias (C1). A classificação só passa a contar no score quando a
janela vence sem contestação — o que é imposto pelo campo `vigente_a_partir_de`,
não por disciplina (§3.3). Com 2+ maintainers, o merge volta a ser a decisão.

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
8. **Enquanto houver um único maintainer, nenhuma classificação conta no score
   antes de vencer a janela de objeção.** Merge não é vigência (§3.3). Reduzir
   ou pular a janela exige um segundo maintainer ativo — nunca pressa de prazo.
9. **O déficit de quórum é declarado publicamente.** A `/metodologia` informa
   quantas classificações vigentes tiveram um único revisor. O projeto não
   apresenta decisão de uma pessoa como se fosse colegiada.
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
    decidido_por: [handle1]           # quem aprovou o PR
    vigente_a_partir_de: "2026-09-24" # fim da janela de objeção (C1);
                                      # antes dessa data não entra no score
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
| `data/direcoes/` + `apply_direcoes.py` | Destino das propostas — muda só para respeitar `vigente_a_partir_de` (§3.3) |
| Governança de PR | **É a mesa decisora** — com um maintainer, acrescida da janela de objeção (§3.2) |
| Scoring engine | **Não muda uma linha** |
| Celery workers | Novo módulo `apps/workers/panel/` ao lado de `enrichment/` |

Código novo: `apps/workers/panel/` (orquestração das 5 etapas, agregação,
geração de PR) e, na Fase 3, componentes de frontend para exibir pareceres.

---

## 11. Riscos e Mitigações

| # | Risco | Descrição | Mitigação |
|---|---|---|---|
| R1 | **Falsa diversidade** | 5 personas sobre o mesmo modelo compartilham os mesmos pontos cegos; dissenso vira teatro | Diversidade por **evidência e tarefa** (insumos distintos por agente); métrica de concordância inter-agentes monitorada — se > 90% num lote, o painel degenerou em "um modelo com cinco fantasias" e deve ser redesenhado (ou reduzido a um agente, mais barato) |
| R2 | **Captura via instruções** | Quem escreve os prompts controla o resultado — e com um maintainer, quem escreve e quem aprova são a mesma pessoa | Definições de agente em `data/painel/`, versionadas e sob a mesma janela de objeção das classificações; toda mudança de instrução é diff público |
| R3 | **Prompt injection** | Ementas são escritas por gabinetes com interesse direto no score; o pipeline ingere texto de Câmara, Senado e Planalto | Texto de fonte tratado como dado não confiável (regra 6); suite de testes com instruções adversariais embutidas em ementas sintéticas |
| R4 | **Ataque de legitimidade** | "Robôs dão nota a deputados" como manchete | Enquadramento de consultoria (§3); decisão humana registrada com nomes; disclosure destacado na `/metodologia`; pareceres 100% públicos |
| R5 | **Deriva de modelo** | Atualizações de modelo mudam vereditos silenciosamente; quebra a promessa de auditabilidade | Modelo pinado por batch em `meta.yml`; transcrições no repo; re-runs comparáveis por hash |
| R6 | **Anchoring entre agentes** | Se um agente vê os outros antes de formar posição, o painel vira cascata | Etapa 2 estritamente independente; confronto só na etapa 3, com posições iniciais já registradas |
| R7 | **Custo descontrolado** | Deliberação multi-rodada explode tokens | Uma única rodada de confronto; batches mensais; orçamento por lote (§15) |
| R8 | **Complacência humana** | Revisores passam a aprovar sem ler ("rubber stamping"). **Com um maintainer este é o risco dominante**, não mais um risco entre outros: não há segundo leitor para pegar o que passou, e a pessoa que revisa é a mesma que quer ver o gargalo resolvido | Taxa de alteração/rejeição monitorada e publicada (§14) — se tender a zero, é alerta, não sinal de qualidade; separação temporal obrigatória entre geração e aprovação (C2); janela pública de objeção como rede de segurança (C1) |
| R9 | **Quórum de papel** | A `GOVERNANCE.md` promete 2 aprovações que não existem; manter a promessa no texto cria falsa garantia para quem lê o projeto de fora | §3.1 nomeia o déficit; C3 publica a proveniência real de cada classificação; a `GOVERNANCE.md` deve ser emendada junto com este PRD |

---

## 12. Fase 1 — Validação Empírica (go/no-go)

O painel **não entra em produção por convicção — entra por evidência.**

> **Emenda 1 (v0.2).** A v0.1 pedia que maintainers curassem ~20 votações novas
> às cegas para servir de gabarito. Isso pressupõe horas de pesquisa legislativa
> que o único maintainer ativo não tem — e um protocolo que depende de tempo
> inexistente não é rigor, é ficção. O protocolo abaixo extrai o máximo de
> evidência **sem custar tempo de curadoria**, e declara o que perde.

### O gabarito cego que já existe

As **7 votações já curadas** em `data/direcoes/` foram decididas em 2024–2025,
antes de o painel existir. São, portanto, um gabarito genuinamente cego e
**não contaminado por ancoragem** — pequeno (n=7), mas real, e de graça.

É pouco para significância estatística e serve bem para o que importa aqui:
**pegar erro grosseiro**. Um painel que diverge do julgamento humano em votações
que já foram consideradas claras o bastante para entrar no score é um painel que
não deve curar nada.

Por isso as 7 **não devem ser reprocessadas** como produção (§18, Q5):
reprocessá-las destruiria o único gabarito limpo disponível.

### Protocolo revisado

1. **Teste cego (n=7).** Painel roda sobre as 7 votações curadas. O maintainer
   não vê a saída antes — a comparação é contra o YAML que já está no git.
2. **Teste de injection.** Suite sintética de ementas com instruções embutidas.
   Independe de gabarito humano e é o teste mais barato de todos.
3. **Revisão post-hoc (n≈10).** Painel roda sobre ~10 votações novas; o
   maintainer revisa a **saída** (minutos por caso) em vez de pesquisar do zero
   (horas por caso), registrando aceite, alteração ou rejeição com o motivo.

### Métricas

| # | Métrica | Meta (go) | Falsificador (no-go) |
|---|---|---|---|
| 1 | Concordância com as 7 curadas (cego) | ≥ 6 de 7 | Divergência em 3 ou mais |
| 2 | Resistência a injection | 100% detectado/ignorado | Qualquer instrução embutida obedecida |
| 3 | Concordância inter-agentes | 60–85% (dissenso saudável) | > 90% (painel decorativo) ou < 40% (ruído) |
| 4 | Taxa de alteração humana no post-hoc | 5–40% | ~0% (ancoragem/complacência) ou > 60% (painel ruim) |
| 5 | Pautas marcadas contestadas | 15–35% | ~0% (painel homogêneo demais) |

### O que este protocolo perde — risco aceito

A métrica 4 é **post-hoc, não cega**: o maintainer avalia uma proposta pronta em
vez de formar julgamento independente. Ancoragem infla concordância, e o número
**não é comparável** ao de um teste cego. Ele serve para detectar painel ruim
(alteração alta), não para provar painel bom (alteração baixa).

Isso é uma perda real de rigor, aceita conscientemente porque a alternativa não
é um teste melhor — é nenhum teste. Fica declarado aqui, e deve ser declarado na
`/metodologia`: **a validação do painel repousa sobre 7 casos cegos**, não sobre
27. Quem surgir como segundo maintainer deve produzir gabarito cego adicional
antes de qualquer expansão de escopo.

### Decisão

- **Go:** métricas 1, 2 e 3 dentro das metas → Fase 2.
- **No-go parcial:** concordância inter-agentes alta demais → redesenhar
  insumos/tarefas ou reduzir painel a 1 agente forte + revisão humana
  (mais barato, mesma honestidade).
- **No-go total:** divergência nas 7 curadas ou qualquer falha de injection → a
  abordagem não serve. Custo total terá sido ~20 execuções de painel.

---

## 13. Fases de Implantação

| Fase | Entrega | Critério de saída |
|---|---|---|
| **1 — Calibração** | Painel + teste cego nas 7 curadas + suite de injection + revisão post-hoc de ~10. Sem superfície pública. | Go/no-go da §12 |
| **2 — Produção de curadoria** | Backlog de votações ZIL processado; PRs gerados; maintainer revisa; janela de objeção aplicada | 7 → 50–100 direções **vigentes** (não só mergeadas) |
| **3 — Superfície de produto** | Pareceres linkados nas páginas de proposição/votação; página de pautas contestadas; canal de contestação (C4); seção na `/metodologia` com a proveniência real (C3) | Publicado com disclosure |
| **4 — Assistência metodológica** | Revisões trimestrais de taxonomia/pesos propostas com evidência | Primeiro ciclo trimestral completo |

Dependências: Fase 1 não depende de nada externo (enrichment já existe).
Fases 2–4 dependem do go da Fase 1. Deploy em produção (feature 010) é
independente e pode correr em paralelo.

---

## 14. Métricas

### De sucesso (por fase)

- **F1:** métricas da §12.
- **F2:** direções **vigentes**/mês (mergeadas não bastam — §3.3); tempo médio
  de revisão humana por PR; taxa de alteração humana sobre propostas (saudável:
  5–25%; ~0% = alerta R8; > 50% = painel ruim); intervalo mediano entre geração
  e aprovação (C2 exige que não seja no mesmo dia).
- **F3:** % de proposições exibidas com parecer; acessos à página de contestadas.
- **F4:** propostas de metodologia aceitas/rejeitadas por ciclo.

### De integridade (contínuas)

- Concordância inter-agentes por lote (janela saudável: 60–85%).
- % de pautas contestadas (esperado: 15–35%; ~0% = painel homogêneo demais).
- Cobertura de transcrições: 100% dos pareceres com `meta.yml` completo.
- **Proveniência (C3):** proporção de classificações vigentes com um único
  revisor. Publicada na `/metodologia`. Enquanto for 100%, o projeto declara
  explicitamente que opera com quórum de um.
- **Objeções recebidas na janela (C1):** quantas, e quantas viraram reversão.
  Zero objeções em muitos meses pode significar tanto qualidade quanto ausência
  de público auditando — não confundir as duas leituras.

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

Este PRD **emenda** duas passagens do [PRD.md](PRD.md) e, a partir da v0.2,
uma da [GOVERNANCE.md](GOVERNANCE.md). As mudanças só entram em vigor com o go
da Fase 1.

**§10 — Direção esperada.** Onde se lê:

> O campo `direcao_esperada` (...) é definido **manualmente** pelo comitê
> editorial em `data/direcoes/` — **nunca gerado automaticamente**.

Leia-se:

> O campo `direcao_esperada` é **decidido** exclusivamente por humanos — nunca
> automaticamente. **Propostas** de direção podem ser geradas pelo painel de
> curadoria multi-perspectiva ([PRD-PAINEL.md](PRD-PAINEL.md)); a decisão
> registrada é humana, e o parecer que fundamentou a proposta é público.
> Enquanto o projeto tiver um único maintainer ativo, a classificação só passa
> a contar no score após a janela pública de objeção (PRD-PAINEL §3.2).

O espírito da cláusula original — nenhuma classificação automática — é
**preservado e reforçado**: o que muda é quem redige o rascunho, não quem decide.

**§12 — Workflow editorial.** Nova linha na tabela:

| Decisão | Arquivo | Processo |
|---------|---------|---------|
| Proposta de `direcao_esperada` via painel | `data/direcoes/[ano].yml` + `data/pareceres/` | PR gerado pelo painel → revisão humana → merge → **janela de objeção de 7 dias** antes de contar no score |

**GOVERNANCE.md — quórum.** O documento prevê 2–5 maintainers e exige 2
aprovações para dados editoriais, mas o projeto opera com um. Manter a promessa
sem cumpri-la cria falsa garantia para quem lê o projeto de fora (R9). Proposta:

> Dados editoriais exigem 2 aprovações de maintainers. **Enquanto o projeto
> tiver menos de dois maintainers ativos**, a regra é substituída por: 1
> aprovação + janela pública de objeção de 7 dias antes de a classificação
> entrar em vigor, com a proveniência declarada na `/metodologia`. A regra
> original volta automaticamente quando houver dois maintainers ativos.

Esta é a única emenda deste PRD que **não** deve esperar o go da Fase 1: ela
descreve o que já é verdade hoje, e o documento atual descreve o que não é.

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
| Q2b | **7 dias de janela de objeção é o prazo certo?** | Curto demais não dá tempo de alguém notar; longo demais trava a curadoria. 7 dias é chute informado — revisar após o primeiro lote da Fase 2, com dados de quando as objeções de fato chegam |
| Q2c | **Recrutar um segundo maintainer é prioridade?** | Sim. Todos os controles de §3.2 são paliativos; o remédio é quórum real. A pergunta operacional é se vale gastar tempo recrutando agora ou depois do painel destravar a curadoria |
| Q3 | Peso sugerido pelo painel ou só direção? | Painel sugere peso com base na tabela do PRD v1 §10; mesa pode alterar |
| Q4 | O contraditor participa do placar ou só provoca? | Participa (5 votos) — abstenção dele conta para "contestada", o que é coerente com o cargo |
| Q5 | Retroatividade: reprocessar as 7 direções manuais pelo painel? | **Não, e agora é mais crítico que na v0.1** — sem o gabarito de 20 casos, essas 7 são o *único* teste cego não contaminado que existe (§12) |
| Q6 | Nome público do sistema na `/metodologia` | "Painel de curadoria multi-perspectiva" — nunca "IA vota" ou variantes |

---

*Documento vivo. Mudanças via PR, como tudo neste projeto.*

# RFC-006: Como o classificador funciona, por que erra, e o que fazer com o texto integral

**Data:** 2026-10-21
**Status:** RFC aberto — sem decisão
**Janela:** fecha em 2026-10-28 (≥ 7 dias, [GOVERNANCE.md](../GOVERNANCE.md) § "Mudanças nas categorias ZIL")
**Relaciona-se com:** [RFC-005](005-rfc-destino-das-categorias.md) (granularidade da taxonomia) e [issue #27](https://github.com/melissa-pereira-deel/zil-observatorio/issues/27) (auditabilidade)

> **Procedência.** A investigação, as medições e a redação são de Claude
> (assistente), a pedido da maintainer, que perguntou como o classificador
> funciona e levantou a hipótese de que faltaria um pipeline com OCR e
> extração de múltiplos PDFs. Tudo que está marcado **medido** foi verificado
> em 2026-10-21 contra a API da Câmara, PDFs reais ou o código; o que está
> marcado **literatura** vem de fonte citada; o que está marcado **suposição**
> não foi testado e é dito como tal. A seção 9 (Decisão) está **vazia** e é
> da maintainer.

---

## 0. Resumo executivo

1. **O classificador nunca lê a proposição.** Ele casa palavras-chave contra
   três campos curtos da API — ementa, ementa detalhada e indexação — e o texto
   integral (`urlInteiroTeor`) é gravado no banco e **nunca aberto**. *(medido)*
2. **A ementa é um insumo fraco por construção.** Em 38% dos casos ela diz *o
   que muda* ("Altera a Lei nº…") e não *sobre o quê*; 40% citam uma lei pelo
   número; só 3% têm ementa detalhada. O campo mais rico — a indexação da
   própria Câmara — está presente em 100% e é justamente o que não persistimos
   (issue #27). *(medido, amostra de 60 PLs de 2024–25)*
3. **OCR não é o gargalo.** O inteiro teor de 2010 em diante é PDF com camada
   de texto nativa. Só o acervo antigo (testado: 2005) é imagem escaneada, e
   2001 nem devolve PDF. Para a janela do projeto (2023+), **não precisa de
   OCR**. *(medido em 7 PDFs)*
4. **A cobertura de fontes canônicas já é alcançável pela API.** Pareceres,
   emendas, substitutivos e destaques estão listados por proposição com URL
   própria — o PL 1847/2024 tem 19 documentos anexos e 58 proposições
   relacionadas. O Senado expõe os textos por matéria. O problema não é
   descobrir os documentos; é que não os lemos. *(medido)*
5. **A Câmara já classifica por tema**, com 32 temas oficiais, presentes em
   100% da amostra, média de 2,5 por proposição. É um prior gratuito que
   ignoramos. Não substitui a taxonomia ZIL — "Energia, Recursos Hídricos e
   Minerais" não é "soberania mineral" — mas filtra o que nunca será ZIL.
   *(medido)*
6. **A literatura é clara sobre LLMs zero-shot em classificação de projetos de
   lei:** 58–83% de acurácia contra codificadores humanos treinados a 90%; a
   receita que funciona é **automatizar onde dois modelos concordam (83% de
   acurácia em 65% dos itens) e mandar o resto para humano**. *(literatura)*
7. **Recomendação:** não trocar o classificador por outro classificador.
   Trocar a *entrada* (texto integral + parecer, em vez de ementa) e a
   *saída* (evidência gravada, confiança, fila de revisão) — e manter a
   decisão editorial humana onde ela já está. O OCR entra como módulo
   opcional para o acervo antigo, não como pré-requisito.

---

## 1. Como o classificador funciona hoje

[`apps/workers/classifiers/__init__.py`](../../apps/workers/classifiers/__init__.py)

```
texto = ementa + " " + ementa_detalhada + " " + indexação     # só isso
texto_limpo = sem_citacoes_de_lei(texto)                      # tira "(Lei Geral de …)"
para cada categoria ZIL:
    casou = [kw for kw in keywords if \bkw\b in texto]
    fortes = [kw for kw in casou if kw ∉ keywords_fracas and kw in texto_limpo]
    categoria entra  ⟺  fortes ≠ ∅
relevancia = casamentos / (0,3 × nº de keywords da categoria), limitado a 1
```

É um **classificador léxico por regra**, sem modelo, sem corpus de treino,
sem noção de contexto. Cada decisão é explicável (é por isso que o
`candidatas.py` consegue dizer "casou por `minerais críticos`"), e cada erro é
de um de três tipos, todos já observados:

| Tipo de erro | Exemplo real | Correção que já existe |
|---|---|---|
| Polissemia | `tarifa` → Tarifa Social de Água | `keywords_fracas` (#26) |
| Lei citada ≠ tema | `dados pessoais` dentro de "(LGPD)" | `sem_citacoes_de_lei` (#23/#26) |
| **Tema fora do vocabulário** | PL 2583/2020, complexo industrial da saúde → caiu em ZIL-EDU por `pesquisa e desenvolvimento` | **nenhuma** — é o RFC-005 (#39) |

O terceiro tipo é o que não tem conserto por keyword: a proposição *é* ZIL,
mas o vocabulário da taxonomia não a descreve. Casar palavras não resolve;
precisa de um leitor que entenda do que o texto trata.

### 1.1 O que o classificador não vê

| Fonte | Existe na API? | Lemos? | Onde está |
|---|---|---|---|
| Ementa | sim | sim | `ementa` |
| Ementa detalhada | sim, em 3% | sim | `ementaDetalhada` |
| Indexação da Câmara | sim, em 100% | sim, **e descartamos** | `keywords` — issue #27 |
| Temas oficiais da Câmara | sim, 32 temas, 100% | **não** | `/proposicoes/{id}/temas` |
| **Texto integral** | sim | **não** | `urlInteiroTeor` — gravado, nunca aberto |
| Pareceres, substitutivos, emendas | sim, com URL cada | **não** | `/proposicoes/{id}/tramitacoes[].url`, `/relacionadas` |
| Textos no Senado | sim, PDF | **não** | `/materia/textos/{codigo}` |
| Leis citadas, artigo a artigo | Planalto | sim, só no enriquecimento | `enrichment/_fetch_planalto` |

---

## 2. O sistema: dependências, fontes e dimensões

```
                 ┌─────────────────────────────────────────────────────┐
                 │  FONTES CANÔNICAS                                   │
                 │  Câmara API ──► metadados (ementa, indexação, temas)│
                 │             ──► inteiro teor (PDF, codteor)         │
                 │             ──► tramitações (parecer, emenda, …)    │
                 │  Senado API ──► matéria, textos (PDF)               │
                 │  Planalto   ──► texto das leis citadas              │
                 │  LexML      ──► URN canônica por norma              │
                 └───────────────┬─────────────────────────────────────┘
                                 ▼
   ┌──────────── AQUISIÇÃO ────────────┐   gargalos: rate limit (300ms),
   │ descobrir ids → baixar documentos │   acervo antigo sem PDF, PDF escaneado
   └───────────────┬───────────────────┘   (pré-2008), User-Agent bloqueado
                   ▼
   ┌──────────── EXTRAÇÃO ─────────────┐   PDF nativo → texto (Tika/pdfplumber)
   │ PDF → texto estruturado           │   PDF imagem → OCR (Tesseract) — raro
   └───────────────┬───────────────────┘   formato: artigos, incisos, "NR"
                   ▼
   ┌──────────── CLASSIFICAÇÃO ────────┐   hoje: regex sobre ementa
   │ texto → {categoria, evidência,    │   alvo: leitor do texto integral com
   │          confiança}               │   evidência gravada e confiança
   └───────────────┬───────────────────┘
                   ▼
   ┌──────────── CURADORIA ────────────┐   humano decide direção e peso
   │ fila por confiança → decisão      │   (isso NÃO muda — é a tese do projeto)
   └───────────────┬───────────────────┘
                   ▼
            Score ZIL / site
```

### 2.1 As dimensões do problema (independentes entre si)

| Dimensão | Pergunta | Estado |
|---|---|---|
| **Cobertura** | Achamos tudo que é ZIL? | Não medimos recall. O `candidatas.py` descarta o que não casa keyword (`if not evidencia: continue`) — matéria invisível, não rótulo errado |
| **Precisão** | O que achamos é ZIL? | Medimos: era ~25% de ruído antes do #26; depois, ainda há tema-fora-do-vocabulário |
| **Granularidade** | 9 categorias bastam? | RFC-005 aberta. A Câmara usa 32; o CAP usa 21 macro + 211 sub |
| **Entrada** | Ementa ou texto? | Ementa. Medido: 38% boilerplate |
| **Auditabilidade** | Dá para saber por quê? | Parcial: evidência existe em memória, não no banco (#27) |
| **Ambiguidade** | Multi-rótulo? Confiança? | Multi-rótulo sim; confiança não existe (é 0/1) |
| **Direção** | Votar sim é pró-ZIL? | Humana, e fica humana. Nenhuma abordagem aqui toca nisso |
| **Custo** | Por proposição | Hoje ~0; LLM sobre texto integral: centavos por documento |

A confusão mais cara é tratar essas dimensões como uma só. "Precisamos de
OCR" é uma resposta à dimensão *Entrada* para um subconjunto (acervo antigo)
que não está na janela do projeto. "Precisamos de um modelo" é uma resposta à
*Precisão* que não resolve *Cobertura* se a entrada continuar sendo a ementa.

---

## 3. Certezas, hipóteses e suposições

### 3.1 Certezas (medidas em 2026-10-21)

| # | Afirmação | Como foi medido |
|---|---|---|
| C1 | O texto integral nunca é lido | `grep` em `apps/ scripts/ packages/`: `url_inteiro_teor` só é gravado e exibido |
| C2 | 38% das ementas começam com "Altera/Acrescenta/Revoga…"; 40% citam lei por número; 3% têm ementa detalhada; 100% têm indexação | 60 PLs de 2024–25 (30 mais recentes de cada ano), `GET /proposicoes/{id}` |
| C3 | PDFs de 2010+ têm camada de texto; 2005 é imagem (24 imagens, 0 operadores de texto); 2001 não devolve PDF | 7 `urlInteiroTeor` (2025, 2024, 2020, 2018, 2015, 2010, 2005, 2001), streams FlateDecode inflados com `zlib` e contagem de operadores `Tj`/`TJ` |
| C4 | Pareceres/emendas/substitutivos têm URL própria na tramitação | PL 1847/2024: 66 tramitações, 19 com documento, 58 relacionadas (19 EMP, 7 DTQ, 2 PRLE) |
| C5 | A Câmara atribui temas oficiais a 100% da amostra, média 2,5/proposição; mas a PNMCE (PL de 2025) não tinha nenhum | `/proposicoes/{id}/temas` em 60 + 5 casos conhecidos |
| C6 | Em 60 PLs aleatórios, o classificador ZIL atual casa 3% (2/60), nenhum multi-rótulo | `classificar_proposicao` local sobre a mesma amostra |
| C7 | O Senado expõe os textos por matéria (PDF), e `senado_client` não os busca | `GET /materia/textos/156993` + `grep def` no cliente |

C6 importa: **a ambiguidade não aparece em projeto aleatório — aparece dentro
do subconjunto relevante.** O caso PL 2583/2020 (saúde industrial → ZIL-EDU)
é típico: a proposição é ZIL, e a categoria errada vem de o vocabulário não
cobrir o tema. Isso é problema de taxonomia (RFC-005) tanto quanto de
classificador.

### 3.2 Hipóteses (com evidência a favor e contra)

| # | Hipótese | A favor | Contra | Como testar barato |
|---|---|---|---|---|
| H1 | Ler o texto integral melhora a classificação sobre ler só a ementa | C2 (ementa é "o que muda"); a Câmara mantém indexação humana justamente porque a ementa não basta | **Literatura:** em CAP, resumo ≥ texto integral para modelos de bag-of-words (ruído/sinal); Longformer não teve vantagem sobre RoBERTa truncado | Amostra de ~30 proposições ZIL já curadas: classificar com (a) ementa, (b) ementa+indexação, (c) parecer, (d) texto integral, contra o rótulo humano |
| H2 | O **parecer** do relator é a melhor fonte única | Resume mérito, impacto e contexto em linguagem corrida; é texto nativo; é o "voto" | Só existe depois da comissão; proposição recém-apresentada não tem | Mesmo experimento de H1 |
| H3 | Os temas oficiais servem como **filtro negativo** (o que nunca é ZIL) | C5: 100% cobertos; "Homenagens e Datas Comemorativas" é o tema mais frequente (19/60) e nunca é ZIL | PNMCE sem tema; o mapeamento tema→ZIL não é 1:1 | Dos ZIL curados, quantos caem em qual tema oficial |
| H4 | Um LLM lendo o texto, com o codebook ZIL no prompt, supera o regex | Literatura: 58–83% em 21 tópicos CAP, zero-shot, 8 línguas incl. português | Mesma literatura: abaixo de humano treinado (90%); −8 pp se determinístico; variação entre execuções | Mesma amostra de H1, 2 modelos, medir concordância |
| H5 | Fine-tuning de um transformer em PT supera LLM zero-shot | Benchmark de 79 LLMs: "fine-tuned transformers may surpass the best zero-shot" (preliminar); BERTimbau e Ulysses Tesemõ existem | Precisa de corpus rotulado — temos 7 votações e ~70 proposições com ZIL | Não agora. Vira viável se a curadoria chegar a centenas |

### 3.3 Suposições (não testadas — ditas como tal)

- **S1.** Que "soberania industrial" é um tema que um leitor genérico reconhece
  a partir do texto. Pode não ser: é um recorte político sobre temas
  convencionais, e um LLM pode precisar do manifesto como contexto.
- **S2.** Que o rate limit da Câmara (300 ms) permite baixar texto integral +
  pareceres em escala. ~240 proposições × ~5 documentos ≈ 1.200 downloads;
  viável, mas não medimos o tamanho médio.
- **S3.** Que a estrutura do texto legal (artigos, incisos, "(NR)") não precisa
  ser parseada para classificar — que texto corrido basta. Para *classificar*,
  provavelmente sim; para *extrair impacto*, provavelmente não.
- **S4.** Que o custo de LLM por documento é aceitável. Texto integral de
  5–20 mil tokens custa centavos por documento; em 240 proposições, unidades
  de real. Não medimos.

---

## 4. O que a literatura e os projetos análogos ensinam

### 4.1 Classificação de projetos de lei por tópico (o problema mais próximo)

**Comparative Agendas Project (CAP)** é a referência de 30 anos para isso: 21
macro-tópicos, 211 subtópicos, codificadores humanos treinados até
**90% de confiabilidade** entre si. Existe um **Brazilian Policy Agendas
Project** (UNESP Araraquara) com manual de codificação de 2019 — é o análogo
direto de `data/taxonomia/categorias.yml`, com décadas de regras para "projeto
que trata de vários assuntos". Vale ler antes de decidir o RFC-005.
([manual](https://minio.la.utexas.edu/compagendas/codebookfiles/CodeManual_Junho_2019.pdf) ·
[CAP na América Latina, RAP 2020](https://www.scielo.br/j/rap/a/vsZ7wryXTddhSwd9MpKgRKP/?lang=pt))

**LLMs zero-shot nesse problema**, três fontes convergentes:

- *Multiclass Classification of Policy Documents with LLMs*
  ([arXiv 2310.08167](https://arxiv.org/abs/2310.08167), publicado em
  [J. Computational Social Science 2025](https://link.springer.com/article/10.1007/s42001-025-00362-2)):
  GPT-3.5/4 em projetos de lei do Congresso dos EUA, 21 tópicos CAP —
  **58–83% de acurácia** conforme o cenário. A conclusão operacional:
  *"depender totalmente do GPT com intervenção humana mínima é insuficiente"*;
  mas **onde os dois modelos concordam (65% dos itens), a acurácia é 83%** —
  automatize essa fatia, codifique à mão os 35% restantes.
- *Benchmark de 79 LLMs em 8 línguas, incluindo português*
  ([Zenodo 2025](https://zenodo.org/records/17512637)): modelos de raciocínio
  sobem o F1 em ~9 pp; **execução determinística custa ~8 pp**; chain-of-thought
  é a técnica mais eficaz; fine-tuning *"may surpass the best zero-shot"*
  (preliminar).
- *Beyond Token Limits* ([arXiv 2509.10199](https://arxiv.org/html/2509.10199)):
  texto longo em CAP, 5 línguas — **Longformer não teve vantagem** sobre
  modelos de 512 tokens, e o melhor modelo aberto superou os GPT. Ou seja:
  comprimento não é o gargalo; o que importa é *qual trecho*.

Para classificação legal multi-rótulo em geral, a linhagem
[EURLEX57K (Chalkidis et al. 2019)](https://aclanthology.org/P19-1636/) →
[baselines 2024](https://arxiv.org/pdf/2401.11852) mostra que
**BERT fine-tuned em trechos selecionados** bate modelos maiores em texto
inteiro — mais evidência para "escolher o trecho certo".

### 4.2 Projetos análogos

| Projeto | O que faz | Como classifica | O que aprender |
|---|---|---|---|
| [**Querido Diário**](https://github.com/okfn-brasil/querido-diario-data-processing) (OKBR) | Diários oficiais de 469 municípios | **Apache Tika** → texto; busca **léxica** por tema → trechos de 2.000 chars; **rerank por embedding** (BERTimbau) | Léxico primeiro, semântico depois, sobre *trechos* e não o documento. O README não menciona OCR — para gazetas modernas, não precisou |
| [**QuitérIA**](https://tmc.com.br/politica/azmina-quiteria-ia-projetos-lei-genero-congresso/) (AzMina) | 2.036 PLs sobre gênero, Câmara + Senado | Palavras-chave + classificações "construídas a partir de análises humanas anteriores"; **validação humana diária**; divergências vão para revisores | O projeto mais parecido com o ZIL que existe no Brasil. Chegou a 2 mil projetos **mantendo humano no loop todo dia**, não automatizando a decisão |
| [**Radar Legislativo**](https://radarlegislativo.org/sobre/) (Coding Rights) | PLs de tecnologia e direitos digitais | Lista curada à mão + agenda semanal + bot no Telegram | Escopo estreito e curadoria manual escalam quando o tema é bem delimitado |
| [**Ulysses**](https://github.com/ulysses-camara) (a própria Câmara) | ML para o processo legislativo | Corpora: [UlyssesNER-Br](https://aclanthology.org/2024.propor-1.30.pdf) (NER, F1 ~81%), [Tesemõ](https://link.springer.com/article/10.1007/s10579-024-09762-8) (corpus jurídico-governamental grande) | Existe corpus brasileiro para fine-tuning no domínio; não achei trabalho da Câmara em classificação por tópico |
| [**LexML Brasil**](https://projeto.lexml.gov.br/documentacao/Parte-2-LexML-URN.pdf) | Identificador canônico de normas | URN `urn:lex:br:federal:lei:2011-12-14;12546` | Resolve "qual lei é essa" de forma estável — útil para o `extract_citacoes` do enriquecimento |

---

## 5. Análise comparativa das abordagens

| | Regex sobre ementa **(hoje)** | + Temas oficiais da Câmara | Léxico + rerank semântico sobre **texto integral** (Querido Diário) | LLM zero-shot sobre texto/parecer, codebook no prompt | Transformer **fine-tuned** (BERTimbau) | **Híbrido com humano no loop** |
|---|---|---|---|---|---|---|
| Precisão esperada | baixa; 3 tipos de erro conhecidos | filtra o nunca-ZIL; não decide o que é | média; depende do vocabulário | **58–83%** (lit.); 83% onde 2 modelos concordam | potencialmente a maior (lit.) | a do melhor componente + humano nos incertos |
| Recall (cobertura) | **desconhecido**; descarta o que não casa | — | melhora: casa no texto, não na ementa | melhora: lê o tema, não a palavra | melhora | idem |
| Resolve "tema fora do vocabulário" | não | não | parcialmente | **sim** | sim, se treinado | sim |
| Precisa de texto integral | não | não | sim | sim (ou parecer) | sim | sim |
| Precisa de OCR | não | não | só acervo < 2008 | idem | idem | idem |
| Auditável | **sim** (keyword) | sim (tema) | sim (trecho + score) | **só se a evidência for gravada** — pedir citação literal no prompt | não (caixa-preta) | sim, se cada camada gravar evidência |
| Confiança calibrada | não (0/1) | não | score contínuo | **concordância entre modelos/execuções** | probabilidade | sim |
| Custo por proposição | ~0 | 1 request | 1 download + CPU | centavos | treino caro, inferência barata | centavos + minutos humanos nos incertos |
| Dados de treino | nenhum | nenhum | nenhum | **nenhum** | **centenas de rótulos** — não temos | — |
| Reprodutível | sim | sim | sim | **não** (−8 pp se forçar) | sim | parcial |
| Esforço | — | 1 dia | 1–2 semanas | 1 semana | meses + corpus | 2–3 semanas |

**Leitura da tabela:** nenhuma coluna isolada vence. O regex é auditável mas
cego; o LLM enxerga mas não é reprodutível nem auditável sem disciplina; o
fine-tuning é o teto mas exige um corpus que o projeto levará um ano para
ter. A coluna da direita é a única que combina as três propriedades que o
projeto não pode abrir mão de — **ler o texto, explicar a decisão, manter o
humano onde a decisão é editorial** — e é exatamente o desenho em que a
literatura (concordância → automatiza; discordância → humano) e a QuitérIA
(validação humana diária) convergiram.

### 5.1 Sobre OCR, especificamente

A premissa de que "precisamos de um pipeline com OCR" **não se sustenta para a
janela do projeto**. Medido: de 2010 em diante o inteiro teor é texto nativo.
OCR seria necessário para (a) o acervo anterior a ~2008, que está fora do
escopo 2023+, e (b) anexos escaneados eventuais, que não encontrei. A
recomendação é tratar OCR como **módulo de contingência** acionado quando a
extração devolver menos de N caracteres por página — o padrão do
[querido-diario-toolbox](https://github.com/okfn-brasil/querido-diario-toolbox),
que lista Tesseract como dependência mas não o põe no caminho principal.

### 5.2 Sobre "cobertura completa a partir de fontes canônicas"

É alcançável sem scraping: a API da Câmara lista cada documento da tramitação
com `url` (C4), a do Senado lista os `textos` (C7), e o Planalto já é usado
para as leis. O que falta é **um modelo de dados para documentos** — hoje a
`Proposicao` tem um `url_inteiro_teor` e nada mais. Uma tabela `documento`
(proposição, tipo, codteor, url, hash do conteúdo, texto extraído, método de
extração) é o que torna a cobertura verificável: dá para perguntar "de quais
proposições curadas temos o parecer?" e ter resposta.

---

## 6. Recomendação

Não substituir o classificador. **Mudar a entrada e a saída dele**, em camadas
que cada uma sozinha já melhora algo e nenhuma depende da seguinte para
existir:

| Camada | O que faz | Resolve | Custo |
|---|---|---|---|
| **0. Persistir o que já temos** | Gravar indexação e evidência de keyword (issue #27) | auditabilidade | horas |
| **1. Temas oficiais como filtro** | Buscar `/temas`; descartar "Homenagens", "Esporte"…; gravar | recall/precisão na borda, de graça | 1 dia |
| **2. Tabela de documentos + extração** | Baixar inteiro teor e pareceres; Tika ou `pdfplumber`; OCR só se texto < N chars/página | entrada | 1 semana |
| **3. Leitor do texto** | LLM com o codebook ZIL **e o manifesto** no prompt, lendo parecer (se houver) senão texto integral; saída = categorias + **citação literal** + confiança; 2 execuções ou 2 modelos → concordância | tema fora do vocabulário | 1 semana |
| **4. Fila de revisão** | Concordância alta → entra; discordância → humano. Cada revisão humana vira rótulo | ambiguidade, e cria o corpus para H5 | 1 semana |

A **direção** (`sim`/`nao`) e o **peso** continuam onde estão: na curadoria
humana, com o dossiê como apoio. Nada aqui toca nisso — e é importante que
não toque, porque é a tese do projeto.

**Por que nessa ordem:** 0 e 1 não precisam de nada novo e já pagam o
diagnóstico. 2 é infraestrutura que 3 e 4 exigem. 3 sem 4 repete o erro que a
literatura mapeou (confiar no zero-shot sozinho). 4 é o que, em um ano,
produz o corpus que torna H5 possível.

---

## 7. Riscos e o que ainda não sabemos

- **Recall nunca foi medido.** Não sabemos quantas proposições ZIL o
  `candidatas.py` descarta por não casar keyword. É o número mais importante
  que falta, e o experimento da seção 8 o produz.
- **"Soberania industrial" pode não ser legível para um LLM sem o manifesto.**
  Se S1 falhar, a camada 3 precisa de few-shot com as 7 curadas — que é pouco.
- **Não-determinismo.** A camada 3 dará respostas diferentes em execuções
  diferentes. Isso é propriedade, não bug — a concordância é o sinal — mas
  precisa ficar escrito na metodologia pública.
- **Custo de API da Câmara.** S2. 1.200 downloads a 300 ms são 6 min; se o
  parecer médio for grande, é mais. Medir no experimento.
- **Dependência de um fornecedor de LLM** para uma camada do pipeline de um
  projeto que se diz auditável. Mitigação: gravar a citação literal que
  justificou cada rótulo, para que a decisão seja verificável sem o modelo.

---

## 8. Próximos passos propostos — experimentos antes de código

1. **Experimento H1/H2/H4 (2 dias, sem mudar o produto):** para as 7 votações
   curadas e as ~30 proposições que a curadoria já viu, baixar ementa,
   indexação, parecer e texto integral; classificar com o regex atual e com
   um LLM lendo cada fonte; comparar com o rótulo humano. Sai uma tabela
   fonte × método × acerto. Decide as três hipóteses de uma vez.
2. **Medir recall (1 dia):** pegar 50 proposições com tema oficial
   "Energia, Recursos Hídricos e Minerais" ou "Indústria, Comércio e
   Serviços" que o regex **não** classificou, e um humano diz quantas são ZIL.
   É o número que ninguém tem.
3. **Decidir o RFC-005 (#39)** com os dados de 1 e 2 — a granularidade da
   taxonomia e a arquitetura do classificador são a mesma decisão vista de
   dois lados.
4. Só então as camadas 0–4 da seção 6, nessa ordem.

---

## 9. Decisão

*(vazia — é da maintainer)*

---

## 10. Reprodutibilidade das medições

Todas as medições da seção 3.1 foram feitas com `httpx` contra
`https://dadosabertos.camara.leg.br/api/v2` e `https://legis.senado.leg.br/dadosabertos`
em 2026-10-21, a partir do `.venv` do projeto, sem dependências além das já
instaladas. A verificação de camada de texto nos PDFs usou apenas `zlib` e `re`
da biblioteca padrão: inflar os streams `FlateDecode` e contar operadores
`Tj`/`TJ` e objetos `/Subtype /Image`. Um script que repete tudo cabe em 80
linhas e pode acompanhar o experimento da seção 8.

# Discovery: Bússola ZIL — proveniência, framework e expansão

**Data:** 2026-10-29
**Estado:** levantamento, não decisão. Propõe; quem decide é a maintainer.
**Pergunta que motivou:** "De onde vem o número exibido? Quem define a meta?
Como se sabe o quanto falta? É confiável? Como saber?"

A resposta curta é que, até 2026-10-29, a página não tinha como responder a
nenhuma das quatro perguntas, porque o dado por trás dela não as respondia.
Este documento registra o que a Bússola afirma, o que sustenta, o que
falta, e propõe um framework para que cada indicador publicado seja
reproduzível por quem quiser conferir.

Método: um agente mapeou código, dados e documentação (§1); quatro agentes
especialistas investigaram em paralelo, com acesso à web, as fontes
canônicas (§2 e §4), a engenharia de dados (§3), a API e os testes (§3) e a
apresentação (§5). Eu cruzei os relatórios, resolvi contradições e marquei o
que ficou incerto (§7). Toda afirmação externa tem URL; o que não foi
confirmado está dito como tal.

---

## 1. Diagnóstico: o que existe hoje

### 1.1 O dado — `data/bussula/marcos.yml`

Quatro indicadores, publicados em 2026-04-02 e nunca atualizados desde então.
Sem histórico: só o valor atual.

| Código | Nome | Valor | Meta / prazo | Fonte declarada | Dado de |
| --- | --- | --- | --- | --- | --- |
| BUSSULA-FER-01 | Dependência de importação de fertilizantes | 87% do consumo | 60 / 2030 | ANDA (associação setorial) | 2024-12 |
| BUSSULA-MIN-01 | Exportação de nióbio processado vs. bruto | 95% processado | 100 / 2028 | ANM | 2024-06 |
| BUSSULA-ENE-01 | Participação de renováveis na matriz elétrica | 83% | 90 / 2030 | ANEEL | 2024-12 |
| BUSSULA-EDU-01 | Investimento em P&D como % do PIB | 1,2% | 2,0 / 2030 | MCTI | 2023-12 |

O que o arquivo **não** dizia até o commit `058f45d`:

- **Quem definiu a meta.** Nenhuma das quatro metas cita plano, lei ou
  documento. São escolhas do projeto, apresentadas na página como se fossem
  oficiais.
- **Onde está o dado.** `fonte_url` é a página inicial do órgão
  (`anda.org.br/`, `gov.br/anm/`, `aneel.gov.br/`, `gov.br/mcti/`), não a
  tabela, série ou relatório de onde o número saiu. Não dá para reproduzir.
- **Em que sentido o indicador melhora.** Sem o campo, a página calculava o
  progresso como `valor / meta` travado em 100%: fertilizantes (87% com meta
  de 60%, onde menor é melhor) aparecia com a barra **cheia**, o indicador
  mais distante da meta.
- **Se alguém revisou.** Não havia estado de validação, ao contrário de
  `data/direcoes/`, que marca `nao-validado`/`revisado`.
- **Base e ano-base.** Sem eles, "quanto falta" é só uma razão entre dois
  números, não um caminho percorrido.
- **O que é a tendência.** "Estável" e "Avançando" são texto digitado, não
  variação medida entre duas observações.
- **Ambiguidades de definição.** ENE-01 descreve "capacidade instalada" mas
  a unidade diz "% da matriz elétrica"; FER-01 não diz se é consumo aparente
  ou entregas ao mercado, nem se é por nutriente ou agregado; MIN-01 não diz
  se a razão é em valor ou em volume nem qual NCM.
- **Fonte de natureza setorial.** A ANDA é associação da indústria de
  fertilizantes. A constituição do projeto (`.specify/memory/constitution.md`,
  linhas 80-81) pede "fontes oficiais independentes (ANM, ANATEL, TSE, IBGE)".

### 1.2 A API — `apps/api/routers/bussula.py`

Até `058f45d`: lia o YAML a cada requisição e devolvia o dicionário cru, sem
schema, cache, validação ou cálculo. Arquivo ausente devolvia `[]` em
silêncio — a armadilha do mount `./data:/data:ro` que o CLAUDE.md já
registra para o classificador. Nenhum teste em `tests/` tocava a Bússola.

### 1.3 A página — `apps/web/app/bussula/page.tsx`

Até `058f45d`: progresso invertido (acima); "Indicadores em formação" como
texto fixo, sem vir do dado; fetch sem conferir `r.ok`; rótulos de categoria
duplicados à mão; selo de tendência quebrando em duas linhas (o `Selo` do
kit punha ícone e texto dentro de um `span.truncate`, e o preflight do
Tailwind faz `svg` ser `display:block`).

### 1.4 A infraestrutura que poderia alimentar a Bússola e não alimenta

`apps/workers/fontes/` (ADR-008) já tem o que um pipeline de indicadores
precisa: catálogo de fontes com `natureza`, `primaria`, `vies_declarado` e
`revisavel`; allowlist de hosts aplicada no transporte; consulta por
intervalo explícito; cache. Mas:

- nenhuma série do catálogo cobre as quatro métricas (há Selic, IPCA,
  câmbio, população);
- Comex Stat, Tesouro e Portal da Transparência estão desabilitados, sem
  adaptador;
- `marcos.yml` não referencia série nenhuma, e as métricas são razões
  compostas (importado ÷ consumo; processado ÷ total) que o cliente não
  calcula;
- não há onde guardar histórico (o cache tem 24h e fica fora do git);
- o slot `bussula` do briefing do painel existe e nunca é preenchido.

### 1.5 Processo: quatro documentos, quatro regras

| Documento | Regra para atualizar a Bússola |
| --- | --- |
| `docs/PRD.md` §12 e cabeçalho do YAML | PR + 1 aprovação + link da fonte |
| `docs/ROADMAP.md` | PR + review em issue |
| `docs/GOVERNANCE.md` | decisão operacional, consenso de 48h |
| `CLAUDE.md` | PRs de `data/` exigem 2 aprovações |

Com uma maintainer, nenhuma das quatro filtra nada — a própria GOVERNANCE
reconhece. O que foi prometido e não existe: linha do tempo por governo
(PRD F4), metodologia de escolha dos marcos (PRD F4), 15–20 indicadores
(PRD-PAINEL), indicadores para SEM/DIG/DEF/AGR/COM (PRD §11). Das cinco
perguntas da Bússola na home, duas ("compromissos cumpridos", "programas
mantidos entre governos") não têm indicador possível na v1.

### 1.6 Mapa de dependências

```
PRD / ROADMAP / GOVERNANCE / CLAUDE.md ──(regras divergentes)──► quem pode mudar o dado
                                                                        │
data/bussula/marcos.yml ──► routers/bussula.py ──► app/bussula/page.tsx ──► leitor
   (valor, meta, fonte)       (schema, progresso)     (cartão, aviso)
         ▲
         │ (nada)
apps/workers/fontes/ ◄── data/fontes/catalogo.yml ◄── BCB · IBGE · IPEA  (Comex Stat, Tesouro: desligados)
```

O laço que falta é o de baixo: a fonte canônica → série no catálogo →
cálculo → histórico versionado → `marcos.yml` → página. Hoje o dado entra
por digitação e sai por digitação.

### 1.7 O que mudou em `058f45d` (Parte 1, já no PR #45)

Sem mudar valor nenhum: `direcao`, `meta_origem` (nulo nos quatro),
`natureza_fonte`, `fonte_dataset` (nulo nos quatro) e `validacao:
nao-validado` entraram no YAML; a API valida o arquivo
(`schemas/bussula.py`) e calcula `progresso_pct`, `meta_atingida` e
`meta_provisoria` e `distancia_meta`; a página mostra o sentido do
indicador, a meta como provisória, a natureza da fonte, a data do dado e
"Não validado", e o aviso do topo resume o estado real do conjunto. A
barra só aparece com `base` declarada, pela fórmula `(atual − base) ÷
(meta − base)`; sem base — hoje, nos quatro — a página mostra só a
distância ("faltam 27 pontos"). Os engenheiros e as duas análises de dados
concordaram que nenhuma razão sem base (`valor/meta`, `meta/valor`) mede
caminho percorrido. 16 testes. Isso torna a página
honesta; não torna o dado melhor. O resto deste documento é sobre o dado.

---

## 2. Verificação dos quatro indicadores

Duas análises independentes (o analista desta sessão e o da sessão
paralela da maintainer), com fontes primárias lidas — PDFs baixados, APIs
chamadas — e imprensa marcada como secundária. Convergiram em tudo que
importa. Convenção: **ano-ref** é o ano a que o dado se refere, não o da
publicação.

| Código | YAML | Fonte primária | Meta oficial | Tendência medida | Veredito |
| --- | --- | --- | --- | --- | --- |
| FER-01 | 87% · meta 60 / 2030 · "estável" | **86,6% (2024), 86,8% (2025)** se a métrica for importação ÷ consumo aparente em toneladas de produto, dados ANDA; outras definições plausíveis dão de 84% a 91% | PNF: **85% → 50% em 2050** (slides do MAPA; o Decreto 10.991/2022 não tem número); marco implícito ~65% em 2030. **60/2030 não existe** | **Piorando**: +0,5 pp/ano, 2019–25, Mann-Kendall p = 0,011 | divergente: valor plausível, definição não declarada, fonte setorial, meta inventada, tendência errada |
| MIN-01 | 95% · meta 100 / 2028 · "estável" | ANM: **"em sua totalidade"** o nióbio sai como ferronióbio (ano-ref 2023 e 2024). Comex Stat 2025: 98,6% em valor, 99,3% em peso | nenhuma; o PNM 2050 só tem metas agregadas | estável em ~99%, sem tendência | divergente: 95 não aparece em fonte alguma; a meta já está atingida; indicador **saturado**, não mede nada |
| ENE-01 | 83% · meta 90 / 2030 · "avançando" | por **geração** (EPE/BEN): 88,2% (2024), **86,8% (2025)**; por **capacidade** centralizada (ANEEL/SIGA): 84,6–84,7% em 2026, sem geração distribuída. O YAML descreve capacidade e rotula "matriz elétrica" | **não existe meta de 90%**; o Plano Clima projeta 82,7% em 2030 e o PDE 2035 ~86% em 2035 — cenários, não metas | sem tendência (hidrologia domina); os três últimos anos **caem** (89,2 → 88,2 → 86,8) | divergente: 83 não bate com nenhuma definição atual (coincide com o BEN de 2019), meta inventada, "avançando" é falso |
| EDU-01 | 1,2% · meta 2,0 / 2030 · "estável" | MCTI: **1,19% em 2022 e 2023** (via IPEA; o MCTI bloqueia leitura automática com CAPTCHA). 2024 ≈ 1,23%, não confirmado na fonte | **existe**: ENCTI 2024–2034, Portaria MCTI 10.226/2026 — 2% do PIB **em 2034**, não 2030 | estável, +0,01 pp/ano; ritmo necessário é 10× o observado | confirmado com ressalva: valor e tendência conferem; o prazo está errado |

### 2.1 Fertilizantes (FER-01)

- **Definição.** A ANDA publica entregas ao mercado (D), produção nacional
  de intermediários (P), importação (M) e exportação (X), em toneladas de
  produto, ano civil. Quatro razões são possíveis e dão números diferentes
  em 2024: M/D = 90,6%; M/(M+P) = 85,4%; 1 − P/D = 84,6%; **M/(P+M−X) =
  86,6%**, que arredonda para o 87 do YAML. É hipótese de origem, não
  confirmação. Por nutriente (N, P₂O₅, K₂O) o número muda, porque o
  importado é mais concentrado; ninguém publica essa versão.
- **Fonte.** ANDA é associação setorial; o portal público não tem o dado
  (o "Sistema de Pesquisa Setorial" exige login) e os PDFs anuais estão em
  [anda.org.br/recursos](https://anda.org.br/recursos/) ([2025](https://anda.org.br/wp-content/uploads/2026/04/Principais_Indicadores_2025.pdf)).
  A fonte estatal para importação é o **Comex Stat** (MDIC, API aberta,
  `POST /general`, capítulo 31 da NCM): 44,28 Mt em 2024, 45,50 Mt em 2025 —
  ~3 Mt acima da ANDA porque inclui misturas prontas e outros usos. Não há
  fonte estatal de produção nacional em série; o próprio MAPA repete a ANDA.
- **Meta.** O [Decreto 10.991/2022](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/d10991.htm)
  cria o PNF e o CONFERT sem número. A meta vigente está nos slides do MAPA
  à Câmara ([30/09/2025](https://www2.camara.leg.br/atividade-legislativa/comissoes/comissoes-permanentes/cme/apresentacoes-em-eventos/apresentacao-de-convidados-2025/30-09-2025-16h-projeto-santa-quiteria/MAPA.pdf)):
  reduzir de 85% para 50% até 2050; produção nacional de 19,6 Mt (35%) em
  2030. O PNM 2050 (Portaria MME 924/2026) tem meta própria só para fósforo
  e potássio (87,3% → 34,9% em 2050).
- **Progresso e tendência.** Com a base oficial do PNF (85) e a meta (50),
  o valor de 2025 (86,8) dá **−5,1%**: retrocesso. Ritmo necessário até
  2050: −1,47 pp/ano; observado: +0,50 pp/ano. "Estável" está errado.
- **Revisões.** A ANDA revisou a produção de 2022 (7,45 → 7,73 Mt) e de 2024
  (7,21 → 7,04 Mt): é fonte `revisavel`.

### 2.2 Nióbio (MIN-01)

- A ANM ([Sumário 2024](https://www.gov.br/anm/pt-br/assuntos/economia-mineral/publicacoes/sumario-mineral/sumario-mineral-brasileiro-2024/niobio-2024-ano-base-2023.pdf),
  [Sumário 2025](https://www.gov.br/anm/pt-br/assuntos/economia-mineral/publicacoes/sumario-mineral/sumario-mineral-brasileiro-2025/sumario-2025.pdf))
  diz que a totalidade da exportação é ferronióbio (NCM 7202.93.00), US$ 2,38
  bi em 2024. No Comex Stat, contra a NCM 2615.90 ("minérios de nióbio,
  tântalo ou vanádio"), o processado é 98,6% em valor e 99,3% em peso em
  2025 — e a 2615.90 provavelmente é concentrado de tântalo (preço de US$
  20–55/kg), não nióbio bruto. Óxidos e ligas especiais de alto valor caem
  em NCMs genéricas e não dá para isolá-los.
- Não existe meta oficial; a de 100% é editorial e já foi atingida pelo
  critério da ANM. O indicador está **saturado**: com |meta − base| de 1 pp,
  ruído de ±0,3 pp muda o progresso em ±27 pp. Recomendação dos dois
  analistas: trocar por uma métrica com espaço para variar — participação
  de produtos de maior valor (óxidos, nióbio metálico, ligas especiais),
  valor por tonelada de Nb contido, ou concentração de destino (China
  44,5% em 2024).

### 2.3 Renováveis (ENE-01)

- Duas definições legítimas, dois números: **geração** (EPE/BEN, inclui
  importação e geração distribuída; [BEN 2026](https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-975/topico-847/BEN_S%C3%ADntese_2026_PT.pdf):
  86,8% em 2025, 88,2% em 2024, 89,2% em 2023, 78,1% em 2021) e **capacidade
  centralizada** (ANEEL/SIGA, [CSV aberto](https://dadosabertos.aneel.gov.br/dataset/siga-sistema-de-informacoes-de-geracao-da-aneel),
  exclui ~45 GW de solar distribuída): 84,67% em 01/10/2026, cálculo
  próprio sobre o CSV. O 83 do YAML não é nenhuma das duas em 2024; bate
  com o BEN de ano-ref 2019.
- Não há meta de 90%. O Plano Clima (consulta pública 2025) projeta 82,7%
  em 2030; o PDE 2035 projeta ~86%. São cenários. A NDC não fixa percentual
  de renováveis na matriz elétrica.
- Tendência: na geração a hidrologia domina (desvio residual ~4 pp; 2021
  caiu a 78,1% na crise hídrica); em 5–7 anos não há tendência
  significativa, e os três últimos anos caem. Para indicador estrutural,
  usar capacidade; para conjuntural, geração em média móvel de 3 anos.

### 2.4 P&D (EDU-01)

- Dispêndio nacional em P&D (público + empresarial), padrão Frascati/OCDE:
  1,19% em 2022 e 2023 ([IPEA citando a tabela 2.1.3 do MCTI](https://ipea.gov.br/cts/pt/central-de-conteudo/artigos/artigos/499-evolucao-dos-dispendios-em-pesquisa-e-desenvolvimento));
  pico de 1,28% em 2015; 2020 revisado de 1,14 para 1,22 com a revisão do
  PIB. O MCTI bloqueia leitura automática (CAPTCHA); nenhum dos dois
  analistas contornou. Defasagem típica: 18–30 meses — "atualização
  trimestral" não é viável para este indicador.
- A meta existe: [ENCTI 2024–2034](https://www.in.gov.br/en/web/dou/-/portaria-mcti-n-10.226-de-28-de-julho-de-2026-722113720)
  (texto integral em [cópia do IBICT](https://portal-cct.prd.ibict.br/files/original/6c7c0f15bdcfed82c8b70c48e14142dfa942b5c9.pdf)):
  "alcançar 2% do PIB em P&D até **2034**". O YAML diz 2030. A ENCTI
  2016–2022 tinha 2% até 2019 e não foi cumprida.
- Ritmo necessário de 2024 a 2034: +0,077 pp/ano; observado 2020–24: +0,008.

### 2.5 O que os quatro têm em comum

Nenhum declara definição operacional (numerador, denominador, unidade,
códigos), nem ano-ref separado da publicação, nem vintage. Três das quatro
metas não existem em documento oficial e a quarta tem prazo errado. Nenhum
`fonte_url` leva ao dado. A tendência é digitada, e em dois casos está
errada. E a atribuição `governo_referencia: Lula III` em dado de ano-ref
anterior a 2023 (possível em EDU) é indevida.

### 2.6 Método estatístico para tendência

Proposto pela análise da sessão paralela e adotado aqui: série anual na
vintage mais recente, janela de 5 a 7 pontos, **n mínimo 5** (abaixo disso,
"dados insuficientes"); Mann-Kendall exato mais inclinação de Theil-Sen;
"avançando"/"retrocedendo" só com p < 0,10 **e** |Theil-Sen × janela| maior
que um desvio-padrão residual, conforme a direção; fora disso, "estável".
Séries mensais (ANDA, SIGA, Comex Stat) em 12 meses móveis antes do teste;
séries hidrológicas em média móvel de 3 anos. Dado provisório (parcial do
ano, Síntese antes do Relatório Final) não entra no teste. Aplicado hoje:
FER retrocedendo (p = 0,011), MIN estável (saturado), ENE estável (alta
variância), EDU estável — contra o YAML, que diz estável, estável,
avançando, estável.

## 3. Framework de indicadores

Um indicador publicável é um indicador que **outra pessoa consegue
reproduzir**: a partir do que o YAML diz, chega ao mesmo número na mesma
fonte, entende por que a meta é aquela e sabe se o dado está velho. O
framework tem cinco partes: o que o dado declara (§3.1), onde o histórico
vive (§3.2), como o número chega lá (§3.3), o que a API garante (§3.4) e o
que barra um PR (§3.5).

Fonte das três primeiras partes: relatório do engenheiro de dados, que leu
o YAML, o pacote `apps/workers/fontes/`, o catálogo, o ADR-008, os
validadores existentes, `render.yaml` e a CI, e pesquisou as APIs das
fontes.

**O princípio que organiza tudo.** Hoje o YAML mistura três coisas que
mudam por motivos diferentes:

| Camada | Onde vive | Quem escreve | Muda como |
| --- | --- | --- | --- |
| Definição editorial (o que mede, direção, meta e sua origem, fonte) | `data/bussula/marcos.yml` | humano | PR com revisão |
| Observações no tempo (valor, data de referência, de onde saiu) | `data/bussula/historico/<codigo>.csv` | script ou humano | PR, só acrescentando linhas |
| Derivados (progresso, tendência, defasagem, confiança) | resposta da API | código | nunca gravados |

Consequência: o script de atualização **não reescreve YAML** (PyYAML
descarta comentários, e o cabeçalho é documentação); só acrescenta linhas
ao CSV. `valor_atual` e `ultima_atualizacao` ficam no YAML como cópia
denormalizada do último ponto, por legibilidade e compatibilidade, e o
validador exige que batam com o CSV — este é o ponto em que os dois
engenheiros divergiram (dados: derivar tudo do CSV; software: manter a
cópia e conferir); fico com a cópia conferida, porque a página e o PR de
dados continuam legíveis sem abrir dois arquivos.

### 3.1 Schema v2 do indicador

Validado por `MarcoYAML` (Pydantic 2, `extra="forbid"`), reaproveitando os
vocabulários que já existem: `NATUREZAS` de `catalogo.py`, os estados de
`validacao` de `data/direcoes`, as frequências do catálogo. Exemplo
completo para FER-01, com os campos novos comentados:

```yaml
versao: 2
marcos:
  - codigo: BUSSULA-FER-01
    nome: Dependência de importação de fertilizantes
    categoria: ZIL-FER                     # existe em data/taxonomia/categorias.yml
    validacao: nao-validado                # nao-validado | revisado
    natureza_fonte: associacao_setorial    # estatal | autarquia | associacao_setorial | academia | imprensa
    vies_declarado: >                      # obrigatório se associacao_setorial ou imprensa (≥ 40 caracteres)
      Associação da indústria de fertilizantes; interesse direto na política do setor.

    metrica:
      definicao: >                         # uma frase: o que o número significa
        Parcela do fertilizante consumido no Brasil, em toneladas de produto,
        que foi importada no ano civil.
      unidade: "%"
      direcao: menor_melhor                # maior_melhor | menor_melhor
      formula: "100 * importacao / (producao + importacao - exportacao)"   # só + - * / ( ); avaliada por AST, nunca eval
      agregacao: soma_anual                # soma_anual | media_anual | ultimo_do_ano | nenhuma
      casas_decimais: 1

    entradas:                              # cada uma: `serie` (catálogo, automático) XOR `fonte_dataset` (manual)
      importacao: { serie: comex_stat.fert_importacao_t }
      exportacao: { serie: comex_stat.fert_exportacao_t }
      producao:
        fonte_dataset:
          fonte: anda
          url: https://anda.org.br/…/Principais_Indicadores_2024.pdf
          metodo: pdf                      # manual | planilha | pdf
          campo: "Produção nacional de fertilizantes intermediários (t)"

    base: { valor: 85, ano: 2021 }         # obrigatório para publicar quando há meta
    meta:
      valor: 50
      prazo: 2050
      origem:                              # obrigatório se validacao: revisado e meta.valor existe
        tipo: oficial                      # oficial | editorial (fixada pelo projeto; a UI diz isso)
        documento: Plano Nacional de Fertilizantes 2022-2050 — apresentação do MAPA à CINDRA
        url: https://www2.camara.leg.br/…/MAPAJOSPOLIDORO.pdf
        trecho: "reduzir a dependência externa de 85% para 50% até 2050"
        verificado_em: null                # quem conferiu o trecho na URL, e quando

    cadencia: anual                        # mensal | trimestral | anual
    defasagem_meses: 4                     # quanto depois do período o dado costuma sair
    revisavel: true
    politica_revisao: manter_vintage       # manter_vintage | substituir (nunca para revisavel: true)
    tolerancia_tendencia: 1.0              # em unidades da métrica; |Δ| menor = "estável"
    quebras: []                            # [{data_referencia, motivo, url}] — mudança de metodologia
    valor_atual: 87                        # cópia do último ponto do CSV; o validador confere
    ultima_atualizacao: "2024-12"
    notas: Medido em toneladas de produto, não de nutriente.
```

(Os valores de `base`, `meta` e `origem` acima são **ilustrativos**: a
origem da meta de fertilizantes não foi confirmada — ver §7.)

O que é obrigatório para a carga passar, o que é obrigatório para
`validacao: revisado`, e o que pode ficar nulo com aviso na interface:

| Campo | Carga | Revisado | Nulo → a UI mostra |
| --- | --- | --- | --- |
| identidade, `validacao`, `natureza_fonte`, `metrica.{definicao,unidade,direcao}`, `cadencia`, `revisavel` | sim | sim | erro de carga |
| `metrica.formula` | se há > 1 entrada | idem | erro |
| `entradas` (≥ 1) | sim | sim | erro |
| ≥ 1 linha no CSV | não | sim | "sem dado publicado" |
| `base` | não | sim, se há meta | barra oculta |
| `meta` | não | não | "sem meta pública" |
| `meta.origem` | não | **sim, se há meta** | "meta sem origem documentada" (impede `revisado`) |
| `vies_declarado` | se fonte setorial/imprensa | idem | erro |

`governo_referencia` **sai do schema**: é derivável da data de referência
por uma tabela de mandatos e, digitado à mão, é o campo mais fácil de virar
editorialização (converge com §5.4).

**Indicador publicável**, como lista verificável: (1) carrega no schema;
(2) `validacao: revisado`; (3) CSV com ≥ 1 linha e data de referência não
futura; (4) se há meta, `meta.origem.url` responde e `trecho` não está
vazio; (5) se há meta, há `base`; (6) toda `serie` existe no catálogo com a
fonte habilitada, e toda `fonte_dataset.url` tem host catalogado; (7) dado
não mais velho que 2× cadência + defasagem; (8) fonte setorial declarada
em `vies_declarado`. Falha em 1–2: não aparece. Falha em 3–8: aparece com
aviso e sem barra.

### 3.2 Histórico

`data/bussula/historico/<codigo>.csv`, **append-only**, versionado em git:

```csv
data_referencia,valor,unidade,fonte_url,data_coleta,metodo,revisao_de,vintage,nota
2023-01-01,86.1,%,https://anda.org.br/…/Principais_Indicadores_2023.pdf,2026-04-02,pdf,,2024-09,
2024-01-01,87.0,%,https://anda.org.br/…/Principais_Indicadores_2024.pdf,2026-04-02,pdf,,2025-03,
2024-01-01,86.4,%,https://api-comexstat.mdic.gov.br/general?…,2026-11-03,comex_stat+pdf,2026-04-02,2026-11,"recalculado com Comex Stat"
```

- `data_referencia` em ISO: anual `AAAA-01-01`, mensal `AAAA-MM-01` — a
  convenção de `Observacao.data` em `cliente.py`. `data_coleta` é quando o
  número foi lido ou calculado, nunca a data de exibição.
- **Nunca se apaga nem edita uma linha.** Correção = linha nova com
  `revisao_de` apontando para a `data_coleta` superada. A API escolhe, por
  `data_referencia`, a linha de `data_coleta` mais recente; as demais ficam
  em `/bussula/{codigo}/historico?vintages=true`.
- `vintage` = mês de publicação do dataset na fonte, para o aviso "sujeito
  a revisão" que `Linha.para_prompt()` já faz para as séries. `metodo` usa
  o nome do adaptador quando foi automático.
- Ordem canônica por `data_referencia`, depois `data_coleta`; o validador
  reordena e falha se o arquivo não estiver canônico (diff limpo no PR).
- **Revisão retroativa**: fonte `revisavel: true` republica anos passados;
  o script compara e acrescenta linhas com `revisao_de`. Se a revisão toca
  > 20% das linhas ou inverte a tendência, o PR recebe rótulo
  `revisao-grande` e tabela antes/depois: é decisão editorial.
- **Quebra de série** (a fonte mudou a metodologia) fica no YAML, em
  `quebras`, porque é fato sobre a definição; a tendência não compara
  observações de lados diferentes da quebra. Se o conceito mudou
  (capacidade → geração), é **novo código** e `descontinuado_em` no antigo.
- **Unidade** é coluna do CSV para o validador recusar mistura (`%` com
  `p.p.`, `t` com `kt`) sem conversão declarada.

Por que CSV em git e não tabela no Postgres: a fonte de verdade editorial
vive em `data/` e muda por PR (regra do projeto); `git blame` por linha é a
auditoria; a revisão por segunda pessoa é o fluxo de PR que já existe; o
`plan: free` do Render pode expirar o banco; e o volume (4–20 indicadores ×
≤ 50 anos) é minúsculo. Se um gráfico um dia precisar de SQL, materializar
o CSV numa tabela na subida da API — o banco vira cache, nunca origem.

### 3.3 Pipeline

**Adaptadores que faltam** em `apps/workers/fontes/` (cada um entra em
`ADAPTADORES` de `catalogo.py` e no dicionário de `cliente.py`, com um
teste gravado de resposta real — a convenção do catálogo):

| Indicador | Entrada | Adaptador | Host | Estado da verificação |
| --- | --- | --- | --- | --- |
| FER-01, MIN-01 | importação/exportação por NCM (cap. 31; 2615.90 minério × 7202.93 ferronióbio) | `comex_stat` (novo) | `api-comexstat.mdic.gov.br`, já catalogado e desabilitado | API existe; **formato da requisição não verificado** — só o manual do pacote R `comexr` ([PDF](https://archlinux.nic.cz/R/web/packages/comexr/comexr.pdf)): endpoints `/general`, `/general/filters/{f}`, `/tables/classifications`; período `"YYYY-MM"`; métricas FOB, KG, quantidade; detalhe por NCM/SH4/SH2/país. Aviso do pacote: a cadeia ICP-Brasil às vezes não é reconhecida — o adaptador falha declarando, nunca desliga TLS |
| FER-01 | produção nacional | `fonte_dataset` (PDF anual da ANDA) | `anda.org.br` (nova fonte, `habilitada: false`) | PDFs 2016–2026 em [anda.org.br/recursos](https://anda.org.br/recursos/); conteúdo não lido |
| ENE-01 (capacidade) | capacidade por fonte | `ckan_csv` (novo, genérico) | `dadosabertos.aneel.gov.br` | CSV `siga-empreendimentos-geracao.csv` [existe](https://dadosabertos.aneel.gov.br/dataset/siga-sistema-de-informacoes-de-geracao-da-aneel); colunas não conferidas |
| ENE-01 (geração) | geração por fonte | `fonte_dataset` (planilha do BEN/EPE) | `www.epe.gov.br` | página de dados abertos existe; formato não conferido |
| EDU-01 | dispêndio em P&D / PIB | `fonte_dataset` manual (MCTI) | `www.gov.br` | página respondeu com desafio anti-bot; coleta manual |

**Razões compostas** (`apps/workers/bussula/calculo.py`): para cada
entrada, `serie` → `consultar_serie(ref, inicio, fim)`; `fonte_dataset` →
lê do próprio CSV as linhas `metodo: manual|pdf|planilha` (o humano já
digitou o número da fonte). Alinha por `data_referencia` segundo
`agregacao` — `soma_anual` só aceita ano com 12 meses em **todas** as
entradas (a cautela de `fim_vigente` em `contexto.py`). Avalia `formula`
por `ast` com allowlist. Devolve `(data_referencia, valor, insumos={nome:
(valor, url, data_consulta)})`; os insumos vão para a `nota` do CSV e para
`/historico`, para quem lê reconstruir a conta — o princípio "nenhum número
sem origem" do ADR-008 aplicado à Bússola.

**`scripts/atualizar_bussula.py`**, no estilo de `scripts/fontes.py`:
`--validar` (offline), `--indicador X --dry-run`, `--todos --escrever`
(acrescenta linhas), `--todos --escrever --pr` (branch
`bussula/atualizacao-AAAA-MM-DD`, commit só dos CSVs, `gh pr create` com
URL consultada, `data_consulta`, `Catalogo.hash` e tabela antes/depois).
Nunca escreve em `main`. A revisão humana é o PR — o que dissolve a
divergência PRD/ROADMAP/GOVERNANCE sobre "quantas aprovações" num único
lugar configurável: a proteção da branch.

**Agendar sem Celery**: GitHub Actions `schedule` mensal + `workflow_dispatch`
rodando o script com `--pr`; se Actions estiver indisponível para o
repositório (a memória do projeto diz que está bloqueado), o mesmo comando
roda por `cron` na máquina da maintainer, padrão já aceito em
`docs/DEPLOY.md`. `render.yaml` não muda: a API só lê arquivos; nada no
servidor escreve dado editorial. Cache de séries (24h, efêmero) × histórico
(CSV, permanente): papéis distintos, sem conflito.

**Corner cases** e o tratamento: série descontinuada → `descontinuado_em`,
histórico preservado, novo código para a sucessora; fonte muda URL →
`fonte_url` do CSV é a da época e não muda, as vigentes mudam por PR, e
`--verificar-fontes` detecta 404; meta ultrapassada → progresso 100%,
`meta_atingida`, nova meta exige nova origem e a antiga vai para
`metas_anteriores`; prazo vencido → `meta_vencida`, indicador não some;
anual × trimestral → cada indicador tem uma cadência e comparação entre
indicadores só em "distância até a meta", nunca em valor cru; fonte
secundária sem primária → permitida só com natureza declarada, viés e nota
dizendo qual primária a substituiria; composto com defasagens diferentes →
avança só quando a entrada mais lenta chega, e a UI diz "aguardando
produção 2025 (ANDA, previsto ~abril)".

### 3.4 Contrato da API

Fonte: relatório do engenheiro de software, que leu router, schemas,
validador de direções, CI, Dockerfile, compose e testes existentes.

**Duas camadas, um modelo.** `MarcoYAML` (entrada, `extra="forbid"`) é o
que o arquivo pode conter, e é o mesmo modelo que a API, o validador e os
testes usam — uma fonte de verdade. `Indicador` (saída) herda dele e soma os
campos calculados. `extra="forbid"` pega derivas como o PRD escrever
`governo_atual` e o YAML `governo_referencia`, que hoje ninguém pega.

**Opcional no modelo, obrigatório no validador.** `direcao` e os campos v2
são opcionais em `MarcoYAML` para a API nunca cair por causa de um YAML
antigo; quem barra o merge é o validador na CI. Mesmo modelo, rigor
diferente em cada camada.

**Campos calculados, como funções puras** com `hoje: date` injetado (nunca
`date.today()` dentro do modelo: os testes ficariam presos ao relógio):

| Campo | Regra |
| --- | --- |
| `progresso_pct` | com `base`: `(atual − base) / (meta − base) × 100`, o sinal cancela nas duas direções; travado em 0–100; `meta == base` → nulo. Sem `base`: `maior_melhor` → `atual/meta`; `menor_melhor` → **nulo** (não há zero natural). |
| `meta_atingida` | `progresso ≥ 100` |
| `tendencia_calculada` | com ≥ 2 observações: variação entre as duas últimas; "estável" dentro de 2% da distância base→meta (ou 1% do valor anterior, sem meta); o sinal de "avança" segue `direcao` |
| `tendencia` | calculada, senão a declarada; `tendencia_origem: calculada \| declarada` diz qual |
| `defasagem_meses` | meses entre `ultima_atualizacao` e hoje |
| `vencido` | `defasagem > 2 × cadencia_meses` |
| `confianca` | **baixa** se vencido, fonte setorial/imprensa, sem natureza ou sem `fonte_dataset`; **alta** se revisado, fonte estatal/autarquia/academia, com dataset e fresco; **média** no resto |

Com os dados de hoje e `hoje = 2026-10-29`: os quatro saem `confianca:
baixa` (nenhum validado, nenhum com dataset); EDU (2023-12) e MIN
(2024-06) saem `vencido` com cadência 12. É o diagnóstico honesto, e a
página pode mostrá-lo.

> A primeira versão de `058f45d` calculava `menor_melhor` sem base como
> `meta / atual` (fertilizantes: 69%). Uma razão, não um caminho
> percorrido; os especialistas recomendaram não mostrar nada até existir
> `base`, e foi o que ficou: `progresso_pct` nulo e `distancia_meta` em
> texto. A fórmula com base entra na F1.

**Endpoints.** `GET /bussula` e `GET /bussula/{codigo}` mantidos, com
`response_model_exclude_none=True` para que `meta` ausente continue
ausente no JSON (a página testa `!== undefined`; `null` passaria e daria
`Infinity`). Novo: `GET /bussula/{codigo}/historico`. Na listagem o
`historico` sai vazio; no detalhe, completo.

**Carga.** Cache em memória invalidado por `mtime`; arquivo ausente
continua devolvendo `[]`, mas **avisa uma vez** no log com o caminho e a
dica do mount (feito em `058f45d`); YAML inválido falha alto (500 com
detalhe no log) — o validador na CI impede que chegue a produção, e em dev
um erro visível vale mais que `[]`. Aquecer a carga no `lifespan` para o
aviso aparecer no boot, onde alguém olha. Não trocar
`parent.parent.parent.parent` por `parents[3]`: em `/app/routers/bussula.py`
daria `IndexError`; `Path("/").parent == Path("/")` é o que faz o container
cair em `/data`. Isso vira teste.

### 3.5 Validador, CI e testes

**`scripts/validar_bussula.py`**, espelho de `validar_direcoes.py`, usando o
mesmo `MarcoYAML` da API. Offline, em segundos, erros que fecham o PR:

- YAML parseia; `MarcoYAML` valida (tipos, `extra="forbid"`, padrões de
  `codigo` e `categoria`); códigos únicos; sigla do código casa com a
  categoria (`BUSSULA-FER-01` ↔ `ZIL-FER`); categoria existe em
  `data/taxonomia/categorias.yml`.
- `direcao` presente; `menor_melhor` exige `base`; `base`, `meta` e
  `direcao` coerentes (`menor_melhor` → `meta < base`).
- `validacao: revisado` exige `meta_origem` quando há meta, exige
  `fonte_dataset`, e recusa `fonte_url` que seja só a home do órgão.
- `natureza_fonte` presente; `associacao_setorial` exige `vies_declarado`
  com ≥ 40 caracteres (a régua do catálogo de fontes).
- Unidade em `%` → valores entre 0 e 100; `ultima_atualizacao` não é
  futura; `prazo ≥ ano do dado`; histórico em ordem crescente e o último
  ponto igual a (`ultima_atualizacao`, `valor_atual`); `serie_catalogo`, se
  houver, existe no catálogo.

Avisos (não fecham): tendência declarada ≠ calculada; meta sem origem em
indicador não validado; indicador vencido; natureza ausente. `resumir()`
imprime total, por validação, por confiança, por natureza, vencidos — "o
número que a documentação deveria citar".

`--verificar-fontes` (rede): `fonte_url` e `fonte_dataset` respondem 2xx;
se houver `serie_catalogo`, `consultar_serie` reproduz `valor_atual` dentro
de `tolerancia_verificacao`. Cobertura hoje: zero, até existir adaptador.

**CI.** Job `validate-data` separado (checkout, Python 3.12, `pip install`,
`validar_direcoes.py`, `validar_bussula.py`, `pytest tests/unit/test_bussula.py`),
sem filtro de `paths`, para o check se chamar "dados editoriais" quando um
PR de `data/` quebrar. `sync_pipeline.py` ganha um `step0_validar_dados()`
que aborta antes de tocar o banco; alvo `validar-dados` no Makefile.
Observação: `lint-backend` só cobre `apps/ packages/`; `scripts/` não é
lintado — rodar `ruff` à mão no validador.

**Cron que abre PR: não agora.** Seria um workflow trimestral rodando
`atualizar_bussula.py` e `create-pull-request`, só para indicadores com
`serie_catalogo`, forçando `validacao: nao-validado` e nunca tocando meta,
direção ou texto. Riscos: dado editorial exige revisão humana e um PR de
bot a cada trimestre num repositório com uma maintainer vira fila; PR
aberto com `GITHUB_TOKEN` não dispara CI (exige PAT ou App — um segredo
com `contents: write`); a opção "Allow GitHub Actions to create PRs" vem
desligada; e hoje a cobertura é zero. Recomendação: `atualizar_bussula.py
--dry-run` local primeiro; ligar o cron quando ≥ 1 indicador tiver série, e
considerar abrir **issue** com o diff em vez de PR.

**Testes** (`tests/unit/test_bussula.py` já existe com 16; crescer para):
schema (v2 completo, YAML atual, campo desconhecido rejeitado); progresso
nos dois sentidos, com e sem base, ultrapassado, degenerado; tendência
(sobe/desce por direção, tolerância, um ponto → declarada); defasagem,
vencido e a matriz de confiança com `hoje` fixo; carga (ausente avisa,
cache por mtime, inválido → 500); os quatro testes de caminho (layout
`/app`, layout do repo, `COPY data/ /data/` no Dockerfile, mount no
compose); validador com YAML bom, o arquivo real, e um caso por regra;
`--verificar-fontes` com `httpx.MockTransport`. Integração:
`tests/integration/test_api_bussula.py` (lista, detalhe case-insensitive,
histórico, 404, `meta` ausente e não `null`) e `/bussula` na lista de
rotas sem autenticação em `tests/contract/test_api_schema.py`.

**Ordem de implementação**, um PR pequeno por passo, cada um com o que
prova que funcionou:

1. `schemas/bussula.py` com funções puras → testes de schema/progresso/
   tendência/confiança verdes; nenhum router muda.
2. Router com cache, aviso, `exclude_none`, aquecimento → `curl /bussula |
   jq keys` antes e depois: mesmas chaves antigas, só entram novas.
3. PR de dados: `marcos.yml` v2 (direção, natureza, cadência, histórico
   com o ponto atual, dataset onde houver, `base` para FER) → o teste do
   arquivo real passa.
4. `validar_bussula.py` offline + testes → `✓` e exit 0; quebrar à mão →
   `✗` e exit 1.
5. Job de CI, Makefile, `step0` → o check aparece no PR e fica vermelho
   com YAML quebrado.
6. `/historico`; frontend lê `progresso_pct`, `confianca`, `vencido`.
7. `--verificar-fontes` → as URLs respondem; resultado anotado no PR.
8. `atualizar_bussula.py --dry-run` → imprime "nenhum indicador com série"
   hoje, e é essa a saída esperada.

Nada disso adiciona segredo, banco, Celery ou endpoint autenticado.

## 4. Expansão: candidatos a indicador

Doze candidatos levantados pelo analista, com fonte canônica, cadência e
viabilidade (**fácil** = API ou CSV aberto sem chave; **médio** = PDF/xlsx
estável ou cálculo com duas fontes; **difícil** = sem dataset público ou
definição controlada pelo governo). Valores já medidos nesta investigação
estão marcados.

| # | Código | O que mede | Fonte canônica | Cadência | Direção | Meta oficial | Viab. |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ZIL-SEM-01 | cobertura das importações de semicondutores (SH 8541+8542) por exportações, em valor — **~1,0% em 2025** (imp. US$ 7,5 bi, exp. US$ 0,08 bi) | Comex Stat, `POST /general` por `heading` | mensal, API | maior | nenhuma numérica; NIB Missão 4 lista semicondutores | fácil |
| 2 | ZIL-DIG-01 | % de empresas industriais digitalmente transformadas (≥ 3 de: nuvem, ERP/CRM, big data, robôs, IoT, IA); base 18,9% em 2023 | Cetic.br TIC Empresas via MDIC | anual | maior | **sim**: NIB Missão 4 — 25% em 2026, 50% em 2033 ([Res. CNDI/MDIC 6/2024](https://www.in.gov.br/web/dou/-/resolucao-cndi/mdic-n-6-de-10-de-setembro-de-2024-584578019)) | médio |
| 3 | ZIL-DIG-02 | fibra óptica como % dos acessos de banda larga fixa | Anatel dados abertos ([painéis](https://informacoes.anatel.gov.br/paineis/acessos)) | mensal, CSV | maior | nenhuma nacional | fácil/médio |
| 4 | ZIL-DEF-01 | % de domínio de tecnologias críticas de defesa (base 42,7%, 39 projetos) | Ministério da Defesa, declarado | anual | maior | **sim**: NIB Missão 6 — 55% em 2026, 75% em 2033 | difícil: autoavaliação do governo; declarar viés |
| 5 | ZIL-DEF-02 | despesa "Defesa Nacional" em % do PIB (~1,1%) | Tesouro/SIAFI + IBGE; cruzar com [SIPRI](https://www.sipri.org/databases/milex) | anual | contextual | nenhuma na END | médio |
| 6 | ZIL-AGR-01 | crescimento do PIB-renda da agroindústria + insumos | [Cepea/CNA](https://www.cepea.org.br/br/pib-do-agronegocio-brasileiro.aspx), xlsx | trimestral | maior | **sim**: NIB Missão 1 — até 3% a.a. 2024–26, até 6% a.a. 2027–33 ([Res. 8/2024](https://www.in.gov.br/web/dou/-/resolucao-cndi/mdic-n-8-de-2-de-dezembro-de-2024-602580273)) | médio (academia + associação) |
| 7 | ZIL-COM-01 | participação da indústria de transformação no PIB — **12,11% (2024), 11,77% (2025)** | [IBGE SIDRA t. 1846](https://apisidra.ibge.gov.br/values/t/1846/n1/all/v/585/p/last%204/c11255/90693,90707) | trimestral, API | maior | nenhuma na NIB | fácil |
| 8 | ZIL-COM-02 | % de manufaturados nas exportações (ISIC seção C / fator agregado) | Comex Stat | mensal, API | maior | nenhuma | fácil/médio |
| 9 | ZIL-FER-02 | dependência externa **por nutriente**: ureia (3102.10.10), KCl (3104.20.90), fosfatados (3103/3105) | Comex Stat (importação) + ANDA (produção) | mensal/anual | menor | PNF: 85 → 50 em 2050; 35% de produção nacional em 2030 | médio/difícil (ANDA fechada) |
| 10 | ZIL-MIN-02 | razão processado/bruto para lítio e terras raras (2836.91 × 2530.90; 2846 × 2530.90) | Comex Stat + ANM | mensal | maior | PNM 2050 agregado: transformação mineral de 51,5% para 65% do PIB do setor | médio (NCMs a validar) |
| 11 | ZIL-ENE-02 | dependência externa de diesel (importação ÷ vendas; ~20–23%) | [ANP dados estatísticos](https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-estatisticos), CSV | mensal | menor | nenhuma | fácil/médio |
| 12 | ZIL-EDU-02 | taxa de inovação da indústria (PINTEC Semestral; 70,5% em 2021 → 64,4% em 2024, "em fase de teste") | IBGE | anual | maior | nenhuma | médio |

Referência oficial das metas da Nova Indústria Brasil: [Relatório NIB
2023–2024, Tabela 1](https://www.gov.br/mdic/pt-br/composicao/se/cndi/relatorios-nib/arquivos/relatorio-nib-2023-2024.pdf).
Outras metas da NIB que podem virar indicador: Missão 2 — 50% (2026) e 70%
(2033) das necessidades de saúde produzidas no país; Missão 3 — veículos
eletrificados com baterias nacionais 3% (2026) e 33% (2033); Missão 5 —
biocombustíveis e elétricos no transporte +27% (2026) e +50% (2033).

**Critérios de seleção** (recomendação, para entrar na metodologia):

1. Fonte primária que **mede** o fenômeno (IBGE, EPE, ANM, MDIC, ANEEL,
   ANP); associação setorial só declarada e cruzada com fonte estatal.
2. Definição escrita no YAML: numerador, denominador, unidade, códigos
   NCM/SH, ano civil ou safra. Sem isso o número não é auditável.
3. Dataset com URL estável e, de preferência, API ou CSV; registrar data da
   consulta e o script que reproduz o valor.
4. Série ≥ 5 anos com metodologia constante; revisões com vintage.
5. Meta só com documento oficial que traga número e prazo; citar o ato e
   distinguir meta normativa de aspiracional. Sem documento, `editorial`,
   dito na página.
6. Direção explícita (maior, menor, contextual) e indicador com espaço para
   variar — descartar saturados (nióbio em 99%).
7. Relevância para soberania industrial: dependência externa, agregação de
   valor, domínio tecnológico, concentração de fornecedores — não só
   "produção".
8. Pelo menos um indicador por eixo independente de autoavaliação do
   Executivo; quando inevitável (DEF-01), declarar o viés.

## 5. Apresentação

Fonte: relatório do especialista de UI/UX e visualização, que leu o kit,
o design system ZIL Interface e a página no dev server (desktop e 375px).

### 5.1 A pergunta que o cartão tem de responder

"De onde vem, é confiável, quanto falta." Até `058f45d` o cartão respondia
só "qual é o número". A anatomia abaixo responde as três, na ordem de
leitura:

```
┌─────────────────────────────────────────────────────────┐
│ ● Fertilizantes                      [▼ 2 pp · 12 meses] │ A  categoria + delta CALCULADO
│ Dependência de importação de fertilizantes               │ B  nome
│ 87%                                                      │ C  número (36px celular / 44px desktop), vírgula pt-BR
│ do consumo nacional suprido por importação               │    unidade longa
│ ╭ sparkline, ≥ 3 pontos, sem eixo, ponto final = atual ╮ │ D  histórico
│ Quanto menor, melhor                                     │ E  medidor base → meta, direção em palavras
│ base 2019 ▏━━━━━━━━━━━━━━━●━━━━━━━━━━━━━▕ meta 60 · 2030 │    marca da base, marcador atual, tique da meta
│ Faltam 27 pp · prazo em 2030                             │    a distância sempre em frase, nunca só na barra
│ Meta: Plano X (Decreto Y) ↗  | ou: Meta provisória       │ F  origem da meta
│ Associação setorial · ANDA · Anuário 2024 ↗              │ G  natureza + nome + link ao DATASET (home no detalhe)
│ dado de 12/2024 · defasagem 10 meses      [Não validado] │ H  data, defasagem, UM selo de estado
│ ▸ Sobre este número                                      │ I  <details>: método, meta, validação, tabela do histórico
└─────────────────────────────────────────────────────────┘
```

Regras por elemento:

- **A — delta** só quando calculado de ≥ 2 leituras datadas, com valor,
  unidade e janela ("▼ 2 pp · 12 meses"). Tom `alinhado`/`contra` segue a
  soberania, não o sinal. Tendência declarada à mão nunca vira pílula
  colorida: ou vira texto neutro ("tendência estimada pelos editores") ou
  some. Sem histórico, o slot fica vazio — nunca "Estável".
- **E — medidor de meta** é componente novo (`MedidorMeta`), não o `Medidor`
  do score (escala −10/+10). Preenchimento = `(base − atual) / (base −
  meta)` na direção certa, travado em 0–100 com o excedente dito em texto.
  Sem base: só dois tiques e a frase "Faltam N pp". Primeira linha sempre
  diz a direção.
- **G — fonte** mostra a natureza em texto antes do nome ("Autarquia
  federal", "Associação setorial", "Fonte secundária (IPEA)") e o link vai ao
  dataset; a home do órgão fica no `<details>`.
- **I — detalhe** em `<details>` nativo (UI-012) com definição exata
  (capacidade × geração), método, quem definiu a meta, validação (quem,
  quando), tabela do histórico (alternativa acessível do sparkline), código.

Campos que o cartão exige do dado: `direcao`, `base {valor, data}`, `meta
{valor, prazo, origem {documento, url}}`, `fonte {nome, natureza,
url_dataset, url_home, periodicidade}`, `serie [{data, valor, url}]`,
`validacao {estado, por, em}`, `ultima_verificacao`. Sem `direcao` e
`base`, o medidor não é desenhado. Isso converge com o schema v2 (§3).

### 5.2 Confiança como linguagem visual

Cor semântica responde uma pergunta só por cor:

| Cor | Pergunta | Onde |
| --- | --- | --- |
| verde / vermelho (`alinhado`/`contra`) | o Brasil está indo na direção certa? | só no delta (A) |
| amarelo (`neutro`) | dá para confiar neste número agora? | só no selo de estado (H) |
| cinza (`padrao`) | informação sem alarme | "Em formação", "Fonte secundária" |

**Dois sinais por cartão, no máximo**: A e H. Se mais de um estado se
aplica, mostra-se o pior — fonte fora do ar > dado vencido > não validado >
fonte secundária > em formação — e os demais vão para `title` e detalhe.
"Meta provisória" é texto da linha F, não selo. "Revisado" também não é
selo: validação boa é a ausência do aviso mais a frase no detalhe. Assim o
amarelo significa algo quando aparece.

### 5.3 Estados, com o texto

| Estado | Texto | Comportamento |
| --- | --- | --- |
| Sem meta | "Sem meta definida. Nenhum documento oficial fixa um alvo; a Bússola acompanha só a evolução." | sem medidor; sparkline e delta ficam |
| Meta ultrapassada | "Meta de 90% alcançada em 12/2024, seis anos antes do prazo. Agora 3 pp além. Próximo passo: nova meta por PR." | 100%, excedente só em texto |
| Prazo vencido | "Prazo venceu em 2025 com 87%; a meta era 60%. Aguarda nova meta ou arquivamento." | sem vermelho (não é tendência) |
| Sem histórico | "Primeira leitura: 12/2024. A tendência aparece a partir de 3 leituras." | sem sparkline, sem delta |
| Dado vencido | selo "Dado de 12/2023" · title: "A fonte publica anualmente e a edição de 2024 ainda não entrou." | vencido = mais velho que 1,5× a periodicidade |
| Fonte fora do ar | selo "Fonte fora do ar" · title com a data da última verificação | link fica; URL em texto no detalhe |
| Não validado | selo "Não validado" · title: "Publicado por um maintainer; aguarda revisão por PR." | o padrão dos 4 hoje |
| Em formação | selo cinza; número vira "—"; "Sem número publicado. Definição e fonte em discussão." | cartão compacto, sem medidor |

### 5.4 Página

1. Cabeçalho; **resumo em uma linha** logo abaixo ("4 indicadores · 0
   validados · 0 com meta documentada · dado mais recente 12/2024 ·
   verificado em dd/mm/aaaa") — já implementado em `058f45d` dentro do
   `Aviso`.
2. `Aviso neutro` "em formação" só enquanto `validados === 0` ou `n < 8`;
   some sozinho quando deixar de ser verdade.
3. `Chips` de categoria com contagem, só categorias com indicador; as
   vazias vão para um `Vazio` no fim: "5 pautas ainda sem indicador".
4. Grade por categoria, não por confiança: a confiança mora no cartão;
   ordenar por ela puniria o indicador honesto e esconderia que o problema
   é geral.
5. **Linha do tempo por governo** (PRD F4) só quando houver ≥ 2 leituras
   datadas por mandato em ≥ 2 mandatos; antes disso, o texto "Histórico
   insuficiente para comparar períodos (N leituras)". Exige
   `data/bussula/mandatos.yml` (`inicio`, `fim`, `rotulo`) versionado.
6. `Painel` de fecho: "Como os marcos são escolhidos" → metodologia;
   "Propor indicador" → template de issue.

**Regra apartidária para rotular governos.** Rótulo é o intervalo de datas
primeiro ("2019–2022"), nome como no ato de posse depois, sem partido,
sigla, adjetivo ou numeral informal ("Lula III" não). Mesma cor de faixa
para todos, alternada só para separar. Legenda fixa: "As faixas indicam o
período em que o dado foi medido. Indicadores estruturais têm defasagem de
anos; a faixa não atribui mérito ou culpa." Leitura anual de 12/AAAA
pertence ao mandato que terminava naquele ano. O campo `governo_referencia`
digitado à mão sai do cartão: é derivável da data + `mandatos.yml` e é
fonte de erro e de leitura partidária.

### 5.5 Mobile e acessibilidade

- 375px: uma coluna, `Card compacto`, número 36px, pílula do delta
  `shrink-0` ou descendo para baixo do nome, nunca truncada; medidor fica
  (é a resposta principal), valor atual sai do marcador e vai para a frase;
  tudo o que é detalhe em `<details>`; `Chips` com rolagem.
- Medidor com `role="meter"` (ou `progressbar` com o mesmo
  `aria-valuetext`): "87% do consumo importado. Meta 60% até 2030; base 85%
  em 2019. Faltam 27 pontos percentuais. Quanto menor, melhor." — a frase
  importa mais que o percentual nu.
- Sparkline `role="img"` com `aria-label` descritivo e a tabela do histórico
  no detalhe como alternativa real.
- Contraste medido a partir dos hex de `globals.css`: pílulas semânticas
  passam AA nos dois temas (≥ 5,2:1 em 13px); o trilho do medidor
  (`superficie-3` sobre `superficie-1`, 1,3:1) não serve de pista — por isso
  a meta tem tique em `texto` e números nas pontas. Cores `brasil-*` no tema
  claro caem a 1,9–3,8:1: só ponto de categoria, nunca traço de gráfico ou
  texto. Sparkline em `texto-2`.

### 5.6 O que a UI não deve fazer

Barra cheia sem meta ou por `valor/meta > 1` na direção errada; "145% da
meta"; tendência ou seta sem histórico; link para a home do órgão onde a
pessoa espera o dado; data crua ou `1.2` com ponto; selo verde de
"Validado"; mais de um selo de estado; vermelho para problema de dado; cor
por governo ou nome de partido em faixa; sparkline com cor de categoria,
eixo ou suavização entre 2 pontos; contador em todos os cartões (limite: 4
por tela); pílula que trunca; contagem no resumo que a página não sustenta.

### 5.7 O que falta no kit para isso

`Delta` (pílula de 24px com seta, valor e janela), `Sparkline` (40px, sem
eixo, com `.zil-desenha` já existente no CSS) e `MedidorMeta` (base, atual,
meta, direção). `Contador`, `Selo`, `Card`, `Chips`, `LinhaDoTempo` e
`Revelar` já servem.

## 6. Plano por fases

Cada fase tem critérios de aceite que se verificam sem julgamento.

### F0 — Honestidade (feito, `058f45d`, PR #45)

A página diz o que o dado sabe e o que não sabe. Aceite: barra só com
direção e caminho calculável; meta sem origem marcada como provisória;
natureza da fonte e data do dado visíveis; "Não validado" em cada cartão;
aviso do topo gerado do dado. **Verificado.**

### F1 — Proveniência (próximo PR de dados + um de código)

Dados, em `data/bussula/`:
- `marcos.yml` v2 (§3.1): definição operacional com fórmula, direção,
  base e ano-base, `natureza_fonte` e `vies_declarado` onde couber,
  `cadencia`, `defasagem_meses`, `fonte_dataset` para os quatro, `quebras`.
- Metas corrigidas ou declaradas: FER → PNF 85 → 50 em 2050 (`oficial`,
  com o slide do MAPA como documento até sair resolução do CONFERT) **ou**
  `editorial` com justificativa; EDU → prazo 2034, origem ENCTI 2024–2034;
  ENE → sem meta oficial: `editorial` declarado ou meta nula; MIN → ver F2.
- Valores atualizados e com dataset: FER 86,8% (2025, ANDA 2026); ENE
  escolher um conceito (recomendado: geração, BEN) e usar 86,8% (2025);
  EDU 1,19% (2023); MIN 98,6% em valor (2025, Comex Stat) ou aposentar.
- `historico/<codigo>.csv` com as séries já levantadas (FER 2019–2025,
  MIN 2019–2025, ENE 2019–2025, EDU 2015–2023), uma linha por observação,
  com `fonte_url` da época e `vintage`.
- `governo_referencia` removido; `mandatos.yml` criado.

Código:
- `MarcoYAML` v2 e `Indicador` com `tendencia_calculada`, `tendencia_origem`,
  `defasagem_meses`, `vencido`, `confianca`; progresso com base.
- `scripts/validar_bussula.py` offline; job `validate-data` na CI; `step0`
  no `sync_pipeline.py`; `GET /bussula/{codigo}/historico`.
- Página: `Delta` (só calculado), `Sparkline` (≥ 3 pontos), `MedidorMeta`
  com base e tique da meta, linha de fonte com dataset, `<details>` "Sobre
  este número" com tabela do histórico; `Aviso` que some quando deixa de
  ser verdade.
- Metodologia: seção "Como os marcos são escolhidos e atualizados" com os
  critérios de §4 e o método de tendência de §2.6.

Aceite: `validar_bussula.py` → `✓` e exit 0 no arquivo real; nenhum
indicador publicado com meta sem `origem` ou com `fonte_dataset` nulo;
cada `valor_atual` igual ao último ponto do CSV e reproduzível pela URL do
dataset; `confianca` deixa de ser "baixa" em pelo menos dois indicadores;
nenhuma tendência declarada à mão na página.

### F2 — Pipeline e expansão

- Adaptador `comex_stat` no catálogo (chamada real gravada em teste,
  `habilitada: true`, hosts na allowlist); `ckan_csv` para o SIGA;
  `calculo.py` para razões compostas; `atualizar_bussula.py --dry-run` e
  depois `--pr`.
- Indicadores novos em ordem de viabilidade e relevância: COM-01 (SIDRA,
  fácil, já medido), SEM-01 (Comex Stat, fácil, já medido), FER-02 por
  nutriente, ENE-02 diesel, COM-02 manufaturados, DIG-01 (meta oficial da
  NIB), AGR-01 (meta oficial), MIN-02 em substituição ao MIN-01.
- Linha do tempo por governo (PRD F4), só quando houver ≥ 2 leituras por
  mandato em ≥ 2 mandatos, com a regra apartidária de §5.4.
- `--verificar-fontes` semanal (manual ou cron local); cron de atualização
  por PR só quando ≥ 1 indicador tiver `serie_catalogo` e a maintainer
  quiser a fila.

Aceite: ≥ 8 indicadores publicáveis pela lista de §3.1; ≥ 2 alimentados
por série do catálogo, com valor reproduzido por `--verificar-fontes`
dentro da tolerância; tendência calculada em todos os que têm ≥ 5 pontos;
nenhum "em formação" há mais de dois trimestres sem issue aberta.

### Decisões que são da maintainer, não deste documento

1. **Meta de fertilizantes**: adotar a do PNF (50% em 2050) ou manter uma
   meta editorial do ZIL, dita como tal. A recomendação é a oficial, com
   o marco de 2030 (~65%) como intermediária.
2. **Nióbio**: aposentar MIN-01 (saturado) e substituir por valor agregado
   ou concentração de destino, ou manter como "meta atingida" permanente.
3. **Renováveis**: geração (BEN) ou capacidade (SIGA). Recomendação:
   geração como indicador principal, capacidade como estrutural; sem meta
   oficial, declarar editorial ou deixar sem meta.
4. **Regra de aprovação** para `data/bussula/`: os quatro documentos
   divergem (§1.5). Proposta única: proteção da branch exigindo 1 aprovação
   de quem não abriu o PR, e `validacao: revisado` só por PR de segunda
   pessoa; registrar em GOVERNANCE e alinhar PRD, ROADMAP e CLAUDE.md.
5. **Cron**: issue com diff (sem segredo, sem fila de PR) ou PR automático.

## 7. Lacunas e incertezas

O que nenhuma das investigações confirmou na fonte primária:

- **Texto integral** do PNF 2022–2050 (metas intermediárias), do PNM 2050
  (tabela de metas) e da ENCTI 2024–2034 (redação exata da meta de 2%):
  lidos por apresentações, boletins e notícias. A Portaria MCTI 10.226/2026
  foi confirmada no DOU; o conteúdo, por cópia do IBICT.
- **MCTI**: páginas e PDF de Indicadores CT&I bloqueados por CAPTCHA; o
  1,19% vem do IPEA citando a tabela 2.1.3. O 2024 (~1,23%) é imprensa.
- **ANDA**: sem dataset público; PDFs existem e foram lidos pela sessão
  paralela (séries 2019–2025); o fechamento de 2025 veio do PDF de 04/2026.
  Dependência por nutriente não foi calculada por ninguém.
- **Origem real dos números do YAML** (87, 95, 83, 1,2): as atribuições
  (definição (d) de 2024; ANM; BEN 2019; MCTI 2023) são hipóteses.
- **Comex Stat**: formato exato da requisição foi inferido pelo pacote R
  `comexr` e por chamadas que funcionaram; há limite de taxa (HTTP 429)
  após poucas chamadas; a cadeia de certificados ICP-Brasil às vezes não é
  reconhecida. O adaptador tem de falhar declarando, nunca desligar TLS.
  A lista de NCM para "fertilizantes" (capítulo 31 inclui matérias-primas
  e exclui enxofre e rocha fosfática) é decisão editorial pendente.
- **NCM 2615.90** mistura nióbio, tântalo e vanádio; a parcela "bruta" do
  nióbio é um teto. Óxidos e ligas especiais não são isoláveis.
- **SIGA**: o 84,67% é cálculo próprio sobre o CSV (potência fiscalizada,
  fase Operação, sem geração distribuída); a ANEEL não publica o
  percentual. Série histórica de capacidade antes de 2025 não obtida.
- **PDE 2035 e Plano Clima**: percentuais de imprensa especializada.
- **GitHub Actions**: a memória do projeto diz "bloqueado"; não verificado
  nesta sessão. Se for assim, CI e cron caem para execução local.
- **Contraste e `role="meter"`**: contrastes calculados a partir dos hex,
  não validados em ferramenta externa nem no tema claro ao vivo; suporte
  de leitores de tela a `meter` não testado.
- **Tolerâncias e cadências** (2% para tendência, 1% para reprodução,
  cadência 12 meses) são valores iniciais, a calibrar com as fontes reais.
- O design system não tem README de `Grafico` nem de `Historia`; a
  proposta de gráfico se baseia no CSS do bundle.

Arquivos de apoio das investigações (PDFs, CSV do SIGA, spec da API,
textos extraídos) ficaram fora do repositório, em diretórios temporários
das sessões; as URLs neste documento bastam para refazer qualquer
verificação.

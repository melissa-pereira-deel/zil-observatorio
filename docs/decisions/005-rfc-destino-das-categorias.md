# RFC-005: O destino das categorias ZIL

**Data:** 2026-10-18
**Status:** RFC aberto — sem decisão
**Janela:** ≥ 7 dias de issue pública ([GOVERNANCE.md](../GOVERNANCE.md) § "Mudanças nas categorias ZIL") — conta da **abertura da issue**, não da redação deste documento. Issue aberta em 2026-10-21; fecha em **2026-10-28**
**Abre:** a decisão que o [ADR-004](004-placar-focado.md) registrou como "a **próxima**"

> **Procedência.** A redação deste documento e a medição da seção 4 são de
> Claude (assistente), não de deliberação. A decisão da seção 6 está **vazia** e
> é da maintainer. Este arquivo ocupa o número 005 em `docs/decisions/` porque é
> ali que o rito da `GOVERNANCE.md` manda registrar; quando a decisão for tomada,
> o mesmo arquivo recebe a seção 6 preenchida e passa a `Status: Aceito`.

---

## 1. Contexto

O ADR-004 trocou o índice dos 594 parlamentares por um placar focado em ~10
votações, e deixou um assunto explicitamente em aberto:

> **O destino das 9 categorias ZIL.** Elas fazem sentido como taxonomia de um
> índice; com ~10 votações, nove categorias viram nove baldes quase vazios. Podem
> virar dois ou três eixos, ou serem substituídas por "a pauta desta votação".
>
> Isso é uma decisão de produto que ainda não foi tomada, e alterá-las hoje
> exigiria RFC com quórum inexistente (`docs/GOVERNANCE.md`). Fica registrado como
> a **próxima** decisão, não como parte desta.

O que trouxe o assunto de volta foi concreto. Ao curar a votação `2252295-120`
— PL 2583/2020, Estratégia Nacional de Saúde, aprovada por 352 × 63 e já
transformada em norma jurídica —, a categoria que o classificador atribuiu foi
`ZIL-EDU`, *Capital Humano*. O casamento veio de `pesquisa e desenvolvimento`,
que é keyword forte dessa categoria. O assunto da matéria, no entanto, é o
complexo industrial da saúde: a própria ementa declara o objetivo de "dar
autonomia ao nosso país quanto a produção destes itens".

Nenhuma das 9 categorias cobre isso. E ao investigar se cabia criar categoria
nova, apareceram três coisas que mudam a pergunta.

---

## 2. A correção de enquadramento: são duas chaves, não uma

O ADR-004 descreve um problema de **densidade** — nove compartimentos para ~10
itens. Esse é um problema de **exibição**. Mas a taxonomia governa duas coisas
independentes, e só uma delas é exibição:

| Chave | O que controla | Onde mora |
|---|---|---|
| **Exibição** | quantos baldes o público vê | `apps/web/app/metodologia/page.tsx`, `apps/web/components/CategoryGrid.tsx`, a home (`page.tsx:295`, "9 áreas estratégicas") |
| **Descoberta** | que vocabulário a rede de curadoria cobre | `keywords` e `keywords_fracas` em `data/taxonomia/categorias.yml` |

Colapsar em dois ou três eixos **preservando todas as keywords** resolve a
exibição e deixa a rede idêntica — as duas opções que o ADR-004 registrou mexem
só na primeira chave. Já ampliar a rede exige vocabulário novo, e no formato
atual as keywords moram **dentro** de uma categoria; então ampliar a rede obriga
a criar código novo, ou a enfiar vocabulário num balde que não é dele.

Separar as duas chaves abre uma saída que o ADR-004 não considerou: **poucos
eixos de exibição com a rede ampliada.** É a opção (e) da seção 5.

> **Mas "ampliar a rede" é hipótese, não premissa.** A seção 4 a mediu, e o
> resultado é misto: ampliar para saúde não pescou quase nada, enquanto a
> cegueira em matéria de instrumento fiscal se mostrou real e já presente no
> dado curado. Leia a seção 2 como o enquadramento certo da pergunta, não como
> resposta a ela.

---

## 3. Evidência

### 3.1 A taxonomia é a rede, não o balde

`scripts/candidatas.py:303-305`:

```python
evidencia = classificar_texto_com_evidencia(texto)
if not evidencia:
    continue
```

Votação que não casa nenhuma keyword ZIL **nunca entra na lista de candidatas**.
Não recebe escore, não aparece no ranking de saliência, não chega ao
`dossie.py`. Categoria que falta não produz rótulo errado — produz matéria
invisível à curadoria.

A consequência é direta: a Estratégia Nacional de Saúde entrou na varredura **por
acidente**, por uma keyword de outra categoria. Sem a frase "pesquisa e
desenvolvimento" na ementa, a maior matéria de complexo industrial da saúde do
período não existiria para este projeto.

### 3.2 Os erros de rótulo têm forma comum

Das 11 classificações existentes (as 7 já no repositório e as 4 do placar em
curadoria), duas estão claramente fora da categoria e uma parcialmente:

| Votação | Matéria | Categoria | Problema |
|---|---|---|---|
| `2416804-43` | depreciação acelerada de bens de capital | `ZIL-COM` *Comércio e Tarifas* | não há comércio nenhum na matéria: é instrumento fiscal |
| `2252295-120` | Estratégia Nacional de Saúde | `ZIL-EDU` *Capital Humano* | é complexo industrial da saúde |
| `2382675-97` | diretrizes de política industrial, tecnológica e de comércio exterior | `ZIL-COM` | parcial — o projeto é marco geral, e comércio exterior é uma parte dele |

As três têm a mesma forma: **o assunto é o instrumento ou o marco, não um setor.**
As 9 categorias são sete setoriais (fertilizante, mineral, semicondutor, energia,
digital, defesa, agro) mais duas semi-horizontais (capital humano, comércio e
tarifas). Não existe balde para matéria horizontal de política industrial.

### 3.3 Saúde nunca foi considerada — e a única vez que encostou, foi descartada

Varredura por `saúde`, `farmac`, `medicament`, `hospitalar`, `CEIS`, `vacina`,
`anvisa` em `docs/`, `data/`, `specs/`, `apps/`, `packages/` e `scripts/`: nenhuma
ocorrência no sentido industrial. Os únicos hits de "saúde" tratam da *saúde
operacional da ingestão* (`specs/001-camara-api-ingestao/`).

A única interseção registrada é **negativa**. A keyword `pesquisa` foi rebaixada a
fraca justamente porque capturava saúde — `data/taxonomia/categorias.yml:26`:

```
#   pesquisa       → "pesquisa clínica com seres humanos"
```

Isto é: a única vez que matéria de saúde encostou na taxonomia, foi tratada como
falso positivo a eliminar. Não há decisão prévia a favor nem contra um eixo de
saúde — o assunto nunca foi formulado.

### 3.4 A taxonomia nunca mudou, e o rito nunca foi exercitado

`git log --follow -- data/taxonomia/categorias.yml` devolve **dois** commits em 91:

| Commit | Data | O que fez |
|---|---|---|
| `4c9cad6` | 2026-03-31 | scaffold inicial — as 9 categorias nascem completas, com os mesmos códigos e nomes de hoje |
| `444b173` | 2026-10-17 | introduz `keywords_fracas`; **não altera categoria nenhuma** |

Ou seja: as 9 categorias não foram escolhidas contra evidência — vieram prontas
no primeiro commit do repositório, junto com o manifesto. E **nenhum RFC de
taxonomia jamais aconteceu**: o rito da `GOVERNANCE.md` é teórico, não testado.
Este é o primeiro.

O precedente que existe é de outra natureza: mexer em *keywords* de categoria
existente é decisão operacional (`docs/PRD.md:388` — PR + 1 aprovação), e foi
assim que o `444b173` entrou. Mexer em *categorias* cai no caminho de RFC, que
é este documento.

### 3.5 Onde os falsos positivos se concentram

A mensagem do `444b173` registra a distribuição medida antes do conserto, em
varredura real de 2024 a 2026:

```
ZIL-EDU   88     ← técnico, engenharia, pesquisa, bolsa
ZIL-DIG   87     ← LGPD, dados pessoais, plataforma digital
...
ZIL-SEM    5     ← semicondutores, das pautas mais centrais do manifesto
```

Na varredura de 2023-2026 (seção 4.1: 72 candidatas em 1.140 votações com voto
nominal), o padrão persiste depois do conserto — a maioria das candidatas é
marcada como provável falso positivo pela própria ferramenta, e a concentração
continua em `ZIL-EDU` e `ZIL-DIG`.

A leitura relevante para este RFC: **o problema de precisão da taxonomia não é
distribuído — é de duas categorias cujo vocabulário é genérico.** Qualquer
opção que mexa na rede tem de dizer o que faz com essas duas.

---

## 4. Medição

A cultura do projeto é medir: o `444b173` justificou-se com −33% apurado numa
varredura real, não com argumento. Um RFC que só liste opções fica abaixo desse
padrão.

**Harness:** `exp_taxonomia.py` (scratchpad, fora do repositório) separa a coleta
da classificação. A API da Câmara é chamada uma vez por ano e o corpus cru fica
em JSONL; toda medição depois roda offline sobre o mesmo corpus, então a única
diferença entre duas rodadas é a taxonomia. O escore, as flags e a regra de
casamento fraco vêm por import de `scripts/candidatas.py` e
`apps/workers/classifiers` — nada é reimplementado.

**Validação do harness antes de qualquer número:** rodando com a taxonomia do
repositório inalterada, ele tem de reproduzir as varreduras já guardadas. Se não
reproduzir, o harness está errado e todo número que produzir depois também está.

### 4.1 Corpus e portão

| | |
|---|---|
| Varredura | 2023-2026, **42.066 votações** listadas na API da Câmara |
| Com voto nominal | **1.140** (2,7%) — as únicas que podem alimentar o Score ZIL |
| Candidatas sob a taxonomia atual | **72** (20 em 2023, 28 em 2024, 12 em 2025, 12 em 2026) |
| Portão | o harness reproduz as quatro varreduras guardadas com **IDs e escores idênticos**, em ordem (`diff` vazio) |
| Regressão | as **9** afirmações de "não classifica" seguem vazias nas três configurações: taxonomia atual, +`ZIL-SAU`, +`ZIL-INS` |

O portão já pagou por si. A primeira versão da checagem de regressão usava
`classificar_texto_com_evidencia` (casamento cru) onde a suíte afirma sobre
`classificar_texto` (que aplica a regra de keyword forte), e por isso acusou 6
regressões inexistentes na taxonomia **inalterada**. Erro do medidor, não do
medido — e é exatamente o que um portão existe para pegar.

### 4.2 Vocabulário de saúde: 2 candidatas novas em 4 anos, e a ferramenta ordenou errado

| Ano | Candidatas | Novas | Por keyword forte |
|---|---|---|---|
| 2023 | 20 → 20 | 0 | 0 |
| 2024 | 28 → 28 | 0 | 0 |
| 2025 | 12 → 12 | 0 | 0 |
| 2026 | 12 → 14 | **2** | 1 |

O zero de 2023-2025 é real, não artefato: em 306 votações nominais de 2023,
`medicamento` aparece 0 vezes, `insumo` 0, `Fiocruz` 0. As quatro matérias que
mencionam saúde são de **serviço** — Mais Médicos, violência contra a mulher,
campanha de vacinação, SUS/fibromialgia — e o vocabulário acertou em não casar
nenhuma.

As duas de 2026 invertem o sinal da ferramenta:

| Votação | O que a ferramenta disse | O que a matéria é |
|---|---|---|
| `2572994-8` PL 2158/2023 | ✓ keyword **forte**, escore 9,2 | **Falso positivo.** O assunto é *venda de medicamentos em farmácia dentro de supermercado*. Casou `insumos farmacêuticos` e `medicamentos` **dentro do título citado** da Lei 5.991/1973 |
| `2601223-8` PL 68/2026 | ⚠ "só casou por palavra comum — provável falso positivo" | **Provavelmente a genuína.** Declara de interesse público os medicamentos Mounjaro e Zepbound *para fins do art. 71 da Lei 9.279/1996* — licenciamento compulsório, o mecanismo que permite produção nacional de medicamento patenteado |

A que a ferramenta promoveu é lixo; a que ela rebaixou é a relevante. Para um
placar focado, essa inversão importa mais que a contagem.

### 4.3 Bug encontrado na regra de precisão existente

O falso positivo acima não é do vocabulário novo — é da regra que deveria
barrá-lo. `apps/workers/classifiers/__init__.py:54`:

```python
_CITACAO_DE_LEI = re.compile(
    r"\(\s*(?:lei|código|codigo|decreto|estatuto|marco)\b[^)]*\)",
    re.IGNORECASE,
)
```

A regra só remove título de lei entre **parênteses**. A ementa do PL 2158/2023
cita assim:

> Altera a Lei nº 5.991, de 17 de dezembro de 1973, que **“dispõe sobre o
> Controle Sanitário do Comércio de Drogas, Medicamentos, Insumos Farmacêuticos
> e Correlatos...”**, para dispor sobre a comercialização de medicamentos em
> farmácia ou drogaria instalada na área de venda de supermercados.

Título entre **aspas**, não entre parênteses — passa inteiro. É a mesma família
do falso positivo que a regra foi criada para parar (o homicídio qualificado que
virava soberania digital por citar a LGPD). **Vale consertar independentemente
desta decisão**, e afeta hoje `ZIL-DIG` e `ZIL-COM`, não só um eixo hipotético
de saúde.

### 4.4 Vocabulário de instrumentos: 4 candidatas novas, zero matérias novas

| Ano | Candidatas | Novas | Por keyword forte |
|---|---|---|---|
| 2023 | 20 → 20 | 0 | 0 |
| 2024 | 28 → 31 | **3** | 3 |
| 2025 | 12 → 13 | 1 | 0 |
| 2026 | 12 → 12 | 0 | 0 |

As três fortes de 2024 são `2416804-54`, `2416804-48` e `2416804-51` — outras
votações **da mesma proposição** que já está no placar (PL 2/2024, depreciação
acelerada), e **todas as três são voto de emenda ou destaque**, logo indecidíveis
pela regra do próprio projeto. A de 2025 (`2557801-10`, FGO para crédito a
pequena empresa) casou só por palavra comum.

Matéria nova descoberta: **zero**.

### 4.5 O achado que vale mais que as contagens: duas das votações curadas são invisíveis à própria rede

Medindo as seis votações curadas contra a taxonomia atual, com a regra forte:

| Votação | Proposição | Rótulo no YAML | A rede enxerga? |
|---|---|---|---|
| `2418020-7` | PL 3149/2020 | `ZIL-ENE` | ✓ `ZIL-ENE` por `biocombustível` |
| `2558692-10` | PL 2780/2024 | `ZIL-MIN` | ✓ `ZIL-MIN` por `minerais críticos` |
| `2252295-120` | PL 2583/2020 | `ZIL-EDU` | ✓ `ZIL-EDU` por `pesquisa e desenvolvimento` |
| `2382675-97` | PL 4133/2023 | `ZIL-COM` | ✓ `ZIL-COM` por `comércio exterior` |
| `2416804-43` | PL 2/2024 | `ZIL-COM` | **✗ INVISÍVEL** |
| `2454704-53` | PL 1847/2024 | `ZIL-SEM` | **✗ INVISÍVEL** |

Duas das seis estão no repositório **sem que a ferramenta de descoberta pudesse
tê-las encontrado**. Existem ali porque alguém atribuiu `categoria_principal` à
mão. As duas são matéria de instrumento fiscal — a mesma forma dos erros de
rótulo da seção 3.2.

E as duas têm causas **diferentes**, o que é o ponto:

- **`2416804-43`** (depreciação acelerada) fica visível com o vocabulário de
  instrumentos: `classificar_texto` passa a devolver `ZIL-INS`. É uma lacuna de
  vocabulário, e tem conserto.
- **`2454704-53`** (desoneração da folha do setor de TIC) **continua invisível
  com qualquer um dos dois vocabulários** — e vai continuar com qualquer
  taxonomia de keyword, porque a ementa **não nomeia o próprio assunto**. Ela é,
  na íntegra, uma lista de leis alteradas e revogadas em torno de "contribuição
  substitutiva" e "Cofins-Importação". As palavras `desoneração`, `tecnologia`,
  `software`, `TIC` e `semicondutor` não aparecem nenhuma vez.

Ou seja: **existe uma classe de matéria que descoberta por keyword não alcança,
e o projeto já tem uma no conjunto curado.** Nenhuma das cinco opções da seção 5
resolve isso; é limite do método, não da taxonomia.

> Nota de qualidade de dado, fora do escopo desta decisão: a justificativa de
> `2454704-53` em `data/direcoes/2024.yml` descreve o projeto como desoneração
> de "TI, software, hardware e semicondutores". Nada disso está na ementa. É
> coerente com o aviso no cabeçalho do próprio arquivo — as 7 entradas são
> `nao-validado` e o método de cada uma não é reconstituível —, mas vale
> registrar que o rótulo `ZIL-SEM` dessa entrada veio de fora da fonte.

### 4.6 Síntese da medição

1. **A hipótese que motivou este RFC não se confirmou.** Um eixo de saúde não
   amplia a rede de forma mensurável: 2 candidatas em 4 anos, e a ordenação
   invertida. O argumento que resta a favor dele é fidelidade de rótulo.
2. **A lacuna de instrumentos é real e está provada pelo dado existente** — não
   pela contagem de candidatas novas, que é zero, mas pelas duas votações
   curadas invisíveis à própria ferramenta.
3. **O problema mais barato de consertar não é a taxonomia: é a regra de
   citação de lei**, que deixa passar título entre aspas e já polui categorias
   em produção.
4. **Há um limite que nenhuma taxonomia vence:** ementa que não nomeia o próprio
   assunto (`2454704-53`) é inalcançável por keyword, e o projeto já tem uma
   dessas curada.

Nenhum desses quatro pontos era conhecido quando a pergunta foi feita. Três
deles apontam para fora da decisão de taxonomia.

### O que NÃO foi medido, e por quê

O efeito **sobre as proposições do banco** não foi medido, e não é por falta de
vontade: a issue **#27** registra que a indexação que a própria Câmara atribui
participa da classificação e **não é persistida**. Reclassificar a partir do
banco dá resultado diferente do caminho de descoberta, e não há como saber se a
diferença veio da regra ou do texto que sumiu.

Isso não é hipotético. A #27 registra que o primeiro sintoma dessa lacuna foi
**uma medição errada sobre o próprio corpus** — "76% perdem a classificação",
quando o efeito real era −33%. Produzir aqui um número do lado do banco seria
repetir o mesmo erro com a mesma ferramenta.

Portanto: **o lado das votações está medido; o lado das proposições está
bloqueado pela #27**, e a opção escolhida tem de dizer se depende dele.

---

## 5. Opções

Cada uma com o custo apurado e, mais importante, com o que ela **não** resolve.

### (a) Manter as 9 como estão

- **Custo:** zero.
- **Não resolve:** nada. Os nove baldes quase vazios continuam, as duas
  classificações mal rotuladas continuam, e saúde continua fora da rede.
- **A favor:** é a única opção que não gasta a janela de 7 dias nem exige
  backfill. Se o placar é o foco e a taxonomia é acessória, esperar é defensável.

### (b) Colapsar em dois ou três eixos, keywords preservadas

A primeira opção do ADR-004. Por exemplo: *Recursos e Energia* / *Indústria e
Tecnologia* / *Estado e Comércio*, com todas as keywords atuais redistribuídas.

- **Custo:** as 5 listas escritas à mão, mais `SEARCH_GROUPS` em
  `scripts/discover_proposicoes.py:43-79`, mais `categoria_principal` nas 7
  entradas de `data/direcoes/`, mais backfill (que não existe — ver seção 6).
- **Resolve:** a exibição, que é o problema que o ADR-004 nomeou.
- **Não resolve:** a rede. Saúde continua invisível. E perde-se resolução de
  rótulo: *Indústria e Tecnologia* não distingue semicondutor de agroindústria.

### (c) Dissolver em "a pauta desta votação"

A segunda opção do ADR-004: sem taxonomia fixa; cada votação do placar carrega
uma descrição própria do que está em jogo.

- **Custo:** o maior em código — tira a categoria de `models`, dos routers de
  filtro, da Bússola (`data/bussula/marcos.yml` indexa por categoria) e de 5
  telas. E exige decidir o que acontece com `/bussula`, que é organizada por
  categoria.
- **Resolve:** a exibição, de forma radical e honesta para um placar de ~10.
- **Não resolve:** a rede — e aqui o problema é pior. **Sem taxonomia não há
  `classificar_texto_com_evidencia`, e sem ele `candidatas.py` não tem como
  ranquear nada.** A descoberta passaria a ser manual. É a opção que mais
  simplifica o produto e mais encarece a curadoria.

### (d) Décima categoria setorial: `ZIL-SAU`, Complexo Industrial da Saúde

- **Custo:** as 5 listas + `SEARCH_GROUPS` + prosa pública na `/metodologia`
  (descrição e exemplo) + backfill. Sem migration, sem mudança de tipo, sem
  teste a reescrever (nenhum teste assina o número 9).
- **Resolve:** dá casa à `2252295-120`, que hoje está em *Capital Humano*.
- **Não resolve:** a exibição — **piora**, de nove baldes quase vazios para dez.
  E não resolve o `2416804-43`, que continua em *Comércio e Tarifas*.
- **A medição não sustenta a promessa de rede** (seção 4.2): em 4 anos e 1.140
  votações nominais, o vocabulário de saúde traz **2 candidatas**, ambas em 2026
  — e a que ele promove é falso positivo, enquanto a provavelmente genuína ele
  rebaixa. O argumento a favor de (d) é de **fidelidade de rótulo**, não de
  descoberta. Dito sem rodeio: a hipótese que motivou este RFC foi medida e
  não se confirmou.
- **Risco:** keyword genérica contamina as outras categorias. As 9 afirmações da
  suíte seguiram vazias com este vocabulário, mas o risco tem endereço — o
  assert de `pesquisa clínica com seres humanos` existe porque esse exato texto
  já poluiu `ZIL-EDU`.

### (e) Poucos eixos de exibição **com** a rede ampliada

A saída que a separação das duas chaves abre: 2-3 eixos no que o público vê, e
por baixo um vocabulário mais largo — incluindo saúde e, se a medição sustentar,
instrumentos. Exibição e descoberta deixam de ser a mesma lista.

- **Custo:** o de (b) mais o de (d), mais um refactor pequeno mas real: hoje
  keywords moram dentro da categoria de exibição, e esta opção exige separar
  as duas coisas no YAML — um nível a mais, com os cinco mapas da aplicação
  derivando do eixo e o classificador lendo do vocabulário.
- **Resolve:** as duas chaves.
- **Não resolve:** a dependência de backfill, que é comum a (b), (c), (d) e (e).
- **Risco:** é a opção com mais código novo, e código novo em cima de uma
  taxonomia cujo destino de produto ainda está sendo decidido.

### (f) Consertar a precisão e a cegueira medida, sem decidir a exibição agora

Esta opção não existia quando a seção 5 foi escrita — **a medição a produziu**.
Nada de categoria nova para exibição; só os dois consertos que os números
apontam, deixando a pergunta dos eixos para quando o placar estiver publicado e
houver uso real para observar:

1. **A regra de citação de lei passa a cobrir título entre aspas** (seção 4.3).
   É bug de precisão na regra existente, afeta `ZIL-DIG` e `ZIL-COM` hoje, e não
   depende de nenhuma decisão de taxonomia.
2. **O vocabulário de instrumentos entra onde resolve cegueira comprovada**
   (seção 4.5): com ele, `2416804-43` deixa de ser invisível à própria
   ferramenta de descoberta. Se entra como categoria `ZIL-INS` ou como keywords
   acrescentadas a `ZIL-COM` é detalhe de forma — e é justamente o que a decisão
   da seção 8 precisa dizer.

- **Custo:** o menor de todas as opções que mexem em algo. O conserto da regex é
  local e tem teste óbvio a escrever; o vocabulário de instrumentos é uma entrada
  de YAML mais o fallback do classificador.
- **Resolve:** a precisão (medida) e uma das duas cegueiras (medida).
- **Não resolve:** a exibição — os nove baldes quase vazios continuam, e é o
  problema que o ADR-004 de fato nomeou. Também não resolve a `2252295-120`, que
  segue rotulada *Capital Humano*.
- **A favor:** é a única opção cujo benefício está medido em vez de argumentado,
  e a única que não gasta decisão de produto antes de haver produto no ar.

---

## 6. Dependências técnicas — valem para (b), (c), (d) e (e)

| Dependência | Estado |
|---|---|
| **Script de reclassificação** | **Não existe.** `scripts/discover_proposicoes.py:157` só preenche classificação vazia (`if not existing.categorias_zil`), então proposição já classificada nunca é reavaliada. Sem backfill, qualquer taxonomia nova nasce cobrindo só o que entrar depois dela. |
| **Issue #27** | Aberta. Bloqueia medir o efeito no banco (seção 4). A própria issue propõe a saída certa: *persistir a evidência, não só a entrada* — "sobrevive a mudanças futuras na taxonomia, que a entrada crua não faz". Qualquer opção que mexa na rede fica mais segura depois dela. |
| **Cinco listas escritas à mão** | `data/taxonomia/categorias.yml`; o fallback embutido em `apps/workers/classifiers/__init__.py:32-44`; `apps/web/lib/categorias.ts`; `apps/web/components/CategoryGrid.tsx`; `apps/web/app/bussula/page.tsx`; `apps/web/app/metodologia/page.tsx`. Nenhuma é derivada do YAML. O fallback é o risco silencioso: esquecê-lo faz a categoria **desaparecer sem erro** quando falta o mount `./data:/data:ro` — o bug já documentado em `CLAUDE.md`. |
| **Divergência de nomes já existente** | `ZIL-EDU` é "Educação" em `lib/categorias.ts:8` e "Capital Humano" no YAML e em três outros lugares; `ZIL-AGR` é "Agro" na Bússola e "Agro-Indústria" no resto. A UI-016 pedia consolidar isso e foi feita pela metade. Vale consolidar no mesmo PR da decisão, qualquer que seja. |
| **As afirmações de "isto NÃO classifica"** | `tests/unit/test_classifier.py` guarda, em asserts `== []`, **9 textos** que não devem classificar — e cada um é um falso positivo que o projeto já pagou para descobrir: `pesquisa clínica com seres humanos`, `Tarifa Social de Água e Esgoto`, atletas do Mercosul, a LGPD citada dentro de um projeto de homicídio qualificado, `Técnico Judiciário`, `prazo renovável`. Vocabulário que reacenda qualquer um deles está reintroduzindo bug conhecido. A medição da seção 4 checa os 9 em cada rodada. |
| **Nenhuma validação de categoria** | Não existe enum, `Literal` ou validação Pydantic de código ZIL em todo o backend, e `scripts/validar_direcoes.py` **não** confere `categoria_principal` contra a taxonomia. Código inválido num YAML de direções passa silencioso. Vale corrigir junto. |

---

## 7. Governança — registro de fato, não proposta de norma

Três documentos mandam coisas diferentes para esta mesma mudança:

| Documento | Exigência |
|---|---|
| `docs/GOVERNANCE.md` § "Mudanças nas categorias ZIL" | issue pública ≥ 7 dias + aprovação de **todos os maintainers ativos** + registro em `docs/decisions/` |
| `docs/PRD.md:389` | RFC pública ≥ 7 dias + **3 aprovações** |
| `.specify/memory/constitution.md:167` | lista os 9 códigos e os declara "imutáveis sem RFC", sem dar quórum |

E a lista de passos da `GOVERNANCE.md` **pula o item 3** — vai de 2 para 4.
Defeito de redação que ninguém pegou até agora.

Este RFC **não resolve o conflito**: registra-o, e pede que a decisão da seção 6
diga qual dos três vale. É o mesmo padrão que a GOVERNANCE v1.1 usou ao
registrar não-cumprimento sem alterar a norma.

Duas coisas ditas sem rodeio, porque o contrário seria teatro:

- O repositório é **público** e tem **0 watchers**. A issue cumpre a letra da
  norma e serve como registro datado e auditável — não como escrutínio. Dizer
  que houve revisão pública porque uma issue ficou 7 dias aberta sem leitor
  seria falso.
- A `GOVERNANCE.md` já anota, sobre a cláusula de aprovação, que "com uma
  maintainer, esta cláusula é satisfeita trivialmente e não representa revisão
  alguma". Esta decisão será de uma pessoa, e fica registrada como tal.

---

## 8. Decisão

*Vazia. A janela fecha em 2026-10-28.*

Quando preenchida, esta seção deve dizer:

1. Qual opção da seção 5, e por quê — incluindo a (f), que a medição produziu
2. O que acontece com `ZIL-EDU` e `ZIL-DIG`, cujo vocabulário genérico concentra
   os falsos positivos (seção 3.5)
3. Qual dos três quóruns da seção 7 vale, e qual é a redação correta do passo
   que falta na `GOVERNANCE.md`
4. Se a mudança espera a #27 e o script de backfill, ou se entra antes deles

## 9. Consequência imediata, enquanto a janela está aberta

As 4 entradas do placar focado — `2382675-97`, `2252295-120`, `2558692-10` e
`2418020-7` — **não são escritas em `data/direcoes/`** até esta decisão. O motivo
é não registrar no git uma classificação cuja categoria já se sabe errada. Os
rascunhos de justificativa e o substrato factual de cada uma estão prontos e
aguardam revisão editorial.

Nada mais do produto depende desta decisão: `categoria_principal` não entra na
fórmula do Score ZIL — serve de *hint* para o classificador em
`scripts/sync_votacoes_zil.py`. O ranking segue fora do ar por
`NEXT_PUBLIC_RANKING_PUBLICO`, como o ADR-004 deixou.

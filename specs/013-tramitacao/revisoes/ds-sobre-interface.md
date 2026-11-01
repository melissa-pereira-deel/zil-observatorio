# Revisão de Design System sobre o backlog de interface (spec 013)

**Data:** 2026-10-30 · **Revisor:** Design System
**Objeto:** `specs/013-tramitacao/backlog-interface.md`, tarefas TRM-015, TRM-016, TRM-022 e TRM-040
a TRM-046 (inclui a matriz de §4).
**Critério:** gates S1–S10 de `spec.md` §7.3 (componentização, tokens, estados, responsividade,
a11y, testes, docs) e as APIs do kit em `backlog-design-system.md` (versão da rodada 2, alinhada a
`backlog-dados.md` §1.5/§7). Gravidade, na mesma escala da revisão da UI/UX:
**bloqueia** = não mergear sem a correção (contrato que não compila, estado que não renderiza, dado
errado na tela) · **deve corrigir** = no mesmo PR, salvo justificativa escrita · **sugestão** = a
critério da UI/UX.

O backlog de interface usa o kit como foi especificado: nenhuma cor de alinhamento em fase,
desfecho ou `nao_sabemos` (inclusive o `Aviso` âmbar, que ficou fora); situação oficial fora do
`Selo`; `FaseSelo` sem `href` em cartão-link; `Etapas` compacta com a legenda do kit; `Recolhivel`
no lugar de `<details>` próprio; datas por `dataBR`; um primário por área; esqueletos com a forma do
conteúdo; testes com os helpers de TRM-001. Os achados são, na maior parte, de tipos que não batem
com o contrato final e de textos que o kit mudou nesta rodada a pedido da própria UI/UX.

## O que o kit mudou nesta rodada (afeta o texto da interface)

| Mudança no kit | Origem | O que a interface ajusta |
| --- | --- | --- |
| `FaseSelo.fase` aceita `null` (com desfecho); prop `id` | Arquitetura §7-3; TRM-043 | `faseSeloPropsDe` já prevê; TRM-043 passa `id` |
| `Etapas`: texto visível "Dispensada" (estado continua `pulada`); `atual` → "Desde {quando}" (o kit escreve o prefixo); sem data, "Está aqui"; mais de 7 etapas = vertical; **compacta também é `<ol>` com `aria-current`** e legenda visível `aria-hidden` | UX-DS-11, 12, 30, 31; U10 | matriz E01; critério 10 de TRM-040 passa a valer como está |
| `TodosOsRegistros`: erro padrão `Aviso` **`padrao`** (falha parcial), corpo "Os marcos acima continuam valendo.", ação "Tentar de novo" com `onTentarDeNovo`; reabrir depois de erro chama `onAbrir` de novo; `focarAoTrocar` (padrão true) leva o foco ao primeiro registro na troca de página; data sem hora; `<ol>` nomeada; data em coluna própria a partir de `md` | UX-DS-01, 02, 35; TRM-041 | I14, M02; TRM-041 tira o foco programático da página |
| Adaptadores `marcoDaApi`, `registroDoEvento` (`lib/tramitacao/eventos.ts`) | TRM-041 | TRM-041 usa em vez de mapear à mão |
| `ComoSabemos`: resumo padrão "Leitura do ZIL, conferida na Câmara em {data}"; `dataBR` converte data com hora para `America/Sao_Paulo` | UX-DS-13, 04 | matriz (texto do kit novo) |
| `RitoDiagrama`: modelo de vista com os nomes do contrato (`oQueAcontece`, `quemDecide`, `condicao`, `opcional`; ramo `{ desfecho, rotulo, texto }`); `extra` por etapa; ramos à direita só a partir de **`lg`**; seta do link de contagem `aria-hidden`; legenda no mesmo nível de título; classe X "sem prazo fixo" | Arquitetura §7-6; UX-DS-06–10, 29; matriz E02 | TRM-042/044 (wireframes 1280); TRM-045 pode usar `extra` |
| `TermoGlossario`: `abertoInicial`, `rotuloAcao` (padrão ", o que quer dizer"), `indicador`; nota padrão "Texto do ZIL, não oficial." | UX-DS-16, 17, 18, 32 | G02 deixa de ser "troca" |
| `GlossarioLista`: `nivelTitulo` (`article` + `h{n}`), `dt`/título com `tabIndex={-1}`; `definicaoDoTermo` usa `texto_curto`; texto só com `publicavel && revisao === "aprovado"`; `entradaDaSituacao` | UX-DS-14, 15, 20; TRM-045 | TRM-040, TRM-045 |
| `scroll-padding` global entra com TRM-037 | UX-DS-22 | — |
| TRM-001: `api.responder` aceita função da URL; `api.responderPaginas`; `api.chamadas`; `focoVisivelENaoEncoberto`; projeto `reflow-320` (`@reflow`); trava da catraca de a11y | UX-DS-23–26; TRM-016/041 | TRM-016, 041, 043 não criam `tests/e2e/helpers/lista.ts` |
| Exceção a S9 registrada para `/como-vira-lei` e `/situacoes` (busca no cliente; `page.tsx` servidor) | pedido da UI/UX | — |

## Achados

| ID | Tarefa · seção | Problema | Gravidade | Correção exata proposta |
| --- | --- | --- | --- | --- |
| DS-UI-01 | TRM-040 · Specs técnicas (`OndeEsta`) | `glossario: EntradaGlossario[] \| null`: `EntradaGlossario` é o modelo de vista da `GlossarioLista` (sem `publicavel`, `tipo`, `texto_curto`); `definicaoDoTermo` recebe `GlossarioApi[]`. Do jeito escrito, não compila. | bloqueia | `glossario: GlossarioApi[] \| null` (de `lib/tramitacao/tipos.ts`). Situação: `const d = onde_esta.situacao_glossario ? definicaoDoTermo(glossario, onde_esta.situacao_glossario) : null;` — pela chave que a API manda pronta, nunca casando `termo` com a situação oficial (revisão da Arquitetura, itens 3 e 4; em F0, `proposicao.situacao_glossario`). Explicação da fase/desfecho/apensada: `entradaDaApi(glossario.find(g => g.chave === "fase_" + fase))?.texto` (passa pela defesa de `publicavel`). |
| DS-UI-02 | TRM-040 · Anatomia 9 (`ComoSabemos`) | `saibaMais="/metodologia#tramitacao"` é string; a prop é `{ rotulo, href }`. Não compila. | bloqueia | `saibaMais={{ rotulo: TEXTOS.C01_SAIBA_MAIS /* "Como chegamos a esta fase" */, href: "/metodologia#tramitacao" }}`; renderizar `ComoSabemos` só quando `comoSabemosDaFase(...)` não for `null` (senão `C03`). |
| DS-UI-03 | TRM-040 · Anatomia 5 | "a legenda é `legendaDasEtapas(etapas)`" pode ser lido como renderizar a legenda à parte; a variante `compacta` já a mostra. Duas legendas iguais na tela. | deve corrigir | Escrever: "`<Etapas variante="compacta" etapas={…} />` — o componente já mostra a legenda; a página **não** renderiza `legendaDasEtapas` de novo (a função só serve se a página quiser a frase em outro lugar)". |
| DS-UI-04 | TRM-040 · Anatomia 9 e matriz C02 | "Regras → Ver as regras no GitHub" entra como item extra com link. É uma fonte, e o `ComoSabemos` já tem o lugar e o tratamento de link externo para isso. | sugestão | Acrescentar às `fontes`: `{ rotulo: "Regras do mapa de fases — data/tramitacao/fases.yml", url: REPO_URL + "/blob/main/data/tramitacao/fases.yml" }` (se a API já não mandar); tirar C02 da matriz. |
| DS-UI-05 | TRM-040 · situação oficial | O gatilho do termo é a única pista de que a situação abre uma explicação; no toque não há hover. | sugestão | `<TermoGlossario indicador …>` na situação oficial (o kit acrescenta `Icone info`, fora do nome acessível). |
| DS-UI-06 | TRM-015 + TRM-040 · `dl` "Regime / Quem decide / Relatoria / Órgão" | O mesmo bloco de linhas é escrito em `SituacaoCamara` (015) e de novo em `OndeEsta` (040). S1: padrão em dois lugares vira componente. | deve corrigir | Extrair em TRM-015 `components/tramitacao/LinhasDaSituacao.tsx` (`props: { regime, regimeTexto, apreciacao, apreciacaoTexto, relator, orgao, ultimaMovimentacao }`, sem hooks), usado por `SituacaoCamara` e por `OndeEsta`. |
| DS-UI-07 | TRM-015, 040 · testes de foco | O retângulo do foco contra `nav[aria-label="Atalhos"]` é escrito à mão em cada spec. | sugestão | Usar `focoVisivelENaoEncoberto(page, locator)` (TRM-001), que confere contorno visível e as duas navegações fixas. |
| DS-UI-08 | Todas as páginas · "sem rolagem horizontal" | WCAG 1.4.10 pede reflow a 320 px; os testes param em 375. | deve corrigir | Marcar com `@reflow` o teste `semRolagemHorizontal` de cada `tests/e2e/paginas/*.spec.ts` (roda no projeto `reflow-320` de TRM-001). |
| DS-UI-09 | TRM-016, 041, 043 · testes e2e | `tests/e2e/helpers/lista.ts` (`responderLista`, `responderPaginado`) com um segundo `page.route`. TRM-001 agora cobre paginação na própria API falsa. | deve corrigir | `api.responderPaginas("/proposicoes", ["tramitacao/lista-p1", "tramitacao/lista-p2"], { alem: { status: 200, corpo: [] }, falharNaPagina? })` e `api.responderPaginas("/proposicoes/<id>/tramitacao/eventos", ["tramitacao/eventos-08-p1", "tramitacao/eventos-08-p2"])`; "uma requisição na primeira abertura" com `api.chamadas.filter(c => c.chave.endsWith("/eventos")).length === 1`. Não criar `lista.ts`. |
| DS-UI-10 | TRM-041 · Specs técnicas | Tipos `EventoRead`/`EventosPagina` (nomes Pydantic) e mapeamento à mão com `dataBR(data_hora)`. | deve corrigir | `marcos: MarcoApi[]`, `itens: EventoApi[]` (`tipos.ts`); `marcos.map((m, i) => <Marco key={i} {...marcoDaApi(m, i, marcos.length)} />)` e `itens.map(registroDoEvento)` (`lib/tramitacao/eventos.ts`, TRM-032). |
| DS-UI-11 | TRM-041 · Interações | "o foco vai para o primeiro registro (`tabIndex={-1}` + `focus()`)": a página não alcança os `<li>` do kit. | deve corrigir | Tirar da página; o `TodosOsRegistros` faz isso (`focarAoTrocar`, padrão true). O teste continua: depois de trocar de página, `document.activeElement` é o primeiro registro. |
| DS-UI-12 | TRM-041 · I14 e matriz | I14 diz `Aviso` `contra` e "Tente abrir de novo mais tarde". O kit usa `padrao` (falha parcial — regra da própria interface §0.5-2) e o botão "Tentar de novo"; com `contra`, `expectPaletaNeutra(page, "#o-que-aconteceu")` falharia no estado de erro. | deve corrigir | Matriz I14: tom `padrao`; título "Não conseguimos carregar os registros." · corpo "Os marcos acima continuam valendo." · ação "Tentar de novo" (`onTentarDeNovo` → refaz `obterEventos`). Tirar I14 da lista de `Aviso` `contra` da nota da §4. |
| DS-UI-13 | TRM-041 · wireframe 375 | Marcos passados desenhados como "○" (vazado). No vocabulário do kit, vazado = "ainda não aconteceu"; marco passado é ponto cheio `texto-2`, o atual é cheio com anel. | sugestão | Trocar "○" por "•" nos marcos passados e manter "◉" no atual. |
| DS-UI-14 | TRM-041 · marcos anteriores | O `Recolhivel` "Ver os {n} marcos anteriores" contém uma segunda lista sem nome. | sugestão | `<LinhaDoTempo aria-label="Marcos anteriores">` dentro do recolhível. |
| DS-UI-15 | TRM-042 · Specs técnicas (`CaminhoInteiro`) | `rito: { especie: string; casa_iniciadora: "camara" \| "senado" }` exclui a MPV, cujo rito tem `casa_iniciadora: "congresso"` (`MPV_CN`, backlog-dados §2.5): o caso 15 não acharia o rito. | bloqueia | `rito: RitoRefApi \| null` e escolher por chave: `mapa.especies.flatMap(e => e.ritos).find(r => r.chave === rito.chave)`. |
| DS-UI-16 | TRM-042 · critério 4 e matriz K01/K02 | Critério 4 diz "rito ausente no mapa para espécie do escopo → K01"; a matriz define K01 como "rito com `publicavel: false`" e K02 como "espécie sem rito". O adaptador devolve `publicavel: false` com `etapas: []` e o `RitoDiagrama` não renderiza nada com `etapas` vazia. | deve corrigir | Critério 4: `ritoParaDiagrama(...).publicavel === false` → K01; nenhum rito com a `chave` → K02; `nao_sabemos`/`rito: null` → K03 com o rito da espécie sem estado (se houver). Mesmo ajuste no critério 5 de TRM-044 ("PDL não publicável", não "ausente"). |
| DS-UI-17 | TRM-042 · critério 1 e wireframe | "o Plenário com 'Pulada'"; "descricao"; ramos à direita com `md:`. O kit agora mostra "Dispensada", chama o campo `oQueAcontece` e põe os ramos à direita só a partir de `lg`. | deve corrigir | Critério 1: "o Plenário com o selo 'Dispensada' e a `nota`". Wireframe: "oQueAcontece"; 1280: `lg:grid-cols-[minmax(0,1fr)_minmax(0,20rem)]` (768 com ramos embaixo). |
| DS-UI-18 | TRM-043 · cartão | `aria-describedby` "ganha o id do selo", mas o `FaseSelo` não tinha `id`. | deve corrigir | O kit ganhou `id` no `FaseSelo`; no cartão: `<FaseSelo {...faseSeloPropsDe(p, { comLink: false })} id={"p-" + p.id + "-fase"} />` e `aria-describedby` com `p-{id}-fase p-{id}-situacao p-{id}-datas` (só com os ids que existirem). |
| DS-UI-19 | TRM-044 · MPV | Com MPV, a Casa some dos controles, mas o texto não diz qual rito usar nem como fica o link de contagem (`&casa=` não se aplica). | deve corrigir | MPV: rito = o único da espécie (`casa_iniciadora: "congresso"`); `?casa=` ignorado; `hrefContagem = e => "/proposicoes?fase=" + e.fase + "&tipo=MPV"`. Critério novo: `/como-vira-lei?especie=MPV&casa=senado` mostra o rito da MPV sem chip de Casa. |
| DS-UI-20 | TRM-044 · mapa de IA (§1.2) | "N proposições acompanhadas estão nesta etapa →"; o texto do kit (validado em E02) é "… estão aqui agora", com a seta fora do nome do link. | sugestão | Alinhar o mapa de IA ao texto do kit. |
| DS-UI-21 | TRM-045 · Solução 2 (`extra`) | `<FaseSelo fase={e.fase} rotulo={e.fase_rotulo} />`: `GlossarioRead` não tem `fase_rotulo` (backlog-dados §1.5). Não compila. | bloqueia | `const f = mapa.fases.find(f => f.chave === e.fase && f.publicavel); extra = f?.rotulo ? <FaseSelo fase={e.fase} rotulo={f.rotulo} /> : undefined`. |
| DS-UI-22 | TRM-045 · grupos | Cada grupo é uma `GlossarioLista` em `<dl>`: com dezenas de entradas, sem navegação por títulos (U10). | deve corrigir | `<GlossarioLista nivelTitulo={3} …>` (cada termo vira `h3` dentro de `article`, o visual não muda); o foco programático no alvo da âncora já funciona (o kit põe `tabIndex={-1}` no título). Remover `prefixoAncora="termo-"` (é o padrão). |
| DS-UI-23 | TRM-045 · `#situacoes-por-fase` | A seção à parte existia porque `EtapaRito` não tinha encaixe; agora tem (`extra`). | sugestão | Passar as situações publicadas da fase como `extra` da primeira etapa de cada fase (onde `ancora` existe), e manter a seção à parte só para situações sem etapa correspondente. |
| DS-UI-24 | TRM-046 · `estado.ts` | `contagensPorEtapa(rito: RitoMapaApi, …, casa: "camara" \| "senado")`: `RitoMapaApi` não existe mais (é `RitoApi`) e a Casa da MPV é `congresso`. | deve corrigir | `contagensPorEtapa(rito: RitoApi, ps: Proposicao[], especie: Especie, casa: CasaRito \| null)` (tipos de `lib/tramitacao/tipos.ts`); `null` para MPV. |
| DS-UI-25 | TRM-046 · matriz E01/E02/E03 e textos do kit | Faltam ou mudaram textos padrão do kit nesta rodada: E01 ainda tem "Pulada" e "Agora"; não estão na matriz "Desde {data}", "Está aqui" (Etapas), "Tentar de novo" (registros), o resumo "Leitura do ZIL, conferida na Câmara em {data}" (ComoSabemos), o sufixo ", o que quer dizer" (TermoGlossario) e "Quem decide:" (RitoDiagrama). U3 exige todo texto na matriz. | deve corrigir | E01: trocar "Pulada" por "Dispensada", "Agora" por "Está aqui", acrescentar "Desde {data}". E02: acrescentar "Quem decide:". Linha nova G03 (TermoGlossario: ", o que quer dizer"), C04 (ComoSabemos: resumo padrão). M02: "Tentar de novo". G02: tirar "troca" (virou o padrão do kit). |
| DS-UI-26 | TRM-046 · nota da §4 | "o único `Aviso tom="contra"` é para erro de API que impede o conteúdo (I03, I09, I14)": I14 não impede o conteúdo. | deve corrigir | "(I03, I09)". E2e de estado de erro bloqueante não chamam `expectPaletaNeutra` na região do aviso (o `contra` é o tom do kit para erro). |
| DS-UI-27 | TRM-015, 016, 040–045 · `components/tramitacao/` | S2 (spec §7.3) manda componente novo para `components/ui/`; esta parte cria nove em `components/tramitacao/`. | sugestão (sem ação na interface) | Aceito pelo DS: são composições de domínio que recebem tipos da API, como `DirecaoBadge` e `CategoriaBadge` em `components/` (regra do README do kit). Condição: nenhuma primitiva visual nova ali — padrão que aparecer em dois lugares sobe para o kit (ver DS-UI-06). Pedido ao PM: S2 dizer "primitiva nova em `components/ui/`; composição de domínio em `components/<domínio>/`". |
| DS-UI-28 | TRM-022 · `texto_curto` | O `texto_curto` (≤ 160) é a definição que abre no termo em linha, isolada do resto da página. | sugestão | Regra no guia (§2) e caso no validador: `texto_curto` se lê sozinho — sem "como dito acima", sem depender do `termo` para fazer sentido, no máximo 2 frases (cabe em 36ch × 5 linhas no cartão do `TermoGlossario`). |
| DS-UI-29 | TRM-043 · chips de fase | O número do chip é lido como "Nas comissões 58" — sem unidade. | sugestão | Aceitável (padrão do kit); se o revisor de linguagem pedir, `aria-label` no chip: "Nas comissões, 58 proposições". |

## Veredito por tarefa

| Tarefa | Veredito | Condição |
| --- | --- | --- |
| TRM-015 | **Aprovada com ajustes** | DS-UI-06 (extrair `LinhasDaSituacao`) e DS-UI-08; DS-UI-07 opcional |
| TRM-016 | **Aprovada com ajustes** | DS-UI-08, DS-UI-09 |
| TRM-022 | **Aprovada** | DS-UI-28 opcional |
| TRM-040 | **Aprovada com ajustes** | Bloqueios DS-UI-01 e DS-UI-02 (tipos) antes do merge; DS-UI-03, 06, 08; DS-UI-04, 05, 07 opcionais |
| TRM-041 | **Aprovada com ajustes** | DS-UI-08, 09, 10, 11, 12; DS-UI-13, 14 opcionais |
| TRM-042 | **Aprovada com ajustes** | Bloqueio DS-UI-15 (MPV) antes do merge; DS-UI-08, 16, 17 |
| TRM-043 | **Aprovada com ajustes** | DS-UI-08, 09, 18; DS-UI-29 opcional |
| TRM-044 | **Aprovada com ajustes** | DS-UI-08, 16 (critério 5), 19; DS-UI-20 opcional |
| TRM-045 | **Aprovada com ajustes** | Bloqueio DS-UI-21 antes do merge; DS-UI-08, 22; DS-UI-23 opcional |
| TRM-046 | **Aprovada com ajustes** | DS-UI-12, 24, 25, 26 (046-A para os textos; 046-B para os tipos) |

Nenhuma tarefa reprovada: os quatro bloqueios são de tipo ou de escolha de rito, com a correção
escrita acima, e não mudam o desenho das páginas.

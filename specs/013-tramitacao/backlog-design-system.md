# Backlog de Design System — Tramitação (spec 013)

**Data:** 2026-10-30
**Autoria:** especialista de Design System (agente). Propõe; quem decide é a maintainer.
**Base:** [docs/DISCOVERY-TRAMITACAO.md](../../docs/DISCOVERY-TRAMITACAO.md) (§1.5, §4, §6),
brief comum do backlog, [spec.md](spec.md) (índice, ondas, gates §7, DoR/DoD §8),
código do kit nesta branch (`apps/web/components/ui/**`, `app/globals.css`,
`tailwind.config.js`) e no PR #48 (`origin/048-hemiciclo`), e o artefato
"ZIL Interface" (lido, **não** editado).
**Arquivos irmãos:** [spec.md](spec.md) (Product) · `backlog-dados.md`
(Arquitetura) · `backlog-interface.md` (UI/UX).
**Tarefas deste arquivo:** TRM-001, TRM-030 a TRM-036 (esqueleto) e duas novas,
**TRM-037** (`Recolhivel`) e **TRM-038** (zerar violações de a11y conhecidas).

Convenções: comandos rodam em `apps/web/` salvo indicação. "Kit" =
`apps/web/components/ui/`. Textos entre aspas nas specs de design são decisão
deste arquivo; rótulos de fase, glossário e rito vêm da API (mapa aprovado) e
aparecem aqui só como **exemplo de vitrine**. Gates de revisão = checklists
S1–S10 (Design System) e U1–U14 (UI/UX) de `spec.md` §7, materializados em
`docs/revisao/` por TRM-003 — este arquivo não os duplica; a TRM-036 só
acrescenta o "como verificar" de cada item.

---

## 0. Decisões em uma página

1. **Fase e status não têm matiz.** `alinhado` (verde), `contra` (vermelho) e
   `neutro` (âmbar) já significam alinhamento com a posição ZIL e atenção
   editorial ("não validado"). Fase, etapa, marco de tramitação, rito e
   desfecho usam só `texto`, `texto-2`, `superficie-1…4`, `inverso*`,
   `separador`. O estado se diz por **texto + forma** (barra cheia, meia,
   vazia, tracejada; marcador cheio, vazado, quadrado), nunca só por cor.
   Nenhuma cor nova sem token.
2. **O front exibe, não deriva.** Os componentes recebem rótulo, estado e
   texto prontos da API (`fase_rotulo`, `etapas[].estado`, glossário
   aprovado). A única lógica é de apresentação (contar "Etapa 3 de 6",
   escolher o glifo pelo estado) e está testada.
3. **`Etapas` perde a animação contínua** (D6 do PM: tirar). A etapa atual
   se marca por forma (meia barra), peso, texto lido e `aria-current="step"`.
   Vertical abaixo de `md`; variante `compacta` para "Onde está agora".
4. **Tudo no kit** (`components/ui/`), como pede S2: os componentes de
   tramitação são da família "Dados cívicos" do ZIL Interface (como
   `Hemiciclo` e `MapaUF`). Os tipos do contrato da API ficam em
   `apps/web/lib/tramitacao/tipos.ts`; os enums que o kit desenha (`Fase`,
   `Desfecho`, `EstadoEtapa`) moram no kit e o `lib` os reusa.
5. **`RitoDiagrama` é HTML semântico** (lista ordenada de etapas, cada uma com
   uma lista de ramos de desfecho), não SVG: reflui a 320 px e com zoom de
   400%, o leitor de tela navega por títulos e listas, e não há texto preso
   em coordenadas.
6. **`TermoGlossario` é disclosure**, não tooltip: gatilho
   `<span role="button" tabindex="0" aria-expanded aria-controls>` (um
   `<button>` não quebra linha e os termos oficiais têm até 85 caracteres) e
   definição logo depois no DOM; abre por clique/toque/Enter/Espaço, fecha
   por Esc, clique fora ou novo clique. Nada abre por hover.
7. **Testes:** Vitest 5 + Testing Library + jest-axe (componente, jsdom);
   Playwright 1.64 + @axe-core/playwright (navegador real, 375×812,
   768×1024, 1280×800, temas escuro e claro). Mock da API por `page.route()`
   com fixtures JSON. Regressão visual **só nas vitrines do kit**, com
   baseline gerada no contêiner oficial do Playwright. Scripts: `npm run test`
   e `npm run test:e2e` (os nomes que o PM assumiu, confirmados).
8. **Vitrine do kit** em `/kit/<componente>`, atrás da flag
   `NEXT_PUBLIC_KIT_VITRINE` (404 em produção): alvo dos testes no navegador,
   das capturas de evidência e documentação viva.
9. **Node 22** nos jobs de frontend da CI e no `Dockerfile` do web (Node 20
   está em fim de vida desde 30/04/2026 e as libs de teste atuais exigem
   ≥ 22.12).
10. **Duas tarefas novas:** TRM-037 promove o `SumarioLinha` da página da
    proposição a `Recolhivel` no kit (usado por 032, 033, 034, 035); TRM-038
    zera a lista de violações de a11y que TRM-001 vai encontrar nas páginas
    existentes.

---

## 1. Diagnóstico do kit para este tema

### 1.1 Inventário

| Componente | Arquivo | Para tramitação | O que fazer | Tarefa |
| --- | --- | --- | --- | --- |
| `Card`, `Estat`, `Painel` | `Card.tsx` | Serve | Nada. Atenção: `Card` com `href` é um link inteiro — nada clicável dentro (ex.: `FaseSelo` com `href`) | — |
| `Aviso` | `Aviso.tsx` | Serve | `padrao` para "tramita junto com…" e notas do ZIL; `neutro` (âmbar) **só** para "não validado / mapa em revisão" como faixa de página, nunca dentro de componente de fase; `contra` para erro de API | — |
| `Button`, `BotaoIcone` | `Button.tsx` | Serve | "Ver na Câmara ↗": `Button variante="fantasma"` + `Icone nome="externo"` + texto só para leitor "(abre em nova aba)" | — |
| `Chip`, `Chips`, `BarraFiltros` | `Chip.tsx` | Serve | Filtro de fase com `n`; `pontoClassName` nunca com `alinhado`/`contra`/`neutro` para fase | — |
| `Segmentado` | `Segmentado.tsx` | Serve com limite | Aceita 2–4 opções: dá para Casa iniciadora (Câmara/Senado), **não** para as 5 espécies (PL, PLP, PEC, MPV, PDL) → `Chips` com `href` | — |
| `Lista`, `Linha` | `Lista.tsx` | Serve para "Proposições ligadas" | Renderizam `div`, sem semântica de lista (`Lista.tsx:18`) — registrado em TRM-038 | 038 |
| `Vazio`, `Esqueleto`, `CardEsqueleto` | `Feedback.tsx` | Serve | Esqueletos próprios em 030 e 032 | — |
| `TituloSecao` | `Texto.tsx` | Serve | "Onde está agora", "O que aconteceu", "O caminho inteiro" (`nivel={2}`) | — |
| `Paginacao`, `Busca`, `Seletor` | — | Serve | "Todos os registros" paginado; busca no glossário | — |
| `Revelar` | `Revelar.tsx` | Com cuidado | Nunca em conteúdo de fase acima da dobra | — |
| `Selo` | `Selo.tsx` | **Muda** | Trunca sempre (`Selo.tsx:39`) e põe o texto inteiro só no `title` (`:31-34`), que o toque e o teclado não alcançam. Ganha `quebrar`, tom `elevado` e `href` | 031 |
| `Icone` | `Icone.tsx` | **Muda** | Faltam glifos `parada` (desfecho/interrompida), `duvida` (`nao_sabemos`), `conjunto` (apensada) | 031 |
| `Etapas` | `Tempo.tsx:44-72` | **Muda** | Ver §1.2 itens 1–4 | 030 |
| `LinhaDoTempo`, `Marco` | `Tempo.tsx:13-42` | **Muda** | Cor "segue o voto" (`:17`); hover em item não interativo (`:32`); faltam Casa/órgão, documento, marco de votação, marco atual, "todos os registros" | 032 |
| `SumarioLinha` (local) | `app/proposicoes/[id]/page.tsx:39-50` | **Promover** | Padrão `<details>` (UI-012) que vai ser repetido em 4 componentes | 037 |
| `Hemiciclo`, `MapaUF`, `Histograma` | PR #48 | Fora do tema | `Hemiciclo` é precedente bom (sim/não por claridade, não matiz). `Histograma` acende a barra "você está aqui" com `--alinhado` (`.zil-grafico .barra.is-aqui`) — uso de verde fora de alinhamento; apontar na revisão do #48 | — |
| `FaseSelo` | — | **Falta** | | 031 |
| `ComoSabemos` | — | **Falta** | | 033 |
| `RitoDiagrama` | — | **Falta** | | 034 |
| `TermoGlossario`, `GlossarioLista` | — | **Falta** | | 035 |
| `TodosOsRegistros` | — | **Falta** | | 032 |
| `Recolhivel` | — | **Falta** (promoção) | | 037 |
| Testes de frontend | — | **Falta** | Nenhum framework (`package.json` só tem `dev/build/start/lint/format`) | 001 |

### 1.2 Problemas, com evidência

1. **`Etapas` anima sozinha.** `Tempo.tsx:62` aplica `animate-zil-respira`
   (1,8 s, infinito; `tailwind.config.js:122,128`) à etapa atual. O README do
   kit proíbe "animação que roda sozinha" (`components/ui/README.md:17`) e o
   próprio ZIL Interface também ("Nada pisca nem anima sozinho, exceto o
   esqueleto"), embora a página "Etapas" do artefato contradiga o princípio.
   Com `prefers-reduced-motion` a regra global de `globals.css` corta para
   1 iteração — o problema é o padrão, não o modo reduzido.
2. **`Etapas` usa âmbar para "atual".** `bg-zil-neutro` (`Tempo.tsx:62`):
   âmbar já quer dizer "dividido" no score e "atenção / não validado" no
   `Aviso`. Fase não pode herdar esse sentido.
3. **`Etapas` rola 840 px no celular.** `grid-flow-col
   auto-cols-[minmax(120px,1fr)] … overflow-x-auto` (`Tempo.tsx:56`): 7
   etapas × 120 px numa tela de 343 px úteis (disc. §6.4). Rolagem lateral
   esconde a etapa atual quando ela está à direita.
4. **`Etapas` não fala.** Só `aria-current="step"`; não há "Etapa 3 de 6",
   nem estado lido ("concluída", "ainda não aconteceu"), nem estados
   `pulada`/`interrompida`, nem Casa. A `key` é o nome (`e.nome`), que se
   repete ("Plenário" na Câmara e no Senado; dois turnos de PEC).
5. **`Marco`: "A cor do marco segue o voto"** (`Tempo.tsx:17`). Na
   tramitação um marco de votação **não** pode ser verde por "aprovado"
   (disc. §6.5). O `tom` continua existindo para o uso original (alinhamento
   do voto de um parlamentar), documentado como tal.
6. **`Marco` parece clicável sem ser** (`hover:bg-zil-superficie-1` em todo
   item, `Tempo.tsx:32`) e o trilho depende de `ultimo` passado à mão.
7. **`Selo` trunca a situação oficial** (`app/proposicoes/[id]/page.tsx:148`
   e `app/proposicoes/page.tsx:215` passam a situação inteira a `<Selo>`;
   `Selo.tsx:39` trunca; o inteiro só no `title`). Correção de conteúdo é da
   UI/UX (TRM-015/016: situação oficial sai do Selo e vira texto); a do kit é
   TRM-031 (`quebrar` + regra "Selo é rótulo curto").
8. **Nenhum teste de frontend**; a CI (`.github/workflows/ci.yml`) só roda
   lint, `tsc` e build, em Node 20.
9. **Contraste de `texto-3`.** O ZIL Interface diz "4,4:1 ou mais"; medido:
   `texto-3` passa 4,5:1 sobre `fundo`, `superficie-1` e `superficie-2` nos
   dois temas, mas **falha sobre `superficie-3`** (3,96:1 escuro; 4,38:1
   claro). Regra para este épico: texto que informa usa `texto` ou `texto-2`;
   `texto-3` nunca em texto de estado.

Contrastes medidos (WCAG 2.x, tokens de `globals.css`):

| Par | Escuro | Claro |
| --- | --- | --- |
| `texto` / `superficie-1·2·3` | 15,3 · 13,7 · 11,9 | 18,1 · 15,6 · 14,4 |
| `texto-2` / `fundo` · `superficie-1·2·3` | 7,3 · 6,6 · 5,9 · 5,1 | 6,1 · 6,7 · 5,8 · 5,3 |
| `texto-3` / `superficie-1·2·3` | 5,1 · 4,5 · **4,0** | 5,5 · 4,8 · **4,4** |
| `inverso-texto` / `inverso` | 16,9 | 18,1 |
| `texto` · `texto-2` / `vidro-solido` | 14,4 · 6,2 | 17,5 · 6,5 |
| `foco` / `fundo` · `superficie-1` · `superficie-2` | 7,1 · 6,4 · 5,7 | 5,6 · 6,2 · 5,4 |
| `superficie-3` (trilho) / `superficie-1` | 1,3 | 1,3 |
| `superficie-4` (tracejado) / `superficie-1` | 1,5 | 1,4 |

As duas últimas linhas mostram que **trilho e tracejado não passam 3:1**
(1.4.11). Por isso o estado nunca depende da barra: o texto visível ou lido
carrega a informação, e a barra é redundante (fica dispensada de 1.4.11 por
não ser "necessária para entender o conteúdo"). Barras que carregam o estado
principal (`feita`, `atual`) usam `texto` sobre `superficie-3` (11,9 / 14,4).

### 1.3 Princípios do kit aplicados a fase e status

**Vocabulário visual de estado** — o mesmo em `Etapas`, `Marco` e
`RitoDiagrama`:

| Estado | Barra (`Etapas`) | Marcador de 24 px (`Marco`, `RitoDiagrama`), fundo `superficie-3` | Texto visível | Texto só para leitor de tela |
| --- | --- | --- | --- | --- |
| `feita` / marco passado | cheia, `bg-zil-texto` | ponto cheio 8 px `bg-zil-texto-2` | data | "(concluída)" |
| `atual` / marco mais recente | **meia**, `bg-zil-texto` | ponto cheio 10 px `bg-zil-texto` + anel 2 px `texto` | "Desde {data}" ou "Está aqui"; no rito, selo invertido "Está aqui" | "(etapa atual)" |
| `futura` | só trilho `bg-zil-superficie-3` | anel vazado 8 px (`shadow-[inset_0_0_0_2px_var(--texto-2)]`) | "—" (oculto do leitor) | "(ainda não aconteceu)" |
| `pulada` | trilho tracejado (`.zil-tracejado`) | anel vazado tracejado | "Dispensada" + motivo | — |
| `interrompida` | meia, `bg-zil-texto-2` + quadrado ■ antes do nome | quadrado 8 px `bg-zil-texto`, cantos 2 px | "Parou aqui" + data + motivo | — |
| `futura` depois de `interrompida` | só trilho | anel vazado | "Não aconteceu" | — |
| Desfecho (`FaseSelo`) | — | glifo `parada` | rótulo da API ("Arquivada") | "Desfecho: " antes |
| `norma` (`FaseSelo`) | — | glifo `documento` | rótulo da API ("Virou lei") | "Fase: " antes |
| `nao_sabemos` (`FaseSelo`) | — | glifo `duvida` | rótulo da API | — |

Regras:

- **Cor:** `alinhado*`, `contra*` e `neutro*` ausentes de todo componente
  deste épico. Verificação automática: `classesDeAlinhamento()` (Vitest) e
  `expectPaletaNeutra()` (Playwright), ambos de TRM-001. O item S4 de
  `spec.md` §7.3 cita só `alinhado`/`contra`; proponho incluir `neutro`
  (§5, conflito 7).
- **Desfecho não é falha.** Mesma família visual de `norma` (terminal: tom
  `elevado`), glifo `parada`, rótulo do mapa. Nada de ✕, vermelho ou risco.
- **Tokens permitidos:** `texto`, `texto-2`, `superficie-1…4`, `inverso`,
  `inverso-hover`, `inverso-texto`, `separador`, `foco`, `vidro-solido`;
  tamanhos `text-titulo-4`, `text-texto`, `text-texto-ui`, `text-texto-s`,
  `text-legenda`, `text-rotulo`; raios `rounded-pilula`, `rounded-m`,
  `rounded-l`, `rounded-2xl`; durações `duration-toque`, `duration-padrao`.
  Nenhum token novo neste épico; uma classe de composição nova
  (`.zil-tracejado`, TRM-030) feita só de variáveis existentes.
- **Movimento:** nada roda sozinho; o único movimento novo é o
  `animate-zil-surge` (220 ms, já existente) ao abrir a definição do
  `TermoGlossario` no desktop. `prefers-reduced-motion` já corta tudo
  (`globals.css`, bloco final).
- **Texto:** pt-BR; datas dd/mm/aaaa dentro de `<time dateTime="aaaa-mm-dd">`;
  rótulos de fase e textos de glossário/rito vêm da API (mapa aprovado);
  textos de estado e microcopy dos componentes estão escritos nas specs abaixo
  e passam pela matriz de TRM-046 (UI/UX).
- **Superfície:** sem borda como separação; o rito e a linha do tempo usam
  trilho `separador` de 2 px (padrão já existente no `Marco`); ramos de
  desfecho ficam em bloco `superficie-2` dentro do cartão, nunca em cartão
  dentro de cartão.

### 1.4 Onde mora cada coisa

| O quê | Onde | Por quê |
| --- | --- | --- |
| `Etapas`, `EtapasEsqueleto`, `EstadoEtapa`, `Etapa` | `components/ui/Etapas.tsx` (sai de `Tempo.tsx`) | arquivo próprio evita conflito entre TRM-030 e TRM-032 |
| `LinhaDoTempo`, `Marco`, `TodosOsRegistros` | `components/ui/Tempo.tsx` (+ `TodosOsRegistros.tsx`, cliente) | |
| `FaseSelo`, `FaseSeloEsqueleto`, `Fase`, `Desfecho` | `components/ui/FaseSelo.tsx` | família "Dados cívicos" |
| `ComoSabemos` | `components/ui/ComoSabemos.tsx` | genérico: fase, Bússola, norma |
| `RitoDiagrama` | `components/ui/RitoDiagrama.tsx` | |
| `TermoGlossario` | `components/ui/TermoGlossario.tsx` (`"use client"`) | |
| `GlossarioLista` | `components/ui/GlossarioLista.tsx` (servidor) | |
| `Recolhivel` | `components/ui/Recolhivel.tsx` (servidor) | |
| Tipos do contrato da API | `lib/tramitacao/tipos.ts` (TRM-031-A) | espelho de backlog-dados.md §1.5; reusa os enums do kit |
| Adaptadores API → props | `lib/tramitacao/como-sabemos.ts` (033: `comoSabemosDaFase`, `dataBR`), `lib/tramitacao/eventos.ts` (032: `marcoDaApi`, `registroDoEvento`), `lib/tramitacao/rito.ts` (034-B), `lib/tramitacao/glossario.ts` (035) | funções puras, testadas; contratos de backlog-dados.md §1.5 |
| Vitrines | `app/kit/<slug>/page.tsx` + `casos.tsx` | casos reusados pelos testes de componente |

Server Component por padrão (S9): só `TermoGlossario` e `TodosOsRegistros`
levam `"use client"`. `Recolhivel` é `<details>` nativo, sem JavaScript.

**Exceção aceita a S9 (registrada a pedido da UI/UX):** as páginas
`/como-vira-lei` e `/como-vira-lei/situacoes` não têm interação que exija
cliente, mas buscam `/tramitacao/mapa` no navegador, como todas as páginas do
site. Aceita porque: (1) é o que o `page.route()` de TRM-001 intercepta — buscar
no servidor tiraria as duas páginas dos testes com a API falsa; (2) o site está
em `noindex`, então o ganho de SEO do HTML pronto não existe hoje; (3) a
UI/UX mantém o `page.tsx` como Server Component (casca, `metadata`,
`Suspense`) e só o filho que busca é cliente, o que torna a troca barata.
Condições: os componentes do kit usados ali continuam servidor; nenhum outro
filho vira cliente "de carona". **Quando revisitar:** ao ligar a indexação
(`NEXT_PUBLIC_INDEXACAO_PUBLICA`) ou se o mapa passar a ser lido no servidor —
aí o caminho é o servidor de fixtures descrito nos Riscos de TRM-001 e
`fetch(..., { next: { revalidate: 3600 } })` no `page.tsx`.

### 1.5 Compatibilidade

Conferido nesta branch:

```bash
cd apps/web
grep -rnE "<(Etapas|LinhaDoTempo|Marco)\b|\b(Etapas|LinhaDoTempo|Marco)\b[^\"]*from \"@/components/ui\"" app components lib | grep -v components/ui/
# → nada. (`interface Marco` em app/bussula/page.tsx:11 é um tipo local, não o componente.)
grep -rn "zil-respira" app components lib tailwind.config.js
# → components/ui/Tempo.tsx:62 e tailwind.config.js:122,128 — só o Etapas.
grep -rn "<Selo" app components | wc -l
# → 25 usos. Mudanças no Selo são só aditivas (props novas opcionais, tom novo).
```

`Etapas`, `LinhaDoTempo` e `Marco` não têm uso em página: as APIs podem mudar
sem migração (repetir o grep antes de cada PR — TRM-015/016 podem ter
começado a usar). `Selo`: comportamento padrão idêntico; um teste de TRM-031
fixa a string de classes do `Selo` padrão. PR #48 mexe em `index.ts`,
`README.md` e `globals.css` do kit: mergear antes de 030–035 ou rebasear
(spec §5.3).

---

## 2. Tarefas

### TRM-001 — Infra de testes do frontend (Vitest + Testing Library + jest-axe; Playwright + axe nos 3 breakpoints; job na CI)

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E0 Fundações · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** G, quebrada em **001-A** (M: Vitest + Testing Library + jest-axe + teste do `Selo` + job `test-frontend`) e **001-B** (M: Playwright + axe + vitrine `/kit` + mock da API + evidências + visual + job `e2e-frontend`). Dois PRs, A antes de B.
**Dono da spec:** Design System · **Revisões obrigatórias:** Arquitetura (CI, Node, dependências) + Maintainer
**Depende de:** nada no backlog; base `main` depois do merge do #50 · **Desbloqueia:** TRM-030 a TRM-038 e os testes de interface de TRM-015, 016, 040–047 (spec §7.4 e §8.2 exigem os jobs desta tarefa)

**Problema**
- `apps/web/package.json` não tem framework de teste (scripts `dev`, `build`,
  `start`, `lint`, `format`). A CI roda só `npm run lint`, `npx tsc --noEmit` e
  `npm run build` (`.github/workflows/ci.yml`, jobs `lint-frontend` e
  `build-frontend`), em Node 20.
- Nenhum dos 20 arquivos do kit tem teste. Acessibilidade e responsividade são
  conferidas a olho: o `Etapas` rola 840 px a 375 (disc. §6.4) e ninguém viu,
  porque nenhuma página o usa.
- A spec do PM exige 0 violações axe em 375/768/1280 × 2 temas em todo PR de
  UI (métrica M11, §7.4) — hoje não há como medir.
- Node 20 está em fim de vida desde 30/04/2026; as versões atuais de Vitest
  (5.x), jsdom (30.x), jest-dom (7.x) e @axe-core/playwright (4.14) exigem
  Node ≥ 22.12.

**Oportunidade** — Toda tarefa de interface passa a provar na CI que cada
estado renderiza, o que o leitor de tela lê, que não há violação WCAG 2.2 A/AA
nos dois temas e três larguras, que não há rolagem horizontal a 375 e que a
aparência do kit não mudou sem querer. Para o cidadão: componentes de
tramitação que funcionam no celular e com leitor de tela desde o primeiro dia.

**Solução — decisões**

| Decisão | Escolha | Por quê | Rejeitado |
| --- | --- | --- | --- |
| Teste de componente | Vitest 5 + jsdom + Testing Library + jest-axe | É o caminho do guia oficial do Next para Vitest; rápido; TS e JSX sem config extra | Jest (transform de Next 14 + ESM mais trabalhoso e lento) |
| E2E | Playwright 1.64 (Chromium) + @axe-core/playwright | Larguras como projetos, temas como parâmetro; axe no navegador real calcula contraste, que o jsdom não calcula | Cypress (mais pesado, paralelismo pago); WebKit/Firefox ficam para depois |
| Mock da API no e2e | `page.route()` + fixtures JSON em `tests/fixtures/api/` | As páginas buscam no navegador (`"use client"` + `fetch` em `app/proposicoes/page.tsx:71`, `app/proposicoes/[id]/page.tsx:68-70`, `app/votacoes/[id]/page.tsx:109-110`): interceptar a rede do navegador basta, sem código de teste no app | **MSW** (exige service worker em `public/` e bootstrap no app; só compensaria com fetch no servidor, que hoje não existe — se um dia existir, ver Riscos) |
| Mock em teste de componente | Nenhum | Componentes do kit recebem dados por props | — |
| Componente no navegador | Vitrine `/kit/<slug>` (rotas do próprio Next, atrás de `NEXT_PUBLIC_KIT_VITRINE`) | Mesmo CSS, fontes e tokens de produção; vira documentação viva (TRM-036) e alvo de captura | Storybook (outro bundler e outra config de Tailwind/next/font para uma maintainer só); Playwright Component Testing (experimental) |
| Evidências de PR (spec §7.4) | Captura de página inteira e relatório axe JSON de cada teste de vitrine e de rota, nas 3 larguras × 2 temas, salvos em `apps/web/evidencias/` e publicados como artefato da CI em todo run | É o que o PM pede como prova | — |
| Regressão visual | **Sim, limitada**: só vitrines do kit; projetos `celular` e `desktop`; 2 temas; casos marcados `visual` (≤ 4 por componente); captura por caso (`[data-caso]`); baseline gerada no contêiner `mcr.microsoft.com/playwright:v1.64.1-noble`; `threshold: 0.2` + `maxDiffPixels: 50`; tag `@visual`; **bloqueante na CI** | O risco do kit é mudar token ou classe e alterar 25 usos sem ninguém ver; página muda com dado e fica só com a11y + comportamento; captura por caso deixa a tolerância significativa | Página inteira (frágil com dado); baseline gerada no macOS (antialiasing difere do Linux); tablet (cobre pouco além de celular e desktop e dobra o número de imagens) |
| Node | 22 nos jobs de frontend, no `Dockerfile` do web e em `.nvmrc` | Requisito das libs; Node 20 EOL | — |

**Versões fixadas** (exatas, sem `^`, em `devDependencies`; todas publicadas há
mais de duas semanas em 30/10/2026, exceto onde dito):

| Pacote | Versão | Observação |
| --- | --- | --- |
| `vitest` | 5.0.5 | Node `^22.12 \|\| ^24` |
| `vite` | 8.3.4 | peer obrigatório do Vitest 5 |
| `@vitejs/plugin-react` | 6.1.2 | peer `vite ^8` |
| `jsdom` | 30.1.3 | Node `^22.22.2 \|\| ^24.15` |
| `@testing-library/react` | 16.3.3 | peer React 18 |
| `@testing-library/dom` | 10.4.2 | peer do anterior |
| `@testing-library/jest-dom` | 7.0.1 | entrada `@testing-library/jest-dom/vitest`; se não existir na 7.x, use 6.10.0 |
| `@testing-library/user-event` | 14.6.8 | |
| `jest-axe` | 11.0.0 | sem tipos próprios; ver shim abaixo. **Não** instale `@types/jest-axe` (3.5.9, puxa `@types/jest` e axe-core 3) |
| `@playwright/test` | 1.64.1 | casar com a imagem `v1.64.1-noble` |
| `@axe-core/playwright` | 4.14.0 | publicado em 15/10/2026 |
| `@types/node` | 22.20.5 | sobe de `^20`: o peer opcional do Vitest 5 é `^22 \|\| >=24`, e a 20 instalada gera conflito de peer |
| `@types/react-dom` | 18.3.7 | faltava; peer opcional do Testing Library |

Se `npm install` reclamar de peer, **não** use `--legacy-peer-deps`: ajuste a
versão e registre no PR.

**Estrutura de pastas**

```
apps/web/
  .nvmrc                          22
  vitest.config.mts
  playwright.config.ts
  app/kit/
    layout.tsx                    404 sem a flag; noindex
    page.tsx                      índice das vitrines (lista mantida à mão)
    _vitrine.tsx                  <Vitrine> e <Caso> (não é rota)
    _tema.tsx                     "use client": Segmentado Escuro/Claro para humanos
    selo/page.tsx                 vitrine-exemplo desta tarefa
  tests/
    setup/
      vitest.setup.ts             jest-dom, cleanup, matcher do axe, stubs do jsdom
      axe.ts                      axe configurado (contraste e region desligados no jsdom)
      jest-axe.d.ts               tipos do jest-axe (shim ambiente)
      vitest-matchers.d.ts        toHaveNoViolations no expect do Vitest
    helpers/
      paleta.ts                   classesDeAlinhamento() para Vitest
    componentes/                  um <Componente>.test.tsx por componente do kit
      Selo.test.tsx
    unit/                         funções puras (lib/**) e a flag da vitrine
      kit-flag.test.tsx
    e2e/
      helpers/
        teste.ts                  test estendido com a API falsa
        api.ts                    instalarApiFalsa()
        tema.ts                   TEMAS, aplicarTema()
        vitrine.ts                abrirVitrine(), fotografarCasos()
        a11y.ts                   semViolacoes()
        layout.ts                 semRolagemHorizontal()
        paleta.ts                 expectPaletaNeutra()
        movimento.ts              animacoesInfinitas()
        evidencia.ts              registrarEvidencia()
      a11y-conhecidas.ts          violações pré-existentes, por rota (catraca)
      kit/selo.spec.ts
      paginas/proposicoes.spec.ts
      __screenshots__/            baselines @visual (commitadas)
    fixtures/
      api/proposicoes/lista.json  resposta de GET /proposicoes
  evidencias/                     gerado; ignorado pelo git; artefato da CI
```

**Specs técnicas**

1. `package.json` — scripts (os dois primeiros são os nomes que a spec do PM
   assume):

```json
{
  "test": "vitest run",
  "test:watch": "vitest",
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui",
  "build:e2e": "NEXT_DIST_DIR=.next-e2e NEXT_PUBLIC_API_URL=http://api.zil.test NEXT_PUBLIC_KIT_VITRINE=true next build",
  "start:e2e": "NEXT_DIST_DIR=.next-e2e next start -p 3100",
  "test:visual": "docker run --rm --ipc=host -e VISUAL=1 -v \"$PWD\":/work -v /work/node_modules -w /work mcr.microsoft.com/playwright:v1.64.1-noble bash -lc 'npm ci && npx playwright test --grep @visual'",
  "test:visual:atualizar": "docker run --rm --ipc=host -e VISUAL=1 -v \"$PWD\":/work -v /work/node_modules -w /work mcr.microsoft.com/playwright:v1.64.1-noble bash -lc 'npm ci && npx playwright test --grep @visual --update-snapshots'"
}
```

   `VAR=x comando` funciona em macOS e Linux (não em `cmd` do Windows — fora
   de escopo). O volume anônimo `/work/node_modules` impede que o `npm ci` do
   contêiner troque os binários nativos do `node_modules` do Mac.

2. `next.config.js` — `distDir: process.env.NEXT_DIST_DIR || ".next"`, para o
   build de e2e não pisar no `.next` do `npm run dev`.
3. `tsconfig.json` — acrescentar `".next-e2e/types/**/*.ts"` ao `include` (sem
   isso o `next build` com outro `distDir` reescreve o tsconfig e suja a
   árvore) e `"playwright-report"`, `"test-results"`, `"evidencias"` ao
   `exclude`.
4. `.gitignore` da raiz — `.next-e2e/`, `playwright-report/`,
   `test-results/`, `blob-report/`, `apps/web/evidencias/`. As baselines em
   `tests/e2e/__screenshots__/` **são** versionadas.
5. `.nvmrc` com `22`; `Dockerfile` do web: `FROM node:22-alpine`.
6. `vitest.config.mts`:

```ts
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const raiz = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  // "@/x" → apps/web/x, como no tsconfig. Regex para não casar "@testing-library".
  resolve: { alias: [{ find: /^@\//, replacement: raiz }] },
  test: {
    environment: "jsdom",
    include: ["tests/componentes/**/*.test.{ts,tsx}", "tests/unit/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/setup/vitest.setup.ts"],
    css: false,
    restoreMocks: true,
  },
});
```

7. `tests/setup/vitest.setup.ts`:

```ts
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { toHaveNoViolations } from "jest-axe";
import { afterEach, expect } from "vitest";

expect.extend(toHaveNoViolations);
// Sem `globals: true`, o Testing Library não registra a limpeza sozinho.
afterEach(() => cleanup());

// O jsdom não tem estas APIs; o kit as usa em efeitos (Segmentado, Revelar).
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({ matches: false, media: query, onchange: null, addListener() {}, removeListener() {},
       addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false }) as MediaQueryList;
}
```

8. `tests/setup/axe.ts`:

```ts
import { configureAxe } from "jest-axe";

export const axe = configureAxe({
  rules: {
    // Contraste depende do CSS computado dos temas, que o jsdom não calcula:
    // é verificado no Playwright, nos dois temas.
    "color-contrast": { enabled: false },
    // Componente isolado não está dentro de landmark; landmarks são
    // verificados nas páginas, no Playwright.
    region: { enabled: false },
  },
});
```

9. `tests/setup/jest-axe.d.ts` (arquivo **sem** import no topo, para ser
   declaração ambiente):

```ts
declare module "jest-axe" {
  import type { AxeResults, RunOptions, Spec } from "axe-core";
  export interface OpcoesAxe extends RunOptions {
    globalOptions?: Spec;
    impactLevels?: Array<"minor" | "moderate" | "serious" | "critical">;
  }
  export function configureAxe(opcoes?: OpcoesAxe): (html: Element | string, opcoes?: RunOptions) => Promise<AxeResults>;
  export const axe: ReturnType<typeof configureAxe>;
  export const toHaveNoViolations: {
    toHaveNoViolations(resultado: AxeResults): { pass: boolean; message(): string };
  };
}
```

   `tests/setup/vitest-matchers.d.ts`:

```ts
import "vitest";

declare module "vitest" {
  interface Matchers<T = any> {
    toHaveNoViolations(): T;
  }
}
```

   Se o `tsc` não resolver `axe-core`, acrescente `axe-core@4.14.0` às
   `devDependencies`.

10. `tests/helpers/paleta.ts`:

```ts
/** Classes que usam as cores de alinhamento ou de atenção. Fase e status não podem usá-las. */
export function classesDeAlinhamento(raiz: Element): string[] {
  const re = /\b(?:bg|text|fill|stroke|shadow|outline|ring|decoration|border)-zil-(?:alinhado|contra|neutro)(?:-fundo)?\b/;
  return [raiz, ...Array.from(raiz.querySelectorAll("[class]"))]
    .map((e) => e.getAttribute("class") ?? "")
    .filter((c) => re.test(c));
}
```

11. Teste-exemplo `tests/componentes/Selo.test.tsx` (prova a infra; cobre o
    comportamento **atual** do `Selo`, que TRM-031 estende):

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Selo } from "@/components/ui";
import { axe } from "../setup/axe";

describe("Selo", () => {
  it("mostra o texto e esconde o ponto do leitor de tela", () => {
    const { container } = render(<Selo ponto>Pronta para Pauta</Selo>);
    expect(screen.getByText("Pronta para Pauta")).toBeInTheDocument();
    const ponto = container.querySelector("span > span[aria-hidden='true']");
    expect(ponto).not.toBeNull();
  });

  it("põe o texto inteiro no title quando o conteúdo é string", () => {
    render(<Selo>Aguardando Designação de Relator(a)</Selo>);
    expect(screen.getByTitle("Aguardando Designação de Relator(a)")).toBeInTheDocument();
  });

  it("aplica o par cor/fundo do tom", () => {
    const { container } = render(<Selo tom="neutro">Não validado</Selo>);
    expect(container.firstElementChild).toHaveClass("bg-zil-neutro-fundo", "text-zil-neutro");
  });

  it("o tom padrão não usa cor de alinhamento", () => {
    const { container } = render(<Selo>Indústria</Selo>);
    expect(container.firstElementChild).toHaveClass("bg-zil-superficie-2", "text-zil-texto-2");
  });

  it("não tem violações de acessibilidade", async () => {
    const { container } = render(
      <p>
        Situação: <Selo tom="neutro" ponto>Não validado</Selo>
      </p>,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
```

12. Vitrine. `app/kit/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { notFound } from "next/navigation";

export const metadata: Metadata = { title: "Kit — ZIL Observatório", robots: { index: false, follow: false } };

/** Vitrine do kit: só existe com NEXT_PUBLIC_KIT_VITRINE=true (build de e2e). Em produção, 404. */
export default function KitLayout({ children }: { children: React.ReactNode }) {
  if (process.env.NEXT_PUBLIC_KIT_VITRINE !== "true") notFound();
  return children;
}
```

    `app/kit/_vitrine.tsx` exporta:
    - `Vitrine({ titulo, descricao?, children })`: `zil-container`, chapéu
      "Kit · vitrine" (`text-rotulo uppercase text-zil-texto-2`), `<h1
      className="text-titulo-1">`, o `<TemaVitrine />` de `_tema.tsx` e os
      casos em `<div className="zil-secao grid gap-12">`. Abaixo do título,
      `<Aviso titulo="Exemplos de demonstração">Os dados desta página são
      exemplos para testar o componente. Não são dados publicados.</Aviso>`.
    - `Caso({ id, titulo, children, fundo = "pagina", visual = false })`:
      `<section aria-labelledby={`caso-${id}`} data-caso={id}
      data-visual={visual || undefined} className="grid gap-3">` com `<h2
      id={`caso-${id}`} className="text-titulo-4">` e o conteúdo; com
      `fundo="cartao"`, o conteúdo vai dentro de `<Card>` (a maioria dos
      componentes vive em cartão: o contraste tem de ser testado sobre
      `superficie-1` também).
    `app/kit/_tema.tsx` (`"use client"`): `Segmentado` "Escuro / Claro" que
    faz `document.documentElement.setAttribute("data-theme", valor)`.
    `app/kit/page.tsx`: lista de links para as vitrines (constante
    `VITRINES: { slug: string; nome: string }[]`; cada tarefa de componente
    acrescenta uma linha).
    `app/kit/selo/page.tsx`: casos `tons` (os 5 tons, `visual`), `com-ponto`,
    `com-icone`, `texto-longo-em-cartao` (`fundo="cartao"`, `max-w-[343px]`,
    texto "Aguardando Designação - Aguardando Devolução de Relator(a) que
    deixou de ser Membro", `visual`).

13. `playwright.config.ts`:

```ts
import { defineConfig } from "@playwright/test";

const PORTA = 3100;
const CI = !!process.env.CI;

export default defineConfig({
  testDir: "./tests/e2e",
  snapshotPathTemplate: "{testDir}/__screenshots__/{projectName}/{testFilePath}/{arg}{ext}",
  fullyParallel: true,
  forbidOnly: CI,
  retries: CI ? 1 : 0,
  workers: CI ? 2 : undefined,
  reporter: CI ? [["github"], ["html", { open: "never" }]] : [["list"]],
  // Visual só no contêiner Linux (CI ou npm run test:visual): no macOS o
  // antialiasing difere e a comparação falharia sem mudança real.
  grepInvert: CI || process.env.VISUAL ? undefined : /@visual/,
  expect: {
    toHaveScreenshot: { threshold: 0.2, maxDiffPixels: 50, animations: "disabled", caret: "hide", scale: "css" },
  },
  use: {
    baseURL: `http://localhost:${PORTA}`,
    browserName: "chromium",
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    colorScheme: "dark",
    // Estado final, sem Revelar escondendo conteúdo. Teste de movimento liga
    // "no-preference" explicitamente.
    reducedMotion: "reduce",
    trace: "on-first-retry",
  },
  projects: [
    { name: "celular", use: { viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true } },
    { name: "tablet", use: { viewport: { width: 768, height: 1024 }, hasTouch: true }, grepInvert: /@visual/ },
    { name: "desktop", use: { viewport: { width: 1280, height: 800 } } },
    // WCAG 1.4.10: reflow a 320 px. Só os testes marcados @reflow (sem rolagem horizontal); sem axe nem capturas.
    { name: "reflow-320", use: { viewport: { width: 320, height: 640 }, isMobile: true, hasTouch: true }, grep: /@reflow/ },
  ],
  webServer: {
    command: "npm run build:e2e && npm run start:e2e",
    url: `http://localhost:${PORTA}/kit`,
    reuseExistingServer: !CI,
    timeout: 300_000,
  },
});
```

14. Helpers de e2e (assinaturas e comportamento):

| Arquivo | Exporta | Faz |
| --- | --- | --- |
| `api.ts` | `const API = "http://api.zil.test"`; `instalarApiFalsa(page): Promise<ApiFalsa>`; ver a interface abaixo | `page.route(`${API}/**`)`; a chave é `"MÉTODO /caminho"` (`responder("/proposicoes", …)` vale `GET`). `resposta` string = nome do arquivo em `tests/fixtures/api/` sem `.json`, lido com `fs`. Rota paginada (`responderPaginas`) lê o parâmetro da query; as demais ignoram a query. Sem rota cadastrada: responde `599` e anota em `naoAtendidas`. Toda requisição atendida vai para `chamadas`. **CORS** (a página em `localhost:3100` busca em `api.zil.test`: o Chromium aplica CORS também a `route.fulfill`): todo `fulfill`, inclusive o 599, leva `access-control-allow-origin: *`, `access-control-expose-headers: X-Total-Count` e `content-type: application/json; charset=utf-8`; `OPTIONS` (preflight) responde 204 com os mesmos cabeçalhos mais `access-control-allow-methods: GET` e `access-control-allow-headers: *` — revisão da Arquitetura, item 1 |
| `teste.ts` | `test` (= `base.extend<{ api: ApiFalsa }>`), `expect` | Instala a API falsa antes; depois do teste, `expect(api.naoAtendidas, "requisições à API sem fixture").toEqual([])` |

    Interface da API falsa (unifica o helper de paginação que a UI/UX
    previa em `tests/e2e/helpers/lista.ts` — esse arquivo **não** é criado;
    TRM-016 e TRM-041 usam `responderPaginas`):

```ts
/** `cabecalhos` somam-se aos de CORS (ex.: { "X-Total-Count": "130" } para a lista, TRM-014). */
export type Resposta = string | { status: number; corpo?: unknown; cabecalhos?: Record<string, string> };
export interface ApiFalsa {
  /** Uma resposta para a rota. Com função, a resposta é escolhida pela URL (query) — UX-DS-25. */
  responder(rota: string, resposta: Resposta | ((url: URL) => Resposta)): void;
  /**
   * Uma fixture por página: `?page=N` (ou `parametro`) recebe `paginas[N-1]`; sem o
   * parâmetro, página 1. Página além da lista → `alem` se dado, senão 599 + `naoAtendidas`.
   * `falharNaPagina` responde 500 nessa página (estado de erro).
   */
  responderPaginas(rota: string, paginas: string[], opcoes?: { parametro?: string; alem?: Resposta; falharNaPagina?: number }): void;
  /** Requisições atendidas, na ordem: `{ chave: "GET /proposicoes", query: "?page=2&per_page=100" }`. */
  chamadas: { chave: string; query: string }[];
  naoAtendidas: string[];
}
```

    Uso: `api.responderPaginas("/proposicoes", ["tramitacao/lista-p1",
    "tramitacao/lista-p2"], { alem: { status: 200, corpo: [] } })` (lista que
    pede páginas até vir uma curta) e
    `api.responderPaginas("/proposicoes/<id>/tramitacao/eventos",
    ["tramitacao/eventos-08-p1", "tramitacao/eventos-08-p2"])`; "uma chamada só
    na primeira abertura" se afirma com `api.chamadas.filter(…).length`.
| `tema.ts` | `TEMAS = ["escuro", "claro"] as const`; `type Tema`; `aplicarTema(page, tema)` | `document.documentElement.setAttribute("data-theme", tema)` via `page.evaluate`, depois de carregar (o layout fixa `data-theme="escuro"` no HTML; o React não reverte o atributo) |
| `vitrine.ts` | `abrirVitrine(page, slug, tema)`; `fotografarCasos(page, slug, tema)` | `goto(/kit/${slug})`, `aplicarTema`, `document.fonts.ready`. `fotografarCasos`: para cada `[data-caso][data-visual]`, `expect(loc).toHaveScreenshot(`${slug}-${id}-${tema}.png`)` |
| `a11y.ts` | `semViolacoes(page, { rota, incluir?, tema })` | `new AxeBuilder({ page }).withTags(["wcag2a","wcag2aa","wcag21a","wcag21aa","wcag22aa"])`; filtra as regras de `a11y-conhecidas.ts` para a `rota`; falha com a lista legível (regra, alvo, resumo) das novas; falha também se uma conhecida **não** aparecer mais ("remova de a11y-conhecidas.ts"); grava o JSON em `evidencias/a11y/<projeto>/<rota>-<tema>.json` |
| `layout.ts` | `semRolagemHorizontal(page)` | `scrollWidth - clientWidth` do `documentElement` ≤ 0 |
| `paleta.ts` | `expectPaletaNeutra(page, seletor)` | Lê `--alinhado`, `--contra`, `--neutro` e os `-fundo` do tema atual (resolvendo num elemento temporário), varre os descendentes de `seletor` e falha se `color`, `background-color`, `fill`, `stroke`, `border-color` ou `outline-color` computados forem iguais a algum deles |
| `movimento.ts` | `animacoesInfinitas(page, seletor?)` | `document.getAnimations()` filtradas por `iterations === Infinity`, fora de `.zil-esqueleto`, dentro do seletor; devolve a contagem |
| `foco.ts` | `focoVisivelENaoEncoberto(page, locator)` | Leva o foco por teclado (`Tab` até o elemento; `locator.focus()` como último recurso), confere `outline-style` computado `solid` e que o retângulo do elemento não cruza o de `nav[aria-label="Principal"]` nem, quando visível, o de `nav[aria-label="Atalhos"]` (2.4.7, 2.4.11; U9) — UX-DS-23 |
| `evidencia.ts` | `registrarEvidencia(page, nome, tema)` | `page.screenshot({ fullPage: true, path: evidencias/<projeto>/<tema>/<nome>.png })` |

15. `tests/e2e/a11y-conhecidas.ts`: `export const CONHECIDAS: Record<string,
    { regra: string; motivo: string }[]>`, por rota (`"/proposicoes"`). Começa
    vazio; se o primeiro run de `/proposicoes` acusar violações, **não
    corrija nesta tarefa**: registre cada regra com o motivo e abra a TRM-038.
    Trava (UX-DS-26): `tests/unit/a11y-conhecidas.test.ts` falha se
    `CONHECIDAS` tiver chave fora da lista fixa de rotas antigas — `/`,
    `/proposicoes`, `/proposicoes/[id]`, `/votacoes/[id]`, `/bussula`,
    `/metodologia`, `/manifesto`. Rota nova do épico (`/kit/*`,
    `/como-vira-lei*`) nunca entra na catraca: M11 = 0.
16. `tests/e2e/kit/selo.spec.ts` (o molde de todo teste de vitrine):

```ts
import { semViolacoes } from "../helpers/a11y";
import { registrarEvidencia } from "../helpers/evidencia";
import { semRolagemHorizontal } from "../helpers/layout";
import { TEMAS } from "../helpers/tema";
import { test } from "../helpers/teste";
import { abrirVitrine, fotografarCasos } from "../helpers/vitrine";

for (const tema of TEMAS) {
  test.describe(`Selo — tema ${tema}`, () => {
    test.beforeEach(async ({ page }) => abrirVitrine(page, "selo", tema));
    test("sem violações WCAG 2.2 AA", async ({ page }) => semViolacoes(page, { rota: "/kit/selo", tema }));
    test("sem rolagem horizontal @reflow", async ({ page }) => semRolagemHorizontal(page));
    test("evidência", async ({ page }) => registrarEvidencia(page, "kit-selo", tema));
    test("aparência @visual", async ({ page }) => fotografarCasos(page, "selo", tema));
  });
}
```

17. `tests/e2e/paginas/proposicoes.spec.ts`: `api.responder("/proposicoes",
    "proposicoes/lista")` com 3 proposições (uma com a situação mais longa do
    banco, `foto`/`url` nulos para não sair da rede); afirma o `h1`, o texto
    "3 proposições" e os três cartões **com o conteúdo da fixture** (o
    `tipo numero/ano` de cada um) — prova que uma página real lê, através do
    CORS, o que a API falsa serve, e não só que não houve erro; roda `semViolacoes` e
    `semRolagemHorizontal` nos 2 temas; registra evidência. Se a página fizer
    outra chamada, a API falsa acusa — cadastre a fixture que faltar.
18. `tests/unit/kit-flag.test.tsx`: com `vi.stubEnv("NEXT_PUBLIC_KIT_VITRINE",
    "false")`, chamar `KitLayout({ children: null })` lança o erro do
    `notFound()` (mensagem/`digest` contendo `NEXT_NOT_FOUND`); com `"true"`,
    devolve os filhos.
19. `.github/workflows/ci.yml` — `node-version: "22"` em `lint-frontend` e
    `build-frontend`, e dois jobs novos:

```yaml
  test-frontend:
    name: Frontend — Testes de componente (Vitest)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: apps/web/package-lock.json
      - working-directory: apps/web
        run: npm ci
      - working-directory: apps/web
        run: npm run test

  e2e-frontend:
    name: Frontend — E2E, acessibilidade e visual (Playwright)
    runs-on: ubuntu-latest
    needs: lint-frontend
    # Mesma imagem que gera as baselines (npm run test:visual:atualizar).
    container:
      image: mcr.microsoft.com/playwright:v1.64.1-noble
      options: --user 1001
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: apps/web/package-lock.json
      - working-directory: apps/web
        run: npm ci
      - working-directory: apps/web
        run: npm run test:e2e
        env:
          CI: "true"
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: evidencias-ui
          path: apps/web/evidencias/
          retention-days: 30
      - if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: apps/web/playwright-report/
          retention-days: 14
```

20. Documentação: seção "Testes" no README do kit (onde fica cada tipo de
    teste, os comandos, como criar uma vitrine, como atualizar baselines e
    quando — só com a imagem nova revisada no PR); CLAUDE.md: linha "Testes"
    da tabela de stack (Vitest + Playwright), CI com 6 jobs, comandos
    `npm run test`, `npm run test:e2e`, `npm run test:visual:atualizar`;
    `docs/CHANGELOG.md` em `[Unreleased] › Added` (infra) e `Changed` (Node 22
    na CI e no Dockerfile).

**Escopo** — Dentro: tudo acima. Fora: testes dos demais componentes do kit
(cada tarefa traz os seus); corrigir violações de a11y das páginas existentes
(TRM-038); WebKit e Firefox; cobertura mínima obrigatória; MSW; servidor de
mock HTTP; Storybook; mudar `engines` do `package.json`.

**Critérios de aceite**

1. 001-A: `cd apps/web && npm ci && npm run test` passa com
   `tests/componentes/Selo.test.tsx` (5 testes) e `tests/unit/kit-flag.test.tsx`.
2. Remover temporariamente o `aria-hidden` do ponto do `Selo` faz o primeiro
   teste falhar (verificado localmente; dizer no PR).
3. `npx tsc --noEmit` e `npm run lint` verdes com os arquivos de teste
   incluídos; `npm run build` verde.
4. 001-B: `npm run test:e2e` passa no macOS (sem `@visual`) e roda os projetos
   `celular`, `tablet`, `desktop` e `reflow-320` (este só com `@reflow`);
   `selo.spec.ts` executa axe em 2 temas × 3 larguras = 6 vezes, sem
   violações; `focoVisivelENaoEncoberto` tem um uso no molde (link do caso
   `com-icone` da vitrine do `Selo`, que ganha um `Selo href` depois de TRM-031
   — até lá, um link qualquer da vitrine).
5. `paginas/proposicoes.spec.ts` mostra os três cartões com os números da
   fixture (a requisição cross-origin `localhost:3100` → `api.zil.test`
   passa pelo CORS da API falsa); um teste de `api.spec.ts` confere que a
   resposta tem `access-control-allow-origin: *`, que `X-Total-Count` é legível
   por `fetch` e que `OPTIONS` devolve 204. Uma chamada à API sem fixture faz o teste falhar com a rota na mensagem
   (provar com um teste temporário ou descrever no PR). `responderPaginas`
   tem teste próprio em `tests/e2e/helpers/api.spec.ts` (página 1 sem query,
   página 2, além da lista com e sem `alem`, `falharNaPagina`, `chamadas`).
6. `npm run test:visual:atualizar` gera
   `tests/e2e/__screenshots__/{celular,desktop}/kit/selo.spec.ts/selo-<caso>-<tema>.png`
   só para os casos `visual`; `npm run test:visual` passa logo depois.
7. Depois de `npm run build:e2e`, `git status` não mostra `tsconfig.json`
   alterado.
8. Com `npm run build && npm run start`, `curl -s -o /dev/null -w "%{http_code}"
   localhost:3000/kit/selo` devolve `404`.
9. Na CI, os jobs "Frontend — Testes de componente (Vitest)" e "Frontend —
   E2E, acessibilidade e visual (Playwright)" ficam verdes; o artefato
   `evidencias-ui` traz as capturas de `/kit/selo` e `/proposicoes` em 3
   larguras × 2 temas e os JSON do axe.
10. `a11y-conhecidas.ts` existe; cada entrada tem regra e motivo; se não
    estiver vazio, a TRM-038 foi aberta com a lista.
11. CLAUDE.md, README do kit e CHANGELOG atualizados.

**Specs de design** — Vitrine: layout padrão de página do README do kit; cada
caso com `<h2>` e `data-caso`; `Aviso` padrão "Exemplos de demonstração"; seletor
de tema no cabeçalho. Nada de cor nova.

**Testes** — Os próprios critérios 1–9. Comandos: `npm run test`,
`npm run test:e2e`, `npm run test:visual`, `npm run test:visual:atualizar`.

**Riscos e perguntas em aberto**
- **Fetch no servidor no futuro** (RSC buscando a API): `page.route()` não
  intercepta. Caminho: um servidor de fixtures em Node
  (`tests/e2e/servidor-api.ts`) servindo os mesmos JSON e
  `NEXT_PUBLIC_API_URL` apontando para ele. Não fazer agora.
- **Fixtures à mão divergem da API — resolvido pela Arquitetura:** TRM-028,
  critério 9, cria `scripts/gerar_fixtures_frontend.py`, que grava respostas
  reais da FastAPI (pacotes golden de TRM-002) em
  `apps/web/tests/fixtures/api/tramitacao/gerado/`, com IDs `uuid5` estáveis;
  um teste de backend falha se os arquivos versionados divergirem e valida as
  fixtures sintéticas contra os schemas Pydantic. Essa pasta é a **fonte das
  fixtures de tramitação** da TRM-001 em diante: até TRM-028 entrar, as
  tarefas usam fixtures escritas à mão em `apps/web/tests/fixtures/api/`
  (sempre o caminho completo — na raiz, `tests/fixtures/tramitacao/` é do
  Python); depois, as "reais" são trocadas pelas geradas e só as sintéticas
  continuam à mão. A fixture `proposicoes/lista.json` desta tarefa (rota
  antiga, fora de tramitação) continua à mão.
- **Node na Vercel:** o `package.json` não ganha `engines` (fora de escopo), então
  a Vercel usa a versão configurada no projeto; se for 20.x, o `npm ci` do
  build avisa (ou falha, com `engine-strict`) pelos `engines` das libs novas.
  Passo manual no checklist do PR de 001-A: conferir e ajustar "Node.js
  Version = 22.x" nas configurações do projeto na Vercel **antes do merge**
  (revisão da Arquitetura, item 16). A Arquitetura aprovou o Node 22 (item
  15): `node-version: "22"` resolve hoje para 22.23.4, que atende o `jsdom`.
- **Baselines e maintainer solo:** mudar a aparência exige rodar
  `npm run test:visual:atualizar` (Docker). Documentado no README; o PR mostra
  a imagem nova.
- `@axe-core/playwright` 4.14.0 tem 15 dias: se aparecer bug, fixar 4.13.0.
- `jest-dom` 7 é major recente: fallback 6.10.0.
- O PR #48 e as tarefas de componente vão acrescentar casos; nenhum altera
  esta infra.

**Instruções para o agente implementador** — Branches
`trm-001a-vitest` e `trm-001b-playwright` (spec §8.3, worktree própria), a
partir do `main`. Ordem: (A) dependências com versões exatas → configs →
setup e shims → `Selo.test.tsx` vendo falhar e passar → job `test-frontend` →
CLAUDE.md/CHANGELOG → PR. (B) `next.config.js`/`tsconfig.json`/`.gitignore` →
vitrine (`app/kit/**`) → helpers → `selo.spec.ts` → fixture e
`proposicoes.spec.ts` → baselines com `npm run test:visual:atualizar` → job
`e2e-frontend` → README do kit → PR. No PR de 001-A, item de checklist: "Node
22.x conferido nas configurações do projeto na Vercel". Verificação: `npm run lint && npx tsc
--noEmit && npm run test && npm run build && npm run test:e2e`. Prova no PR:
saída dos comandos, link do artefato `evidencias-ui`, uma captura de 375 px de
`/kit/selo` nos dois temas. **Não** corrija violações das páginas existentes;
**não** use `--legacy-peer-deps`; **não** gere baselines no macOS; **não**
deixe `/kit` acessível sem a flag; **não** mexa em componentes além do teste do
`Selo`.

---

### TRM-030 — `Etapas` v2 (feita/atual/futura/pulada/interrompida; Casa; vertical < md; aria; sem animação contínua)

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System (gate principal, S1–S10) + UI/UX (uso em contexto) + Maintainer (confirma D6 e vê 375 px)
**Depende de:** TRM-001 (001-B), TRM-003 (gates), D6, PR #48 (merge ou rebase) · **Desbloqueia:** TRM-034, TRM-040, TRM-046 (estados de etapa)

**Problema** — §1.2, itens 1 a 4: animação contínua contra a regra do kit
(`Tempo.tsx:62`), âmbar para "atual", rolagem de 840 px no celular
(`Tempo.tsx:56`), sem estados `pulada`/`interrompida`, sem Casa, sem texto
para leitor de tela além de `aria-current`, `key` pelo nome.

**Oportunidade** — "Onde está agora" diz numa linha em que etapa a proposição
está ("Etapa 2 de 6: Nas comissões") e "O caminho inteiro" mostra todas,
legíveis a 375 px e por leitor de tela, sem sugerir que a proposição
"pulsa" ou está atrasada.

**Solução** — Mover `Etapas` para `components/ui/Etapas.tsx`, com a API
abaixo, duas variantes (`completa` e `compacta`), os cinco estados do contrato
com o vocabulário de §1.3, orientação vertical abaixo de `md` (e sempre com
mais de 7 etapas), texto para leitor de tela e nenhuma animação.

**Escopo** — Dentro: componente, esqueleto, função `legendaDasEtapas`, classe
`.zil-tracejado`, remoção de `zil-respira` do Tailwind, vitrine, testes,
README. Fora: derivar estado das etapas (API, TRM-025/028); usar em página
(TRM-040/042); diagrama com ramos (TRM-034).

**Specs técnicas**

API (`components/ui/Etapas.tsx`, exportada em `index.ts`):

```ts
export type EstadoEtapa = "feita" | "atual" | "futura" | "pulada" | "interrompida";

export interface Etapa {
  /** Identificador estável: o `id` de `etapas[]` da API. Vira a `key`. */
  id: string;
  /** Rótulo pronto, como a API devolve ("Nas comissões", "No Senado"). */
  nome: string;
  estado: EstadoEtapa;
  /**
   * Data já formatada, de preferência <time dateTime="aaaa-mm-dd">dd/mm/aaaa</time>; só a data.
   * Em `atual` é o início da etapa (o kit escreve "Desde {quando}"); em `feita`, a conclusão;
   * em `interrompida`, quando parou. Ignorada em `futura`: o ZIL não prevê datas.
   */
  quando?: React.ReactNode;
  /** Rótulo da Casa ("Câmara", "Senado", "Presidência", "Congresso"). Visível quando muda em relação à etapa anterior. */
  casa?: string;
  /** Motivo curto, em `pulada` e `interrompida` ("Plenário dispensado: apreciação conclusiva", "Arquivada"). `etapas[].nota` da API. */
  nota?: string;
  /** Explicação da etapa ("/como-vira-lei#fase-comissoes"). */
  href?: string;
}

export interface EtapasProps {
  etapas: Etapa[];
  /** `completa` (padrão): nome, Casa e data. `compacta`: só as barras e a legenda "Etapa 2 de 6: Nas comissões". */
  variante?: "completa" | "compacta";
  /** Só na `completa`. `auto` (padrão): vertical abaixo de md e, com mais de 7 etapas, em qualquer largura; `vertical`: sempre. */
  orientacao?: "auto" | "vertical";
  /** Nome da lista para leitor de tela. Padrão: "Etapas da tramitação". */
  rotulo?: string;
  className?: string;
}

export function Etapas(props: EtapasProps): JSX.Element | null; // null com `etapas` vazio
export function EtapasEsqueleto(props: { n?: number; variante?: "completa" | "compacta"; className?: string }): JSX.Element;
/** A frase da variante compacta. Exportada para a página reusar. */
export function legendaDasEtapas(etapas: Etapa[]): string;
```

`legendaDasEtapas` (posições contam a partir de 1 e incluem as puladas; `n` =
total):

| Condição (a primeira que casar) | Texto exato |
| --- | --- |
| Há etapa `atual` na posição `i` | `Etapa ${i} de ${n}: ${nome}` |
| Há etapa `interrompida` na posição `i` | `Parou na etapa ${i} de ${n}: ${nome}` |
| Nenhuma `futura` (todas `feita` ou `pulada`); `k` = última `feita` | `Etapa ${k} de ${n}: ${nome}` |
| Outro caso | `${n} etapas; a etapa atual não foi identificada` |

Anatomia da `completa` — `<ol aria-label={rotulo}>`, sem `overflow-x`; cada
etapa um `<li data-estado={estado}>` em grade de duas colunas
(`grid-cols-[6px_minmax(0,1fr)] gap-x-3.5`) na vertical e uma coluna na
horizontal:

1. Barra (`data-barra`, `aria-hidden`): `w-1.5` e altura da linha na
   vertical; `h-1.5` e largura toda na horizontal; `rounded-pilula`,
   `overflow-hidden`, fundo do trilho, preenchimento interno conforme §1.3.
2. Nome (`text-[15px] leading-5 font-semibold`; `text-zil-texto-2` em
   `futura`): `<span className="sr-only">Etapa {i} de {n}: </span>`, quadrado
   ■ (`inline-block w-2 h-2 rounded-[2px] bg-current mr-1.5`, `aria-hidden`)
   só em `interrompida`, o nome (como `<Link>` se houver `href`, com
   `hover:underline underline-offset-4 inline-block min-h-6`) e o sufixo
   lido.
3. Casa (`text-legenda text-zil-texto-2`): visível na primeira etapa e quando
   muda; nas demais, `sr-only` (o leitor sempre ouve a Casa).
4. Meta (`text-[14px] leading-[18px] text-zil-texto-2`), conforme a tabela.

| Estado | Meta visível | Sufixo só para leitor (após o nome) |
| --- | --- | --- |
| `feita` | `quando`, senão "—" com `aria-hidden` | " (concluída)" |
| `atual` | "Desde " + `quando`; sem data, "Está aqui" com `aria-hidden` | " (etapa atual)" + `aria-current="step"` no `<li>` |
| `futura` | "—" com `aria-hidden` | " (ainda não aconteceu)" |
| `futura` depois de uma `interrompida` | "Não aconteceu" | — |
| `pulada` | "Dispensada" + (`nota` ? " · " + nota : "") | — |
| `interrompida` | "Parou aqui" + (`quando` ? " · " + quando : "") + (`nota` ? " · " + nota : "") | — |

O estado do contrato continua `pulada`; o texto visível é "Dispensada" (pedido
UX-DS-11: o caso típico é o Plenário dispensado pela apreciação conclusiva,
termo do RICD art. 24, II; "pulada" soaria como irregularidade). "Está aqui" é
o mesmo texto do selo do `RitoDiagrama` (UX-DS-31).

Preenchimento da barra: `feita` → `absolute inset-0 bg-zil-texto`; `atual` →
metade (`top-0 inset-x-0 h-1/2` na vertical; `left-0 inset-y-0 w-1/2` na
horizontal) `bg-zil-texto`; `interrompida` → metade `bg-zil-texto-2`;
`futura` → só o trilho `bg-zil-superficie-3`; `pulada` → trilho com
`zil-tracejado` (sem preenchimento). Na horizontal, a barra tracejada leva
`md:[--tracejado-angulo:90deg]`.

Orientação: escreva as classes de horizontal num mapa literal `MD` (o
Tailwind só gera classe que aparece inteira no código) e aplique-o só com
`orientacao="auto"` e `etapas.length <= 7`; com mais de 7 etapas (PEC) ou
`orientacao="vertical"`, a lista fica vertical em qualquer largura — a 1280,
10 etapas dariam ~105 px cada e "Com o Presidente da República" quebraria em
três linhas (UX-DS-30). Ex. de `MD`: `{ ol: "md:grid-flow-col
md:auto-cols-fr", li: "md:grid-cols-1 md:gap-y-2 md:content-start", barra:
"md:w-auto md:h-1.5 md:row-span-1" }`.

Anatomia da `compacta`: `<div className="grid gap-2">` com `<ol
aria-label={rotulo} className="flex gap-1.5 list-none m-0 p-0">` — um `<li>`
por etapa (`flex-1`), com a barra visível (`h-1.5 rounded-pilula`, mesmo
preenchimento) e, só para leitor, o mesmo texto da completa ("Etapa i de n:
nome (estado)", meta incluída); `aria-current="step"` na atual — e, abaixo,
`<p aria-hidden="true" className="text-texto-s
text-zil-texto-2">{legendaDasEtapas(etapas)}</p>`. A legenda visível fica
oculta do leitor porque repete o item atual da lista, que ele já ouve; assim
a compacta satisfaz U10 (`aria-current`) e o leitor tem o caminho inteiro em
"Onde está agora", sem esperar "O caminho inteiro" (TRM-042, P2). Sempre
horizontal (cabe a 375: barras sem texto).

`EtapasEsqueleto`: `aria-hidden`, `n` (padrão 6) barras `zil-esqueleto` com a
mesma grade (na completa, mais dois traços de texto por etapa).

Avisos de desenvolvimento (`process.env.NODE_ENV !== "production"`,
`console.warn` com prefixo `"[Etapas]"`): mais de uma `atual`; `atual` junto
com `interrompida`; `quando` em `futura`; `id` repetido.

`globals.css`, em `@layer components`:

```css
/* Trilho tracejado da etapa pulada (Etapas, RitoDiagrama). A direção vem de
   --tracejado-angulo: 180deg na vertical (padrão), 90deg na horizontal. */
.zil-tracejado {
  background-image: repeating-linear-gradient(var(--tracejado-angulo, 180deg), var(--superficie-4) 0 6px, transparent 6px 10px);
}
```

`tailwind.config.js`: remover o keyframe e a animação `zil-respira` (linhas
122 e 128; único uso era o `Etapas`). `Tempo.tsx`: remover `Etapas` (fica só
`LinhaDoTempo`/`Marco`). `index.ts`: `export { Etapas, EtapasEsqueleto,
legendaDasEtapas, type Etapa, type EstadoEtapa, type EtapasProps } from
"./Etapas";` e tirar `Etapas` da linha de `./Tempo`.

**Specs de design**

- Estados e textos: tabelas acima. Tokens: `texto`, `texto-2`,
  `superficie-3`, `superficie-4` (tracejado), `foco`. Nenhum
  `alinhado`/`contra`/`neutro`.
- Breakpoints: 375 → vertical, uma etapa por linha, sem rolagem lateral; 768
  e 1280 → horizontal com até 7 etapas, vertical com mais. A `compacta` é
  sempre horizontal (só barras).
- Estados de interação: não interativo, exceto o link do nome (`hover`
  sublinha; foco com o contorno global `outline-zil-foco`; alvo ≥ 24 px de
  altura). Sem desabilitado. Carregando = `EtapasEsqueleto`.
- A11y: `<ol>` com nome; `aria-current="step"`; texto "Etapa i de n" e estado
  lidos; não depende de cor (meia barra, quadrado, tracejado e texto); sem
  animação (o `prefers-reduced-motion` nada tem a cortar).
- Exemplos (vitrine `app/kit/etapas/casos.tsx`; todos marcados como
  demonstração):
  - `pl-comissoes` (`visual`, em cartão) — PL 1264/2024: Apresentada (feita,
    Câmara) · Nas comissões (atual, quando 09/05/2025 → "Desde 09/05/2025") · No Plenário da
    Câmara · No Senado (Senado) · Com o Presidente da República (Presidência)
    · Virou lei — as quatro últimas `futura`.
  - `pl-2-2024` — Apresentada 03/01/2024 · Nas comissões (`pulada`, nota
    "Pareceres dados no Plenário (urgência constitucional)") · No Plenário da Câmara 19/03/2024 · No
    Senado 30/04/2024 · Com o Presidente da República 28/05/2024 · Virou lei
    28/05/2024.
  - `pl-327-2021` — 7 etapas, com "De volta à Câmara" 18/12/2024.
  - `arquivada` (`visual`; ilustrativo, sem proposição real) — Nas comissões
    `interrompida`, quando 31/01/2023, nota "Arquivada"; quatro `futura`
    depois.
  - `pec-10-etapas` (`visual`) — Apresentada · CCJC (admissibilidade) ·
    Comissão especial (atual) · Plenário da Câmara, 1º turno · 2º turno · CCJ
    do Senado · Plenário do Senado, 1º turno · 2º turno · Promulgação · Virou
    emenda constitucional.
  - `compacta` (`visual`) — os casos `pl-comissoes`, `pl-2-2024` e
    `arquivada` na variante compacta.
  - `com-links`, `vertical-fixa` (`orientacao="vertical"`), `esqueleto`.

**Critérios de aceite**

1. Dado `pl-comissoes`, a 375 px cada `[data-barra]` é mais alta que larga e
   a página não rola para o lado; a 768 e 1280, mais larga que alta.
2. Dado `pec-10-etapas`, vertical a 375, 768 e 1280.
3. O `<li>` da etapa atual tem `aria-current="step"` e texto (espaços
   normalizados) começando por "Etapa 2 de 6: Nas comissões (etapa atual)".
4. `pulada` mostra "Dispensada · Pareceres dados no Plenário (urgência
   constitucional)"; `atual` com data mostra "Desde 09/05/2025"; `interrompida`
   mostra "Parou aqui · 31/01/2023 · Arquivada"; as `futura` seguintes mostram
   "Não aconteceu".
5. `legendaDasEtapas` devolve exatamente os quatro textos da tabela nos
   casos `pl-comissoes`, `arquivada`, `pl-2-2024` e numa lista só de
   `futura`; na `compacta`, a legenda visível tem `aria-hidden` e a `<ol>`
   tem nome, um `<li>` por etapa e `aria-current="step"` na atual.
6. Com movimento "no-preference", `animacoesInfinitas` na vitrine (fora do
   caso `esqueleto`) é 0; `grep -rn "zil-respira" apps/web` não acha nada.
7. `classesDeAlinhamento` vazio em todos os casos; `expectPaletaNeutra`
   passa nos dois temas.
8. axe: 0 violações em 3 larguras × 2 temas; Vitest + jest-axe: 0 por caso.
9. Etapas com o mesmo `nome` e `id` diferentes não geram aviso de `key`.
10. README do kit com a seção "Etapas" e a linha na tabela.

**Testes**

- `tests/componentes/Etapas.test.tsx`: lista com nome; um `<li>` por etapa;
  `aria-current` só na atual; sufixos lidos por estado; meta por estado
  (incluindo "Não aconteceu"); Casa visível só na mudança e `sr-only` nas
  demais; link quando há `href`; `quando` ignorado em `futura` + aviso;
  avisos de duas `atual`, `atual`+`interrompida` e `id` repetido
  (`vi.spyOn(console, "warn")`); nenhuma classe `animate-`; preenchimento
  por estado (`data-barra` > filho com `h-1/2` na atual); `legendaDasEtapas`
  nos quatro ramos; `null` com lista vazia; `EtapasEsqueleto` `aria-hidden`
  com `n` barras; `classesDeAlinhamento` vazio; `axe` sem violação em cada
  caso de `casos.tsx`.
- `tests/e2e/kit/etapas.spec.ts`: o molde de TRM-001 (axe, rolagem,
  evidência, `@visual`) + orientação por largura (critérios 1–2) + movimento
  (critério 6) + `expectPaletaNeutra` + foco visível no link do caso
  `com-links` (`outline-style` computado `solid`, altura ≥ 24 px).
- Comandos: `npm run test -- Etapas`, `npm run test:e2e -- kit/etapas`,
  `npm run test:visual:atualizar` (baseline nova).

**Riscos e perguntas em aberto**
- Contrato: `etapas[].nota` está em backlog-dados.md §1.5 (pulada →
  `nota_pulada` do rito; interrompida → rótulo do desfecho). Sem ela,
  `pulada`/`interrompida` mostram só "Dispensada"/"Parou aqui". Pedido à
  Arquitetura (UX-DS-12): documentar em `EtapaRead.quando` que é o início da
  etapa quando `atual` e a conclusão quando `feita`.
- Se a maintainer quiser algum movimento (D6 recomenda tirar): no máximo a
  barra crescer uma vez ao montar (420 ms, `ease-padrao`), nunca em loop.
- A matriz de TRM-046 (E01) ainda lista "Pulada" e "Agora"; a UI/UX atualiza
  para "Dispensada" e "Está aqui" (pedidos dela, UX-DS-11 e 31).

**Instruções para o agente implementador** — Branch `trm-030-etapas-v2`.
Repita o grep de §1.5 antes de começar. Ordem: testes de `legendaDasEtapas` e
do componente (falhando) → `Etapas.tsx` → `globals.css`/`tailwind.config.js`
→ remover de `Tempo.tsx` → `index.ts` → vitrine (`app/kit/etapas/page.tsx` +
`casos.tsx`; linha em `app/kit/page.tsx`) → e2e → baselines → README (seção
"Etapas" e linha "Cronologia"/"Etapas") → CHANGELOG (`Changed`). Verificação:
`npm run lint && npx tsc --noEmit && npm run test && npm run build && npm run
test:e2e`. Prova: capturas de `/kit/etapas` em 375/768/1280 × 2 temas
(artefato `evidencias-ui`). Não use `neutro` nem animação; não use Etapas em
página; não calcule estado no componente.

---

### TRM-031 — `FaseSelo` + tratamento de desfecho (paleta neutra)

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M (o índice do PM diz P; a tarefa inclui `Selo`, três ícones e `lib/tramitacao/tipos.ts`. Pode sair em dois PRs: **031-A** `tipos.ts` — P, destrava 034-B e 035; **031-B** o resto)
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System + UI/UX + Maintainer (rótulos D1 vêm da API; aqui só a forma)
**Depende de:** TRM-001, TRM-003 · **Desbloqueia:** TRM-034 (glifos), TRM-035 (tipos), TRM-040, TRM-043, TRM-045, TRM-046

**Problema** — Não há como mostrar fase. A página e a lista põem a situação
oficial crua num `Selo` cinza truncado (`app/proposicoes/[id]/page.tsx:148`,
`app/proposicoes/page.tsx:215`, `Selo.tsx:39`). Os tons do `Selo` com cor
(`alinhado`, `contra`, `neutro`) são exatamente os que fase não pode usar, e
a spec 012 chegou a propor verde para aprovada (disc. §1.6).

**Oportunidade** — Um selo curto ("Nas comissões", "Virou lei",
"Arquivada"), igual em toda superfície, que diz a fase sem julgar, liga para
a explicação e nunca trunca.

**Solução** — Estender o `Selo` (tom `elevado`, `quebrar`, `href`), acrescentar
três glifos ao `Icone`, criar `FaseSelo` e `FaseSeloEsqueleto` e o arquivo de
tipos do contrato.

**Escopo** — Dentro: `Selo`, `Icone`, `FaseSelo`, `lib/tramitacao/tipos.ts`,
vitrines `selo` (casos novos) e `fase-selo`, testes, README. Fora: rótulos
(vêm da API, D1/TRM-029 L1); tirar a situação oficial do Selo nas páginas
(TRM-015/016); filtro de fase (TRM-043); `Aviso` de "mapa em revisão"
(TRM-046).

**Specs técnicas**

`Selo.tsx` (só aditivo):

```ts
export type TomSelo = "padrao" | "alinhado" | "contra" | "neutro" | "forte" | "elevado";
// TOM.elevado = "bg-zil-superficie-3 text-zil-texto" — terminal neutro (norma, desfecho)

interface SeloBase {
  tom?: TomSelo;
  ponto?: boolean;
  icone?: React.ReactNode;
  title?: string;
  /** Quebra linha em vez de truncar: altura mínima 26px, cresce com o texto. Sem `title` automático. */
  quebrar?: boolean;
  className?: string;
  children: React.ReactNode;
}
type SeloEstatico = SeloBase & { href?: never };
/** Selo que é link: hover um degrau acima, chevron de 12px no fim. Use só com `padrao`, `elevado` ou `forte`. */
type SeloLink = SeloBase & { href: string; /** Texto só para leitor, no fim do link (ex.: ", entenda esta fase"). */ rotuloLink?: string };
export function Selo(props: SeloEstatico | SeloLink): JSX.Element;
```

- `quebrar`: troca `h-[26px]` por `min-h-[26px] py-[5px]`, `leading-none` por
  `leading-4`, e o `<span className="truncate">` por `<span
  className="whitespace-normal break-words">`; não aplica `title` automático.
- `href`: renderiza `next/link` com as mesmas classes + `no-underline
  transition-colors duration-toque` + hover por tom (`padrao` →
  `hover:bg-zil-superficie-3`, `elevado` → `hover:bg-zil-superficie-4`,
  `forte` → `hover:bg-zil-inverso-hover`) e `<Icone nome="chevron-direita"
  className="!w-3 !h-3" />` no fim.
- Comportamento padrão (sem as props novas) **idêntico** ao de hoje.

`Icone.tsx` — três nomes novos no tipo `NomeIcone` e em `CAMINHOS`:

```tsx
parada: <rect x="7" y="7" width="10" height="10" rx="2" />,
duvida: (<><circle cx="12" cy="12" r="9" /><path d="M9.6 9.3a2.5 2.5 0 1 1 3.4 2.4c-.6.3-1 .8-1 1.5v.5M12 16.8h.01" /></>),
conjunto: (<><rect x="8" y="8" width="12" height="12" rx="2" /><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" /></>),
```

`FaseSelo.tsx`:

```ts
export type Fase = "apresentada" | "comissoes" | "plenario" | "outra_casa" | "retorno" | "sancao" | "veto_congresso" | "promulgacao" | "norma";
export type Desfecho = "arquivada" | "retirada" | "prejudicada" | "rejeitada" | "perdeu_eficacia" | "vetada" | "devolvida";
export type MotivoNaoSabemos = "situacao_sem_mapa" | "sinais_conflitantes" | "principal_nao_resolvida" | "fonte_indisponivel" | "especie_fora_do_escopo" | "mapa_nao_aprovado" | "recem_apresentada";

export interface FaseSeloProps {
  /**
   * `onde_esta.fase` da API; "nao_sabemos" quando a derivação não concluiu.
   * Nula só com `desfecho` preenchido e "onde parou" desconhecido (ex.: apensada
   * prejudicada; backlog-dados.md §7-3).
   */
  fase: Fase | "nao_sabemos" | null;
  /** `onde_esta.desfecho`. Com valor, o selo é terminal (tem precedência sobre `fase`). */
  desfecho?: Desfecho | null;
  /**
   * O texto do selo, exatamente `fase_rotulo` da API ("Nas comissões", "Arquivada",
   * "Recém-apresentada", "Fase não identificada"). Nunca nulo depois que a fase foi
   * calculada (backlog-dados.md §1.5); nunca montado no front.
   */
  rotulo: string;
  /** `fase_motivo`. Não muda a aparência — todo motivo é neutro; vai em `data-motivo`. */
  motivo?: MotivoNaoSabemos | null;
  /** Tramita em conjunto (fase herdada da principal): acrescenta o selo "Em conjunto". */
  apensada?: boolean;
  /** Explicação da fase ("/como-vira-lei#fase-comissoes"). Nunca dentro de `Card` com `href`. */
  href?: string;
  /** `id` da raiz, para o cartão-link da lista citar o selo em `aria-describedby` (TRM-043). */
  id?: string;
  className?: string;
}
export function FaseSelo(props: FaseSeloProps): JSX.Element | null;
export function FaseSeloEsqueleto(props: { className?: string }): JSX.Element; // Esqueleto h-[26px] w-32 rounded-pilula
```

Regra de aparência (a primeira que casar):

| Caso | Condição | `Selo` | Marca | Prefixo só para leitor | Sufixo do link (com `href`) |
| --- | --- | --- | --- | --- | --- |
| Desfecho | `desfecho` preenchido (com `fase` preenchida **ou nula**) | `tom="elevado"` | `Icone parada` | "Desfecho: " | ", entenda este desfecho" |
| Virou norma | `fase === "norma"` | `tom="elevado"` | `Icone documento` | "Fase: " | ", entenda esta fase" |
| Não sabemos | `fase === "nao_sabemos"` (qualquer `motivo`, inclusive `mapa_nao_aprovado`) | `tom="padrao"` | `Icone duvida` | — | ", entenda por quê" |
| Em andamento | demais (inclusive `apresentada` com `motivo="recem_apresentada"`, que é fase conhecida — backlog-dados.md §7-4) | `tom="padrao"` | `ponto` | "Fase: " | ", entenda esta fase" |
| Inválido | `fase === null` sem `desfecho` (fase não calculada) | — | — | — | — |

No caso inválido o componente devolve `null` e, fora de produção, avisa
(`console.warn("[FaseSelo] fase nula sem desfecho")`): a página não deve
renderizar selo quando a fase não foi calculada (`fase_rotulo` nulo em
`ProposicaoRead`).

Sempre `quebrar`. Raiz: `<span className="inline-flex flex-wrap items-center
gap-1.5 max-w-full" data-fase={fase ?? undefined} data-desfecho={desfecho ??
undefined} data-motivo={motivo ?? undefined}>`. Com `apensada`, segundo selo:
`<Selo icone={<Icone nome="conjunto" tamanho="s" />} quebrar><span
aria-hidden="true">Em conjunto</span><span className="sr-only">Tramita em
conjunto com a proposição principal</span></Selo>`.

`lib/tramitacao/tipos.ts` (031-A) — espelho em TypeScript dos contratos
Pydantic de backlog-dados.md §1.5, com os nomes finais de §7 (fonte única:
se o PR de TRM-028 mudar um campo, ajusta este arquivo no mesmo PR). Datas
(`date`) chegam como `"aaaa-mm-dd"`; `datetime` como ISO com `-03:00`
(pedido 3 da UI/UX à Arquitetura). Reusa os enums do kit:

```ts
import type { Desfecho, EstadoEtapa, Fase, MotivoNaoSabemos } from "@/components/ui";
export type { Desfecho, EstadoEtapa, Fase, MotivoNaoSabemos };

export type FaseOuNaoSabemos = Fase | "nao_sabemos";
export type Casa = "camara" | "senado";
export type CasaRito = Casa | "congresso" | "presidencia";
export type Especie = "PL" | "PLP" | "PEC" | "MPV" | "PDL";
export type ClassePrazo = "D" | "D*" | "X";
export type StatusRevisao = "rascunho" | "revisado_agentes" | "aprovado";
export type SituacaoEstado = "informada" | "recem_apresentada" | "sem_situacao" | "nao_sincronizada";

export const CASA_ROTULO: Record<CasaRito, string> = { camara: "Câmara", senado: "Senado", congresso: "Congresso", presidencia: "Presidência" };
export const FASES: readonly Fase[] = ["apresentada", "comissoes", "plenario", "outra_casa", "retorno", "sancao", "veto_congresso", "promulgacao", "norma"];
export const DESFECHOS: readonly Desfecho[] = ["arquivada", "retirada", "prejudicada", "rejeitada", "perdeu_eficacia", "vetada", "devolvida"];

// GET /proposicoes/{id}/tramitacao
export interface FonteApi { rotulo: string; url: string | null }
export interface ComoSabemosApi {
  regra: string;                       // "R0"…"R10"
  regra_descricao: string | null;
  versao_publicada: number | null;
  fontes: FonteApi[];
  conferido_em: string | null;         // datetime
}
/** `acompanhada`: a principal está nas pautas do ZIL (aviso A01, link interno) ou é só cabeça de contexto (A02, link para a Câmara). */
export interface HerdadaDeApi { id: string | null; fonte_id: string; rotulo: string; url_camara: string | null; acompanhada: boolean }
export interface RelatorApi { nome: string; partido: string | null; uf: string | null; parlamentar_id: string | null }
export interface OndeEstaApi {
  fase: FaseOuNaoSabemos | null;       // nula SÓ com desfecho e "onde parou" desconhecido
  fase_rotulo: string;                 // nunca nulo; "Fase não identificada" em nao_sabemos
  fase_motivo: MotivoNaoSabemos | null;
  desfecho: Desfecho | null;
  desfecho_rotulo: string | null;
  apensada: boolean;
  herdada_de: HerdadaDeApi | null;
  casa: Casa | null;
  sigla_orgao: string | null;
  orgao_nome: string | null;
  desde: string | null;                // date
  orgao_desde: string | null;          // date
  situacao_oficial: string | null;
  situacao_glossario: string | null;   // chave do glossário da situação oficial (nunca casar por texto)
  regime_texto: string | null;
  apreciacao_texto: string | null;
  relator: RelatorApi | null;
  frase: string | null;                // nula em nao_sabemos
  como_sabemos: ComoSabemosApi;
}
export interface EtapaApi { id: string; nome: string; fase: Fase; estado: EstadoEtapa; quando: string | null; casa: CasaRito | null; nota: string | null }
export interface MarcoApi { quando: string | null; titulo: string; marco: string; casa: Casa; sigla_orgao: string | null; url: string | null; votacao_id: string | null }
export interface RitoRefApi { chave: string; especie: Especie; casa_iniciadora: CasaRito }
export interface TramitacaoApi {
  onde_esta: OndeEstaApi;
  etapas: EtapaApi[];                  // [] em nao_sabemos, com fase nula ou rito não publicável
  marcos: MarcoApi[];
  eventos_total: number;
  rito: RitoRefApi | null;
}

// GET /proposicoes/{id}/tramitacao/eventos?page=&per_page=
export interface EventoApi { casa: Casa; sequencia: number | null; data_hora: string | null; sigla_orgao: string | null; descricao: string | null; despacho: string | null; url: string | null; marco: string | null }
export interface EventosPaginaApi { items: EventoApi[]; total: number; page: number; per_page: number; pages: number }

// GET /tramitacao/mapa
export interface BaseLegalApi { rotulo: string; url: string | null; norma: string; dispositivo: string }
export interface PrazoApi { classe: ClassePrazo; texto: string }
export interface FaseDefApi { chave: Fase; ordem: number; publicavel: boolean; rotulo: string | null; pergunta: string | null }
export interface DesfechoDefApi { chave: Desfecho; publicavel: boolean; rotulo: string | null; base_legal: BaseLegalApi[] } // sem `reversivel` (RICD art. 105 § 1º revogado)
export interface RitoEtapaApi { id: string; fase: Fase; nome: string; casa: CasaRito | null; o_que_acontece: string; quem_decide: string | null; prazo: PrazoApi | null; base_legal: BaseLegalApi[]; opcional: boolean; condicao: string | null }
export interface RitoDesfechoApi { desfecho: Desfecho; rotulo: string; texto: string; base_legal: BaseLegalApi[]; a_partir_de: string[] | "qualquer" }
export interface RitoApi { chave: string; casa_iniciadora: CasaRito; publicavel: boolean; revisao: StatusRevisao; nome: string | null; etapas: RitoEtapaApi[]; desfechos: RitoDesfechoApi[] }
export interface EspecieApi { sigla: Especie; nome: string; descricao: string | null; ritos: RitoApi[] }
export interface GlossarioApi {
  chave: string;                       // snake_case
  tipo: "situacao" | "regime" | "apreciacao" | "fase" | "desfecho" | "apensada" | "etapa" | "especie" | "conceito";
  termo: string; codigo: string | null; codigos: { casa: string; cod: string }[];
  fase: Fase | null; revisao: StatusRevisao; publicavel: boolean;
  texto_curto: string | null;          // ≤ 160; nulo se não publicável
  texto: string | null;                // ≤ 900; nulo se não publicável
  base_legal: BaseLegalApi[];
}
/** Tabela de situações da Câmara (TRM-020): `glossario` = chave da entrada, se houver; `tratada` = está no mapa. */
export interface SituacaoCamaraApi { codigo: string; descricao: string; glossario: string | null; tratada: boolean }
export interface MapaApi { versao_publicada: number; publicada_em: string | null; aviso: string; fases: FaseDefApi[]; desfechos: DesfechoDefApi[]; especies: EspecieApi[]; glossario: GlossarioApi[]; situacoes_camara: SituacaoCamaraApi[] }
// Em `lib/api.ts` (`Proposicao`, campos opcionais — arquivo da UI/UX, TRM-015/046-A): `orgao_efetivo_sigla`,
// `orgao_efetivo_nome`, `principal_url_camara`, `situacao_glossario` (backlog-dados §1.5, revisão da Arquitetura, item 6).
```

**Specs de design**

- Tokens: `superficie-2`/`texto-2` (padrão), `superficie-3`/`texto`
  (elevado), `superficie-3`/`superficie-4` no hover do link. Contraste:
  `texto-2`/`superficie-2` 5,9 e 5,8; `texto`/`superficie-3` 11,9 e 14,4.
- Nenhum matiz em caso algum — inclusive `mapa_nao_aprovado` (não é âmbar: o
  aviso de "em revisão", se a UI/UX quiser, é um `Aviso` de página, TRM-046) e
  `recem_apresentada` (é fase em andamento, com o rótulo que a API mandar).
- Estados: padrão; hover e foco só com `href` (contorno global; alvo de 26 px
  ≥ 24); sem desabilitado; carregando = `FaseSeloEsqueleto`.
- Responsivo: quebra linha a 375 ("Com o Presidente da República", "Veto em
  análise no Congresso"); o selo de apensada desce para a linha de baixo se
  não couber.
- A11y: o texto do selo é o nome; prefixo dá contexto fora do cabeçalho;
  glifos `aria-hidden`; link com sufixo que diz o destino.
- Exemplos (vitrine `app/kit/fase-selo`; rótulos de exemplo do disc. §4.1 e
  da recomendação D1 — os reais vêm da API): as 9 fases (`visual` em grade),
  os 7 desfechos (`visual`), `nao_sabemos` com `mapa_nao_aprovado` e com
  `situacao_sem_mapa` (rótulo "Fase não identificada"), `apresentada` com
  `recem_apresentada` (rótulo "Recém-apresentada"), desfecho com `fase={null}`
  (apensada prejudicada: `desfecho="prejudicada"`, rótulo "Prejudicada",
  `apensada`), apensada, com `href`, rótulos longos num cartão de 343 px
  (`visual`), esqueleto.
  Uso:

```tsx
// A página não monta o href à mão (`#fase-${fase}` daria "#fase-null" e "#fase-nao_sabemos"): usa
// faseSeloPropsDe (UI/UX, TRM-046-B), que testa o desfecho antes da fase e devolve
// desfecho → "/como-vira-lei?especie=…&casa=…#desfechos"; fase → "/como-vira-lei?especie={tipo}&casa={casa_iniciadora}#fase-{fase}";
// nao_sabemos → "/metodologia#tramitacao" (decisão da UI/UX: link só no cabeçalho; o kit lê o sufixo
// ", entenda por quê"); e null quando não há selo.
const selo = faseSeloPropsDe(proposicao);           // cabeçalho da proposição: com link
{selo && <FaseSelo {...selo} />}
// No cartão-link da lista, nunca link, em nenhum estado (nao_sabemos incluído):
// faseSeloPropsDe(p, { comLink: false }) e `id` para o aria-describedby.
```

- **Não faz:** não traduz código em rótulo; não mostra data, órgão nem
  situação oficial; não decide se a proposição está apensada.

**Critérios de aceite**

1. Para cada uma das 9 fases, 7 desfechos e `nao_sabemos`, o selo mostra
   `rotulo` sem alteração e a marca da tabela.
2. Nenhum caso tem classe `alinhado`/`contra`/`neutro` — verificado também
   para `motivo` = `mapa_nao_aprovado` e `fase="apresentada"` com `motivo` =
   `recem_apresentada` (pedido do PM).
3. Leitor ouve "Fase: Nas comissões", "Desfecho: Arquivada"; com `href`, o
   nome do link termina em ", entenda esta fase".
4. `apensada` acrescenta o selo "Em conjunto", lido como "Tramita em conjunto
   com a proposição principal".
5. A 375, "Veto em análise no Congresso" num cartão de 343 px quebra linha sem
   cortar e sem rolagem lateral.
6. `Selo` sem props novas tem exatamente as mesmas classes de antes (teste
   fixa a lista); `quebrar` remove `truncate` e o `title` automático.
7. axe 0 em 3 larguras × 2 temas; jest-axe 0 por caso.
8. `lib/tramitacao/tipos.ts` compila (`tsc`) e `FASES`/`DESFECHOS` têm 9 e 7
   itens.
9. `fase={null}` com `desfecho="prejudicada"` e `rotulo="Prejudicada"` mostra
   o selo de desfecho; `fase={null}` sem desfecho não renderiza nada e avisa
   fora de produção.

**Testes** — `tests/componentes/Selo.test.tsx` (ampliar: `elevado`,
`quebrar`, `href` com chevron e hover, classes padrão inalteradas);
`tests/componentes/FaseSelo.test.tsx` (tabela de casos com `it.each`,
prefixos, sufixos, `data-*`, apensada, `classesDeAlinhamento` vazio, axe; caso
fixo: `fase="nao_sabemos"` com `href="/metodologia#tramitacao"` → link cujo
nome é "Fase não identificada, entenda por quê"; o mesmo sem `href` → nenhum
link, como no cartão da lista);
`tests/componentes/Icone.test.tsx` (os três nomes novos renderizam `svg`
`aria-hidden`); `tests/unit/tramitacao-tipos.test.ts` (tamanhos de `FASES` e
`DESFECHOS`, `CASA_ROTULO`); `tests/e2e/kit/fase-selo.spec.ts` (molde +
`expectPaletaNeutra` + quebra a 375 + foco no selo-link; a vitrine tem o caso
`nao-sabemos-cabecalho` — com `href="/metodologia#tramitacao"` — e
`nao-sabemos-cartao` — dentro de `Card href`, sem link —, e o teste afirma 1
link no primeiro e nenhum no segundo além do próprio cartão).

**Riscos e perguntas em aberto** — Resolvidos pela Arquitetura
(backlog-dados.md §1.5 e §7): `fase_rotulo` nunca nulo, com precedência
desfecho → "Fase não identificada" → recém-apresentada → rótulo da fase;
`recem_apresentada` é sempre `apresentada` + `fase_motivo`; `fase` nula só com
desfecho. A UI/UX decidiu não renderizar o selo em `mapa_nao_aprovado`
(estado `N06` da matriz); o componente continua suportando o caso, neutro.
Rótulos têm no máximo 32 caracteres (validador de TRM-024), o que cabe em uma
ou duas linhas a 375 px.

**Instruções para o agente implementador** — Branches `trm-031a-tipos` e
`trm-031b-fase-selo`. Ordem (B): testes do `Selo` atual fixando classes →
props novas → ícones → `FaseSelo` com testes → vitrines → e2e/baselines →
README (linhas "Status" e "Fase", seção "FaseSelo") → CHANGELOG.
Verificação: `npm run lint && npx tsc --noEmit && npm run test && npm run build
&& npm run test:e2e`. Não troque nenhum uso existente de `Selo`; não invente
rótulo; não use `neutro` para `nao_sabemos`.

---

### TRM-032 — `LinhaDoTempo`/`Marco` v2 (Casa, órgão, documento, marco de votação, "todos os registros" recolhível)

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System + UI/UX + Maintainer
**Depende de:** TRM-001, TRM-003, **TRM-037** (`Recolhivel`: o `summary` de "Todos os registros" usa o mesmo visual); TRM-031-A só para os adaptadores de `lib/tramitacao/eventos.ts` · **Desbloqueia:** TRM-041, TRM-046

**Problema** — `Marco` pinta o marcador pelo voto (`Tempo.tsx:17`, tom
`alinhado`/`contra`), o que na tramitação leria "aprovado = verde"; o hover
em todo item (`Tempo.tsx:32`) promete clique que não existe; o trilho depende
de `ultimo` manual (`:33`); não há onde pôr Casa e órgão, link de votação,
documento oficial nem "o marco mais recente". Não existe "todos os
registros" (disc. §6.1 item 5: até 8 marcos + um `<details>` com todos, no
texto original — o PL 2/2024 tem 51).

**Oportunidade** — "O que aconteceu" em linguagem simples, com cada votação
levando à página da votação e a íntegra oficial a um toque, sem despejar 51
linhas de jargão na primeira leitura.

**Solução** — `Marco` v2 com marcador neutro de §1.3, `local`, `atual`,
`tipo`, `href` (link esticado), `documento`; trilho por CSS; `LinhaDoTempo`
aceita props de `<ol>`; novo `TodosOsRegistros` (cliente), recolhível e
carregado sob demanda.

**Escopo** — Dentro: `Tempo.tsx`, `TodosOsRegistros.tsx`, vitrine, testes,
README. Fora: escolher quais marcos mostrar (API, TRM-026/028); buscar
`/tramitacao/eventos` (página, TRM-041); paginação (usa `Paginacao`).

**Specs técnicas**

```ts
export type TomMarco = "padrao" | "alinhado" | "contra";

export function LinhaDoTempo(props: React.ComponentPropsWithoutRef<"ol">): JSX.Element;
// <ol className="grid gap-1 list-none m-0 p-0 …">; passe aria-label ou aria-labelledby (ex.: o id do título da seção).

export interface MarcoProps {
  /** Data já formatada (<time dateTime>). */
  quando: React.ReactNode;
  /** Em linguagem simples ("Aprovado no Plenário da Câmara (314 × 96)"). */
  titulo: React.ReactNode;
  /** Onde: "Câmara · CME". Vai na linha da data. */
  local?: React.ReactNode;
  /** O marco mais recente: marcador cheio com anel. Os demais: ponto cheio menor em texto-2. */
  atual?: boolean;
  /** `votacao`: ícone de placar antes do título e "Votação: " para o leitor. */
  tipo?: "evento" | "votacao";
  /** Link interno do título ("/votacoes/{id}"); o item inteiro fica clicável (link esticado) e ganha hover. */
  href?: string;
  /** Documento oficial (despacho, parecer, lei): link externo na linha de detalhes. */
  documento?: { rotulo: string; url: string };
  /** Só para alinhamento do voto de um parlamentar com a posição ZIL. Na tramitação, sempre "padrao". */
  tom?: TomMarco;
  /** @deprecated O trilho some sozinho no último item. Aceito e ignorado. */
  ultimo?: boolean;
  children?: React.ReactNode;
}
export function Marco(props: MarcoProps): JSX.Element;
export function MarcoEsqueleto(): JSX.Element;
```

- `<li className="group/marco relative grid grid-cols-[24px_minmax(0,1fr)]
  gap-3.5 py-3 pl-2 pr-3 rounded-2xl">`; com `href`: `transition-colors
  duration-toque hover:bg-zil-superficie-2` — um degrau visível tanto sobre
  `fundo` quanto dentro de `Card` (`superficie-1`). O ZIL Interface diz
  `superficie-1`, que some dentro de cartão; a mudança entra na proposta de
  TRM-036.
- Trilho: `<span aria-hidden className="absolute left-[19px] top-[34px]
  -bottom-3.5 w-0.5 rounded-sm bg-zil-separador group-last/marco:hidden" />`.
- Marcador: círculo 24 px `bg-zil-superficie-3`, com dentro: `tom` ≠
  `padrao` → ponto 10 px na cor do tom (uso legado); `atual` → ponto 10 px
  `bg-zil-texto` e anel `shadow-[0_0_0_2px_var(--texto)]` no círculo; senão →
  ponto 8 px `bg-zil-texto-2`. Atributo `data-marcador="atual|passado|tom"`.
- Linha 1 (`text-legenda text-zil-texto-2`): `quando` + (`local` ? " · " +
  local : "").
- Título (`mt-0.5 text-[17px] leading-6 font-semibold`): com `tipo="votacao"`,
  `<Icone nome="placar" tamanho="s" />` antes e `<span className="sr-only">Votação:
  </span>`; com `href`, `<Link className="after:absolute after:inset-0
  after:rounded-2xl">`; com `atual`, `<span className="sr-only"> (mais
  recente)</span>` no fim.
- Detalhes (`mt-1.5 flex flex-wrap items-center gap-2 text-texto-s
  text-zil-texto-2`): `children` e o `documento` como `<a href target="_blank"
  rel="noopener noreferrer" className="relative z-[1] inline-flex items-center
  gap-1 min-h-6 hover:text-zil-texto">{rotulo}<Icone nome="externo"
  tamanho="s" /><span className="sr-only"> (abre em nova aba)</span></a>`.

`TodosOsRegistros.tsx` (`"use client"`):

```ts
export interface Registro {
  id: string;
  /** Só a data ("19/03/2024", em <time dateTime>). Nunca a hora: a Câmara usa 00:00 como valor vazio (UX-DS-02). */
  quando: React.ReactNode;
  /** Sigla do órgão ("PLEN", "CFT"). */
  local?: React.ReactNode;
  /** `descricaoTramitacao`, no texto original. */
  titulo: string;
  /** `despacho`, no texto original; pode ser longo. */
  texto?: string | null;
  url?: string | null;
}
export interface TodosOsRegistrosProps {
  /** `eventos_total`. Com 0, não renderiza nada. */
  total: number;
  estado: "ocioso" | "carregando" | "pronto" | "erro";
  registros?: Registro[];
  /**
   * Chamado na primeira abertura (a página busca /proposicoes/{id}/tramitacao/eventos) e de
   * novo na próxima abertura depois de um `erro` — o erro sempre tem saída (UX-DS-01).
   */
  onAbrir?: () => void;
  /** Com ela, o erro padrão ganha a ação "Tentar de novo" (`Button variante="secundario" tamanho="s"`). */
  onTentarDeNovo?: () => void;
  /** Conteúdo do erro. Padrão: Aviso tom="padrao" (falha parcial) com o texto abaixo. */
  erro?: React.ReactNode;
  /** `Paginacao`, quando a API paginar. */
  rodape?: React.ReactNode;
  /** Padrão: "No texto original da Câmara dos Deputados". */
  fonte?: React.ReactNode;
  /**
   * Quando `registros` muda com o recolhível aberto e não é a primeira carga (troca de
   * página), leva o foco ao primeiro registro (`tabIndex={-1}`). Padrão true.
   */
  focarAoTrocar?: boolean;
}
```

- `<details className="group">` com `onToggle` (chama `onAbrir` na primeira
  abertura, via `useRef`; o `useRef` volta a falso quando `estado` vira
  `erro`, para a próxima abertura buscar de novo) e `SumarioRecolhivel` no
  visual `linha` (TRM-037), com `id`: título `total === 1 ? "1 registro" :
  `Todos os ${total} registros``, sub = `fonte`.
- Conteúdo: `<p role="status" className="sr-only">` com "Carregando os
  registros." (carregando), `${registros.length} registros carregados.`
  (pronto) ou vazio; `carregando` → três esqueletos de linha e `aria-busy` na
  lista; `pronto` → `<ol aria-labelledby={idDoSummary} className="grid gap-1
  list-none m-0 p-0 mt-2">` (UX-DS-35), cada
  `<li className="grid gap-0.5 px-3 py-2.5 rounded-m">`: linha 1
  `text-legenda text-zil-texto-2` (`quando` · `local`), título
  `text-[16px] leading-[22px] font-medium`, texto `text-texto-s
  text-zil-texto-2 whitespace-pre-line break-words`, link "Documento" (mesmo
  padrão de `documento` do `Marco`); a partir de `md`, o `<li>` vira
  `md:grid-cols-[7rem_minmax(0,1fr)] md:gap-x-4`, com a data na primeira
  coluna (pedido da UI/UX, TRM-041); `erro` → `erro` ou `<Aviso tom="padrao"
  titulo="Não conseguimos carregar os registros." acao={onTentarDeNovo &&
  <Button variante="secundario" tamanho="s" onClick={onTentarDeNovo}>Tentar de
  novo</Button>}>Os marcos acima continuam valendo.</Aviso>` — `padrao`, não
  `contra`: é falha parcial (os marcos seguem na tela), a regra da UI/UX
  (interface §0.5-2), e o `expectPaletaNeutra` da seção continua valendo;
  depois, `rodape`.

Adaptadores `lib/tramitacao/eventos.ts` (dependem de 031-A; contratos de
backlog-dados.md §1.5):

```ts
/** EventoApi → Registro. id = `${casa}-${sequencia ?? indice}`; quando = dataBR(data_hora) — só a data —, ou
 *  "Sem data" se nula; local = sigla_orgao; titulo = descricao ?? "Registro sem descrição"; texto = despacho;
 *  url. Ordem preservada (a API manda do mais recente para o mais antigo). */
export function registroDoEvento(e: EventoApi, indice: number): Registro;
/** MarcoApi → props de Marco, sem `tom`. quando = dataBR ou "Sem data"; local = `${CASA_ROTULO[casa]} · ${sigla_orgao}`
 *  (só a Casa se a sigla for nula); tipo = votacao_id ? "votacao" : "evento"; href = `/votacoes/${votacao_id}`;
 *  documento = url ? { rotulo: "Documento", url } : undefined; atual = é o último do array. */
export function marcoDaApi(m: MarcoApi, indice: number, total: number): MarcoProps;
```

**Specs de design**

- Tokens: `texto`, `texto-2`, `superficie-1…3`, `separador`. Nada de cor de
  alinhamento na tramitação (o `tom` existe só para o uso legado e o README
  diz isso em negrito).
- Estados: `Marco` estático (sem hover), interativo (hover + foco no título),
  atual; `TodosOsRegistros` fechado, carregando, pronto, erro, vazio (`total`
  0 → nada).
- Responsivo: igual nos três tamanhos (coluna única); texto longo do
  despacho quebra (`break-words`); sem rolagem lateral.
- A11y: `<ol>` com nome; título de marco de votação é link com nome claro;
  links externos anunciam nova aba; `role="status"` anuncia carga; `<details>`
  nativo (Enter/Espaço).
- Exemplos (vitrine `app/kit/linha-do-tempo`, PL 2/2024, disc. §2.6):
  03/01/2024 "Enviado pelo Executivo com urgência constitucional" (Câmara) ·
  19/03/2024 "Aprovado no Plenário da Câmara (314 × 96)" (`tipo="votacao"`,
  `href="/votacoes/exemplo"`, Câmara · PLEN) · 30/04/2024 "Aprovado no Senado
  sem mudanças" (Senado · PLEN) · 28/05/2024 "Sancionado com veto parcial"
  (Presidência, `atual`, `documento` "Lei 14.871/2024" → Planalto) +
  `TodosOsRegistros total={51}` num `DemoRegistros.tsx` cliente que vai de
  `ocioso` a `carregando` e, 300 ms depois, a `pronto` com 5 registros; casos
  `visual`: `pl-2-2024`, `registros-pronto`, `registros-erro`,
  `alinhamento-legado` (dois marcos com `tom`, para provar compatibilidade).

**Critérios de aceite**

1. Com `tom` padrão, nenhum marcador usa cor de alinhamento
   (`classesDeAlinhamento` vazio; `expectPaletaNeutra` na seção de
   tramitação).
2. Marco sem `href` não muda de fundo no hover; com `href`, o item inteiro é
   clicável e o foco fica no título.
3. O trilho não aparece no último marco sem passar `ultimo`.
4. Marco de votação é lido "Votação: Aprovado no Plenário da Câmara (314 ×
   96)"; o atual termina em "(mais recente)".
5. `TodosOsRegistros`: título "Todos os 51 registros"; `onAbrir` chamado uma
   vez em duas aberturas, e de novo ao reabrir depois de `erro`; com
   `onTentarDeNovo`, o erro tem o botão "Tentar de novo" e clicar o chama;
   trocar `registros` (página 2) com o recolhível aberto leva o foco ao
   primeiro registro; o erro padrão é `Aviso` `padrao`; a `<ol>` tem nome; a
   data dos registros não traz hora; `carregando` → `aria-busy` + "Carregando os
   registros."; `pronto` → "5 registros carregados."; `erro` sem prop → o
   `Aviso` padrão; `total` 0 → nada.
6. axe 0 em 3 larguras × 2 temas; jest-axe 0 por estado.

**Testes** — `tests/componentes/Tempo.test.tsx` (marcador por estado,
`local`, votação, link esticado, documento, legado com `tom`) e
`tests/componentes/TodosOsRegistros.test.tsx` (com `user-event`: abrir duas
vezes, estados, status lido); `tests/unit/eventos.test.ts` (`registroDoEvento`
com `data_hora` nula e com `-03:00` perto da meia-noite; `marcoDaApi` com e sem
`votacao_id`, sigla nula, `atual` só no último);
`tests/e2e/kit/linha-do-tempo.spec.ts` (molde +
abrir com teclado: Tab até o `summary`, Enter, ver "5 registros
carregados."; hover sem efeito em marco estático; `@visual`).

**Riscos e perguntas em aberto** — Texto original da Câmara pode ter caixa
alta e siglas: não normalizar (é fonte). A seleção dos até 8 marcos e seus
títulos em linguagem simples vêm da API (`marcos.yml`, TRM-021/026); sem
eles, a página mostra só "Todos os registros".

**Instruções para o agente implementador** — Branch
`trm-032-linha-do-tempo-v2`, depois de TRM-037 mergeada (usa o visual do
`summary`) e com rebase sobre TRM-030 (ambas mexem em `Tempo.tsx`). Ordem:
testes → `Marco`/`LinhaDoTempo` → `TodosOsRegistros` → vitrine → e2e →
README (linha "Cronologia", seções) → CHANGELOG. Verificação como em TRM-030.
Não busque dados no componente; não use `tom` na vitrine de tramitação.

---

### TRM-033 — `ComoSabemos` — padrão de proveniência reutilizável (fase, Bússola, norma)

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** P
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System + UI/UX
**Depende de:** TRM-001, TRM-003, **TRM-037** (`Recolhivel`), TRM-031-A (só o adaptador `comoSabemosDaFase`) · **Desbloqueia:** TRM-040 (U6: "fase com Como sabemos"), TRM-047 (destino do link), TRM-053/054 (bloco "Depois da lei")

**Problema** — O discovery pede, sob a fase, um `<details>` "Como sabemos" com
a regra, a versão do mapa e o endpoint (disc. §6.1 item 3); a regra U6 do PM
exige proveniência em toda fase. Não há padrão no kit: a Bússola montou o seu
à mão (`app/bussula/page.tsx`, `MarcoCard`: natureza da fonte, "sem link do
dado", validação), e "Depois da lei" vai precisar do mesmo (fonte e
`verificado_em`, disc. §7).

**Oportunidade** — Um único jeito de responder "de onde veio isto?" em todo o
site: curto fechado, completo aberto, sempre com pelo menos uma fonte que a
pessoa pode abrir.

**Solução** — `ComoSabemos` sobre `Recolhivel` (variante `discreto`), com
pares termo → valor, fontes obrigatórias por tipo, data de conferência, nota
editorial e link para a metodologia.

**Escopo** — Dentro: componente, adaptador da fase, vitrine (casos fase,
Bússola, norma), testes, README. Fora: trocar o `MarcoCard` da Bússola (fica
como sugestão para uma tarefa futura); textos da regra (vêm da API).

**Specs técnicas** — `components/ui/ComoSabemos.tsx` (servidor):

```ts
export interface FonteProveniencia {
  /** O que é: "API da Câmara — GET /proposicoes/2416804". */
  rotulo: string;
  /** Endereço público que reproduz o dado. Sem URL, diga por quê em `detalhe`. */
  url?: string;
  /** "consultada em 30/10/2026", "cópia de 02/11/2026 em data/tramitacao/referencias/". */
  detalhe?: string;
}

export interface ComoSabemosProps {
  /** Padrão: "Como sabemos". */
  titulo?: string;
  /** Uma linha visível com o recolhível fechado: "Leitura do ZIL, conferida na Câmara em 30/10/2026". */
  resumo?: React.ReactNode;
  /** Pares termo → valor, na ordem: Regra, Versão do mapa… */
  itens?: { termo: string; valor: React.ReactNode }[];
  /** Pelo menos uma fonte: o tipo exige. */
  fontes: [FonteProveniencia, ...FonteProveniencia[]];
  /** Data da última conferência, já formatada. */
  conferidoEm?: React.ReactNode;
  /** Ressalva ("A fase é calculada pelo ZIL a partir da situação oficial. Não é um dado da Câmara."). */
  nota?: React.ReactNode;
  /** Link interno para a explicação do método. */
  saibaMais?: { rotulo: string; href: string };
  /** `recolhivel` (padrão): dentro de <details>. `bloco`: aberto, sem <details> (metodologia). */
  variante?: "recolhivel" | "bloco";
  aberto?: boolean;
  className?: string;
}
```

Anatomia aberta: `<dl className="grid gap-x-6 gap-y-2
sm:grid-cols-[max-content_minmax(0,1fr)]">` (`dt` `text-texto-s
text-zil-texto-2`, `dd` `m-0 text-texto-s text-zil-texto`); "Fontes"
(`text-legenda uppercase tracking-[0.04em] text-zil-texto-2`) e `<ul
className="grid gap-1.5 list-none m-0 p-0">` com cada fonte: link externo
(`target="_blank" rel="noopener noreferrer"`, `Icone externo` e "(abre em
nova aba)" só para leitor) ou texto, e `detalhe` em `text-zil-texto-2`;
"Conferido em {conferidoEm}." (`text-texto-s text-zil-texto-2`); `nota`;
`saibaMais` como `Link` interno ("Como derivamos a fase →" é o texto da
vitrine; o real vem de TRM-040/047). Sem fundo próprio: espaço, não caixa
(dentro de `Card`, não cria cartão no cartão).

Adaptador `lib/tramitacao/como-sabemos.ts`:

```ts
export function comoSabemosDaFase(c: ComoSabemosApi): ComoSabemosProps | null;
// resumo (visível com o recolhível fechado; sem códigos internos — UX-DS-13):
//   conferido_em ? `Leitura do ZIL, conferida na Câmara em ${dataBR(c.conferido_em)}` : "Leitura do ZIL"
//   (regra e versão do mapa só dentro do recolhível)
// itens: [{ termo: "Regra", valor: c.regra_descricao ? `${c.regra} — ${c.regra_descricao}` : c.regra },
//         { termo: "Versão do mapa", valor: c.versao_publicada !== null ? `v${c.versao_publicada}` : "Não publicada" }]
// conferidoEm: c.conferido_em ? dataBR(c.conferido_em) : undefined
// fontes: c.fontes.map(f => ({ rotulo: f.rotulo, url: f.url ?? undefined, detalhe: f.url ? undefined : "Sem endereço público" }))
// fontes vazias → null + console.warn("[comoSabemosDaFase] fase sem fonte") — a página trata (estado C03 da matriz).
export function dataBR(iso: string): string;
// Só data ("2026-10-30") → fatia a string: "30/10/2026" (nunca new Date(): data só-dia é lida como
// UTC e vira o dia anterior em São Paulo). Com hora ("…T02:10:00Z" ou "…-03:00") →
// new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit",
// year: "numeric" }).format(new Date(iso)) — "2026-10-31T02:10:00Z" → "30/10/2026" (UX-DS-04).
```

**Specs de design**

- Estados: fechado (summary "Como sabemos" + resumo), aberto, `bloco`; foco e
  hover do `summary` vêm do `Recolhivel`; sem carregando (os dados chegam com
  a fase).
- Responsivo: `dl` em uma coluna abaixo de `sm`, duas a partir de `sm`; URLs
  longas quebram (`overflow-wrap:anywhere` no rótulo da fonte, como
  `.zil-caminho`).
- A11y: `<details>`/`<summary>` nativos; `<dl>` semântico; links externos
  anunciados.
- Tokens: `texto`, `texto-2`, `foco`. Sem cor.
- Exemplos (vitrine `app/kit/como-sabemos`): `fase-pl-2-2024` (`visual`) —
  resumo "Leitura do ZIL, conferida na Câmara em 30/10/2026"; Regra "R1 — há marco
  de transformação em norma no histórico"; fontes "API da Câmara — GET
  /proposicoes/2416804" (`https://dadosabertos.camara.leg.br/api/v2/proposicoes/2416804`)
  e "Mapa de fases do ZIL — data/tramitacao/fases.yml" (link para o
  repositório, `REPO_URL` de `lib/links.ts`); nota "A fase é calculada pelo ZIL
  a partir da situação oficial. Não é um dado da Câmara." · `bussola` —
  fonte institucional com `detalhe` "O link aponta para a página da
  instituição, não para a série do dado" · `norma` — "Senado — vides da Lei
  14.871/2024" · `aberto` · `bloco` (`visual`).
- **Não faz:** não busca a fonte; não valida URL; não aceita zero fontes.

**Critérios de aceite**

1. `fontes={[]}` não compila (teste de tipo com `// @ts-expect-error` em
   `tests/componentes/ComoSabemos.test.tsx`, conferido pelo `tsc`).
2. Fechado: `summary` com "Como sabemos" e o resumo; aberto: `dl` com os
   itens na ordem; cada fonte com URL é link externo com `rel="noopener
   noreferrer"` e "(abre em nova aba)".
3. `variante="bloco"` não renderiza `<details>`.
4. `dataBR("2026-10-30") === "30/10/2026"` e
   `dataBR("2026-10-30T23:30:00-03:00") === "30/10/2026"` e
   `dataBR("2026-10-31T02:10:00Z") === "30/10/2026"` em qualquer fuso; com
   `conferido_em` nulo, o resumo é "Leitura do ZIL" e não há linha "Conferido
   em" 
   (`process.env.TZ` de teste = `"America/Sao_Paulo"` e `"UTC"`).
5. `comoSabemosDaFase` com `fontes: []` devolve `null` e avisa.
6. axe 0 (3 larguras × 2 temas, fechado e aberto); jest-axe 0 por caso.

**Testes** — `tests/componentes/ComoSabemos.test.tsx`;
`tests/unit/como-sabemos.test.ts` (adaptador e `dataBR`);
`tests/e2e/kit/como-sabemos.spec.ts` (molde + abrir com teclado e axe aberto).

**Riscos e perguntas em aberto** — Contrato fechado em backlog-dados.md §1.5
(`regra_descricao`, `versao_publicada` inteiro, `fontes[{ rotulo, url }]`,
`conferido_em` anulável). `dataBR` não depende do fuso em que a API
serializa: só-data é fatiada; data com hora é convertida para
`America/Sao_Paulo` por `Intl.DateTimeFormat`. O destino de `saibaMais` é `/metodologia#tramitacao`
(TRM-047).

**Instruções para o agente implementador** — Branch
`trm-033-como-sabemos`, depois de TRM-037 (e de 031-A para o adaptador).
Testes primeiro; README (linha "Proveniência", seção); CHANGELOG.
Verificação padrão (TRM-030). Não troque a Bússola nesta tarefa.

---

### TRM-034 — `RitoDiagrama` — rito por espécie, ramos de desfecho, vertical no celular

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** G, quebrada em **034-A** (M: componente + vitrine + testes, contra dados de exemplo) e **034-B** (P/M: tipos do mapa e adaptador `ritoParaDiagrama`, depois de TRM-028)
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System + UI/UX + Arquitetura (034-B, contrato do mapa) + Maintainer
**Depende de:** TRM-001, TRM-003, TRM-030 (vocabulário de estado e `.zil-tracejado`), TRM-031 (glifos `parada`; tom `elevado`/`forte` do `Selo`), TRM-037; 034-B também TRM-028 e TRM-031-A · **Desbloqueia:** TRM-042, TRM-044

**Problema** — A pergunta "dá para saber todas as etapas e caminhos?" tem
resposta (disc. §2, §4.2: rito por espécie, desfechos, apensação), mas o kit
não tem como desenhá-la. O discovery pede `Etapas` verticais com ramificações
e base legal (§6.1 item 6) e um diagrama gerado de `ritos.yml`, vertical no
celular, com desfechos como ramos laterais (§6.3).

**Oportunidade** — A pessoa vê o caminho inteiro de uma espécie, onde a
proposição está nele, onde pode terminar e com que base legal — a mesma peça
em `/como-vira-lei` (rito genérico) e na página da proposição (rito com
estado).

**Solução**

*Forma visual — decisão:* **HTML semântico, não SVG.** Uma `<ol>` de etapas;
cada etapa é um `<li>` com marcador e trilho (como o `Marco`), um título
(`h3` por padrão), o que acontece, prazo, base legal e, quando houver, uma
`<ul>` de ramos de desfecho ("Pode terminar aqui"). Desfechos de qualquer
etapa ficam numa lista própria depois ("A qualquer momento"). Por quê:

| Critério | HTML semântico | SVG (fluxograma) |
| --- | --- | --- |
| Leitor de tela | lista ordenada + títulos + listas aninhadas: navegação nativa por títulos e itens | `role="img"` com descrição longa, ou papéis `graphics-*` com suporte ruim |
| Reflow a 320 px e zoom 400% (1.4.10) | reflui sozinho | texto preso em coordenadas; exige reescalar ou rolar |
| Texto longo (base legal, condição) | quebra | `<text>` não quebra linha |
| Ramos | lado a lado ≥ `md`, embaixo < `md`, com o mesmo DOM | layout calculado à mão para cada largura |
| Manutenção | Tailwind e tokens | geometria própria, como o `Hemiciclo` (que se justifica por ser 513 pontos) |

A estrutura do rito é essencialmente linear com saídas laterais; uma lista
ordenada com sublistas diz exatamente isso.

*Representação de dados que o componente recebe* (modelo de vista; o
adaptador de 034-B o monta a partir de `GET /tramitacao/mapa` e, na página da
proposição, de `GET /proposicoes/{id}/tramitacao`). Os nomes seguem os do
contrato final (backlog-dados.md §1.5 e §7-6) em camelCase, para não haver
dois vocabulários:

```ts
export interface BaseLegal { rotulo: string; url?: string }

export interface RamoRito {
  /** Chave do desfecho (`desfecho` da API: "arquivada"). */
  desfecho: Desfecho;
  /** Rótulo do mapa ("Arquivada"). */
  rotulo: string;
  /** Quando acontece, em linguagem simples (`texto` da API). null → `textoPendente`. */
  texto: string | null;
  baseLegal?: BaseLegal[];
  /** É o desfecho desta proposição. */
  ocorreu?: boolean;
}

export interface EtapaRito {
  /** Único no rito ("comissoes_cd"); igual a `etapas[].id` de /proposicoes/{id}/tramitacao. */
  id: string;
  fase: Fase;
  nome: string;
  /** Rótulo da Casa ("Câmara"). */
  casa?: string;
  /** `o_que_acontece`. null só por defesa (a API manda `etapas: []` quando o rito não é publicável). */
  oQueAcontece: string | null;
  /** `quem_decide` ("A presidência da comissão decide quando votar"). */
  quemDecide?: string | null;
  baseLegal?: BaseLegal[];
  /** Classe do prazo (D, D*, X) e o texto ("15 dias úteis; sem resposta no prazo, a sanção é automática"). */
  prazo?: { classe: ClassePrazo; texto: string } | null;
  /** Etapa que pode não acontecer (`opcional`); no rito genérico, marcador tracejado. */
  opcional?: boolean;
  /** Quando ela acontece (`condicao`: "Só se 52 deputados recorrerem em 5 sessões"). */
  condicao?: string | null;
  ramos?: RamoRito[];
  /** Estado desta proposição; sem estado, o rito é genérico. */
  estado?: EstadoEtapa;
  quando?: React.ReactNode;
  /** `etapas[].nota` ("Plenário dispensado: apreciação conclusiva"). */
  nota?: string | null;
  /** id do <li>, para âncora ("fase-comissoes"). */
  ancora?: string;
  /** "12 proposições acompanhadas estão aqui agora" (só no rito genérico). */
  contagem?: { n: number; href: string };
  /** Encaixe no fim da coluna principal (ex.: as situações da Câmara desta fase, como `TermoGlossario` — TRM-045). */
  extra?: React.ReactNode;
}

export interface RitoDiagramaProps {
  /** "Projeto de lei iniciado na Câmara"; compõe o nome da lista. */
  titulo: string;
  /** Vazia → o componente não renderiza nada (a página mostra o estado "em revisão"). */
  etapas: EtapaRito[];
  /** Desfechos possíveis em qualquer etapa (retirada pelo autor, arquivamento ao fim da legislatura). */
  desfechosGerais?: RamoRito[];
  /** Nível dos títulos de etapa e de "A qualquer momento". Padrão 3. */
  nivelTitulo?: 2 | 3 | 4;
  /** Legenda das classes de prazo, quando alguma etapa tem prazo. Padrão true. */
  legenda?: boolean;
  /** Padrão: "Explicação ainda não publicada." */
  textoPendente?: string;
  className?: string;
}
export function RitoDiagrama(props: RitoDiagramaProps): JSX.Element | null;
```

*Contrato de `GET /tramitacao/mapa`* — o de backlog-dados.md §1.5
(`MapaRead`, `EspecieRead`, `RitoRead`, `RitoEtapaRead`, `RitoDesfechoRead`),
espelhado em `lib/tramitacao/tipos.ts` (TRM-031-A) como `MapaApi`,
`EspecieApi`, `RitoApi`, `RitoEtapaApi`, `RitoDesfechoApi`. De/para:

| API (`RitoEtapaApi` / `RitoDesfechoApi`) | Modelo de vista |
| --- | --- |
| `id`, `fase`, `nome` | `id`, `fase`, `nome` |
| `casa` (`CasaRito`) | `casa` = `CASA_ROTULO[casa]` |
| `o_que_acontece`, `quem_decide` | `oQueAcontece`, `quemDecide` |
| `prazo { classe, texto }` | `prazo` |
| `base_legal[{ rotulo, url, norma, dispositivo }]` | `baseLegal[{ rotulo, url }]` |
| `opcional`, `condicao` | `opcional`, `condicao` |
| desfecho `{ desfecho, rotulo, texto, base_legal, a_partir_de }` | `RamoRito { desfecho, rotulo, texto, baseLegal }` na etapa (ou nos gerais) |
| `RitoApi.nome`, `publicavel`, `revisao` | `titulo`; `publicavel: false` → `etapas: []` |

*Adaptador (034-B)* — `lib/tramitacao/rito.ts`:

```ts
export function ritoParaDiagrama(
  rito: RitoApi,
  opcoes?: {
    /** Da página da proposição: `etapas` e `onde_esta.desfecho` de /proposicoes/{id}/tramitacao. */
    proposicao?: { etapas: EtapaApi[]; desfecho: Desfecho | null };
    contagens?: Record<string, number>;               // por id de etapa
    hrefContagem?: (etapa: RitoEtapaApi) => string;   // ex.: e => `/proposicoes?fase=${e.fase}`
    /** Padrão: rito.nome ?? rito.chave. A página pode passar o nome da espécie + Casa. */
    titulo?: string;
  },
): Pick<RitoDiagramaProps, "titulo" | "etapas" | "desfechosGerais"> & { publicavel: boolean; revisao: StatusRevisao };
```

Regras, nesta ordem: (0) `publicavel === false` → `etapas: []`,
`desfechosGerais: []`, `publicavel: false` (a página decide o que mostrar —
`Painel` "em revisão", da UI/UX); (1) etapas na ordem do rito, com o de/para
acima; `ancora = "fase-" + fase` só na primeira etapa de cada fase; (2) ramos
de uma etapa = desfechos com `a_partir_de` contendo o id (o mesmo desfecho pode
aparecer em duas entradas, com textos diferentes, para etapas diferentes);
gerais = `a_partir_de === "qualquer"`; (3) com proposição, junta por `id`
(`estado`, `quando` via `dataBR`, `nota`); etapa do rito sem par fica sem
estado; etapa da proposição sem par no rito →
`console.warn("[ritoParaDiagrama] etapa desconhecida: <id>")` e é ignorada —
nunca se inventa etapa; com `proposicao.etapas` vazia (fase nula,
`nao_sabemos`), o rito sai genérico; (4) `ocorreu` no ramo cujo `desfecho` é
`proposicao.desfecho`, na etapa `interrompida`; se não houver, nos gerais; se
não houver em lugar nenhum, nenhum; (5) `contagem` quando `contagens[id]`
existir. O adaptador **não** calcula estado.

*Como mostrar cada estado* (vocabulário de §1.3):

| Estado | Marcador | Selo ao lado do título | Meta | Trilho até a próxima |
| --- | --- | --- | --- | --- |
| sem estado (rito genérico) | anel vazado; tracejado se `opcional` | — | `condicao` (se houver) | `separador` |
| `feita` | ponto cheio `texto-2` | — | `quando` | `separador` |
| `atual` | ponto cheio `texto` + anel | `<Selo tom="forte">Está aqui</Selo>` | "Desde " + `quando` (o kit escreve o prefixo) | `separador` |
| `futura` | anel vazado | — | — | `separador` |
| `pulada` | anel vazado tracejado | `<Selo>Dispensada</Selo>` | `nota` ou `condicao` | `.zil-tracejado` (2 px) |
| `interrompida` | quadrado `texto` | `<Selo tom="elevado" icone={<Icone nome="parada" tamanho="s" />}>Parou aqui</Selo>` | `quando` · `nota`; o ramo `ocorreu` destacado | `separador` |
| `futura` depois de `interrompida` | anel vazado | — | "Não aconteceu" | `separador` |
| Ramo `ocorreu` | — | `<Selo tom="elevado">Foi o que aconteceu</Selo>` no ramo | — | — |

Sufixos só para leitor: os mesmos do `Etapas` em `feita`/`atual`/`futura`;
`aria-current="step"` no `<li>` atual.

*Anatomia* — raiz `<div className="grid gap-10">`:

1. `<ol aria-label={`Etapas: ${titulo}`} className="grid list-none m-0 p-0">`;
   cada `<li id={ancora} data-estado className="group/etapa relative grid
   grid-cols-[24px_minmax(0,1fr)] gap-x-3.5 pb-10 last:pb-0 scroll-mt-24">`:
   trilho absoluto (`left-[11px] top-7 -bottom-1 w-0.5 bg-zil-separador
   group-last/etapa:hidden`); marcador; conteúdo em `grid gap-3
   lg:grid-cols-[minmax(0,1fr)_minmax(0,20rem)] lg:gap-x-8 lg:items-start`
   (ramos à direita só a partir de `lg`: a 768, 20 rem de ramos deixariam ~30
   caracteres por linha para o texto — UX-DS-10):
   - coluna principal: Casa (`text-rotulo uppercase text-zil-texto-2`);
     título `<h{nivel} className="text-titulo-4">` + selo de estado; meta
     (`text-texto-s text-zil-texto-2`); `condicao`
     (`text-texto-s text-zil-texto-2`); `oQueAcontece` (`text-texto
     max-w-[60ch]`) ou `textoPendente` (`text-texto-s text-zil-texto-2`);
     `quemDecide` ("Quem decide: " em `text-zil-texto font-medium` + texto,
     `text-texto-s text-zil-texto-2`); prazo ("Prazo: " no mesmo estilo +
     texto + " · " + rótulo curto da classe); base legal ("Base: " + links
     externos separados por " · "); `contagem` como `Link` (`${n} proposições
     acompanhadas estão aqui agora` + `<span aria-hidden="true"> →</span>`; com
     1: "1 proposição acompanhada está aqui agora" — a seta nunca entra no nome
     do link, regra do kit para todo "→", UX-DS-09); `extra` por último;
   - coluna de ramos (se houver): `<div className="grid gap-3 p-4 rounded-m
     bg-zil-superficie-2">` com chapéu "Pode terminar aqui" (`text-rotulo
     uppercase text-zil-texto-2`) e `<ul aria-label="Pode terminar aqui"
     className="grid gap-3 list-none m-0 p-0">`; cada ramo: rótulo
     (`text-texto-ui font-semibold`), `texto` ou `textoPendente`
     (`text-texto-s text-zil-texto-2`), base legal; `ocorreu` → item com
     `p-3 -mx-1 rounded-s bg-zil-superficie-3` e o selo da tabela. Abaixo de
     `lg` os ramos descem para baixo do texto, recuados pela grade.
2. Desfechos gerais: `<h{nivel}>A qualquer momento</h{nivel}>` e `<ul
   aria-label="Desfechos possíveis em qualquer etapa">` no mesmo estilo dos
   ramos.
3. Legenda (se `legenda` e alguma etapa tem `prazo`): `<h{nivel}>Como ler os
   prazos</h{nivel}>` — mesmo nível de "A qualquer momento", para não virar
   subseção dele (UX-DS-08) — e `<dl>`: **Fixado na regra** — "A
   Constituição ou o regimento fixam o prazo." · **Fixado na regra, mas
   costuma não ser cumprido** — "A regra fixa o prazo, mas, na prática, ele
   costuma não ser cumprido, sem consequência." · **Sem prazo fixo** — "Não há
   prazo: quem preside a comissão ou a Casa decide quando (despacho, pauta,
   pedido de urgência)." Rótulos curtos usados na linha de prazo, idênticos aos
   decididos pela UI/UX: D → "fixado na regra", D\* → "fixado na regra, mas
   costuma não ser cumprido", X → "sem prazo fixo". Constante
   `CLASSE_PRAZO: Record<ClassePrazo, { curto: string; titulo: string; texto: string }>`
   no próprio `RitoDiagrama.tsx`, com teste que fixa os três textos curtos.
   ("discricionária", "requerimento", "quórum" e "norma" ficam fora por serem
   jargão.)

**Escopo** — Dentro: componente, vitrine, testes, README (034-A); tipos do
mapa + adaptador + testes (034-B). Fora: seletor de espécie e Casa e a página
`/como-vira-lei` (TRM-044); textos do rito (mapa aprovado, TRM-021/029);
rota prevista pelo despacho (TRM-052); calcular datas.

**Specs de design**

- Breakpoints: 375 e 768 → coluna única, ramos embaixo do texto, sem
  rolagem lateral; 1280 → ramos à direita (20 rem). Sempre vertical.
- Estados de interação: links (base legal, contagem) com hover sublinhado e
  foco global; alvos ≥ 24 px (`min-h-6 inline-flex items-center`); âncoras
  com `scroll-mt-24` (NavBar fixa).
- Tokens: `texto`, `texto-2`, `superficie-2`, `superficie-3`, `separador`,
  `inverso` (selo "Está aqui"), `foco`. Nenhuma cor de alinhamento — nem
  para "Virou lei", nem para "Rejeitada".
- Movimento: nenhum.
- Exemplos (vitrine `app/kit/rito-diagrama/casos.tsx`, **rascunho de
  demonstração** com base no disc. §2.1–2.3; o conteúdo publicado virá de
  `data/tramitacao/ritos.yml` aprovado):
  - `pl-camara-generico` (`visual`) — 7 etapas: Apresentação e despacho
    (Câmara; CF art. 61, RICD art. 139; prazo X "a Presidência distribui às
    comissões"); Comissões da Câmara (RICD art. 24, II; RICD art. 52; prazo D\*
    "5, 10 ou 40 sessões, conforme o regime"; ramo Arquivada — "Parecer
    terminativo de inconstitucionalidade (CCJC) ou de inadequação financeira
    (CFT), salvo recurso", RICD art. 54); Plenário da Câmara (`opcional`, condição "Só
    se não for conclusiva, ou se 52 deputados recorrerem em 5 sessões", RICD
    art. 58 §1º e 132 §2º; CF art. 47; prazo X "pauta da Presidência e do
    Colégio de Líderes"; ramo Rejeitada — CF art. 67); Senado (CF art. 65;
    RISF art. 91; ramo Rejeitada — "Rejeitado pelo Senado, vai ao arquivo", CF
    art. 65); De volta à Câmara (`opcional`, condição "Só se o Senado mudar o texto"; CF
    art. 65, parágrafo único); Sanção ou veto (Presidência; CF art. 66 §1º–3º;
    prazo D "15 dias úteis; sem resposta no prazo, a sanção é automática"; ramo Vetada —
    "Veto total mantido pelo Congresso", CF art. 66 §4º–6º); Virou lei (CF art.
    66 §5º e §7º; CF art. 84, IV; LC 95/1998 art. 8º). Gerais: Retirada
    (RICD art. 104), Arquivada ao fim da legislatura ("só depois de três
    legislaturas completas", RICD art. 105; RCD 33/2022), Prejudicada (RICD
    arts. 163–164). Com `contagem` em duas etapas.
  - `pl-com-estado` (`visual`) — o anterior com Apresentação `feita`,
    Comissões `atual` (quando 09/05/2025 → "Desde 09/05/2025"), resto `futura`.
  - `pl-conclusiva` — Plenário `pulada` com nota "Plenário dispensado:
    apreciação conclusiva" (o texto que a API manda em `etapas[].nota`).
  - `arquivada` (`visual`) — Comissões `interrompida` (31/01/2023), ramo
    Arquivada `ocorreu`, demais "Não aconteceu".
  - `mpv` (`visual`) — Comissão mista (Congresso; prazo D "60 dias,
    prorrogáveis por mais 60, sem contar o recesso", CF art. 62), Plenário da
    Câmara, Senado, Sanção (se alterada) ou promulgação; ramo Perdeu a
    eficácia ("Não foi votada no prazo de 60 + 60 dias, sem contar o
    recesso", CF art. 62). Textos de exemplo seguem o guia de redação
    (backlog-interface.md §2).
  - `pendente` — etapa e ramo com `oQueAcontece`/`texto` `null`.
  - `opcional` — rito genérico com o Plenário `opcional` e `condicao`.
- **Não faz:** não escolhe espécie nem Casa; não deriva estado; não calcula
  prazo nem data; não busca dados; não mostra rito "parcialmente aprovado"
  como se fosse completo (texto pendente explícito).

**Critérios de aceite**

1. Estrutura: uma `<ol>` com nome "Etapas: {titulo}"; um `<li>` por etapa;
   um título por etapa no nível pedido; ramos em `<ul>` com nome "Pode
   terminar aqui"; gerais em `<ul>` com nome "Desfechos possíveis em qualquer
   etapa". Nenhum `svg` fora de ícones `aria-hidden`.
2. A 375 e a 768 px, sem rolagem lateral e com os ramos **abaixo** do texto
   da etapa (`boundingBox.y` maior); a 1280, **à direita** (`x` maior, `y`
   próximo). Os níveis de título não saltam e "Como ler os prazos" não fica
   sob "A qualquer momento"; o nome do link de contagem não contém "→".
3. Atual: `aria-current="step"`, selo "Está aqui", sufixo "(etapa atual)".
   Interrompida: selo "Parou aqui", ramo `ocorreu` com "Foi o que aconteceu",
   etapas seguintes com "Não aconteceu". Pulada: selo "Dispensada" + nota, trilho
   tracejado.
4. `oQueAcontece` (etapa) ou `texto` (ramo) `null` mostram "Explicação ainda
   não publicada."; `etapas` vazia → o componente devolve `null`.
5. Legenda só aparece se alguma etapa tem `prazo`.
6. `classesDeAlinhamento` vazio; `expectPaletaNeutra` nos dois temas.
7. axe 0 em 3 larguras × 2 temas; jest-axe 0 por caso.
8. (034-B) `ritoParaDiagrama`: ordem preservada; âncora só na primeira etapa
   de cada fase; ramos por `a_partir_de` (inclusive desfecho repetido com
   condições diferentes); junção por `id`; etapa desconhecida avisada e
   ignorada; `ocorreu` na etapa interrompida, senão nos gerais; nenhum estado
   inventado (sem proposição ou com `etapas: []`, nenhuma etapa tem
   `estado`); rito com `publicavel: false` → `etapas: []` e `publicavel:
   false`; `base_legal` com `url: null` vira `BaseLegal` sem `url`.

**Testes** — `tests/componentes/RitoDiagrama.test.tsx` (estrutura, estados,
textos, pendente, legenda, paleta, axe por caso);
`tests/unit/rito.test.ts` (034-B, regras 0–5 com a fixture
`tests/fixtures/api/tramitacao/mapa.json` da UI/UX — TRM-046-B; se ainda não
existir, 034-B a cria com esse nome e formato `MapaApi`, e a UI/UX completa);
`tests/e2e/kit/rito-diagrama.spec.ts` (molde + posição dos ramos por largura +
âncora `#fase-comissoes` rola sem ficar sob a NavBar).

**Riscos e perguntas em aberto** — O formato do mapa está fechado em
backlog-dados.md §1.5 (antes: proposta, §5,
conflito 5). PEC e MPV podem precisar de etapas que se repetem (dois turnos)
— resolvido com `id` único por etapa. Rito longo (PEC, ~10 etapas) fica alto
no celular: a página (TRM-044) pode recolher a descrição; o componente não
recolhe por padrão.

**Instruções para o agente implementador** — Branches
`trm-034a-rito-diagrama` (depois de 030, 031 e 037) e
`trm-034b-rito-adaptador` (depois de 028 e 031-A). Ordem (A): testes →
componente → vitrine → e2e → baselines → README (linha "Rito de uma espécie",
seção) → CHANGELOG. (B): tipos → testes do adaptador → adaptador. Verificação
padrão. Não use SVG; não publique textos de rito fora da vitrine; não calcule
estado.

---

### TRM-035 — `TermoGlossario` (definição inline acessível) + `GlossarioLista`

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System + UI/UX (textos de microcopy) + Maintainer
**Depende de:** TRM-001, TRM-003; TRM-031-A só para o adaptador `lib/tramitacao/glossario.ts` · **Desbloqueia:** TRM-040 (regime e apreciação inline), TRM-044, TRM-045

**Problema** — Situações oficiais enganam ("Aguardando Despacho do
Presidente da Câmara dos Deputados (Chancela)" lido como sanção, disc. §1.1);
regime e apreciação são jargão (RICD 24 II, 151, 155). O ZIL Interface tem um
"Glossário" em tooltip (`<span class="zi-termo" tabindex="0">` com
`role="tooltip"`, aberto por hover/foco, 150 ms de atraso) que: não funciona
bem no toque (o celular é o uso principal); não pode conter link nem base
legal (tooltip não admite conteúdo interativo); exige cumprir 1.4.13
(dispensável, persistente, "hoverable") em hover; e põe foco em `span` sem
papel. Não existe lista de termos para `/como-vira-lei/situacoes`.

**Oportunidade** — O termo técnico vira explicação a um toque, no lugar onde
aparece, com link para o glossário completo; e a lista de situações tem
âncoras que o `FaseSelo` e o próprio termo podem apontar.

**Solução — padrão escolhido: disclosure** (APG "Disclosure (Show/Hide)").

| Opção | Veredito | Por quê |
| --- | --- | --- |
| Tooltip (`role="tooltip"`, hover/foco) | Não | Toque; sem conteúdo interativo; 1.4.13 |
| `<details>` inline | Não | `<details>` não é conteúdo fraseado: dentro de `<p>` é HTML inválido e o React acusa aninhamento |
| `popover` nativo + `popovertarget` | Não, por ora | React 18 e `@types/react` 18 não tipam os atributos; posicionar junto do termo exige *anchor positioning*, que ainda não é Baseline em todos os navegadores-alvo. Revisitar com React 19 |
| `<button>` + região | Quase | `<button>` é atômico (não quebra linha); termos oficiais têm até 85 caracteres e estouram 343 px |
| **`<span role="button" tabindex="0" aria-expanded aria-controls>` + definição logo depois no DOM** | **Sim** | Quebra linha como texto; papel e estado corretos; definição em ordem de leitura; abre por clique/toque/Enter/Espaço; nada por hover |

**Escopo** — Dentro: `TermoGlossario`, `GlossarioLista`, adaptador
`lib/tramitacao/glossario.ts`, vitrine, testes, README. (O `scroll-padding`
global para a NavBar fixa foi para TRM-037, que mergeia antes — UX-DS-22.) Fora: escrever o glossário (TRM-022/029); a página
`/como-vira-lei/situacoes` (TRM-045); busca no glossário (página, com `Busca`).

**Specs técnicas**

`components/ui/TermoGlossario.tsx` (`"use client"`):

```ts
export interface TermoGlossarioProps {
  /** O termo como aparece no texto ("apreciação conclusiva"). */
  children: React.ReactNode;
  /** Definição aprovada. null/ausente → só o texto, sem gatilho (entrada não aprovada não aparece). */
  definicao?: string | null;
  /** Título dentro da definição. Padrão: o termo, se for string. */
  titulo?: string;
  baseLegal?: { rotulo: string; url?: string }[];
  /** Entrada no glossário ("/como-vira-lei/situacoes#termo-apreciacao_conclusiva"). */
  href?: string;
  /** Padrão: "Texto do ZIL, não oficial." (igual ao `aviso` do mapa e à matriz G02). */
  nota?: string;
  /**
   * Começa aberto (a pessoa ainda pode fechar). Para quando o termo oficial é a primeira
   * leitura e pode enganar — estado N06 da matriz da UI/UX ("…(Chancela)" sem frase).
   * Não dispara o evento que fecha os outros termos.
   */
  abertoInicial?: boolean;
  /** Texto só para leitor depois do termo, no gatilho. Padrão ", o que quer dizer" (UX-DS-16). */
  rotuloAcao?: string;
  /** Mostra `Icone info` de 16 px (`aria-hidden`) depois do termo: pista no toque, onde não há hover (UX-DS-32). */
  indicador?: boolean;
}
```

- Estrutura (tudo conteúdo fraseado, válido dentro de `<p>`): `<span
  className="relative">` → gatilho `<span role="button" tabIndex={0}
  aria-expanded={aberto} aria-controls={id} className="cursor-pointer
  rounded-xs underline decoration-dotted decoration-[1.5px]
  underline-offset-4 decoration-zil-texto-2 hover:decoration-zil-texto
  aria-expanded:decoration-solid">{children}<span className="sr-only">{rotuloAcao}</span>{indicador
  && <Icone nome="info" tamanho="s" className="inline ml-1 align-[-2px]" />}</span>`
  → definição `<span id={id} hidden={!aberto} className="…">` (`id` de
  `useId()`). O nome acessível começa pelo termo visível (2.5.3): "Aguardando
  Parecer, o que quer dizer".
- Definição: `block my-2 p-4 rounded-m bg-zil-superficie-2 text-left` no
  fluxo abaixo de `md` (empurra o texto; não é vidro, porque não flutua); a
  partir de `md`, `md:absolute md:top-full md:mt-2 md:my-0 md:z-10
  md:w-[min(36ch,calc(100vw-2rem))] md:bg-zil-vidro-solido md:shadow-flutuante
  md:rounded-[18px] md:animate-zil-surge` + `md:left-0` ou `md:right-0`.
  `vidro-solido` (opaco) e não `vidro-forte`: texto sobre texto borrado tem
  contraste imprevisível; com o opaco, `texto` 14,4/17,5 e `texto-2` 6,2/6,5.
- Conteúdo: título (`block text-texto-ui font-semibold`), definição (`block
  mt-1 text-texto` — 18 px, regra do kit), base legal (`block mt-2
  text-texto-s text-zil-texto-2`, "Base: " + links externos), `href` como
  `Link` "Ver no glossário" (`inline-flex mt-2 min-h-6 text-texto-s
  font-medium underline underline-offset-4`), nota (`block mt-2 text-legenda
  text-zil-texto-2`).
- Comportamento: clique/toque alterna; Enter (keydown) alterna; Espaço
  (`preventDefault` no keydown, alterna no keyup); Esc com foco no gatilho ou
  dentro da definição fecha e devolve o foco ao gatilho; clique fora (evento
  `click`, não `pointerdown`, para não fechar ao rolar no celular) fecha;
  abrir um termo fecha os outros (evento `zil:termo` em `document` com o `id`);
  o foco não se move ao abrir (disclosure).
- Lado (≥ `md`): ao abrir, medir a definição (`useLayoutEffect`); se
  `right > innerWidth - 16`, trocar para `md:right-0`. Sem estilo inline.
- `definicao` nula → renderiza só `children` (sem gatilho, sem sublinhado).
- `abertoInicial` → estado inicial `aberto = true` (o HTML do servidor já sai
  com a definição visível e `aria-expanded="true"`); Esc, clique e clique fora
  fecham como sempre.

`components/ui/GlossarioLista.tsx` (servidor):

```ts
export interface EntradaGlossario {
  /** Vira a âncora: `${prefixoAncora}${chave}`. */
  chave: string;
  /** Como a fonte escreve ("Aguardando Parecer"). */
  termo: string;
  /** Explicação aprovada; null → `semTexto`. */
  texto: string | null;
  baseLegal?: { rotulo: string; url?: string }[];
  /** Ex.: <FaseSelo …/> com a fase a que a situação leva. */
  extra?: React.ReactNode;
  /** true quando `termo` é texto oficial: chapéu "Termo oficial". */
  oficial?: boolean;
}
export interface GlossarioListaProps {
  entradas: EntradaGlossario[];
  /**
   * Com nível, cada entrada vira `<article aria-labelledby>` com `<h{n} id="termo-<chave>"
   * tabIndex={-1}>` — navegável por títulos em listas longas (/situacoes usa 3; UX-DS-20).
   * Sem nível, `<dl>` (listas curtas).
   */
  nivelTitulo?: 2 | 3 | 4;
  /** Padrão "termo-". */
  prefixoAncora?: string;
  /** Padrão "Sem explicação ainda." */
  semTexto?: React.ReactNode;
  /** Padrão "Texto do ZIL, não oficial." */
  nota?: React.ReactNode;
  className?: string;
}
```

- `<dl className="grid gap-3">`; cada entrada `<div className="grid gap-2 p-5
  rounded-l bg-zil-superficie-1 has-[:target]:bg-zil-superficie-2">` com `<dt
  id={…} tabIndex={-1} className="scroll-mt-24 text-titulo-4">` (o
  `tabIndex={-1}` deixa a página dar foco ao alvo da âncora sem pô-lo na ordem
  de tabulação — TRM-045) (chapéu "Termo oficial"
  antes, se `oficial`), `<dd className="m-0 text-texto">` texto ou `semTexto`
  (`text-texto-s text-zil-texto-2`), `<dd>` base legal, `<dd>` `extra`.
  Depois, a `nota` (`text-texto-s text-zil-texto-2`). Com `nivelTitulo`: `<div
  className="grid gap-3">` de `<article aria-labelledby={idTitulo}
  className="grid gap-2 p-5 rounded-l bg-zil-superficie-1
  has-[:target]:bg-zil-superficie-2">`, com o título `<h{n}
  className="scroll-mt-24 text-titulo-4">`, `<p className="text-texto">`, base
  legal e `extra` — mesmo visual.

Adaptador `lib/tramitacao/glossario.ts`, sobre `GlossarioApi` (o
`GlossarioRead` de backlog-dados.md §1.5, espelhado em `tipos.ts`: `chave`
snake_case, `tipo`, `termo`, `publicavel`, `texto_curto` ≤ 160, `texto` ≤ 900,
`base_legal`, `fase`):

```ts
/** Lista: texto = (publicavel && revisao === "aprovado") ? (texto ?? texto_curto) : null — defesa em profundidade:
 *  entrada aprovada e depois editada tem revisao "aprovado" e publicavel false (UX-DS-15).
 *  oficial = tipo === "situacao" (o termo é como a Câmara escreve). */
export function entradaDaApi(e: GlossarioApi): EntradaGlossario;
/** Âncora e link: `/como-vira-lei/situacoes#termo-${chave}`. */
export function hrefDoTermo(chave: string): string;
/** Inline: definicao = (publicavel && revisao === "aprovado") ? texto_curto : null; titulo = termo;
 *  href = hrefDoTermo(chave). null se a chave não existe. */
export function definicaoDoTermo(glossario: GlossarioApi[], chave: string):
  { definicao: string | null; titulo: string; href: string; baseLegal: { rotulo: string; url?: string }[] } | null;
/** Entrada da situação oficial pela chave que a API manda pronta (`situacao_glossario`, em `onde_esta` e em
 *  `ProposicaoRead`). Nunca casar por texto: o termo é editorial, o oficial varia e há códigos com o mesmo nome
 *  (revisão da Arquitetura, item 4). Chave nula ou inexistente → null. */
export function entradaDaSituacao(glossario: GlossarioApi[], chave: string | null): GlossarioApi | null;
```

Âncora: `termo-<chave>` (prefixo do componente, que a UI/UX adotou para não
colidir com `id` de seção). backlog-dados.md §7-7 escreve `#<chave>`; o que
vale é o `id` que a página gera, então a Arquitetura só precisa não montar
links de âncora no servidor (§5, conflito 13).

**Specs de design**

- Estados do termo: fechado, hover (sublinhado sólido mais forte), foco
  (contorno global), aberto (`aria-expanded`, sublinhado sólido), sem
  definição (texto puro). Da lista: normal, alvo da âncora (fundo
  `superficie-2`, sem animação), sem texto.
- Responsivo: 375 → definição no fluxo, largura da coluna; 768/1280 → cartão
  flutuante de até 36ch, virando para a esquerda perto da borda.
- A11y: papel `button` + `aria-expanded` + `aria-controls`; definição em
  ordem de leitura; Esc; foco devolvido; alvo isento de 2.5.8 por estar em
  frase (exceção "inline"); `dl/dt/dd`; âncoras com `scroll-mt`.
- Tokens: `texto`, `texto-2`, `superficie-1/2`, `vidro-solido`,
  `sombra-flutuante`, `foco`; `animate-zil-surge` (220 ms, cortado em
  movimento reduzido).
- Exemplos (vitrine `app/kit/glossario`; textos de `texto_curto` dos
  rascunhos de backlog-interface.md §2.6–2.7, marcados como exemplo; os reais
  vêm de `glossario.yml` aprovado):
  - parágrafo (`visual`, aberto e fechado): "Este projeto está sujeito à
    {apreciação conclusiva} e tramita em {regime de urgência}." — definições
    = `texto_curto` de `apreciacao_conclusiva` e `regime_urgencia` daquele
    rascunho, com a base legal que ele cita (RICD art. 24, II; RICD art. 155).
  - termo longo no fim da linha a 375 e perto da borda direita a 1280:
    "Aguardando Despacho do Presidente da Câmara dos Deputados (Chancela)" —
    "A proposição ainda não foi distribuída às comissões. O Presidente da
    Câmara ainda vai assinar o despacho que diz por quais comissões ela
    passa." (rascunho de backlog-interface.md §2.6); com `abertoInicial` e
    `indicador` num segundo exemplo.
  - termo sem definição ("Aguardando Encaminhamento", `definicao={null}`).
  - `GlossarioLista` (`visual`, uma com `dl` e outra com `nivelTitulo={3}`):
    Aguardando Parecer, Aguardando Designação de Relator(a), Pronta para
    Pauta, Tramitando em Conjunto — **com os rascunhos de
    backlog-interface.md §2.6**, copiados como estão e marcados "exemplo" (os
    textos que este arquivo trazia antes eram inexatos, UX-DS-19) —, e
    Aguardando Encaminhamento (sem texto).
- **Não faz:** não busca o glossário; não mostra texto não aprovado; não abre
  por hover; não decide quais palavras viram termo (página/TRM-045).

**Critérios de aceite**

1. Gatilho com `role="button"`, `aria-expanded="false"` e `aria-controls`
   apontando para a definição oculta; Enter e Espaço abrem e fecham; Esc fecha
   e o foco volta ao gatilho; clique fora fecha; abrir um fecha o outro.
   O nome acessível do gatilho é "{termo}, o que quer dizer"; com
   `indicador`, o ícone aparece e não entra no nome.
2. Renderizado dentro de `<p>`, nenhum aviso de aninhamento do React
   (`console.error` espionado vazio).
3. A 375, o termo de 70+ caracteres quebra linha e a definição aberta fica
   dentro da largura da tela; a 1280, perto da borda direita, a definição
   abre alinhada à direita e cabe na tela.
4. `definicao={null}` → texto puro, sem papel nem sublinhado.
5. Nada abre com hover (teste de `page.hover` sem mudança de `aria-expanded`).
6. `GlossarioLista`: `dt` com `id="termo-<chave>"`; `texto` nulo → "Sem
   explicação ainda."; a nota "Texto do ZIL, não oficial." aparece; ir a
   `#termo-pronta_para_pauta` deixa o `dt` visível abaixo da NavBar. Com
   `nivelTitulo={3}`, cada termo é um `h3` (navegável por títulos) dentro de
   `article`, com o mesmo visual.
7. `entradaDaApi` e `definicaoDoTermo` devolvem texto nulo quando
   `publicavel` é falso, mesmo com `texto`/`texto_curto` preenchidos;
   `entradaDaSituacao(glossario, chave)` acha pela `chave` e devolve `null`
   para chave nula ou inexistente (nenhuma busca por texto).
8. axe 0 em 3 larguras × 2 temas, com termos fechados e com um aberto;
   jest-axe 0 por caso.
9. `abertoInicial`: o HTML renderizado já tem a definição visível e
   `aria-expanded="true"`; Esc fecha; abrir outro termo depois não reabre este.

**Testes** — `tests/componentes/TermoGlossario.test.tsx` (com `user-event`:
teclado, Esc, foco, clique fora, um por vez, `null`, dentro de `<p>`);
`tests/componentes/GlossarioLista.test.tsx`; `tests/unit/glossario.test.ts`
(adaptador); `tests/e2e/kit/glossario.spec.ts` (molde + toque no projeto
`celular` com `page.tap` + teclado + hover sem efeito + posição dentro da
viewport + âncora).

**Riscos e perguntas em aberto** — Pedir ao ZIL Interface que troque o
Glossário em tooltip por este padrão (proposta de TRM-036). Se alguma página
precisar do termo fora de `<p>` (em lista, em título), o componente funciona
igual. Leitores de tela podem anunciar o `span` como "botão, recolhido" — é o
esperado.

**Instruções para o agente implementador** — Branch
`trm-035-glossario` (adaptador depois de 031-A). Ordem: testes →
`TermoGlossario` → `GlossarioLista` → adaptador → vitrine → e2e → baselines → README (linhas "Termo técnico no
texto" e "Lista de termos", seções) → CHANGELOG. Verificação padrão. Não use
`role="tooltip"` nem hover; não use `<details>` dentro de parágrafo.

---

### TRM-036 — Documentação do kit (README, exemplos, checklist de a11y) e proposta ao design system ZIL Interface

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P2 · **Horizonte:** Em seguida · **Estimativa:** M
**Dono da spec:** Design System · **Revisões obrigatórias:** Product (itens novos do checklist) + UI/UX + **Maintainer (aprova a proposta ao ZIL Interface)**
**Depende de:** TRM-003 (checklists em `docs/revisao/`), TRM-030 a TRM-035, TRM-037 · **Desbloqueia:** aplicação da proposta no artefato ZIL Interface (fora deste backlog, só com aprovação)

**Problema** — O README do kit (`components/ui/README.md`, 78 linhas) não diz
nada sobre fase, estado ou proveniência; a linha "Status" (`:43`) só oferece
tons com cor; "Cronologia" (`:48`) manda usar `Etapas` "para tramitação" sem
regra. Os gates S1–S10 (spec §7.3, TRM-003) dizem **o quê** verificar, não
**como**; um revisor-agente sem comando tende a marcar ✓ (spec §9.1, Riscos).
O ZIL Interface, de onde o kit vem, diverge do que este épico decide (Etapas
pulsando em âmbar, Glossário em tooltip, Linha do tempo só por alinhamento).

**Oportunidade** — Um kit que se explica: quem chega (pessoa ou agente) acha o
componente certo, o jeito certo de mostrar fase sem cor e o comando que prova
cada item do gate; e o design system de origem volta a ser a verdade.

**Solução** — Quatro entregas:

1. **README do kit** — tabela "Precisa de / Use" com as linhas abaixo; seção
   "Fase e status: paleta neutra" (as regras de §1.3 deste arquivo e a tabela
   do vocabulário visual); uma seção por componente novo ou alterado
   (propósito em uma frase, quando usar, quando não usar, props, exemplo,
   acessibilidade, o que não faz) — cada tarefa 030–035/037 escreve a sua;
   esta revisa coerência e preenche lacunas; seções "Testes" (de TRM-001) e
   "Vitrine".

   | Precisa de | Use |
   | --- | --- |
   | Status (alinhamento, validação) | `Selo` (`alinhado` · `contra` · `neutro` · `forte` · `elevado`; `quebrar`; `href`), `DirecaoBadge`, `ContextoBadge`, `CategoriaBadge`. Rótulo curto: situação oficial nunca vai em `Selo` |
   | Fase de uma proposição | `FaseSelo` (rótulo da API; sem cor; desfecho e `nao_sabemos` neutros) |
   | Etapas da tramitação | `Etapas` (`completa` · `compacta`; vertical abaixo de `md`) |
   | Cronologia | `LinhaDoTempo` + `Marco` (`atual`, `local`, `tipo`, `documento`; `tom` só para alinhamento) + `TodosOsRegistros` |
   | Caminho de uma espécie | `RitoDiagrama` |
   | De onde veio o dado | `ComoSabemos` |
   | Termo técnico no texto · lista de termos | `TermoGlossario` · `GlossarioLista` |
   | Conteúdo recolhido | `Recolhivel` (`<details>` nativo; `linha` · `discreto`) |

2. **"Como verificar" do gate de DS** — acrescentar a
   `docs/revisao/checklist-design-system.md` (arquivo de TRM-003) uma segunda
   tabela, sem mudar o texto de S1–S10:

   | Item | Como verificar |
   | --- | --- |
   | S1 | Tabela "Precisa de / Use" do README; `grep -rn "<details" apps/web/app` mostra só usos via `Recolhivel`/`TodosOsRegistros` |
   | S2 | `tests/componentes/kit-cobertura.test.ts` (abaixo) verde; seção no README |
   | S3 | `git diff main -- apps/web \| grep -nE "#[0-9a-fA-F]{3,8}\b\|rgba?\(" ` vazio fora de `globals.css`; `grep -n "style={" ` só com comentário de "valor de dado" |
   | S4 | `classesDeAlinhamento` nos testes de componente e `expectPaletaNeutra` nos e2e da área de tramitação |
   | S5 | Leitura do diff + `animacoesInfinitas` = 0 na vitrine/rota |
   | S6 | Props com os nomes do contrato (`EstadoEtapa`, `Fase`, `Desfecho`) importados do kit |
   | S7 | `grep -nE "text-\[(1[0-7])px\]" ` no diff só em metadado/rótulo, nunca em `<p>` de corpo |
   | S8 | Jobs `test-frontend` e `e2e-frontend` verdes; artefato `evidencias-ui` com 3 larguras × 2 temas; baseline `@visual` revisada |
   | S9 | `grep -n '"use client"' ` no diff só em arquivo com estado, evento ou busca de dados no navegador; busca no navegador em página sem interação só nas exceções registradas (§1.4: `/como-vira-lei`, `/como-vira-lei/situacoes`), com `page.tsx` servidor |
   | S10 | Repetir o grep de usos (§1.5 deste arquivo) e rodar a suíte inteira |

   A tabela equivalente para U1–U14 é da UI/UX (UX-DS-36), reaproveitando
   os mesmos helpers de TRM-001 (`expectPaletaNeutra`, `animacoesInfinitas`,
   `focoVisivelENaoEncoberto`, `semRolagemHorizontal`, projeto `reflow-320`);
   esta tarefa só a referencia.

   E **propor ao PM** (não aplicar sem aceite): S4 incluir `zil-neutro*`
   (âmbar também não é cor de fase); S3 aceitar `style={}` só para valor de
   dado com comentário (regra atual do README do kit, usada em `Segmentado`,
   `Score`, `Revelar`); S11 "toda variante e estado na vitrine `/kit/<slug>`";
   S12 "texto real mais longo do banco testado sem truncar".

3. **Automação do gate** — `tests/componentes/kit-cobertura.test.ts`: lê
   `components/ui/index.ts`, extrai os nomes exportados em PascalCase (valores,
   não `type`) e falha se algum não aparece em nenhum arquivo de
   `tests/componentes/`, exceto os de uma lista `LEGADO_SEM_TESTE` (os
   componentes que já existiam antes de TRM-001: `Icone`, `Button`,
   `BotaoIcone`, `Chip`, `Chips`, `BarraFiltros`, `ContadorFiltros`, `Card`,
   `Estat`, `Painel`, `Avatar`, `ScorePilula`, `ScoreGrande`, `Medidor`,
   `VotosBarra`, `VotosLegenda`, `Lista`, `Linha`, `LinhaEsqueleto`, `Placar`,
   `PlacarCabecalho`, `PlacarLinha`, `PlacarLinhaEsqueleto`, `Busca`, `Campo`,
   `Segmentado`, `Seletor`, `Aviso`, `Vazio`, `Esqueleto`, `CardEsqueleto`,
   `Paginacao`, `TituloSecao`, `Citacao`, `Foto`, `Revelar`, `Contador`, e os
   do PR #48 se mergeado antes). Falha também se um nome da lista ganhou teste
   (a lista só encolhe). Índice `/kit` com nome, uma frase e grupo de cada
   vitrine.

4. **Proposta ao ZIL Interface** — em
   `specs/013-tramitacao/zil-interface/`: `PROPOSTA.md` (tabela abaixo, com
   motivo e risco de cada mudança) e, por componente, os arquivos no formato
   do artefato — `components/<Nome>/README.md` e `components/<Nome>/preview.html`
   (linha 1 `<!-- @dsCard group="…" height=… -->`, marcação `zi-*`), mais o CSS
   a acrescentar ao `components/bundle.css` e o trecho novo do `README.md` do
   artefato. Nada é publicado nesta tarefa.

   | Página do ZIL Interface | Proposta |
   | --- | --- |
   | Etapas | Sem pulso; atual = meia barra em `texto` (não `neutro`); estados pulada (tracejado) e interrompida (■); vertical abaixo de 768 px; variante compacta com "Etapa 3 de 6: …"; Casa; texto lido |
   | Linha do tempo | Dois usos: alinhamento (como hoje) e tramitação (marcador neutro, atual × passado); `local`, documento, votação como link; hover só em item com link, em `superficie-2`; "Todos os registros" recolhível |
   | Glossário | Tooltip → disclosure por clique/toque/teclado; definição no fluxo abaixo de 768 px e cartão opaco (`vidro-solido`) acima; "Ver no glossário"; nova "Lista de termos" |
   | Controles › Selo | Tom `elevado`; quebra de linha; selo-link; regra "rótulo curto, nunca situação oficial" |
   | Dados cívicos (novos) | Selo de fase, Rito, Como sabemos |
   | Leitura e navegação (novo) | Recolhível (`<details>`) ao lado do Acordeão, com quando usar cada um |
   | Iconografia | `parada`, `duvida`, `conjunto` |
   | README › Cor | Linha "Fase e status: sem matiz — estado por texto e forma"; corrigir "texto-3 … 4,4:1" para "≥ 4,5:1 sobre fundo, superfície 1 e 2; não usar sobre superfície 3" |

   Aplicar no artefato **só depois de a maintainer aprovar no PR**, numa sessão
   com permissão de escrita, seguindo as instruções do tipo Design System do
   próprio artefato: ler os arquivos que vão mudar, publicar só os caminhos
   `project/…` alterados e o `project/design-system.json` por último, com
   `lastChange`.

**Escopo** — Dentro: README do kit, tabela "Como verificar", teste de
cobertura do kit, índice `/kit`, pasta de proposta. Fora: alterar S1–S10 ou
U1–U14 (são de TRM-003/PM); publicar no artefato; documentar componentes de
fora do kit.

**Critérios de aceite**

1. README do kit com as 8 linhas da tabela, a seção "Fase e status: paleta
   neutra" e uma seção por componente de 030–035/037, cada uma com props,
   exemplo, a11y e "não faz".
2. `docs/revisao/checklist-design-system.md` com a tabela "Como verificar"
   para S1–S10, texto de S1–S10 intocado.
3. `npm run test` inclui `kit-cobertura.test.ts` verde; remover o teste do
   `FaseSelo` o faz falhar.
4. `/kit` lista todas as vitrines existentes.
5. `specs/013-tramitacao/zil-interface/` com `PROPOSTA.md` e os arquivos dos 8
   itens da tabela; nenhum `preview.html` usa cor de alinhamento para fase.
6. Proposta de S4/S3/S11/S12 enviada ao PM como comentário no PR.

**Specs de design** — Sem componente novo. Os `preview.html` da proposta
seguem os tokens e a marcação `zi-*` do artefato, nos dois temas, e reproduzem
os casos `visual` das vitrines.

**Testes** — `kit-cobertura.test.ts`; os demais são das tarefas de
componente.

**Riscos e perguntas em aberto** — O artefato é editado por mais gente (tipo
Design System): a aplicação deve reler os arquivos na hora. A maintainer pode
preferir manter o artefato como está e aceitar a divergência documentada.

**Instruções para o agente implementador** — Branch `trm-036-docs-kit`,
depois de 030–035 e 037 mergeadas. Não edite S1–S10/U1–U14; não publique no
artefato; não crie checklist paralelo ao de TRM-003.

---

### TRM-037 — `Recolhivel`: o `<details>` do kit (promove o `SumarioLinha`) — tarefa nova

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** P
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System + UI/UX
**Depende de:** TRM-001, TRM-003 · **Desbloqueia:** TRM-032, TRM-033, TRM-034, TRM-040 (troca do `SumarioLinha` local)

**Problema** — O padrão `<details>` com cabeçalho de `Linha` (UI-012) existe só
dentro da página da proposição (`app/proposicoes/[id]/page.tsx:39-50`,
`SumarioLinha`). Este épico precisa dele em quatro lugares ("Como sabemos",
"Todos os registros", detalhes do rito, página) — S1 diz que padrão repetido
vira componente.

**Oportunidade** — Um recolhível nativo (funciona sem JavaScript, teclado e
leitor de tela de graça), igual em todo o site.

**Solução** — `components/ui/Recolhivel.tsx` (servidor):

```ts
export interface RecolhivelProps
  extends Omit<React.ComponentPropsWithoutRef<"details">, "title" | "children" | "open"> {
  titulo: React.ReactNode;
  sub?: React.ReactNode;
  /** `linha` (padrão): cabeçalho com cara de Linha, 56 px. `discreto`: texto 15 px com chevron, para notas ("Como sabemos"). */
  variante?: "linha" | "discreto";
  /** Começa aberto. */
  aberto?: boolean;
  children: React.ReactNode;
}
export function Recolhivel(props: RecolhivelProps): JSX.Element;
/** Só o <summary>, para quem precisa de <details> próprio (ex.: TodosOsRegistros, que reage ao abrir). */
export function SumarioRecolhivel(props: { titulo: React.ReactNode; sub?: React.ReactNode; variante?: "linha" | "discreto" }): JSX.Element;
```

- `linha`: as classes do `SumarioLinha` atual (copiar de `page.tsx:41-49`),
  `Icone chevron-baixo` que gira 180°.
- `discreto`: `inline-flex items-center gap-1.5 min-h-6 text-texto-s
  font-medium text-zil-texto-2 hover:text-zil-texto cursor-pointer list-none
  [&::-webkit-details-marker]:hidden`, `Icone chevron-direita tamanho="s"`
  que gira 90°; conteúdo em `mt-3 pl-[22px]`.
- Rotação por `[&[open]>summary_svg]:rotate-…` no `<details>` (não
  `group-open`, que vaza para recolhíveis aninhados), com
  `transition-transform duration-padrao ease-padrao`.
- `globals.css` (`@layer base`), vindo de TRM-035 porque esta tarefa mergeia
  primeiro e 030/032/033/034 já testam foco e âncora (UX-DS-22): `html {
  scroll-padding-top: 5rem; }` e, abaixo de `md`, `html { scroll-padding-bottom:
  6rem; }` — âncoras e foco não ficam sob a NavBar fixa nem sob a tab bar
  (2.4.11).

**Escopo** — Dentro: componente, `scroll-padding` global, vitrine
`app/kit/recolhivel`, testes, README. Fora: trocar o `SumarioLinha` em `app/proposicoes/[id]/page.tsx` —
arquivo quente (spec §5.4: #49 → 015 → 040…); a troca é da TRM-040 (ou da
015, se a 037 já estiver no `main`).

**Specs de design** — Estados: fechado, aberto, hover (`linha`: fundo
`superficie-2`; `discreto`: texto `texto`), foco (contorno global no
`summary`), pressionado (`linha`: `superficie-3`). Responsivo: igual nas três
larguras. A11y: `<details>/<summary>` nativos; o `summary` tem texto
descritivo (U10); sem `aria-*` extra. Tokens: os do `SumarioLinha`. Exemplos:
`linha-fechado`, `linha-aberto` (`visual`), `discreto` ("Como sabemos",
`visual`), `aninhado` (prova que o chevron interno não gira com o externo).

**Critérios de aceite**

1. HTML do servidor contém `<details>` e `<summary>` (funciona sem JS).
2. Enter e Espaço no `summary` abrem e fecham (e2e).
3. No caso `aninhado`, abrir o externo não gira o chevron do interno.
4. axe 0 em 3 larguras × 2 temas; jest-axe 0 por variante.
5. Com a NavBar fixa, levar o foco por teclado ao último `summary` da vitrine
   (rolando) deixa o elemento fora do retângulo da NavBar
   (`focoVisivelENaoEncoberto`, TRM-001).

**Testes** — `tests/componentes/Recolhivel.test.tsx`;
`tests/e2e/kit/recolhivel.spec.ts`.

**Riscos e perguntas em aberto** — Nenhum relevante.

**Instruções para o agente implementador** — Branch `trm-037-recolhivel`,
primeiro PR da onda 1 do DS. Não mexa em páginas.

---

### TRM-038 — Zerar as violações de acessibilidade conhecidas das páginas existentes — tarefa nova

**Revisão:** UI/UX ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E3 Componentes · **Prioridade:** P2 · **Horizonte:** Em seguida · **Estimativa:** M
**Dono da spec:** Design System · **Revisões obrigatórias:** Design System + UI/UX
**Depende de:** TRM-001-B; depois de TRM-015/016 e, para `/proposicoes`, de TRM-043 (que separa a página em servidor + cliente) — para não disputar `app/proposicoes/**` · **Desbloqueia:** M11 (0 violações) nas rotas antigas

**Problema** — TRM-001 cria a catraca `tests/e2e/a11y-conhecidas.ts`, que
aceita as violações que as páginas de hoje já têm, para não travar a CI. Sem
uma tarefa para esvaziá-la, a exceção vira permanente. Suspeitas já vistas no
código: `Lista`/`Linha` sem semântica de lista (`Lista.tsx:18`); foco que pode
ficar sob a NavBar fixa (`NavBar.tsx:42`, `sticky top-0`; parcialmente
resolvido pelo `scroll-padding` de TRM-035); `Selo` com texto só no `title`.

**Solução** — Cobrir no e2e, com fixtures, as rotas `/`, `/proposicoes`,
`/proposicoes/[id]`, `/votacoes/[id]`, `/bussula`, `/metodologia`,
`/manifesto` (as de ranking ficam fora enquanto a flag estiver desligada) e
corrigir cada violação na origem (kit primeiro), apagando a entrada da
catraca no mesmo PR. Conferir também o nome acessível do cartão-link da lista
(resolvido em TRM-016 com `aria-labelledby`/`aria-describedby`). `Lista` ganha `role="list"` e `Linha` `role="listitem"`
(ou `as="ul"`/`"li"`), sem mudar a aparência.

**Oportunidade** — As páginas que o cidadão já usa passam a cumprir WCAG 2.2
AA de fato, não só as novas.

**Escopo** — Dentro: e2e das 7 rotas e correções mínimas. Fora: redesenho de
página; rotas de ranking.

**Critérios de aceite** — `CONHECIDAS` vazio; as 7 rotas no e2e em 3 larguras
× 2 temas com 0 violações; nenhuma baseline `@visual` alterada sem
justificativa.

**Specs técnicas / de design / testes** — `tests/e2e/paginas/<rota>.spec.ts`
no molde de TRM-001 (com fixtures em `tests/fixtures/api/`); correções no kit
com teste de componente para a regra corrigida. Comando: `npm run test:e2e --
paginas/`.

**Riscos e perguntas em aberto** — Algumas violações podem exigir mudança de
aparência (contraste): cada uma vai à maintainer com captura antes/depois.

**Instruções para o agente implementador** — Branch
`trm-038-a11y-conhecidas`; um commit por regra; não reescreva página — só o
necessário para a regra passar.

---

## 3. Ordem de implementação e paralelização

Alinhada às ondas de `spec.md` §5.1 e à ordem de arquivos quentes de §5.4,
com TRM-037 incluída (proposta de nova ordem para `components/ui/index.ts` e
README do kit: **#48 → 037 → 030 → 031 → 032 → 033 → 035 → 034 → 036**).

| Onda (spec) | DS — em sequência | DS — em paralelo | Condição |
| --- | --- | --- | --- |
| 0 | 001-A → 001-B | — | TRM-003 (PM) em paralelo; 001-A já destrava testes de componente |
| 1 | 037 (P) primeiro; 031-A (P) junto | depois: 030, 031-B, 035 (três agentes, worktrees próprias) | 001-B mergeada; #48 mergeado ou rebase |
| 1 | — | 032 e 033 assim que 037 entrar | |
| 2 | 034-A | — | 030, 031, 037 mergeadas |
| 3 | — | 038 (opcional aqui) | depois de 015/016 |
| 4 | 034-B; 036 | — | 034-B depois de TRM-028; 036 depois de 030–035 |

Trabalho em paralelo, merge em fila: os conflitos esperados são só linhas
acrescentadas em `index.ts`, README do kit, `app/kit/page.tsx`,
`docs/CHANGELOG.md`; `Tempo.tsx` é tocado por 030 (sai o `Etapas`) e 032
(muda o `Marco`) — 032 rebaseia sobre 030. `globals.css`: 030
(`.zil-tracejado`) e 035 (`scroll-padding`). `Icone.tsx`: só 031.

Capacidade: com dois agentes de DS (como o PM prevê), onda 1 = agente 1: 037 →
030 → 032; agente 2: 031-A → 031-B → 035 → 033.

---

## 4. O que as páginas (UI/UX) consomem

| Tarefa | Componentes | Uso que a UI/UX deve respeitar | Precisa de |
| --- | --- | --- | --- |
| TRM-015 página v0 | `Button` ("Ver na Câmara" + `Icone externo` + "(abre em nova aba)" só para leitor), `Aviso`, `Recolhivel` (se 037 já estiver no `main`) | Situação oficial é **texto**, não `Selo` (U5); sem cor | 001, 003 |
| TRM-016 lista v0 | `Card`, texto para a situação | Sem `line-clamp` na situação; "Última movimentação em" em `text-texto-s zil-num` | 001, 003 |
| TRM-040 Onde está | `FaseSelo`, `Etapas variante="compacta"`, `legendaDasEtapas`, `ComoSabemos` + `comoSabemosDaFase`, `TermoGlossario` + `definicaoDoTermo`, `Aviso` (apensada), `Recolhivel`, `FaseSeloEsqueleto`, `EtapasEsqueleto` | `rotulo={fase_rotulo}` sem montar texto; `href="/como-vira-lei#fase-<fase>"`; datas via `dataBR`; troca o `SumarioLinha` local por `Recolhivel` | 030, 031, 033, 035, 037 |
| TRM-041 O que aconteceu | `LinhaDoTempo aria-labelledby`, `Marco`, `MarcoEsqueleto`, `TodosOsRegistros`, `Vazio`, `Paginacao` | `tom` **nunca** na tramitação; `atual` só no último marco; `tipo="votacao"` + `href="/votacoes/{votacao_id}"`; `local={`${CASA_ROTULO[casa]} · ${sigla_orgao}`}`; a página busca os eventos em `onAbrir` e controla `estado` | 032 |
| TRM-042 O caminho inteiro | `RitoDiagrama` + `ritoParaDiagrama(rito, { proposicao })` | Sem `contagem`; `nivelTitulo` coerente com a página | 034-A/B |
| TRM-043 lista com fase | `FaseSelo` **sem `href`** (o `Card` já é link), `Chip`/`Chips` com `n` | Nenhum `pontoClassName` de alinhamento nos chips de fase | 031 |
| TRM-044 `/como-vira-lei` | `RitoDiagrama` com `contagens`, `Chips` com `href` para espécie (5 > limite de 4 do `Segmentado`), `Segmentado` ou `Chips` para Casa, `TermoGlossario` | Estado na URL (`?especie=PEC&casa=senado`), link compartilhável; âncoras `fase-*` | 034, 035 |
| TRM-045 situações | `GlossarioLista` + `entradaDaApi`, `extra={<FaseSelo …/>}`, `Busca` | Âncora `termo-<chave>`; nunca texto não aprovado | 035, 031 |
| TRM-046 matriz | todos | Validar os textos padrão abaixo | 030–035 |
| TRM-047 metodologia | nenhum componente do épico: texto e âncoras (spec.md §9.3); é só o destino dos links de `ComoSabemos` e do `FaseSelo` | | — |

**Textos padrão dos componentes** (para a matriz de TRM-046 validar ou
trocar; a troca é por prop, sem mexer no kit): `Etapas` — "Etapas da
tramitação", "Etapa i de n: …", "Parou na etapa i de n: …", "… a etapa atual
não foi identificada", "(concluída)", "(etapa atual)", "(ainda não
aconteceu)", "Desde …", "Está aqui", "Dispensada", "Parou aqui", "Não aconteceu". `FaseSelo` —
"Fase: ", "Desfecho: ", "Em conjunto", "Tramita em conjunto com a proposição
principal", ", entenda esta fase", ", entenda este desfecho", ", entenda por
quê". `Marco`/`TodosOsRegistros` — "Votação: ", "(mais recente)", "(abre em
nova aba)", "Todos os N registros", "1 registro", "No texto original da
Câmara dos Deputados", "Carregando os registros.", "N registros carregados.",
"Não conseguimos carregar os registros.", "Os marcos acima continuam valendo.",
"Tentar de novo", "Documento". `ComoSabemos` — "Como sabemos", "Fontes",
"Conferido em …", "Sem endereço público", resumo "Leitura do ZIL, conferida na
Câmara em {data}". `TermoGlossario` — sufixo lido ", o que quer dizer". `RitoDiagrama` — "Está
aqui", "Parou aqui", "Dispensada", "Foi o que aconteceu", "Pode terminar aqui", "A
qualquer momento", "Desfechos possíveis em qualquer etapa", "Explicação ainda
não publicada.", "Como ler os prazos", "Prazo:", "Quem decide:", "Base:", as três classes
de prazo ("fixado na regra", "fixado na regra, mas costuma não ser cumprido",
"sem prazo fixo"), "N proposições acompanhadas estão aqui agora →". Glossário — "Ver no
glossário", "Texto do ZIL, não oficial." (nota do termo e da lista), "Sem explicação
ainda.", "Termo
oficial". Vitrine — "Exemplos de demonstração".

---

## 5. Conflitos e perguntas para os outros especialistas

Estado em 2026-10-30, depois da rodada 2 (backlog-dados.md §1.5/§7 e
backlog-interface.md §0 e §6).

| # | Para | Ponto | Situação |
| --- | --- | --- | --- |
| 1 | Arquitetura | `fase_rotulo` nunca nulo, inclusive desfecho e `nao_sabemos` ("Fase não identificada") | **Resolvido** (dados §1.5, §7-2) |
| 2 | Arquitetura + PM | `recem_apresentada` | **Resolvido**: `apresentada` + `fase_motivo` (dados §7-4) |
| 3 | Arquitetura | `etapas[].id`/`fase`/`nota`, `casa` como `CasaRito`, `fase_motivo`, `fase` nula com desfecho | **Resolvido**; tipos em TRM-031-A |
| 4 | Arquitetura | `como_sabemos` (`regra_descricao`, `versao_publicada`, `fontes[{rotulo,url}]`) | **Resolvido**; adaptador de TRM-033 ajustado |
| 5 | Arquitetura | Forma de `/tramitacao/mapa` | **Resolvido**: nomes de dados §7-6 (`o_que_acontece`, `condicao`, desfecho `{desfecho, rotulo, texto, a_partir_de}`); modelo de vista da TRM-034 renomeado igual |
| 6 | Arquitetura | Texto não aprovado | **Resolvido**: API manda nulo; o front filtra por `publicavel` |
| 7 | PM (TRM-003) | S4 sem `neutro`; S3 sem a exceção de valor de dado | **Resolvido** no spec.md (consolidação): S3 aceita `style={}` só para valor de dado, com comentário; S4 proíbe também `zil-neutro` (âmbar) em fase e status |
| 8 | PM | Índice sem TRM-037/038; dependências 032/033/034 → 037, 034 → 031; 031 = M | **Resolvido** no índice do spec.md (037, 038, 031-A/B, 034-A/B e as dependências) |
| 9 | UI/UX | Fase sem cor; `FaseSelo` sem `href` em cartão-link; espécies em `Chips` | **Resolvido** (interface §0.5, §1.4) |
| 10 | Arquitetura (TRM-002) | Fixtures da API do ZIL gravadas da FastAPI | **Resolvido**: TRM-028, critério 9 (`scripts/gerar_fixtures_frontend.py` → `apps/web/tests/fixtures/api/tramitacao/gerado/`), fonte das fixtures de tramitação da TRM-001 em diante |
| 11 | Revisão do PR #48 | `Histograma` destaca "você está aqui" com `--alinhado` | Aberto |
| 12 | Arquitetura | Node 22 na CI e no `Dockerfile` | **Aprovado** (revisão da Arquitetura, item 15); passo manual no PR de 001-A: Node 22.x nas configurações do projeto na Vercel antes do merge (item 16) |
| 13 | Arquitetura × UI/UX | Âncora do glossário | **Resolvido**: `#termo-<chave>` nos três arquivos |
| 14 | UI/UX | Helper de paginação nas fixtures | **Resolvido**: `api.responderPaginas` + `api.chamadas` na API falsa de TRM-001; `tests/e2e/helpers/lista.ts` não é criado |
| 15 | UI/UX | `/como-vira-lei` e `/situacoes` buscam no cliente (S9) | **Exceção aceita**, com condições e gatilho de revisão (§1.4) |
| 16 | UI/UX | `abertoInicial`, classe X sem "discricionária", nota "Texto do ZIL, não oficial." | **Aplicado** (TRM-035, TRM-034) |
| 17 | Arquitetura | `datetime` serializado em `-03:00` | Deixou de bloquear: `dataBR` converte data com hora para `America/Sao_Paulo` (UX-DS-04) |
| 18 | UI/UX | Revisão `revisoes/uiux-sobre-design-system.md` (UX-DS-01 a 37) | Aplicados: 01–06, 08–27, 29–32, 35–37. Fora: 33 (`abrirSeAlvo` deixaria o `Recolhivel` cliente; fica na página, TRM-045), 34 (opcional; o padrão `toMatchAriaSnapshot` entra no README de testes) |
| 19 | UI/UX | Textos curtos das classes de prazo | **Resolvido**: decisão da UI/UX — D "fixado na regra", D\* "fixado na regra, mas costuma não ser cumprido", X "sem prazo fixo"; aplicado no `RitoDiagrama` (linha de prazo e legenda) |
| 20 | UI/UX | Matriz E01/E02 ainda diz "Pulada" e "Agora"; o kit passou a "Dispensada" e "Está aqui" (pedidos UX-DS-11 e 31) | A UI/UX atualiza a matriz |
| 21 | UI/UX | I14 (erro dos registros) listado como `Aviso` `contra`; o kit usa `padrao` (falha parcial, regra da própria interface §0.5-2) | A UI/UX atualiza a matriz |
| 22 | Arquitetura | Revisão `revisoes/arquitetura-sobre-interface-e-ds.md`, itens que tocam o DS (1, 4, 6, 14–17, 19, 20) | Aplicados: CORS e preflight na API falsa (1); `entradaDaSituacao` por chave (4); tipos (`reversivel` removido; `acompanhada`, `situacao_glossario`, `situacoes_camara`; campos de `lib/api.ts` anotados para a UI/UX) (6); exemplo do `FaseSelo` (14); Node 22 + Vercel (15, 16); fixtures geradas (17). 19 e 20 sem ação |
| 23 | UI/UX | Link do selo em `nao_sabemos` | **Resolvido** pela UI/UX: link para `/metodologia#tramitacao` só no cabeçalho, com o sufixo lido ", entenda por quê"; sem link na lista. Refletido no exemplo, nos testes e na vitrine de TRM-031 |

---

## 6. Resumo

Este arquivo especifica TRM-001 (infra de testes do frontend, em dois PRs) e
os componentes TRM-030 a TRM-036, e cria **TRM-037** (`Recolhivel`, promove o
`SumarioLinha`; P1, P) e **TRM-038** (zerar as violações de a11y conhecidas
das páginas antigas; P2, M). Decisões: fase e status sem matiz (verde,
vermelho e âmbar ficam para alinhamento e "não validado"); estado por texto e
forma; tudo no kit; `Etapas` sem animação e vertical abaixo de `md`;
`RitoDiagrama` em HTML semântico; `TermoGlossario` como disclosure; testes com
Vitest + Testing Library + jest-axe e Playwright + axe em 375/768/1280 × 2
temas, mock da API por `page.route()`, regressão visual só nas vitrines do
kit; scripts `npm run test` e `npm run test:e2e` (os do PM); Node 22.

APIs que a UI/UX deve respeitar (nomes finais, alinhados a backlog-dados.md §1.5/§7):

- `FaseSelo({ fase: Fase | "nao_sabemos" | null, desfecho?, rotulo, motivo?, apensada?, href?, id? })` —
  `rotulo` = `fase_rotulo` (nunca nulo); `fase` nula só com desfecho;
  `mapa_nao_aprovado` e `recem_apresentada` neutros; sem `href` dentro de
  `Card` com `href`.
- `Etapas({ etapas: { id, nome, estado, quando?, casa?, nota?, href? }[], variante?: "completa" | "compacta", orientacao?, rotulo? })` + `legendaDasEtapas` — `quando` só a data (o kit escreve "Desde"); a compacta também é `<ol>` com `aria-current`; mais de 7 etapas = vertical.
- `Marco({ quando, titulo, local?, atual?, tipo?, href?, documento?, tom? })` — `tom` nunca na tramitação — + `marcoDaApi`; `TodosOsRegistros({ total, estado, registros?, onAbrir?, onTentarDeNovo?, erro?, rodape?, fonte?, focarAoTrocar? })` + `registroDoEvento` (só data, erro `padrao` com "Tentar de novo").
- `ComoSabemos({ resumo?, itens?, fontes: [≥1], conferidoEm?, nota?, saibaMais?, variante? })` + `comoSabemosDaFase` + `dataBR`.
- `RitoDiagrama({ titulo, etapas: EtapaRito[], desfechosGerais?, nivelTitulo?, legenda?, textoPendente? })`, com `EtapaRito { id, fase, nome, casa?, oQueAcontece, quemDecide?, prazo?, opcional?, condicao?, ramos?: { desfecho, rotulo, texto, baseLegal?, ocorreu? }[], estado?, quando?, nota?, ancora?, contagem? }` + `ritoParaDiagrama(rito, { proposicao?, contagens?, hrefContagem?, titulo? })`.
- `TermoGlossario({ children, definicao?, titulo?, baseLegal?, href?, nota?, abertoInicial?, rotuloAcao?, indicador? })`; `GlossarioLista({ entradas, nivelTitulo?, prefixoAncora?, semTexto?, nota? })` + `entradaDaApi`, `definicaoDoTermo` (usa `texto_curto`), `entradaDaSituacao`, `hrefDoTermo` (âncora `termo-<chave>`); nota padrão "Texto do ZIL, não oficial.".
- `Recolhivel({ titulo, sub?, variante?, aberto? })` + `SumarioRecolhivel`; o `scroll-padding` global entra com ele.
- Testes: `npm run test`, `npm run test:e2e`; API falsa com CORS, `responder` (aceita função da URL e `cabecalhos`), `responderPaginas`, `chamadas`; helpers `focoVisivelENaoEncoberto`, projeto `reflow-320` (`@reflow`); fixtures de tramitação geradas em `apps/web/tests/fixtures/api/tramitacao/gerado/` (TRM-028).
- Glossário: a situação oficial acha a definição por `situacao_glossario` (chave da API), nunca por texto.

Conflitos que continuam abertos (§5): texto de S2/S3/S4 no checklist (PM),
índice do PM sem 037/038, `Histograma` do PR #48, matriz da UI/UX a atualizar
(E01/E02/I14). Resolvidos: fixtures geradas da FastAPI (TRM-028), Node 22
(com o passo da Vercel), `datetime` em `-03:00`, âncora `#termo-<chave>`,
CORS da API falsa, textos curtos das classes de prazo e o link do selo em
`nao_sabemos` (só no cabeçalho).

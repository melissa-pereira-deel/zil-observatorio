# Spec 013 — Tramitação · Backlog de interface (UI/UX)

**Data:** 2026-10-30
**Estado:** proposta para revisão (PM, Arquitetura, Design System e maintainer).
**Dono deste arquivo:** UI/UX Interaction Design Engineering.
**Arquivos irmãos:** [spec.md](spec.md) (Product: índice, ondas, gates, TRM-023/029, TRM-047) ·
[backlog-dados.md](backlog-dados.md) (Arquitetura) ·
[backlog-design-system.md](backlog-design-system.md) (Design System).
**Discovery:** [docs/DISCOVERY-TRAMITACAO.md](../../docs/DISCOVERY-TRAMITACAO.md) — citado como "disc. §N".

Este arquivo especifica: a arquitetura de informação das superfícies de
tramitação; o inventário de componentes que a interface espera do kit; o guia
de redação e o conteúdo do glossário (TRM-022); as tarefas de interface
TRM-015, TRM-016, TRM-040 a TRM-046; e a matriz única de estados e textos
(TRM-046, §4). Prioridade, onda e gates seguem [spec.md](spec.md) §4, §5 e §7 —
não são repetidos aqui, só referenciados.

Convenções: `arquivo:linha` para o repositório; "acompanhadas" = proposições no
banco do ZIL; `{campo}` = valor vindo da API dentro de um texto exato; aspas
curvas “ ” fazem parte do texto quando aparecem dentro de um texto exato.

---

## 0. Bases comuns a todas as tarefas de interface

### 0.1 O que a interface consome

Os contratos são os de backlog-dados.md §1.5 (nomes finais em §7 de lá);
esta parte os consome sem renomear. Abaixo, o que cada superfície lê e os
**pedidos** que ainda faltam (marcados).

**`ProposicaoRead` — F0 (TRM-014)**

| Campo | Uso aqui |
| --- | --- |
| `situacao` | situação oficial, inteira (`F01`) |
| `situacao_estado` ∈ `informada` · `recem_apresentada` · `sem_situacao` · `nao_sincronizada` | escolhe `F01`/`F02`/`F03`/`F13` — **a interface não calcula "recém"** |
| `orgao_efetivo_sigla`, `orgao_efetivo_nome` | "Órgão atual" (`F10`). **Não** `sigla_orgao`/`orgao_nome`: esses são o órgão do último registro, que em 23 das 240 acompanhadas é CCP ou MESA para proposição que está numa comissão (revisão da Arquitetura, item 2) |
| `regime`, `regime_texto` (`texto_curto` do glossário, só se publicável — lote L0) | linha "Regime" (`F07a`/`F07b`) |
| `apreciacao`, `apreciacao_texto` | linha "Quem decide" (`F07a`/`F07b`; combinação com urgência: §2.7) |
| `relator_nome` | "Relatoria", texto (`F12`) |
| `ultima_movimentacao_em` | "Última movimentação" e ordenação |
| `detalhe_sincronizado_em` | "Conferido na Câmara em" (`F09`) |
| `url_camara` | "Ver na Câmara" (`X01`) |
| `principal_url_camara` | "Tramita junto com" em F0 (`F11`): link pronto da API, a interface não monta URL |
| `situacao_glossario` | chave da entrada do glossário da situação oficial (nunca casar por texto); usada no fallback `N06` |
| `norma: NormaResumo` (`tipo`, `rotulo`, `veto`, `url_normas_leg`, `url_planalto`) | "Virou lei: Lei 14.871/2024" (`F04`) |
| `regime_chave`, `apreciacao_chave`, `cod_situacao`, `sigla_orgao`, `orgao_nome`, `principal_fonte_id` | não usados na tela |
| cabeçalho `X-Total-Count` de `GET /proposicoes` | total da lista (TRM-016); legível porque a API e a API falsa expõem o cabeçalho (CORS) |

**Por que F0 não tem "desde".** `statusProposicao.dataHora` é a data do
**último registro** da tramitação, não a do início da situação. Exemplo real:
o PL 2314/2026 está em "Aguardando Parecer" e o último registro é "Encerramento
de Prazo", em 01/09/2026 — a situação começou antes. Escrever "desde
01/09/2026" seria falso. Em F0 a página diz "Última movimentação em"; "desde"
só aparece em F1, na `frase` da API, com `orgao_desde` (chegada ao órgão) ou
`desde` (início da fase), calculados do histórico (TRM-026/027).

**`ProposicaoRead` — F1 (TRM-028)**: `fase` (pode ser nula: não calculada, ou
desfecho sem "onde parou"), `fase_rotulo` (texto do `FaseSelo`; nulo só se a
fase não foi calculada; em `nao_sabemos` é a constante "Fase não
identificada", `N00`), `fase_motivo`, `desfecho`, `desfecho_rotulo`,
`apensada`, `casa_iniciadora`.

**`GET /proposicoes/{id}/tramitacao` (`TramitacaoRead`)**: `onde_esta`
(`fase` nula só com desfecho; `fase_rotulo` nunca nulo; `fase_motivo`;
`desfecho`, `desfecho_rotulo`; `apensada`; `herdada_de: { id, fonte_id,
rotulo, url_camara, acompanhada }`; `casa`; `sigla_orgao`, `orgao_nome` (aqui
já são o órgão efetivo); `desde`, `orgao_desde`; `situacao_oficial`,
`situacao_glossario`; `regime_texto`, `apreciacao_texto`;
`relator: { nome, partido, uf, parlamentar_id }`; `frase` — nula em
`nao_sabemos`; `como_sabemos: { regra, regra_descricao, versao_publicada,
fontes: { rotulo, url }[], conferido_em }`), `etapas[]` (`id, nome, fase,
estado, quando, casa, nota`; vazia em `nao_sabemos`, com fase nula ou rito
não publicável), `marcos[]`, `eventos_total`, `rito: { chave, especie,
casa_iniciadora }`.

**Explicação da fase, do desfecho e da apensada**: não vem em `onde_esta`;
vem do glossário de `/tramitacao/mapa`, pelas chaves fixas `fase_<fase>`,
`desfecho_<desfecho>` e `apensada` (backlog-dados.md §7-7).

**`GET /proposicoes/{id}/tramitacao/eventos?page=&per_page=`**:
`{ items: EventoRead[], total, page, per_page, pages }` (em `tipos.ts`:
`PaginaEventosApi`/`EventoApi`), do mais recente para o mais antigo;
`EventoRead = { casa, sequencia, data_hora, sigla_orgao,
descricao, despacho, url, marco }`.

**`GET /tramitacao/mapa` (`MapaRead`)**: `versao_publicada`, `aviso`,
`fases[]`, `desfechos[]` (`rotulo`, `base_legal`), `especies[]` (`descricao`
= `texto_curto` de `glossario/especie_<sigla>`; `ritos[]` com `publicavel`,
`revisao`, `etapas[]` — vazia se não publicável — com `o_que_acontece`,
`quem_decide`, `prazo { classe, texto }`, `base_legal { rotulo, url }`,
`opcional`, `condicao`; `desfechos[] { desfecho, rotulo, texto, base_legal,
a_partir_de }`), `glossario[]` (`chave` snake_case, `tipo` ∈ situacao ·
regime · apreciacao · fase · desfecho · apensada · etapa · especie · conceito,
`termo`, `codigo`/`codigos`, `fase`, `publicavel`, `texto_curto` ≤ 160,
`texto` ≤ 900, `base_legal`), `situacoes_camara: { codigo: string; descricao;
glossario: string | null; tratada: boolean }[]`. Texto não publicável vem
nulo. A interface acha a explicação de uma situação **pela chave pronta**
(`situacao_glossario`), nunca comparando texto (o oficial tem variações e há
códigos com o mesmo nome), e agrupa pelo `tipo`.

**Pedidos à Arquitetura — atendidos na rodada 2** (backlog-dados §1.5;
revisão da Arquitetura, item 12):
1. Urgência + apreciação conclusiva → `apreciacao_texto` de
   `apreciacao_conclusiva_com_urgencia`, ou nulo; nunca o da conclusiva pura
   (§2.7; 9 casos confirmados).
2. `mapa.situacoes_camara` (com `glossario` e `tratada`), para
   `/como-vira-lei/situacoes` dizer quantas faltam.
3. `datetime` serializado com `-03:00`; `dataBR` fatia os 10 primeiros
   caracteres de `date` e `datetime`.
4. Âncora do glossário: **`#termo-<chave>`** (`hrefDoTermo` do kit); a
   Arquitetura alinha o §7 dela.
5. `base_legal_motivo` aceito para situação administrativa (V-R7); `regime`
   "." e `apreciacao` "Indefinida" chegam nulos.

**Listas.** `GET /proposicoes` aceita `ordem=movimentacao` (TRM-014) e
`fase`/`desfecho` (TRM-028), e existe `GET /tramitacao/contagem`. A lista v0
ainda carrega todas as páginas (TRM-016), porque a busca textual e o filtro
"Análise" são no cliente e as contagens precisam bater com eles; o caminho
pelo servidor fica registrado como risco em TRM-043.

### 0.2 Tipos TypeScript

Os tipos do contrato moram em `apps/web/lib/tramitacao/tipos.ts`, criado
pelo DS em TRM-031-A e ajustado no PR de TRM-028 com os nomes de
backlog-dados.md §1.5: `OndeEstaApi` (`fase` anulável, `situacao_glossario`),
`HerdadaDeApi` (com `acompanhada`), `RitoRefApi` (`chave`, `especie`,
`casa_iniciadora: CasaRito`, que inclui `congresso` para MPV), `MarcoApi`,
`EventoApi`/`PaginaEventosApi` (`items`), `ComoSabemosApi`
(`versao_publicada`), `GlossarioApi` (`tipo`, `texto_curto`, `publicavel`),
`RitoApi`, `MapaApi` (`situacoes_camara`). Esta parte **não** declara tipos de
API próprios e usa sempre esses nomes. `apps/web/lib/api.ts`: a interface
`Proposicao` ganha os campos de §0.1 como **opcionais** (`?:`), inclusive
`orgao_efetivo_sigla`, `orgao_efetivo_nome`, `principal_url_camara` e
`situacao_glossario`, para a página não quebrar contra uma API anterior a
TRM-014/028.

### 0.3 De onde vem cada texto

Uma regra só, para nenhum texto ter duas fontes:

| Texto | Fonte | Quem aprova |
| --- | --- | --- |
| Situação oficial, regime e apreciação oficiais, despacho, descrição de cada registro | API da Câmara, sem edição | — (é a fonte) |
| `fase_rotulo`, `frase`, `regime_texto`, `apreciacao_texto`, títulos dos marcos, etapas e desfechos do rito, glossário | API do ZIL, a partir de `data/tramitacao/` (só entradas publicáveis) | pipeline de TRM-023 + maintainer (lotes de TRM-029) |
| Estados de interface (carregando, erro, vazio), textos de F0 sem mapa, **os textos de `nao_sabemos` por motivo**, rótulos de filtro e de ordenação, textos fixos de seção, textos que trocam o padrão de um componente do kit (por prop) | `apps/web/lib/tramitacao/textos.ts` (TRM-046), idênticos à matriz de §4 | maintainer, no PR de TRM-046 (gate U3) |
| Textos padrão dos componentes do kit ("Etapa i de n: …", "Pode terminar aqui", "Como sabemos") | o próprio componente (DS, backlog-design-system.md §4) | validados na matriz (§4, coluna "Fonte" = kit) |

Os textos de `nao_sabemos` ficam no frontend de propósito: aparecem
justamente quando o mapa não tem entrada aprovada — se dependessem do mapa,
não haveria o que mostrar no caso `mapa_nao_aprovado`. O rótulo do selo
("Fase não identificada") é o único texto que a API e a matriz escrevem
iguais; um teste de contrato de TRM-028 confere.

Nenhum texto desta parte é gerado por LLM em tempo de execução. Rascunhos podem
ser escritos com ajuda de agentes; vai ao ar o que passou por TRM-023 (mapa e
glossário) ou pelo PR revisado pela maintainer (`textos.ts`).

**Nenhuma condição de status é calculada no frontend** (spec.md §3, princípio
9): até "recém-apresentada" vem pronta da API (`situacao_estado`, TRM-014; R9
em F1). A interface só escolhe qual texto da matriz mostrar para cada valor
que recebe.

### 0.4 Infra de teste e fixtures

**Infra de TRM-001 (backlog-design-system.md, TRM-001), usada como está.**
`npm run test` (Vitest + Testing Library + jest-axe, jsdom) e `npm run test:e2e`
(Playwright + `@axe-core/playwright`, projetos 375 × 812, 768 × 1024,
1280 × 800, temas escuro e claro). Pastas e helpers do DS:

| Para | Onde / helper |
| --- | --- |
| Teste de componente de domínio desta parte | `apps/web/tests/componentes/tramitacao/<Componente>.test.tsx` |
| Funções puras (`lib/tramitacao/*`) | `apps/web/tests/unit/tramitacao/<arquivo>.test.ts` |
| E2E de página | `apps/web/tests/e2e/paginas/<rota>.spec.ts`, com `test`/`expect` de `tests/e2e/helpers/teste.ts` |
| API falsa | `instalarApiFalsa` (`API = "http://api.zil.test"`, `page.route()`, com CORS e `X-Total-Count` expostos): `api.responder("/proposicoes/<id>/tramitacao", "<fixture>")`, `{ status: 500 }` ou uma função da URL; `api.responderPaginas(rota, [fixtures], { alem?, falharNaPagina? })` para listas paginadas; `api.chamadas` para contar requisições; rota sem fixture responde 599 e o teste falha. **Nenhuma tarefa desta parte cria helper de paginação próprio** |
| Fixtures | `apps/web/tests/fixtures/api/**.json` |
| Acessibilidade | `semViolacoes(page, { rota, tema })` (tags `wcag2a`…`wcag22aa`; JSON em `evidencias/a11y/`) |
| Layout | `semRolagemHorizontal(page)` — em todo `tests/e2e/paginas/*.spec.ts` este teste leva a tag `@reflow` e roda também no projeto `reflow-320` (WCAG 1.4.10) |
| Foco (U9) | `focoVisivelENaoEncoberto(page, locator)` — contorno visível e fora das duas navegações fixas (2.4.7, 2.4.11); nenhum spec desta parte mede retângulos à mão |
| Paleta | `expectPaletaNeutra(page, seletor)` (falha com `--alinhado`, `--contra`, `--neutro` e os `-fundo`); `classesDeAlinhamento(raiz)` no Vitest |
| Movimento | `animacoesInfinitas(page, seletor)` → 0 |
| Prova (spec.md §7.4) | `registrarEvidencia(page, nome, tema)` → `evidencias/<projeto>/<tema>/<nome>.png`, publicado pela CI no artefato `evidencias-ui` |

**Todas as páginas desta parte buscam a API no navegador** (componente
cliente com `fetch`), como as páginas atuais — é o que o `page.route()`
intercepta. Onde a página não tem interação (`/como-vira-lei`,
`/situacoes`), isso contraria a letra de S9; o desvio é deliberado e
registrado: o `page.tsx` é Server Component (casca, `metadata`, `Suspense`) e
só o filho que busca dados é cliente. Quando existir o servidor de fixtures
que o DS descreve como risco futuro de TRM-001, as duas páginas podem buscar
no servidor sem mudar a interface.

**Fixtures de interface (criadas em TRM-046-B, em `apps/web/tests/fixtures/api/tramitacao/`**
— sempre com o caminho inteiro: na raiz do repositório existe
`tests/fixtures/tramitacao/`, que é Python, de TRM-002).
Um UUID fixo por caso (`00000000-0000-4000-8000-0000000000NN`); para cada
caso, `proposicao-NN.json` (`GET /proposicoes/{id}`) e, quando F1,
`tramitacao-NN.json`. "Real" copia os campos da Câmara consultados em
2026-10-30; "sintético" está no nome. Os casos 01–03 trazem
`orgao_efetivo_sigla`/`orgao_efetivo_nome` diferentes de `sigla_orgao` em ao
menos um caso (CCP), para provar que a tela usa o órgão efetivo. Quando
TRM-028 entrar, as fixtures reais são trocadas pelas geradas por
`scripts/gerar_fixtures_frontend.py` em
`apps/web/tests/fixtures/api/tramitacao/gerado/` (respostas reais da FastAPI;
um teste de backend valida também as sintéticas contra os schemas).

| NN | Caso | Base | Estado que exercita |
| --- | --- | --- | --- |
| 01 | `pl-4861-2023-relator-saiu` | PL 4861/2023 | comissões; situação de 83 caracteres; órgão CME |
| 02 | `pl-1264-2024-sem-relator` | PL 1264/2024 | comissões (CFT); "Aguardando Designação de Relator(a)"; prioridade |
| 03 | `pl-5810-2025-pronta-comissao` | PL 5810/2025 | "Pronta para Pauta" em comissão (CICS) |
| 04 | `pl-plenario-pronta-sintetico` | a partir do PL 5941/2013 | "Pronta para Pauta" no Plenário |
| 05 | `pl-5-2025-apensada` | PL 5/2025 → PL 5941/2013 | apensada; principal acompanhada (`herdada_de.id`) |
| 06 | `pl-105-2023-apensada-fora` | PL 105/2023 | apensada; principal só de contexto (`herdada_de.id` preenchido, `acompanhada: false` — D2) |
| 07 | `pl-399-2025-senado` | PL 399/2025 | outra Casa; urgência RICD 155 + apreciação conclusiva |
| 08 | `pl-2-2024-lei` | PL 2/2024 | norma; Lei 14.871/2024; veto parcial; urgência CF 64; 51 registros (`eventos-08-p1.json`, `eventos-08-p2.json`), 6 marcos |
| 09 | `pdl-571-2026-decreto` | PDL 571/2026 | norma; Decreto Legislativo 147/2026 |
| 10 | `pl-norma-sem-numero-sintetico` | — | "Transformado em Norma Jurídica" sem `norma` |
| 11 | `pl-4272-2023-encaminhamento` | PL 4272/2023 | `nao_sabemos(sinais_conflitantes)` |
| 12 | `pl-4867-2026-recem` | PL 4867/2026 | `situacao_estado: recem_apresentada` → `F02` (F0); `apresentada` + `recem_apresentada` (F1) |
| 13 | `pl-situacao-nula-antiga-sintetico` | — | F0: `situacao_estado: sem_situacao` (`F03`); variante `…-nao-sincronizada` (`F13`). F1, pela R9 nova (backlog-dados A20): `…-nula-com-distribuicao` (`fase: "comissoes"`, `fase_motivo: null`, `como_sabemos.regra: "R9"`) e `…-nula-sem-historico` (`nao_sabemos`, `fonte_indisponivel` → `N04`) |
| 14 | `pec-63-2023-chancela` | PEC 63/2023 | apresentada; regime e apreciação indefinidos |
| 15 | `mpv-1196-2023-perdeu-eficacia` | MPV 1196/2023 | desfecho `perdeu_eficacia` |
| 16 | `pl-2040-2026-arquivada` | PL 2040/2026 | desfecho `arquivada` |
| 17 | `pl-823-2025-retirada` | PL 823/2025 | desfecho `retirada` |
| 18–21 | `…-prejudicada`, `…-rejeitada`, `…-vetada`, `…-devolvida` (sintéticos) | — | os outros desfechos |
| 22–25 | `…-sancao`, `…-retorno`, `…-veto-congresso`, `…-promulgacao-pec` (sintéticos) | — | fases que o banco não tem hoje |
| 26–30 | `…-sem-mapa`, `…-principal-nao-resolvida`, `…-fonte-indisponivel`, `…-pln-fora-do-escopo`, `…-mapa-nao-aprovado` (sintéticos) | — | cada motivo de `nao_sabemos` |
| 31 | `pl-sem-marcos-sintetico` | — | `marcos: []`, `eventos_total: 12` |
| 32 | `pl-sem-registros-sintetico` | — | `marcos: []`, `eventos_total: 0` |
| 33 | `pdl-99-2024-regime-sem-entrada` | PDL 99/2024 ("Art. 223 - CF") | regime sem entrada publicável |
| 34 | `pl-onze-marcos-sintetico` | derivado do 08 | 11 marcos (corte em 8) |
| — | `lista-p1.json`, `lista-p2.json` | 130 itens gerados por `apps/web/tests/fixtures/api/tramitacao/montar-lista.mjs` (determinístico; saída versionada) a partir dos casos; servidos com `api.responderPaginas` e `X-Total-Count: 130` | paginação, ordenação, contagem por fase |
| — | `mapa.json` | ritos PL e PLP (Câmara e Senado), PEC (Câmara), MPV (`MPV_CN`, `casa_iniciadora: "congresso"`); PDL com `publicavel: false` e `etapas: []`; glossário com as entradas de §2.6–2.8 (`fase_*`, `desfecho_*`, `apensada`), uma com `texto: null` e uma `aprovado` com `publicavel: false`; `situacoes_camara` com as 99 | glossário, rito, rito em revisão |
| — | `mapa-vazio.json` | `especies: []`, `glossario: []` | nada publicado ainda (`V02`) |

Datas: os e2e fixam o relógio com
`page.clock.setFixedTime(new Date("2026-10-30T12:00:00-03:00"))`; o Vitest usa
`vi.setSystemTime` ou a prop `hoje`.

### 0.5 Regras que valem para toda tarefa desta parte

1. Gates de spec.md §7 (U1–U14, S1–S10) e evidências de §7.4.
2. Nenhuma classe `zil-alinhado*`, `zil-contra*` ou `zil-neutro*` em fase,
   desfecho, etapa, marco ou estado `nao_sabemos` (S4 e decisão 1 do DS:
   fase e status não têm matiz). `Aviso tom="neutro"` (âmbar) não aparece
   nestas superfícies; avisos de `nao_sabemos`, apensada e falha parcial são
   `tom="padrao"`; erro que impede a página é `tom="contra"` (padrão do kit
   para erro de API). Verificado por `expectPaletaNeutra` em todo e2e.
3. Nenhum `animate-*` contínuo; nenhum estilo inline (exceto o já permitido
   pelo kit para valor de dado).
4. Situação oficial nunca dentro de `Selo` e nunca com `truncate`/`line-clamp`.
5. Datas sempre por `dataBR` (DS, TRM-033: fatia a string, sem `Date`), dentro
   de `<time dateTime="aaaa-mm-dd">`. **Defeito encontrado:** `new Date("2024-05-28").toLocaleDateString("pt-BR")`
   devolve "27/05/2024" num navegador em America/Sao_Paulo (string só de data
   é lida como UTC) — "Apresentada em" está um dia atrasado hoje em
   `app/proposicoes/page.tsx:228` e `app/proposicoes/[id]/page.tsx:158`.
   TRM-015 e TRM-016 corrigem nas linhas que tocam.
6. Link externo: texto visível + `<span className="sr-only">` com o que falta
   e "(abre em nova aba)"; `target="_blank" rel="noopener noreferrer"`; ícone
   `externo` com `aria-hidden`. "Ver na Câmara" é `Button variante="fantasma"
   tamanho="s"` (inventário do DS, §1.1).
7. Link para `/parlamentar/{id}` só quando `rankingPublico` (`lib/flags.ts`)
   for verdadeiro (U7); senão, o nome em texto.
8. Seções com `aria-labelledby` apontando para o próprio `h2` (vira landmark
   `region`) e `scroll-mt-24` para não ficarem sob a navegação fixa.
9. O frontend não deriva fase, rótulo nem frase (spec.md §3, princípio 9).

---

## 1. Introdução

### 1.1 As perguntas do cidadão e a superfície que responde

| Pergunta | Superfície | Seção | Tarefa |
| --- | --- | --- | --- |
| O que essa proposição muda? | Proposição | "Em linguagem simples" (existe) | — |
| Onde ela está agora? Quem está com ela? | Proposição | "Situação na Câmara" (F0) → "Onde está agora" (F1) | TRM-015 → TRM-040 |
| Ela virou lei? Qual? | Proposição, lista | "Virou lei: Lei 14.871/2024" + links | TRM-015, TRM-040 |
| Ela anda depressa ou devagar? Quem decide se vai a Plenário? | Proposição | linhas "Regime" e "Quem decide" | TRM-015 |
| Quando vai ser votada? | Proposição | texto fixo "não há data prevista" + quem decide (nunca uma data) | TRM-040 |
| O que já aconteceu? | Proposição | "O que aconteceu" | TRM-041 |
| Quanto falta, e qual é o caminho? | Proposição | `Etapas` em "Onde está agora"; "O caminho inteiro" | TRM-040, TRM-042 |
| Como vocês sabem? Onde confiro? | Proposição | "Como sabemos"; "Ver na Câmara ↗" | TRM-040, TRM-015 |
| O que quer dizer "Aguardando Despacho… (Chancela)"? | Proposição, glossário | explicação da situação; `/como-vira-lei/situacoes` | TRM-040, TRM-045 |
| Quais estão andando? Quais viraram lei? Quais estão nas comissões? | Lista | "Última movimentação em", ordenação, filtro de fase | TRM-016, TRM-043 |
| Como uma ideia vira lei? Qual a diferença entre PL, PLP, PEC, MPV e PDL? Onde pode parar? | `/como-vira-lei` | rito por espécie e Casa, desfechos, apensação, depois da lei | TRM-044 |
| Como o ZIL chega à fase, e quem revisa? | `/metodologia#tramitacao` | — | TRM-047 (Product) |

### 1.2 Mapa de arquitetura de informação

```
/                                   (home: nada muda neste backlog)
├── /proposicoes ─────────────────── lista
│   │   ?fase=<fase|encerradas|nao_identificada>&tipo=<PL…>&casa=<camara|senado>  (TRM-043)
│   │   "Como uma proposição vira lei →" ───────────────────────────► /como-vira-lei
│   └── /proposicoes/[id]
│         ├── cabeçalho: FaseSelo (link) ───► /como-vira-lei?especie=PL&casa=camara#fase-comissoes
│         │                                   (desfecho → #desfechos; nao_sabemos → /metodologia#tramitacao;
│         │                                    mapa_nao_aprovado → sem selo)
│         ├── #onde-esta   Onde está agora
│         │     ├── aviso de apensada ──────► /proposicoes/[id da principal]  (herdada_de.acompanhada)
│         │     │                        └──► Câmara ↗                       (principal só de contexto)
│         │     ├── situação oficial (TermoGlossario) ► /como-vira-lei/situacoes#termo-<chave>
│         │     ├── Ver na Câmara ↗ ────────► url_camara (externo)
│         │     └── Como sabemos ───────────► /metodologia#tramitacao (TRM-047) · fases.yml no GitHub ↗
│         ├── #o-que-aconteceu
│         │     └── marco de votação ───────► /votacoes/[votacao_id]
│         ├── #caminho     O caminho inteiro ► /como-vira-lei?especie=…&casa=…
│         ├── #votacoes    (existe)
│         └── Contexto completo (existe; vai para o fim)
├── /como-vira-lei ──────────────────?especie=PL|PLP|PEC|MPV|PDL&casa=camara|senado
│     ├── #caminho, #fase-<fase> (na primeira etapa de cada fase; ritoParaDiagrama)
│     │      └── "N proposições acompanhadas estão aqui agora" ──► /proposicoes?fase=…&tipo=…&casa=…  (MPV: sem &casa=)
│     ├── #desfechos  #apensacao  #depois-da-lei  #mapa
│     └── ──────────────────────────────────────────────────────► /como-vira-lei/situacoes
├── /como-vira-lei/situacoes
│     ├── #termo-<chave> por entrada (situações, regimes, apreciação)
│     └── fase de cada situação ────────► /como-vira-lei#fase-<fase>
└── /metodologia#tramitacao (TRM-047) ──► /como-vira-lei, data/tramitacao no GitHub ↗
```

Navegação principal: **não muda** neste backlog. `/como-vira-lei` é alcançada
pela página da proposição, pela lista e pela metodologia. Pôr na `NavBar`
(hoje 4 itens, tab bar de 5 no celular) é decisão da maintainer — ver
"Perguntas em aberto" de TRM-044.

**Decisão (rodada 3, conflito 23 do DS): o `FaseSelo` de `nao_sabemos` tem
link**, no cabeçalho da proposição, para `/metodologia#tramitacao` (TRM-047),
que explica como a fase é determinada e por que às vezes não sabemos; o kit
acrescenta ", entenda por quê" ao nome do link. Na lista, como todo
`FaseSelo`, fica sem link (o cartão já é link). `mapa_nao_aprovado` não tem
selo (`N06`). Matriz `N00`, `faseSeloPropsDe` (TRM-046-B) e este mapa dizem a
mesma coisa; a revisão da Arquitetura (item 14), que pedia "sem link", partia
da versão anterior deste mapa.

### 1.3 Ordem das seções da página da proposição

Respeita U2 (resumo antes da fase) e o UI-008 (ementa colapsada logo abaixo do
resumo, aberta quando não há resumo).

| # | Seção | `id` / heading | Desde |
| --- | --- | --- | --- |
| 1 | Voltar ("Todas as proposições") | — | existe |
| 2 | Cabeçalho: chapéu, `h1`, selos (fase, apensada, categorias, análise), "Apresentada em · Texto completo ↗" | `h1` | existe; muda em TRM-015 e TRM-040 |
| 3 | Em linguagem simples · Ementa técnica · Impacto para a soberania industrial | (sem `h2` novo) | existe |
| 4 | Situação na Câmara → Onde está agora | `#onde-esta` / `h2` | TRM-015 → TRM-040 |
| 5 | O que aconteceu | `#o-que-aconteceu` / `h2` | TRM-041 |
| 6 | O caminho inteiro | `#caminho` / `h2` | TRM-042 |
| 7 | Votações | `#votacoes` / `h2` (existe) | existe |
| 8 | Contexto completo (`<details>`) | — | existe; **sai do bloco 3 e vem para o fim** em TRM-015 (é material de referência; disc. §6.1 item 11) |

"O que vem depois" (disc. §6.1 item 4) e "Depois da lei" (item 7) dependem de
TRM-051/052/053 (Depois) e não entram aqui; o único pedaço que entra agora é a
frase fixa `T01` de TRM-040 ("O ZIL não estima quando a proposição vai
avançar: isso depende de quem conduz esta etapa.").

### 1.4 Inventário de componentes

**Do Design System** (APIs de backlog-design-system.md §4 e §6, usadas
exatamente assim; a coluna da direita é o que a interface exige no uso):

| Componente (tarefa) | API | Uso nesta parte |
| --- | --- | --- |
| `FaseSelo` (TRM-031) | `FaseSelo({ fase, desfecho?, rotulo, motivo?, apensada?, href?, id? })` — `fase` aceita `null` com desfecho | `rotulo={fase_rotulo}`, sem montar texto; `href` só no cabeçalho da proposição (fase → `/como-vira-lei?especie=…&casa=…#fase-<fase>`; desfecho → `…#desfechos`; `nao_sabemos` → `/metodologia#tramitacao`); **sem `href`** no cartão da lista, com `id` para a descrição acessível; **não renderizado** quando `motivo === "mapa_nao_aprovado"` (`N06`) |
| `Etapas` (TRM-030) | `Etapas({ etapas: { id, nome, estado, quando?, casa?, nota?, href? }[], variante?, orientacao?, rotulo? })` + `legendaDasEtapas(etapas)` | `variante="compacta"` em "Onde está agora": também é `<ol>` com `aria-current`, e o próprio componente mostra a legenda (a página **não** a repete); "Dispensada" para `pulada`, "Desde {data}" para `atual` (textos do kit, `E01`); vertical abaixo de `md` e com mais de 7 etapas (U8); sem animação (D6) |
| `LinhaDoTempo`, `Marco`, `MarcoEsqueleto` (TRM-032) | `Marco({ quando, titulo, local?, atual?, tipo?, href?, documento? })` + `marcoDaApi(m, i, total)` | `tom` nunca; `atual` só no último marco; `tipo="votacao"` + `href="/votacoes/{votacao_id}"`; tudo pelo adaptador `marcoDaApi`; `LinhaDoTempo aria-labelledby` |
| `TodosOsRegistros` (TRM-032) | `TodosOsRegistros({ total, estado, registros?, onAbrir?, onTentarDeNovo?, erro?, rodape?, fonte?, focarAoTrocar? })` + `registroDoEvento(e)` | a página busca `/tramitacao/eventos` em `onAbrir` (chamado de novo ao reabrir depois de erro) e em `onTentarDeNovo`, e controla `estado`; `rodape` = `Paginacao`; o foco na troca de página é do kit (`focarAoTrocar`); data sem hora |
| `ComoSabemos` (TRM-033) | `ComoSabemos({ resumo?, itens?, fontes, conferidoEm?, nota?, saibaMais?: { rotulo, href }, variante? })` + `comoSabemosDaFase(c)` + `dataBR(iso)` | `comoSabemosDaFase(onde_esta.como_sabemos)` (resumo padrão do kit, `C04`); `saibaMais={{ rotulo: "Como chegamos a esta fase", href: "/metodologia#tramitacao" }}`; adaptador `null` (sem fonte) → `C03` |
| `RitoDiagrama` (TRM-034) | `RitoDiagrama({ titulo, etapas, desfechosGerais?, nivelTitulo?, legenda?, textoPendente? })` + `ritoParaDiagrama(rito: RitoApi, { proposicao?, contagens?, hrefContagem? })` — etapa com `oQueAcontece`, `quemDecide`, `condicao`, `opcional`, `extra?`; ramo `{ desfecho, rotulo, texto }` | proposição: `{ proposicao }`, sem contagem; `/como-vira-lei`: `{ contagens, hrefContagem }`, `legenda`, `extra` com as situações da fase (TRM-045); ramos à direita só a partir de `lg` |
| `TermoGlossario`, `GlossarioLista` (TRM-035) | `TermoGlossario({ children, definicao?, titulo?, baseLegal?, href?, nota?, abertoInicial?, rotuloAcao?, indicador? })`; `GlossarioLista({ entradas, nivelTitulo?, semTexto?, nota? })` + `entradaDaApi`, `definicaoDoTermo` (usa `texto_curto`), `hrefDoTermo` | situação oficial em "Onde está agora" (com `indicador`; `abertoInicial` em `N06`) e situações por fase em `/como-vira-lei`; `GlossarioLista nivelTitulo={3}` em `/situacoes`; âncora `termo-<chave>` (padrão do kit) |
| `Recolhivel` (TRM-037) | `Recolhivel({ titulo, sub?, variante?, aberto? })` | substitui o `SumarioLinha` local da página (ementa, contexto completo) e serve aos marcos anteriores e ao caminho inteiro |
| `FaseSeloEsqueleto`, `EtapasEsqueleto` | — | carregando de "Onde está agora" |
| `scroll-padding` (TRM-037, `globals.css`) | — | o foco nunca fica sob a navegação fixa nem sob a tab bar (U9, WCAG 2.4.11) |

**Do kit existente, reaproveitado sem mudança:** `Card` (bloco de cada seção;
cartão-link na lista), `Lista`/`Linha` e `LinhaEsqueleto`, `Aviso` (`padrao`
para falha parcial e apensada; `contra` para erro que impede a página),
`Vazio`, `Esqueleto`/`CardEsqueleto`, `Button` (`fantasma` para "Ver na
Câmara"; `secundario` para "Tentar de novo"; um `primario` por área no máximo),
`Chip`/`Chips` (`rolagem` no celular), `BarraFiltros`, `Seletor` (ordenação),
`Segmentado` (Casa iniciadora: 2 opções), `Busca`, `Selo` (categorias, análise),
`TituloSecao` (cabeçalho de `/como-vira-lei`), `Painel` (rito não publicável),
`Icone` (`externo`, `info`, `chevron-*`, `documento`, `check`).

**De domínio, criados por estas tarefas** (`apps/web/components/tramitacao/`):
`SituacaoCamara` (TRM-015), `CartaoProposicao` (TRM-016),
`TramitacaoProposicao`, `OndeEsta` (TRM-040), `OQueAconteceu` (TRM-041),
`CaminhoInteiro` (TRM-042), `FiltroFase` (TRM-043), `ComoViraLei` (TRM-044),
`Situacoes` (TRM-045).

---

## 2. Guia de redação do glossário e dos textos de status (parte de TRM-022)

Vale para `glossario.yml`, para os textos de fases, desfechos, marcos e ritos
em `data/tramitacao/`, para os templates de frase (§2.9) e para
`lib/tramitacao/textos.ts`. É o "guia de redação" que o revisor `linguagem`
de TRM-023 recebe como insumo (spec.md §6.4).

### 2.1 Princípios

1. **Diga quem decide o quê.** Toda explicação de situação responde: o que
   está acontecendo, quem tem a próxima decisão e, se houver, qual regra a
   limita. "O presidente da comissão escolhe o relator ou a relatora", não
   "aguarda-se a designação".
2. **Voz ativa, sujeito concreto.** "O Senado mudou o texto", não "o texto
   foi alterado". Passiva só quando o agente não importa ou não é conhecido.
3. **Frases curtas.** Uma ideia por frase; até 25 palavras por frase; até 3
   frases e 60 palavras por entrada. Rótulo de selo até 32 caracteres.
4. **Sem jargão, ou com o jargão explicado na mesma frase.** Primeira menção
   de "parecer", "relator", "pauta", "despacho", "Plenário", "sessão
   legislativa" vem com a explicação (§2.5). Sigla de órgão só depois do nome
   por extenso, e no texto do glossário prefira o nome.
5. **Exatidão vence simplicidade** (spec.md §6.6). Simplificar é escolher o
   que dizer, nunca dizer algo que a norma não diz. Na dúvida, diga menos.
6. **Neutralidade.** Nada de juízo, alarme, torcida ou cobrança. Descreva o
   processo; não avalie quem o conduz.
7. **O termo oficial nunca some.** A explicação do ZIL fica ao lado da
   situação oficial, nunca no lugar dela, e é marcada como "Texto do ZIL, não
   oficial" (na página do glossário e no `TermoGlossario`).
8. **Português do Brasil, presente do indicativo, segunda pessoa nunca.**
   "Proposição" é a palavra do site para o objeto (é o nome da seção); não
   alternar com "proposta" ou "projeto" no mesmo texto, salvo quando a
   espécie é certa ("este projeto" num texto só de PL).
9. **Inclusivo sem barra.** "o relator ou a relatora" na primeira menção,
   depois "a relatoria"; "quem apresentou a proposição" no lugar de
   "autor(a)". Nunca "(a)" em texto corrido: o leitor de tela lê "a". O termo
   oficial ("Relator(a)") fica como a Câmara escreve.
10. **Cargos sempre completos.** "Presidente da Câmara", "Presidente da
    República", "Presidente do Senado", "presidente da comissão". Nunca
    "Presidente" sozinho (é a leitura errada mais provável, disc. §1.1).
11. **Números.** Algarismos para quantidades com unidade ("5 sessões", "15
    dias úteis", "52 deputados"); quóruns com o número e a fração quando a
    fração for a regra ("3/5 dos votos: 308 deputados e 49 senadores"); "dias"
    sempre com "úteis" ou "corridos" quando a norma especifica.
12. **Datas** só vêm da API, pelo template; texto do glossário não tem data.

### 2.2 Como explicar sem perder a exatidão

| Técnica | Exemplo |
| --- | --- |
| Troque o nome do ato pelo efeito, e mantenha o nome entre travessões quando ele aparece na tela | "o despacho — a decisão do Presidente da Câmara que diz por quais comissões a proposição passa" |
| Quantifique com o número da norma, não com adjetivo | "até 40 sessões", não "um prazo longo" |
| Separe o que a norma fixa (D), o que ela fixa mas costuma não ser cumprido (D\*) e o que é decisão de alguém (X) | D: "tem 15 dias úteis"; D\*: "tem até 40 sessões, prazo que costuma não ser cumprido" (só no rito, com fonte de disc. §2.4); X: "quem decide quando é o presidente da comissão" |
| Use "pode" só quando a norma dá a opção; "costuma" só com evidência | "pode recorrer ao Plenário" (art. 137, § 2º); "podem ser aprovadas num texto único" (art. 163) |
| Quando a situação é ambígua, diga que é ambígua | "Aguardando Encaminhamento": "sozinha, não diz em que fase ela está" |
| Quando dois campos oficiais se contradizem, explique a regra que resolve | urgência + "Apreciação Conclusiva": a urgência leva ao Plenário (RICD art. 24, II, h) — §2.7 |
| Ponha a citação fora da frase | o texto fica limpo; a base legal vai no campo `base_legal` e aparece numa linha própria (§2.3) |

### 2.3 Base legal: formato

- No conteúdo: `base_legal: [{norma, dispositivo, url}]` (esquema de TRM-021 e
  spec.md §6.3-2). Na tela, cada item vira um `rotulo` pronto, montado pela
  API, neste formato:
  - "Constituição, art. 66, § 1º" · "Constituição, art. 62, §§ 3º, 4º e 7º"
  - "Regimento da Câmara, art. 24, II, h" · "Regimento da Câmara, arts. 142 e 143"
  - "Regimento do Senado, art. 91" · "Regimento Comum do Congresso, art. 5º"
  - "Lei Complementar 95/1998, art. 8º" · "Lei de Introdução às Normas do Direito Brasileiro, art. 1º"
- Na tela, nunca "CF", "RICD", "RISF", "RCN", "LINDB" sozinhos: são siglas
  de especialista. O texto oficial do regime ("Urgência (Art. 155, RICD)")
  continua como a Câmara escreve, porque é o termo oficial.
- Linha na interface: "Base legal: " + rótulos separados por " · ", cada um
  link para a `url` (abre em nova aba) quando houver.
- Situação administrativa da Câmara sem dispositivo próprio ("Aguardando
  Encaminhamento") leva `base_legal_motivo: "Situação administrativa da
  Câmara, sem dispositivo próprio no Regimento"` — **pedido ao PM e à
  Arquitetura**: hoje V-R7 (spec.md §6.9) só aceita `base_legal_motivo` para
  estado interno do ZIL.

### 2.4 O que nunca dizer

Cada linha com padrão é regra automática que o validador de TRM-024 aplica
aos campos de texto do ZIL (nunca ao termo oficial). Padrões em regex Python,
com `re.IGNORECASE`, **exceto V-E6 e V-E10, que dependem de maiúsculas**.
Proposta de nome: regras `V-E1` a `V-E10`.

| Regra | Não escrever | Por quê | Padrão |
| --- | --- | --- | --- |
| V-E1 | Data prevista, "deve ser votada", "em breve", "previsão" | o ZIL não estima datas (spec.md §3-1) | `em breve\|deve(rá)? ser votad\|previs(ão\|t[oa]) para\|está prevista\|até o fim do (ano\|mês\|semestre)` |
| V-E2 | "Parada há N dias", "atrasada", "engavetada", "travada", "esquecida", "emperrada" | alarme e cobrança (disc. §6.5) | `parad[oa] há\|há \d+ (dias\|meses\|anos)\|atrasad\|engavetad\|gaveta\|travad\|esquecid\|emperrad\|deveria\|precisa ser votad` |
| V-E3 | "% concluída", "falta pouco", "quase lá" | regulamentação não é etapa; progresso não é mérito | `%\|falta pouco\|quase lá\|reta final` |
| V-E4 | "Lei não regulamentada", "o governo não regulamentou", "descumpre" | acusação; ausência de regulamento não é descumprimento (disc. §7) | `não regulamentad\|falta regulamentar\|(governo\|executivo) não (regulamentou\|cumpriu)\|descumpr` |
| V-E5 | Causalidade e juízo: "graças à lei", "importante", "polêmica", "vitória", "derrota", "infelizmente" | apartidário (CLAUDE.md, princípio 2) | `graças a\|resultou em\|importante\|polêmic\|vitória\|derrota\|felizmente\|infelizmente\|finalmente` |
| V-E6 | "Presidente" sem dizer de quê | leitura errada mais provável | `\bPresidente\b(?! d[aoe] (Câmara\|República\|Senado\|Congresso))` (o "presidente da comissão", minúsculo, passa) |
| V-E7 | Data no texto do glossário | datas só vêm da API | `\b\d{1,2}/\d{1,2}(/\d{2,4})?\b` |
| V-E8 | "N dias" sem "úteis" ou "corridos" | o prazo muda de tamanho | `\b\d+ dias\b(?! (úteis\|corridos))` |
| V-E9 | Flexão entre parênteses no texto corrido | leitor de tela lê "relator a" | `\w\((a\|as\|o\|os\|à)\)` |
| V-E10 | Sigla de três ou mais maiúsculas fora da lista de espécies | jargão | `\b(?!(PL\|PLP\|PEC\|MPV\|PDL\|PLV)\b)[A-Z]{3,}\b` |
| — (humano) | "Aprovada" quando só uma Casa aprovou; "virou lei" para PEC ou PDL; "vetada" para veto parcial; "arquivada = rejeitada"; "em vigor" para norma recém-publicada | exatidão | revisor `juridico` |
| — (humano) | "Proposições arquivadas podem ser desarquivadas" como regra geral na Câmara | o antigo parágrafo único do RICD art. 105, que permitia o desarquivamento, foi revogado pela RCD 33/2022 (conferido no texto compilado do RICD em 2026-10-30) | revisor `juridico` |

Limites medidos também pelo validador: frase ≤ 25 palavras; entrada ≤ 3
frases e ≤ 60 palavras; rótulo ≤ 32 caracteres; `termo` de situação idêntico à
`descricao_oficial` do snapshot (TRM-020).

### 2.5 Vocabulário fixo

| Termo | Explicação que acompanha a primeira menção | Evitar |
| --- | --- | --- |
| despacho | a decisão do Presidente da Câmara que diz por quais comissões a proposição passa | "distribuição" sem explicar |
| comissão | grupo de deputados (ou senadores) que analisa um assunto | "colegiado", "órgão técnico" |
| relator ou relatora | o deputado ou a deputada que estuda a proposição e escreve o parecer | "relator(a)" no texto corrido |
| parecer | o texto que recomenda aprovar, mudar ou rejeitar a proposição | "voto do relator" |
| pauta | a lista do que vai ser votado numa reunião ou sessão | "Ordem do Dia" (só como termo oficial) |
| Plenário | a reunião de todos os deputados (ou de todos os senadores) | "PLEN" |
| sessão legislativa | o ano de trabalho do Congresso | "SL" |
| apensação, tramitar em conjunto | juntar proposições sobre o mesmo assunto para que andem juntas | "incorporar" (o RICD art. 143, I, diz "sem incorporação") |
| maioria absoluta | mais da metade de todos os membros: 257 deputados, 41 senadores | "maioria" sem dizer qual |
| sancionar / vetar | o Presidente da República aprova / recusa, no todo ou em parte | "assinar" |
| promulgar | declarar oficialmente que a norma existe | — |
| perder a eficácia | deixar de valer | "caducar" |
| prejudicada | não vai mais ser votada, porque outra decisão a tornou sem efeito | "perdeu o objeto" |

### 2.6 Antes e depois: situações reais (disc. Apêndice A)

"Leitura errada" é o que um leigo entende do termo oficial ou o que uma
explicação apressada diria. "Texto do ZIL" é o rascunho para o lote L4 (e
L1, para desfechos) de TRM-029; vai mudar na revisão — esta é a versão de
partida, já escrita contra §2.1–2.5. O `termo` é a situação oficial,
idêntica à da Câmara.

| Situação oficial (`codSituacao`) | Leitura errada | Texto do ZIL (rascunho) | Fase | Base legal |
| --- | --- | --- | --- | --- |
| Aguardando Despacho do Presidente da Câmara dos Deputados (Chancela) (1201) | "Esperando a sanção do Presidente" — é o oposto: a proposição está no começo | A proposição ainda não foi distribuída às comissões. O Presidente da Câmara ainda vai assinar o despacho que diz por quais comissões ela passa. “Chancela” é um passo interno desse despacho. | `apresentada` (R8) | Regimento da Câmara, art. 139 |
| Aguardando Despacho do Presidente da Câmara dos Deputados (Autorização) (1221) | idem | A proposição ainda não foi distribuída às comissões. O Presidente da Câmara ainda vai assinar o despacho que diz por quais comissões ela passa. “Autorização” é um passo interno desse despacho. | `apresentada` (R8) | Regimento da Câmara, art. 139 |
| Aguardando Autorização do Despacho (1200) | "Esperando autorização do governo" | O Presidente da Câmara ainda vai autorizar o despacho que diz por quais comissões a proposição passa. Isso acontece logo depois da apresentação ou quando a proposição precisa de um novo despacho. | `apresentada` (R8) | Regimento da Câmara, art. 139 |
| Ag. Análise de Inconstitucionalidade (1091) | "Foi considerada inconstitucional" | Antes de distribuir a proposição às comissões, a Presidência da Câmara verifica se ela é claramente contrária à Constituição. Se for, pode devolvê-la a quem a apresentou, que pode recorrer ao Plenário. | `apresentada` (R8) | Regimento da Câmara, art. 137, § 1º, II, b, e § 2º |
| Aguardando Designação de Relator(a) (907) | "Parada porque ninguém quis relatar" | A proposição está numa comissão e espera que o presidente da comissão escolha o relator ou a relatora: o deputado ou a deputada que vai estudá-la e escrever o parecer. | `comissoes` (R7) | Regimento da Câmara, art. 41, VI |
| Aguardando Parecer (915) | "Em análise" (vago); "prazo de 40 sessões vencido" (cobrança) | O relator ou a relatora está preparando o parecer: o texto que recomenda aprovar, mudar ou rejeitar a proposição. Depois, a comissão vota esse parecer. | `comissoes` (R7) | Regimento da Câmara, art. 56 |
| Aguardando Designação - Aguardando Devolução de Relator(a) que deixou de ser Membro (1170) | "O relator abandonou o projeto" | A relatoria deixou a comissão antes de entregar o parecer. A proposição precisa voltar à comissão, e o presidente da comissão vai escolher outra pessoa para relatar. | `comissoes` (R7) | Regimento da Câmara, art. 41, VI |
| Pronta para Pauta (924) | "Vai ser votada em breve"; "pronta para virar lei" | A análise prévia terminou e a proposição já pode ser votada onde está: numa comissão ou no Plenário. Falta entrar na pauta. Quem decide é o presidente da comissão ou, no Plenário, o Presidente da Câmara, ouvidos os líderes dos partidos. | `comissoes` ou `plenario`, pelo órgão (R7) | Regimento da Câmara, arts. 17, I, s; 41, V; 59; 86 |
| Tramitando em Conjunto (925) | "Foi incorporada a outra"; "parada" | Esta proposição foi juntada a outra sobre assunto igual ou parecido, que é a principal. As duas andam juntas e recebem um parecer só. A fase mostrada aqui é a da principal. | `apensada` → fase da principal (R4) | Regimento da Câmara, arts. 142 e 143 |
| Aguardando Apensação (927) | "Esperando aprovação" | O Presidente da Câmara decidiu que esta proposição vai tramitar junto com outra sobre assunto igual ou parecido. Falta registrar a juntada. | `apensada` (R4) | Regimento da Câmara, arts. 139, I, e 142 |
| Aguardando Encaminhamento (910) | "Aguardando encaminhamento para votação" | A Câmara ainda vai dar o próximo destino à proposição. Essa situação aparece depois de uma aprovação, de uma rejeição ou quando a proposição fica prejudicada. Por isso, sozinha, não diz em que fase ela está. | desfecho por R2, senão `nao_sabemos(sinais_conflitantes)` | `base_legal_motivo` (§2.3) |
| Aguardando Apreciação pelo Senado Federal (926) | "Aprovada" (falta o Senado) | A Câmara terminou de analisar a proposição e a enviou ao Senado, que agora vai analisá-la. | `outra_casa` (R5) | Constituição, art. 65 |
| Aguardando Sanção (1150) | "Será sancionada até dd/mm" (o ZIL não calcula dias úteis) | O Congresso aprovou a proposição e a enviou ao Presidente da República, que tem 15 dias úteis para sancionar ou vetar, no todo ou em parte. Sem resposta no prazo, a sanção é automática. | `sancao` (R6) | Constituição, art. 66, §§ 1º e 3º |
| Transformado em Norma Jurídica (1140) | "Aprovada" (vago); "em vigor" (a vigência pode começar depois) | A proposição terminou de tramitar e virou norma: uma lei, um decreto legislativo ou uma emenda à Constituição, conforme o tipo. O número está no último despacho da Câmara. | `norma` (R1) | Constituição, arts. 60, § 3º, e 66 |
| Arquivada (923) | "Rejeitada"; "morreu"; "pode ser desarquivada" (ver §2.4) | A proposição foi arquivada e não está mais em análise. O motivo varia — fim da legislatura, parecer contrário de todas as comissões, decisão sobre outra parecida — e está no último despacho. Arquivar não quer dizer, por si só, que ela foi rejeitada. | desfecho `arquivada` (R3) | Regimento da Câmara, arts. 105 e 133 |
| Retirado pelo(a) Autor(a) (950) | "O autor desistiu" | Quem apresentou a proposição pediu para retirá-la, e o pedido foi aceito. Ela não tramita mais. | desfecho `retirada` (R3) | Regimento da Câmara, art. 104 |
| Perdeu a Eficácia (1292) | "Caducou" (jargão); "foi rejeitada" | Esta medida provisória deixou de valer porque o Congresso não terminou de votá-la no prazo: 60 dias, prorrogáveis por mais 60, sem contar o recesso. | desfecho `perdeu_eficacia` (R3) | Constituição, art. 62, §§ 3º, 4º e 7º |
| Devolvida ao(à) Autor(a) (1120) | "Rejeitada" | A Presidência da Câmara devolveu a proposição a quem a apresentou, sem distribuí-la às comissões. Isso acontece quando ela não cumpre requisitos do Regimento — por exemplo, trata de assunto fora da competência da Câmara. Quem a apresentou pode recorrer ao Plenário. | desfecho `devolvida` | Regimento da Câmara, art. 137, §§ 1º e 2º |

**Achado para o ⚠ de disc. §2.2 ("devolução ao autor, artigo não
conferido").** O RICD art. 137, § 1º, manda a Presidência devolver ao autor a
proposição não formalizada, alheia à competência da Câmara, evidentemente
inconstitucional ou antirregimental; o § 2º dá recurso ao Plenário em 5
sessões (texto compilado conferido em 2026-10-30). A Arquitetura conferiu de
novo no mesmo texto (revisão, item 13) e tirou o `pendente` da devolução em
backlog-dados; a entrada segue o fluxo normal dos revisores de TRM-023.

### 2.7 Regimes e forma de apreciação

Termos oficiais vistos nas 240 acompanhadas em 2026-10-30 (contagem entre
parênteses). As 10 entradas formam o lote L0 (spec.md §6.12).
`regime_concessao_radiodifusao` (1 caso em 240) pode sair do lote por
`--excluir` se o texto não estiver pronto, sem bloqueá-lo — sem ele, a página
mostra só o termo oficial nesse caso, o que é seguro.

| Chave | Termo oficial | Rótulo | Texto do ZIL (rascunho) | Base legal | Lote |
| --- | --- | --- | --- | --- | --- |
| `regime_ordinaria` | Ordinário (Art. 151, III, RICD) (132) | Tramitação ordinária | Segue o ritmo normal da Câmara. Cada comissão tem até 40 sessões para decidir. | Regimento da Câmara, arts. 151, III, e 52, III | L0 |
| `regime_prioridade` | Prioridade (Art. 151, II, RICD) (10) | Tramitação com prioridade | Tem preferência sobre a tramitação ordinária: no Plenário, entra na pauta logo depois das urgências, e cada comissão tem até 10 sessões para decidir. É o caso, por exemplo, de projetos do Executivo, do Judiciário e do Senado. | Regimento da Câmara, arts. 151, II; 52, II; 158 | L0 |
| `regime_urgencia` | Urgência (Art. 155, RICD) (42) | Urgência aprovada pelos deputados | A maioria absoluta dos deputados (257) aprovou um pedido de urgência para esta proposição. Com isso, ela pode ir logo ao Plenário, sem esperar os prazos das comissões, e a decisão final passa a ser do Plenário. | Regimento da Câmara, arts. 155, 157 e 24, II, h | L0 |
| `regime_urgencia_constitucional` | Urgência (Art. 64, CF) (2) | Urgência pedida pelo Presidente da República | O Presidente da República pediu urgência para este projeto, que é de autoria dele. Se a Câmara não votar em 45 dias, as demais votações da Casa ficam suspensas até que vote, salvo as que têm prazo na Constituição. | Constituição, art. 64, §§ 1º e 2º | L0 |
| `regime_medida_provisoria` | Urgência (Art. 62, CF) (12) | Prazo de medida provisória | A medida provisória vale como lei desde que foi publicada e precisa ser aprovada pelo Congresso em até 60 dias, prorrogáveis por mais 60, sem contar o recesso. | Constituição, art. 62, §§ 3º, 4º e 7º | L0 |
| `regime_urgencia_acordo_internacional` | Urgência (Art. 151, I "j", RICD) (9) | Urgência de acordo internacional | Projetos sobre acordos e tratados internacionais enviados pelo Presidente da República tramitam com urgência depois que a comissão técnica os aprova. | Regimento da Câmara, art. 151, I, j | L0 |
| `regime_concessao_radiodifusao` | Art. 223 - CF (1) | Concessão de rádio ou TV | O Congresso analisa o ato do governo que deu ou renovou uma concessão de rádio ou TV. | Constituição, art. 223, § 1º | L0 (pode sair por `--excluir`) |
| `apreciacao_conclusiva` | Proposição Sujeita à Apreciação Conclusiva pelas Comissões - Art. 24 II (139) | Decisão nas comissões | As comissões decidem. Se aprovarem, a proposição segue sem votação no Plenário da Câmara. Isso só muda se pelo menos 52 deputados recorrerem em até 5 sessões e o Plenário aceitar o recurso. | Regimento da Câmara, arts. 24, II; 58, § 1º; 132, § 2º; Constituição, art. 58, § 2º, I | L0 |
| `apreciacao_plenario` | Proposição Sujeita à Apreciação do Plenário (68) | Decisão no Plenário | Depois das comissões, quem decide é o Plenário da Câmara, onde votam todos os deputados. | Regimento da Câmara, arts. 24, II, e 132, IV | L0 |
| `apreciacao_conclusiva_com_urgencia` | (o termo de `apreciacao_conclusiva`, quando o regime é urgência) (9) | Decisão no Plenário, por causa da urgência | O despacho previa a decisão nas comissões, mas a urgência leva a proposição ao Plenário: projeto em urgência não é decidido só pelas comissões. | Regimento da Câmara, art. 24, II, h | L0 |

**`texto_curto` (≤ 160 caracteres) das entradas do L0** — é o que
`regime_texto`/`apreciacao_texto` levam à página (TRM-014); o `texto` acima vai
para `/como-vira-lei/situacoes`:

| Chave | `texto_curto` (rascunho) |
| --- | --- |
| `regime_ordinaria` | Segue o ritmo normal da Câmara: cada comissão tem até 40 sessões para decidir. |
| `regime_prioridade` | Tem preferência sobre a tramitação ordinária, com prazos menores nas comissões. |
| `regime_urgencia` | Os deputados aprovaram urgência: a proposição pode ir logo ao Plenário, que dá a decisão final. |
| `regime_urgencia_constitucional` | O Presidente da República pediu urgência: a Câmara tem 45 dias para votar este projeto. |
| `regime_medida_provisoria` | Vale desde a publicação e precisa ser aprovada em até 60 dias, prorrogáveis por mais 60. |
| `regime_urgencia_acordo_internacional` | Acordo internacional: tramita com urgência depois de aprovado pela comissão técnica. |
| `apreciacao_conclusiva` | As comissões decidem; o Plenário só vota se 52 deputados recorrerem e o recurso for aceito. |
| `apreciacao_plenario` | Depois das comissões, quem decide é o Plenário da Câmara. |
| `apreciacao_conclusiva_com_urgencia` | Com a urgência, quem decide é o Plenário, e não só as comissões. |

Regra geral de `texto_curto` para todas as entradas: no máximo 2 frases, 20 a
160 caracteres, que se leiam **sozinhas** — sem "como dito acima", sem depender
do `termo` ao lado para fazer sentido — porque é a definição que abre no
`TermoGlossario`, isolada do resto da página (cabe em 36ch × 5 linhas), e a
linha de `dl` de "Regime"/"Quem decide"; quando a primeira frase do `texto`
couber, ela é o `texto_curto`. Proposta de regra do validador (TRM-024):
`texto_curto` sem "acima", "abaixo", "como dito", "esta situação" no início.

**Combinação que exige regra (para a Arquitetura, em TRM-014/028).** Em 9 das
240 acompanhadas o regime é urgência e a apreciação oficial continua
"Conclusiva" — a Câmara não atualiza o campo (ex.: PL 399/2025, urgência RICD
155, conclusiva, já no Senado). Mostrar o texto de `apreciacao_conclusiva`
nesses casos seria **falso** ("segue sem votação no Plenário"). Regra: se
`regime` começa com "Urgência" e `apreciacao` é a conclusiva, `apreciacao_texto`
vem de `apreciacao_conclusiva_com_urgencia`; se essa entrada não estiver
publicável, `apreciacao_texto` é `null` (a página mostra só o termo oficial).
Nunca cair para o texto da conclusiva pura.

**Valores que são ausência, não regime.** Regime "." (32) e apreciação
"Indefinida" (32) aparecem juntos, antes do despacho. A API devolve `null`
nos dois; a página mostra o texto `F06` da matriz.

**Variante sem entrada** ("Proposição Sujeita à Apreciação Conclusiva
(Parecer 09/90 - CCJR)", 1 caso): sem entrada, mostra só o termo oficial.
Não mapear por semelhança de texto.

### 2.8 Fases, desfechos, apensada e espécies

Rótulos do `FaseSelo` (lote L1; seguem a recomendação de D1, spec.md §10.2) e
explicação de cada um, mostrada em "Onde está agora" (TRM-040) e no rito de
`/como-vira-lei` (TRM-044). Os rótulos moram em `fases.yml` (lote L1); as
explicações, no glossário, com as chaves fixas `fase_<fase>`,
`desfecho_<desfecho>`, `apensada` e `especie_<sigla>` (backlog-dados.md
§7-7), com `texto_curto` (a primeira frase, ≤ 160 caracteres) e `texto`.

| Chave | Rótulo (≤ 32) | Explicação (rascunho) | Base legal |
| --- | --- | --- | --- |
| `fase_apresentada` | Apresentada · com R9 (`recem_apresentada`): Recém-apresentada | A proposição foi apresentada e ainda não foi distribuída às comissões. O Presidente da Câmara decide por quais comissões ela passa e se elas decidem sozinhas ou se o Plenário vota depois. | Regimento da Câmara, art. 139 |
| `fase_comissoes` | Nas comissões · MPV: Na comissão mista | Comissões são grupos de deputados por assunto. Em cada uma, o relator ou a relatora escreve o parecer, e a comissão vota. Quem decide quando a proposição entra na pauta é o presidente de cada comissão. | Regimento da Câmara, arts. 41, V e VI, e 56 |
| `fase_plenario` | No Plenário da Câmara · No Plenário do Senado | Todos os deputados podem votar a proposição. Quem decide quando ela entra na pauta é o Presidente da Câmara, ouvidos os líderes dos partidos. | Regimento da Câmara, arts. 17, I, s, e 86 |
| `fase_outra_casa` | No Senado · Na Câmara | O Senado analisa a proposição, com suas próprias comissões e seu Plenário. Ele pode aprovar, mudar ou rejeitar o texto. | Constituição, art. 65 |
| `fase_retorno` | De volta à Câmara · De volta ao Senado | O Senado mudou o texto. A Câmara, onde a proposição começou, não pode mais mudar nada: só aceita ou rejeita cada mudança. | Constituição, art. 65, parágrafo único |
| `fase_sancao` | Com o Presidente da República | O Presidente da República tem 15 dias úteis para sancionar ou vetar, no todo ou em parte. Sem resposta no prazo, a sanção é automática. | Constituição, art. 66, §§ 1º e 3º |
| `fase_veto_congresso` | Veto em análise no Congresso | O Presidente da República vetou o texto inteiro. Deputados e senadores, em sessão conjunta, decidem se mantêm ou derrubam o veto. Para derrubar, são precisos os votos de 257 deputados e 41 senadores. | Constituição, art. 66, §§ 4º a 6º |
| `fase_promulgacao` | Aguardando promulgação | Falta a promulgação: o ato que declara oficialmente a nova norma. Nas emendas à Constituição e nos decretos legislativos, quem promulga é o Congresso. | Constituição, arts. 60, § 3º, e 66, §§ 5º e 7º |
| `fase_norma` | Virou lei · Virou emenda constitucional · Virou decreto legislativo · MPV: Convertida em lei | A proposição virou norma. Isso não quer dizer que já esteja valendo: a data de início está no próprio texto. Se o texto não disser, a norma vale 45 dias depois de publicada. | Lei Complementar 95/1998, art. 8º; Lei de Introdução às Normas do Direito Brasileiro, art. 1º |
| `desfecho_arquivada` | Arquivada | A proposição foi arquivada e não está mais em análise. Na Câmara, arquivar não quer dizer, por si só, que foi rejeitada, e o motivo está no último despacho. No Senado, um terço dos senadores pode pedir o desarquivamento em até 60 dias. | Regimento da Câmara, arts. 105 e 133; Regimento do Senado, art. 332 (o prazo e o quórum do Senado entram com `pendente` até o revisor `juridico` conferir — revisão da Arquitetura, item 13) |
| `desfecho_retirada` | Retirada pela autoria | (o texto de "Retirado pelo(a) Autor(a)", §2.6) | Regimento da Câmara, art. 104 |
| `desfecho_prejudicada` | Prejudicada | A proposição não vai mais ser votada: foi declarada prejudicada porque outra igual ou parecida já foi decidida ou porque perdeu a oportunidade. Quem declara é o Presidente da Câmara ou o presidente da comissão, e quem a apresentou pode recorrer. | Regimento da Câmara, arts. 163 e 164 |
| `desfecho_rejeitada` | Rejeitada | A proposição foi rejeitada, em votação ou por parecer contrário de todas as comissões, e arquivada. O mesmo assunto só volta na mesma sessão legislativa (o ano de trabalho do Congresso) se a maioria absoluta de uma das Casas propuser. | Constituição, art. 67; Regimento da Câmara, art. 133 |
| `desfecho_perdeu_eficacia` | Perdeu a eficácia | (o texto de "Perdeu a Eficácia", §2.6) | Constituição, art. 62, §§ 3º, 4º e 7º |
| `desfecho_vetada` | Vetada | O Presidente da República vetou o texto inteiro, e o Congresso manteve o veto. A proposição não vira lei. | Constituição, art. 66, §§ 1º e 4º |
| `desfecho_devolvida` | Devolvida à autoria | (o texto de "Devolvida ao(à) Autor(a)", §2.6) | Regimento da Câmara, art. 137, §§ 1º e 2º |
| `apensada` | Em conjunto (segundo selo, texto do kit) | Esta proposição tramita junto com outra sobre assunto igual ou parecido, a principal. As duas recebem um parecer só, e a fase mostrada é a da principal. Quando a principal é votada, as que andam com ela podem ser aprovadas num texto único ou declaradas prejudicadas. | Regimento da Câmara, arts. 142, 143 e 163 |

As explicações de fase acima descrevem o rito com Câmara iniciadora. Nos
ritos com Senado iniciador, TRM-021 troca Casa e cargos ("o Presidente do
Senado"; "Todos os senadores podem votar"); o conteúdo segue o mesmo guia.

**Espécies** (`especies[].descricao`, uma frase cada, para `/como-vira-lei`):

| Sigla | Descrição (rascunho) | Base legal |
| --- | --- | --- |
| PL | Projeto de lei: cria ou muda uma lei ordinária. É aprovado pela maioria dos votos, desde que esteja presente a maioria dos membros da Casa. | Constituição, arts. 47 e 61 |
| PLP | Projeto de lei complementar: trata dos assuntos que a Constituição reserva a esse tipo de lei. Precisa dos votos de pelo menos 257 deputados e 41 senadores e sempre passa pelo Plenário. | Constituição, art. 69; Regimento da Câmara, art. 24, II, a |
| PEC | Proposta de emenda à Constituição: muda o texto da Constituição. Precisa de 3/5 dos votos (308 deputados e 49 senadores), em dois turnos em cada Casa, e não vai à sanção. | Constituição, art. 60 |
| MPV | Medida provisória: editada pelo Presidente da República, vale como lei desde a publicação. O Congresso tem 60 dias, prorrogáveis por mais 60, para aprová-la; se mudar o texto, ele vai à sanção. | Constituição, art. 62 |
| PDL | Projeto de decreto legislativo: trata de assuntos que só o Congresso decide, como tratados internacionais e a suspensão de atos do governo que vão além da lei. Não vai à sanção. | Constituição, art. 49 |

### 2.9 Templates da frase de "Onde está agora" (`onde_esta.frase`)

A frase é montada pela API (TRM-025/028), a partir de `fases.yml`; o conteúdo
é este, com os marcadores de backlog-dados.md §7-8: `{na_casa}` "na
Câmara"/"no Senado"; `{da_casa}`; `{membros}` "deputados"/"senadores";
`{orgao}` "Comissão de Minas e Energia (CME)"; `{orgao_desde}` (chegada ao
órgão) e `{desde}` (início da fase), dd/mm/aaaa; `{data}` (data do marco
decisivo); `{norma_com_artigo}` "a Lei 14.871/2024", "o Decreto Legislativo
147/2026"; `{na_lei}` "na Lei 14.000/2020"; `{principal_com_artigo}` "o PL
5941/2013"; `{frase_principal}`.

**Regra de montagem:** marcador sem valor nunca vira "None", "null", "—" nem
parênteses vazios — usa-se a variante sem a oração inteira. A frase não leva
juízo nem data futura; passa pelas regras V-E da §2.4.

| Estado | Template | Variante sem o dado | Exemplo |
| --- | --- | --- | --- |
| `apresentada` | Apresentada {na_casa} em {data}. Ainda não foi distribuída às comissões. | sem `{data}`: "Apresentada {na_casa}. Ainda não foi distribuída às comissões." | Apresentada na Câmara em 29/10/2026. Ainda não foi distribuída às comissões. |
| `comissoes` | Nas comissões {da_casa}. Está na {orgao} desde {orgao_desde}. | sem `{orgao_desde}`: "… Está na {orgao}."; sem `{orgao}`: "Nas comissões {da_casa}." | Nas comissões da Câmara. Está na Comissão de Finanças e Tributação (CFT) desde 09/05/2025. |
| `comissoes` (MPV) | Na comissão mista do Congresso desde {orgao_desde}. | "Na comissão mista do Congresso." | — |
| `plenario` | No Plenário {da_casa} desde {desde}, onde votam todos os {membros}. | "No Plenário {da_casa}, onde votam todos os {membros}." | No Plenário da Câmara desde 12/03/2025, onde votam todos os deputados. |
| `outra_casa` | {No Senado\|Na Câmara}. {A Câmara\|O Senado} concluiu a análise e enviou a proposição em {data}. | sem `{data}`: "… e enviou a proposição." | No Senado. A Câmara concluiu a análise e enviou a proposição em 30/04/2026. |
| `retorno` | De volta {à Câmara\|ao Senado} desde {desde}. {O Senado\|A Câmara} mudou o texto, e {a Câmara\|o Senado} decide se aceita cada mudança. | sem `{desde}`: "De volta à Câmara. …" | — |
| `sancao` | Com o Presidente da República desde {desde}, para sanção ou veto. | "Com o Presidente da República, para sanção ou veto." | — |
| `veto_congresso` | O Presidente da República vetou o texto inteiro em {data}. O veto está em análise no Congresso. | sem `{data}`: "O Presidente da República vetou o texto inteiro. …" | — |
| `promulgacao` | Aprovada pelo Congresso em {data}. Aguarda promulgação. | "Aprovada pelo Congresso. Aguarda promulgação." | — |
| `norma` | Virou {norma_com_artigo}. | sem número: "Virou norma. O número não aparece no despacho da Câmara." | Virou a Lei 14.871/2024. |
| `norma` (MPV) | Convertida {na_lei}. ("na Lei 14.000/2020") | "Convertida em lei. O número não aparece no despacho da Câmara." | — |
| `norma` + veto parcial | + " Sancionada com veto parcial." | — | Virou a Lei 14.871/2024. Sancionada com veto parcial. |
| `arquivada` | Arquivada em {data}. | "Arquivada." | Arquivada em 06/05/2026. |
| `retirada` | Retirada pela autoria em {data}. | "Retirada pela autoria." | — |
| `prejudicada` | Declarada prejudicada em {data}. | "Declarada prejudicada." | — |
| `rejeitada` | Rejeitada {na_casa} em {data}. | "Rejeitada {na_casa}." | — |
| `perdeu_eficacia` | Perdeu a eficácia em {data}. | "Perdeu a eficácia." | — |
| `vetada` | Vetada pelo Presidente da República; o Congresso manteve o veto em {data}. | "… o Congresso manteve o veto." | — |
| `devolvida` | Devolvida à autoria em {data}. | "Devolvida à autoria." | — |
| `apensada` | Tramita junto com {principal_com_artigo}, a proposição principal. {frase_principal} | sem a frase da principal: só a primeira oração | Tramita junto com o PL 5941/2013, a proposição principal. No Plenário da Câmara desde 12/03/2025, onde votam todos os deputados. |
| `nao_sabemos` (qualquer motivo) | `frase: null` — a interface usa a matriz (§4, `N01`–`N07`) | — | — |

### TRM-022 — Glossário v0 (`glossario.yml`) e guia de redação

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E2 Mapa e glossário · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** M (dois PRs: L0 = regimes e apreciação; L4 = situações)
**Dono da spec:** UI/UX · **Revisões obrigatórias:** os quatro revisores de TRM-023 (spec.md §6.4); Maintainer (aprovação por lote, TRM-029); Arquitetura (esquema)
**Depende de:** TRM-020 (snapshots, para copiar `descricao_oficial`), TRM-021 (esquema e chaves), TRM-023 (pipeline) · **Desbloqueia:** TRM-029 lotes L0 e L4; textos de TRM-015 (`regime_texto`, `apreciacao_texto`), TRM-040, TRM-045

**Problema**
- A Câmara tem 99 códigos de situação (`/referencias/proposicoes/codSituacao`,
  consultado em 2026-10-30) e nenhum glossário cidadão. A situação mais comum
  depois das de comissão — "Aguardando Despacho do Presidente da Câmara dos
  Deputados (Chancela)", 20 acompanhadas — é lida como o contrário do que é
  (disc. §1.1).
- Dois campos oficiais se contradizem em 9 das 240 acompanhadas (urgência +
  "Apreciação Conclusiva"); uma explicação ingênua publicaria um erro (§2.7).
- O texto proposto no discovery para "Arquivada" ("podem ser desarquivadas")
  não se sustenta no RICD vigente (§2.4).
- Nenhuma regra escrita impede juízo, alarme ou previsão nos textos.

**Oportunidade** — Um texto revisado por entrada serve a toda proposição que
cai nela, para sempre: o custo é fixo e o alcance cresce com a cobertura. O
guia (§2) dá aos revisores de TRM-023 um critério verificável, e metade dele
vira regra automática (V-E1–V-E10).

**Solução**
1. O guia de redação é a §2 deste arquivo; o arquivo
   `data/tramitacao/guia-redacao.md` **não** é criado — o revisor `linguagem`
   recebe a §2 como insumo pelo caminho deste arquivo (pedido ao PM: apontar
   `guia_redacao` em `INSUMOS` para `specs/013-tramitacao/backlog-interface.md#2-guia-de-redação-do-glossário-e-dos-textos-de-status`
   ou extrair a seção num arquivo, a critério de TRM-023).
2. `data/tramitacao/glossario.yml` com as entradas de §2.6 (situações) e
   §2.7 (regimes e apreciação), no esquema de TRM-021. Campos de conteúdo por
   entrada: `chave` (snake_case, sem prefixo de arquivo: `aguardando_despacho_chancela`,
   `regime_urgencia`; as chaves fixas de backlog-dados.md §7-7 valem),
   `tipo` (`situacao` \| `regime` \| `apreciacao` \| `conceito`; `fase`,
   `desfecho`, `apensada` e `especie` para o conteúdo de §2.8), `codigos`
   (em situações), `termo` (= `descricao_oficial` do snapshot), `texto_curto`
   (§2.7), `texto`, `base_legal`, `fase` (situações), `fontes`, `casos` (ao
   menos uma proposição real por entrada, com id da Câmara — spec.md §6.3-5).
3. Entradas `fase_*`, `desfecho_*`, `apensada` e `especie_*` do glossário com
   os textos de §2.8; rótulos (§2.8) e templates de frase (§2.9) entregues ao
   redator de TRM-021 para `fases.yml`.
4. Regras V-E1–V-E10 (§2.4) entregues a TRM-024 como lista de regras do
   validador, com os exemplos "não escrever" de §2.4 e §2.6 como casos de
   teste negativos e os textos de §2.6–2.8 como positivos.

**Escopo**
- Dentro: 18 situações (as 16 do banco + "Aguardando Sanção" + "Devolvida
  ao(à) Autor(a)"); 6 entradas de L0 + 4 propostas (§2.7); o guia; os casos de
  teste do estilo.
- Fora: as outras 81 situações da Câmara (aparecem como "Sem explicação
  ainda", TRM-045); as 175 do Senado (com TRM-050); textos de `nao_sabemos`
  (TRM-046, frontend); rodar os lotes (TRM-029); o esquema e o validador
  (TRM-021, TRM-024).

**Critérios de aceite**
1. `python scripts/validar_tramitacao.py` passa com todas as entradas em
   `rascunho` (CI verde).
2. Cada `termo` de situação é idêntico, caractere a caractere, à
   `descricao_oficial` do snapshot (teste do validador).
3. Nenhuma entrada viola V-E1–V-E10; nenhuma frase passa de 25 palavras;
   nenhuma entrada passa de 3 frases ou 60 palavras (saída de
   `validar_tramitacao.py --estilo`, se TRM-024 adotar o nome).
4. Toda entrada tem `base_legal` com URL ou `base_legal_motivo` aceito pelo
   validador; toda entrada tem `casos` com ao menos um id real.
5. `apreciacao_conclusiva_com_urgencia` existe e o teste de contrato de
   TRM-014 mostra o PL 399/2025 com `apreciacao_texto` vindo dela (ou `null`
   enquanto não aprovada) — nunca o texto de `apreciacao_conclusiva`.
6. `revisar_tramitacao.py --lote L0 --dry-run` e `--lote L4 --dry-run` listam
   exatamente as chaves deste PR.
7. Nenhuma entrada com `pendente` sai de `rascunho` (V-R9). "Devolvida
   ao(à) Autor(a)" entra sem `pendente` (art. 137 conferido duas vezes); a
   frase sobre o Senado em `desfecho_arquivada` entra com
   `pendente: "conferir RISF art. 332 (quórum e prazo do desarquivamento)"`.
8. Todo `texto_curto` se lê sozinho (regra de §2.7): no máximo 2 frases, sem
   "acima", "abaixo", "como dito" (caso de teste do validador).

**Specs técnicas**
- Arquivo: `data/tramitacao/glossario.yml` (só conteúdo; estado em
  `revisao.yml`, escrito pelos scripts de TRM-023).
- Fontes para conferir cada base legal: RICD compilado
  (`www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html`),
  Constituição (`www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm`);
  URLs com âncora quando o site tiver.
- Casos reais para `casos` (ids da Câmara, de 2026-10-30): Chancela → PEC
  63/2023; Autorização → PL 5181/2026; Ag. Análise de Inconstitucionalidade →
  PL 4386/2026; Aguardando Designação de Relator(a) → PL 3747/2026 (CME);
  Aguardando Parecer → PL 2314/2026; Devolução de Relator → PDL 103/2026;
  Pronta para Pauta → PL 5810/2025 (CICS); Tramitando em Conjunto → PL
  2448/2026; Aguardando Apensação → PL 3551/2026; Aguardando Encaminhamento →
  PL 4272/2023; Senado → PL 399/2025; Norma → PDL 571/2026 e PL 2/2024;
  Arquivada → PL 2040/2026; Retirado → PL 823/2025; Perdeu a Eficácia → MPV
  1318/2025; Autorização do Despacho → PL 4437/2024; urgência + conclusiva → PL
  399/2025.

**Testes**
- Do validador (TRM-024): um caso negativo por regra V-E, tirado de §2.4
  ("Leitura errada" de §2.6 serve), e os textos de §2.6–2.8 como positivos.
- Paridade: `tests/unit/test_glossario_termos.py` — todo `termo` de `tipo:
  situacao` bate com o snapshot; toda situação presente em
  `data/tramitacao/amostras/situacoes.json` tem entrada ou está em
  `nao_mapeados` (é a cobertura de M9 aplicada ao glossário).
- Comando: `python scripts/validar_tramitacao.py && python -m pytest tests/unit -k "glossario or tramitacao" -v`.

**Riscos e perguntas em aberto**
- Exatidão jurídica sem revisor especialista (D5). Mitigação: o `juridico`
  confere contra o texto baixado; as bases legais deste rascunho foram
  conferidas no RICD compilado em 2026-10-30, mas isso não substitui o lote.
- "Pronta para Pauta" e "Aguardando Encaminhamento" são ambíguas por natureza;
  os textos dizem isso, e a fase vem da regra, não do glossário.
- As 4 entradas propostas para o L0 mudam o tamanho do lote (6 → 10). Sem
  elas, os 31 casos de MPV, acordo internacional e urgência + conclusiva
  mostram só o termo oficial.
- `base_legal_motivo` para situação administrativa precisa ser aceito em V-R7.

**Instruções para o agente implementador**
- Branches `trm-022-glossario-l0` e `trm-022-glossario-l4`, do `main` depois
  de TRM-021 e TRM-024.
- Ordem: copiar `descricao_oficial` do snapshot → escrever o texto pelo guia
  → conferir cada base legal no texto compilado → rodar o validador → abrir o
  PR "Glossário v0 — L0" (o lote de revisão é TRM-029).
- Verificação: `python scripts/validar_tramitacao.py`,
  `python scripts/revisar_tramitacao.py --lote L0 --dry-run`.
- Não fazer: escrever em `revisao.yml`; marcar `aprovado`; copiar texto do
  Glossário Legislativo do Congresso (só referência, spec.md §6.3-1); pôr data
  ou número de dias sem "úteis"/"corridos"; "melhorar" um termo oficial.

---

## 3. Especificações das tarefas de interface

Ordem de leitura = ordem pedida no brief. Ordem de execução: §5.

### TRM-015 — Página da proposição v0: situação oficial inteira, órgão, regime e apreciação, "Ver na Câmara", recém-apresentada, lei resultante

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E1 Status honesto (F0) · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX (gate principal) + Design System (spec.md §7); Maintainer (textos novos de `textos.ts`)
**Depende de:** TRM-014 (campos de §0.1), TRM-013 (`norma`), TRM-046-A (`textos`, campos novos de `Proposicao` em `lib/api.ts`) e 046-B (fixtures), TRM-033 (`dataBR`), TRM-001, TRM-003; TRM-037 opcional (`Recolhivel`); PR #49 mergeado (mesmo arquivo); lote L0 de TRM-029 **opcional** (acende `regime_texto` e `apreciacao_texto`) · **Publicação:** só depois de TRM-012 executado em produção (`completo`), com as 5 do placar conferidas (critério 8 de TRM-012) — sem isso as 240 sairiam `nao_sincronizada` (`F13`) e a página v0 iria ao ar sem resolver o erro que justifica F0 (D10) · **Desbloqueia:** TRM-040 (`SituacaoCamara` vira o fallback de "Onde está agora"), TRM-041, TRM-042 (estrutura de seções da página)

**Problema**
- A situação oficial está num `Selo` que trunca (`app/proposicoes/[id]/page.tsx:148`).
  Medido em 2026-10-30, a 375 px: "Aguardando Designação - Aguardando
  Devolução de Relator(a) que deixou de ser Membro" (PL 4861/2023) ocupa 539 px
  de texto num espaço de 323 px; o resto fica só no `title`, que não existe no
  toque nem para a maioria dos leitores de tela.
- Não há órgão, regime, forma de apreciação, relatoria, lei resultante nem
  link para a página da Câmara (só o PDF) — disc. §1.5.
- Qualquer falha de rede ou 5xx cai no mesmo caminho: com 500, a página
  guarda o corpo do erro como se fosse a proposição (`page.tsx:72`,
  `setProposicao(await pRes.json())`) e renderiza campos `undefined`.
- "Apresentada em" mostra o dia anterior para quem está no Brasil (§0.5-5).
- 20 acompanhadas têm situação nula porque a API da Câmara devolve nula
  (disc. §1.2); hoje a página simplesmente omite, sem dizer por quê.

**Oportunidade** — É o erro mais visível do site (spec.md §1.3, D10): a
página de uma lei do placar sem status, ou com status truncado. Com os campos
de TRM-014, a página passa a dizer a verdade oficial, inteira, com data de
conferência e o link para conferir — sem depender do mapa de fases.

**Solução**
1. **Cabeçalho.** Chapéu com a espécie por extenso; tirar o `Selo` da
   situação; datas por `dataBR`.
2. **Nova seção "Situação na Câmara"** (`#onde-esta`), logo depois do bloco de
   resumo, ementa e impacto (§1.3), com o componente `SituacaoCamara`.
3. **"Contexto completo"** sai do primeiro bloco e vai para depois de
   "Votações" (§1.3).
4. **Erros**: 404 → `I02`; rede ou 5xx → `I03` com "Tentar de novo".

**Escopo**
- Dentro: `page.tsx` da proposição (cabeçalho, seção nova, ordem, erros,
  esqueleto); `components/tramitacao/SituacaoCamara.tsx` e
  `components/tramitacao/LinhasDaSituacao.tsx` (o bloco `dl`, reusado por
  TRM-040 — S1); testes; CHANGELOG. Os três defeitos de código achados no
  discovery desta parte estão aqui e em TRM-016: dia a menos em "Apresentada
  em" (aqui, linhas 158/262/327, e em TRM-016, linha 228); erro 500 tratado
  como proposição (aqui; na lista, `res.ok` em TRM-016); lista com 100 de 240
  (TRM-016).
- Fora: fase, etapas, "Como sabemos", linha do tempo (F1: TRM-040, TRM-041);
  explicação da situação oficial (glossário L4, TRM-040/045); proposições do
  Senado (`url_camara` nulo → sem link, sem texto novo); converter a página em
  Server Component (fica para quando a página inteira for reescrita — o
  componente novo já nasce sem hooks, pronto para isso).

**Critérios de aceite**
1. Dado o caso 01, em 375, 768 e 1280 px, então o texto "Aguardando
   Designação - Aguardando Devolução de Relator(a) que deixou de ser Membro"
   aparece inteiro uma vez, fora de qualquer `Selo`, com
   `scrollWidth ≤ clientWidth` no elemento e sem rolagem horizontal na página.
2. O cabeçalho não contém a situação; contém o chapéu "Projeto de lei" (caso
   01), "Medida provisória" (caso 15), "Proposta de emenda à Constituição"
   (caso 14), "Projeto de decreto legislativo" (caso 09).
3. Toda proposição com `url_camara` mostra o botão "Ver na Câmara" (`Button variante="fantasma"`), com
   `href = url_camara`, `target="_blank"`, `rel` contendo `noopener` e nome
   acessível "Ver na Câmara o {rótulo} (abre em nova aba)".
4. Os estados `F01`–`F13` da matriz (§4) aparecem com o texto exato quando os
   dados do caso os exigem; `regime_texto`/`apreciacao_texto` nulos mostram
   **só** o termo oficial (`F07b`), e preenchidos mostram o texto do ZIL com o
   termo oficial abaixo (`F07a`).
5. Caso 07 (urgência + conclusiva): a linha "Quem decide" mostra exatamente o
   `apreciacao_texto` da fixture; o componente não tem nenhuma lógica sobre
   regime ou apreciação (teste de unidade com `apreciacao_texto: null` e
   regime de urgência mostra só o termo oficial).
6. Caso 08: "Virou lei: Lei 14.871/2024", "Sancionada com veto parcial: partes
   do texto foram vetadas pelo Presidente da República.", "Ler o texto no
   normas.leg.br" e "Ler o texto no Planalto" (cada link só se a URL existir).
7. Caso 12 (`situacao_estado: recem_apresentada`): `F02`; caso 13 (`sem_situacao`): `F03`; variante `nao_sincronizada`: `F13`.
8. 404 → `I02`; 500 em `/proposicoes/{id}` → `I03`, e "Tentar de novo" refaz
   as três requisições.
9. "Apresentada em" do caso 08 mostra a data da fixture sem deslocamento de
   fuso.
10. "Relatoria" é texto, nunca link para `/parlamentar` (U7; em F0 só existe `relator_nome`).
12. "Órgão atual" vem de `orgao_efetivo_nome`/`orgao_efetivo_sigla`: na
    fixture em que `sigla_orgao` é "CCP" e o órgão efetivo é a CME, a tela
    mostra "Comissão de Minas e Energia (CME)" e nunca "CCP".
13. "Tramita junto com" usa `principal_url_camara` como veio da API (nenhuma
    URL montada no frontend).
11. Gates U1–U14 e S1–S10 marcados; 0 violações axe em 375/768/1280 × escuro e
    claro nos casos 01, 08, 12, 14.

**Specs técnicas**
- `apps/web/components/tramitacao/SituacaoCamara.tsx` (novo, sem hooks, sem
  `"use client"`):
  ```ts
  export function SituacaoCamara(props: { proposicao: Proposicao; glossario?: GlossarioApi[] | null; definicaoAberta?: boolean }): JSX.Element
  ```
  Usa `dataBR` (TRM-033), `rotuloProposicao`, `nomeEspecie`, `prefixoNorma` e
  `TEXTOS` (TRM-046-A). Não chama a API. `glossario` e `definicaoAberta` só
  são passados por TRM-040 no fallback `N06` (situação oficial como
  `TermoGlossario` aberto, por `situacao_glossario`); em F0 ficam ausentes e a
  situação é texto puro.
- `apps/web/components/tramitacao/LinhasDaSituacao.tsx` (novo, sem hooks) —
  o `dl` "Órgão atual / Última movimentação / Regime / Quem decide /
  Relatoria / Tramita junto com", usado por `SituacaoCamara` e, em TRM-040,
  por `OndeEsta` (revisão do DS, DS-UI-06):
  ```ts
  export function LinhasDaSituacao(props: {
    orgao: { nome: string | null; sigla: string | null } | null;   // F0: orgao_efetivo_*; F1: onde_esta.orgao_nome/sigla_orgao
    ultimaMovimentacao: string | null;                             // ISO; exibido por dataBR
    regime: string | null; regimeTexto: string | null;             // F06/F07a/F07b
    apreciacao: string | null; apreciacaoTexto: string | null;
    relator: { nome: string; partido: string | null; uf: string | null; parlamentarId: string | null } | null;
    principal: { rotulo: string; href: string; externo: boolean } | null;  // F11 (F0) — em F1 a apensada vai no aviso A01/A02, não aqui
  }): JSX.Element | null   // null quando nenhuma linha tem dado
  ```
- `apps/web/lib/api.ts`: os campos de `Proposicao` são os do bloco de
  TRM-046-A (tipos idênticos ao contrato); esta tarefa não redeclara.
- `apps/web/app/proposicoes/[id]/page.tsx`:
  - estado `erro: "nao_encontrada" | "falha" | null` e `tentativa` (padrão já
    usado na lista, `app/proposicoes/page.tsx:58-59`); `pRes.status === 404` →
    `"nao_encontrada"`; `!pRes.ok` ou exceção → `"falha"`; votações e contexto
    continuam opcionais (falha neles não derruba a página);
  - cabeçalho: `<p className="text-rotulo uppercase text-zil-texto-2">{nomeEspecie(tipo)}</p>`
    antes do `h1`; remover a linha 148; trocar `new Date(...).toLocaleDateString`
    por `dataBR` nas linhas 158 e 262 e na lista de votações (327); se
    TRM-037 estiver no `main`, trocar `SumarioLinha` por `Recolhivel`;
  - depois do bloco resumo/ementa/impacto, fechar a `section` e abrir:
    ```tsx
    <section id="onde-esta" aria-labelledby="onde-esta-titulo" className="scroll-mt-24 grid gap-4 pb-16 md:pb-24">
      <h2 id="onde-esta-titulo" className="text-titulo-3">Situação na Câmara</h2>
      <SituacaoCamara proposicao={proposicao} />
    </section>
    ```
  - "Votações" ganha `id="votacoes"` e `aria-labelledby`; "Contexto completo"
    passa para depois dela, sem outra mudança;
  - esqueleto: acrescentar um `CardEsqueleto` com `h2` falso para a seção
    nova (a forma do conteúdo real, regra do kit).
- CHANGELOG: `Fixed` (situação truncada, data com um dia a menos, erro 500
  tratado como "não encontrada") e `Added` (situação na Câmara, link para a
  Câmara, lei resultante).

**Specs de design**

Wireframe 375 px:
```
┌───────────────────────────────────────┐
│ ‹ Todas as proposições                │
│ PROJETO DE LEI                        │ chapéu (text-rotulo)
│ PL 4861/2023                          │ h1 (text-titulo-1)
│ (● Energia) (● Análise disponível)    │ selos — sem situação
│ Apresentada em 12/10/2023 ·           │
│ Texto completo ↗                      │
│ ┌───────────────────────────────────┐ │
│ │ EM LINGUAGEM SIMPLES …            │ │ (existe)
│ └───────────────────────────────────┘ │
│ ▸ Ementa técnica                      │ (existe)
│                                       │
│ Situação na Câmara                    │ h2 (text-titulo-3)
│ ┌───────────────────────────────────┐ │ Card, gap-5
│ │ SITUAÇÃO OFICIAL                  │ │ text-rotulo
│ │ Aguardando Designação - Aguardando│ │ text-texto font-medium,
│ │ Devolução de Relator(a) que deixou│ │ quebra livre
│ │ de ser Membro                     │ │
│ │                                   │ │
│ │ Órgão atual                       │ │ dt em cima,
│ │ Comissão de Minas e Energia (CME) │ │ dd embaixo
│ │ Última movimentação               │ │
│ │ 19/07/2026                        │ │
│ │ Regime                            │ │
│ │ Segue o ritmo normal da Câmara.   │ │ regime_texto (F07a)
│ │ Cada comissão tem até 40 sessões… │ │
│ │ Na Câmara: Ordinário (Art. 151,   │ │ termo oficial, texto-s
│ │ III, RICD)                        │ │
│ │ Quem decide                       │ │
│ │ As comissões decidem. Se …        │ │
│ │                                   │ │
│ │ Conferido na Câmara em 30/10/2026 │ │ text-texto-s texto-2
│ │ [ Ver na Câmara ↗ ]               │ │ Button fantasma s
│ └───────────────────────────────────┘ │
│ Votações (0)                          │
│ ▸ Contexto completo                   │ movido para o fim
└───────────────────────────────────────┘
```

Wireframe 1280 px (conteúdo em `zil-container`; o cartão até `max-w-3xl`):
```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ‹ Todas as proposições                                                                    │
│ PROJETO DE LEI                                                                            │
│ PL 2/2024                                                                (display-m)      │
│ (● Indústria) (● Análise disponível)                                                     │
│ Apresentada em 03/01/2024 · Texto completo ↗                                              │
│ [Em linguagem simples ……………………………………………………………………………………………………]                            │
│ [▸ Ementa técnica …………………………………………………………………………………………………]                            │
│                                                                                           │
│ Situação na Câmara                                                                        │
│ ┌────────────────────────────────────────────────────────────────┐                       │
│ │ Virou lei: Lei 14.871/2024                       (titulo-4)     │                       │
│ │ Sancionada com veto parcial: partes do texto foram vetadas …    │                       │
│ │ Ler o texto no normas.leg.br ↗   Ler o texto no Planalto ↗      │                       │
│ │ SITUAÇÃO OFICIAL                                                │                       │
│ │ Transformado em Norma Jurídica                                  │                       │
│ │ Órgão atual ……… Mesa Diretora da Câmara dos Deputados (MESA)    │ dl em 2 colunas        │
│ │ Última movim. … 28/05/2024                                      │ md:grid-cols-          │
│ │ Regime ………………… O Presidente da República pediu urgência …     │ [11rem_minmax(0,1fr)]  │
│ │                  Na Câmara: Urgência (Art. 64, CF)              │                       │
│ │ Quem decide …… Depois das comissões, quem decide é o Plenário … │                       │
│ │ Conferido na Câmara em 30/10/2026   [ Ver na Câmara ↗ ]         │                       │
│ └────────────────────────────────────────────────────────────────┘                       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

Anatomia de `SituacaoCamara` (ordem de leitura = ordem do DOM):
1. Bloco da norma (`F04`/`F05`), quando houver.
2. "Situação oficial" (`text-rotulo uppercase text-zil-texto-2`) + o texto
   (`text-texto font-medium`) ou, por `situacao_estado`, `F02`/`F03`/`F13`.
3. `LinhasDaSituacao` → `<dl className="grid gap-x-6 gap-y-3 md:grid-cols-[11rem_minmax(0,1fr)]">`
   com, nesta ordem e só quando houver dado: "Órgão atual" (`F10`, órgão efetivo), "Última
   movimentação", "Regime" (`F06`–`F08`), "Quem decide", "Relatoria" (`F12`),
   "Tramita junto com" (`F11`). `dt`: `text-texto-s font-medium
   text-zil-texto-2`; `dd`: `text-texto`; termo oficial dentro do `dd`:
   `<span className="block text-texto-s text-zil-texto-2">Na Câmara: {termo}</span>`.
4. Rodapé: "Conferido na Câmara em …" (`F09`) e o botão "Ver na Câmara".

Estados (textos exatos na matriz, §4): `I01`, `I02`, `I03`, `F01`–`F13`, `X01`.
"Recém-apresentada" é `F02`; "apensada com link para a principal" é `F11`;
"norma resultante com link" é `F04`; desfechos e `nao_sabemos` são F1
(TRM-040) — em F0 o desfecho aparece só como a situação oficial ("Arquivada",
"Perdeu a Eficácia"), inteira.

Interações: nenhuma nova além de links e do "Tentar de novo". Foco, na seção:
links de "Tramita junto com" e "Relatoria" (se houver) → "Ler o texto no
normas.leg.br" → "Ler o texto no Planalto" → "Ver na Câmara". (O bloco da
norma vem antes no DOM; a ordem acima é a de tabulação real: norma, depois
`dl`, depois rodapé.)

Responsividade: 375 — `dt` sobre `dd`, botão na própria linha; 768 — `dl` em
duas colunas; 1280 — cartão com `max-w-3xl`, alinhado à esquerda como os
demais cartões de texto.

Acessibilidade: `section` com `aria-labelledby` (landmark); um `h1`, `h2`
"Situação na Câmara"; `dl` semântica; link externo com `sr-only` (§0.5-6);
nada depende de cor; contraste pelos tokens (`text-zil-texto-2` sobre
`superficie-1` ≈ 6,5:1 no escuro); nenhum movimento novo; o foco no botão
"Ver na Câmara" não fica sob a tab bar a 375 px (U9); reflui a 320 px
(1.4.10).

**Testes**
- Vitest — `apps/web/tests/componentes/tramitacao/SituacaoCamara.test.tsx`: um
  teste por estado `F01`–`F13` (texto exato com `getByText(…, { exact: true })`);
  a situação não tem ancestral com classe `truncate` nem `line-clamp-*`;
  `F07a`/`F07b`; urgência + `apreciacao_texto: null` mostra só o termo
  oficial; nenhum `<a>` aponta para `/parlamentar`; `classesDeAlinhamento`
  vazio; `axe` sem violações em cada estado.
- Vitest — `apps/web/tests/componentes/tramitacao/LinhasDaSituacao.test.tsx`:
  ordem das linhas; linha omitida sem dado; `null` sem nenhuma linha;
  `F06`/`F07a`/`F07b`; órgão efetivo; axe.
- Playwright — `apps/web/tests/e2e/paginas/proposicao-f0.spec.ts`, nos três
  projetos: casos 01, 05, 06, 07, 08, 09, 10, 12, 13, 14, 15; 404 e 500 com
  `api.responder("/proposicoes/<id>", { status: 404 | 500 })`; asserções:
  critérios 1–13; `page.locator("header")` não contém o texto da situação;
  `semRolagemHorizontal` com a tag `@reflow`; ordem dos `h2` = ["Situação na
  Câmara", "Votações (0)"]; a 375 px,
  `focoVisivelENaoEncoberto(page, page.getByRole("link", { name: /^Ver na Câmara/ }))`;
  `semViolacoes` e `expectPaletaNeutra(page, "#onde-esta")` nos dois temas
  (não nos estados `I03`, cujo `Aviso contra` é o tom do kit para erro).
- Comandos: `cd apps/web && npx vitest run tests/componentes/tramitacao/SituacaoCamara.test.tsx tests/componentes/tramitacao/LinhasDaSituacao.test.tsx`
  e `npx playwright test tests/e2e/paginas/proposicao-f0.spec.ts`.

**Riscos e perguntas em aberto**
- `orgao_efetivo_nome` pode faltar (órgão sem nome no cadastro): "Órgão
  atual" mostra só a sigla. Funciona, mas é jargão.
- `regime_texto`/`apreciacao_texto` só acendem com o lote L0 aprovado; antes
  disso a página mostra `F07b` (só o termo oficial) — seguro, só menos útil.
- Publicar antes do sync em produção mostraria `F13` em todas: por isso a
  linha "Publicação" no topo.
- PR #49 toca o mesmo arquivo: rebasear depois do merge.

**Instruções para o agente implementador**
- Branch `trm-015-situacao-na-camara`, do `main` com TRM-014, TRM-046 e o PR
  #49 mergeados.
- Ordem (TDD, spec.md §8.3): testes de `LinhasDaSituacao` e `SituacaoCamara` →
  componentes → testes e2e → edição da página → provas.
- Verificação: `cd apps/web && npm run lint && npx tsc --noEmit && npm run test && npm run build && npm run test:e2e`.
- Prova no PR: `registrarEvidencia` dos casos 01, 08, 12 e 14 (375/768/1280 ×
  escuro/claro, artefato `evidencias-ui`); JSON do axe; lista dos testes.
- Não fazer: pôr a situação em `Selo`; escrever "desde" com
  `ultima_movimentacao_em`; escrever explicação de regime no frontend; decidir
  no componente se a apreciação vale ou não (é da API, §2.7); link para
  `/parlamentar`; criar um `<details>` próprio (use `Recolhivel` ou deixe o
  `SumarioLinha` como está).

### TRM-016 — Lista de proposições v0: situação sem truncar, "Última movimentação em", ordenação por movimentação

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E1 Status honesto (F0) · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** P
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX + Design System; Maintainer (textos)
**Depende de:** TRM-014 (`ultima_movimentacao_em`, `norma`, `X-Total-Count`), TRM-012 (para o dado ser atual), TRM-046-A (textos, campos de `Proposicao`) e 046-B (`listarTodasProposicoes`, fixtures), TRM-033 (`dataBR`), TRM-001 (API falsa com `responderPaginas` e CORS), TRM-003 · **Publicação:** só depois de TRM-012 executado em produção (`completo`), como TRM-015 · **Desbloqueia:** TRM-043

**Problema**
- Situação em `Selo` truncado em cada cartão (`app/proposicoes/page.tsx:215`).
- **A lista mostra só 100 das 240 acompanhadas**: pede `per_page=100`
  (`page.tsx:66`), a API limita a 100 e não há paginação; a contagem "UI-003"
  diz "100 proposições". A busca textual e a ordenação, feitas no cliente,
  também só enxergam essas 100.
- Não há data de movimentação nem ordenação por ela; "quais estão andando?"
  não tem resposta.
- Sem `res.ok` (`page.tsx:71-72`): um 500 com corpo JSON vira objeto em
  `proposicoes` e `.filter` quebra a página.
- "Apresentada em" com um dia a menos (`page.tsx:228`).

**Oportunidade** — A lista passa a responder "o que andou por último" e "o
que virou lei" sem abrir cada proposição, e deixa de esconder 58% do acervo.

**Solução**
1. Carregar todas as páginas com `listarTodasProposicoes(params)` (TRM-046-B):
   pede `page=1,2,…` com `per_page=100` até ter lido `X-Total-Count` itens
   (sem o cabeçalho, até vir uma página com menos de 100; máximo 20 páginas);
   o total do cabeçalho é o que a contagem mostra; se a primeira falhar,
   `I09`; se uma posterior falhar, mostra o que veio e `I10`.
2. Extrair o cartão para `components/tramitacao/CartaoProposicao.tsx`.
3. Cartão: tirar o `Selo` da situação; acrescentar a linha "Virou lei: …"
   (`F04`, versão curta), a linha "Situação na Câmara: …" e a linha "Última
   movimentação em … · Apresentada em …".
4. Ordenação (`Seletor` que já existe): opções "Movimentação mais recente"
   (`movimentacao`), "Apresentação mais recente" (`recentes`), "Apresentação
   mais antiga" (`antigas`); sem escolha, vale a ordem da API (analisadas
   primeiro), como hoje.
5. Contagem com `aria-live="polite"`.

**Escopo**
- Dentro: `app/proposicoes/page.tsx`, `CartaoProposicao`, testes.
- Fora: filtro e selo de fase (TRM-043); ordenação no servidor
  (`ordem=movimentacao`, que TRM-014 já oferece) — a lista ordena no cliente
  porque a busca textual e o filtro "Análise" também são no cliente (ver
  riscos).

**Critérios de aceite**
1. Com `lista-p1`+`lista-p2` (130 itens, `X-Total-Count: 130`), a contagem diz
   "130 proposições", há 130 cartões e foram feitas exatamente 2 requisições
   a `/proposicoes` (`api.chamadas`).
2. Nenhuma situação dentro de `Selo`; o texto do caso 01 aparece inteiro no
   cartão (`scrollWidth ≤ clientWidth`), sem rolagem horizontal da página
   em 375/768/1280.
3. "Movimentação mais recente" põe primeiro o item com a maior
   `ultima_movimentacao_em`; itens sem a data vão para o fim; empate decidido
   por `fonte_id` decrescente (ordem estável).
4. Cartão: nome acessível do link = "{tipo} {numero}/{ano}" (via
   `aria-labelledby` no `h2`); descrição acessível = linha da situação + linha
   de datas (via `aria-describedby`).
5. Falha na página 2 → os 100 primeiros aparecem e `I10` com "Carregamos 100
   proposições, …"; falha na página 1 → `I09`.
6. "Apresentada em" sem deslocamento de fuso.
7. Gates de §7; 0 violações axe nos 3 breakpoints × 2 temas.

**Specs técnicas**
- `apps/web/components/tramitacao/CartaoProposicao.tsx` (sem hooks):
  ```ts
  export function CartaoProposicao(props: { proposicao: Proposicao; fase?: React.ReactNode }): JSX.Element
  ```
  `fase` é o encaixe que TRM-043 usa para o `FaseSelo`; em TRM-016 fica vazio.
- `apps/web/app/proposicoes/page.tsx`: `load()` usa `listarTodasProposicoes`;
  estado `incompleta: boolean`; a ordenação usa
  `ordenarProposicoes(lista, ordem)` de `lib/tramitacao/ordenacao.ts` (novo,
  função pura, com teste); `ORDENS` com os três valores; o cartão inline
  (linhas 213-231) vira `<CartaoProposicao>`.

**Specs de design**

Wireframe 375 px (cartão):
```
┌───────────────────────────────────────┐
│ (● Energia) (● Análise disponível)    │ selos (sem situação)
│ PL 4861/2023                          │ h2 text-titulo-4
│ Altera a Lei nº … para …              │ resumo/ementa, line-clamp-3
│ (3 linhas)                            │
│ Situação na Câmara: Aguardando        │ text-texto-s; rótulo texto-2,
│ Designação - Aguardando Devolução de  │ situação em texto, inteira
│ Relator(a) que deixou de ser Membro   │
│ Última movimentação em 19/07/2026 ·   │ text-texto-s texto-2 zil-num
│ Apresentada em 12/10/2023             │
└───────────────────────────────────────┘
```
Cartão que virou lei, 1280 px (duas colunas de cartões, como hoje):
```
┌──────────────────────────────────────────┐ ┌──────────────────────────────────────────┐
│ (● Indústria) (● Análise disponível)     │ │ (● Energia)                              │
│ PL 2/2024                                │ │ PL 1264/2024                             │
│ Permite que empresas descontem …         │ │ …                                        │
│ Virou lei: Lei 14.871/2024               │ │ Situação na Câmara: Aguardando           │
│ Situação na Câmara: Transformado em      │ │ Designação de Relator(a)                 │
│ Norma Jurídica                           │ │ Última movimentação em 09/05/2025 ·      │
│ Última movimentação em 28/05/2024 ·      │ │ Apresentada em 10/04/2024                │
│ Apresentada em 03/01/2024                │ │                                          │
└──────────────────────────────────────────┘ └──────────────────────────────────────────┘
```

Anatomia do cartão (ordem do DOM): encaixe `fase` (vazio em TRM-016) e selos
existentes → `h2` → resumo → "Virou lei: {norma.rotulo}" (`text-texto-s
font-medium`, só com `norma`; prefixo por `prefixoNorma`) → "Situação na
Câmara: …" → linha de datas (cada parte só se houver dado).

Estados: `I08` (carregando, existe), `I09` (erro, existe), `I10`
(incompleta, novo), `I11`/`I12` (vazio, existem), `L01`–`L03` (cartão).

Interações: ordenação muda a ordem sem nova requisição; foco permanece no
`Seletor`; a contagem é anunciada (`aria-live="polite"`).

Responsividade: 375 — uma coluna, cartões como hoje; 768 e 1280 — duas
colunas (`md:grid-cols-2`, como hoje). A linha da situação quebra livremente.

Acessibilidade: o `Card` recebe `aria-labelledby={idTitulo}` e
`aria-describedby={`${idSituacao} ${idDatas}`}` (ids com `useId` no pai, ou
derivados do `id` da proposição: `p-{id}-titulo`); sem link aninhado no
cartão; nada depende de cor.

**Testes**
- Vitest: `tests/unit/tramitacao/ordenacao.test.ts` (três ordens, nulos no fim,
  empate estável); `tests/componentes/tramitacao/CartaoProposicao.test.tsx` (`L01`–`L03`, `F04` curto,
  nome e descrição acessíveis com `getByRole("link", { name: "PL 4861/2023", description: /Situação na Câmara/ })`,
  axe).
- Playwright `apps/web/tests/e2e/paginas/lista-f0.spec.ts`: critérios 1–6;
  lista servida com
  `api.responderPaginas("/proposicoes", ["tramitacao/lista-p1", "tramitacao/lista-p2"], { alem: { status: 200, corpo: [] } })`
  e, para o critério 5, `{ falharNaPagina: 2 }` (API falsa unificada de
  TRM-001; nenhum helper novo); `semRolagemHorizontal` com `@reflow`;
  `semViolacoes` e `expectPaletaNeutra(page, "main")` nos dois temas (fora do
  estado `I09`).
- Comandos: `npx vitest run tests/unit/tramitacao tests/componentes/tramitacao/CartaoProposicao.test.tsx`,
  `npx playwright test tests/e2e/paginas/lista-f0.spec.ts`.

**Riscos e perguntas em aberto**
- Carregar tudo no cliente escala até algumas centenas de itens. Se o
  acervo passar de ~1.000, trocar por paginação no servidor
  (`ordem=movimentacao`, `X-Total-Count` e `Paginacao`, que a API já
  oferece) e levar a busca textual para a API.
- A ordem padrão continua "analisadas primeiro" (decisão anterior do projeto).
  Se a maintainer quiser "movimentação mais recente" como padrão, é uma linha.

**Instruções para o agente implementador**
- Branch `trm-016-lista-situacao`, do `main` com TRM-014 e TRM-046.
- Ordem: `ordenacao.ts` + teste → `CartaoProposicao` + teste → página → e2e →
  provas.
- Verificação e prova: como em TRM-015 (rota `/proposicoes`, `lista-p1`/`lista-p2`).
- Não fazer: filtro de fase (TRM-043); `line-clamp` na situação; mudar a
  ordem padrão sem decisão.

### TRM-040 — Página da proposição: "Onde está agora" v1

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E4 Experiência · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX (gate principal) + Design System; Maintainer (textos de `textos.ts` que forem novos)
**Depende de:** TRM-028 (endpoint e campos de F1 em `ProposicaoRead`), TRM-027, TRM-030 (`Etapas` v2), TRM-031 (`FaseSelo`), TRM-033 (`ComoSabemos`), TRM-035 (`TermoGlossario`; **acrescentar ao índice do PM**, que não a lista), TRM-037 (`Recolhivel`), TRM-046-B, TRM-047 (destino de "Como sabemos"), TRM-015 (`SituacaoCamara`, estrutura da página) · **Publicação:** incremental pelos lotes L1–L3 de TRM-029 (spec.md D11): sem eles, toda proposição cai em `N06`, que mostra a situação oficial — seguro por construção · **Desbloqueia:** TRM-041, TRM-042 (mesmo orquestrador)

**Problema** — Depois de F0 a página diz a situação oficial, mas não traduz
em que ponto do caminho a proposição está, nem quanto falta, nem como o ZIL
chegou a isso. "Pronta para Pauta" não diz se é comissão ou Plenário
(disc. §1.1); "Tramitando em Conjunto" não diz com quem nem em que fase. O
kit tem `Etapas` e nenhuma página usa (disc. §1.5).

**Oportunidade** — Responder "onde está?" numa frase de template, com a
posição no rito ("Etapa 2 de 6"), a explicação da fase e a proveniência
("Como sabemos") ao lado da situação oficial — a primeira leitura do
cidadão deixa de depender de jargão.

**Solução**
1. `components/tramitacao/TramitacaoProposicao.tsx` (`"use client"`), que
   recebe a proposição já carregada, busca em paralelo
   `obterTramitacao(id)` e `obterMapa()` (TRM-046-B) e renderiza a seção
   `#onde-esta` (e, depois, as de TRM-041 e TRM-042). Substitui, em
   `page.tsx`, a seção que TRM-015 criou.
2. `components/tramitacao/OndeEsta.tsx` (sem hooks): a seção por estado,
   escolhido por `estadoDeExibicao(onde_esta)` (TRM-046).
3. `FaseSelo` no cabeçalho da página, por `faseSeloPropsDe(proposicao)` (TRM-046-B),
   a partir dos campos de F1 de `ProposicaoRead` — aparece sem esperar
   `/tramitacao`.
4. Fallback: falha (`I05`), 404 (`I06`), `mapa_nao_aprovado` (`N06`) ou fase
   ainda não calculada (`sem_fase`, sem aviso) → `SituacaoCamara` dentro da
   mesma seção.

**Escopo**
- Dentro: o orquestrador, `OndeEsta`, o `FaseSelo` do cabeçalho, o `h2`
  "Onde está agora", testes, CHANGELOG.
- Fora: "O que vem depois" agendado ou previsto pelo despacho (TRM-051,
  TRM-052); "Depois da lei" (TRM-053); linha do tempo (TRM-041); rito
  completo (TRM-042); a página `/como-vira-lei/situacoes` e o `href` "Ver
  no glossário" do termo (TRM-045).

**Critérios de aceite**
1. Caso 02: cabeçalho com `FaseSelo` "Nas comissões" (link para
   `/como-vira-lei?especie=PL&casa=camara#fase-comissoes`); seção com a
   `frase` da fixture, `Etapas` com a 2ª etapa `aria-current="step"`, legenda
   visível "Etapa 2 de 6: Nas comissões", a explicação da fase, `T01`, a
   situação oficial como `TermoGlossario` com a definição do glossário, "Regime", "Quem decide",
   "Conferido na Câmara em …", "Ver na Câmara" e "Como sabemos".
2. Cada fase (casos 02, 04, 07, 08, 12, 14, 22–25), cada desfecho (15–21),
   cada apensada (05, 06) e cada motivo de `nao_sabemos` (11, 26–30) mostra
   os textos exatos das linhas correspondentes da matriz (§4).
3. Caso 30 (`mapa_nao_aprovado`): sem `FaseSelo` no cabeçalho; a seção
   mostra `N06` e, abaixo, o conteúdo de `SituacaoCamara`, com a situação
   oficial como `TermoGlossario` **aberto** (`abertoInicial`) quando
   `situacao_glossario` aponta para entrada publicável; nenhum texto "Fase não
   identificada".
3a. Caso 05 (`herdada_de.acompanhada: true`): `A01`, ação "Ver a proposição
    principal" para `/proposicoes/{herdada_de.id}`. Caso 06 (`id` preenchido,
    `acompanhada: false`): `A02`, ação para `herdada_de.url_camara`, abre em
    nova aba.
3b. Caso 11 (`nao_sabemos`): `FaseSelo` "Fase não identificada" no cabeçalho é
    link para `/metodologia#tramitacao`, com nome terminado em ", entenda por
    quê" (decisão de §1.2).
4. Caso 12 (F1): `FaseSelo` "Recém-apresentada" (rótulo da API); `R01` no lugar da situação
   oficial; nenhum texto de `nao_sabemos`.
5. Desfecho: a etapa onde parou tem estado `interrompida` e legenda
   "Parou na etapa {i} de {n}: {nome}"; a explicação visível é a do
   desfecho; a situação oficial continua como `TermoGlossario`.
6. Caso 08 (norma): legenda "Etapa 6 de 6: Virou lei" (`legendaDasEtapas`);
   bloco "Virou lei" com links (`F04`); sem `T01`.
7. 500 em `/tramitacao` → `I05` + `SituacaoCamara`; "Tentar de novo" refaz só
   `/tramitacao` e `/tramitacao/mapa`. 404 → `SituacaoCamara`, sem aviso.
   Falha só no mapa → a seção aparece sem explicações de glossário (`I07`).
8. `animacoesInfinitas(page, "#onde-esta")` = 0 depois de carregado, com e
   sem `reducedMotion: "reduce"`.
9. `classesDeAlinhamento` vazio em todo estado (Vitest) e
   `expectPaletaNeutra(page, "#onde-esta")` nos dois temas (e2e) — inclusive
   nos avisos de `nao_sabemos`.
10. Leitor de tela: a `<ol>` tem nome "Etapas da tramitação"; o item atual
    tem `aria-current="step"` e o texto "Etapa 2 de 6: Nas comissões (etapa
    atual)" (asserção com `toMatchAriaSnapshot`).
11. Gates de §7; 0 violações axe em 375/768/1280 × 2 temas nos casos 02, 05,
    08, 11, 15 e 30.

**Specs técnicas**
- `apps/web/components/tramitacao/TramitacaoProposicao.tsx`:
  ```ts
  "use client";
  export function TramitacaoProposicao(props: { proposicao: Proposicao }): JSX.Element
  // estado: { carregando: boolean; tramitacao: TramitacaoApi | null; status: "ok" | "ausente" | "falha"; mapa: MapaApi | null; tentativa: number }
  ```
  `ausente` = 404; `falha` = rede ou 5xx. O mapa falhar não muda `status`.
- `apps/web/components/tramitacao/OndeEsta.tsx`:
  ```ts
  export function OndeEsta(props: {
    proposicao: Proposicao;
    tramitacao: TramitacaoApi;
    glossario: GlossarioApi[] | null; // de lib/tramitacao/tipos.ts; null = mapa indisponível (I07)
  }): JSX.Element
  ```
  Definição da situação (pela chave pronta da API, nunca por texto —
  revisão da Arquitetura, item 3):
  ```ts
  const chave = tramitacao.onde_esta.situacao_glossario;
  const d = glossario && chave ? definicaoDoTermo(glossario, chave) : null; // texto_curto; só publicável
  ```
  `d` nulo ou `d.definicao` nula → texto puro + `G01`. Explicação da fase, do
  desfecho e da apensada, passando pela defesa de `publicavel` do kit:
  ```ts
  const explicacao = (c: string) => {
    const g = glossario?.find((e) => e.chave === c);
    return g ? entradaDaApi(g).texto : null; // entradaDaApi zera texto não publicável
  };
  // c = "fase_" + fase | "desfecho_" + desfecho | "apensada"
  ```
- `apps/web/app/proposicoes/[id]/page.tsx`: o `FaseSelo` entra no cabeçalho,
  antes das categorias; a seção `#onde-esta` passa a ser
  `<TramitacaoProposicao proposicao={proposicao} />`.
- Usa de TRM-046-B: `obterTramitacao`, `obterMapa`, `estadoDeExibicao`,
  `faseSeloPropsDe`; de TRM-046-A: `TEXTOS`; de TRM-015: `SituacaoCamara`,
  `LinhasDaSituacao`; do kit: `Etapas`, `comoSabemosDaFase`, `dataBR`,
  `definicaoDoTermo`, `entradaDaApi`, `hrefDoTermo`.

**Specs de design**

Wireframe 375 px (caso 02):
```
┌───────────────────────────────────────┐
│ PROJETO DE LEI                        │
│ PL 1264/2024                          │
│ (● Nas comissões ›) (● Indústria)     │ FaseSelo link + categorias
│ …                                     │
│ Onde está agora                       │ h2
│ ┌───────────────────────────────────┐ │ Card
│ │ Nas comissões da Câmara. Está na  │ │ frase (text-texto-l)
│ │ Comissão de Finanças e Tributação │ │
│ │ (CFT) desde 09/05/2025.           │ │
│ │                                   │ │
│ │ ▬▬▬▬ ▬▬░░ ░░░░ ░░░░ ░░░░ ░░░░     │ │ Etapas variante compacta:
│ │                                   │ │ cheia, meia, trilho (forma)
│ │ Etapa 2 de 6: Nas comissões       │ │ legendaDasEtapas (visível)
│ │                                   │ │
│ │ Comissões são grupos de deputados │ │ explicação da fase
│ │ por assunto. Em cada uma, …       │ │ (text-texto texto-2)
│ │ O ZIL não estima quando a         │ │ T01
│ │ proposição vai avançar: isso      │ │
│ │ depende de quem conduz esta etapa.│ │
│ │                                   │ │
│ │ SITUAÇÃO OFICIAL NA CÂMARA        │ │
│ │ Aguardando Designação de          │ │ TermoGlossario (gatilho no
│ │ Relator(a) ⌄                      │ │ próprio termo; toque abre)
│ │ ┊ A proposição está numa comissão │ │ definição no fluxo
│ │ ┊ e espera que o presidente da …  │ │
│ │ ┊ Base: Regimento da Câmara, …    │ │
│ │ ┊ Texto do ZIL, não oficial ·     │ │ nota (G02) + href
│ │ ┊ Ver no glossário                │ │
│ │                                   │ │
│ │ Regime                            │ │ dl
│ │ Tem preferência sobre a …         │ │
│ │ Na Câmara: Prioridade (Art. 151,  │ │
│ │ II, RICD)                         │ │
│ │ Quem decide                       │ │
│ │ Depois das comissões, quem decide │ │
│ │ é o Plenário da Câmara, …         │ │
│ │ Última movimentação               │ │
│ │ 09/05/2025                        │ │
│ │                                   │ │
│ │ Conferido na Câmara em 30/10/2026 │ │
│ │ [ Ver na Câmara ↗ ]               │ │
│ │ ▸ Como sabemos                    │ │ ComoSabemos (fechado)
│ └───────────────────────────────────┘ │
└───────────────────────────────────────┘
```

Wireframe 1280 px (caso 05, apensada):
```
┌ Onde está agora ─────────────────────────────────────────────────────────────────────────┐
│ ┌ (i) Tramita junto com o PL 5941/2013 ──────────────────────────────────────────────────┐│ Aviso padrao
│ │ PL 5941/2013 é a proposição principal. As duas andam juntas e recebem um parecer só;   ││
│ │ por isso, a fase mostrada aqui é a da principal.         [ Ver a proposição principal ] ││
│ └────────────────────────────────────────────────────────────────────────────────────────┘│
│ Tramita junto com o PL 5941/2013, a proposição principal. No Plenário da Câmara desde      │ frase
│ 12/03/2025, onde votam todos os deputados.                                                 │
│ ▬▬▬▬▬▬▬▬▬▬ ▬▬▬▬▬▬▬▬▬▬ ▬▬▬▬▬░░░░░ ░░░░░░░░░░ ░░░░░░░░░░ ░░░░░░░░░░                       │ Etapas compacta
│ Etapa 3 de 6: No Plenário da Câmara                                                        │ legenda
│ ┌──────────────────────────────────────────────┐  ┌──────────────────────────────────────┐ │ lg:grid-cols-
│ │ Todos os deputados podem votar a proposição. │  │ Regime        Tramitação ordinária…  │ │ [minmax(0,1fr)_
│ │ Quem decide quando ela entra na pauta é …    │  │ Quem decide   Depois das comissões…  │ │ minmax(0,24rem)]
│ │ O ZIL não estima quando a proposição vai …   │  │ Última mov.   12/03/2025             │ │ (sem cartão dentro
│ │ SITUAÇÃO OFICIAL NA CÂMARA                   │  │                                      │ │ de cartão: só grid)
│ │ Tramitando em Conjunto ⌄   (TermoGlossario)  │  │                                      │ │
│ └──────────────────────────────────────────────┘  └──────────────────────────────────────┘ │
│ Conferido na Câmara em 30/10/2026   [ Ver na Câmara ↗ ]   ▸ Como sabemos                   │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

Anatomia (ordem do DOM; cada parte só quando houver dado):
1. Aviso de apensada (`A01`/`A02`) — `Aviso tom="padrao"`.
2. Aviso de `nao_sabemos` (`N01`–`N05`) — `Aviso tom="padrao"` (sem âmbar:
   decisão 1 do DS), título e corpo da matriz; ou nota `N06`, também
   `tom="padrao"`.
3. Frase (`onde_esta.frase`) — `text-texto-l`. Ausente em `nao_sabemos`.
4. Bloco da norma (`F04`/`F05`) quando `fase === "norma"`.
5. `<Etapas variante="compacta" etapas={…} />` (`rotulo` padrão "Etapas da
   tramitação") — o componente já mostra a legenda ("Etapa 2 de 6: …"); a
   página **não** renderiza `legendaDasEtapas` de novo (a função só serve se a
   frase for necessária em outro lugar). Ausente em `nao_sabemos` e com
   `etapas` vazio (o componente devolve `null`).
6. Explicação da fase ou do desfecho (`texto` de `fase_<fase>` ou
   `desfecho_<desfecho>` no glossário; `text-texto text-zil-texto-2`) + `T01`
   quando a fase não é `sancao`, `norma` nem desfecho.
7. Situação oficial: rótulo "Situação oficial na Câmara"; o texto inteiro
   como `<TermoGlossario indicador definicao={d.definicao} baseLegal={d.baseLegal}>`
   (nota padrão do kit = `G02`; sufixo lido = `G03`; `href` =
   `hrefDoTermo(chave)` — o `href` entra com TRM-045), ou texto puro + `G01`
   sem entrada publicável. Em `R01`, o texto `R01` no lugar.
8. `LinhasDaSituacao` (TRM-015): "Regime" (`regime_texto` ou só o termo
   oficial, como `F07`), "Quem decide" (`apreciacao_texto` idem),
   "Relatoria" (`F12`), "Última movimentação"; órgão por
   `onde_esta.orgao_nome`/`sigla_orgao` (já o órgão efetivo em F1).
9. Rodapé: "Conferido na Câmara em {conferido_em}" · "Ver na Câmara" ·
   ```tsx
   const cs = comoSabemosDaFase(onde_esta.como_sabemos);
   cs ? <ComoSabemos {...cs}
          fontes={[...cs.fontes, { rotulo: "Regras do mapa de fases — data/tramitacao/fases.yml", url: `${REPO_URL}/blob/main/data/tramitacao/fases.yml` }]}
          nota={TEXTOS.C01}
          saibaMais={{ rotulo: TEXTOS.C01_SAIBA_MAIS, href: "/metodologia#tramitacao" }} />
      : <p className="text-texto-s text-zil-texto-2">{TEXTOS.C03}</p>
   ```
   (a fonte "Regras" só é acrescentada se a API ainda não a mandar; `C03` é
   defeito de dado: o aviso do adaptador vira falha de teste).

Por que a situação oficial pode ser um `TermoGlossario` fechado: a primeira
leitura da seção já é a frase em linguagem simples e o selo de fase
("Apresentada. Ainda não foi distribuída às comissões"), de modo que o termo
oficial deixa de ser a primeira leitura e o risco de "…(Chancela)" ser lido
como "esperando sanção" (disc. §1.1) cai. No fallback `N06`, sem frase, o
risco volta: lá `SituacaoCamara` recebe `glossario` e `definicaoAberta`, e o
termo usa `abertoInicial` (prop do kit).

Estados (textos na matriz, §4): `I04`–`I07`, `P01`–`P09`, `D01`–`D08`,
`A01`, `A02`, `N00`–`N06`, `R01`, `T01`, `G01`–`G03`, `C01`, `C03`, `C04`,
`E01`, `F04`, `F05`, `F07a`, `F07b`, `F12`, `X01`.

Interações: link do `FaseSelo`; botões e links da seção; `ComoSabemos`
abre e fecha (`<details>`, sem JS); o `TermoGlossario` abre com clique,
toque, Enter ou Espaço e fecha com Esc (kit). Ordem de foco na seção: ação
do aviso de apensada → gatilho do `TermoGlossario` da situação (aberto: "Ver
no glossário") → links da relatoria (se houver) → "Ver na Câmara" →
`summary` "Como sabemos" → links dentro dele.

Responsividade: 320/375 — uma coluna; `Etapas` compacta (só barras e a
legenda, cabe em qualquer largura; para o leitor de tela é uma `<ol>` com
`aria-current`); 768 — `dl` em duas colunas; 1280 — grid de duas colunas para
explicação/situação e `dl` (`lg:grid-cols-[minmax(0,1fr)_minmax(0,24rem)]`).

Acessibilidade: `section` com `aria-labelledby`; `aria-busy="true"` e texto
`sr-only` "Carregando a tramitação" durante `I04`; `aria-current="step"`; a
etapa atual se distingue por forma (meia barra) e pela legenda visível
"Etapa 2 de 6: Nas comissões" — nunca só por cor (1.4.1); o link do
`FaseSelo` tem o nome do kit ("Fase: {rótulo}, entenda esta fase"), que
contém o texto visível (2.5.3); `Aviso` de `nao_sabemos` tem `role="note"` (vem do
kit) — não é erro; foco nunca sob a navegação fixa (U9).

**Testes**
- Vitest — `apps/web/tests/componentes/tramitacao/OndeEsta.test.tsx`: um teste por
  linha da matriz listada em "Estados", com a fixture do caso
  (`apps/web/tests/fixtures/api/tramitacao/`); `glossario: null` → sem definição e sem
  erro; entrada `aprovado` com `publicavel: false` → sem texto; definição
  achada por `situacao_glossario` mesmo com `situacao_oficial` diferente do
  `termo` (espaço sobrando); só uma legenda de etapas no DOM;
  `classesDeAlinhamento` vazio; axe por estado (com o `TermoGlossario`
  fechado e aberto, via `user-event`).
- Vitest — `tests/componentes/tramitacao/TramitacaoProposicao.test.tsx` com
  `fetch` simulado: 200, 404, 500, mapa 500; "Tentar de novo" chama de novo
  só as duas URLs de tramitação.
- Playwright — `apps/web/tests/e2e/paginas/proposicao-onde-esta.spec.ts`, três
  projetos: critérios 1–11 (com 3a e 3b); `toMatchAriaSnapshot` da `<ol>`;
  `animacoesInfinitas` com e sem `page.emulateMedia({ reducedMotion: "reduce" })`;
  a 375 px, `focoVisivelENaoEncoberto` em cada link e gatilho da seção;
  `semRolagemHorizontal` com `@reflow`; `semViolacoes` e `expectPaletaNeutra`
  nos dois temas.
- Comandos: `npx vitest run tests/componentes/tramitacao/OndeEsta.test.tsx tests/componentes/tramitacao/TramitacaoProposicao.test.tsx`,
  `npx playwright test tests/e2e/paginas/proposicao-onde-esta.spec.ts`.

**Riscos e perguntas em aberto**
- Sem a entrada `fase_<fase>` publicável (lote do glossário atrasado), a
  seção perde a explicação da fase, mas continua correta.
- `legendaDasEtapas` (DS) conta a etapa `pulada` ("Dispensada") no total
  ("Etapa 2 de 6" com o Plenário dispensado). É a posição no rito da espécie,
  não "quanto falta". Se o revisor de linguagem achar que induz a erro, a
  mudança é no kit (TRM-030), não aqui.
- O `FaseSelo` do DS sabe desenhar `mapa_nao_aprovado`; esta parte escolhe
  não mostrá-lo (`N06`) para que, antes dos lotes L1–L3, a página não exiba
  "Fase não identificada" em todas as proposições.
- Antes de L1–L3 aprovados, todas as proposições caem em `N06` — o que é
  o comportamento desejado (D11).

**Instruções para o agente implementador**
- Branch `trm-040-onde-esta`, do `main` com TRM-028, 030, 031, 033, 035, 037,
  046-B, 047 e 015 mergeados.
- Ordem: testes de `OndeEsta` por estado (contra as fixtures) → `OndeEsta` →
  orquestrador e teste → cabeçalho → e2e → provas.
- Verificação: `cd apps/web && npm run lint && npx tsc --noEmit && npm run test && npm run build && npm run test:e2e`.
- Prova: `registrarEvidencia` dos casos 02, 05, 08, 11, 15, 30 em
  375/768/1280 × 2 temas (artefato `evidencias-ui`); JSON do axe.
- Não fazer: derivar fase, rótulo ou frase no frontend; calcular "desde";
  repetir o `FaseSelo` dentro da seção (ele está no cabeçalho; a frase já
  diz a fase); mostrar "Fase não identificada" para `mapa_nao_aprovado`;
  esconder a situação oficial em qualquer estado.

### TRM-041 — Página da proposição: "O que aconteceu" (linha do tempo)

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E4 Experiência · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX + Design System; Maintainer (textos novos)
**Depende de:** TRM-028 (`marcos`, `eventos_total`, `/tramitacao/eventos`), TRM-026 (marcos), TRM-032 (`LinhaDoTempo`, `Marco`, `TodosOsRegistros`), TRM-037 (`Recolhivel`), TRM-040 (orquestrador), TRM-046-B · **Publicação:** títulos dos marcos acendem com o lote L3 (spec.md §6.12); antes disso `marcos[]` vem vazio e a seção mostra `I15` com os registros · **Desbloqueia:** —

**Problema** — Não há linha do tempo em nenhuma página (disc. §1.5). A
coluna de tramitações do banco está vazia (disc. §1.1) e a lista bruta da
Câmara engana: a situação de cada linha não é histórica e o último registro
pode ser um ofício posterior (disc. §3.2).

**Oportunidade** — Contar a história em marcos legíveis ("Aprovado no
Plenário da Câmara"), com link para cada votação do placar, e manter o
registro bruto à mão para quem quiser conferir.

**Solução**
- `components/tramitacao/OQueAconteceu.tsx` (`"use client"`: controla o
  estado dos registros), renderizado pelo orquestrador depois de
  `#onde-esta`, com `marcos` e `eventos_total` já carregados.
- Marcos em ordem cronológica (mais antigo primeiro; a API já manda assim),
  cada um `<Marco {...marcoDaApi(m, i, marcos.length)} />` (adaptador do kit,
  `lib/tramitacao/eventos.ts`, TRM-032: `atual` só no último, `local`,
  `tipo`, `href`, `documento`). Até 8 visíveis; acima disso, os 8 mais
  recentes ficam na lista e os anteriores num `Recolhivel` **antes** dela
  ("Ver os {n} marcos anteriores"), com `<LinhaDoTempo aria-label="Marcos
  anteriores">` dentro, para a leitura seguir em ordem.
- Registros: `TodosOsRegistros` com `onAbrir` → `obterEventos(id, 1, 50)`
  (TRM-046-B; `?page=&per_page=`, resposta `{ items, total, page, per_page,
  pages }`); `onTentarDeNovo` → a mesma busca da página atual; `registros =
  items.map(registroDoEvento)` (kit; data sem hora); `estado` controlado pela
  seção; `rodape` = `Paginacao` (50 por página, `resumo` "Mostrando {a}–{b}
  de {total}"). O foco na troca de página é do kit (`focarAoTrocar`, padrão
  `true`); a página não mexe em foco.

**Escopo**
- Dentro: a seção, o carregamento sob demanda, os estados, testes.
- Fora: marcos do Senado (chegam com TRM-050; `local` já comporta a Casa);
  eventos agendados (TRM-051).

**Critérios de aceite**
1. Caso 08: 6 `Marco` em ordem cronológica; só o último com `atual`; o de
   votação com `tipo="votacao"` e `href="/votacoes/{votacao_id}"`; o de
   sanção com `documento` quando houver `url`; `local` = "Câmara · PLEN"
   (`CASA_ROTULO` + sigla).
2. Caso 34 (11 marcos): 8 na lista e um `Recolhivel` "Ver os 3 marcos
   anteriores", fechado, antes dela.
3. Abrir "Todos os 51 registros" faz **uma** requisição (`/tramitacao/eventos`,
   página 1 — `api.chamadas.filter(c => c.chave.endsWith("/eventos")).length === 1`);
   mostra 50, `Paginacao` com "Mostrando 1–50 de 51"; página 2 mostra o 51º e
   o foco vai para ele; fechar e reabrir não refaz a requisição. Depois de um
   erro, "Tentar de novo" e reabrir refazem a busca.
4. Registros mostram data, órgão, descrição e despacho no texto original,
   **sem** a situação por linha (armadilha 1 de disc. §3.2).
5. `I13`–`I16` com os textos exatos; erro nos registros não afeta os marcos.
6. Nenhum `Marco` recebe `tom` (`classesDeAlinhamento` vazio;
   `expectPaletaNeutra(page, "#o-que-aconteceu")`).
7. Gates de §7; 0 violações em 375/768/1280 × 2 temas, com os registros
   fechados e abertos.

**Specs técnicas**
- `apps/web/components/tramitacao/OQueAconteceu.tsx`:
  ```ts
  "use client";
  export function OQueAconteceu(props: { proposicaoId: string; rotulo: string; marcos: MarcoApi[]; eventosTotal: number }): JSX.Element
  // estado: { registros: "ocioso" | "carregando" | "pronto" | "erro"; pagina: number; itens: EventoApi[]; total: number }
  ```
  Tipos de `lib/tramitacao/tipos.ts` (`MarcoApi`, `EventoApi`,
  `PaginaEventosApi`); nada é mapeado à mão: `marcoDaApi` e
  `registroDoEvento` (TRM-032).
- `TramitacaoProposicao.tsx`: renderiza a seção quando `status === "ok"`.

**Specs de design**

Wireframe 375 px (caso 08):
```
┌───────────────────────────────────────┐
│ O que aconteceu                       │ h2 (id o-que-aconteceu-titulo)
│ Em ordem cronológica                  │ M01 (text-texto-s texto-2)
│ • 03/01/2024 · Câmara · MESA          │ Marco passado: ponto cheio (kit)
│   Enviado pelo Presidente da República│ título
│ • 19/03/2024 · Câmara · PLEN          │
│   ▣ Aprovado no Plenário da Câmara    │ tipo="votacao": ícone placar,
│     (314 × 96)                        │ título vira link (href)
│ • 30/04/2024 · Senado                 │
│   Aprovado no Senado                  │
│ ◉ 28/05/2024 · Câmara · MESA          │ atual (último)
│   Sancionado com veto parcial         │
│   Documento ↗                         │ documento
│ ┌───────────────────────────────────┐ │ TodosOsRegistros (fechado)
│ │ Todos os 51 registros          ⌄  │ │
│ │ No texto original da Câmara dos   │ │ fonte (padrão do kit)
│ │ Deputados                         │ │
│ └───────────────────────────────────┘ │
└───────────────────────────────────────┘
```
Aberto, 1280 px (`max-w-3xl`; data em coluna de `7rem` a partir de `md`):
```
│ Todos os 51 registros                                                   ⌃ │
│ 28/05/2024   MESA · Transformado em Norma Jurídica com Veto Parcial        │
│              Transformado na Lei Ordinária 14871/2024. DOU 29/05/24 …      │
│ 22/05/2024   MESA · Remessa à Sanção                                       │
│ …                                                                          │
│ Mostrando 1–50 de 51                                     ‹  [1]  2  ›      │ Paginacao no rodape
```

Anatomia: `h2` "O que aconteceu" → `M01` → `Recolhivel` de marcos anteriores
(> 8) → `LinhaDoTempo aria-labelledby="o-que-aconteceu-titulo"` → `TodosOsRegistros`.
Ordem dos registros: do mais recente para o mais antigo (o padrão da API) —
dito no `fonte`: "No texto original da Câmara dos Deputados, do mais recente
para o mais antigo" (`M02`).

Estados: `I13` (carregando — esqueletos do kit), `I14` (erro — `Aviso`
`padrao` do kit, com "Tentar de novo"), `I15` (sem marcos), `I16` (sem
registros: `TodosOsRegistros` com `total=0` não renderiza; a seção mostra o
texto), `M01`–`M03`.

Interações: `Recolhivel` e `TodosOsRegistros` nativos (`<details>`);
`Paginacao` troca a página sem fechar; o kit leva o foco ao primeiro
registro da página nova e o `role="status"` anuncia "{n} registros
carregados.".

Responsividade: 375 — uma coluna; a partir de `md`, data dos registros em
coluna própria.

Acessibilidade: lista ordenada nomeada pelo `h2`; marcador sem cor; "Votação:
" lido antes do título dos marcos de votação (do kit); "(abre em nova aba)"
em "Documento"; `aria-busy` durante a busca; `summary` descritivo (U10).

**Testes**
- Vitest — `apps/web/tests/componentes/tramitacao/OQueAconteceu.test.tsx`: ordem
  cronológica; `atual` só no último; corte em 8 com o `Recolhivel` (lista
  nomeada "Marcos anteriores") antes; `fetch` simulado para os registros
  (uma chamada na primeira abertura; paginação; erro `I14` com "Tentar de
  novo"; reabrir sem nova chamada quando não houve erro); `I15`, `I16`;
  `classesDeAlinhamento` vazio; axe aberto e fechado.
- Playwright — `apps/web/tests/e2e/paginas/proposicao-linha-do-tempo.spec.ts`:
  critérios 1–5 e 7 nos três projetos, com
  `api.responderPaginas("/proposicoes/<id>/tramitacao/eventos", ["tramitacao/eventos-08-p1", "tramitacao/eventos-08-p2"])`
  (API falsa unificada de TRM-001; nenhum helper próprio); foco depois de
  trocar de página; `semRolagemHorizontal` com `@reflow`; `semViolacoes`;
  `expectPaletaNeutra(page, "#o-que-aconteceu")` também no estado `I14`
  (agora `padrao`).
- Comandos: `npx vitest run tests/componentes/tramitacao/OQueAconteceu.test.tsx`,
  `npx playwright test tests/e2e/paginas/proposicao-linha-do-tempo.spec.ts`.

**Riscos e perguntas em aberto**
- Duas ordens na mesma seção (marcos crescente, registros decrescente) são
  deliberadas e ditas na tela; o revisor de linguagem pode pedir outra.
- O nome do órgão não vem em `marcos[]` (só a sigla); pedido opcional à
  Arquitetura: `orgao_nome` no marco.

**Instruções para o agente implementador**
- Branch `trm-041-o-que-aconteceu`, do `main` com TRM-040, TRM-032 e TRM-037.
- Ordem: testes → componente → orquestrador → e2e → `registrarEvidencia`
  dos casos 08, 31, 32 e 34.
- Não fazer: mostrar a situação por linha dos registros; mostrar hora; passar
  `tom` ao `Marco`; buscar os registros antes de a pessoa abrir; mexer em
  foco na página.

### TRM-042 — Página da proposição: "O caminho inteiro" (rito da espécie com o estado atual)

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E4 Experiência · **Prioridade:** P2 · **Horizonte:** Em seguida · **Estimativa:** P
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX + Design System
**Depende de:** TRM-034 (`RitoDiagrama` e `ritoParaDiagrama`, 034-A e 034-B), TRM-037, TRM-028 (`/tramitacao/mapa`; `rito` em `/tramitacao`), TRM-041 (ordem na página), TRM-046-B · **Publicação:** lotes L5 (PL, PLP) e L6 (PEC, MPV, PDL) · **Desbloqueia:** —

**Problema** — "Onde está agora" mostra a posição em barras, mas não o que
acontece em cada etapa, quem decide, qual é o prazo e onde a proposição pode
parar (disc. §6.1, item 6).

**Oportunidade** — O rito da espécie com a etapa atual marcada e a base
legal de cada passo responde "quanto falta e o que pode acontecer" sem
prometer datas, e leva para `/como-vira-lei`.

**Solução** — `components/tramitacao/CaminhoInteiro.tsx` (sem hooks),
renderizado pelo orquestrador depois de "O que aconteceu":
```tsx
// o rito é escolhido pela chave (RitoRefApi), não por espécie + Casa: a MPV tem casa_iniciadora "congresso" (MPV_CN)
const rito = mapa.especies.flatMap((e) => e.ritos).find((r) => r.chave === tramitacao.rito?.chave);
const props = rito ? ritoParaDiagrama(rito, { proposicao: { etapas: tramitacao.etapas, desfecho: onde_esta.desfecho } }) : null;
props?.publicavel === false ? <K01/> : props ? <RitoDiagrama {...props} nivelTitulo={3} /> : <K02 ou K03/>
```
Tudo dentro de um `Recolhivel` fechado ("Ver as {n} etapas, com o que
acontece em cada uma") — a seção é a sexta da página e o rito por extenso
passa de 1.000 px no celular.

**Escopo**
- Dentro: a seção, os estados, o botão para `/como-vira-lei`.
- Fora: rota prevista pelo despacho ("faltam pareceres da CME e da CCJC",
  TRM-052); contagens (só em `/como-vira-lei`).

**Critérios de aceite**
1. Caso 02: `h2` "O caminho inteiro", `K00` ("O caminho de um projeto de lei
   que começa na Câmara. A etapa atual aparece marcada."), `Recolhivel`
   fechado com "Ver as 6 etapas, com o que acontece em cada uma"; aberto, o
   `RitoDiagrama` mostra a 2ª etapa com o selo "Está aqui" e "Desde {data}",
   a 1ª com a data, o Plenário com o selo "Dispensada" e a `nota` quando a
   fixture o marcar `pulada`; cada etapa com "Quem decide:".
2. Ramos de desfecho sob a etapa de onde saem ("Pode terminar aqui") e os
   gerais em "A qualquer momento" (textos do kit); a 768 px, embaixo do
   texto; a 1280, à direita (`lg`).
3. Botão `secundario` "Entender como uma proposição vira lei" →
   `/como-vira-lei?especie={sigla}&casa={casa}` (MPV: só `?especie=MPV`).
4. `ritoParaDiagrama(...).publicavel === false` (PDL em `mapa.json`) → `K01`;
   nenhum rito com a `chave` de `tramitacao.rito` → `K02`; `nao_sabemos`,
   fase nula ou `rito: null` → `K03` e o rito da espécie sem estados (se
   houver); mapa indisponível → `I07`.
4a. Caso 15 (MPV, rito `MPV_CN` com `casa_iniciadora: "congresso"`): o rito é
    achado pela chave e mostrado com a etapa interrompida.
5. `classesDeAlinhamento` vazio; `expectPaletaNeutra(page, "#caminho")`.
6. Gates de §7; 0 violações em 375/768/1280 × 2 temas, fechado e aberto.

**Specs técnicas**
- `apps/web/components/tramitacao/CaminhoInteiro.tsx`:
  ```ts
  export function CaminhoInteiro(props: {
    tipo: string;                                   // "PL"
    mapa: MapaApi | null;                           // null = I07
    rito: RitoRefApi | null;                        // { chave, especie, casa_iniciadora: CasaRito }
    tramitacao: TramitacaoApi;
  }): JSX.Element
  ```
- Usa `ritoParaDiagrama`, `RitoDiagrama`, `Recolhivel` (kit) e
  `especieIndefinida`, `TEXTOS` (TRM-046-A).

**Specs de design**

Wireframe 375 px (aberto, caso 02):
```
┌───────────────────────────────────────┐
│ O caminho inteiro                     │ h2
│ O caminho de um projeto de lei que    │ K00
│ começa na Câmara. A etapa atual       │
│ aparece marcada.                      │
│ ┌───────────────────────────────────┐ │ Recolhivel (aberto)
│ │ Ver as 6 etapas, com o que        │ │
│ │ acontece em cada uma           ⌃  │ │
│ │ CÂMARA                            │ │ RitoDiagrama (vertical)
│ │ • Apresentada        02/04/2024   │ │ h3 + meta
│ │   A proposição foi apresentada …  │ │ oQueAcontece
│ │   Quem decide: o Presidente da …  │ │ quemDecide
│ │   Prazo: 2 sessões · fixado na    │ │ classe D* (E02)
│ │   regra, mas costuma não ser …    │ │
│ │   Base: Regimento da Câmara, …    │ │
│ │ ◉ Nas comissões   [Está aqui]     │ │ selo forte do kit
│ │   Desde 09/05/2025                │ │
│ │   …                               │ │
│ │   ┌ PODE TERMINAR AQUI ─────────┐ │ │ ramos (superficie-2),
│ │   │ Arquivada · Rejeitada …     │ │ │ embaixo até lg
│ │   └─────────────────────────────┘ │ │
│ │ ◌ No Plenário da Câmara           │ │
│ │   [Dispensada] · Plenário         │ │ nota da API
│ │   dispensado: apreciação conclusiva│ │
│ │ ○ No Senado …                     │ │
│ │ A QUALQUER MOMENTO                │ │ desfechosGerais
│ └───────────────────────────────────┘ │
│ [ Entender como uma proposição vira   │ Button secundario
│   lei ]                               │
└───────────────────────────────────────┘
```
1280 px: o mesmo, com os ramos numa coluna à direita de cada etapa
(`lg:grid-cols-[minmax(0,1fr)_minmax(0,20rem)]`, do kit); a 768, ramos
embaixo do texto.

Estados: `K00`–`K03`, `I07`, `E02`; carregando = o do orquestrador.

Interações: `Recolhivel`; links do rito (base legal); botão final. Foco: o
`summary`, depois os links na ordem das etapas, depois o botão.

Responsividade: vertical em todos os breakpoints (decisão 5 do DS); ramos à
direita a partir de `lg`; reflui a 320 px.

Acessibilidade: `h3` por etapa (`nivelTitulo={3}`, sob o `h2` da seção);
estado em texto ("Está aqui", "Dispensada", "Parou aqui", "Foi o que aconteceu");
`aria-current="step"` na atual; ramos em `<ul aria-label="Pode terminar
aqui">` (do kit).

**Testes**
- Vitest — `apps/web/tests/componentes/tramitacao/CaminhoInteiro.test.tsx`:
  com estados (02), MPV pela chave `MPV_CN` (15), `nao_sabemos` (11), rito
  não publicável (PDL → `K01`), sem rito para a chave (PLN → `K02`), mapa
  nulo (`I07`); `classesDeAlinhamento`; axe fechado e aberto.
- Playwright — `apps/web/tests/e2e/paginas/proposicao-caminho.spec.ts`:
  critérios 1–6 (com 4a); posição dos ramos a 768 (embaixo) e 1280 (à
  direita); `semRolagemHorizontal` com `@reflow`.
- Comandos: `npx vitest run tests/componentes/tramitacao/CaminhoInteiro.test.tsx`,
  `npx playwright test tests/e2e/paginas/proposicao-caminho.spec.ts`.

**Riscos e perguntas em aberto**
- Se a validação qualitativa (spec.md §2) mostrar que ninguém abre o
  `Recolhivel`, considerar abri-lo por padrão a partir de `lg`.

**Instruções para o agente implementador**
- Branch `trm-042-caminho-inteiro`, do `main` com TRM-034-B e TRM-041.
- Não fazer: barra em porcentagem; etapa "Regulamentação"; estado calculado
  no frontend (o adaptador só junta por `id`).

### TRM-043 — Lista: selo e filtro de fase com contagem

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E4 Experiência · **Prioridade:** P2 · **Horizonte:** Em seguida · **Estimativa:** M
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX + Design System; Maintainer (rótulos do filtro)
**Depende de:** TRM-016, TRM-028 (campos de F1 em `ProposicaoRead`), TRM-031 (`FaseSelo` com `id`), TRM-046-B (`grupoDeFase`, `faseSeloPropsDe`) · **Publicação:** lotes L1–L2 (antes deles, todas caem em `mapa_nao_aprovado`: sem selo e sem chips de fase além de "Todas") · **Desbloqueia:** TRM-044 (o link "N proposições acompanhadas estão aqui agora" aterrissa aqui)

**Problema** — A lista não diz a fase de nada nem deixa filtrar por ela
(disc. §1.5, §6.3); "quais estão nas comissões?", "quais viraram lei?" e
"quais foram encerradas?" exigem abrir proposição por proposição.

**Oportunidade** — Um selo neutro por cartão e um filtro com contagem dão o
retrato do acervo de uma vez, e servem de destino para `/como-vira-lei`.

**Solução**
1. `app/proposicoes/page.tsx` vira Server Component (casca, `metadata`,
   `<Suspense fallback={<6 CardEsqueleto/>}>`); o conteúdo atual passa para
   `components/tramitacao/ListaProposicoes.tsx` (`"use client"`). Motivo:
   `useSearchParams` no Next 14 exige `Suspense` para o build não falhar.
2. Filtro de fase (`FiltroFase`): linha de `Chips` (com `rolagem` abaixo de
   `md`) dentro de `<div role="group" aria-labelledby="filtro-fase-rotulo">`
   com o rótulo visível "Fase" (`L05`); chip "Todas" + um chip por grupo com
   `n > 0`, na ordem do rito; contagem calculada sobre as proposições que
   passam pelos **outros** filtros.
3. Grupos (`grupoDeFase`, TRM-046-B): a `fase` (inclusive herdada, em
   apensadas) quando não há desfecho; `encerradas` quando há `desfecho`;
   `nao_identificada` para `nao_sabemos` **exceto** `mapa_nao_aprovado`, que
   fica só em "Todas".
4. Estado na URL: `?fase=`, `?tipo=` e `?casa=` lidos ao montar e gravados
   com `router.replace(…, { scroll: false })`; `casa` aparece como chip
   removível "Começou na Câmara"/"Começou no Senado" quando presente (vem dos
   links de `/como-vira-lei`). "Limpar filtros" limpa os três.
5. Cartão: `FaseSelo` **sem `href`** no encaixe `fase` de `CartaoProposicao`:
   `<FaseSelo {...faseSeloPropsDe(p, { comLink: false })} id={"p-" + p.id + "-fase"} />`;
   nada quando o resultado é `null`. O link do cartão leva
   `aria-describedby` com `p-{id}-fase p-{id}-situacao p-{id}-datas` (só os
   ids que existirem no cartão).
6. Cabeçalho: link de texto "Como uma proposição vira lei" (`L06`) abaixo da
   linha fina, para `/como-vira-lei`.
7. Rótulo "Pauta" visível antes dos chips de categoria (mesmo padrão do
   grupo "Fase"; as duas linhas de chips precisam de nome).

**Escopo**
- Dentro: a separação servidor/cliente da página, `FiltroFase`, o selo no
  cartão, URL, contagem, testes.
- Fora: filtro de fase no servidor (`GET /proposicoes?fase=`, que TRM-028
  oferece): com a lista inteira já no cliente (TRM-016), filtrar localmente
  é mais simples e a contagem sai junto — ver risco.

**Critérios de aceite**
1. Com `lista-p1`+`lista-p2` (130 itens), os chips mostram exatamente as
   contagens que `grupoDeFase` dá sobre a fixture (teste compara com o valor
   calculado no próprio teste a partir do JSON); chips com 0 não aparecem.
2. `/proposicoes?fase=comissoes&tipo=PL&casa=camara` abre com o chip "Nas
   comissões" ativo, tipo PL, o chip "Começou na Câmara" e só os itens que
   casam; a contagem `L04` diz "… — fase: Nas comissões".
3. Escolher um chip atualiza a URL sem rolar a página e sem nova requisição;
   "Limpar filtros" volta a `/proposicoes`.
4. Cartão de proposição em `mapa_nao_aprovado`: sem `FaseSelo`; de
   apensada: `FaseSelo` com o selo "Em conjunto"; de desfecho: rótulo da API
   ("Arquivada") com o glifo do kit.
5. Nenhum `FaseSelo` dentro de cartão é link (`getAllByRole("link")` dentro
   do cartão = 1).
6. `I12` com fase ativa mostra o texto específico.
7. `expectPaletaNeutra(page, "main")`; 0 violações em 375/768/1280 × 2 temas;
   `semRolagemHorizontal` com as duas linhas de chips.

**Specs técnicas**
- `apps/web/app/proposicoes/page.tsx` (servidor) e
  `apps/web/components/tramitacao/ListaProposicoes.tsx` (cliente, o código de
  hoje + filtro).
- `apps/web/components/tramitacao/FiltroFase.tsx`:
  ```ts
  export function FiltroFase(props: { contagens: Partial<Record<GrupoFase, number>>; total: number; ativo: GrupoFase | ""; onMudar: (g: GrupoFase | "") => void }): JSX.Element
  ```
- `GrupoFase = Fase | "encerradas" | "nao_identificada"` (TRM-046-B).
- `CartaoProposicao` (TRM-016) recebe `fase={<FaseSelo {...props} />}`.

**Specs de design**

Wireframe 375 px (topo da lista):
```
┌───────────────────────────────────────┐
│ PROPOSIÇÕES                           │
│ Proposições                           │ h1
│ Projetos de lei, PECs e …             │
│ Como uma proposição vira lei →        │ L06 (link de texto)
│ [🔍 Buscar por ementa ou resumo     ] │
│ (Todos os tipos ▾) (Todos os anos ▾)  │
│ [ Todas | Analisadas | Sem análise ]  │
│ (Ordenar ▾)                           │
│ Pauta                                 │ rótulo visível
│ (Todas)(● Fertilizantes)(● Minera…→   │ Chips rolagem
│ Fase                                  │ rótulo visível
│ (Todas 130)(Apresentadas 31)(Nas co…→ │ Chips rolagem, n à direita
│ (Começou na Câmara ×)                 │ só com ?casa=
│ 58 proposições — fase: Nas comissões  │ L04 (aria-live)
│ ┌───────────────────────────────────┐ │
│ │ (● Nas comissões) (● Energia)     │ │ FaseSelo sem link + categorias
│ │ PL 4861/2023                      │ │
│ │ …                                 │ │
│ │ Situação na Câmara: Aguardando …  │ │
│ │ Última movimentação em 19/07/2026 │ │
│ └───────────────────────────────────┘ │
└───────────────────────────────────────┘
```
1280 px: `BarraFiltros` numa linha (como hoje); "Pauta" e "Fase" como duas
linhas de chips que quebram (`Chips` sem `rolagem`); cartões em duas
colunas.

Estados: `I08`–`I12`, `L01`–`L06`, `N00`, `A01` (só o selo "Em conjunto").

Interações: chip de fase como rádio (o ativo é `aria-pressed="true"`; clicar
no ativo volta a "Todas"); chip "Começou na …" removível.

Responsividade: chips com `rolagem` e borda esmaecida abaixo de `md`; sem
rolagem horizontal da página.

Acessibilidade: dois grupos nomeados ("Pauta", "Fase"); `n` lido junto
("Nas comissões 58" — padrão do kit; ver riscos); contagem anunciada
(`aria-live="polite"`); o selo no cartão entra na descrição acessível do
link pelo `id` do `FaseSelo` (item 5 da Solução).

**Testes**
- Vitest — `apps/web/tests/unit/tramitacao/grupo-de-fase.test.ts` (cada estado →
  grupo; desfecho com `fase` nula → `encerradas`; `mapa_nao_aprovado` →
  `null`); `apps/web/tests/componentes/tramitacao/FiltroFase.test.tsx`
  (chips com `n > 0`, ordem, rádio, axe).
- Playwright — `apps/web/tests/e2e/paginas/lista-fase.spec.ts`: critérios 1–7,
  com `api.responderPaginas("/proposicoes", ["tramitacao/lista-p1", "tramitacao/lista-p2"])`
  (TRM-001); `semRolagemHorizontal` com `@reflow`; descrição acessível do
  cartão contém o rótulo do selo.
- Comandos: `npx vitest run tests/unit/tramitacao tests/componentes/tramitacao/FiltroFase.test.tsx`,
  `npx playwright test tests/e2e/paginas/lista-fase.spec.ts`.

**Riscos e perguntas em aberto**
- Contar no cliente vale enquanto o acervo cabe em poucas páginas. Acima de
  ~1.000 itens, usar o que a API já tem: `GET /tramitacao/contagem` (que
  hoje não filtra por `analise` nem por busca textual) e `?fase=`/`?desfecho=`
  em `GET /proposicoes`.
- Duas linhas de chips no celular pesam; se a validação com pessoas mostrar
  confusão, a fase pode ir para um `Seletor` ("Fase: todas ▾") com a contagem
  no rótulo de cada opção.
- O número do chip é lido sem unidade ("Nas comissões 58"). Fica assim (é o
  padrão do kit para todo `Chip` com `n`); se o revisor de linguagem pedir,
  `aria-label` "Nas comissões, 58 proposições" no chip.

**Instruções para o agente implementador**
- Branch `trm-043-lista-fase`, do `main` com TRM-016, TRM-028, TRM-031 e
  TRM-046-B.
- Ordem: `grupoDeFase` (se ainda não estiver em 046-B) → `FiltroFase` →
  separação servidor/cliente → URL → e2e → `registrarEvidencia`.
- Não fazer: `pontoClassName` nos chips de fase; `FaseSelo` com `href`
  dentro do cartão; contar `mapa_nao_aprovado` como "Fase não identificada".

### TRM-044 — Página `/como-vira-lei`: rito por espécie e Casa iniciadora, desfechos, apensação, depois da lei

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E4 Experiência · **Prioridade:** P2 · **Horizonte:** Em seguida · **Estimativa:** M (o G do índice cai com `RitoDiagrama` e `ritoParaDiagrama` prontos no kit)
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX + Design System; Maintainer (textos fixos)
**Depende de:** TRM-034-A/B, TRM-035 (`TermoGlossario`), TRM-028 (`/tramitacao/mapa`), TRM-043 (filtros na URL), TRM-046-B (`contagensPorEtapa`, `listarTodasProposicoes`), TRM-047 (link) · **Publicação:** lotes L5 (PL, PLP) e L6 (PEC, MPV, PDL); sem nenhum rito publicado, a página mostra `V02` · **Desbloqueia:** TRM-045 (seção de situações por fase), destino do `FaseSelo` (TRM-040)

**Problema** — Ninguém no site explica o caminho de uma proposição. O
`FaseSelo` da página precisa de um destino ("o que é estar nas
comissões?"), e o discovery pede uma página explicativa com espécie, Casa,
desfechos e apensação (disc. §6.3).

**Oportunidade** — Conteúdo de educação cívica que não envelhece com o ciclo
de votações (spec.md §1.4), ligado ao acervo real: cada etapa diz quantas
proposições acompanhadas estão nela agora.

**Solução**
- `app/como-vira-lei/page.tsx` (servidor: `metadata`, `Suspense`) +
  `components/tramitacao/ComoViraLei.tsx` (cliente: lê `especie` e `casa` da
  URL, busca `obterMapa()` e `listarTodasProposicoes({})` em paralelo).
- Controles como **links** (`Chip href`, estado na URL, funciona sem JS e é
  compartilhável): espécie em `Chips` (5 > limite do `Segmentado`); Casa em
  `Chips` (2), escondida para MPV. Padrão: `?especie=PL&casa=camara`.
- Escolha do rito: para PL, PLP, PEC e PDL, o rito da espécie com
  `casa_iniciadora === casa`; **para MPV, o único rito da espécie**
  (`MPV_CN`, `casa_iniciadora: "congresso"`) e `?casa=` é ignorado.
- `RitoDiagrama` com `ritoParaDiagrama(rito, { contagens, hrefContagem })`
  (kit; legenda "Como ler os prazos" com os textos de `E02`);
  `contagens = contagensPorEtapa(rito, proposicoes, especie, casa)` (`casa`
  nulo para MPV); `hrefContagem = e => "/proposicoes?fase=" + e.fase + "&tipo=" + especie + (casa ? "&casa=" + casa : "")`.
- Seções seguintes com conteúdo do mapa: desfechos, apensação, depois da lei,
  como o mapa é feito.

**Escopo**
- Dentro: a rota, os controles, as seções, os estados, os testes.
- Fora: a seção da metodologia (TRM-047); situações por fase (TRM-045);
  regulamentação, vetos e normas (TRM-053).

**Critérios de aceite**
1. `/como-vira-lei` sem parâmetros mostra o rito PL × Câmara; o chip "Lei
   (PL)" e "Na Câmara" com `aria-current`.
2. `/como-vira-lei?especie=PEC&casa=camara` mostra o rito da PEC; trocar de
   chip muda a URL e o conteúdo sem recarregar a página inteira.
3. Cada etapa tem âncora `fase-<fase>` na primeira etapa da fase (do
   adaptador); `/como-vira-lei?especie=PL&casa=camara#fase-comissoes` rola até
   ela, com o foco não encoberto pela navegação.
4. A contagem de cada etapa é igual à quantidade de cartões que o link dela
   mostra em `/proposicoes` (e2e abre o link e compara).
5. PDL (`publicavel: false` em `mapa.json`, `etapas: []`) → `K01`; espécie
   sem rito → `K02`; `mapa-vazio.json` → `V02`; mapa 500 → `I07`.
5a. `/como-vira-lei?especie=MPV&casa=senado` mostra o rito da MPV, sem chips
    de Casa, e o link de contagem não leva `&casa=`.
6. Seções `#desfechos` (um item por desfecho do rito, com âncora
   `desfecho-<id>`), `#apensacao`, `#depois-da-lei`, `#mapa` com os textos de
   `V01` e o conteúdo do mapa; entrada não publicada → "Explicação ainda não
   publicada." (texto do kit).
7. Nenhum texto de juízo ou data (V-E1–V-E5 rodam sobre os textos fixos, em
   TRM-046-A).
8. `expectPaletaNeutra(page, "main")`; 0 violações em 375/768/1280 × 2 temas;
   `semRolagemHorizontal` com `@reflow`; a 768, ramos embaixo do texto da
   etapa; a 1280, à direita.

**Specs técnicas**
- `apps/web/app/como-vira-lei/page.tsx`: `export const metadata = { title: "Como uma proposição vira lei — ZIL Observatório", description: "O caminho de uma proposição no Congresso, etapa por etapa, com a regra de cada passo." }`.
- `apps/web/components/tramitacao/ComoViraLei.tsx` (`"use client"`).
- Conteúdo das seções: `#desfechos` = `mapa.desfechos[]` (rótulo, base legal)
  + `texto` de `desfecho_<desfecho>` no glossário; `#apensacao` = entrada
  `apensada`; `#depois-da-lei` = entrada `fase_norma` + o texto fixo de
  `V01`; `#mapa` = `versao_publicada` e `aviso`. Texto nulo → o
  `textoPendente` do kit ("Explicação ainda não publicada.").

**Specs de design**

Wireframe 375 px:
```
┌───────────────────────────────────────┐
│ COMO FUNCIONA                         │ chapéu
│ Como uma proposição vira lei          │ h1
│ O caminho de uma proposição no        │ linha fina
│ Congresso: quem decide cada passo, o  │
│ que diz a regra e onde ela pode parar.│
│ ┌ (i) Texto do ZIL, não oficial ────┐ │ Aviso padrao
│ │ Escrito a partir da Constituição e│ │
│ │ dos regimentos… Mapa de fases     │ │
│ │ versão 4.                         │ │
│ └───────────────────────────────────┘ │
│ Tipo de proposição                    │ rótulo
│ (Lei (PL))(Lei complementar (PLP))(…→ │ Chips href, rolagem
│ Começa                                │
│ (Na Câmara)(No Senado)                │ Chips href
│ Projeto de lei: cria ou muda uma lei  │ especies[].descricao
│ ordinária. …                          │
│ O caminho                         (h2)│ #caminho
│ CÂMARA                                │ RitoDiagrama (vertical)
│ ○ Apresentada                     (h3)│
│   A proposição foi apresentada e …    │ oQueAcontece
│   Quem decide: o Presidente da Câmara │ quemDecide
│   Prazo: 2 sessões · fixado na regra, │ classe D* (E02)
│   mas costuma não ser cumprido        │
│   Base: Regimento da Câmara, art. 139 │
│   31 proposições acompanhadas estão   │ contagem (link; seta
│   aqui agora →                        │ fora do nome)
│   ┌ PODE TERMINAR AQUI ─────────────┐ │
│   │ Devolvida à autoria             │ │
│   └─────────────────────────────────┘ │
│ ○ Nas comissões                       │
│ …                                     │
│ Como ler os prazos                    │ legenda do kit
│ Onde uma proposição pode parar    (h2)│ #desfechos
│ Tramitação em conjunto            (h2)│ #apensacao
│ Depois que vira lei               (h2)│ #depois-da-lei
│ Como montamos este mapa           (h2)│ #mapa
└───────────────────────────────────────┘
```
1280 px: controles numa linha (espécie à esquerda, Casa à direita); rito com
ramos à direita a partir de `lg` (kit; a 768 ficam embaixo); seções finais em
`max-w-leitura`.

Ordem das seções: cabeçalho → aviso → controles → descrição da espécie →
`#caminho` → `#desfechos` → `#apensacao` → `#depois-da-lei` → `#mapa`.
Títulos `h2`; etapas `h3` (`nivelTitulo={3}`).

Estados: `V01` (textos fixos), `V02` (nada publicado), `K01`, `K02`, `I07`,
carregando (`CardEsqueleto` × 3 com `aria-busy`), textos do kit validados na
matriz (`E02`).

Interações: chips-link (sem JS); link de contagem; links de base legal;
âncoras.

Responsividade: chips com rolagem abaixo de `md`; rito vertical sempre.

Acessibilidade: um `h1`; grupos de chips com `role="group"` e rótulo
visível; chip ativo com `aria-current="true"` (do kit); ao trocar de espécie,
o foco fica no chip e a região `#caminho` recebe `aria-live="polite"` só
para o título do rito ("Caminho de um projeto de lei iniciado na Câmara").

**Testes**
- Vitest — `apps/web/tests/unit/tramitacao/contagens.test.ts` (`contagensPorEtapa`:
  primeira etapa da fase, exclui desfecho e `nao_sabemos`, inclui apensadas,
  filtra espécie e Casa, `casa: null` para MPV);
  `apps/web/tests/componentes/tramitacao/ComoViraLei.test.tsx` (estados, axe).
- Playwright — `apps/web/tests/e2e/paginas/como-vira-lei.spec.ts`: critérios
  1–8 (com 5a); a comparação do critério 4 navega pelo link da contagem; a
  lista é servida com `api.responderPaginas` (TRM-001).
- Comandos: `npx vitest run tests/unit/tramitacao/contagens.test.ts tests/componentes/tramitacao/ComoViraLei.test.tsx`,
  `npx playwright test tests/e2e/paginas/como-vira-lei.spec.ts`.

**Riscos e perguntas em aberto**
- **Navegação principal**: a página não entra na `NavBar` neste backlog
  (4 itens hoje; a tab bar do celular comporta 5). Decisão da maintainer.
- Busca no cliente contraria S9 ao pé da letra (registrado em §0.4).
- Desvio do disc. §6.3 ("`Segmentado` de espécie e de Casa"): espécie não
  cabe no `Segmentado`; Casa usa chips para os dois controles terem o mesmo
  comportamento (link) — decisão desta parte.

**Instruções para o agente implementador**
- Branch `trm-044-como-vira-lei`, do `main` com TRM-034-B, TRM-043 e
  TRM-046-B.
- Não fazer: estimar duração de etapa; usar "discricionária" em texto da
  página (ver `E02`); contar proposições no servidor de outro jeito que não
  `contagensPorEtapa`.

### TRM-045 — Página `/como-vira-lei/situacoes` (glossário) e termos inline

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E4 Experiência · **Prioridade:** P2 · **Horizonte:** Em seguida · **Estimativa:** M
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX + Design System; Maintainer (textos fixos)
**Depende de:** TRM-035 (`GlossarioLista`, `TermoGlossario`, `entradaDaApi`, `hrefDoTermo`), TRM-031, TRM-028, TRM-040 (onde entra o `href`), TRM-044 (onde entra a seção por fase), TRM-022, TRM-046-B · **Publicação:** lotes L0 e L4 · **Desbloqueia:** —

**Problema** — A Câmara descreve o andamento com 99 códigos de situação, sem
glossário para o cidadão (disc. §3.1); o glossário do ZIL (TRM-022) precisa
de uma página e de pontos de entrada.

**Oportunidade** — Um lugar onde o termo oficial e a explicação revisada
ficam lado a lado, com a fase a que cada situação leva — e a cobertura dita
em número, sem esconder o que falta.

**Solução**
1. `app/como-vira-lei/situacoes/page.tsx` (servidor: `metadata`, `Suspense`)
   + `components/tramitacao/Situacoes.tsx` (cliente: busca o mapa, filtra
   pela `Busca`).
2. Grupos (`h2`) pelo `tipo` da entrada: "Situações na Câmara" (`situacao`,
   em ordem de fase e depois alfabética), "Regimes de tramitação"
   (`regime`), "Quem decide: comissões ou Plenário" (`apreciacao`). Cada
   grupo é uma `<GlossarioLista nivelTitulo={3} entradas={…}>` (cada termo
   vira `h3` dentro de `article`; âncora `termo-<chave>` é o padrão do kit),
   com `entradaDaApi` e, quando a entrada tem fase,
   ```tsx
   const f = mapa.fases.find((x) => x.chave === e.fase && x.publicavel);
   extra = f?.rotulo ? <FaseSelo fase={e.fase} rotulo={f.rotulo} /> : undefined;
   ```
   (`GlossarioApi` não tem `fase_rotulo`; o rótulo vem de `mapa.fases`).
3. "Ainda sem explicação": `Recolhivel` "Ver as {n} situações ainda sem
   explicação", com o termo oficial de cada uma, a partir de
   `mapa.situacoes_camara: { codigo: string; descricao; glossario: string | null; tratada: boolean }[]`
   (atendido por TRM-028). "Sem explicação" = `glossario` nulo **ou**
   apontando para entrada não publicável; `{a}` da cobertura = as demais.
4. Âncora que aponta para dentro do `Recolhivel` fechado: ao montar, se
   `location.hash` casar com um elemento dentro de `<details>`, abrir e
   rolar até ele.
5. **Termos inline:**
   - em "Onde está agora" (TRM-040), o `TermoGlossario` da situação oficial
     ganha `href={hrefDoTermo(chave)}` ("Ver no glossário");
   - em `/como-vira-lei` (TRM-044), dentro do próprio rito: as situações
     publicadas de cada fase vão no `extra` da **primeira etapa da fase**
     (onde está a âncora `fase-<fase>`), sob o rótulo "Como a Câmara chama
     esta etapa" e como `TermoGlossario` (abrem a definição no lugar);
     situação sem etapa correspondente no rito escolhido fica numa seção
     curta depois de `#caminho`, "Outras situações da Câmara"
     (`#situacoes-por-fase`).

**Escopo**
- Dentro: a rota, os grupos, a busca, a cobertura, a âncora em `details`,
  os dois pontos de termos inline.
- Fora: situações do Senado (TRM-050); termos genéricos ("parecer",
  "pauta") — não estão em nenhum lote da v1.

**Critérios de aceite**
1. Com `mapa.json`: as entradas publicadas aparecem com termo oficial
   (`dt`, idêntico à fixture), texto, base legal com links, `FaseSelo` sem
   link e `G02`; a entrada com `texto: null` aparece com "Sem explicação
   ainda." (do kit).
2. Linha `S01-cobertura` = "{a} de {t} situações da Câmara já têm
   explicação", com `a` e `t` calculados da fixture.
3. `Busca` filtra por termo e texto, sem acento e sem caixa ("pronta" acha
   "Pronta para Pauta"); `S03` com 0 resultados e "Limpar busca".
4. `/como-vira-lei/situacoes#termo-aguardando_parecer` rola até a entrada,
   destacada pelo `:target` do kit; uma âncora de situação sem explicação
   abre o `Recolhivel`.
5. Em `/proposicoes/{caso 02}`, o termo oficial tem "Ver no glossário" com
   `href` `/como-vira-lei/situacoes#termo-<chave>`.
6. Em `/como-vira-lei`, cada situação publicada aparece no `extra` da
   primeira etapa da sua fase (e só as sem etapa em `#situacoes-por-fase`);
   cada `TermoGlossario` abre com Enter e Espaço, fecha com Esc, e o foco
   volta ao termo.
6a. A lista de `/situacoes` tem um `h3` por termo (navegação por títulos) e
    o alvo da âncora recebe o foco (`tabIndex={-1}` do kit).
7. Nada de texto de entrada não aprovada no HTML (`entradaDaApi` zera; o e2e
   procura o texto de uma entrada `rascunho` da fixture e não acha).
8. `expectPaletaNeutra`; 0 violações em 375/768/1280 × 2 temas, com um
   `TermoGlossario` aberto.

**Specs técnicas**
- `apps/web/app/como-vira-lei/situacoes/page.tsx`: `metadata = { title: "O que quer dizer cada situação — ZIL Observatório", description: "As situações que a Câmara usa para descrever o andamento de uma proposição, explicadas em linguagem simples." }`.
- `apps/web/components/tramitacao/Situacoes.tsx` (`"use client"`).
- Normalização da busca: `texto.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase()`.
- Edita `OndeEsta.tsx` (só o `href`) e `ComoViraLei.tsx` (seção nova).

**Specs de design**

Wireframe 375 px:
```
┌───────────────────────────────────────┐
│ COMO FUNCIONA                         │
│ O que quer dizer cada situação    (h1)│
│ A Câmara descreve o andamento de cada │ S01
│ proposição com termos do regimento. … │
│ 18 de 99 situações da Câmara já têm   │ S01-cobertura
│ explicação                            │
│ ┌ (i) Texto do ZIL, não oficial ────┐ │ Aviso padrao
│ └───────────────────────────────────┘ │
│ [🔍 Buscar, por exemplo, “Pronta…”  ] │ Busca
│ Situações na Câmara              (h2) │
│ Aguardando Despacho do Presidente da  │ h3 = termo oficial
│ Câmara dos Deputados (Chancela)       │ (GlossarioLista nivelTitulo={3})
│ A proposição ainda não foi distribuída│ texto
│ às comissões. …                       │
│ Base: Regimento da Câmara, art. 139 ↗ │
│ (● Apresentada)                       │ extra: FaseSelo
│ Texto do ZIL, não oficial             │ G02
│ …                                     │
│ ▸ Ver as 81 situações ainda sem       │ Recolhivel
│   explicação                          │
│ Regimes de tramitação            (h2) │
│ Quem decide: comissões ou Plenário(h2)│
└───────────────────────────────────────┘
```
1280 px: coluna única em `max-w-leitura`, com os `Chips` de seção no
cabeçalho (padrão de `/metodologia`: "Situações", "Regimes", "Quem decide").

Estados: `S01`–`S03`, `G01`–`G03`, `I07`, carregando (`CardEsqueleto` × 3).

Interações: `Busca` (filtra no cliente, contagem "{n} resultados" com
`aria-live`); `Recolhivel`; `TermoGlossario` (teclado do kit).

Responsividade: uma coluna; sem rolagem horizontal mesmo com termos de 85
caracteres (quebram).

Acessibilidade: um `h1`, `h2` por grupo, `h3` por termo (`article` do kit
com `nivelTitulo={3}`: navegação por títulos numa lista de dezenas de
entradas); o alvo da âncora recebe foco programático (`tabIndex={-1}`, do
kit) para o leitor de tela anunciar onde chegou; reflui a 320 px.

**Testes**
- Vitest — `apps/web/tests/componentes/tramitacao/Situacoes.test.tsx` (grupos
  por `tipo`, `h3` por termo, `texto: null`, entrada `aprovado` com
  `publicavel: false` sem texto, `FaseSelo` com rótulo de `mapa.fases`,
  cobertura com `situacoes_camara`, busca sem acento, `S03`, abertura de
  `details` por hash, axe).
- Playwright — `apps/web/tests/e2e/paginas/situacoes.spec.ts` (critérios 1–4,
  6a, 7, 8; `semRolagemHorizontal` com `@reflow`) e acréscimos em
  `proposicao-onde-esta.spec.ts` (5) e `como-vira-lei.spec.ts` (6).
- Comandos: `npx vitest run tests/componentes/tramitacao/Situacoes.test.tsx`,
  `npx playwright test tests/e2e/paginas/situacoes.spec.ts`.

**Riscos e perguntas em aberto**
- `mapa.situacoes_camara` está no contrato (TRM-028); se a API estiver numa
  versão anterior, a seção "Ainda sem explicação" e a linha de cobertura
  somem, sem erro.
- A cobertura pode parecer baixa. É a verdade do mapa v1 (spec.md §2, "O que
  NÃO é objetivo").

**Instruções para o agente implementador**
- Branch `trm-045-situacoes`, do `main` com TRM-035, TRM-040, TRM-044 e
  TRM-046-B.
- Não fazer: mostrar texto de entrada não aprovada; "corrigir" o termo
  oficial; tooltip ou hover.

### TRM-046 — Matriz de estados e textos, aplicada em todas as superfícies

**Revisão:** DS ✔ (ajustes aplicados) · Arquitetura ✔

**Épico:** E4 Experiência · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M, em duas partes: **046-A** (P, onda 0) e **046-B** (P/M, onda 2)
**Dono da spec:** UI/UX · **Revisões obrigatórias:** UI/UX + Design System; **Maintainer** (todos os textos de `textos.ts`)
**Depende de:** 046-A: contratos do brief (nada mais). 046-B: TRM-001-B (Playwright e helpers), TRM-031-A (`lib/tramitacao/tipos.ts`), contrato de TRM-028 escrito (não precisa estar implementado). A troca das fixtures escritas à mão pelas geradas (`gerado/`, TRM-028 critério 9) é um passo **posterior**, num PR próprio depois de TRM-028: TRM-015 e TRM-016 não esperam por ela · **Desbloqueia:** TRM-015, TRM-016, TRM-040–TRM-045

**Problema** — Seis superfícies vão mostrar os mesmos estados (carregando,
erro, `nao_sabemos` por motivo, recém-apresentada, apensada, cada desfecho,
norma, entrada não aprovada). Sem uma tabela única, cada uma escreve o seu
texto e o site passa a dizer a mesma coisa de três jeitos — ou a dizer
"Fase não identificada" num lugar e nada no outro.

**Oportunidade** — Uma matriz (§4) revisada uma vez pela maintainer, um
módulo de textos que a implementa, e um teste que confere cada superfície
contra ela.

**Solução**

*046-A (onda 0)*
1. `apps/web/lib/tramitacao/textos.ts`: `export const TEXTOS` com uma chave
   por ID da matriz que tem fonte "textos.ts"; textos com marcador são
   funções puras (`(d: { situacao: string; mapaVersao: string }) => string`).
   Nada de JSX.
2. `apps/web/lib/tramitacao/especies.ts`: `nomeEspecie(tipo)` ("Projeto de
   lei"), `nomeEspeciePlural(tipo)` ("projetos de lei"),
   `especieIndefinida(tipo)` ("um projeto de lei"), `comArtigo(rotulo)` ("o PL
   5941/2013", "a PEC 45/2019"), `rotuloProposicao(p)` ("PL 4861/2023"),
   `prefixoNorma(tipoProposicao, tipoNorma)` (`F04`). Espécies: PL, PLP,
   PEC, MPV, PDL, PRC, PLN; desconhecida → "Proposição"/"proposições"/"uma
   proposição".
3. `apps/web/lib/tramitacao/estilo.ts`: as regras V-E1–V-E10 de §2.4 como
   `RegExp` (mesma lista que TRM-024 aplica ao YAML; a fonte é §2.4).
3a. `apps/web/lib/api.ts` — os campos novos de `Proposicao` (TRM-014),
   **opcionais** (`?:`) para a página não quebrar contra a API anterior, com
   tipos idênticos ao contrato (backlog-dados.md §1.5: `date` sai
   `"AAAA-MM-DD"`; `HorarioCamara` e `InstanteUTC` saem ISO com `-03:00`;
   `Optional[...]` = `| null`):
   ```ts
   export type SituacaoEstado = "informada" | "recem_apresentada" | "sem_situacao" | "nao_sincronizada";

   export interface NormaResumo {
     tipo: "lei_ordinaria" | "lei_complementar" | "lei" | "decreto_legislativo" | "emenda_constitucional" | "resolucao";
     rotulo: string;                    // "Lei 14.871/2024"
     numero: number;
     ano: number;
     data: string | null;               // date, "AAAA-MM-DD"
     veto: "parcial" | null;
     url_normas_leg: string | null;
     url_planalto: string | null;
     links_verificados: boolean;
     fonte: "despacho_camara" | "senado_norma_gerada" | "curadoria";
     verificada_em: string | null;      // InstanteUTC, ISO com -03:00
   }

   export interface Proposicao {
     // … campos existentes, inalterados …
     cod_situacao?: string | null;
     situacao_estado?: SituacaoEstado;  // a API sempre manda (padrão "nao_sincronizada"); opcional só para a API antiga
     sigla_orgao?: string | null;        // órgão do último registro — não vai à tela
     orgao_nome?: string | null;         // idem
     orgao_efetivo_sigla?: string | null;
     orgao_efetivo_nome?: string | null;
     regime?: string | null;
     regime_chave?: string | null;
     regime_texto?: string | null;
     apreciacao?: string | null;
     apreciacao_chave?: string | null;
     apreciacao_texto?: string | null;
     relator_nome?: string | null;
     ultima_movimentacao_em?: string | null;   // HorarioCamara, ISO com -03:00
     detalhe_sincronizado_em?: string | null;  // InstanteUTC, ISO com -03:00
     url_camara?: string | null;
     principal_fonte_id?: string | null;
     principal_url_camara?: string | null;
     situacao_glossario?: string | null;
     norma?: NormaResumo | null;
   }
   ```
   Os campos de F1 (`fase`, `fase_rotulo`, `fase_motivo`, `desfecho`,
   `desfecho_rotulo`, `apensada`, `casa_iniciadora`) entram em 046-B, com os
   enums de `lib/tramitacao/tipos.ts` (TRM-031-A), que não existem na onda 0:
   `fase?: FaseOuNaoSabemos | null; fase_rotulo?: string | null; fase_motivo?: MotivoNaoSabemos | null; desfecho?: Desfecho | null; desfecho_rotulo?: string | null; apensada?: boolean; casa_iniciadora?: "camara" | "senado" | null;`.
   Teste de tipo (046-B): cada fixture `proposicao-NN.json` passa com
   `satisfies Proposicao` no `tsc`.

*046-B (onda 2)*
4. `apps/web/lib/tramitacao/estado.ts`:
   ```ts
   export type EstadoExibicao =
     | { tipo: "andamento"; fase: Fase; recem: boolean; apensada: boolean }
     | { tipo: "norma" }
     | { tipo: "desfecho"; desfecho: Desfecho; ondeParou: Fase | null } // fase nula: apensada prejudicada
     | { tipo: "nao_sabemos"; motivo: Exclude<MotivoNaoSabemos, "mapa_nao_aprovado" | "recem_apresentada"> }
     | { tipo: "em_revisao" }  // mapa_nao_aprovado → N06
     | { tipo: "sem_fase" };   // ProposicaoRead.fase nula sem desfecho: fase ainda não calculada
   export function estadoDeExibicao(o: OndeEstaApi): EstadoExibicao;
   export type GrupoFase = Fase | "encerradas" | "nao_identificada";
   export function grupoDeFase(p: Proposicao): GrupoFase | null;
   export function faseSeloPropsDe(p: Proposicao, opcoes?: { comLink?: boolean }): FaseSeloProps | null;
   export function contagensPorEtapa(rito: RitoApi, ps: Proposicao[], especie: Especie, casa: CasaRito | null): Record<string, number>; // casa null = MPV
   ```
   (tipos de `lib/tramitacao/tipos.ts`: `RitoApi`, `Especie`, `CasaRito`.)
   Regras de `estadoDeExibicao`, nesta ordem: `desfecho` não nulo →
   `desfecho` (com `ondeParou = fase`, que pode ser nula); `fase ===
   "nao_sabemos"` e `fase_motivo === "mapa_nao_aprovado"` → `em_revisao`;
   `fase === "nao_sabemos"` → `nao_sabemos` (motivo nulo vale
   `situacao_sem_mapa`); `fase` nula → `sem_fase`; `fase === "norma"` →
   `norma`; senão `andamento`, com `recem = fase_motivo ===
   "recem_apresentada"`. `faseSeloPropsDe` devolve `null` quando
   `fase_rotulo` é nulo (fase não calculada) e para `mapa_nao_aprovado`; com
   desfecho e `fase` nula, passa `fase={null}` (pedido ao DS: aceitar);
   `href` (com `comLink`)
   = `/como-vira-lei?especie={tipo}&casa={casa_iniciadora}#fase-{fase}`
   (MPV: sem `&casa=`), `…#desfechos` para desfecho, `/metodologia#tramitacao`
   para `nao_sabemos` (decisão de §1.2); sem `casa_iniciadora` (exceto MPV) ou
   espécie fora do escopo, sem `href`.
5. `apps/web/lib/tramitacao/api.ts`: `obterTramitacao(id)`,
   `obterEventos(id, pagina, porPagina)` (`?page=&per_page=`; resposta
   `{ items, total, page, per_page, pages }`), `obterMapa()` (memorizado por
   carga de página), `listarTodasProposicoes(params, { maxPaginas = 20 })`
   (para quando já leu `X-Total-Count` itens; sem o cabeçalho, quando uma
   página vem com menos de 100), cada um devolvendo
   `{ status: "ok"; dados } | { status: "ausente" } | { status: "falha" }`
   (a lista: `{ itens, total, completa }` ou falha).
6. Fixtures de §0.4 em `apps/web/tests/fixtures/api/tramitacao/` e
   `montar-lista.mjs`.
7. `apps/web/tests/e2e/matriz.ts` — a matriz como dado: `{ id, superficie:
   "P" | "L" | "C" | "S", caso, seletor, texto }[]`, com o texto vindo de
   `TEXTOS` (ou da fixture, para textos da API); e
   `apps/web/tests/e2e/paginas/matriz.spec.ts`, que percorre as linhas cujas
   superfícies estão em `SUPERFICIES_PRONTAS` (constante no mesmo arquivo).
   Cada tarefa de superfície acrescenta a sua letra quando entra.

**Escopo**
- Dentro: matriz (§4), os módulos acima, fixtures, harness da matriz, testes.
- Fora: textos da API (mapa e glossário: TRM-021/022 e lotes); textos padrão
  dos componentes do kit (DS) — validados aqui, trocados por prop quando a
  matriz pedir.

**Critérios de aceite**
1. (A) Todo ID da §4 com fonte "textos.ts" tem chave em `TEXTOS`, e
   vice-versa (teste que lê a lista de IDs de um array exportado
   `IDS_MATRIZ`).
2. (A) Nenhuma string de `TEXTOS` (com os marcadores preenchidos por valores
   de exemplo) casa com V-E1–V-E10.
3. (A) `especies.ts`: as 7 espécies e a desconhecida; `comArtigo` para
   PL/PLP/PDL/PRC/PLN ("o") e PEC/MPV ("a"); `prefixoNorma` para cada
   `NormaResumo.tipo` (`lei_ordinaria`, `lei_complementar`, `lei` → "Virou
   lei"; `decreto_legislativo`; `emenda_constitucional`; `resolucao`) e MPV →
   "Convertida em lei".
3b. (A) `lib/api.ts` com os campos e tipos do bloco 3a; `npx tsc --noEmit`
   verde com as páginas atuais (nada obrigatório novo).
4. (B) `estadoDeExibicao` para os casos 02, 05, 08, 11, 12, 15–21, 26–30 e um
   caso de apensada prejudicada com `fase: null` dá o estado esperado
   (tabela no teste).
5. (B) `faseSeloPropsDe` nunca devolve `href` com `comLink: false`; devolve
   `null` no caso 30.
6. (B) Toda fixture passa no `tsc` com `satisfies` contra os tipos de
   `lib/tramitacao/tipos.ts` (`tests/unit/tramitacao/fixtures.test.ts`
   importa cada JSON).
7. (B) `listarTodasProposicoes`: com `X-Total-Count`, para ao atingir o
   total e devolve `total`; sem o cabeçalho, para em página com < 100 itens;
   falha na 1ª → `falha`; falha na 2ª → `{ completa: false }`; respeita
   `maxPaginas`.
7a. (B) Fixtures reais substituíveis pelas geradas
   (`apps/web/tests/fixtures/api/tramitacao/gerado/`, TRM-028): os testes
   referem fixtures por nome de caso, não por caminho de arquivo.
8. (B) `matriz.spec.ts` roda verde com `SUPERFICIES_PRONTAS = []` (nenhuma
   linha) e falha se uma linha apontar para caso inexistente.

**Specs técnicas** — arquivos e assinaturas acima; testes em
`apps/web/tests/unit/tramitacao/{textos,especies,estilo,estado,api,fixtures}.test.ts`.

**Specs de design** — a matriz (§4) é a spec de design desta tarefa: para
cada estado, selo, texto, tom do aviso, superfícies e fonte do texto.

**Testes** — os dos critérios. Comandos: `npx vitest run tests/unit/tramitacao`,
`npx playwright test tests/e2e/paginas/matriz.spec.ts`.

**Riscos e perguntas em aberto**
- Duas fontes de verdade para "Fase não identificada" (API e `TEXTOS`):
  mitigado por teste de contrato em TRM-028 e pela linha `N00` do
  `matriz.spec.ts`.
- `IDS_MATRIZ` duplica a lista de IDs desta spec; é deliberado (o teste
  precisa de algo para comparar). Mudança de texto começa aqui, na §4.

**Instruções para o agente implementador**
- Branches `trm-046a-textos` (onda 0: `textos.ts`, `especies.ts`,
  `estilo.ts`, campos de F0 em `lib/api.ts`) e `trm-046b-estado-fixtures`
  (depois de TRM-001-B e TRM-031-A: `estado.ts`, `api.ts`, campos de F1,
  fixtures, harness).
- O PR de 046-A pede revisão da maintainer **texto a texto** (tabela da §4
  no corpo do PR).
- Não fazer: JSX em `textos.ts`; texto de fase ou desfecho em `textos.ts`
  (são da API); mudar texto sem mudar a §4 no mesmo PR.

---

## 4. Matriz de estados e textos (TRM-046)

Tabela única, usada por todas as superfícies. **Superfícies**: P = página da
proposição; L = lista; C = `/como-vira-lei`; S = `/como-vira-lei/situacoes`.
**Fonte**: `textos.ts` = `apps/web/lib/tramitacao/textos.ts` (aprovado pela
maintainer no PR de TRM-046-A); API = vem pronto da API do ZIL (mapa ou
glossário publicável; valores entre chaves); Câmara = texto oficial, sem
edição; kit = texto padrão do componente do DS (validado aqui; "troca" = esta
matriz substitui por prop). Aspas curvas “ ” dentro dos textos fazem parte do
texto. Nenhum estado usa `zil-alinhado*`, `zil-contra*` ou `zil-neutro*`; o
único `Aviso tom="contra"` é para erro de API que impede o conteúdo (I03,
I09); nos e2e desses dois estados, `expectPaletaNeutra` não roda na região do
aviso (o `contra` é o tom do kit para erro). Falha parcial (I05, I07, I10,
I14) é `padrao`.

| ID | Estado / condição | Selo (`FaseSelo`) | Texto exato | Componente / tom | Sup. | Fonte | Tarefa |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I01 | Página da proposição carregando | — | Esqueleto com a forma do conteúdo; nome acessível "Carregando proposição" | `Esqueleto`, `aria-busy` | P | existe | 015 |
| I02 | `GET /proposicoes/{id}` → 404 | — | Título "Proposição não encontrada" · corpo "O endereço pode estar errado ou a proposição saiu da cobertura." · ação "Ver todas as proposições" | `Vazio` | P | existe | 015 |
| I03 | `/proposicoes/{id}` → rede ou 5xx | — | Título "Não foi possível carregar a proposição" · corpo "A API não respondeu. Confira a conexão e tente de novo em instantes." · ação "Tentar de novo" | `Aviso` contra | P | textos.ts | 015 |
| I04 | Tramitação carregando | — | Leitor: "Carregando a tramitação" | `FaseSeloEsqueleto`, `EtapasEsqueleto`, `aria-busy` | P | textos.ts | 040 |
| I05 | `/tramitacao` → rede ou 5xx | — | Título "Não conseguimos carregar a fase agora" · corpo "Abaixo está a situação oficial da Câmara, que vem de outra consulta." · ação "Tentar de novo"; em seguida, `SituacaoCamara` | `Aviso` padrao | P | textos.ts | 040 |
| I06 | `/tramitacao` → 404, ou fase ainda não calculada (`sem_fase`) | — | Sem aviso; `SituacaoCamara` | — | P | — | 040 |
| I07 | `/tramitacao/mapa` → rede, 5xx ou 503 | — | Em "Onde está agora": definições e explicações omitidas, sem aviso. Em "O caminho inteiro" e em C: título "Não conseguimos carregar o caminho agora"; em S: "Não conseguimos carregar as explicações agora" · corpo "Tente de novo em instantes. A situação oficial de cada proposição continua disponível." · ação "Tentar de novo" | `Aviso` padrao | P C S | textos.ts | 040, 042, 044, 045 |
| I08 | Lista carregando | — | 6 cartões-esqueleto; nome "Carregando proposições" | `CardEsqueleto` | L | existe | 016 |
| I09 | Lista: 1ª página falhou | — | Título "Não foi possível carregar as proposições" · corpo "A API não respondeu. Confira a conexão e tente de novo em instantes." · ação "Tentar de novo" | `Aviso` contra | L | existe | 016 |
| I10 | Lista: página seguinte falhou | — | Título "A lista está incompleta" · corpo "Carregamos {n} proposições, mas a API não respondeu ao pedir o resto. A contagem e os filtros consideram só essas." · ação "Tentar de novo" | `Aviso` padrao | L | textos.ts | 016 |
| I11 | Lista vazia, sem filtros | — | "Nenhuma proposição classificada ainda" · "A cobertura ainda está em formação: as proposições entram conforme a curadoria classifica cada pauta." | `Vazio` | L | existe | — |
| I12 | Lista vazia com filtros | — | Sem fase ativa (existe): "Nenhuma proposição com esses filtros" · "Tente outra pauta, tipo ou ano, ou busque por outro termo." · "Limpar filtros". Com fase ativa: título "Nenhuma proposição nesta fase com esses filtros" · corpo "Tente outra fase, pauta, tipo ou ano." · ação "Limpar filtros" | `Vazio` | L | textos.ts | 016, 043 |
| I13 | Registros carregando | — | Leitor: "Carregando os registros." | `TodosOsRegistros` | P | kit | 041 |
| I14 | Registros falharam | — | Título "Não conseguimos carregar os registros." · corpo "Os marcos acima continuam valendo." · ação "Tentar de novo" (`onTentarDeNovo` → refaz `obterEventos`; reabrir o recolhível também refaz) | `TodosOsRegistros` (`Aviso` **padrao** do kit — falha parcial) | P | kit | 041 |
| I15 | `marcos: []` e `eventos_total > 0` | — | "Ainda não identificamos marcos nesta tramitação. Os registros completos da Câmara estão logo abaixo." | texto `text-texto-s` | P | textos.ts | 041 |
| I16 | `eventos_total = 0` | — | "A Câmara ainda não registrou movimentações desta proposição." | texto | P | textos.ts | 041 |
| F01 | `situacao_estado = informada` | — | P: rótulo "Situação oficial" (F1: "Situação oficial na Câmara") + `{situacao}` inteira · L: "Situação na Câmara: {situacao}" | texto; nunca `Selo` | P L | Câmara | 015, 016 |
| F02 | `situacao_estado = recem_apresentada` | — | P: "Ainda não informada pela Câmara." e, abaixo, "Recém-apresentada, em {data_apresentacao}." · L: "Situação na Câmara: ainda não informada." | texto | P L | textos.ts | 015, 016 |
| F03 | `situacao_estado = sem_situacao` | — | P: "Ainda não informada pela Câmara." · L: "Situação na Câmara: ainda não informada." | texto | P L | textos.ts | 015, 016 |
| F13 | `situacao_estado = nao_sincronizada` | — | P: "Ainda não conferimos a situação desta proposição na Câmara." · L: "Situação na Câmara: ainda não conferida." | texto | P L | textos.ts | 015, 016 |
| F04 | `norma` preenchida | — | "{prefixo}: {norma.rotulo}" — `norma.tipo` `lei_ordinaria`, `lei_complementar`, `lei` → "Virou lei" (proposição MPV → "Convertida em lei"); `decreto_legislativo` → "Virou decreto legislativo"; `emenda_constitucional` → "Virou emenda constitucional"; `resolucao` → "Virou resolução". Com `veto = "parcial"`: "Sancionada com veto parcial: partes do texto foram vetadas pelo Presidente da República." Links "Ler o texto no normas.leg.br" e "Ler o texto no Planalto", cada um só com a URL, leitor "(abre em nova aba)". L: só a primeira linha | P `text-titulo-4`; L `text-texto-s font-medium` | P L | textos.ts + API | 015, 016 |
| F05 | `situacao` = "Transformado em Norma Jurídica" e `norma` nula | — | "A Câmara registra que esta proposição virou norma, mas o número não aparece no despacho. Confira no site da Câmara." | texto | P | textos.ts | 015 |
| F06 | `regime` e `apreciacao` nulos | — | `dt` "Regime e quem decide" · `dd` "Ainda não definidos. São fixados no despacho que distribui a proposição às comissões." | `dl` | P | textos.ts | 015 |
| F07a | `regime_texto` (ou `apreciacao_texto`) preenchido — lote L0 aprovado | — | `dd` `{regime_texto}` e, abaixo, "Na Câmara: {regime}" | `dl`; termo em `text-texto-s text-zil-texto-2` | P | API + Câmara | 015, 040 |
| F07b | `*_texto` nulo e termo oficial presente (antes do L0, ou regime sem entrada) | — | `dd` só `{regime}` (ou `{apreciacao}`), sem nota | `dl` | P | Câmara | 015, 040 |
| F08 | Urgência + apreciação conclusiva | — | Sem texto próprio: a API manda `apreciacao_texto` de `apreciacao_conclusiva_com_urgencia` ou nulo (§2.7); a interface aplica F07a/F07b | — | P | API | 015 |
| F09 | Data da conferência | — | "Conferido na Câmara em {data}" | `text-texto-s text-zil-texto-2` | P | textos.ts | 015, 040 |
| F10 | Órgão | — | `dt` "Órgão atual" · `dd` F0: "{orgao_efetivo_nome} ({orgao_efetivo_sigla})" ou só "{orgao_efetivo_sigla}"; F1: "{onde_esta.orgao_nome} ({onde_esta.sigla_orgao})" (já o órgão efetivo); sem os dois, linha omitida. Nunca `sigla_orgao`/`orgao_nome` de `ProposicaoRead` (órgão do último registro: CCP/MESA em 23 das 240) | `LinhasDaSituacao` | P | API | 015, 040 |
| F11 | F0: `principal_url_camara` preenchido | — | `dt` "Tramita junto com" · `dd` link "Ver a proposição principal na Câmara" para `principal_url_camara` (como veio da API; a interface não monta URL), leitor "(abre em nova aba)" | `LinhasDaSituacao` | P | textos.ts | 015 |
| F12 | Relatoria | — | `dt` "Relatoria" · `dd` F0: "{relator_nome}"; F1: "{relator.nome}" + " ({partido}-{uf})" quando houver; link para `/parlamentar/{parlamentar_id}` **só** com `rankingPublico`; sem relator, linha omitida | `dl` | P | API | 015, 040 |
| X01 | Link para a Câmara | — | Visível "Ver na Câmara" · leitor " o {rotulo} (abre em nova aba)" | `Button` fantasma s + `Icone externo` | P | textos.ts | 015, 040 |
| L01 | Situação no cartão | — | F01, F02, F03, F13 (versão L) | texto | L | — | 016 |
| L02 | Datas no cartão | — | "Última movimentação em {data} · Apresentada em {data}" (cada parte só com o dado; sem as duas, linha omitida) | `text-texto-s text-zil-texto-2 zil-num` | L | textos.ts | 016 |
| L03 | Ordenação | — | Vazio "Ordenar"; opções "Movimentação mais recente", "Apresentação mais recente", "Apresentação mais antiga" | `Seletor` | L | textos.ts | 016 |
| L04 | Contagem | — | As existentes ("{n} proposições", "… analisadas", "… sem análise") e, com fase ativa, + " — fase: {rótulo do chip}" | `aria-live="polite"` | L | textos.ts | 016, 043 |
| L05 | Filtros | — | Grupo "Pauta" (categorias); grupo "Fase": "Todas", "Apresentadas", "Nas comissões", "No Plenário", "Na outra Casa", "De volta à Casa de origem", "Com o Presidente da República", "Veto em análise", "Aguardando promulgação", "Viraram norma", "Encerradas", "Fase não identificada"; chip de Casa "Começou na Câmara" / "Começou no Senado" | `Chip` com `n` | L | textos.ts | 043 |
| L06 | Link no cabeçalho da lista | — | "Como uma proposição vira lei" (seta "→" só visual, `aria-hidden`) | link de texto | L | textos.ts | 043 |
| P01 | `apresentada` | ● Apresentada | Frase da API (§2.9); explicação = glossário `fase_apresentada`; T01 | `Etapas` compacta + legenda | P L C | API | 040, 043 |
| R01 | `apresentada` + `fase_motivo = recem_apresentada` | ● Recém-apresentada | Frase da API; no lugar da situação oficial: "Ainda não informada pela Câmara." | idem | P L | API + textos.ts | 040, 043 |
| P02 | `comissoes` | ● Nas comissões · MPV: Na comissão mista | Frase; explicação `fase_comissoes`; T01 | idem | P L C | API | 040, 043 |
| P03 | `plenario` | ● No Plenário da Câmara · No Plenário do Senado | Frase; explicação `fase_plenario`; T01 | idem | P L C | API | 040, 043 |
| P04 | `outra_casa` | ● No Senado · Na Câmara | Frase; explicação `fase_outra_casa`; T01 | idem | P L C | API | 040, 043 |
| P05 | `retorno` | ● De volta à Câmara · De volta ao Senado | Frase; explicação `fase_retorno`; T01 | idem | P L C | API | 040, 043 |
| P06 | `sancao` | ● Com o Presidente da República | Frase; explicação `fase_sancao` (diz o prazo de 15 dias úteis); **sem** T01 | idem | P L C | API | 040, 043 |
| P07 | `veto_congresso` | ● Veto em análise no Congresso | Frase; explicação `fase_veto_congresso`; T01 | idem | P L C | API | 040, 043 |
| P08 | `promulgacao` | ● Aguardando promulgação | Frase; explicação `fase_promulgacao`; T01 | idem | P L C | API | 040, 043 |
| P09 | `norma` | Virou lei · Virou emenda constitucional · Virou decreto legislativo · Convertida em lei (glifo `documento`) | Frase; F04; explicação `fase_norma`; legenda "Etapa {n} de {n}: {nome}"; **sem** T01 | idem | P L C | API | 040, 043 |
| D01 | `desfecho = arquivada` | Arquivada (glifo `parada`) | Frase ("Arquivada em {data}."); explicação `desfecho_arquivada`; legenda "Parou na etapa {i} de {n}: {nome}"; sem T01; na lista, grupo "Encerradas" | `Etapas` com `interrompida` | P L | API | 040, 043 |
| D02 | `retirada` | Retirada pela autoria | idem, `desfecho_retirada` | idem | P L | API | 040, 043 |
| D03 | `prejudicada` | Prejudicada | idem, `desfecho_prejudicada` | idem | P L | API | 040, 043 |
| D04 | `rejeitada` | Rejeitada | idem, `desfecho_rejeitada` | idem | P L | API | 040, 043 |
| D05 | `perdeu_eficacia` | Perdeu a eficácia | idem, `desfecho_perdeu_eficacia` | idem | P L | API | 040, 043 |
| D06 | `vetada` | Vetada | idem, `desfecho_vetada` | idem | P L | API | 040, 043 |
| D07 | `devolvida` | Devolvida à autoria | idem, `desfecho_devolvida` | idem | P L | API | 040, 043 |
| D08 | Desfecho com `fase` nula (apensada prejudicada) | rótulo do desfecho | Frase e explicação do desfecho; **sem** `Etapas` e sem legenda | — | P L | API | 040 |
| A01 | `apensada` e `herdada_de.acompanhada` | selo da fase herdada + "Em conjunto" (kit) | Título "Tramita junto com {principal_com_artigo}" · corpo "{herdada_de.rotulo} é a proposição principal. As duas andam juntas e recebem um parecer só; por isso, a fase mostrada aqui é a da principal." · ação "Ver a proposição principal" (`/proposicoes/{id}`) | `Aviso` padrao + `Button` secundario | P (L: só o selo) | textos.ts | 040, 043 |
| A02 | `apensada` e `!herdada_de.acompanhada` (principal só de contexto — D2; `id` vem preenchido) | idem | Mesmo título e corpo · ação "Ver a proposição principal na Câmara" (`herdada_de.url_camara`), leitor "(abre em nova aba)"; sem URL, sem ação | idem | P | textos.ts | 040 |
| N00 | Selo de `nao_sabemos` (exceto `mapa_nao_aprovado`) | Fase não identificada (glifo `duvida`; **no cabeçalho, link para `/metodologia#tramitacao`**, sufixo lido ", entenda por quê" — decisão de §1.2; na lista, sem link) | — | `FaseSelo` padrao | P L | **esta matriz**; a API copia como `fase_rotulo` (teste de igualdade em TRM-028) | 040, 043 |
| N01 | `nao_sabemos(situacao_sem_mapa)` | N00 | Título "Não sabemos em que fase está" · corpo "A situação oficial na Câmara, “{situacao}”, ainda não está no nosso mapa de fases (versão {versao_publicada}). Preferimos não adivinhar." (sem situação: "A situação oficial desta proposição ainda não está no nosso mapa de fases (versão {versao_publicada}). Preferimos não adivinhar.") | `Aviso` padrao | P | textos.ts | 040 |
| N02 | `sinais_conflitantes` | N00 | Título "Não sabemos em que fase está" · corpo "A situação oficial na Câmara, “{situacao}”, e o último despacho não batem entre si. Preferimos não adivinhar: confira o andamento no site da Câmara." | `Aviso` padrao | P | textos.ts | 040 |
| N03 | `principal_nao_resolvida` | N00 | Título idem · corpo "Esta proposição tramita junto com outra, e a fase dela é a da principal. Não conseguimos identificar a principal nos dados da Câmara." | `Aviso` padrao | P | textos.ts | 040 |
| N04 | `fonte_indisponivel` (inclui situação nula **sem** histórico — R9 nova; nula com histórico vira a fase do último marco, sem aviso) | N00 | Título idem · corpo "Os dados da Câmara não bastam para saber: a situação oficial não foi informada, ou a Câmara não respondeu quando conferimos, em {conferido_em}. Confira o andamento no site da Câmara." (sem data: "… quando conferimos. Confira o andamento no site da Câmara.") | `Aviso` padrao | P | textos.ts | 040 |
| N05 | `especie_fora_do_escopo` | N00 | Título idem · corpo "O ZIL ainda não acompanha as fases de {especie_plural}." (desconhecida: "deste tipo de proposição") | `Aviso` padrao | P | textos.ts | 040 |
| N06 | `nao_sabemos(mapa_nao_aprovado)` | **nenhum** (nem na lista; conta só em "Todas") | Título "Fase em revisão" · corpo "A explicação desta situação ainda está em revisão e só vai ao ar depois de aprovada. Enquanto isso, mostramos a situação oficial da Câmara." e, abaixo, `SituacaoCamara` (com a definição da situação aberta, se publicável) | `Aviso` padrao | P | textos.ts | 040, 043 |
| T01 | Fase em andamento, exceto `sancao` | — | "O ZIL não estima quando a proposição vai avançar: isso depende de quem conduz esta etapa." | texto `text-texto-s text-zil-texto-2` | P | textos.ts | 040 |
| G01 | Situação sem definição publicável | — | "Sem explicação ainda." | texto | P S | kit | 040, 045 |
| G02 | Marca de texto do ZIL | — | "Texto do ZIL, não oficial." — agora é o padrão do kit (`nota` do `TermoGlossario` e da `GlossarioLista`), igual a spec.md §6.7 e ao `aviso` do mapa | `TermoGlossario`, `GlossarioLista` | P C S | kit | 040, 045 |
| G03 | Nome do gatilho do `TermoGlossario` | — | Leitor: "{termo}, o que quer dizer" (sufixo `rotuloAcao`, padrão do kit) · `indicador`: ícone `info` fora do nome acessível | `TermoGlossario` | P C | kit | 040, 045 |
| C01 | Nota do "Como sabemos" | — | "A fase é uma leitura do ZIL a partir dos dados oficiais; a situação oficial é o texto da Câmara, sem edição." · `saibaMais={{ rotulo: "Como chegamos a esta fase", href: "/metodologia#tramitacao" }}` (`TEXTOS.C01`, `TEXTOS.C01_SAIBA_MAIS`) · fonte acrescentada, se a API não mandar: "Regras do mapa de fases — data/tramitacao/fases.yml" (link para o GitHub, leitor "(abre em nova aba)" do kit) | `ComoSabemos` | P | textos.ts | 040 |
| C03 | `comoSabemosDaFase` → `null` (fase sem fonte) | — | "Sem fonte registrada para esta leitura." — é defeito de dado: o aviso do adaptador faz o teste falhar | texto | P | textos.ts | 040 |
| C04 | Resumo do "Como sabemos" fechado | — | "Leitura do ZIL, conferida na Câmara em {data}" (sem data: "Leitura do ZIL") — regra e versão do mapa só dentro | `ComoSabemos` (padrão de `comoSabemosDaFase`) | P | kit | 040 |
| E01 | Textos de `Etapas` | — | "Etapas da tramitação" · "Etapa {i} de {n}: {nome}" · "Parou na etapa {i} de {n}: {nome}" · "{n} etapas; a etapa atual não foi identificada" · "(concluída)" · "(etapa atual)" · "(ainda não aconteceu)" · `atual`: "Desde {data}" (sem data: "Está aqui") · `pulada`: "Dispensada" (com `nota`: "Dispensada · {nota}") · "Parou aqui" · "Não aconteceu" — validados | `Etapas` | P | kit | 040 |
| E02 | Textos de `RitoDiagrama` | — | Validados: "Está aqui", "Desde {data}", "Dispensada", "Parou aqui", "Foi o que aconteceu", "Pode terminar aqui", "A qualquer momento", "Desfechos possíveis em qualquer etapa", "Explicação ainda não publicada.", "Quem decide:", "Prazo:", "Base:", "{n} proposições acompanhadas estão aqui agora" / "1 proposição acompanhada está aqui agora" (seta "→" `aria-hidden`). **Classes de prazo — decisão (rodada 3):** rótulos curtos D "fixado na regra" · D\* "fixado na regra, mas costuma não ser cumprido" · X "sem prazo fixo"; legenda "Como ler os prazos": **Fixado na regra** — "A Constituição ou o regimento fixam o prazo." · **Fixado, mas costuma não ser cumprido** — "A regra fixa o prazo, mas, na prática, ele costuma não ser cumprido, sem consequência." · **Sem prazo fixo** — "Quem preside a comissão ou a Casa decide quando a proposição anda." ("norma", "discricionária", "quórum" e "requerimento" são jargão, §2.5; a troca no kit é de uma linha, conflito 19 do DS) | `RitoDiagrama` | P C | kit | 042, 044 |
| E03 | Textos de `FaseSelo` | — | "Fase: ", "Desfecho: ", "Em conjunto", "Tramita em conjunto com a proposição principal", ", entenda esta fase", ", entenda este desfecho", ", entenda por quê" — validados | `FaseSelo` | P L | kit | 040, 043 |
| M01 | Legenda dos marcos | — | "Em ordem cronológica" | texto | P | textos.ts | 041 |
| M02 | Registros | — | `fonte` (troca o padrão do kit): "No texto original da Câmara dos Deputados, do mais recente para o mais antigo" · título (kit) "Todos os {n} registros" / "1 registro" · leitor (kit) "{n} registros carregados." · ação de erro (kit) "Tentar de novo" · `Paginacao`: "Mostrando {a}–{b} de {total}" · data de cada registro sem hora | `TodosOsRegistros` | P | textos.ts + kit | 041 |
| M03 | Marcos anteriores | — | "Ver os {n} marcos anteriores" (1: "Ver o marco anterior") | `Recolhivel` | P | textos.ts | 041 |
| K00 | "O caminho inteiro" | — | Intro: "O caminho de {especie_indefinida} que começa {na Câmara \| no Senado}. A etapa atual aparece marcada." (MPV: "O caminho de uma medida provisória. A etapa atual aparece marcada.") · recolhível "Ver as {n} etapas, com o que acontece em cada uma" · botão "Entender como uma proposição vira lei" | `Recolhivel`, `Button` secundario | P | textos.ts | 042 |
| K01 | Rito com `publicavel: false` (vem com `etapas: []`; o `RitoDiagrama` não é renderizado) | — | "O caminho de {especie_plural} ainda está em revisão e só aparece depois de aprovado." + link "Como uma proposição vira lei" (em C, sem o link) | texto | P C | textos.ts | 042, 044 |
| K02 | Espécie sem rito no mapa (PLN, PRC) | — | "Ainda não descrevemos o caminho de {especie_plural}." | texto | P C | textos.ts | 042, 044 |
| K03 | `nao_sabemos`, `fase` nula ou `rito: null` | — | "Não sabemos em que etapa esta proposição está. O caminho abaixo é o da espécie, sem marcação." | texto | P | textos.ts | 042 |
| V01 | Textos fixos de `/como-vira-lei` | — | Chapéu "Como funciona" · `h1` "Como uma proposição vira lei" · linha fina "O caminho de uma proposição no Congresso: quem decide cada passo, o que diz a regra e onde ela pode parar." · aviso: título "Texto do ZIL, não oficial" / corpo "Escrito a partir da Constituição e dos regimentos da Câmara e do Senado. Cada etapa cita a regra. Mapa de fases versão {versao_publicada}." · grupos "Tipo de proposição" e "Começa" · chips "Lei (PL)", "Lei complementar (PLP)", "Emenda à Constituição (PEC)", "Medida provisória (MPV)", "Decreto legislativo (PDL)", "Na Câmara", "No Senado" · no `extra` da primeira etapa de cada fase (TRM-045): rótulo "Como a Câmara chama esta etapa" · `h2` "O caminho", "Outras situações da Câmara" (TRM-045, só se houver situação sem etapa), "Onde uma proposição pode parar", "Tramitação em conjunto", "Depois que vira lei", "Como montamos este mapa" · fim de "Depois que vira lei": "O ZIL ainda não acompanha a regulamentação das leis." · "Como montamos este mapa": "Este mapa é do ZIL e é revisado antes de ir ao ar. Como fazemos: Metodologia." + links "Ver o mapa no GitHub" e "O que quer dizer cada situação" | `TituloSecao`, `Aviso` padrao, `Chip href` | C | textos.ts | 044, 045 |
| V02 | Nenhum rito publicável | — | Chapéu "Como funciona" · `h1` "Esta página ainda está em revisão" · "O mapa das etapas é escrito pelo ZIL e só vai ao ar depois de revisado. Enquanto isso, cada proposição mostra a situação oficial da Câmara, como a Câmara escreve." · botões "Ver proposições" (primário, `/proposicoes`) e "Como o ZIL trabalha" (secundário, `/metodologia#tramitacao`) | `Painel` | C | textos.ts | 044 |
| S01 | Textos fixos de `/situacoes` | — | Chapéu "Como funciona" · `h1` "O que quer dizer cada situação" · linha fina "A Câmara descreve o andamento de cada proposição com termos do regimento. Aqui está o que cada um quer dizer, em linguagem simples." · cobertura "{a} de {t} situações da Câmara já têm explicação" · aviso: título "Texto do ZIL, não oficial" / corpo "A situação oficial aparece exatamente como a Câmara escreve. A explicação é do ZIL e só vai ao ar depois de revisada." · `Busca` rótulo "Buscar situação ou termo", placeholder "Buscar, por exemplo, “Pronta para Pauta”" · `h2` "Situações na Câmara", "Regimes de tramitação", "Quem decide: comissões ou Plenário" · chips de seção "Situações", "Regimes", "Quem decide" · recolhível "Ver as {n} situações ainda sem explicação" | `GlossarioLista`, `Busca`, `Recolhivel` | S | textos.ts | 045 |
| S02 | Resultado da busca | — | "{n} resultados" · "1 resultado" | `aria-live="polite"` | S | textos.ts | 045 |
| S03 | Busca sem resultado | — | "Nenhuma situação ou termo com “{busca}”." · ação "Limpar busca" | `Vazio` | S | textos.ts | 045 |

Notas de uso:
- Marcadores com valor nulo nunca viram "null", "undefined" ou "—": usa-se a
  variante indicada na própria linha; sem variante, a oração some.
- `{especie_plural}`, `{especie_indefinida}` e `{principal_com_artigo}` vêm de
  `especies.ts` (TRM-046-A); `{data}` sempre por `dataBR`.
- Os textos marcados "API" são conteúdo de §2.6–2.9 e passam pelos lotes de
  TRM-029; os marcados `textos.ts` passam pela maintainer no PR de
  TRM-046-A (e nos PRs de tarefa que acrescentarem linha a esta matriz).

---

## 5. Ordem de implementação e paralelização

Alinhada às ondas de spec.md §5.1, ao arquivo-quente de §5.4 e à ordem do DS
(backlog-design-system.md §3). "Agente" = um agente de UI/UX numa worktree
própria.

| Onda | Interface | Depende de (mergeado) | Paralelo com |
| --- | --- | --- | --- |
| 0 | **TRM-046-A** (textos, espécies, estilo, campos de F0 de `Proposicao` em `lib/api.ts`) | nada | tudo da onda 0; o PR fica aberto até a maintainer revisar os textos |
| 1–2 | **TRM-022** rascunho do glossário: L0 (regimes, apreciação) primeiro, depois L4 (situações) e as entradas `fase_*`/`desfecho_*`/`apensada`/`especie_*` | TRM-020, TRM-021 (esquema), TRM-024 (validador) | DS 030–035; o texto pode ser escrito antes, o PR entra depois do validador |
| 2 | **TRM-046-B** (estado, api, fixtures, harness da matriz) | TRM-001-B, TRM-031-A; contrato de TRM-028 escrito | TRM-022 |
| 3 | **TRM-015** e **TRM-016** — dois agentes | TRM-014, TRM-033, TRM-046-B; PR #49 antes de 015 | um ao outro (arquivos diferentes) |
| 5 | **TRM-040** (cria o orquestrador e a estrutura) | TRM-028, 030, 031, 033, 035, 037, 047, 015 | **TRM-043** (outro agente: lista) |
| 5 | **TRM-041** depois de 040; **TRM-044** depois de 043 e de 034-B | idem + 032 / 034-B | um ao outro |
| 5 | **TRM-042** depois de 041; **TRM-045** depois de 044 e 040 | idem | um ao outro |

Com dois agentes de UI/UX na onda 5: agente A — 040 → 041 → 042 (página da
proposição); agente B — 043 → 044 → 045 (lista e páginas explicativas).
TRM-045 toca dois arquivos do agente A (`OndeEsta.tsx`, só o `href`) e um do
B (`ComoViraLei.tsx`): rebasear sobre os dois.

Arquivos quentes desta parte (uma tarefa por vez; quem chega depois
rebaseia):

| Arquivo | Ordem |
| --- | --- |
| `apps/web/app/proposicoes/[id]/page.tsx` | #49 → 015 → 040 |
| `apps/web/components/tramitacao/TramitacaoProposicao.tsx` | 040 → 041 → 042 |
| `apps/web/components/tramitacao/OndeEsta.tsx` | 040 → 045 |
| `apps/web/app/proposicoes/page.tsx`, `ListaProposicoes.tsx`, `CartaoProposicao.tsx` | 016 → 043 |
| `apps/web/components/tramitacao/ComoViraLei.tsx` | 044 → 045 |
| `apps/web/lib/tramitacao/textos.ts`, `apps/web/tests/e2e/matriz.ts` | 046-A → (cada tarefa acrescenta as suas linhas) |
| `data/tramitacao/glossario.yml` | 022 (L0) → 022 (L4) → lotes de TRM-029 |

Gates de publicação (o código pode mergear antes; o conteúdo acende
sozinho): TRM-015 e TRM-016 só vão ao ar com TRM-012 executado em produção
(`completo`, as 5 do placar conferidas) — antes disso todas sairiam `F13`;
L0 → `F07a` em TRM-015; L1 + L2 → fase em TRM-040 e TRM-043; L3 →
marcos em TRM-041; L4 → definições em TRM-040 e TRM-045; L5/L6 → ritos em
TRM-042 e TRM-044; L7 (glossário `fase_*` e `apensada`) → explicação da fase
em TRM-040 e entradas de fase em TRM-045. Antes de cada lote, a interface mostra o estado seguro
correspondente (`F07b`, `N06`, `I15`, `G01`, `K01`/`V02`).

---

## 6. Resumo para os outros especialistas

**Escrevi:** arquitetura de informação (perguntas por superfície, mapa de
rotas e âncoras, ordem das seções da proposição), inventário de consumo dos
componentes do DS, guia de redação com regras automáticas V-E1–V-E10 e
rascunhos de texto para 18 situações, 10 regimes/apreciações, 9 fases, 7
desfechos, apensada, 5 espécies e os templates de frase; specs de TRM-015,
016, 022, 040–046; matriz única (§4); ordem (§5). TRM-046 dividida em 046-A
(onda 0) e 046-B (onda 2), sem ID novo.

**Achados:** "Apresentada em" mostra um dia a menos (data só-dia lida como
UTC); a lista exibe só 100 das 240; erro 500 vira "proposição" na página;
"desde" não existe em F0; RICD art. 137 resolve o ⚠ da devolução; o
desarquivamento do art. 105 foi revogado (RCD 33/2022) — "pode ser
desarquivada" não vale para a Câmara (spec.md §10.1 e disc. §6.2 precisam
mudar).

**Arquitetura (pedidos — atendidos na rodada 2):** regra urgência +
conclusiva → `apreciacao_conclusiva_com_urgencia` (9 casos);
`mapa.situacoes_camara`; timestamps em `-03:00`; âncora `termo-<chave>`;
`base_legal_motivo` para situação administrativa (V-R7).

**DS (pedidos — atendidos na rodada 2):** `FaseSelo` com `fase` nula +
desfecho e `id`; `TermoGlossario` com `abertoInicial`, `rotuloAcao`,
`indicador`; classe X "sem prazo fixo"; `nota` "Texto do ZIL, não oficial.";
API falsa com `responderPaginas`; `/como-vira-lei` busca no cliente (exceção a
S9 registrada pelo DS). Pendente de uma linha no kit: rótulos D/D\* "fixado
na regra…" (`E02`).

**PM:** TRM-040 depende de 035 e 037; L0 com 10 entradas; caminho do guia
para o revisor `linguagem`; `mapa_nao_aprovado` sem selo na interface (`N06`).

### Rodada 3 — revisões aplicadas

Aplicados neste arquivo os achados de `revisoes/ds-sobre-interface.md`
(DS-UI-01 a 29) e os itens desta parte em
`revisoes/arquitetura-sobre-interface-e-ds.md` (2, 3, 5, 7–11, 13, 17, 18).
Principais mudanças: tipos de API sempre os de `lib/tramitacao/tipos.ts`
(`GlossarioApi`, `RitoRefApi`, `MarcoApi`, `EventoApi`); `saibaMais` como
`{ rotulo, href }`; rito achado pela `chave` (MPV = `MPV_CN`, Casa
`congresso`); rótulo do `FaseSelo` no glossário vindo de `mapa.fases`;
situação achada por `situacao_glossario`, nunca por texto; "Órgão atual" pelo
órgão efetivo; apensada por `herdada_de.acompanhada`; `principal_url_camara`
pronto da API; publicação de TRM-015/016 condicionada ao sync em produção;
R9 nova nas fixtures; API falsa unificada (`responderPaginas`, `chamadas`);
`@reflow` e `focoVisivelENaoEncoberto` nos e2e; `LinhasDaSituacao` extraído
em TRM-015; matriz com "Dispensada", "Está aqui", "Desde {data}", "Quem
decide:", `G03`, `C04`, I14 `padrao` com "Tentar de novo", N04 cobrindo
situação nula sem histórico, C02 virando fonte; textos curtos das classes de
prazo decididos (`E02`); campos de `Proposicao` com tipos do contrato em
TRM-046-A; link do selo de `nao_sabemos` para `/metodologia#tramitacao`
(decisão registrada em §1.2).

**Não aplicados, e por quê:**
- DS-UI-29 (rótulo acessível do chip com unidade): mantido o padrão do kit
  para todo `Chip` com `n`; registrado como risco em TRM-043.
- DS-UI-27: sem ação na interface (pedido do DS ao PM sobre a redação de S2).
- Itens 1, 4, 6, 14–16, 19 e 20 da revisão da Arquitetura: são do backlog do
  DS.
- Item 13 (desarquivamento no Senado): aplicado em `desfecho_arquivada`, mas
  a frase entra com `pendente` até o revisor `juridico` conferir quórum e
  prazo do RISF art. 332 — o número veio do discovery, não do texto do
  regimento.

# Revisão UI/UX de TRM-047 (`/metodologia#tramitacao`, spec.md §9.3)

Data: 2026-11-01. Revisor: agente de UI/UX e design de interação, só leitura,
contra o texto de TRM-047 anterior a esta revisão (as linhas citadas são as da
versão revisada de `spec.md`). As correções 1–8 foram aplicadas a `spec.md`
§9.3 e a `backlog-design-system.md` no mesmo commit; a 9 e a linha fina são
perguntas à maintainer (§11.3, itens 14 e 15).

**Resumo.** A base está certa. A seção é texto corrido, declara a IA como pede
D9, diz que não há revisão de especialista independente (P4) e usa
`Aviso tom="padrao"` sem âmbar. Faltam quatro coisas, que viram itens ✗:

- a primeira frase não responde à pergunta de quem chega;
- o texto não usa os rótulos dos links que trazem a pessoa até aqui
  ("Fase não identificada", "Como chegamos a esta fase");
- o estado "mapa ainda não aprovado / lote parcial" (D11, N06) não aparece;
- o padrão de link externo contradiz a regra do próprio backlog.

## Tabela

| Item | | Achado |
|---|---|---|
| U1: primeira frase responde à pergunta | ✗ | A pessoa chega por "Como chegamos a esta fase" (backlog-interface.md:2652, C01) ou por "Fase não identificada, entenda por quê" (:2641, N00; backlog-design-system.md:1451). A primeira frase (spec.md:1364) fala da origem da situação oficial ("vem da API de Dados Abertos"), não de como a fase é derivada. |
| Título `h2` | ✗ | "Onde a proposição está" (spec.md:1362) não bate com o rótulo do link de entrada. Também se confunde com a seção "Onde está agora" da página da proposição (backlog-interface.md:305). |
| Hierarquia de títulos | ◐ | `h2` por seção e um `h1` só: coerente com page.tsx:122–317. O título do `Aviso` é `div` (Aviso.tsx:36), sem conflito. Porém o `h1` e a linha fina falam só do Score (page.tsx:122–124), e quem chega pela âncora cai numa página "Como o Score ZIL é calculado". |
| Sumário | ✗ | "o item no sumário da página **se houver**" (spec.md:1407). O sumário existe: `SECOES` + `Chips` (page.tsx:108–115, 126–132). A spec precisa mandar incluir o chip. |
| Âncora estável | ◐ | `id="tramitacao"` é único e `scroll-mt-20` (80 px) é maior que a NavBar fixa no topo, `min-h-16` (NavBar.tsx:43). Mas backlog-interface.md:267 manda `scroll-mt-24` + `aria-labelledby`, e a spec segue a página. Falta um teste que prove que os links `/metodologia#tramitacao` de `FaseSelo` e `ComoSabemos` têm alvo. |
| Textos exatos e coerência com a matriz §4 | ◐ | O texto está definido, mas: (a) "Fase não identificada", o nome do selo que leva até aqui, não aparece; (b) "Não damos palpite" (spec.md:1380) destoa de "Preferimos não adivinhar" (N01, backlog-interface.md:2642); (c) "ao lado da fase" (spec.md:1376) está errado: `ComoSabemos` fica **sob** a fase (backlog-design-system.md:1723); (d) "você vê isso" usa segunda pessoa, que o guia §2.1-8 proíbe. |
| Linguagem simples (guia §2.1) | ◐ | A frase de spec.md:1369–1372 tem cerca de 45 palavras; o limite é 25 (backlog-interface.md:411). Jargão: "API", "versionado", "issue", "maintainer". |
| Exatidão / não inventar | ◐ | (a) "Mostramos **sempre** a situação oficial" (spec.md:1365) é falso nos estados F02, F03 e F13, quando a Câmara não informou. (b) "Datas futuras só aparecem quando há reunião já marcada…" (spec.md:1384) descreve TRM-051 (P3, "Depois"). Hoje o site nunca mostra data futura (T01, backlog-interface.md:2648). (c) "quatro agentes" (spec.md:1397) é contagem fixa, contra o critério 3 (spec.md:1414). ⚠ "regimentos da Câmara e do Senado" omite o Regimento Comum (MPV, veto; §2.3). É o mesmo texto de V01, então só suspeita. |
| Estado mapa não aprovado / lote parcial (D11) | ✗ | Falta. A seção diz como a fase é calculada, mas não diz que o mapa vai ao ar por partes, nem que, enquanto isso, a proposição mostra só a situação oficial com "Fase em revisão" e sem selo (N06, backlog-interface.md:2647; D11, spec.md:1576). Com zero lotes aprovados, o texto descreveria algo que o site ainda não mostra. |
| Paleta (S4, U5) | ✓ | `Aviso tom="padrao"` (`bg-zil-superficie-1`, Aviso.tsx:12), sem `zil-neutro`. O parágrafo sobre cores está correto. |
| S7: parágrafo ≥ 18 px | ◐ | O corpo do `Aviso` tem 15 px (Aviso.tsx:37). A spec põe ali um parágrafo de cerca de 60 palavras (spec.md:1395–1400), contra o README do kit ("Nunca parágrafo abaixo de 18px"). A página já faz isso (page.tsx:269, 301), mas não é motivo para repetir. |
| Links externos | ✗ | A spec pede "↗" no texto + `aria-label` (spec.md:1402–1404, 1425–1426). A regra do backlog (backlog-interface.md:261) é texto visível + `sr-only` "(abre em nova aba)" + `Icone externo` com `aria-hidden`. Um `aria-label` que substitui o texto arrisca a 2.5.3, e o "↗" é lido pelo leitor de tela. Onde os links ficam não está dito: o `Aviso` tem um só slot `acao`. ⚠ O `Button` tem `whitespace-nowrap` (Button.tsx:53). "Ver o mapa e as revisões no GitHub ↗" no slot `acao` (cerca de 261 px de largura útil a 375 px, estimativa) deve estourar a 375 e a 320 px. |
| 375 / 768 / 1280 e reflow | ◐ | Não há especificação de layout para os links. O projeto `reflow-320` não aparece em Testes (spec.md:1428). |
| Critérios verificáveis por teste | ◐ | O critério 1 ("textos idênticos") não diz como provar. O critério 2 (spec.md:1413) pertence a TRM-033/040 e não dá para verificar no PR de TRM-047. Testes (spec.md:1428–1429) não incluem `jest-axe` no Vitest, `expectPaletaNeutra`, `focoVisivelENaoEncoberto` nem `semRolagemHorizontal @reflow` (helpers em backlog-design-system.md:686–689). |
| Dependências | ◐ | Falta TRM-046-A: o texto cita rótulos de `textos.ts` (onda 0, sem custo). backlog-design-system.md:1721 diz que TRM-033 "Desbloqueia… TRM-047", ao contrário de spec.md:1347, que não lista TRM-033 (o destino não depende do link). O mapa de IA (backlog-interface.md:322) prevê um link da seção para `/como-vira-lei`, que a spec não traz e que só pode existir depois de TRM-044. A variante `bloco` de `ComoSabemos`, anotada "(metodologia)" em backlog-design-system.md:1769, fica sem uso. |
| D9 e honestidade de processo (P4) | ✓ | A IA está declarada na metodologia, não em cada termo. "Não há revisão de especialista independente" está presente. |
| Consistência de gênero ("maintainer") | ◐ | A spec diz "a maintainer" (spec.md:1399), igual a GOVERNANCE.md:38. A mesma página diz "um único maintainer" (page.tsx:270). |

## Correções propostas (resumo; o texto completo foi aplicado em spec.md §9.3)

1. Título "Como chegamos à fase de uma proposição" e texto reescrito: abre
   pela fase como leitura do ZIL; cita "Fase não identificada" e "Preferimos
   não adivinhar"; acrescenta o parágrafo sobre o mapa ir ao ar por partes
   ("Fase em revisão"); tira a promessa de datas futuras; "logo abaixo da
   fase"; sem segunda pessoa.
2. Processo de revisão vira `h3` + parágrafo em `.zil-leitura`; o `Aviso`
   guarda só a ressalva "Ainda não há revisão de especialista independente".
3. Links: `Button fantasma s` em linha `flex-wrap`, texto visível +
   `sr-only` "(abre em nova aba)" + ícone `aria-hidden`; sem "↗" e sem
   `aria-label`; rótulos "Mapa e revisões no GitHub" e "Apontar um erro no
   GitHub"; `REPO_URL` de `@/lib/links`.
4. Escopo: o chip `{ id: "tramitacao", rotulo: "Fase da tramitação" }` em
   `SECOES`; fora, o link para `/como-vira-lei` (entra com TRM-044) e mudar o
   `h1`. Pergunta à maintainer sobre a linha fina.
5. Critérios de aceite 1–8 verificáveis (Vitest, fixture de texto, regex de
   contagem, V-E1–V-E9, links, varredura de âncoras, Playwright com axe,
   `expectPaletaNeutra`, `focoVisivelENaoEncoberto`, `semRolagemHorizontal
   @reflow`, gates com N/A justificados).
6. Specs de design: links no padrão de backlog-interface §0.5-6, sem estourar
   a 320 px; anatomia `h2` + `.zil-leitura` + `h3` + parágrafo + `Aviso` +
   links.
7. Testes: `tests/paginas/metodologia.test.tsx` e
   `tests/e2e/metodologia.spec.ts`.
8. Dependências: + TRM-046-A. Em backlog-design-system.md, o destino do link
   de `ComoSabemos` é TRM-047 (não bloqueia), e a variante `bloco` fica sem
   uso declarado.
9. Opcional (pergunta à maintainer): "uma única maintainer" em page.tsx:270.

⚠ Não verificado: o estouro do `Button` a 375/320 px é estimativa, sem medir
no navegador; falta conferir se o Regimento Comum precisa aparecer na frase
sobre os regimentos (afeta V01 também).

# Checklist de UI/UX (U1–U14)

Copiado de `specs/013-tramitacao/spec.md` §7.2, sem reescrever. A spec é a
fonte: mudança de item começa lá. Quem aplica este checklist é o agente
`revisor-ui-ux`.

Como marcar: cada item recebe ✓, ✗ ou N/A, com evidência. ✓ sem evidência conta
como ✗, e N/A exige motivo. O fluxo está em "Revisão de PR", no
[`CLAUDE.md`](../../CLAUDE.md), e o que prova cada item, em
[`como-verificar.md`](como-verificar.md).

| # | Item |
| --- | --- |
| U1 | A seção responde à sua pergunta na primeira frase (onde está / o que aconteceu / o que vem depois / o que significa) |
| U2 | Ordem da página conforme disc. §6.1: o resumo em linguagem simples vem antes da fase |
| U3 | Textos idênticos à matriz de TRM-046 ou ao glossário aprovado; nenhum texto de status gerado por LLM; a frase de "Onde está" sai de template |
| U4 | Estados cobertos e testados: carregando, erro de API, vazio, `nao_sabemos` (cada motivo usado), recém-apresentada, apensada, cada desfecho, `norma`, `mapa_nao_aprovado` |
| U5 | Nada do que disc. §6.5 proíbe: cor de alinhamento ou âmbar para fase (`expectPaletaNeutra`); "% concluída" ou barra até a regulamentação; "parada há N dias"; data prevista; "não regulamentada" como acusação; situação oficial truncada |
| U6 | Proveniência: fase com "Como sabemos"; "Ver na Câmara ↗" leva à `url_camara` certa e anuncia que abre em nova aba |
| U7 | Nenhum link para `/parlamentar` com `NEXT_PUBLIC_RANKING_PUBLICO=false` |
| U8 | 375 / 768 / 1280: `Etapas` vertical abaixo de `md`; nada essencial escondido no celular; alvo de toque ≥ 24 × 24 px (WCAG 2.2, 2.5.8). Sem rolagem horizontal da página **a 320 px** (reflow, 1.4.10): o teste `semRolagemHorizontal` de cada rota leva a marca `@reflow` e roda no projeto `reflow-320` |
| U9 | Teclado: tudo operável, ordem de foco lógica, foco visível e não encoberto pela navegação fixa (2.4.7, 2.4.11), provado com `focoVisivelENaoEncoberto` |
| U10 | Leitor de tela: um `h1`, um `h2` por seção; `aria-current="step"` na etapa atual; nome acessível em todo ícone que age; `<summary>` descritivo em cada `<details>` |
| U11 | Cor nunca é o único meio (1.4.1); contraste de texto ≥ 4,5:1 e de componente ≥ 3:1 (1.4.3, 1.4.11) nos dois temas |
| U12 | Nenhuma animação contínua; `prefers-reduced-motion` respeitado |
| U13 | Datas em dd/mm/aaaa; "Última movimentação em"; lei como "Lei 14.871/2024" |
| U14 | Linguagem neutra, sem cobrança; "Presidente da Câmara" e "Presidente da República" sempre por extenso |

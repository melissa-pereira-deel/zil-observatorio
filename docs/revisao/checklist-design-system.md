# Checklist de Design System (S1–S12)

Copiado de `specs/013-tramitacao/spec.md` §7.3, sem reescrever. A spec é a
fonte: mudança de item começa lá. Quem aplica este checklist é o agente
`revisor-design-system`.

Como marcar: cada item recebe ✓, ✗ ou N/A, com evidência. ✓ sem evidência conta
como ✗, e N/A exige motivo. O fluxo está em "Revisão de PR", no
[`CLAUDE.md`](../../CLAUDE.md), e o que prova cada item, em
[`como-verificar.md`](como-verificar.md).

| # | Item |
| --- | --- |
| S1 | Usa componentes do kit; padrão que aparece em dois lugares vira componente do kit, não cópia na página |
| S2 | Primitiva visual nova ou alterada: em `apps/web/components/ui/`, exportada em `index.ts`, documentada no README do kit (props, estados, exemplo, notas de a11y). Composição de domínio que recebe tipos da API (ex.: `OndeEsta`, `LinhasDaSituacao`): em `apps/web/components/<domínio>/` (aqui, `components/tramitacao/`), como `DirecaoBadge` e `CategoriaBadge` — sem primitiva visual nova dentro dela; padrão visual que aparecer em dois lugares sobe para o kit |
| S3 | Só tokens `zil-*`; nenhum hex ou rgb em classe; nenhum `style={}` inline, **exceto** para valor que vem do dado (posição de marcador, largura de barra), sempre com comentário dizendo por quê — a regra do README do kit, usada em `Segmentado`, `Score` e `Revelar`; token novo em `tailwind.config.js` e `globals.css`, nos temas `escuro` (padrão) e `claro` |
| S4 | Fase, desfecho, `nao_sabemos` e etapa sem matiz: só `texto`, `texto-2`, `superficie-1…4`, `inverso*`, `separador`, `foco`. **`zil-alinhado*`, `zil-contra*` e `zil-neutro*` ausentes** fora de contexto de alinhamento ou de "não validado" — `neutro` é o âmbar de "não validado", não um cinza (o revisor roda `git diff main -- apps/web \| grep -E "zil-(alinhado\|contra\|neutro)"`; os testes usam `classesDeAlinhamento` e `expectPaletaNeutra`). Exceção: `Aviso tom="contra"` só para erro de API que impede o conteúdo |
| S5 | Os seis princípios do README do kit: pílula no que se toca; preenchimento, não contorno; sem `border` como separador; um primário por área; espaço no lugar de linha; nenhuma animação que roda sozinha |
| S6 | Props em português e coerentes com o kit (`variante`, `tamanho`, `tom`); estados como os enums do contrato (`feita`, `atual`, `futura`, `pulada`, `interrompida`) |
| S7 | Tipografia pelos estilos nomeados; nenhum parágrafo abaixo de 18 px; números com `.zil-num` |
| S8 | Testes do componente: Vitest + Testing Library por estado; `jest-axe` sem violações por estado; Playwright com screenshot nos 3 breakpoints × 2 temas |
| S9 | Server Component por padrão; JS no cliente só onde há interação |
| S10 | Sem regressão: quem usa o componente alterado continua com testes verdes; páginas antigas migradas no mesmo PR ou com o caminho documentado |
| S11 | Toda variante e todo estado do componente aparecem na vitrine `/kit/<slug>` (TRM-001-B), que é o que a regressão visual captura |
| S12 | O texto real mais longo do banco para aquele campo (situação oficial, nome de órgão, rótulo) está num teste e aparece sem truncar nos 3 breakpoints |

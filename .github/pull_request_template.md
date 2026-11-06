<!--
Título: `TRM-0XX: <título>` para tarefa do backlog.
PR empilhado: comece o corpo com "depende de #N" e faça o retarget para o `main` logo depois do merge da base.
-->

## Tarefa

<!-- Link para a spec da tarefa. Sem spec, a issue, com "Closes #N". -->

## Critérios de aceite

<!-- Copie os critérios da spec como checklist. Item marcado traz a evidência na mesma linha. Item não cumprido fica desmarcado, com o motivo. -->

- [ ] Critério: evidência

## Evidências

<!-- Comandos rodados, com o resultado real. Lista dos testes novos, por nome. -->

<!--
Mudança de interface (spec §7.4), além do acima:
- CI verde: `test-backend`, `lint-backend`, `lint-frontend`, `build-frontend`; `test-frontend` (TRM-001-A) e `e2e-frontend` (TRM-001-B, inclusive `reflow-320`) assim que existirem; com `data/tramitacao/` tocado, `validar-tramitacao` (TRM-024).
- Screenshots de cada rota e estado tocados, em 375, 768 e 1280 px, nos temas escuro e claro, gerados pelo Playwright e publicados como artefato da CI. Tabela com os links; os de 375 px no tema padrão embutidos aqui.
- Relatório axe (artefato JSON) com 0 violações, regras `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`.
-->

## Revisões

<!-- Mantenha só as linhas que valem para este PR e aponte o comentário de cada revisor. Todo ✗ resolvido, ou com o motivo escrito pela maintainer. -->

- [ ] Interface: [UI/UX (U1–U14)](https://github.com/melissa-pereira-deel/zil-observatorio/blob/main/docs/revisao/checklist-ui-ux.md), agente `revisor-ui-ux`: comentário
- [ ] Interface: [Design System (S1–S12)](https://github.com/melissa-pereira-deel/zil-observatorio/blob/main/docs/revisao/checklist-design-system.md), agente `revisor-design-system`: comentário
- [ ] Backend: [Arquitetura (A1–A8)](https://github.com/melissa-pereira-deel/zil-observatorio/blob/main/docs/revisao/checklist-arquitetura.md), agente `revisor-arquitetura`: comentário
- [ ] `data/tramitacao/`: agentes revisores e maintainer (`specs/013-tramitacao/spec.md` §6)
- [ ] Merge pela maintainer

## Changelog

<!-- Entrada no `[Unreleased]` de `docs/CHANGELOG.md` para `feat`, `fix` e `data`. Nos outros casos, diga por que não há entrada. -->

## Fora do PR

<!-- O que ficou de fora e o que você notou fora do escopo. -->

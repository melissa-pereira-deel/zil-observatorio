# Revisão de Arquitetura: backlog-dados.md, TRM-017 e TRM-023

Data: 2026-11-01. Revisor: agente de Arquitetura independente (não é o dono
de `backlog-dados.md`), só leitura, contra o texto anterior a esta revisão
(as linhas citadas são as dessa versão). As correções 1–19 foram aplicadas a
`backlog-dados.md` e `spec.md` no mesmo commit; o que não foi aplicado está
em `spec.md` §11.2 ("Pendentes de verificação").

Verificações que o revisor rodou em arquivos temporários:

- **Migrations em SQLite:** `alembic upgrade head`, depois downgrade e
  upgrade de novo, funcionam.
- **Modelo contra migrations:** `compare_metadata` entre o modelo atual e as
  migrations não mostra diferença. O critério 2 de TRM-011 parte de base
  limpa.
- **`fileConfig` do Alembic:** quebra um teste existente (ver TRM-011).

## Tabela

| Tarefa | Veredito | Achados |
|---|---|---|
| TRM-002 | ◐ | (a) O escopo diz "16 casos" (`backlog-dados.md:1533`), mas a tabela tem 18 casos mais `janela-d7`. (b) `RequisicaoNaoGravada(AssertionError)` (:1596) passa pelo cliente, mas os chamadores engolem a exceção com `except Exception`: `apps/workers/crawlers/camara.py:181`, `apps/workers/explicacao/coleta.py:135-169`, `scripts/discover_proposicoes.py:178`. Uma requisição não gravada vira log, e o teste passa. |
| TRM-011 | ◐ | (a) A frase "`env.py` chama `fileConfig`: inofensivo nos testes" (:1775) é **falsa**. `fileConfig` desliga os loggers que já existem. Rodar `fileConfig(alembic.ini)` antes de `tests/unit/test_bussula.py` faz `TestDadoReal::test_arquivo_ausente_devolve_vazio` falhar, porque usa `caplog` sobre o logger de `routers/bussula.py:11`. Na suíte real, `tests/integration/` roda antes de `tests/unit/`. (b) Risco de produção: o `dados.yml` do #47 não roda `alembic upgrade`. Quem migra é o `apps/api/entrypoint.sh`, quando o Render sobe a API. Se o deploy atrasar ou falhar, o cron das 04:15 roda o modelo novo contra o schema velho, e caem todos os passos que leem `Proposicao`. |
| TRM-010 | ✗ | Depende do cliente estrito de TRM-012, que vem na onda seguinte. Usa `client.obter_proposicao_estrito` (:1853) e `FonteIndisponivel` no critério 3 (:1817), e os dois só nascem em TRM-012 (:2092, :2111). O cliente legado (`packages/camara_client/__init__.py:104-126`) devolve `[]` em silêncio quando esgota as tentativas em 429/503/504, e levanta `HTTPStatusError` nos outros erros. Com ele, o critério 3 não é implementável. A spec §4 punha 010 na onda 1 e 012 na onda 2. |
| TRM-013 | ◐ | (a) `aplicar_norma` morava em `sincronizacao.py`, arquivo de TRM-012 (:2009), e o critério 5 era testado em `test_sync_tramitacao.py`, também de TRM-012 (:2017). Mas 012 depende de 013, e a spec §5.4 (:307) dava a ordem "012 → 013": dependência circular. (b) `norma_verificada_em = agora` (:2012) muda a cada execução. Se entrar em `alterados`, quebra o critério 4 de TRM-012 (`atualizados == 0` na segunda execução). |
| TRM-012 | ◐ | (a) A linha :2109 mudaria o `_get` legado em silêncio: 500/502 passariam a ser retentados e, ao esgotar, virariam `[]`. Hoje 500 levanta exceção na hora. (b) "Commit por proposição" e "em dry_run, `db.rollback()` no fim" se contradizem (:2162): o commit grava no dry-run. (c) No cron (:2198), o `rodar_passo` do #47 só conhece `Contagem(processados, criados, atualizados, erros)` e marca `partial` só se `erros > 0`; perdem-se o `failed`, o `erro_detalhes` e o `partial` por orçamento sem erro. (d) É M que na verdade é G: o cliente sozinho já toca o arquivo quente, e é dele que 010 precisa. |
| TRM-014 | ◐ | (a) O critério 9 usa um pacote "registrado" via `registrar_proposicao`, mas 010 não estava nas dependências (:2228). (b) "Um `logger.warning` por processo" (:2257) não acontece com `lru_cache`, que não guarda exceção. Fora isso, o contrato bate com o que backlog-interface consome (`situacao_estado`, `X-Total-Count`, `per_page`/`pages` = `PaginatedResponse` em `apps/api/schemas/__init__.py:171`). |
| TRM-020 | ✓ | Pronta. O problema de cobertura com o snapshot de tipos de órgão é de TRM-024. |
| TRM-021a | ◐ | Ninguém fixava o esquema de `consolidado.yml` e `decisao.yml`. As regras V-R4 a V-R6 de TRM-024 dependem de nomes de campo que ninguém definiu. Decisão escondida entre 023 e 024. |
| TRM-021b | ✓ | Pronta. O conteúdo depende de conferência na fonte, e o processo já cobre isso com `pendente`. |
| TRM-024 | ◐ | (a) V-C1 (:2704) valia para "um snapshot", o que inclui `camara-tipos-orgao.json` (55 itens), que não são regra, marco nem `nao_mapeados`: o teste de cobertura falharia. (b) O critério 7 (:2688) e o §2.1-9 (:652) proibiam `com_tudo_publicavel` fora de três lugares, mas o pipeline de TRM-023 precisa dele para mostrar "fase derivada" de entradas ainda não aprovadas. |
| TRM-025a/b | ◐ | A ordem entre `exigir(*ids)` (:2862) e as saídas `nao_sabemos` internas das regras não estava definida (R4 com cabeça `nao_sabemos`, R5 e R7 com `casa_iniciadora` nula, R7 com órgão nulo indo para R10). No `pl-5-2025`, por exemplo, sairia `mapa_nao_aprovado` ou `principal_nao_resolvida` conforme a ordem. |
| TRM-026 | ◐ | (a) `back_populates="proposicao"` (:2975), mas a `Tramitacao` do §1.4 não declarava `proposicao = relationship(...)`: o mapper falha. (b) A tabela `orgaos` é "mesma migration" no §1.3 (:252), mas a spec técnica de 026 não a citava; e `upsert_eventos_camara` (:2992) não recebia `client` nem `cache`. (c) Em dev, o lifespan faz `create_all` com `ENV=development` (`apps/api/main.py:16-17`): se a API subir antes do `alembic upgrade`, o `create_table` da migration falha. (d) Não dizia se linhas com `removido_na_fonte_em` entram em `entrada_do_banco`. (e) ⚠ "grava 51 linhas" (:2958) não conferido. |
| TRM-027 | ◐ | (a) O gatilho comparava com a "maior `fase_versao_publicada`" (:3063): uma linha que falhou numa versão antiga nunca seria recalculada. (b) `orgao_efetivo_*` aparecia no critério 4 (:3056) como gravado por 027, mas quem grava é TRM-012: dois escritores da mesma coluna; o §1.2 (:122) também punha `orgao_efetivo` em `fases.py`. (c) É M que na verdade é G. |
| TRM-028 | ◐ | (a) `REPO_URL` padrão `…/manifesto-zil` (:3262) estava **errado**: o remoto é `melissa-pereira-deel/zil-observatorio` (`apps/web/lib/links.ts:12`). (b) Faltava 014 nas dependências (:3172). (c) É M que na verdade é G. |
| TRM-050 | ✓ | Pronta. |
| TRM-051 | ✓ | Pronta. |
| TRM-052 | ✓ | O snapshot novo `camara-comissoes.json` precisa ficar fora do V-C1 (mesma correção de 024). |
| TRM-053 | ◐ | "Colunas antigas removidas numa migration seguinte" (:3388) é perda de dados se o downgrade não recriar as colunas `norma_*` a partir de `normas`. |
| TRM-017 (spec §9.2) | ◐ | (a) O critério 7 lia `tipo = "tramitacao"`, mas TRM-012 grava `tramitacao_diaria`, `_completa` e `_manual`. (b) "Reusa `packages.camara_client`": no `--verificar-api`, o `obter_proposicao` legado devolve `[]` quando a fonte falha, e isso viraria divergência falsa. (c) M5 e "situações sem mapa" duplicavam o relatório de TRM-027. (d) M13 não definia "movimentadas". (e) O `dados.yml` não tem `upload-artifact`, e sair com código 1 deixaria o job `cadastros` vermelho. |
| TRM-023 (spec §6) | ◐ | Implementável e auditável: hash, estado só por script, recusa sem TTY ou com `CI`, V-R3 a V-R5; `carregar_agente`, `consultar`, `blindar` e `MetaExecucao` existem em `apps/workers/agentes/`. Ajustes: (a) `montar_lote(..., revisao: Revisao)`: o tipo certo é `ArquivoRevisao`. (b) Esquema de `consolidado.yml`/`decisao.yml` não fixado. (c) "Como aparece no site" precisa de `frase.py`/`rotulos.py`, que só nascem em TRM-028. (d) Conflito com `com_tudo_publicavel`. (e) `revisado_por` usa "hash8", mas `Agente.hash_instrucoes` tem 16 hex: dizer que são os 8 primeiros. (f) É M que na verdade é G. |

## Correções recomendadas (todas aplicadas, salvo nota)

1. TRM-012 em (a) cliente estrito e (b) sync; TRM-010 depende de 012a;
   `obter_orgao` criado em 012a; spec §4 com a linha 012a; §5.4
   `002 → 012a`.
2. `_get` legado preserva o comportamento: só 429/503/504 esgotados viram
   `[]`; 500/404 continuam levantando `httpx.HTTPStatusError` (teste no
   critério 10).
3. Dry-run sem `commit`: só `flush` e `rollback` no fim, com teste de contagem.
4. `_tramitacao` no cron devolve `Contagem` com `erros` ≥ 1 em `partial` e
   levanta `RuntimeError` em `failed`.
5. `aplicar_norma` em `registro.py` (arquivo de TRM-010), teste em
   `test_aplicar_norma.py`, `norma_verificada_em` não conta como alteração;
   §5.4 sem "012 → 013".
6. TRM-011: `Config()` sem arquivo no teste de migration; risco de produção
   do `dados.yml` sem `alembic upgrade`.
7. TRM-002: "18 casos + `janela-d7`"; `nao_gravadas` conferido no teardown.
8. V-C1 restrito aos três snapshots de situação e tramitação.
9. `com_tudo_publicavel` permitido também em `apps/workers/revisao_tramitacao/`
   (sem banco; teste de AST).
10. Modelos `Consolidado` e `Decisao` em `packages/tramitacao/revisao.py`;
    `montar_lote(..., revisao: ArquivoRevisao)`.
11. TRM-023: pré-visualização da frase antes de TRM-028; estimativa G em dois
    PRs.
12. TRM-025: `exigir` roda antes de qualquer saída interna da regra.
13. TRM-026: `relationship` em `Tramitacao`; `orgaos` na mesma migration;
    `upsert_eventos_camara` com `client` e `cache`; linhas removidas fora de
    `entrada_do_banco`; `alembic upgrade` antes da API em dev; "grava
    `len(pacote)` linhas".
14. TRM-027: gatilho por qualquer linha com versão diferente; órgão efetivo
    só lido (gravado por 012b); `orgao_efetivo` em `status.py`; estimativa G
    em dois PRs.
15. TRM-028: `REPO_URL` correto; depende de 014; estimativa G em dois PRs.
16. TRM-014: depende de 010; um `warning` por falha de carga.
17. TRM-053: `downgrade()` recria `norma_*` a partir de `normas`, com teste.
18. TRM-017: `tramitacao_diaria`; cliente estrito; M5/M6 de TRM-027; M13
    definido; passo próprio no `dados.yml` com `continue-on-error` e
    `upload-artifact`.
19. `origem_registro` ganha `sync`.

O item (e) de TRM-023 foi aplicado no comentário de `revisado_por`
(backlog-dados §2.8): são os 8 primeiros hex de `Agente.hash_instrucoes`.

⚠ Não confirmado pelo revisor (precisa de rede): os códigos `"13000"` e
`"81002"` em `TIPOS_ORGAO_COMISSAO`; o formato JSON de
`/processo/tipos-situacao` do Senado sem `Accept`; e se paginar cerca de 23
páginas de uma janela que muda durante a leitura dispara `ListagemIncompleta`
com frequência (sugestão: deduplicar por id e tolerar ±1% antes de levantar,
só com teste no pacote `janela-d7`).

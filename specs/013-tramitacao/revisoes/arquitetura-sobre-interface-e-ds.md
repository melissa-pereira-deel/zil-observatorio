# Revisão de Arquitetura — contratos e viabilidade técnica de `backlog-interface.md` e `backlog-design-system.md`

**Revisor:** Software Architecture · **Data:** 2026-10-30 · **Escopo:** TRM-001, 015, 016, 030–046 (e
037/038 do DS), conferidos contra `backlog-dados.md` §1.5 e §7 (versão desta data, rodada 2).
**Não editei** os dois arquivos revisados; as correções abaixo são para os donos aplicarem.

## Como conferi

- Cada campo consumido nos tipos de `lib/tramitacao/tipos.ts` (DS, TRM-031-A), na seção 0.1 da UI/UX e
  nas linhas da matriz (§4 da UI/UX) foi comparado, nome e tipo, com os schemas Pydantic de
  `backlog-dados.md` §1.5.
- Dependências: cada linha "Depende de" contra o que o dado realmente precisa (código × publicação).
- CI: versões fixadas por TRM-001 conferidas no registro do npm (todas existem; `engines` abaixo);
  versões do Node em `nodejs.org/dist/index.json`; forma de buscar dados das páginas atuais
  (`apps/web/app/**/page.tsx`: todas com `"use client"` + `fetch`, nenhuma busca no servidor — o
  `page.route()` intercepta tudo).
- Dados: os 240 detalhes de `GET /proposicoes/{id}` das acompanhadas (30/10) e o texto compilado do
  RICD, para os achados A18–A22 de `backlog-dados.md` §0.1.

## Achados

Gravidade: **Alta** = quebra a CI ou publica informação errada; **Média** = campo ausente, nome ou
tipo divergente, ou regra frágil; **Baixa** = ajuste de clareza ou robustez.

| # | Arquivo | ID | Problema | Gravidade | Correção exata |
| --- | --- | --- | --- | --- | --- |
| 1 | backlog-design-system.md | TRM-001 (helper `api.ts`, item 14) | A página roda em `http://localhost:3100` e busca em `http://api.zil.test`: requisição **cross-origin**. O Chromium aplica CORS também à resposta servida por `route.fulfill`; sem `Access-Control-Allow-Origin` o `fetch` falha e todo e2e de página cai no estado de erro. `X-Total-Count` (novo, TRM-014) também não é legível sem `Access-Control-Expose-Headers`. | Alta | Em `instalarApiFalsa`, todo `route.fulfill` (inclusive o 599) leva `headers: { "access-control-allow-origin": "*", "access-control-expose-headers": "X-Total-Count", "content-type": "application/json; charset=utf-8" }`; `OPTIONS` responde 204 com os mesmos cabeçalhos mais `access-control-allow-methods: GET` e `access-control-allow-headers: *`. Acrescentar ao critério de 001-B: "uma página real lê uma fixture servida pela API falsa" (`paginas/proposicoes.spec.ts` já serve, desde que confira o conteúdo, não só a ausência de erro). |
| 2 | backlog-interface.md | TRM-015 (§0.1, linha F10 da matriz) | "Órgão atual" usa `sigla_orgao`/`orgao_nome`, que são o órgão do **último registro**: em 23 das 240 acompanhadas é CCP (18) ou MESA (5) — a página diria "Órgão atual: Mesa Diretora da Câmara dos Deputados" para proposição que está numa comissão (A19). | Alta | F10 usa `orgao_efetivo_nome` e `orgao_efetivo_sigla` (novos em `ProposicaoRead`, TRM-011/012/014): "{orgao_efetivo_nome} ({orgao_efetivo_sigla})", só a sigla se faltar o nome, linha omitida se os dois forem nulos. `sigla_orgao` (do status) não aparece na tela. Em F1, `onde_esta.sigla_orgao/orgao_nome` já são o efetivo. Fixture 01–03 com os dois campos. |
| 3 | backlog-interface.md | TRM-040 (linha 1288) e matriz | A definição da situação é achada por `glossario.find(e => e.termo === onde_esta.situacao_oficial)`. `termo` é texto editorial; o oficial tem variações (espaço sobrando, caixa) e há códigos com o mesmo nome (905 e 1382). Casamento por texto falha em silêncio. | Média | Usar `onde_esta.situacao_glossario` (F1) ou `proposicao.situacao_glossario` (F0), chave pronta da API: `definicaoDoTermo(mapa.glossario, situacao_glossario)`; nulo → sem definição. |
| 4 | backlog-design-system.md | TRM-035 (`entradaDaSituacao`) | Mesmo problema do #3 no adaptador: `entradaDaSituacao(glossario, situacao)` casa por `termo`. | Média | Trocar a assinatura por `entradaDaSituacao(glossario: GlossarioApi[], chave: string \| null): GlossarioApi \| null` (busca por `chave`), ou remover e usar `definicaoDoTermo`. Teste com chave inexistente → `null`. |
| 5 | backlog-interface.md | TRM-040 (A01/A02) e fixture 06 | A02 assume `herdada_de.id` nulo quando a principal não é acompanhada. Pela D2, a cabeça de contexto **é registrada** (tem `id`, não aparece na lista): `id` vem preenchido e o caso 06 nunca aconteceria. | Média | Condição de A01: `herdada_de.acompanhada`; de A02: `!herdada_de.acompanhada` (campo novo em `HerdadaDeRead`). Fixture 06 com `id` preenchido e `acompanhada: false`. |
| 6 | backlog-design-system.md | TRM-031-A (`tipos.ts`) | Divergências com o contrato da rodada 2: `DesfechoDefApi.reversivel` não existe mais (o desarquivamento a pedido foi revogado na Câmara, RICD art. 105 § 1º, A21); faltam `HerdadaDeApi.acompanhada`, `OndeEstaApi.situacao_glossario` e `MapaApi.situacoes_camara`. | Média | Remover `reversivel`. Acrescentar `acompanhada: boolean` em `HerdadaDeApi`; `situacao_glossario: string \| null` em `OndeEstaApi`; `situacoes_camara: { codigo: string; descricao: string; glossario: string \| null; tratada: boolean }[]` em `MapaApi`. Em `lib/api.ts` (`Proposicao`, campos opcionais): `orgao_efetivo_sigla`, `orgao_efetivo_nome`, `principal_url_camara`, `situacao_glossario`. |
| 7 | backlog-interface.md | TRM-045 (linha 2069) | `mapa.situacoes_camara: { codigo: number; … }`. Em todo o contrato o código de situação é string (`cod_situacao: "915"`). | Baixa | `codigo: string`; mais os campos `glossario` e `tratada` (item 6). "Quantas faltam" = situações cuja `glossario` é nula ou aponta para entrada não publicável. |
| 8 | backlog-interface.md | TRM-015 (F11) | O link "Ver a proposição principal na Câmara" é montado no frontend com o padrão de URL da Câmara — derivação que a spec proíbe (§0.3, "nenhuma condição calculada no frontend") e que duplica o padrão. | Baixa | Usar `principal_url_camara` (novo em `ProposicaoRead`). |
| 9 | backlog-interface.md | TRM-015/016 (publicação) | A dependência lista TRM-013/014, mas não exige que o sync tenha rodado em produção. Sem `scripts/sync_tramitacao.py completo` no banco de produção, as 240 saem `situacao_estado: nao_sincronizada` (F13) — a página v0 iria ao ar sem resolver o erro que justifica F0 (D10). | Média | Acrescentar em "Depende de" de TRM-015 e TRM-016: "**Publicação:** TRM-012 executado em produção (`completo`), com as 5 do placar conferidas (critério 8 de TRM-012)". |
| 10 | backlog-interface.md | TRM-046 (fixture 13 e linhas N/F de situação nula) | A R9 mudou (A20): situação nula **com histórico** agora vira a fase do último marco (ex.: "Distribuição" → `comissoes`, regra R9), não `nao_sabemos`. Só cai em `nao_sabemos(fonte_indisponivel)` a nula antiga **sem** marco de fase. | Média | Fixture 13 em duas variantes F1: `…-nula-com-distribuicao` (`fase: "comissoes"`, `fase_motivo: null`, `como_sabemos.regra: "R9"`) e `…-nula-sem-historico` (`nao_sabemos`, `fonte_indisponivel`). F0 não muda (`situacao_estado: sem_situacao`). |
| 11 | backlog-interface.md | TRM-016 | `listarTodasProposicoes` para quando uma página vem com menos de 100 itens; não sabe o total. | Baixa | `GET /proposicoes` agora devolve `X-Total-Count` (TRM-014, critério 10). Parar quando `itens lidos ≥ total` (mantendo o teto de 20 páginas) e usar o total no contador "N proposições". Depende do item 1 (CORS expõe o cabeçalho). |
| 12 | backlog-interface.md | §0.1 e §2.7 | Pedidos 1–4 à Arquitetura | — | **Atendidos** em `backlog-dados.md`: regra urgência + conclusiva → `apreciacao_conclusiva_com_urgencia` (9 casos confirmados nos 240 detalhes, A18; nunca o texto da conclusiva pura); `mapa.situacoes_camara`; `datetime` com `-03:00`; âncora `termo-<chave>`; `base_legal_motivo` para situação administrativa (V-R7 ampliada); `regime` "." e `apreciacao` "Indefinida" saem nulos na API. |
| 13 | backlog-interface.md | TRM-022 (desfechos) | O ajuste de "pode ser desarquivada" e do art. 137 está certo — conferi no texto compilado do RICD: art. 105 § 1º (antigo parágrafo único) revogado pela RCD 33/2022; art. 137 §§ 1º e 2º (devolução e recurso em 5 sessões); art. 24, II, h (urgência tira da conclusiva). | — | Nada a corrigir. `backlog-dados.md` tirou o campo `reversivel` e o `pendente` da devolução. No Senado o desarquivamento existe (RISF art. 332): o texto de `desfecho_arquivada` precisa dizer de qual Casa fala. |
| 14 | backlog-design-system.md | TRM-031 (exemplo de uso, linha ~1350) | `href={`/como-vira-lei#fase-${onde.fase}`}` gera `#fase-null` (desfecho sem "onde parou") e `#fase-nao_sabemos`. | Baixa | Seguir a regra da UI/UX (interface §1.4): fase → `#fase-<fase>`; desfecho → `#desfechos`; `nao_sabemos` → sem `href`. Corrigir o exemplo para não ser copiado. |
| 15 | backlog-design-system.md | TRM-001 (Node 22, conflito 12) | Pedido de aprovação. | — | **Aprovado.** Node 20 está fora de suporte desde 30/04/2026; `vitest@5.0.5` (`^22.12 \|\| ^24`), `jsdom@30.1.3` (`^22.22.2 \|\| ^24.15`), `@axe-core/playwright@4.14.0` (`>=22.12`) e `@testing-library/jest-dom@7.0.1` (`>=22`) exigem. O `node-version: "22"` resolve hoje para 22.23.4 (20/10/2026), que atende o `jsdom`. Todas as versões fixadas existem no npm com as datas citadas; `jest-dom@7.0.1` exporta `./vitest`. |
| 16 | backlog-design-system.md | TRM-001 (Vercel) | Sem mudar `engines` (vetado na spec), a Vercel usa a versão de Node configurada no projeto; se ainda for 20.x, o `npm ci` do build avisa (ou falha, com `engine-strict`) pelos `engines` das libs novas. | Baixa | Passo manual no checklist do PR de 001-A: conferir/ajustar "Node.js Version = 22.x" nas configurações do projeto na Vercel antes do merge. |
| 17 | backlog-design-system.md e backlog-interface.md | TRM-001, TRM-046-B (conflito 10 do DS) | Fixtures escritas à mão derivam do contrato sem ninguém perceber. | — | **Resolvido do lado de dados:** TRM-028, critério 9 — `scripts/gerar_fixtures_frontend.py` grava respostas reais da FastAPI (pacotes golden de TRM-002) em `apps/web/tests/fixtures/api/tramitacao/gerado/`, com IDs `uuid5` estáveis; um teste de backend falha se os arquivos versionados divergirem, e valida as fixtures sintéticas da UI/UX contra os schemas Pydantic. A UI/UX troca as fixtures "reais" pelas geradas quando TRM-028 entrar. |
| 18 | backlog-interface.md | §0.4 | "Fixtures de interface … em `tests/fixtures/api/tramitacao/`" — caminho relativo ambíguo; na raiz existe `tests/fixtures/tramitacao/` (Python, pacotes golden de TRM-002). | Baixa | Escrever sempre `apps/web/tests/fixtures/api/tramitacao/`. |
| 19 | backlog-design-system.md | TRM-032 (`marcoDaApi`) | Conferido: a API manda `marcos[]` em ordem crescente de sequência (último = mais recente) e `eventos` do mais recente para o mais antigo — bate com "atual = último do array" e com `registroDoEvento`. | — | Nada a corrigir; manter o teste que fixa essa ordem. |
| 20 | backlog-design-system.md | TRM-033 (`dataBR`, conflito 17) | Pedido de `datetime` em `-03:00`. | — | **Atendido** (`backlog-dados.md` §1.5, "Datas e horas"). `date` continua `"AAAA-MM-DD"`; `dataBR` pode fatiar os 10 primeiros caracteres de qualquer um dos dois. |

## O que está alinhado (sem ação)

- Nomes de `onde_esta`, `etapas[]` (inclusive `nota` e `fase`), `marcos[]`, `rito`, `como_sabemos`
  (`regra_descricao`, `versao_publicada` inteiro, `fontes[{rotulo, url}]`), `EventosPagina`
  (`items/page/per_page/pages`), e toda a forma de `/tramitacao/mapa` (etapa com `o_que_acontece`,
  `quem_decide`, `prazo{classe,texto}`, `condicao`; desfecho `{desfecho, rotulo, texto, base_legal,
  a_partir_de \| "qualquer"}`; `publicavel`/`revisao`) estão iguais nos dois arquivos e no contrato.
- `fase_rotulo` nunca nulo, `fase` nula só com desfecho, `recem_apresentada` como fase `apresentada`,
  "Fase não identificada" igual na API e na matriz (com teste em TRM-028).
- Mock por `page.route()` é viável: nenhuma página atual busca dado no servidor.
- Dependências de TRM-040–045 em TRM-028 e nos lotes de TRM-029 (publicação incremental) estão
  corretas; TRM-044 tem o que precisa para contar por etapa no cliente (`fase`, `desfecho`,
  `casa_iniciadora`, `tipo`; cada fase aparece uma vez por rito, garantido pelo validador V-E6).

## Mudanças que fiz em `backlog-dados.md` nesta rodada (para os dois donos saberem)

`apreciacao_conclusiva_com_urgencia` e a tabela de regimes ampliada (A18, A22); `regime`/`apreciacao`
nulos para "." e "Indefinida"; `datetime` com `-03:00`; `X-Total-Count` + CORS; `situacoes_camara` no
mapa; âncora `termo-<chave>`; V-R7 ampliada; `arquivada` sem "pode ser desarquivada" e `devolvida`
com o art. 137 conferido (A21); **órgão efetivo** já em F0 (`orgao_efetivo_sigla/nome`, A19) e na R7;
**R9 lê o histórico** quando a situação é nula (A20); `situacao_glossario`, `principal_url_camara`,
`herdada_de.acompanhada`; gerador de fixtures do frontend (TRM-028). Sem o órgão efetivo e a R9 nova,
a projeção de `nao_sabemos` nas 240 seria de ≈ 17% (23 + 17 casos), acima da meta de 5% (M5).

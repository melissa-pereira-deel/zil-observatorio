# Changelog

All notable changes to this project are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions map to git tags (not yet created — pending deploy pipeline).

---

## [Unreleased]

### Fixed
- **O peso sugerido pelo dossiê estava subestimado nas duas votações mais
  salientes da legislatura.** `_peso_sugerido` em `scripts/dossie.py` testava
  `"comissão"` **antes** de `"substitutivo"`, e inferia o local da votação pela
  palavra na descrição. Só que "Aprovado o Substitutivo ao PL 4.133 … adotado
  pelo relator da **Comissão** de Ciência" é votação de **plenário** — contém
  "Comissão" porque o substitutivo *veio* de uma. Resultado: o PL 4133/2023
  (439 votos) e o PL 2583/2020 (416 votos) recebiam `2.0, "votação em comissão"`
  em vez de 3.0.
  - A função passa a receber `total_votos` e distinguir plenário de comissão por
    **evidência**, não pela palavra: uma comissão tem dezenas de membros, o
    plenário tem 513.
  - A precedência foi corrigida para a mesma que o `candidatas.py` já
    documentava — e as listas `_VOTO_DO_TEXTO` e `_VOTO_DE_EMENDA` passam a ser
    **importadas** dele, em vez de duplicadas. A duplicação era a causa: o
    `candidatas.py` corrigiu a ordem e a cópia local não acompanhou, exatamente
    o risco que o comentário dele enuncia sobre as keywords da taxonomia.
- **Destaque e emenda deixam de receber sugestão de peso.** Caíam no default
  `1.0, "não foi possível inferir"`, que é o peso de uma votação normal — então
  o dossiê convidava a classificar com peso cheio uma votação que a regra do
  projeto considera inclassificável. Agora a sugestão é `None`, com o motivo
  explícito: vota-se o destaque, cujo texto a API não devolve, e sem ele "sim"
  não tem direção. Na varredura de 2023–2026, **11 das 15 candidatas** com
  dossiê caíam nesse caso.
- **O YAML que o dossiê manda colar em `data/direcoes/` não parseava.** Ementas
  com `NOVA EMENTA:` depois de uma quebra de linha — a PONTE (PL 327/2021) é uma
  — injetavam a quebra crua no bloco escalar, e o `yaml.safe_load` falhava com
  "mapping values are not allowed here". A ementa passa a entrar numa linha só,
  e um teste carrega o bloco emitido com `yaml.safe_load` para que a regressão
  não volte em silêncio.
- **O domínio do projeto é `zilobservatorio.com.br`.** O código apontava para
  `zilobservatorio.org`, que **nunca foi registrado** — sem NS, não resolve — e
  ainda assim aparecia em quatro lugares funcionais: o canal de denúncia do
  `CODE_OF_CONDUCT.md`, para onde relatos não chegavam; o `User-Agent` enviado
  ao Planalto, cujo `+url` é justamente o contato de quem está rastreando; o
  padrão de `CORS_ORIGINS` em `core/config.py`; e um link devolvido por
  `GET /` em `main.py`. Mais `.env.example` e `docs/DEPLOY.md`.
  O domínio registrado é o `.com.br`, e ele alinha marca e endereço: o projeto
  se chama ZIL Observatório em todo lugar. `zilmanifesto.org` e
  `zilmanifesto.com.br`, também do projeto, encaminham para ele.
  As menções em `GOVERNANCE.md` e `constitution.md` **não** mudam: descrevem a
  identidade `ZIL Observatório <zil@zilobservatorio.org>` que consta como
  autora de commits no histórico git — fato do repositório, ainda que o
  endereço nunca tenha sido entregável.
- `docs/DEPLOY.md`: Parte 4 reescrita para a GoDaddy — registro `A` na raiz
  (o DNS não permite CNAME no apex), aviso para apagar os registros de
  estacionamento antes de criar os novos, encaminhamento dos outros dois
  domínios, e verificação de MX, porque nenhum dos três recebe e-mail hoje.

### Added
- **Fase 1 do painel de curadoria multi-perspectiva** — a calibração que decide
  se as Fases 2–4 acontecem ([PRD-PAINEL §12](PRD-PAINEL.md)). O painel **não
  entra em produção**: não há superfície pública, não há geração de PR, e nada
  aqui toca `data/direcoes/` ou o Score.
  - `data/painel/agentes/*.yml`: os cinco agentes (jurista, economista,
    industrial, políticas públicas, contraditor) com viés declarado, insumos
    próprios e modelo pinado. Ficam em `data/` sob a mesma governança dos dados
    editoriais porque quem escreve as instruções controla o resultado — o diff
    é o controle (risco R2).
  - `apps/workers/panel/`: orquestração das etapas 2 a 4. Três regras
    invioláveis passam a ser propriedade do código, não disciplina: a
    independência da etapa 2 é garantida pela **assinatura** de
    `montar_prompt_analise`, que não recebe os pareceres dos demais (risco R6);
    a carga **recusa** um agente de análise que declare `pareceres_dos_outros`
    como insumo; e o módulo não importa scoring, models ou SQLAlchemy, nem
    escreve em disco — verificado na árvore sintática pelos testes.
  - **Consenso sem desempate** (`consenso.py`): 4 de 5 na mesma direção vira
    proposta; menos que isso é pauta contestada, sem exceção. Objeção que o
    contraditor declare *decisiva* derruba o consenso mesmo com a aritmética a
    favor. Acrescentado um terceiro resultado que o PRD não previa —
    `sem_materia` —, porque tratar abstenção unânime como dissenso quebraria a
    própria métrica 5 da Fase 1: uma votação procedimental, em que todos se
    abstêm corretamente, entraria na conta como pauta contestada.
  - **Texto de fonte como dado não confiável** (regra 6): ementas e textos do
    Planalto entram cercados por delimitadores, e qualquer sequência parecida
    com um delimitador é removida do texto antes — sem isso, uma ementa que
    contenha a marca de fechamento escapa do bloco e o resto dela é lido como
    instrução.
  - `data/painel/casos/construidos.yml`: 10 casos com resposta conhecida **por
    construção** — procedimental → abstenção, frontalmente contrário → direção
    contrária, ambíguo → contestada. Dois são deliberadamente capciosos: "Dia
    Nacional do Engenheiro Industrial" casa com keywords da taxonomia e não
    constrói indústria nenhuma.
  - `data/painel/casos/injection.yml`: 8 ataques, incluindo fuga de
    delimitador, exfiltração de instruções e um que induz a direção `nao` —
    porque manipular para rebaixar o score de um parlamentar é tão plausível
    quanto o inverso.
  - `scripts/painel.py`: runner do go/no-go, com `--dry-run` que monta os
    prompts e conta as chamadas sem gastar token. O relatório nomeia os
    falsificadores da §12 em vez de só imprimir faixas, e imprime o
    denominador junto de cada percentual — sobre ~10 casos, "15–35% de
    contestadas" são entre uma e três votações, e as faixas servem para
    disparar inspeção, não para aprovar o painel.
  - **O relatório não dá verde falso.** Sem `ANTHROPIC_API_KEY`, toda consulta
    falha e todo parecer degrada para abstenção — o que é certo para o dado e
    perigoso para o relatório, porque abstenção também é o resultado correto de
    um caso procedimental. Na primeira versão, `--injection` fechava em "100%
    resistido (8/8)" sem nada ter rodado: nenhum ataque obedecia porque nenhum
    chegava ao modelo, um verde falso na única métrica que o PRD trata como
    binária. Agora o script exige a chave antes de executar, e qualquer caso com
    erro registrado em `meta.erros` torna a rodada **inconclusiva**, com saída
    não-zero. Três testes de regressão cobrem isso.
  - 58 testes novos, nenhum deles chamando a API. O que só se mede com modelo
    de verdade — se ele resiste a injection, se as perspectivas divergem onde
    deveriam — fica fora da CI, em `scripts/painel.py`.
  - `CLAUDE.md`: `data/painel/` e `scripts/painel.py` nas listagens de
    estrutura, o bloco de comandos do painel, e uma seção com as quatro
    garantias que o código impõe por construção — mais as três coisas que
    convém não reaprender do jeito difícil (`sem_materia` não é `contestada`,
    categoria é sugestão e não norma, e os testes offline não provam resistência
    a injection).
- **Campo `processo` em `data/direcoes/[ano].yml`** (`nominal` | `simbolica`)
  e três verificações que impedem curadoria de virar trabalho perdido.
  Pelo **art. 185 do Regimento Interno da Câmara**, o processo **simbólico** é
  a regra: os favoráveis permanecem como estão, os contrários se manifestam, e
  o Presidente proclama apenas o resultado — **ninguém registra quem votou o
  quê**. Uma votação assim não produz voto individual, logo não contribui para
  o Score ZIL por mais bem classificada que esteja.
  Três das sete votações curadas eram simbólicas, com peso 3.0, 3.0 e 2.0, e
  somavam zero: **o Score ZIL se apoiava em 4, não em 7**. Nada no fluxo
  verificava isso — `validar_direcoes.py` validava schema, `apply_direcoes.py`
  aplicava direção e peso sem olhar se havia voto.
  - `scripts/dossie.py`: quando não há voto individual, o dossiê deixa de dizer
    "votos individuais não retornados pela API" — que soa como falha técnica
    passageira — e passa a explicar o art. 185 e que a votação **não entra no
    Score ZIL**. É o aviso mais barato: chega antes da pesquisa editorial.
  - `scripts/validar_direcoes.py`: valida o campo offline e ganha
    `--verificar-api`, que consulta a Câmara e falha se uma entrada declarar
    `nominal` sem ter voto, ou se uma entrada sem o campo for simbólica.
  - `scripts/apply_direcoes.py`: avisa ao aplicar direção a votação sem voto
    individual, e o resumo informa quantas das curadas alimentam o score.
  - Medido na varredura de 2023–2026: **211 de 246 votações (86%) são
    simbólicas**. É a regra, não a exceção.

### Fixed
- **`aprovacao` da API da Câmara é inteiro, não booleano — e o `resultado` das
  votações nunca era gravado.** `VotacaoAPI.aprovacao` era anotado
  `Optional[bool]` num dataclass simples, que não coage nada: a anotação era
  falsa e dois call sites confiaram nela.
  `sync_votacoes_zil.py` testava `aprovacao is True`, e como `1 is True` é
  falso, **toda votação era gravada sem resultado**.
  `sync_votacoes_proposicoes.py` testava `aprovacao is False` para rejeição, e
  como `0 is False` também é falso, **toda rejeição virava nulo**.
  Corrigido na borda, com `_como_bool()` em `packages/camara_client`, mais os
  dois call sites. Depois da correção, a varredura de 2023+ gravou 197
  aprovações e **30 rejeições** — as 30 que antes se perdiam.
- **A página de proposição afirmava "Rejeitado" em votação sem placar.** Com
  `resultado` nulo, `proposicoes/[id]/page.tsx` inferia o resultado do placar;
  com `0 > 0` falso, uma votação **simbólica** — que não tem voto nominal —
  aparecia como rejeitada, contradizendo a própria descrição. Três das sete
  votações curadas são simbólicas, então isso estava no ar. A inferência agora
  exige placar; sem ele, nenhum selo é exibido.
- `scripts/sync_votacoes_zil.py`: votação já existente no banco agora tem o
  `resultado` preenchido se estiver nulo. Corrigir o bug não consertava o dado
  já gravado, e rodar o seed de novo não ajudava — havia um retorno antecipado
  antes. Só preenche o que está nulo; nunca sobrescreve.

### Changed
- **`docs/PRD-PAINEL.md`: aprovação registrada.** O header marcava "0.4
  (proposta — aguardando aprovação dos maintainers)" enquanto a Fase 1 já estava
  na `main`. O registro foi escrito dentro dos limites que o próprio documento
  impõe, e os três importam:
  - **Plural removido.** Não havia maintainers a invocar: a `GOVERNANCE.md` v1.1
    registra uma pessoa e anota que a identidade institucional no git é a mesma
    maintainer. O registro diz "maintainer única" — o projeto não apresenta
    decisão individual como colegiada.
  - **A aprovação não autoriza as Fases 2–4.** A condição inegociável 3 exige o
    go/no-go da §12, e ele **não foi executado**: não existe `data/pareceres/`,
    não há transcrição nem métrica no repositório. Aprovar o documento não
    produz o teste, e o registro diz isso explicitamente para que ninguém leia
    "aprovado" como "calibrado".
  - **A carência de C1a continua fora de vigor**, porque `apply_direcoes.py`
    ainda não lê `vigente_a_partir_de` — regra inviolável 10.
  - §13 passa a distinguir **entrega** de **critério de saída** na linha da Fase
    1: ela existir na `main` não libera a Fase 2. Q8 fica registrada como
    respondida, sem apagar a pergunta, porque a razão dela segue valendo — o
    painel não está no caminho crítico.
  - A versão segue 0.4: neste documento as versões são reservadas a emendas de
    conteúdo, e a substância da proposta não mudou. Precedente: o `Status:
    Aceito` do ADR-004.
- **`docs/PRD-PAINEL.md` v0.4 — o painel sai do caminho crítico.** O PRD do
  painel de curadoria foi escrito em 2026-09-17, um dia antes de o
  [ADR-004](decisions/004-placar-focado.md) ser aceito, e era o **único
  documento do projeto que não o citava** — enquanto `PRD.md`, `ROADMAP.md`,
  `GOVERNANCE.md`, `ARCHITECTURE.md` e o `README.md` já haviam migrado.
  O ADR-004 troca o produto da v1 por um placar focado em ~10 votações e revoga
  a meta de 50–100 classificações, que era exatamente a justificativa do painel:
  §1, §2.1 e o objetivo O1 se apoiavam nela, e o critério de saída da Fase 2 era
  "7 → 50–100 direções vigentes".
  - Nova **§2.3** encara a consequência sem suavizar: o painel foi proposto para
    um problema de volume que o projeto decidiu não ter mais. O placar é
    entregável sem painel algum, e a distância entre as 7 classificações de hoje
    e o alvo é de três, não de noventa e três.
  - A justificativa que sobra é **qualidade, não vazão** — escrutínio
    adversarial sobre as ~10 classificações que vão sustentar o placar
    publicamente, com um único revisor humano (§3.1).
  - A economia se inverte: com ~10 votações o custo deixa de ser restrição, e o
    que o preço baixo autoriza é mais compute **por votação** (rodadas, modelos
    distintos, re-runs), não mais votações. R7 rebaixado, Q1 revisto.
  - Dois resíduos que a Emenda 2 já havia tornado falsos e que sobreviveram na
    v0.3: a §12 afirmava que a validação "repousa sobre 7 casos cegos, não sobre
    27" — mas a própria §12 estabelece que as 7 **não são cegas nem validadas**,
    então não são 7 nem 27, é zero; e a §15 orçava a Fase 1 em "~30 votações
    (27 + re-runs)", contando as 20 curadorias cegas que a Emenda 2 eliminou.
  - Novo **aviso de n pequeno** na §14: as faixas de concordância inter-agentes
    (60–85%) e de pautas contestadas (15–35%) foram calibradas para lotes de
    dezenas a centenas. Sobre ~10 votações não são estatísticas — "15–35%" é
    entre uma e três votações. Servem para disparar inspeção, não para aprovar
    o painel, e quem reportar o percentual reporta o denominador.
  - Novas questões em aberto: **Q7** — o veredito emite `categoria_principal`, e
    o ADR-004 deixou o destino das 9 categorias em aberto, então a categoria é
    sugestão registrada e fica fora das métricas da Fase 1; **Q8** — se vale
    construir o painel agora que ele não bloqueia nada.
- **O classificador passa a exigir uma keyword forte**
  (`data/taxonomia/categorias.yml`, `apps/workers/classifiers/__init__.py`).
  A regra antiga era "uma keyword qualquer basta". Numa varredura real de 2024
  a 2026 isso produziu 298 proposições em que ZIL-EDU (88) e ZIL-DIG (87) —
  as duas categorias de vocabulário mais genérico — eram as maiores, enquanto
  **ZIL-SEM, semicondutores, ficava com cinco**. A distribuição estava
  invertida em relação à tese do projeto.
  - Novo campo `keywords_fracas` por categoria: subconjunto de `keywords` que
    não basta sozinho. Acompanhada de uma forte, a fraca continua valendo.
  - A lista é toda baseada em falso positivo **medido**: `técnico` casava com
    "Técnico Judiciário", `tarifa` com "Tarifa Social de Água e Esgoto",
    `Mercosul` com atletas do Mercosul no futebol, `pesquisa` com pesquisa
    clínica, `plataforma digital` com regulação de rede social. As demais
    entraram por polissemia inequívoca (`bolsa`, `renovável`, `satélite`).
  - Keyword que casa **dentro do nome de uma lei citada** entre parênteses não
    classifica mais — a ementa cita leis para dizer quais altera, não para
    dizer do que trata.
  - `energia renovável` e `energias renováveis` entram como **fortes**: o termo
    isolado `renovável` é ambíguo ("prazo renovável"), a expressão não é.
  - `classificar_texto_com_evidencia()` ganha `apenas_fortes`; o padrão segue
    devolvendo todos os casamentos, que é o que permite à ferramenta de
    curadoria explicar por que uma candidata entrou na lista.
  - `scripts/candidatas.py` deixa de manter a própria cópia da lista e da regra
    de citação, e passa a importá-las do classificador.
  - **As 7 votações curadas não são afetadas:** a categoria delas vem de
    `categoria_principal` nos YAMLs de direções, não do classificador
    (`scripts/sync_votacoes_zil.py:140`).

### Added
- **Ferramentas de apoio à curadoria editorial** — atacam o gargalo real do
  projeto, que é tempo de pesquisa por classificação:
  - `scripts/dossie.py`: dado o ID de uma votação, reúne ementa, ementa
    detalhada, palavras-chave, situação, placar contado dos votos individuais,
    orientações de bancada e as leis citadas com link para o Planalto — e emite
    o YAML pronto para colar, **sem o campo `direcao`**, que é a decisão humana.
    Funciona sem banco e sem `ANTHROPIC_API_KEY`. O bloco de análise assistida
    vem **por último e rotulado**, para não ancorar o julgamento antes da
    leitura das fontes primárias (risco registrado em `PRD-PAINEL.md` §12).
  - `scripts/candidatas.py`: varre um ano na API da Câmara e ranqueia votações
    por saliência — precisão do casamento temático, classificabilidade da
    direção, margem disputada e pistas de plenário. Destaca votações
    **rejeitadas** e diz **por qual keyword** cada candidata entrou na lista.
  - `scripts/validar_direcoes.py`: valida os YAMLs de direções, que hoje não têm
    validação alguma. Pega `direcao: Sim` com maiúscula, `peso` fora da tabela,
    `fonte_id` duplicado e justificativa ausente ou curta demais — e reporta a
    distribuição de direções, expondo a variância zero do corpus atual.
  - `tests/unit/test_ferramentas_curadoria.py`: 25 testes das funções puras.
- `apps/workers/classifiers/__init__.py`: `classificar_texto_com_evidencia()` —
  mesma classificação de `classificar_texto()`, mas devolve **quais keywords
  casaram** em cada categoria. Sem a procedência não dá para distinguir uma
  votação sobre `minerais críticos` de uma que casou com `técnico`.

- **Indexação por buscadores atrás de flag, desligada por padrão**
  ([apps/web/lib/flags.ts](../apps/web/lib/flags.ts),
  `apps/web/app/robots.ts`, `apps/web/app/layout.tsx`). Estar no ar e estar no
  Google são coisas diferentes, e só a primeira é reversível: uma URL indexada
  continua aparecendo em busca e em cache muito depois de a página mudar. Com
  as 7 classificações ainda `nao-validado`, um resultado de busca levaria
  alguém direto a um número que o projeto não sustenta. Duas camadas, porque
  uma não substitui a outra — `robots.txt` pede para não rastrear, a meta tag
  impede indexar URL descoberta por link. Liga com
  `NEXT_PUBLIC_INDEXACAO_PUBLICA=true` + redeploy, no mesmo padrão de
  `NEXT_PUBLIC_RANKING_PUBLICO`.

### Changed
- `docs/DEPLOY.md`: documenta o deploy **sem domínio próprio** (domínios do
  Render e da Vercel), a ordem correta de preencher `CORS_ORIGINS` — que só é
  possível depois que a Vercel atribui o domínio — e a flag de indexação.
  Registra que toda `NEXT_PUBLIC_*` é gravada no bundle durante o build e que
  mudá-la exige redeploy, não só salvar no painel.
- `scripts/candidatas.py`: **o tema passa a dominar a disputa no ranqueamento.**
  A nota anterior media só o formato da votação — margem, plenário, se era
  requerimento — e o tema entrava como meio ponto por categoria. O resultado
  medido na varredura de 2024 e 2025: a Política Nacional de Minerais Críticos
  e Estratégicos, a tese do projeto em forma de lei, ficou em **último lugar**
  entre 12 por ter sido quase unânime, enquanto a Tarifa Social de Água e
  Esgoto liderava por ter casado com a palavra `tarifa`. Com placar focado
  (ADR-004), o topo da lista precisa ser o que mais importa.
- `scripts/candidatas.py`: requerimento de **urgência** deixa de ser penalizado
  como manobra processual. Diferente de `"Rejeitado o Requerimento"`, a urgência
  nomeia o objeto: quem votou sim quis pautar aquele projeto. Entra com o peso
  mínimo (0,5), porque mede intenção de pautar, não posição sobre o mérito.
- `scripts/dossie.py`: `_peso_sugerido()` distingue urgência de requerimento
  genérico, e a justificativa impressa registra a diferença.

### Fixed
- `scripts/candidatas.py`: keyword que casa **dentro do nome de uma lei citada**
  não conta mais como tema. O PL 996/2015 — homicídio qualificado contra membros
  do MP e da Magistratura — liderava a lista de 2024 por casar `dados pessoais`
  e `proteção de dados` dentro de "(Lei Geral de Proteção de Dados Pessoais)",
  uma das leis que ele altera. Citar uma lei não é ser sobre o tema dela.
- `scripts/candidatas.py`: keywords que casam com o português comum
  (`técnico`, `engenharia`, `tarifa`, `pesquisa`, `bolsa`, `importação`…) não
  sustentam sozinhas a inclusão de uma votação, e a candidata recebe aviso
  visível. Cada uma da lista produziu um falso positivo real nas varreduras:
  `técnico` casou com "Técnico Judiciário", `engenharia` com obras do Exército,
  `tarifa` com "Tarifa Social de Água e Esgoto".
- `scripts/candidatas.py`: o aviso sobre votações rejeitadas afirmava que eram
  "a via mais natural" para quebrar a variância zero do corpus. **Não são.** Das
  14 rejeitadas de 2024 e 2025, 10 são `"Rejeitado o Requerimento"` sem dizer
  qual, e a API não desambigua — `objetosPossiveis` devolve dezenas de
  candidatos (81 numa votação da PONTE). Sem saber o que foi rejeitado, a
  direção é chute. O texto agora diz isso.


#### Pipeline de dados — discovery, sync e orquestração
- `scripts/discover_proposicoes.py`: descoberta de proposições via API da Câmara —
  busca por keywords das 9 categorias ZIL, classifica localmente, persiste com dados
  completos; suporta `--dry-run`, `--enriquecer`, e janela temporal customizada
- `scripts/sync_votacoes_proposicoes.py`: sync de votações por proposição — itera
  proposições no banco, busca votações na API da Câmara, sincroniza votações + votos
  individuais; suporta `--dry-run`, `--proposicao-id`, `--skip-with-votes`/`--no-skip`
- `scripts/sync_pipeline.py`: orquestrador sequencial dos 4 passos do pipeline —
  discovery → votação sync → enrichment → score recalculation; suporta `--skip-*`
  flags individuais e `--dry-run` global
- `packages/camara_client/__init__.py`: novo método `pesquisar_proposicoes()` com
  busca por keywords, iteração trimestral (restrição da API), e deduplicação por ID
- `packages/camara_client/__init__.py`: novo método `listar_votacoes_proposicao()`
  para buscar votações de uma proposição específica via API da Câmara
- `apps/workers/tasks.py`: `task_enriquecer_pendentes` agora processa proposições
  com `contexto_status = "pendente"` (além de `NULL`)

#### UI/UX — credibilidade, acessibilidade e componentes compartilhados (UI-001 a UI-022)
- `components/ParlamentarAvatar.tsx`: componente reutilizável com fallback de iniciais
  quando foto está ausente ou falha ao carregar — suporta tamanhos sm/md/lg
- `components/DirecaoBadge.tsx`: badge de direção esperada (FAVORÁVEL/CONTRÁRIA) com
  link para /metodologia — usado em proposições e votações
- `components/ui/Badge.tsx`: sistema unificado de badges com variantes `category`,
  `status`, `result` — substitui badges ad hoc espalhados pelas páginas
- `lib/categorias.ts`: mapa centralizado de categorias ZIL com labels legíveis —
  elimina duplicação de strings de categoria em múltiplos componentes
- `ScoreGauge.tsx`: tooltip com âncora de credibilidade ("baseado em N votos ·
  ver metodologia →"), design tokens `zil-*` consolidados (UI-001, UI-016, UI-019)
- `ContextoBadge.tsx`: badge "Contexto pendente" removido da UI pública — aparece
  apenas quando `contexto_status === "pronto"` (UI-002)
- `ranking/page.tsx`: contagem de resultados acima da lista, empty state explicativo,
  busca textual na mesma linha dos filtros, remoção de decoração tipográfica (UI-003/004/005/006)
- `proposicoes/page.tsx`: contagem de resultados, empty state, unificação de filtros,
  remoção de letra decorativa (UI-003/004/005/006)
- `proposicoes/[id]/page.tsx`: síntese de posição ZIL ("ZIL avalia: FAVORÁVEL · com
  base em N votações"), `resultado` inferido de votos quando null, collapse nativo
  com `<details>/<summary>` (UI-010/011/012)
- `votacoes/[id]/page.tsx`: redesign com linguagem mais acessível, placar visual,
  filtro por tipo de voto, links para perfil do parlamentar
- `parlamentar/[id]/page.tsx`: hero metric zone com gauge + proporção em 2 colunas,
  legenda do duplo encoding (dot = alinhamento, badge = voto) com mini badge visual,
  affordance nos cards de categoria, frase de síntese interpretativa, remoção de
  score duplicado e código interno das categorias (UI-013 a UI-022)

#### Segurança — hardening de secrets
- `.pre-commit-config.yaml`: hooks `detect-secrets` (Yelp v1.5.0) e
  `detect-private-key` para bloquear commits com API keys ou chaves privadas
- `core/config.py`: validação de startup em produção — app recusa iniciar se
  variáveis obrigatórias estiverem ausentes ou se DATABASE_URL for SQLite
- `.gitignore`: catch-all para variantes `.env.*` (exceto `.env.example`) +
  padrões para chaves privadas, certificados e credenciais
- `.env.example`: contém apenas placeholders vazios com comentários instrutivos —
  nunca valores reais
- `docker-compose.yml`: credenciais substituídas por `${VAR:-default}` para
  carregamento seguro via `.env`
- `CLAUDE.md`: seção "Segurança e segredos" com 7 regras para manuseio de secrets

#### Testes
- `tests/unit/test_camara_client.py`: 6 testes para `listar_votacoes_proposicao`
  (retorno, lista vazia, resposta non-list, endpoint correto, mapeamento, campos opcionais)
- `tests/unit/test_sync_votacoes.py`: 6 testes para `sync_votacoes_por_proposicao`
  (criação, dedup, skip, dry-run, classificação, linking)
- `tests/integration/test_pipeline_scoring.py`: 3 testes end-to-end validando
  apply_direcoes + recalcular_todos_scores (score positivo, negativo, sem direção)
- Total: **151 testes passando**

#### Documentação
- `specs/002-legislative-enrichment-pipeline/`: spec completo com tasks.md (12 tasks),
  plan.md, contracts/api.md, data-model.md, quickstart.md, research.md
- `specs/ui-ux-credibility-polish/spec.md`: spec das 22 tasks UI/UX

### Changed
- **Redefinição de produto: placar focado no lugar de índice abrangente**
  ([ADR-004](decisions/004-placar-focado.md)). A v1 deixa de perseguir Score ZIL
  para os 594 parlamentares e passa a ser um placar de ~10 votações bem
  pesquisadas. O Score ZIL permanece (−10 a +10) e o motor não muda; muda o
  universo sobre o qual ele opera. Revogadas as metas de cobertura em `PRD.md` e
  `ROADMAP.md`; `constitution.md` registra o fato sem alterar a norma (1.0.1 →
  1.0.2, PATCH).
- **Afirmações falsas removidas da plataforma e dos documentos.** A home
  convidava a *"crie uma conta gratuita"* para votar em deliberações e cobrar
  parlamentares — não existe autenticação no projeto, era CTA para fluxo
  impossível. O `metadata.description` (que vai para buscadores) prometia
  monitorar "cada parlamentar brasileiro". O `ScoreExplainer` dizia "não é
  opinião — é matemática", quando a aritmética opera sobre 7 classificações
  não validadas e a escolha das votações é juízo editorial. Os nove "exemplos"
  de proposições na página de metodologia são hipotéticos e agora estão
  rotulados como tal. `NavBar` apontava para `/sobre`, rota inexistente.
- **`CONTRIBUTING.md` e `GOVERNANCE.md` (v1.1 → v1.2): canais e reuniões.**
  Removida a promessa de "reunião aberta semanal, gravada e publicada", que
  nunca existiu; registrado que **não há agenda de reuniões** e que formato e
  periodicidade serão definidos em conjunto quando houver quórum de
  contribuidores — assim como as próprias diretrizes do projeto. O Discord passa
  a ser descrito como **canal previsto**, com o convite a ser publicado quando
  existir; o canal ativo hoje são as issues do GitHub. Também corrigidos: "voto
  em decisões comunitárias" (sem mecanismo), "revisada pelo comitê editorial"
  (nunca constituído), "lista de proposições pendentes na plataforma" (não há
  fluxo na UI) e GitHub Discussions (desabilitado).
- **Renomeação do repositório** `manifesto-zil` → `zil-observatorio` propagada
  para badge de CI, comando de clone, link público no frontend, CHANGELOG,
  ARCHITECTURE, DEPLOY e `launch.json`.
- **Senado: capacidade ≠ dado.** O README marcava "Crawler Senado Federal ✅"
  enquanto a página de metodologia dizia que o Senado não está na v1. Não era
  contradição: o crawler existe, mas nenhum dado do Senado foi ingerido e as 7
  direções são todas da Câmara. O README passa a dizer as duas coisas.
- `README.md` e `CLAUDE.md`: sincronizados com o estado real do código, que ambos
  subestimavam. Correções: ingestão do Senado, `/bussula`, `/metodologia` e CI/CD
  estavam marcados como backlog mas já existem; contagem de testes de 98 para 151;
  link quebrado para `docs/MANIFESTO.md` removido (o manifesto é a home da
  plataforma); comando `uvicorn apps.api.main:app` do Quick Start corrigido para
  `cd apps/api && uvicorn main:app`, já que a forma documentada falhava com
  `ModuleNotFoundError` por causa dos imports curtos (ADR-002); as 22 tarefas de
  design critique marcadas como concluídas. Adicionadas seções sobre o volume real
  de curadoria editorial (7 votações com direção definida — o gargalo atual da v1)
  e sobre as pendências conhecidas de infraestrutura (`make migrate`, `make seed`,
  `make test`, `admin_token` em query string, código dormente).
- `scripts/apply_direcoes.py`: agora chama `recalcular_todos_scores(db)` automaticamente
  após aplicar direções — elimina necessidade de recalcular scores manualmente
- `apps/api/routers/legislativo.py`: endpoints de proposições e votações retornam campos
  de enriquecimento (resumo_simples, categorias) em linguagem mais acessível
- `apps/api/routers/parlamentares.py`: campo de contagem de votos adicionado à resposta
- `apps/api/schemas/__init__.py`: novos schemas para campos de enriquecimento

### Fixed
- **Texto de lei voltava ilegível do Planalto**: o servidor devolve
  `Content-Type: text/html` **sem charset**, então o httpx assumia utf-8 num
  conteúdo windows-1252 — "dispõe" virava "disp?e". Pior que não voltar: parecia
  dado bom. `_fetch_planalto` passa a fixar o encoding quando o servidor não
  declara. Junto: `_strip_tags` agora resolve entidades HTML (`&nbsp;`, `&amp;`),
  que antes sobreviviam até o banco e até o prompt do LLM.
- **`anthropic` não estava nas dependências**: o pacote era importado com
  `try/except` em `apps/workers/enrichment` e nunca declarado em
  `requirements.txt`. O passo de LLM do pipeline de enriquecimento não podia
  rodar em ambiente nenhum, mesmo com a chave configurada.

- **Busca de leis no Planalto nunca funcionou**: `_fetch_planalto` enviava
  `User-Agent: ZIL-Observatorio/1.0`, e o Planalto derruba a conexão para
  agentes que não pareçam navegador. Toda resolução de lei falhava em silêncio e
  virava `nao_encontrada` — ou seja, o pipeline de enriquecimento vinha rodando
  sem o texto legal que é a razão de ele existir. Trocado para
  `Mozilla/5.0 (compatible; ZIL-Observatorio/1.0; +https://zilobservatorio.org)`,
  a convenção de crawler bem-comportado: passa no filtro e continua
  identificando quem chama, com endereço de contato.

- **Taxonomia editorial ignorada em qualquer container (silenciosamente)**:
  `routers/bussula.py` e `workers/classifiers` resolvem o caminho dos YAMLs
  relativo ao próprio arquivo, o que dentro do container aponta para `/data/...`
  — inexistente, já que só `apps/api` era montado. O classificador caía na
  taxonomia embutida de fallback (57 das 131 keywords curadas, 44% de cobertura)
  e `/bussula` respondia `[]`. Nenhum dos dois gerava erro, então o problema
  passaria despercebido até produção. Adicionado mount `./data:/data:ro` em
  `api`, `worker` e `beat`.
- **`make migrate` não existia de fato**: `alembic.ini` apontava para
  `data/migrations`, diretório nunca commitado. Criado o ambiente de migrations
  (`env.py` lendo `DATABASE_URL` do ambiente em vez de credencial versionada) e
  a migration inicial com as 8 tabelas, validada contra Postgres limpo —
  `alembic check` reporta zero drift em relação aos modelos. Novo alvo
  `make migrate-stamp` para bancos criados pelo `create_all` sem carimbo.
- **`make setup` falhava mesmo com migrations**: subia a API antes de migrar, e
  o `create_all` do lifespan criava as tabelas sem carimbo do Alembic. Reordenado
  para migrar com apenas `db` e `redis` no ar, e só então subir o restante.
- **`make seed` chamava script inexistente**: criado `scripts/seed.py`, que
  sincroniza da API da Câmara as votações já curadas em `data/direcoes/`, aplica
  as direções e recalcula scores. Dado real e rastreável, nunca fictício.
- **`make test` coletava 0 testes**: o container `api` monta só `apps/api` e
  `tests/` fica na raiz. Alvos passam a rodar no host (como a CI), com `PYTHON`
  autodetectando `.venv`. `test-web` deixou de chamar `npm test`, que não existe
  em `apps/web`, e passa a rodar lint + type check.
- **Token de admin trafegava em query string**: `POST /proposicoes/{id}/enriquecer`
  recebia `admin_token` na URL, que vaza em log de servidor, histórico de browser
  e header `Referer`. Migrado para `Authorization: Bearer`, com comparação em
  tempo constante (`secrets.compare_digest`) e 6 testes cobrindo ausência de
  header, token errado, esquema errado, query string e servidor sem token.
- **Variável do compose derrubava a aplicação**: `Settings` recusava qualquer
  chave do `.env` não declarada, então `POSTGRES_USER` ou `POSTGRES_PORT` — que
  são do docker compose — causavam `ValidationError` no import. Passa a usar
  `extra="ignore"`.
- **Postgres local sombreava o container**: a porta do host virou
  `POSTGRES_PORT` (default 5432 inalterado), porque um Postgres local na 5432
  faz o host falar com o banco errado sem nenhum aviso.
- **CI vermelha desde 2026-04-04 — lint do backend**: `.github/workflows/ci.yml` instalava
  `ruff` sem pin, então cada run pegava a versão mais recente e o conjunto de regras mudava
  sozinho (267 erros na CI contra 5 no `ruff==0.8.6` pinado em `requirements.txt`). Passa a
  instalar de `apps/api/requirements.txt`, alinhado ao job de testes e ao
  `cache-dependency-path` que o próprio job já declarava. Os 5 erros reais foram corrigidos:
  `routers/legislativo.py` tinha `import os` morto; os imports pós-`sys.path` em
  `crawlers/camara.py` e `crawlers/senado.py` receberam `# noqa: E402`, seguindo a convenção
  já usada em `tests/conftest.py`.
- **CI vermelha desde 2026-04-04 — lint do frontend**: `apps/web` não tinha config de ESLint,
  apesar de `eslint` e `eslint-config-next` estarem nas devDependencies. Sem config, `next lint`
  abria o assistente interativo de setup e saía com código 1 na CI (sem TTY), o que também
  deixava o job `Frontend — Build` permanentemente pulado por `needs:`. Adicionado
  `apps/web/.eslintrc.json` com `next/core-web-vitals` — equivalente à opção "Strict
  (recommended)" que o assistente sugeria.
- **Pre-commit bloqueava todo commit**: `.pre-commit-config.yaml` passa
  `--baseline .secrets.baseline` ao hook `detect-secrets`, mas o arquivo nunca foi
  commitado — o hook abortava com `Invalid path: .secrets.baseline` em qualquer commit,
  para quem tivesse rodado `pre-commit install`. Baseline gerado e adicionado; as 5
  detecções são placeholders de desenvolvimento já documentados (`zil:zil` do Postgres
  local, `zil-dev-key` do Typesense) — nenhum segredo real.
- **Celery worker e beat não iniciavam no Docker**: `docker-compose.yml` montava
  `apps/workers` em `/workers`, fora do `WORKDIR` (`/app`) — `celery -A workers.tasks`
  abortava com `ModuleNotFoundError: No module named 'workers'`, porque o diretório pai
  do pacote não estava no `sys.path`. O bootstrap de `sys.path` em `apps/workers/tasks.py`
  não cobre o caso: ele só executa depois que o módulo já foi localizado. Mount corrigido
  para `/app/workers` em ambos os serviços — worker sobe com as 7 tasks registradas e
  beat inicia o scheduler.
- **Enrichment não executava**: `apps/workers/enrichment/__init__.py` usava `os.getenv()`
  para ler configurações — falha silenciosa quando variável de ambiente vazia sobrescreve
  o `.env` (Pydantic BaseSettings dá precedência a env vars). Corrigido para usar
  `core.config.settings` consistentemente com o resto do codebase. 406 proposições
  enriquecidas com sucesso após a correção.
- **CORS em dev**: `main.py` agora usa `allow_origin_regex` para aceitar qualquer porta
  localhost, corrigindo chamadas de API de preview servers em portas dinâmicas
- **Caminho SQLite**: DATABASE_URL usa caminho absoluto — mesmo banco independente
  do diretório de execução
- **Resolução de .env**: `core/config.py` resolve `.env` relativo ao arquivo de config,
  não ao cwd do processo
- **Proxy Next.js → FastAPI**: `next.config.js` com rewrite para que preview no browser
  alcance a API backend

---

## [0.4.0] — 2026-04-02

Features 002–009 from the v1 backlog, all implemented in a single release.

### Added

#### 002 — Senado Federal ingestion
- `packages/senado_client/__init__.py`: `SenadoClient` with `listar_senadores()`,
  `listar_materias_ano()`, `listar_votacoes_materia()`, `obter_votos_votacao()`
- `apps/workers/crawlers/senado.py`: `sync_senadores()`, `sync_materias()`,
  `sync_votacoes_materia()`, `run_full_sync()` with `IngestionRun` audit trail
- Two new Celery tasks in `apps/workers/tasks.py`:
  - `task_sync_senadores` — weekly Monday 03:30
  - `task_sync_votacoes_senado` — every 6 hours at :30

#### 003 — Editorial workflow script
- `scripts/apply_direcoes.py`: loads `data/direcoes/*.yml`, matches by `fonte_id +
  fonte`, updates `Votacao.direcao_esperada` and `Votacao.peso`; supports `--ano`
  and `--dry-run` CLI flags

#### 004 — Frontend: /ranking
- Partido filter fetched live from `/parlamentares/partidos/ranking`
- Server-side filters: fonte, uf, partido, ordem (per_page=600)
- Client-side name search
- Skeleton loading (12 animated rows while fetching)
- Split display: scored parlamentares with rank numbers / unscored section (opacity-50)

#### 005 — Frontend: /parlamentar/[id]
- Per-category alignment breakdown with progress bars
- Clickable category cards to filter vote history
- "← Voltar ao ranking" navigation link
- Vote history table with alinhamento indicator per vote

#### 006 — Frontend: /proposicoes + detail pages
- Tipo filter (PL, PEC, PLP, MPV, PDL, PRC) and ano filter (last 10 years)
- Clickable rows link to `/proposicoes/[id]`
- `apps/web/app/proposicoes/[id]/page.tsx`: ementa, categories, situacao,
  url_inteiro_teor, votação list with placar and link to voting detail
- `apps/web/app/votacoes/[id]/page.tsx`: full voting record with per-parlamentar
  votes, filterable by vote type, each row links to `/parlamentar/[id]`

#### 007 — Frontend: /bussula
- Fetches `/bussula`, groups indicators by category
- `MarcoCard`: valor_atual, progress bar toward meta, tendência symbol, fonte link
- Empty state explains how to add indicators via YAML PR

#### 008 — Frontend: /metodologia
- Static page: score formula, weights table (3.0/2.0/1.0/0.5), gradient scale visual
- 9 category descriptions with examples, 5 limitations, editorial process

#### 009 — CI/CD
- `.github/workflows/ci.yml` rewritten with 4 jobs:
  - `test-backend`: pytest with pip cache
  - `lint-backend`: ruff only
  - `lint-frontend`: npm ci + ESLint + tsc --noEmit
  - `build-frontend`: next build (depends on lint-frontend)
- CI badge added to README

### Changed
- `apps/api/routers/parlamentares.py`: `per_page` limit raised from 100 to 600
- `apps/api/routers/legislativo.py`: added `GET /proposicoes/{id}/votacoes` and
  `GET /votacoes/{id}` endpoints
- `apps/api/routers/bussula.py`: new router reading `data/bussula/marcos.yml`
- `apps/api/requirements.txt`: added `pyyaml==6.0.2` (was missing, used by classifier)
- `apps/api/main.py`: registered `bussula` router

### Fixed
- Removed unused imports (`case`, `Field`, `func`, `FonteEnum`) that would fail ruff CI

---

## [0.3.0] — 2026-04-02

Feature 001 merged from branch `001-camara-api-ingestao`.

### Added
- `CLAUDE.md`: development guidelines, ADRs summary, coding conventions
- Enhanced `apps/api/models/__init__.py`: `IngestionRun`, `ScoreVotacao`, `Proposicao`
  models; `VotoEnum` with ausente/abstencao/obstrucao/artigo_17
- `apps/workers/crawlers/camara.py`: full sync with idempotent upsert,
  `IngestionRun` audit logging
- `apps/workers/scoring/__init__.py`: `recalcular_score_parlamentar()` with
  `ScoreVotacao` persistence; `recalcular_todos_scores()`
- `apps/workers/classifiers/__init__.py`: keyword classifier against
  `data/taxonomia/categorias.yml`; `relevancia_score()`
- `packages/camara_client/__init__.py`: retry logic, pagination, full deputy/
  voting/vote sync
- 98 tests across `tests/unit/`, `tests/integration/`, `tests/contract/`
- `tests/conftest.py`: SQLite in-memory fixtures (ADR-001)
- `specs/001-camara-api-ingestao/`: full Specify Kit spec set

---

## [0.2.0] — 2026-04-01

Homepage redesign and design system foundation.

### Added
- `apps/web/components/ui/`: Button, Badge, Card, Callout, SectionHeader
- `apps/web/components/NavBar.tsx`: responsive nav with hamburger menu on mobile
- `apps/web/components/ScoreExplainer.tsx`: visual score scale, weights, formula
- `apps/web/components/RankingPreview.tsx`: top/bottom 5 from API with skeleton + error
- `apps/web/components/CategoryGrid.tsx`: 9 ZIL category cards with filter links
- `apps/web/components/ManifestoSignature.tsx`: sign form + share button
- `apps/web/app/page.tsx`: new landing page composing all sections
- `apps/web/app/manifesto/page.tsx`: redirect to `/`
- `apps/web/tailwind.config.js`: `zil-*` design tokens (green, gold, cream, dark, orange)
- `apps/web/app/globals.css`: base typography and utility classes

### Removed
- `apps/web/app/page.jsx`: replaced by `page.tsx`; removed internal SPA router,
  mock data, inline styles, and duplicated nav/footer

---

## [0.1.0] — 2026-03-31

Initial scaffold.

### Added
- `apps/api/`: FastAPI app, SQLAlchemy models (Parlamentar, Votacao, Voto, Proposicao),
  Pydantic schemas, routers for parlamentares, legislativo
- `apps/workers/`: Celery app, task definitions with beat schedule, Câmara crawler stub,
  scoring engine stub, keyword classifier with `data/taxonomia/categorias.yml`
- `apps/web/`: Next.js 14 scaffold with TypeScript, Tailwind CSS, postcss
- `packages/camara_client/__init__.py`: Câmara API client stub
- `data/taxonomia/categorias.yml`: 9 ZIL categories with Portuguese/English keywords
- `docker-compose.yml`: api + worker + beat + redis + postgres services
- `docs/ARCHITECTURE.md`, `docs/PRD.md`, `docs/GOVERNANCE.md`: founding documents
- `pytest.ini`, `tests/test_classifier.py`, `tests/test_scoring.py`: initial test suite

---

[Unreleased]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/melissa-pereira-deel/zil-observatorio/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/melissa-pereira-deel/zil-observatorio/releases/tag/v0.1.0

# Discovery: tramitação — onde a proposição está, o que vem depois, o que virou

**Data:** 2026-10-30
**Estado:** levantamento, não decisão. Propõe; quem decide é a maintainer.
**Pergunta que motivou:** "De onde vêm os status das proposições? Existe uma
ordem, um fluxo pré-definido, regras determinísticas? É possível saber todas
as etapas e caminhos, da criação até virar lei e ser de fato implementada?
É possível obter dados de proposições implementadas para entender seu
impacto?"

Método: quatro agentes trabalharam em paralelo, somente leitura. Um levantou
o processo legislativo nas fontes canônicas (Constituição, Regimentos da
Câmara, do Senado e do Congresso, LC 95/1998, Decreto 12.002/2024); outro
inventariou as APIs da Câmara e do Senado com chamadas ao vivo, os arquivos
em massa, as fontes pós-lei e os MCPs e bibliotecas existentes; outro mapeou
código e banco; o último sintetizou fases, arquitetura de informação, dados e
roteiro. Eu cruzei os relatórios, conferi os números no banco e na API e
resolvi as contradições. Toda afirmação externa tem URL ou referência
normativa; `arquivo:linha` para o que é do repositório.

Marcas usadas:

- **D** — regra determinística, com prazo ou quórum fixado em norma.
- **D\*** — prazo fixado em norma que, na prática, é descumprido sem consequência.
- **X** — decisão discricionária (despacho, pauta, requerimento).
- **⚠** — não verificado, ou verificado só em fonte secundária.

---

## Respostas curtas

**De onde vêm os status?** Do campo `statusProposicao.descricaoSituacao` de
`GET /proposicoes/{id}` da API da Câmara. No ZIL, só
`scripts/discover_proposicoes.py:215-233` grava esse campo, e só quando cria a
proposição. Faltam por três razões:

1. `scripts/sync_votacoes_zil.py:113-142` e `_upsert_proposicao`
   (`apps/workers/crawlers/camara.py:61-103`) criam proposições a partir das
   votações sem buscar o detalhe. **As 5 proposições do placar estão sem
   status — e 4 delas já viraram lei.**
2. Nada atualiza a situação depois da criação. O que aparece é uma foto do
   dia em que a proposição entrou no banco.
3. A própria API devolve situação nula para projetos recém-apresentados,
   ainda sem despacho: 29% dos PLs de 2026 (1.519 de 5.200).

**Existe um fluxo determinístico?** Em parte. O rito está escrito em norma, e
quóruns e alguns prazos são determinísticos (sanção em 15 dias úteis; medida
provisória em 60 + 60 dias). Mas a escolha das comissões, a pauta e a maioria
dos prazos de comissão são discricionários ou descumpridos sem consequência.
Dá para dizer **qual é a próxima etapa do rito**; não dá para dizer
**quando**, salvo quando já há reunião agendada ou um prazo legal correndo.

**Dá para saber todas as etapas e caminhos?** Sim, por espécie (PL, PLP, PEC,
MPV, PDL), com os desfechos possíveis (arquivamento, retirada,
prejudicialidade, rejeição, perda de eficácia, veto total) e a tramitação em
conjunto. O que não existe é uma ordem oficial das situações nem um glossário
para o cidadão: a Câmara tem 99 códigos de situação e 235 tipos de
tramitação; o Senado, 175 tipos de situação. O mapa de fases e o glossário
têm de ser feitos pelo ZIL — versionados, testados e auditáveis (§4).

**Dá para saber se a lei foi implementada e qual o impacto?** Não existe base
oficial que ligue projeto → lei → regulamentação → execução → resultado. O
que dá para automatizar é o começo da cadeia: o Senado informa a lei gerada
por um projeto (`normaGerada`) e, para parte das leis, quais decretos
regulamentam quais dispositivos (`vides` da API de legislação). Execução e
avaliação existem em fontes esparsas e exigem curadoria; atribuir um efeito a
uma lei exige avaliação, não um indicador (§7).

**MCPs e ferramentas:** não há MCP oficial da Câmara, do Senado ou do
Congresso. Há comunitários úteis para explorar em desenvolvimento; em
produção, o recomendado é chamar as APIs oficiais diretamente (§3.6).

---

## 1. Diagnóstico: o que existe hoje

### 1.1 Modelo e banco

`Proposicao` (`apps/api/models/__init__.py:83-124`) guarda o status como
texto livre:

| Campo | Linha | Preenchido no banco de desenvolvimento (240 proposições) |
| --- | --- | --- |
| `situacao` | :96 | 219 |
| `data_apresentacao` | :97 | 235 |
| `ultimo_despacho` | :98 | 235 |
| `url_inteiro_teor` | :102 | 235 |
| `tramitacoes` (JSON) | :103 | **0** |
| `autores` (JSON) | :95 | **0** |

Não há colunas para código de situação, órgão atual, regime, forma de
apreciação, relator, proposição principal (apensação) nem lei resultante.
Não há tabela de tramitação.

As 16 situações distintas no banco, mais nulo:

| Situação | Qtd. | O que de fato quer dizer |
| --- | --- | --- |
| Aguardando Parecer | 50 | Na comissão, com relator trabalhando |
| Aguardando Designação de Relator(a) | 43 | Na comissão, sem relator |
| Tramitando em Conjunto | 24 | Apensada; anda junto com a principal |
| Arquivada | 22 | Parada; o motivo (fim de legislatura, parecer terminativo, rejeição) está no despacho (§2.2) |
| *(nula)* | 21 | Ver §1.2 |
| Aguardando Despacho do Presidente da Câmara dos Deputados (Chancela) | 20 | Recém-apresentada, antes da distribuição |
| Transformado em Norma Jurídica | 16 | Virou lei (ou decreto legislativo) |
| Pronta para Pauta | 8 | Instrução concluída — em comissão **ou** no Plenário; só o órgão diz qual |
| Perdeu a Eficácia | 8 | Medida provisória não votada a tempo |
| Aguardando Despacho do Presidente da Câmara dos Deputados (Autorização) | 7 | Recém-apresentada, antes da distribuição |
| Aguardando Encaminhamento | 7 | Ambígua: num caso o despacho diz que a proposição ficou prejudicada; noutro, que foi aprovada como substitutivo de outra |
| Aguardando Apreciação pelo Senado Federal | 5 | A Câmara concluiu; está no Senado |
| Aguardando Designação - Aguardando Devolução de Relator(a) que deixou de ser Membro | 4 | Na comissão, relator saiu |
| Ag. Análise de Inconstitucionalidade | 2 | Recém-apresentada, triagem antes da distribuição |
| Retirado pelo(a) Autor(a) | 1 | Encerrada pelo autor |
| Aguardando Autorização do Despacho | 1 | Recém-apresentada |
| Aguardando Apensação | 1 | Vai tramitar em conjunto |

Duas lições saem da tabela. Um leigo lê "Aguardando Despacho do Presidente"
como "esperando sanção do Presidente da República", quando é o oposto: a
proposição acabou de chegar à Câmara. E "Pronta para Pauta" e "Aguardando
Encaminhamento" não dizem a fase sem o órgão e o despacho.

### 1.2 Por que falta status

| Origem | Proposições | Com situação | Causa |
| --- | --- | --- | --- |
| `sync_votacoes_zil` (2026-09-17) | 5 | **0** | Cria a proposição a partir da votação, sem `GET /proposicoes/{id}` |
| `discover_proposicoes` (2026-10-29) | 235 | 219 | 16 nulas porque a API devolve nula (PL recém-apresentado) |

As 5 primeiras são justamente as do placar:

| Proposição | Situação real na Câmara (consulta de 2026-10-30) |
| --- | --- |
| PL 327/2021 (Paten) | Transformado em Norma Jurídica — Lei 15.103/2025, veto parcial |
| PL 2/2024 (depreciação acelerada) | Transformado em Norma Jurídica — Lei 14.871/2024 |
| PL 528/2020 (combustível do futuro) | Transformado em Norma Jurídica — Lei 14.993/2024 |
| PL 1847/2024 (desoneração TIC) | Transformado em Norma Jurídica — Lei 14.973/2024 |
| PL 1264/2024 (PADIS) | Aguardando Designação de Relator(a), na CFT, desde 09/05/2025 |

Mesmo quando a API tem o dado, a situação pode atrasar em relação aos
eventos. O PL 278/2026 registra em 15/09/2026 "Transformação em Norma
Jurídica — Lei Ordinária 15504/2026", mas a situação dos eventos seguintes
continua "Aguardando Sanção". O tipo de tramitação é o sinal mais confiável.

### 1.3 O que já é buscado e jogado fora

`packages/camara_client/__init__.py:376-391` já tem `obter_autores`,
`obter_tramitacoes` e `obter_relacionadas`. Só a ficha de fatos do pipeline
de explicação os usa, e em memória (`apps/workers/explicacao/coleta.py:49-54,
138-150`). `scripts/dossie.py:147-150` busca a situação na hora e também não
guarda. Do `statusProposicao`, o discover descarta `codSituacao`, `regime`,
`siglaOrgao`, `apreciacao` e `uriUltimoRelator`.

### 1.4 Senado: integração quebrada

`packages/senado_client/__init__.py:202-230` espera
`IdentificacaoMateria.CodigoMateria` e `SituacaoAtual` em
`/materia/pesquisa/lista`. A resposta atual é plana (`Codigo`, `Ementa`,
`Data`, `UrlDetalheMateria`) e não traz situação: o cliente descarta todas as
matérias, e o banco tem 0 do Senado. Os endpoints `/materia/*` respondem com
`deprecation: 18 Mar 2025` e `sunset: 01 Feb 2026`; `/votacao/senador/{id}`
devolve 404. A família nova é `/processo*` e `/votacao` (§3.3).

### 1.5 O que a API e a página mostram

- `ProposicaoRead` (`apps/api/schemas/__init__.py:48-67`) expõe só
  `situacao`. Não há endpoint de tramitação, autores ou relacionadas.
- A página (`apps/web/app/proposicoes/[id]/page.tsx`) mostra a situação crua
  num `Selo` cinza que trunca texto longo (:148). Não mostra órgão, regime,
  relator, autores, linha do tempo, próximos passos, lei resultante nem link
  para a página da Câmara (só o PDF).
- A lista (`app/proposicoes/page.tsx:215`) mostra o mesmo Selo e não filtra
  por situação.
- O kit tem `LinhaDoTempo`, `Marco` e `Etapas`
  (`apps/web/components/ui/Tempo.tsx:13-72`; "Etapas para tramitação" no
  README do kit) — **nenhuma página os usa**. `Etapas` pulsa a etapa atual com
  animação contínua, contra a regra do próprio kit ("animação que roda
  sozinha").

### 1.6 Documentos anteriores

`docs/DISCOVERY-DADOS-PROPOSICOES.md` (2026-04-05) e
`specs/012-enriquecimento-dados-proposicoes/spec.md` já propunham situação
estruturada (F-001), cadeia legislativa (F-003), órgão e relator (F-007) e
lei resultante (F-008). Nada foi implementado. Este documento os atualiza:

| Continua valendo | Fica superado |
| --- | --- |
| Persistir `statusProposicao` inteiro; sync de detalhe; endpoint de tramitação | Lei resultante por `urnFinal` — o campo vem sempre nulo (100% nos arquivos de 2015, 2019 e 2021) |
| Autores, temas, relator (F-002, F-004 a F-006) | Endpoint de tramitação "a partir do JSON existente" — o JSON está sempre vazio |
| | Cores por situação (verde para aprovada, laranja para arquivada) — verde e vermelho são reservados a alinhamento no kit |
| | Contagens (406 proposições) — o banco tem 240 |

---

## 2. O processo canônico

Fontes: Constituição Federal (CF), Regimento Interno da Câmara (RICD),
Regimento Interno do Senado (RISF), Resolução do Congresso 1/2002 (RCN 1/02),
LC 95/1998, LINDB, Decreto 12.002/2024. URLs no fim (§ Fontes).

**Três premissas corrigidas durante o levantamento:**

- O PL 327/2021 (Paten) virou a **Lei 15.103/2025**, não a 14.990/2024 (que
  cria o marco do hidrogênio de baixa emissão).
- O Decreto 9.191/2017 foi **revogado** pelo Decreto 12.002/2024 (art. 77, I).
- O arquivamento ao fim da legislatura mudou com a RCD 33/2022: na Câmara, só
  vão ao arquivo proposições que já tramitaram **três legislaturas completas**.

### 2.1 Tronco: projeto de lei ordinária iniciado na Câmara

| # | Etapa | Regra | Tipo | Base |
| --- | --- | --- | --- | --- |
| 1 | Apresentação | Parlamentares, comissões, Presidente da República, STF, tribunais superiores, PGR, cidadãos (1% do eleitorado em 5 estados) | D | CF 61 |
| 2 | Despacho | O Presidente da Câmara distribui às comissões (até 4 de mérito; acima, comissão especial; CFT e CCJC quando cabem). Proposição conexa é apensada | X (quais comissões); D\* (prazo) | RICD 139 |
| 3 | Regime | Urgência (151 I; 155, por maioria absoluta), prioridade (151 II, ex.: projetos do Executivo), ordinária (151 III) | D pelo tipo; X por requerimento | RICD 151–155 |
| 4 | Forma de apreciação | Regra: **conclusiva nas comissões**. Vai ao Plenário se for PLP, código, iniciativa popular, matéria indelegável, projeto do Senado já aprovado em Plenário, com pareceres divergentes ou em urgência | D | RICD 24 II; CF 58 §2º I |
| 5 | Comissões | Relator, parecer; prazos de 5, 10 ou 40 sessões conforme o regime | D\* | RICD 52 |
| 5a | Parecer terminativo | Inconstitucionalidade (CCJC) ou inadequação financeira (CFT) arquiva, salvo recurso | D | RICD 54 |
| 6 | Aprovação conclusiva | Abre prazo de recurso: 5 sessões, 1/10 dos deputados (52) | D | RICD 58 §1º, 132 §2º |
| 7 | Plenário | Pauta: Presidente e Colégio de Líderes. Maioria simples, presente a maioria absoluta | X (pauta); D (quórum) | CF 47; RICD 183 |
| 8 | Casa revisora | Aprova → sanção; rejeita → arquivo; emenda → volta | D | CF 65 |
| 9 | Senado | Despacho às comissões; decisão terminativa só em casos previstos; recurso de 9 senadores em 5 dias úteis | X/D | RISF 91 |
| 10 | Volta à iniciadora | Só aceita ou rejeita as emendas do Senado | D | CF 65 p.ú. |
| 11 | Sanção ou veto | **15 dias úteis**. Veto total ou parcial (de artigo, parágrafo, inciso ou alínea inteiros). Silêncio é sanção tácita | D | CF 66 §§1º–3º |
| 12 | Veto no Congresso | 30 dias corridos; depois tranca a pauta. Derrubada: 257 deputados e 41 senadores | D\* | CF 66 §§4º–6º |
| 13 | Promulgação | Presidente da República em 48 h; se não, Presidente ou Vice do Senado | D | CF 66 §§5º e 7º |
| 14 | Publicação no DOU | — | D | CF 84 IV |
| 15 | Vigência | A lei traz cláusula de vigência; omissa, 45 dias | D | LC 95 art. 8º; LINDB 1º |
| 16 | Regulamentação | Decreto e atos infralegais. **Não há prazo geral**; só se a própria lei fixar | X | CF 84 IV; Decreto 12.002/2024 art. 4º §2º |

### 2.2 Desfechos e caminhos alternativos

| Evento | Regra | Tipo | Base |
| --- | --- | --- | --- |
| Arquivamento (Câmara) | Ao fim da legislatura, só se tramitou 3 legislaturas completas; há exceções | D | RICD 105; RCD 33/2022 |
| Arquivamento (Senado) | Ao fim da legislatura, com exceções; desarquivamento por 1/3 em 60 dias | D | RISF 332 |
| Retirada pelo autor | A qualquer tempo; depois de parecer favorável, decide o Plenário | X | RICD 104 |
| Prejudicialidade | Matéria idêntica já decidida, ou perda de oportunidade | D/X | RICD 163–164 |
| Rejeição | Mesma matéria só volta na mesma sessão legislativa por maioria absoluta | D | CF 67 |
| Tramitação em conjunto (apensação) | A mais antiga tem precedência; um só parecer para todas | X | RICD 142–143 |
| Sustação de decreto | PDL contra ato do Executivo que exorbita a lei | X | CF 49 V |
| Devolvida ao autor | A Presidência devolve proposição mal formalizada, alheia à competência da Câmara, evidentemente inconstitucional ou antirregimental | X | RICD 137 §1º |

### 2.3 Variantes por espécie

| Espécie | Diferenças |
| --- | --- |
| **PLP** | Sempre vai ao Plenário; dois turnos na Câmara; maioria absoluta (257 e 41) — CF 69; RICD 148, 183 |
| **PEC** | Proposta por 1/3 de uma Casa, pelo Presidente ou por mais da metade das Assembleias; CCJC (admissibilidade) e comissão especial; dois turnos em cada Casa com 3/5 (308 e 49); **sem sanção** — promulgada pelas Mesas, inclusive em partes — CF 60; RICD 202; RISF 354–363 |
| **MPV** | Vale desde a edição. Comissão mista; 60 + 60 dias, suspensos no recesso; tranca a pauta no 45º dia (para PLs sobre matéria que poderia ser MPV — STF, MS 27.931); aprovada sem mudança é promulgada; alterada vira **PLV** e vai à sanção; não votada, **perde a eficácia** — CF 62; RCN 1/02 |
| **PDL** | Matéria exclusiva do Congresso (tratados, sustação de atos do Executivo, concessões de rádio e TV); **sem sanção** — CF 49 |
| **PLN** | Orçamento (PLDO, PLOA, PPA, créditos): CMO e sessão do Congresso — CF 166. Fora do escopo do ZIL hoje |

### 2.4 Prazos e quóruns

| Item | Valor | Tipo | Base |
| --- | --- | --- | --- |
| Deliberação | Maioria dos votos, presente a maioria absoluta | D | CF 47 |
| Lei complementar | Maioria absoluta (257 / 41) | D | CF 69 |
| PEC | 3/5 em dois turnos em cada Casa (308 / 49) | D | CF 60 §2º |
| Derrubada de veto | Maioria absoluta em cada Casa | D | CF 66 §4º |
| Recurso contra decisão conclusiva | 1/10; 5 sessões (Câmara) ou 5 dias úteis (Senado) | D | RICD 58; RISF 91 |
| Comissões da Câmara | 5 / 10 / 40 sessões | D\* | RICD 52 |
| Urgência constitucional | 45 dias em cada Casa + 10 para as emendas do Senado | D | CF 64 |
| Sanção | 15 dias úteis | D | CF 66 §1º |
| Veto no Congresso | 30 dias corridos (ex.: o VET 8/2025 levou 5 meses) | D\* | CF 66 §4º |
| MPV | 60 + 60 dias; tranca no 45º | D | CF 62 |
| Vacatio supletiva | 45 dias | D | LINDB 1º |

### 2.5 Depois da lei

A cadeia canônica é publicação → vigência → regulamentação (decreto, depois
portaria, resolução, instrução normativa) → habilitação e execução (despesa
ou renúncia de receita) → avaliação. Vigência não é eficácia: o benefício da
Lei 14.871 só existe "por decreto" (art. 2º); os critérios do Paten ficaram
para regulamento (Lei 15.103, art. 3º §2º).

- O Decreto 12.002/2024 **não cria** prazo nem acompanhamento da
  regulamentação.
- A Constituição exige avaliação de políticas públicas com divulgação de
  resultados (CF 37 §16, EC 109/2021), mas não há registro central.
- Para benefício tributário — o caso típico de política industrial — a LC
  224/2025 incluiu o art. 14-A na LRF: prazo máximo de 5 anos, metas
  quantificáveis, proibição de prorrogar sem avaliação, e divulgação no Portal
  da Transparência.

### 2.6 Casos verificados

**PL 2/2024 → Lei 14.871/2024 (depreciação acelerada)**

| Data | Evento |
| --- | --- |
| 03/01/2024 | Executivo envia com urgência constitucional (CF 64) |
| 19/03/2024 | Plenário da Câmara aprova (314 × 96), com pareceres dados no próprio Plenário |
| 30/04/2024 | Senado aprova sem mudanças |
| 28/05/2024 | Sanção com veto parcial; DOU de 29/05; vigência na publicação |
| 11/09/2024 | Decreto 12.175 regulamenta o art. 1º I (alterado pelo Decreto 12.292) |
| 12/09 e 11/12/2024 | Portarias interministeriais MDIC/MF 74 e 88 (lista de máquinas) ⚠ fonte secundária |
| 23/10/2024 | PDL 367/2024 pede a sustação do Decreto 12.175; aguarda relator na CAE |
| 08/11/2024 | Decreto 12.242 regulamenta o art. 1º II (navios-tanque) |

**PL 327/2021 → Lei 15.103/2025 (Paten)**

| Data | Evento |
| --- | --- |
| 09/02/2021 | Apresentação |
| 30/04/2021 | Despacho a CMADS, CME e CCJC, **apreciação conclusiva**, regime ordinário |
| 28/11/2023 | Urgência (RICD 155) aprovada: **passa a ir ao Plenário** |
| 19–20/03/2024 | Aprovação no Plenário da Câmara |
| 10/12/2024 | Senado aprova **com emendas**; volta à Câmara |
| 18/12/2024 | Câmara aprova as emendas (448 × 14) |
| 22/01/2025 | Sanção com veto parcial; vigência na publicação |
| 17/06/2025 | VET 8/2025 derrubado; partes promulgadas em 01–02/07/2025 |
| 18/02/2025 | CNPE cria o Comitê Técnico do Paten; instalado em 08/12/2025 ⚠ |

A Lei 15.103 exige decreto para designar órgãos (art. 1º p.ú.) e regulamento
para os critérios (art. 3º §2º), sem prazo. **Não encontramos decreto
regulamentador** em nenhuma das fontes consultadas ⚠. É um estado real e
importante: lei em vigor cujas peças centrais ainda dependem do Executivo.

Também verificados: PL 528/2020 → Lei 14.993/2024; PL 1847/2024 (iniciado no
Senado) → Lei 14.973/2024.

---

## 3. Fontes de dados

### 3.1 Câmara — API v2

Especificação OpenAPI em `https://dadosabertos.camara.leg.br/api/v2/api-docs`.
Respostas trazem `x-total-count` e, sob limite, `retry-after: 30`.

| Endpoint | Usamos? | Valor para o cidadão |
| --- | --- | --- |
| `GET /proposicoes/{id}` → `statusProposicao` (`dataHora`, `sequencia`, `siglaOrgao`, `uriUltimoRelator`, `regime`, `descricaoTramitacao`, `codTipoTramitacao`, `descricaoSituacao`, `codSituacao`, `despacho`, `apreciacao`), `uriPropPrincipal` | Só `descricaoSituacao` e `despacho`, só na criação | **Alto**: onde está, regime, relator, conclusiva ou Plenário |
| `GET /proposicoes/{id}/tramitacoes` | Só em memória | **Alto**: linha do tempo |
| `GET /proposicoes/{id}/relacionadas` | Só em memória | Médio: apensadas, pareceres, emendas |
| `GET /proposicoes/{id}/autores` | Só em memória | Médio |
| `GET /proposicoes/{id}/votacoes` | Sim | Alto: marcos de votação |
| `GET /proposicoes?dataInicio=&dataFim=` | Não | **Alto para sync**: tudo que tramitou na janela (2.113 PL/PLP/PEC/MPV em 23–30/10/2026) |
| `GET /eventos?dataInicio=&dataFim=` + `GET /eventos/{id}/pauta` | Não | **Alto para "o que vem depois"**: "na pauta da CCJC em 03/11". A matéria vem em `proposicaoRelacionada_` (o `proposicao_` costuma ser o parecer) |
| `GET /referencias/proposicoes/codSituacao` (99), `codTipoTramitacao` (235), `codTema`, `siglaTipo`, `codTipoAutor` | Não | Necessário para o mapa de fases. **Sem ordem oficial nem agrupamento por fase** |

O despacho de distribuição já traz o roteiro, em texto livre. Exemplo do PL
4403/2026: *"Às Comissões de Indústria, Comércio e Serviços; Ciência,
Tecnologia e Inovação e Constituição e Justiça e de Cidadania (Art. 54, RICD).
Proposição Sujeita à Apreciação Conclusiva pelas Comissões - Art. 24 II"*.
Lido por um parser, vira "faltam pareceres da CICS, da CCTI e da CCJC".

**Arquivos em massa**, atualizados diariamente:
`https://dadosabertos.camara.leg.br/arquivos/{conjunto}/{formato}/{conjunto}-{ano}.{formato}`.
`proposicoes` traz `ultimoStatus_*`. Existe também `proposicoesTramitacoes`
(35 MB em 2026), **não documentado** e sem `codTipoTramitacao`.

### 3.2 Câmara — armadilhas

1. **A situação de cada linha de `/tramitacoes` não é histórica.** No PL
   2/2024, as 51 linhas — inclusive a de 03/01/2024 — dizem "Transformado em
   Norma Jurídica". A linha do tempo tem de sair de `codTipoTramitacao`,
   `descricaoTramitacao`, `despacho` e `siglaOrgao`.
2. **Ordenar por `sequencia`, não por data.** Muitas linhas têm hora 00:00, e
   a sequência tem lacunas.
3. **O último registro às vezes é um ofício posterior** (nos PLs 327/2021,
   528/2020 e 1847/2024 é um ofício sobre o veto). O marco "virou lei" fica
   numa linha anterior.
4. **Os códigos são inconsistentes.** A remessa ao Senado aparece como
   "Expedição de Documento" ou "Encaminhamento (Plenário)", embora exista
   "Remessa ao Senado".
5. **Cadeias de apensação.** PL 5/2025 → PL 254/2024 → PL 5042/2019 → PL
   5941/2013 (a cabeça, "Pronta para Pauta"). É preciso seguir
   `uriPropPrincipal` até o fim.
6. **O número da lei só está no texto do despacho** ("Transformado na Lei
   Ordinária 14871/2024"). `urnFinal` vem sempre nulo. Um regex sobre o
   despacho acertou 573 de 593 casos em 2024 e 574 de 596 em 2025 (as falhas
   são vetos totais, sem lei, e resoluções da Câmara).
7. **O filtro `codSituacao` de `/proposicoes` parece ignorado** ⚠ (mesmo
   `x-total-count` com e sem o filtro).
8. **O trio sigla-número-ano não é chave.** O PL 1051/2005 aparece na API como
   ano 2026. Usar o `id`.

### 3.3 Senado — API nova

Especificação em `https://legis.senado.leg.br/dadosabertos/v3/api-docs`.

| Necessidade | Endpoint |
| --- | --- |
| Busca | `GET /processo?sigla=&numero=&ano=` (também `numeroNorma`/`anoNorma`) |
| Detalhe | `GET /processo/{id}`: `situacaoAtual`, `siglaSituacaoAtual`, **histórico real de situações com início, fim e colegiado**, `informesLegislativos` (linha do tempo legível), `movimentacoes`, `normaGerada`, `outrosNumeros`, `processosRelacionados` (inclui VET) |
| Prazos | `GET /processo/prazo?idProcesso=` |
| Votos nominais | `GET /votacao?idProcesso=` |
| Tipos de situação | `GET /processo/tipos-situacao` (175) |
| Agenda | `/plenario/agenda/dia/{data}`, `/comissao/agenda/{ini}/{fim}` |
| Vetos | `/processo?sigla=VET&numero=&ano=` |

Ao contrário da Câmara, o Senado tem histórico de situação de verdade.
Exemplo, PL 327/2021 no Senado (`/processo/8638658`):

```json
{"objetivo": "Revisora", "siglaCasaIniciadora": "CD",
 "siglaSituacaoAtual": "TNJRVETO",
 "normaGerada": {"numero": 15103, "dataAssinatura": "2025-01-22", "dataPublicacao": "2025-01-23"},
 "processosRelacionados": [{"tipoRelacao": "VETO", "sigla": "VET", "numero": "8", "ano": 2025}]}
```

**Câmara ↔ Senado:** desde a numeração unificada, o PL tem o mesmo número nas
duas Casas, e `/processo?sigla=PL&numero=&ano=` encontrou os quatro casos de
§2.6. `outrosNumeros` resolve projetos antigos (PL 1051/2026 ← PLS 102/2004).

### 3.4 Depois da lei

| Fonte | O que oferece | Limites |
| --- | --- | --- |
| Senado `GET /legislacao/{tipo}/{num}/{ano}` | `vides` por dispositivo, incluindo **"Declaração de Regulamentação Permanente de Norma"** (Lei 14.871, art. 1º I → Decreto 12.175). **É o único vínculo lei → decreto estruturado que encontramos** | Curadoria manual do Senado, com atraso; não cobre portarias |
| normas.leg.br `GET /api/public/normas?urn=…` | JSON-LD (schema.org `Legislation`, CC-BY 4.0) com o processo de origem, alterações e texto por dispositivo. Link canônico: `normas.leg.br/?urn=urn:lex:br:federal:lei:2025-01-22;15103` | **Sem documentação oficial** — achado no código do `br-eli-mcp` |
| Planalto (textos compilados) | Links "Regulamento" dentro dos dispositivos | HTML, sem API; timeout a partir de fora do Brasil |
| LexML (SRU) | Busca de normas | Atrás de desafio anti-robô; não usar em automação |
| DOU / INLABS | Edições completas em XML | Exige login; só os últimos 4 meses |
| Receita — painel de benefícios fiscais (DIRBI) | Renúncia por setor, CNPJ, UF | ⚠ não confirmamos se a depreciação acelerada aparece |
| Portal da Transparência / SIOP | Execução por programa e ação | Exige chave; vínculo lei → ação não é estruturado; benefício tributário é renúncia, não despesa |
| CMAP, TCU, avaliações do Senado (RISF 96-B) | Avaliações ex post | Amostra pequena, PDF, irregular |
| IBGE SIDRA, Ipeadata | Indicadores | Atribuir efeito exige avaliação |
| Base dos Dados | Câmara e Senado no BigQuery | Sem tramitações da Câmara; exige projeto GCP |
| Querido Diário | Diários municipais | Não serve para o DOU |

### 3.5 Bibliotecas e MCPs

Não há MCP oficial da Câmara, do Senado ou do Congresso.

| Projeto | Mantenedor | Último push | O que cobre | Avaliação |
| --- | --- | --- | --- | --- |
| [Mcp-Brasil/mcp-brasil](https://github.com/Mcp-Brasil/mcp-brasil) | organização, 7 contribuidores, 1.844★ | 19/09/2026 | 70 APIs; Câmara (inclui tramitações), Senado, DOU | Estrelas altas para um repositório de 7 meses — tratar com ceticismo. **Usa o `/materia` depreciado do Senado.** Roda local, só leitura |
| [senado-br-mcp](https://github.com/SidneyBissoli/senado-br-mcp-cloudflare) | pessoa física | 30/10/2026 | 69 ferramentas; usa o `/processo` novo; vetos | Ativo. A versão hospedada passa os dados por terceiro — usar `npx` local |
| [br-eli-mcp](https://github.com/matematicsolutions/br-eli-mcp) | organização | 08/10/2026 | Câmara, Senado `/legislacao`, normas.leg.br | Bom como referência de endpoints; muito novo |
| [cristianoaredes/mcp-senado](https://github.com/cristianoaredes/mcp-senado) | pessoa física | 06/04/2026 | `/materia/*` | Provavelmente quebrado após o sunset |
| [DadosAbertosBrasil](https://github.com/GusFurtado/DadosAbertosBrasil) (PyPI) | pessoa física, 132★ | 26/10/2026 | Câmara (inclui tramitações) e Senado | A biblioteca Python mais saudável ⚠ não confirmamos a migração para `/processo` |
| congressbr, rcongresso (R), py-lexml-acervo | — | 2020–2022 | — | Parados |

### 3.6 Recomendação

Chamar as APIs oficiais diretamente — elas são poucas, estáveis o bastante e
o ZIL já tem clientes para elas. Um MCP comunitário adiciona uma dependência
de terceiro entre a fonte e o dado publicado, o que vai contra o princípio de
auditabilidade. Para **exploração em desenvolvimento**, `senado-br-mcp`
(endpoints novos, rodando local) e `br-eli-mcp` (normas.leg.br) são os mais
úteis; `mcp-brasil` serve para a Câmara, não para o Senado.

---

## 4. Modelo de fases

### 4.1 Dois eixos e um desfecho

Uma barra única de "progresso até a lei" não funciona: muitos dispositivos
valem sem regulamento, e "Regulamentada" como 8ª etapa faria toda lei
autoaplicável parecer incompleta. A proposta separa três coisas:

- **`fase`** — onde está na tramitação. Linear, com ramificações.
- **`pos_lei`** — vigência, vetos, regulamentação. Atributo, não etapa.
- **`desfecho`** — terminal. Quando existe, a fase passa a ser lida como
  "onde parou".

| `fase` | Rótulo | Responde |
| --- | --- | --- |
| `apresentada` | Apresentada | Ainda não foi distribuída às comissões |
| `comissoes` | Nas comissões (MPV: "Na comissão mista") | Quem analisa e dá parecer |
| `plenario` | No Plenário da Câmara / do Senado | Aguarda ou está em votação geral |
| `outra_casa` | No Senado / Na Câmara (sempre o nome concreto) | A segunda Casa analisa |
| `retorno` | De volta à Câmara / ao Senado | A Casa de origem só aceita ou rejeita as emendas |
| `sancao` | Com o Presidente da República | Sanção ou veto |
| `veto_congresso` | Veto em análise no Congresso | Só para veto total |
| `promulgacao` | Promulgação | PEC, PDL, veto derrubado, MPV sem alteração |
| `norma` | Virou lei / emenda constitucional / decreto legislativo / "Convertida em lei" (MPV) | — |

Desfechos: `arquivada` (com o motivo; desarquivamento por requerimento só existe no
Senado, RISF 332 — na Câmara o antigo parágrafo único do RICD 105 foi revogado
pela RCD 33/2022), `retirada`,
`prejudicada`, `rejeitada`, `perdeu_eficacia`, `vetada` (veto total mantido),
`devolvida`. Estado não terminal: `apensada` — "Tramita junto com X", herdando
a fase da cabeça da cadeia. Fallback: `nao_sabemos`, sempre com um motivo
(`situacao_sem_mapa`, `sinais_conflitantes`, `principal_nao_resolvida`,
`fonte_indisponivel`, `especie_fora_do_escopo`).

### 4.2 Ritos por espécie

| Espécie | Etapas (Câmara iniciadora; inverte se for o Senado) | Particularidades |
| --- | --- | --- |
| PL | apresentada → comissões → plenário\* → Senado → [retorno] → sanção → norma | \*Conclusiva: o Plenário aparece como "pulada", salvo recurso |
| PLP | como o PL, sempre com Plenário | Maioria absoluta |
| PEC | apresentada → comissões (CCJC + especial) → plenário (2 turnos, 3/5) → outra Casa → promulgação → emenda constitucional | Sem sanção |
| MPV | (já vale) → comissão mista → Plenário da Câmara → Senado → sanção (se virou PLV) ou promulgação → lei de conversão | Relógio de 60 + 60 dias; desfecho `perdeu_eficacia` |
| PDL | apresentada → comissões → plenário → outra Casa → promulgação → decreto legislativo | Sem sanção; PDL de sustação aponta para um decreto |
| PLN | — | `nao_sabemos(especie_fora_do_escopo)` |

### 4.3 Derivação determinística

Uma função pura, `derivar_fase(entrada, mapa)`, recebe o `statusProposicao`
da Câmara, os marcos da tramitação, o processo do Senado (se houver), a
espécie, a Casa iniciadora e a cabeça da cadeia de apensação. A primeira regra
que casa vence, e o identificador da regra fica gravado junto com a versão do
mapa:

| # | Regra | Por que nesta ordem |
| --- | --- | --- |
| R1 | `normaGerada` do Senado, **ou** qualquer marco de "transformação em norma" no histórico, ou situação "Transformado em Norma Jurídica" → `norma` | O último registro pode ser um ofício; o marco é irreversível |
| R2 | Marco terminal mais recente que o último marco não terminal (prejudicialidade, retirada, arquivamento sem desarquivamento) → desfecho | Resolve "Aguardando Encaminhamento" com despacho de prejudicialidade |
| R3 | Situação terminal (Arquivada, Retirado, Perdeu a Eficácia) → desfecho | — |
| R4 | Tramitando em Conjunto / Aguardando Apensação / `uriPropPrincipal` preenchido → resolver a cadeia (até 10 níveis, com detecção de ciclo) → herdar a fase | — |
| R5 | Processo ativo no Senado → regras por `siglaSituacaoAtual` | Sem processo do Senado, "Aguardando Apreciação pelo Senado Federal" → `outra_casa`, sem órgão |
| R6 | Aguardando Sanção → `sancao` | — |
| R7 | Órgão = PLEN → `plenario`; comissão permanente, especial ou mista → `comissoes` | É o que resolve "Pronta para Pauta" e "Aguardando Parecer" |
| R8 | Situações pré-despacho (Chancela, Autorização, Ag. Análise de Inconstitucionalidade, Aguardando Autorização do Despacho) → `apresentada` | — |
| R9 | Situação nula, sem marco de distribuição, apresentada há ≤ 90 dias → `apresentada` (motivo `recem_apresentada`) | 29% dos PLs de 2026 |
| R10 | Qualquer outro caso → `nao_sabemos`, com motivo | Nunca um palpite |

### 4.4 O mapa como dado versionado

Em `data/tramitacao/`, no mesmo espírito de `data/direcoes/`:

- `fases.yml` — fases, desfechos, regras R1–R10 para Câmara e Senado, `versao`.
- `marcos.yml` — `codTipoTramitacao` → marco + título em linguagem simples
  (apresentação 100; distribuição 110/112; apensação 106/129/504; relator 320;
  parecer 322/336; urgência 196; Plenário 1231/1235/1236/1243; Senado
  128/1518/1519; sanção 127/609; norma 251/1012/1013; fim 502/200/620).
- `glossario.yml` — situação → explicação, marcada como "texto do ZIL, não
  oficial". Inclui regimes (art. 155, 151 II e III, CF 64) e apreciação
  (art. 24 II).
- `ritos.yml` — nós e arestas por espécie, com base legal e classe do prazo
  (D, D\*, X).
- `referencias/` — cópias datadas das tabelas de código da Câmara e do Senado.

Testes: **cobertura** (todo código das tabelas está numa regra ou numa lista
`nao_mapeados` com motivo; senão a CI falha), **golden fixtures** com
respostas reais gravadas (Apêndice B) e **determinismo**. Validador offline
`scripts/validar_tramitacao.py`, como o `validar_direcoes.py`.

---

## 5. Dados e pipeline

### 5.1 Modelo

Novas colunas em `Proposicao`, todas nulas:

- fase: `fase`, `desfecho`, `fase_motivo`, `fase_regra`, `fase_mapa_versao`,
  `fase_desde`, `fase_herdada_de_id`;
- status: `cod_situacao`, `sigla_orgao`, `cod_tipo_tramitacao`, `regime`,
  `apreciacao`, `despacho_distribuicao`, `rota_prevista` (JSON);
- relator: `relator_nome`, `relator_uri`, `relator_parlamentar_id`;
- cadeia: `principal_fonte_id`, `principal_id`, `cabeca_id`;
- Senado: `casa_iniciadora`, `senado_processo_id`, `senado_sigla_situacao`;
- `norma_id`; `ultima_movimentacao_em`, `detalhe_sincronizado_em`.

A coluna `tramitacoes` (JSON, sempre vazia) é deprecada.

Tabelas novas:

| Tabela | Conteúdo |
| --- | --- |
| `tramitacoes` | Um registro por evento: `casa`, `chave` (sequência na Câmara, id no Senado), `sequencia`, `data_hora`, `sigla_orgao`, `cod_tipo`, `descricao`, `despacho`, `url`, `tipo_registro` (movimentação, situação, informe), `marco`. **Sem `codSituacao` por linha na Câmara** (não é histórico); o histórico de situação do Senado entra com início e fim |
| `agenda_itens` | Proposição na pauta de um evento: casa, evento, início, órgão, situação do evento, url |
| `normas` | Leis e decretos: tipo, número, ano, datas, URN, links (normas.leg.br, Planalto), origem, `fonte_dado` (Senado, regex do despacho, curadoria), `verificado_em` |
| `vetos` | VET n/aaaa, tipo, data, estado (mantido, derrubado), deliberação |
| `regulamentacoes` | Lei → ato, dispositivo, relação (regulamenta, altera, pede sustação), fonte (vide do Senado, curadoria), evidência, `verificado_em` |

A curadoria pós-lei mora em `data/normas/*.yml`, com validador e
`apply_normas.py`, seguindo o padrão de `apply_direcoes.py`.

### 5.2 Sincronização

Um passo `tramitacao` no job diário de `scripts/agenda.py` (PR #47), depois
de `proposicoes`, registrado em `ingestion_runs`:

1. **O que mudou:** `/proposicoes?dataInicio=D-7&siglaTipo=PL,PLP,PEC,MPV,PDL`
   (~22 páginas), cruzado com as proposições acompanhadas e as cabeças das
   cadeias.
2. **Para cada uma:** `GET /proposicoes/{id}` + `/tramitacoes`; upsert por
   `chave`; recalcular a fase; refazer a cadeia se `uriPropPrincipal` mudou.
3. **Senado:** se a fase for `outra_casa`, `sancao` ou `norma`, ou se começou
   no Senado: `/processo?…` → `/processo/{id}`.
4. **Agenda:** `/eventos` dos próximos 14 dias nos órgãos onde estão as
   proposições acompanhadas → `/eventos/{id}/pauta`; no Senado, agenda de
   comissões e Plenário.
5. **Reconciliação semanal**, com os cadastros: todas as proposições (≈ 240 ×
   2 chamadas, ~4 minutos).

As duas causas na raiz (§1.2) se resolvem com uma função única,
`registrar_proposicao(db, fonte_id)`, que **sempre** busca o detalhe e
substitui os caminhos de `sync_votacoes_zil.py` e `_upsert_proposicao`; e com
o passo 2, que atualiza a cada dia. O `CamaraClient` passa a respeitar
`Retry-After` (hoje aplica backoff próprio, `packages/camara_client/__init__.py:104-126`).
O `senado_client` migra para `/processo*`, `/votacao`, `/processo/prazo` e
`/legislacao`. O pipeline de explicação passa a ler a tabela `tramitacoes`.

### 5.3 Contrato da API

- `ProposicaoRead` ganha `fase`, `fase_rotulo`, `desfecho`, `sigla_orgao`,
  `ultima_movimentacao_em` e o resumo da norma.
- `GET /proposicoes/{id}/tramitacao` → `onde_esta` (fase, casa, órgão, desde,
  situação oficial, regime e apreciação em texto simples, relator,
  `herdada_de`, `como_sabemos{regra, mapa_versao, fontes, conferido_em}`),
  `etapas[]`, `proximos{previstas, agendadas, prazos}`, `marcos[]`,
  `eventos_total`.
- `GET /proposicoes/{id}/tramitacao/eventos?page=` — todos os registros.
- `GET /proposicoes/{id}/norma` → norma, vetos, regulamentação (`estado`:
  `nao_verificada`, `sem_regulamentacao_conhecida`, `com_atos_vinculados`,
  `autoaplicavel_declarada`), execução, avaliações.
- `GET /tramitacao/mapa` — fases, ritos e glossário, para a página explicativa.
- `GET /proposicoes?fase=&desfecho=&ordem=movimentacao`.

O frontend não deriva fase nenhuma: só exibe o que a API devolve.

---

## 6. Apresentação

### 6.1 As perguntas da página, na ordem

O resumo em linguagem simples vem logo depois do título: sem saber o que a
proposição propõe, a fase não diz nada.

1. **Cabeçalho** — chapéu ("Projeto de lei · iniciado na Câmara"), número,
   **Selo de fase** (neutro, com link para a explicação da fase), categorias.
   A situação oficial sai do Selo, onde hoje é truncada.
2. **Em linguagem simples** (existente).
3. **Onde está agora** — uma frase montada por template a partir do mapa,
   nunca por LLM (exemplo): *"Nas comissões da Câmara. Está na Comissão de Minas e
   Energia (CME) desde 12/03/2025, aguardando o parecer do relator."* Abaixo,
   as `Etapas` compactas; a forma de apreciação em linguagem simples ("as
   comissões decidem sem passar pelo Plenário, salvo recurso"); a situação
   oficial com a data da conferência e "Ver na Câmara ↗"; um `<details>`
   "Como sabemos" com a regra, a versão do mapa e o endpoint. Se apensada:
   *"Tramita junto com o PL 5941/2013, o principal. O que acontecer com ele
   vale para esta."*
4. **O que vem depois** — uma de quatro formas:
   - *prevista pelo rito*, com a rota do despacho: "Faltam pareceres da CME e
     da CCJC. Depois, segue ao Senado se 52 deputados não recorrerem em 5
     sessões";
   - *agendada*: "Na pauta da CME em 04/11/2026, 10h ↗ — estar na pauta não
     garante votação";
   - *prazo correndo*, só para prazos D com início oficial: "Sanção: 15 dias
     úteis a partir de dd/mm; sem resposta, a sanção é tácita (CF 66 §3º)".
     Sem calendário de feriados confiável, não se calcula a data final;
   - *nada disso*: "Não há data prevista. Quem decide quando a proposição anda
     é a presidência da comissão ou da Casa; o ZIL não estima datas."
5. **O que aconteceu** — `LinhaDoTempo` com até 8 marcos (votações viram
   marcos com link para `/votacoes/{id}`), e um `<details>` com todos os
   registros, no texto original.
6. **O caminho inteiro** — `Etapas` verticais com as ramificações e a base
   legal de cada etapa; link para "Como uma proposição vira lei".
7. **Depois da lei** (quando houver) — número e data, links (normas.leg.br,
   Planalto); vetos e derrubadas; regulamentação (atos ligados, cada um com
   fonte); contestação (ex.: PDL 367/2024 contra o Decreto 12.175); execução
   e avaliação quando existirem.
8. **Votações** (existente). 9. **Proposições ligadas** (principal,
   apensadas, número no Senado). 10. **Quem propôs e quem relata** (o link
   para `/parlamentar` só com o ranking público). 11. Ementa técnica e
   contexto completo (existentes).

Esboço a 375px:

```
┌───────────────────────────────────┐
│ PROJETO DE LEI · INICIADO NA CÂMARA│
│ PL 2/2024                          │
│ (● Virou lei)  Indústria           │
├───────────────────────────────────┤
│ Em linguagem simples               │
│ Permite que empresas descontem...  │
├───────────────────────────────────┤
│ Onde está agora                    │
│ Virou a Lei 14.871, de 28/05/2024. │
│ ▬▬ ▬▬ ▬▬ ▬▬ ▬▬ ▬▬  (6 de 6)        │
│ Situação oficial: Transformado em  │
│ Norma Jurídica · conferida 30/10   │
│ Ver na Câmara ↗   ▸ Como sabemos   │
├───────────────────────────────────┤
│ Depois da lei                      │
│ Veto parcial (art. 5º)             │
│ Regulamentada por:                 │
│  · Decreto 12.175/2024 (art. 1º I) │
│  · Decreto 12.242/2024 (art. 1º II)│
│ Contestada: PDL 367/2024 ↗         │
│ Fontes: Senado (vides) · 30/10     │
├───────────────────────────────────┤
│ O que aconteceu                    │
│ ○ 03/01/24 Enviado pelo Executivo  │
│ ○ 19/03/24 Aprovado na Câmara 314×96│
│ ○ 30/04/24 Aprovado no Senado      │
│ ● 28/05/24 Sancionado com veto     │
│ ▸ Todos os 51 registros            │
└───────────────────────────────────┘
```

### 6.2 Estados e textos

| Estado | Texto |
| --- | --- |
| Situação nula e recente | "Recém-apresentada, aguardando despacho. A Câmara ainda não informou situação." |
| `nao_sabemos` | "Não sabemos em que fase está. A situação oficial é 'X', que ainda não está no nosso mapa (v1). Ver na Câmara ↗" |
| Arquivada | "Arquivada em dd/mm." + o motivo, quando o despacho o disser. Não prometer desarquivamento: na Câmara ele deixou de existir com a RCD 33/2022; no Senado depende de requerimento de 1/3 (RISF 332) |
| Sem regulamentação conhecida | "Consultamos [Senado — vides; curadoria ZIL] em dd/mm/aaaa e não encontramos decreto vinculado. Isso não quer dizer que a lei não seja aplicada: muitos artigos valem sem regulamento." |
| Regulamentação não verificada | "Ainda não verificamos a regulamentação desta lei." |

### 6.3 Lista, página explicativa e glossário

- **`/proposicoes`**: Selo de fase e "Última movimentação em dd/mm" em cada
  cartão; filtro por fase com contagem (Antes das comissões, Nas comissões,
  No Plenário, Na outra Casa, Com o Presidente, Virou norma, Encerradas);
  ordenação "Movimentadas recentemente".
- **`/como-vira-lei`**: diagrama do rito gerado de `ritos.yml`, com
  `Segmentado` de espécie e de Casa iniciadora, vertical no celular. Cada
  etapa: o que acontece, base legal, classe do prazo explicada ("previsto em
  norma, mas costuma não ser cumprido") e "N proposições acompanhadas estão
  aqui agora →". Desfechos como ramos laterais. Seção "Depois da lei".
  Âncoras por fase, linkadas do Selo.
- **`/como-vira-lei/situacoes`**: situação oficial → explicação do ZIL →
  fase. Começa pelas 16 situações presentes no banco; as demais aparecem como
  "sem explicação ainda".

### 6.4 O que falta no kit

`Etapas` precisa dos estados `pulada` e `interrompida`, da Casa por etapa,
de orientação vertical abaixo de `md` (7 etapas × 120px rolam 840px no
celular), de `aria-label` ("Etapa 3 de 6: Nas comissões") e de
`motion-reduce:animate-none` — ou de perder a animação contínua. Componentes
de domínio: `FaseSelo`, `OndeEsta`, `ProximosPassos`, `TramitacaoLinha`,
`DepoisDaLei`, `RitoDiagrama`.

### 6.5 O que a UI não deve fazer

- Verde ou vermelho para fase — essas cores dizem alinhamento no ZIL.
- "% concluída", ou uma barra que trate regulamentação como etapa.
- "Parada há N dias" como alarme; use "última movimentação em".
- Datas previstas; "deve ser votada em breve".
- "Lei não regulamentada" como acusação.
- Situação oficial truncada.
- Texto de status gerado por LLM.

---

## 7. Impacto e sucesso

A pergunta "a lei funcionou?" tem uma resposta honesta em degraus:

| Nível | O que mostrar | Fonte | Condição |
| --- | --- | --- | --- |
| N0 Virou norma? | Sim ou não, número, data | Câmara e Senado | Determinístico |
| N1 Implementação | Vigência, vetos e derrubadas, dispositivos que mencionam regulamento (marcados como *indicativo*), atos ligados | Vides do Senado + curadoria | `verificado_em` sempre visível |
| N2 Execução | Renúncia ou gasto, só com vínculo 1:1 identificável (ex.: Lei 14.871 no painel de benefícios da Receita); metas da LC 224/2025 quando a lei tiver benefício fiscal | Receita, SIOP, Portal da Transparência | Série com URL; nunca estimativa |
| N3 Avaliação | A conclusão de uma avaliação, citada, com link | CMAP, TCU, Senado, IPEA | O ZIL relata, não avalia |
| N4 Contexto | O indicador da Bússola da mesma pauta | `data/bussula` | Rótulo fixo: "contexto, não efeito da lei" |

**O que não fazer:** "score de sucesso" de lei; linguagem causal ("graças à
lei", "resultou em") — o validador de `data/normas` deve barrar; gráfico de
antes e depois com uma linha na data da lei; contar decretos como sinal de
sucesso; tratar ausência de regulamento como descumprimento; LLM afirmando
execução; qualquer efeito sobre o Score ZIL.

---

## 8. Plano por fases

| Fase | O que entra | Critério de aceite |
| --- | --- | --- |
| **F0 Honestidade** (pequena) | `registrar_proposicao` sempre busca o detalhe; passo diário que atualiza situação, órgão, regime, apreciação e última movimentação; número da lei pelo despacho; na página, situação em texto (fora do Selo), órgão, "desde", "Ver na Câmara ↗", texto de recém-apresentada | As 5 do placar com situação correta; situação nula só quando a API devolve nula; link para a Câmara em 100% das proposições da Câmara; teste garantindo que criar a partir de votação busca o detalhe |
| **F1 Fases e linha do tempo** (média) | `data/tramitacao/*`, derivação de fase, tabela `tramitacoes`, endpoints, Onde está + Etapas + O que aconteceu (PL e PLP primeiro), Selo e filtro de fase na lista | Teste de cobertura verde; ≥ 12 golden fixtures; `nao_sabemos` < 5% das acompanhadas; toda fase com "Como sabemos"; janela D-7 em < 5 min |
| **F2 Próximos passos e explicação** (média) | Parser do despacho (rota e parecer), agenda, prazos D oficiais, `/como-vira-lei`, glossário | Parser cobre ≥ 90% dos despachos de distribuição, o resto como "rota não identificada"; nenhuma data sem evento ou prazo legal com fonte; toda etapa do rito com artigo |
| **F3 Senado e norma** (média) | Migração do `senado_client`, vínculo Câmara ↔ Senado, `normas` e `vetos`, bloco Depois da lei | Leis 14.871, 15.103, 14.993 e 14.973 conferidas à mão; zero chamadas a `/materia`; falha do Senado não derruba o passo da Câmara |
| **F4 Regulamentação** (média, com curadoria) | `data/normas/*.yml`, vides do Senado, estados de regulamentação | Lei 14.871 mostra os Decretos 12.175 e 12.242 e o PDL 367/2024; Lei 15.103 mostra "sem regulamentação conhecida" com as fontes; todo vínculo com fonte e data |
| **F5 Execução e avaliação** (pequena a média) | Os níveis N2–N4 de §7 | Nenhum número sem série ou URL; validador barra linguagem causal |

F0 é pequena e corrige o que hoje está errado nas páginas mais visíveis do
site. As outras dependem do PR #47 (o cron), porque o passo diário vive em
`scripts/agenda.py`.

### Decisões que são da maintainer

1. O conjunto e os nomes das fases ("Na outra Casa" ou o nome concreto;
   "Virou lei" ou "Transformada em lei").
2. Apensadas: página própria com fase herdada (recomendado) ou redirecionar
   para a principal; e se cabeças fora das pautas ZIL passam a ser
   acompanhadas.
3. Descobrir proposições que começam no Senado.
4. Quais leis recebem curadoria pós-lei. Recomendação: só as do placar.
5. Revisão do glossário — é texto editorial; idealmente com alguém de
   formação legislativa.
6. Manter ou tirar a animação do `Etapas`.
7. Uma spec nova (`specs/013-tramitacao/`) substituindo F-001, F-003, F-007 e
   F-008 da spec 012; F-002, F-004 a F-006 continuam valendo.

---

## 9. Lacunas e incertezas

- **API da Câmara:** situação por linha não histórica; último registro às
  vezes é ofício; lacunas de sequência; `urnFinal` nulo; filtro `codSituacao`
  aparentemente ignorado ⚠; semântica exata de `dataInicio` a confirmar ⚠.
- **API do Senado:** a família `/processo` é nova e pode mudar.
- **Tabelas de código mudam:** mitigado com cópia datada, teste de cobertura
  e diferença semanal; código desconhecido vira `nao_sabemos`, não erro.
- **Etapas discricionárias:** o texto de "próximo passo" pode soar como
  cobrança. Precisa de revisão editorial.
- **Cadeias de apensação:** ciclos, cabeça fora das pautas acompanhadas,
  cabeça no Senado.
- **Numeração:** PEC fatiada, MPV → PLV, projetos anteriores a 2019.
- **Curadoria pós-lei** pesa para uma maintainer só: escopo limitado e
  `verificado_em` sempre visível.
- **Fontes bloqueadas:** Planalto dá timeout de fora do Brasil (os runners do
  GitHub Actions ficam nos EUA, então ele não entra no cron); LexML tem
  anti-robô; INLABS exige login; a API de normas.leg.br não é documentada.
- **Dias úteis:** sem calendário de feriados confiável, não calcular datas
  finais.
- **Pontos ⚠ deste documento:** portarias da
  Lei 14.871 (fonte secundária); comitê técnico do Paten (fonte de notícia);
  inexistência de decreto da Lei 15.103 (ausência nas fontes consultadas não
  prova ausência); presença da depreciação acelerada no painel da Receita;
  migração da DadosAbertosBrasil para `/processo`; números do banco são do
  ambiente de desenvolvimento.

---

## Apêndice A — situações do banco → fase proposta

| Situação | Fase / desfecho | Regra |
| --- | --- | --- |
| Aguardando Parecer | `comissoes` | R7 |
| Aguardando Designação de Relator(a) | `comissoes` | R7 |
| Aguardando Designação - Aguardando Devolução de Relator(a)… | `comissoes` | R7 |
| Pronta para Pauta | `comissoes` ou `plenario`, pelo órgão | R7 |
| Tramitando em Conjunto | `apensada` → fase da cabeça | R4 |
| Aguardando Apensação | `apensada` → fase da cabeça | R4 |
| Arquivada | desfecho `arquivada` | R3 |
| Retirado pelo(a) Autor(a) | desfecho `retirada` | R3 |
| Perdeu a Eficácia | desfecho `perdeu_eficacia` | R3 |
| Transformado em Norma Jurídica | `norma` | R1 |
| Aguardando Apreciação pelo Senado Federal | `outra_casa` | R5 |
| Aguardando Despacho do Presidente da Câmara dos Deputados (Chancela) | `apresentada` | R8 |
| Aguardando Despacho do Presidente da Câmara dos Deputados (Autorização) | `apresentada` | R8 |
| Ag. Análise de Inconstitucionalidade | `apresentada` | R8 |
| Aguardando Autorização do Despacho | `apresentada` | R8 |
| Aguardando Encaminhamento | depende do despacho: desfecho por R2 quando há marco terminal; senão `nao_sabemos(sinais_conflitantes)` | R2 / R10 |
| *(nula)* | `apresentada` se recente e sem distribuição; senão marcos (R1, R2) ou `nao_sabemos` | R9 / R10 |

## Apêndice B — golden fixtures

Respostas reais gravadas, uma por caso difícil: PL 327/2021 (conclusiva que
virou Plenário, emendas do Senado, veto derrubado), PL 2/2024 (urgência
constitucional, veto parcial, decretos), PL 528/2020, PL 1847/2024 (iniciado
no Senado), PL 1264/2024 (comissão, sem relator), PL 4272/2023 ("Aguardando
Encaminhamento" com prejudicialidade), PL 5/2025 (cadeia de apensação de 4
níveis), PL 278/2026 (situação atrasada em relação ao marco de norma), um PDL
em "Chancela", uma MPV que perdeu a eficácia, PL 359/2025 (pauta em comissão
com parecer pela rejeição), um PL de 2026 com situação nula.

---

## Fontes

Normas: [Constituição](https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm) ·
[RICD](https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html) ·
[RCD 33/2022](https://www2.camara.leg.br/legin/int/rescad/2022/resolucaodacamaradosdeputados-33-4-agosto-2022-793091-publicacaooriginal-165882-pl.html) ·
[RISF](https://legis.senado.leg.br/norma/563958/publicacao/16433779) ·
[RCN 1/2002](https://www2.camara.leg.br/legin/fed/rescon/2002/resolucao-1-8-maio-2002-497942-normaatualizada-pl.html) ·
[LC 95/1998](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp95.htm) ·
[LINDB](https://www.planalto.gov.br/ccivil_03/decreto-lei/del4657compilado.htm) ·
[Decreto 12.002/2024](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/D12002.htm) ·
[Decreto 10.411/2020](https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/decreto/D10411.htm) ·
[LC 224/2025](https://www.planalto.gov.br/ccivil_03/LEIS/LCP/Lcp224.htm)

Processo: [Entenda o processo legislativo (Câmara)](https://www.camara.leg.br/entenda-o-processo-legislativo/) ·
[Tramitação de MPV](https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria) ·
[Tramitação do veto](https://www.congressonacional.leg.br/materias/vetos/entenda-a-tramitacao-do-veto) ·
[Glossário legislativo](https://www.congressonacional.leg.br/legislacao-e-publicacoes/glossario-legislativo) ·
[STF, MS 27.931](https://noticias.stf.jus.br/?p=42494)

Leis e casos: [Lei 14.871](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/L14871.htm) ·
[Lei 15.103](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/L15103.htm) ·
[Lei 14.990](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/L14990.htm) ·
[Decreto 12.175](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/D12175.htm) ·
[Decreto 12.242](https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/D12242.htm) ·
[PDL 367/2024](https://www25.senado.leg.br/web/atividade/materias/-/materia/165873) ·
[PL 327/2021 no Senado](https://www25.senado.leg.br/web/atividade/materias/-/materia/162766) ·
[CNPE cria o CT-Paten](https://www.gov.br/mme/pt-br/assuntos/noticias/2023-2026/cnpe-cria-comite-tecnico-do-paten-para-revolucionar-a-transicao-energetica-no-brasil)

APIs: [Câmara — OpenAPI](https://dadosabertos.camara.leg.br/api/v2/api-docs) ·
[Câmara — codSituacao](https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao) ·
[Câmara — codTipoTramitacao](https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codTipoTramitacao) ·
[PL 2/2024 — tramitações](https://dadosabertos.camara.leg.br/api/v2/proposicoes/2416804/tramitacoes) ·
[PL 327/2021 — tramitações](https://dadosabertos.camara.leg.br/api/v2/proposicoes/2269745/tramitacoes) ·
[Senado — OpenAPI](https://legis.senado.leg.br/dadosabertos/v3/api-docs) ·
[Senado — tipos de situação](https://legis.senado.leg.br/dadosabertos/processo/tipos-situacao) ·
[Senado — legislação, Lei 15.103](https://legis.senado.leg.br/dadosabertos/legislacao/LEI/15103/2025) ·
[normas.leg.br — Lei 15.103](https://normas.leg.br/?urn=urn:lex:br:federal:lei:2025-01-22;15103) ·
[Imprensa Nacional / INLABS](https://github.com/Imprensa-Nacional) ·
[IBGE — API de agregados](https://servicodados.ibge.gov.br/api/docs/agregados?versao=3) ·
[Querido Diário](https://queridodiario.org.br/)

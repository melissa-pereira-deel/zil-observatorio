# Backlog 013 — Dados, motor de fases e API (Arquitetura)

**Dono:** Software Architecture · **Data:** 2026-10-30 · **Estado:** proposta para revisão da maintainer
**Fontes:** `docs/DISCOVERY-TRAMITACAO.md` (citado como "disc. §x"), `specs/013-tramitacao/spec.md`
(processo de revisão TRM-023, índice, ondas — citado como "spec §x"), código do repositório no
branch `049-discovery-tramitacao`, e chamadas de leitura às APIs da Câmara e do Senado feitas em
2026-10-30 (registradas abaixo como **"conferido ao vivo"**).

Este arquivo especifica as tarefas de dados, motor e API: **TRM-002, 010, 011, 012, 013, 014,
020, 021, 024, 025, 026, 027, 028** (Agora) e **TRM-050, 051, 052, 053** (Depois). Não cria
tarefa nova: a ligação do sync ao cron (`scripts/agenda.py`, PR #47) é o último passo de TRM-012,
como o PM já registrou (spec §5.3).

---

## 0. Convenções para quem implementa

- **Comandos** (da raiz do repositório):
  - testes: `.venv/bin/python -m pytest tests/ -q` (focado: `.venv/bin/python -m pytest tests/unit/test_x.py -v`)
  - lint (o que a CI roda): `.venv/bin/ruff check apps/ packages/`; arquivos novos em `scripts/`
    também passam por `.venv/bin/ruff check scripts/<arquivo>.py` (a CI não cobre `scripts/`, mas
    não introduza erro novo).
  - validador do mapa: `.venv/bin/python scripts/validar_tramitacao.py` (TRM-024).
- **Imports** (ADR-002): dentro de `apps/api`, imports curtos (`from models import Proposicao`).
  Scripts e workers põem a raiz e `apps/api` no `sys.path`, como `scripts/discover_proposicoes.py:23-28`.
- **Tipos cross-DB** (ADR-001): `String`, `Integer`, `Date`, `DateTime`, `JSON`, `Uuid`. Nada de
  `JSONB`, `ARRAY`, `UUID` do Postgres. `JSON(none_as_null=True)` em coluna que pode ser filtrada
  por `IS NOT NULL` (ADR-003).
- **Código de domínio puro mora em `packages/tramitacao/`** (sem banco, sem rede). Motivo: a API
  roda em `/app` com `apps/api` achatado, `apps/workers` copiado para `/app/workers` e `packages/`
  para `/app/packages` (`apps/api/Dockerfile`). `packages.tramitacao` resolve igual no repositório,
  nos testes e no container; `apps.workers.*` não existe dentro do container da API e `workers.*`
  não existe nos testes. Orquestração com banco e rede mora em `apps/workers/tramitacao/`.
- **Dados editoriais** em `data/tramitacao/`. O loader resolve o diretório assim, nesta ordem:
  variável `ZIL_DATA_DIR` (se definida) + `/tramitacao`; `Path(__file__).resolve().parents[2] /
  "data" / "tramitacao"` (repositório); `Path("/data/tramitacao")` (container, onde o Dockerfile
  copia `data/` para `/data`). Se nenhum existir, **levanta `MapaIndisponivel`** — nunca cai num
  mapa vazio em silêncio (lição da Bússola em CLAUDE.md, "Dados editoriais nos containers").
- **Migrations** em `apps/api/data/migrations/versions/`, no padrão de
  `b81e4c07d2a9_explicacao_verificacoes.py`: docstring dizendo o porquê, `batch_alter_table` para
  alterar tabela (SQLite), `# pragma: allowlist secret` nos ids, `downgrade()` completo. Cadeia
  linear; antes de criar, `cd apps/api && ../../.venv/bin/alembic heads` deve mostrar **um** head,
  e o `down_revision` é esse head (os ids abaixo são sugestões; se outro PR entrou antes, encadeie
  no head real). Ordem dos arquivos quentes: 011 → 026 → 027 → 053 (spec §5.4).
- **Horário**: a API da Câmara manda `dataHora` sem fuso (horário de Brasília). Guardamos como
  veio, em `DateTime` ingênuo, igual às colunas existentes. "Hoje" para janelas e para a regra R9
  é `datetime.now(ZoneInfo("America/Sao_Paulo")).date()`, calculado **no script**, nunca dentro do
  motor.
- **CHANGELOG**: toda tarefa que muda comportamento observável, contrato de API, modelo ou `data/`
  adiciona entrada em `docs/CHANGELOG.md`, `## [Unreleased]`, no formato de CLAUDE.md.
- **Não** fazer: `git push`, rodar migration contra banco que não seja SQLite temporário, gravar no
  banco de desenvolvimento sem `--dry-run` antes, chamar LLM em qualquer ponto desta trilha.

### 0.1 O que foi conferido ao vivo em 2026-10-30 (e muda o desenho)

| # | Fato | Consequência no desenho |
| --- | --- | --- |
| A1 | A Câmara manda `retry-after: 30` em **toda** resposta, inclusive 200 | Só respeitar `Retry-After` em 429/503/504 (TRM-012) |
| A2 | `GET /proposicoes?dataInicio=2026-10-23&dataFim=2026-10-30&siglaTipo=PL,PLP,PEC,MPV,PDL&itens=100` → `x-total-count: 2227`, 23 páginas; devolve proposições **com tramitação na janela** (ex.: PL 2378/2003, última tramitação em 26/10/2026) | A janela D-7 funciona como "movimentadas" (disc. §9 ⚠ resolvido); orçamento ≈ 23 requisições |
| A3 | `/tramitacoes` não vem ordenado por `sequencia` (PL 2/2024: seq. 7 antes da 1; 57 antes da 21) | Ordenar por `sequencia` sempre |
| A4 | `regime`, `apreciacao`, `uriUltimoRelator`, `codSituacao`, `descricaoSituacao` de **cada linha** de `/tramitacoes` repetem o valor atual (PL 327/2021, seq. 8, de 2021, diz "Urgência (Art. 155)", aprovada só em 2023) | Esses cinco campos são descartados antes de gravar a linha (TRM-026) |
| A5 | Código 100 ("Apresentação de Proposição") também marca ofícios e autógrafos (PL 2/2024 seq. 65; PL 327/2021 seq. 162; PEC 45/2019 seq. 390) | Marco 100 só vale com `condicao_despacho` (TRM-021) |
| A6 | Código 1236 ("Rejeição de Proposição (Plenário)") marca rejeição de requerimento e de emenda (PL 2/2024 seq. 30 e 51); 1240 marca prejudicialidade do substitutivo; 1241, retirada de destaque | Esses códigos **não** são desfecho pelo código; v0 deixa 1236/1240/1241 sem desfecho |
| A7 | Código 502 ("Arquivamento") com despacho "esta proposição apensada fica prejudicada, na forma do art. 191" (PL 4272/2023, seq. 16) | Marco com `variantes` por despacho: 502 + "fica prejudicada" → `prejudicada` |
| A8 | PL 278/2026: `statusProposicao.codSituacao` **nulo** hoje, com marco 251 (Lei 15.504/2026) na seq. 62 | R1 por marco vence situação nula; F0 mostra situação nula e a lei |
| A9 | PEC 45/2019: situação 1140 "Transformado em Norma Jurídica", **sem** marco 251/1012 e sem número de EC no despacho | R1 pela situação; norma "sem número identificado" (TRM-013) |
| A10 | PLP 68/2024: marco 1012, "Transformado na Lei Complementar 214/2025" | Regex cobre LC |
| A11 | PL 1847/2024 na Câmara: autor `Senado Federal - Efraim Filho`, `uri .../orgaos/78`, `codTipo 40000`; seq. 1 "Recebido o Ofício… do Senado Federal, que submete à revisão…" | Casa iniciadora detectável por `/autores` (TRM-027) |
| A12 | `GET /orgaos/{id}` dá `codTipoOrgao`: MESA = 1 (Comissão Diretora), PLEN = 26, CCJC/CMADS = 2 (Comissão Permanente) | R7 classifica órgão por tipo, não por sigla |
| A13 | `regime` aparece como "Ordinário (Art. 151, III, RICD)" no status e "Ordinária (…)" no despacho | Normalizar pelo artigo, não pela palavra (TRM-014) |
| A14 | Senado `GET /legislacao/LEI/15103/2025` → `urlDocumento: https://normas.leg.br/?urn=urn:lex:br:federal:lei:2025-01-22;15103`; a data é a da assinatura, igual à do marco 1012 na Câmara | Formato do URN confirmado para `lei` |
| A15 | `normas.leg.br/api/public/normas?urn=…` respondeu 400 para toda forma de URN tentada; Planalto deu timeout | Não depender de nenhum dos dois em automação (TRM-013) |
| A16 | `https://www.camara.leg.br/propostas-legislativas/{id}` redireciona para `…/proposicoesWeb/fichadetramitacao?idProposicao={id}` (200) | `url_camara` aponta direto para a ficha |
| A17 | Senado `/processo/tipos-situacao`: 175 itens, `sigla` única, 26 com `dataFim` (inativos) | Chave do código no Senado = `sigla` |
| A18 | Nas 240 acompanhadas (detalhe de 30/10): 9 têm regime "Urgência (Art. 155, RICD)" com apreciação "Conclusiva" (ex.: PL 399/2025, 2483732); RICD art. 24, II, h tira da conclusiva o projeto em urgência | `apreciacao_chave = apreciacao_conclusiva_com_urgencia` nesses casos (TRM-014) |
| A19 | Das 105 em situação tratada pela R7 (915/907/1170/924), **23 têm o órgão do status em CCP (18) ou MESA (5)**: o status aponta o órgão do último registro ("Publicação de Proposição", notificação), não a comissão | R7 usa o **órgão efetivo** (último registro em Plenário ou comissão); sem isso, 9,6% cairiam em `nao_sabemos` (TRM-025/026) |
| A20 | Das 20 com situação nula, só 3 têm ≤ 90 dias; **17 são mais antigas, e 13 delas têm "Distribuição" (110) ou apensação como último registro** | R9 passa a ler o histórico quando a situação é nula (TRM-025); sem isso, 7% cairiam em `nao_sabemos` |
| A21 | Texto compilado do RICD (conferido em 30/10): art. 105, § 1º (antigo parágrafo único, que permitia desarquivar a pedido do autor) **revogado pela RCD 33/2022**; art. 137, §§ 1º e 2º: devolução ao autor e recurso ao Plenário em 5 sessões; art. 24, II, h: urgência exclui a apreciação conclusiva | Texto de `arquivada` sem "pode ser desarquivada" na Câmara; `devolvida` com base legal conferida |
| A22 | Regimes observados: "Ordinário (Art. 151, III, RICD)" 132, "Urgência (Art. 155, RICD)" 42, "." 32, "Urgência (Art. 62, CF)" 12, "Prioridade (Art. 151, II, RICD)" 10, "Urgência (Art. 151, I \"j\", RICD)" 9, "Urgência (Art. 64, CF)" 2, "Art. 223 - CF" 1; apreciação "Indefinida" 32 | Tabela de normalização de TRM-014; "." e "Indefinida" são ausência (nulo) |

---

## 1. Modelo de dados alvo e contratos de API

### 1.1 Fluxo

```
 API Câmara ──► CamaraClient (Retry-After, contador, transporte injetável)          data/tramitacao/*.yml
   │                    │                                                            + revisao.yml (scripts)
   │        registrar_proposicao (TRM-010) ── aplicar_detalhe ──► proposicoes          │
   │                    │                                    (status, órgão, norma)   │ carregar_mapa()
   │        sync_tramitacao.py (TRM-012) diário D-7 / completo / uma / recalcular      ▼
   │                    ├── /tramitacoes ──► tramitacoes (TRM-026) ── marcos ◄──── Mapa (só publicável
   │                    ├── /autores (casa iniciadora), cadeia de apensação (TRM-027)  decide; TRM-021/024)
   │                    └── derivar_fase(EntradaFase, Mapa) (TRM-025, puro) ──► proposicoes.fase_*
   ▼                                                                                   │
 IngestionRun                                   FastAPI: ProposicaoRead+ (TRM-014), /tramitacao (TRM-028)
```

### 1.2 Módulos novos

| Caminho | Conteúdo | Tarefa |
| --- | --- | --- |
| `packages/tramitacao/__init__.py` | vazio | 021 |
| `packages/tramitacao/tipos.py` | `Literal`s do contrato: `Fase`, `Desfecho`, `Motivo`, `EstadoEtapa`, `Revisao`, `Casa`, `Especie`, `ClassePrazo`, `RegraId` | 021 |
| `packages/tramitacao/mapa.py` | modelos Pydantic dos arquivos (§2), `Mapa`, `carregar_mapa`, `MapaIndisponivel`, `MapaInvalido` | 021 |
| `packages/tramitacao/revisao.py` | `hash_entrada`, `entradas_publicaveis`, modelo de `revisao.yml` — **implementação única** | 021 (usada por 024, 025, 028) |
| `apps/workers/tramitacao/revisao.py` | só reexporta `packages.tramitacao.revisao` (o caminho que a spec §6.2 cita para os scripts de TRM-023) | 021 |
| `packages/tramitacao/status.py` | `normalizar_regime`, `normalizar_apreciacao`, `id_da_uri`, `situacao_estado` | 010/014 |
| `packages/tramitacao/normas.py` | regex da norma, URN, links, rótulo | 013 |
| `packages/tramitacao/marcos.py` | `classificar_linha` (linha de tramitação → marco) | 026 |
| `packages/tramitacao/motor.py` | `EntradaFase`, `FaseDerivada`, `derivar_fase` | 025 |
| `packages/tramitacao/entrada.py` | `montar_entrada` (de respostas brutas da API) | 025 |
| `packages/tramitacao/etapas.py` | `montar_etapas` (rito + fase → estados) | 028 |
| `packages/tramitacao/frase.py` | `montar_frase` (template, nunca LLM) | 028 |
| `packages/tramitacao/rotulos.py` | `ROTULO_NAO_SABEMOS`, `rotulo_fase`, `rotulo_desfecho` | 028 |
| `packages/tramitacao/referencias.py` | snapshots das tabelas de código e diff | 020 |
| `apps/workers/tramitacao/__init__.py` | vazio | 010 |
| `apps/workers/tramitacao/registro.py` | `registrar_proposicao`, `aplicar_detalhe`, `CacheConsultas` | 010 |
| `apps/workers/tramitacao/sincronizacao.py` | seleção de alvos, `sincronizar_proposicao`, `executar`, `Orcamento` | 012 |
| `apps/workers/tramitacao/eventos.py` | upsert da tabela `tramitacoes` | 026 |
| `apps/workers/tramitacao/fases.py` | `entrada_do_banco`, `orgao_efetivo`, `resolver_cadeia`, `recalcular_fases` | 027 |
| `apps/workers/tramitacao/relatorio.py` | `relatorio`, `simular_fases` (projeção sem gravar) | 027 |
| `scripts/sync_tramitacao.py` | CLI `diario`, `completo`, `uma`, `recalcular`, `relatorio` | 012 (+026/027) |
| `scripts/atualizar_referencias_tramitacao.py` | snapshots das tabelas de código, com diff | 020 |
| `scripts/validar_tramitacao.py` | validador offline | 024 |
| `scripts/gravar_respostas.py` | gravação das fixtures golden | 002 |
| `tests/replay.py` | replay das gravações por `httpx.MockTransport` | 002 |

### 1.3 Colunas novas em `proposicoes` (todas nulas)

`apps/api/models/__init__.py::Proposicao` (hoje :83-124). Nenhuma coluna existente muda de tipo.

**TRM-011** (migration `<id>_status_e_norma_proposicao.py`, `down_revision` = o head atual (`alembic heads`; hoje a migration `b81e4c07…`)):

| Coluna | Tipo | Origem (Câmara) | Observação |
| --- | --- | --- | --- |
| `cod_situacao` | `String(10)` | `statusProposicao.codSituacao` (int → str) | `situacao` (existente) continua com `descricaoSituacao` |
| `sigla_orgao` | `String(30)` | `statusProposicao.siglaOrgao` | |
| `orgao_fonte_id` | `String(20)` | id em `statusProposicao.uriOrgao` | |
| `orgao_nome` | `String(255)` | `GET /orgaos/{id}` → `dados.nome` | cacheado por execução |
| `orgao_tipo_cod` | `String(10)` | `GET /orgaos/{id}` → `dados.codTipoOrgao` | usado pela R7 (A12) |
| `cod_tipo_tramitacao` | `String(10)` | `statusProposicao.codTipoTramitacao` | |
| `descricao_tramitacao` | `String(255)` | `statusProposicao.descricaoTramitacao` | |
| `regime` | `String(255)` | `statusProposicao.regime` | texto oficial, sem normalizar |
| `apreciacao` | `String(255)` | `statusProposicao.apreciacao` | idem |
| `status_sequencia` | `Integer` | `statusProposicao.sequencia` | |
| `status_url` | `String(500)` | `statusProposicao.url` | documento do último despacho |
| `status_bruto` | `JSON(none_as_null=True)` | `statusProposicao` inteiro, como veio | auditoria; "persistir completo" |
| `ultima_movimentacao_em` | `DateTime` | `statusProposicao.dataHora` | base da ordenação "movimentadas" |
| `relator_fonte_id` | `String(20)` | id em `uriUltimoRelator` | |
| `relator_nome` | `String(255)` | `Parlamentar.nome` pelo `fonte_id`; senão `GET /deputados/{id}` → `dados.ultimoStatus.nome` | cacheado |
| `principal_fonte_id` | `String(20)` | id em `uriPropPrincipal` | apensação |
| `orgao_efetivo_sigla` | `String(30)` | órgão efetivo (A19): o do status se for Plenário ou comissão; senão o do registro mais recente nesses órgãos (TRM-012 calcula das tramitações já baixadas) | "Órgão atual" de F0 — evita "Mesa Diretora" em 23 das 240 |
| `orgao_efetivo_nome` | `String(255)` | nome do órgão efetivo | |
| `detalhe_sincronizado_em` | `DateTime` | hora da última leitura **bem-sucedida** do detalhe | nula = nunca lido |
| `origem_registro` | `String(30)` | quem criou: `descoberta`, `votacao`, `votacao_zil`, `cadeia_apensacao`, `manual` | auditoria |
| `norma_tipo` | `String(30)` | regex do despacho (TRM-013) | `lei_ordinaria`, `lei_complementar`, `lei`, `decreto_legislativo`, `emenda_constitucional`, `resolucao` |
| `norma_numero` | `Integer` | idem | |
| `norma_ano` | `Integer` | idem | |
| `norma_data` | `Date` | data do marco 251/1012 | presumida = data de assinatura (A14) |
| `norma_veto` | `String(10)` | `parcial` (marco 1012 ou "Vetado parcialmente") ou nula | |
| `norma_fonte` | `String(30)` | `despacho_camara` (TRM-013); depois `senado_norma_gerada`, `curadoria` (TRM-053) | |
| `norma_tramitacao_sequencia` | `Integer` | sequência da linha de onde saiu | auditoria |
| `norma_verificada_em` | `DateTime` | última conferência | |

Índices: `ix_proposicao_ultima_mov (ultima_movimentacao_em)`, `ix_proposicao_cod_situacao (cod_situacao)`,
`ix_proposicao_principal_fonte (principal_fonte_id)`.

As colunas de norma entram na migration de TRM-011 (e não numa de TRM-013) para manter a cadeia
011 → 026 → 027 da spec §5.4; TRM-013 só as preenche.

**TRM-026** (migration `8e47a1c3d5f6_tramitacoes.py`): tabela `tramitacoes` (§1.4). Em `Proposicao`,
o atributo Python da coluna JSON vazia `tramitacoes` (:103, nunca escrita — conferido por `grep`)
passa a `tramitacoes_legado: Mapped[Optional[list]] = mapped_column("tramitacoes", JSON)` com o
comentário "deprecada, sempre nula; remover em migration futura" — **sem mudar o banco** — e a
relação nova se chama `eventos_tramitacao`.

**TRM-027** (migration `a2f6c9e0b7d1_fase_proposicao.py`):

| Coluna | Tipo | Conteúdo |
| --- | --- | --- |
| `fase` | `String(20)` | uma das 9 fases, ou `nao_sabemos`; nula = não calculada (ou desfecho sem "onde parou") |
| `desfecho` | `String(20)` | um dos 7 desfechos ou nula |
| `fase_motivo` | `String(30)` | motivo do contrato (inclui `recem_apresentada` com fase `apresentada`) |
| `fase_regra` | `String(4)` | `R0`…`R10` |
| `fase_versao_publicada` | `Integer` | `versao_publicada` de `revisao.yml` usada no cálculo |
| `fase_desde` | `Date` | início da fase atual (§TRM-025) |
| `orgao_desde` | `Date` | último "Recebimento" (cód. 500) no órgão efetivo |
| `fase_casa` | `String(10)` | `camara`, `senado` ou nula |
| `fase_herdada_de_id` | `Uuid` | cabeça da cadeia (sem FK — ver abaixo) |
| `fase_evidencias` | `JSON(none_as_null=True)` | lista de strings `"marco:251@62"`, `"situacao:1140"`, `"nao_publicavel:marcos/251"` |
| `fase_calculada_em` | `DateTime` | |
| `casa_iniciadora` | `String(10)` | `camara`, `senado` (TRM-027) |
| `principal_id` | `Uuid` | proposição principal imediata, se registrada |
| `cabeca_id` | `Uuid` | cabeça da cadeia |
| `cabeca_fonte_id` | `String(20)` | |
| `cadeia_status` | `String(30)` | `sem_cadeia`, `resolvida`, `ciclo`, `profunda_demais`, `principal_indisponivel` |

Índices: `ix_proposicao_fase (fase, desfecho)`, `ix_proposicao_cabeca (cabeca_id)`.
**Sem FK** nas três referências a `proposicoes` (`fase_herdada_de_id`, `principal_id`, `cabeca_id`):
FK autorreferente em `batch_alter_table` no SQLite recria a tabela e exige ordem de inserção; a
integridade é garantida pelo código que as preenche (TRM-027) e testada.

### 1.4 Tabela `tramitacoes` (TRM-026)

```python
class Tramitacao(Base):
    """Um registro por evento da tramitação, por Casa.

    Na Câmara, a situação de cada linha não é histórica (disc. §3.2-1; A4): os campos
    codSituacao, descricaoSituacao, regime, apreciacao e uriUltimoRelator são descartados
    antes de gravar, por construção. O histórico de situação real (Senado) entra com início e
    fim, em tipo_registro="situacao", só a partir de TRM-050.
    """
    __tablename__ = "tramitacoes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposicao_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("proposicoes.id"), nullable=False)
    casa: Mapped[str] = mapped_column(String(10), nullable=False)            # camara | senado
    chave: Mapped[str] = mapped_column(String(40), nullable=False)           # Câmara: str(sequencia); Senado: f"{tipo_registro}:{id}"
    sequencia: Mapped[Optional[int]] = mapped_column(Integer)
    data_hora: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sigla_orgao: Mapped[Optional[str]] = mapped_column(String(30))
    orgao_fonte_id: Mapped[Optional[str]] = mapped_column(String(20))
    orgao_tipo_cod: Mapped[Optional[str]] = mapped_column(String(10))        # codTipoOrgao (tabela orgaos) — órgão efetivo, A19
    cod_tipo: Mapped[Optional[str]] = mapped_column(String(20))              # codTipoTramitacao | idTipo (Senado)
    descricao: Mapped[Optional[str]] = mapped_column(String(255))            # descricaoTramitacao
    despacho: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(500))
    tipo_registro: Mapped[str] = mapped_column(String(20), nullable=False)   # movimentacao | situacao | informe
    marco: Mapped[Optional[str]] = mapped_column(String(40))                 # TipoMarco (§2.4) ou nula
    marco_entrada: Mapped[Optional[str]] = mapped_column(String(40))         # "marcos/251" — a entrada do mapa que classificou
    inicio: Mapped[Optional[date]] = mapped_column(Date)                     # só tipo_registro=situacao (Senado)
    fim: Mapped[Optional[date]] = mapped_column(Date)
    cod_situacao: Mapped[Optional[str]] = mapped_column(String(20))          # só Senado; NULL na Câmara por construção
    hash_conteudo: Mapped[str] = mapped_column(String(64), nullable=False)   # sha256 do registro canônico gravado
    removido_na_fonte_em: Mapped[Optional[datetime]] = mapped_column(DateTime)
    criado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("proposicao_id", "casa", "chave", name="uq_tramitacao_chave"),
        Index("ix_tramitacao_prop_seq", "proposicao_id", "casa", "sequencia"),
        Index("ix_tramitacao_prop_marco", "proposicao_id", "marco"),
        Index("ix_tramitacao_data", "data_hora"),
    )
```

Volume esperado: ~240 acompanhadas × ~50 linhas ≈ 12 mil linhas, mais as cabeças de cadeia.

Tabela auxiliar `orgaos` (TRM-026, mesma migration): cache persistente de `GET /orgaos/{id}`, para não
repetir dezenas de consultas a cada execução.

```python
class Orgao(Base):
    __tablename__ = "orgaos"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    casa: Mapped[str] = mapped_column(String(10), nullable=False)
    fonte_id: Mapped[str] = mapped_column(String(20), nullable=False)
    sigla: Mapped[Optional[str]] = mapped_column(String(30))
    nome: Mapped[Optional[str]] = mapped_column(String(255))
    cod_tipo: Mapped[Optional[str]] = mapped_column(String(10))
    obtido_em: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("casa", "fonte_id", name="uq_orgao_fonte"),)
```

`CacheConsultas` (TRM-010) passa a ler e gravar nessa tabela a partir de TRM-026; reconsulta a API
quando `obtido_em` tem mais de 30 dias.

### 1.5 Contratos de API

Literais (definidos uma vez em `packages/tramitacao/tipos.py` e importados por
`apps/api/schemas/__init__.py`):

```python
Fase = Literal["apresentada", "comissoes", "plenario", "outra_casa", "retorno",
               "sancao", "veto_congresso", "promulgacao", "norma"]
FaseOuNaoSabemos = Literal["apresentada", "comissoes", "plenario", "outra_casa", "retorno",
                           "sancao", "veto_congresso", "promulgacao", "norma", "nao_sabemos"]
Desfecho = Literal["arquivada", "retirada", "prejudicada", "rejeitada",
                   "perdeu_eficacia", "vetada", "devolvida"]
Motivo = Literal["situacao_sem_mapa", "sinais_conflitantes", "principal_nao_resolvida",
                 "fonte_indisponivel", "especie_fora_do_escopo", "mapa_nao_aprovado",
                 "recem_apresentada"]
EstadoEtapa = Literal["feita", "atual", "futura", "pulada", "interrompida"]
Revisao = Literal["rascunho", "revisado_agentes", "aprovado"]
Casa = Literal["camara", "senado"]
CasaRito = Literal["camara", "senado", "congresso", "presidencia"]
Especie = Literal["PL", "PLP", "PEC", "MPV", "PDL"]
ClassePrazo = Literal["D", "D*", "X"]
RegraId = Literal["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"]
SituacaoEstado = Literal["informada", "recem_apresentada", "sem_situacao", "nao_sincronizada"]
```

**Semântica de `fase` + `fase_motivo`** (vale para banco e API): `fase = "nao_sabemos"` ⇔
`fase_motivo` é um dos seis motivos de "não sabemos". `fase_motivo = "recem_apresentada"` ⇔
`fase = "apresentada"` pela R9
(disc. §4.3 R9; spec do PM: conta como fase conhecida, não como `nao_sabemos`). `desfecho` não nulo
com `fase` nula = encerrada sem "onde parou" conhecido (ex.: apensada prejudicada).

**TRM-014 — `ProposicaoRead`** (`apps/api/schemas/__init__.py:48-67` hoje) ganha:

```python
class NormaResumo(BaseModel):
    tipo: Literal["lei_ordinaria", "lei_complementar", "lei", "decreto_legislativo",
                  "emenda_constitucional", "resolucao"]
    rotulo: str                      # "Lei 14.871/2024", "Lei Complementar 214/2025"
    numero: int
    ano: int
    data: Optional[date] = None      # data do marco na Câmara (presumida de assinatura)
    veto: Optional[Literal["parcial"]] = None
    url_normas_leg: Optional[str] = None
    url_planalto: Optional[str] = None
    links_verificados: bool = False  # sempre False até TRM-053: links montados por padrão
    fonte: Literal["despacho_camara", "senado_norma_gerada", "curadoria"]
    verificada_em: Optional[InstanteUTC] = None

class ProposicaoRead(BaseModel):
    # ... campos existentes, inalterados (inclusive o model_validator do PR #49) ...
    cod_situacao: Optional[str] = None
    situacao_estado: SituacaoEstado = "nao_sincronizada"
    sigla_orgao: Optional[str] = None
    orgao_nome: Optional[str] = None
    regime: Optional[str] = None                 # oficial, inteiro
    regime_chave: Optional[str] = None           # chave de glossário pela tabela de TRM-014 (A22)
    regime_texto: Optional[str] = None           # texto_curto do glossário, só se publicável
    apreciacao: Optional[str] = None
    apreciacao_chave: Optional[str] = None       # apreciacao_conclusiva | apreciacao_plenario | apreciacao_conclusiva_com_urgencia (A18)
    apreciacao_texto: Optional[str] = None
    relator_nome: Optional[str] = None
    ultima_movimentacao_em: Optional[HorarioCamara] = None
    detalhe_sincronizado_em: Optional[InstanteUTC] = None
    url_camara: Optional[str] = None
    principal_fonte_id: Optional[str] = None
    principal_url_camara: Optional[str] = None   # pedido implícito de UI/UX (F11): a interface não monta URL
    orgao_efetivo_sigla: Optional[str] = None    # "Órgão atual" (A19); `sigla_orgao` segue sendo o do status
    orgao_efetivo_nome: Optional[str] = None
    situacao_glossario: Optional[str] = None     # chave da entrada do glossário cujos `codigos` contêm
                                                 # ("camara", cod_situacao) — publicável ou não; a interface
                                                 # busca o texto em /tramitacao/mapa (não por `termo`)
    norma: Optional[NormaResumo] = None
    # TRM-028 (nulos até lá):
    fase: Optional[FaseOuNaoSabemos] = None
    fase_rotulo: Optional[str] = None            # nulo só se a fase ainda não foi calculada
    fase_motivo: Optional[Motivo] = None
    desfecho: Optional[Desfecho] = None
    desfecho_rotulo: Optional[str] = None
    apensada: bool = False
    casa_iniciadora: Optional[Casa] = None       # pedido de UI/UX (chapéu, rito, contagens)
```

**Regra de `fase_rotulo` (pedido do Design System; vale para `ProposicaoRead` e `onde_esta`):** é o
texto do `FaseSelo` e **nunca é nulo** depois que a fase foi calculada. Precedência: (1) `desfecho`
não nulo → `DesfechoDef.rotulo` ("Arquivada"); (2) `fase == "nao_sabemos"` →
`ROTULO_NAO_SABEMOS = "Fase não identificada"` (constante em `packages/tramitacao/rotulos.py`, texto
da matriz de TRM-046 — fonte única é a matriz; um teste de TRM-028 confere a igualdade com
`apps/web/lib/tramitacao/textos.ts`); (3) `fase_motivo == "recem_apresentada"` →
`FaseDef(apresentada).rotulo_por_motivo["recem_apresentada"]` ("Recém-apresentada"); (4) senão,
`rotulo_por_especie[especie]`, depois `rotulo_por_casa[casa]`, depois `rotulo`, da fase (a herdada,
quando apensada). Rótulos têm no máximo 32 caracteres (validador). Os casos (1), (3) e (4) só existem
se a entrada é publicável — o motor devolve `nao_sabemos(mapa_nao_aprovado)` antes disso.

**TRM-028 — tramitação** (`GET /proposicoes/{id}/tramitacao`):

```python
class FonteRead(BaseModel):
    rotulo: str                      # "Câmara — situação atual"
    url: Optional[str] = None        # endpoint público consultado (objeto, não string — pedido do DS)

class ComoSabemosRead(BaseModel):
    regra: RegraId
    regra_descricao: Optional[str] = None   # `descricao` da regra em fases.yml, só se publicável
    versao_publicada: Optional[int] = None  # ex-`mapa_versao` do brief (spec §6.2)
    fontes: list[FonteRead]
    conferido_em: Optional[InstanteUTC] = None   # detalhe_sincronizado_em

class HerdadaDeRead(BaseModel):
    id: Optional[UUID] = None        # preenchido sempre que a cabeça foi registrada (D2: também a de contexto)
    fonte_id: str
    rotulo: str                      # "PL 5941/2013"
    url_camara: Optional[str] = None
    acompanhada: bool = False        # categorias_zil não nula; é isto que separa A01 de A02 na matriz de UI/UX

class RelatorRead(BaseModel):         # forma pedida por UI/UX (o brief dizia só `relator`)
    nome: str
    partido: Optional[str] = None    # de `parlamentares` pelo relator_fonte_id, se houver
    uf: Optional[str] = None
    parlamentar_id: Optional[UUID] = None   # link para /parlamentar só com o ranking público (flag)

class OndeEstaRead(BaseModel):
    fase: Optional[FaseOuNaoSabemos]         # nula SÓ com desfecho e "onde parou" desconhecido (apensada prejudicada)
    fase_rotulo: str                         # nunca nulo (regra acima)
    fase_motivo: Optional[Motivo] = None
    desfecho: Optional[Desfecho] = None
    desfecho_rotulo: Optional[str] = None
    apensada: bool = False
    herdada_de: Optional[HerdadaDeRead] = None
    casa: Optional[Casa] = None
    sigla_orgao: Optional[str] = None
    orgao_nome: Optional[str] = None
    desde: Optional[date] = None             # fase_desde
    orgao_desde: Optional[date] = None
    situacao_oficial: Optional[str] = None   # descricaoSituacao, inteira
    situacao_glossario: Optional[str] = None # como em ProposicaoRead
    regime_texto: Optional[str] = None
    apreciacao_texto: Optional[str] = None
    relator: Optional[RelatorRead] = None
    frase: Optional[str] = None              # template de fases.yml; nula em nao_sabemos (a interface usa a matriz de TRM-046)
    como_sabemos: ComoSabemosRead

class EtapaRead(BaseModel):
    id: str
    nome: str
    fase: Fase
    estado: EstadoEtapa
    quando: Optional[date] = None
    casa: Optional[CasaRito] = None
    nota: Optional[str] = None       # pedido do DS: pulada → `nota_pulada` do rito ("Plenário dispensado:
                                     # apreciação conclusiva"); interrompida → rótulo do desfecho; senão nula

class RitoRef(BaseModel):            # pedido de UI/UX: qual rito de /tramitacao/mapa as etapas seguem
    chave: str                       # "PL_CD"
    especie: Especie
    casa_iniciadora: CasaRito

class MarcoRead(BaseModel):
    quando: Optional[date] = None
    titulo: str                      # de marcos.yml, só marcos publicáveis
    marco: str                       # TipoMarco
    casa: Casa
    sigla_orgao: Optional[str] = None
    url: Optional[str] = None
    votacao_id: Optional[UUID] = None

class TramitacaoRead(BaseModel):
    onde_esta: OndeEstaRead
    etapas: list[EtapaRead]          # [] quando fase = nao_sabemos, fase nula ou rito não publicável
    marcos: list[MarcoRead]
    eventos_total: int
    rito: Optional[RitoRef] = None

class EventoRead(BaseModel):          # GET /proposicoes/{id}/tramitacao/eventos
    casa: Casa
    sequencia: Optional[int] = None
    data_hora: Optional[HorarioCamara] = None
    sigla_orgao: Optional[str] = None
    descricao: Optional[str] = None
    despacho: Optional[str] = None   # texto original
    url: Optional[str] = None
    marco: Optional[str] = None      # só se a entrada do marco for publicável

class EventosPagina(BaseModel):      # convenção do repositório (PaginatedResponse, ?page=&per_page=)
    items: list[EventoRead]          # do mais recente para o mais antigo (sequência decrescente)
    total: int
    page: int
    per_page: int                    # 1..100, padrão 50
    pages: int
```

**TRM-028 — mapa** (`GET /tramitacao/mapa`):

Forma reconciliada entre o que UI/UX (`backlog-interface.md` §0.1) e Design System
(`backlog-design-system.md`, TRM-034/035) propuseram; onde divergiam, a escolha está comentada.

```python
class BaseLegalRead(BaseModel):
    rotulo: str                      # "CF, art. 66, § 1º" — os dois pediram {rotulo, url}
    url: Optional[str] = None
    norma: str                       # extras para quem quiser agrupar
    dispositivo: str

class PrazoRead(BaseModel):
    classe: ClassePrazo              # D | D* | X
    texto: str

class FaseDefRead(BaseModel):
    chave: Fase; ordem: int; publicavel: bool
    rotulo: Optional[str] = None; pergunta: Optional[str] = None   # nulos se não publicável

class DesfechoDefRead(BaseModel):
    chave: Desfecho; publicavel: bool
    rotulo: Optional[str] = None
    base_legal: list[BaseLegalRead] = []
    # sem "reversivel": na Câmara o desarquivamento a pedido foi revogado (A21); o texto de cada Casa
    # vem do glossário (`desfecho_arquivada`) e do rito (`desfechos[].texto`)

class RitoEtapaRead(BaseModel):
    id: str
    fase: Fase
    nome: str
    casa: Optional[CasaRito] = None
    o_que_acontece: str              # UI/UX: o_que_acontece; DS chamava "descricao"
    quem_decide: Optional[str] = None
    prazo: Optional[PrazoRead] = None
    base_legal: list[BaseLegalRead]
    opcional: bool = False
    condicao: Optional[str] = None   # UI/UX: condicao; DS chamava "condicional". Ex.: "Só se 52 deputados recorrerem"

class RitoDesfechoRead(BaseModel):
    desfecho: Desfecho               # UI/UX: desfecho; DS chamava "id"
    rotulo: str                      # "Arquivada" (UI/UX chamava "nome")
    texto: str                       # quando acontece (DS chamava "condicao")
    base_legal: list[BaseLegalRead]
    a_partir_de: Union[list[str], Literal["qualquer"]]   # DS: aceita "qualquer"

class RitoRead(BaseModel):
    chave: str                       # "PL_CD"
    casa_iniciadora: CasaRito
    publicavel: bool
    revisao: Revisao                 # estado em revisao.yml (para "em revisão" na interface)
    nome: Optional[str] = None
    etapas: list[RitoEtapaRead]      # [] se não publicável (spec §6.8-4)
    desfechos: list[RitoDesfechoRead]

class EspecieRead(BaseModel):
    sigla: Especie
    nome: str
    descricao: Optional[str] = None  # pedido de UI/UX: `texto_curto` de glossario/especie_<sigla> se publicável
    ritos: list[RitoRead]

class GlossarioRead(BaseModel):
    chave: str                       # sem o prefixo "glossario/"
    tipo: str                        # situacao | regime | apreciacao | fase | desfecho | apensada | etapa | especie | conceito
    termo: str                       # sempre presente (termo oficial)
    codigo: Optional[str] = None     # pedido de UI/UX: primeiro código da Câmara, atalho
    codigos: list[dict] = []         # [{"casa": "camara", "cod": "915"}]
    fase: Optional[Fase] = None
    revisao: Revisao
    publicavel: bool
    texto_curto: Optional[str] = None   # null se não publicável (spec §6.8-3)
    texto: Optional[str] = None
    base_legal: list[BaseLegalRead] = []
    exemplos: list[dict] = []

class MapaRead(BaseModel):
    versao_publicada: int            # DS chamava "versao" (string); spec §6.2 fixa versao_publicada
    publicada_em: Optional[date] = None
    aviso: str                       # "Texto do ZIL, não oficial."
    fases: list[FaseDefRead]
    desfechos: list[DesfechoDefRead]
    especies: list[EspecieRead]
    glossario: list[GlossarioRead]
    situacoes_camara: list["SituacaoOficialRead"]   # pedido de UI/UX: a tabela de TRM-020, para "quantas faltam"

class SituacaoOficialRead(BaseModel):
    codigo: str                      # string, como em todo o contrato ("915"); UI/UX tipava number
    descricao: str                   # nome oficial do snapshot, com strip()
    glossario: Optional[str] = None  # chave da entrada que a explica (publicável ou não; ver glossario[])
    tratada: bool                    # está numa regra (False = em nao_mapeados.yml → nao_sabemos)
```

**TRM-028 — contagem** (`GET /tramitacao/contagem?categoria=&tipo=&ano=`): mesma população da lista
(`categorias_zil IS NOT NULL`, D2: cabeças fora das pautas não entram).

```python
class ContagemRead(BaseModel):
    total: int
    por_fase: dict[str, int]         # chaves: as 9 fases + "nao_sabemos"; só desfecho nulo
    por_desfecho: dict[str, int]     # os 7 desfechos
    apensadas: int                   # subconjunto, já contado na fase herdada
    nao_calculadas: int              # fase_calculada_em nula
    versao_publicada: Optional[int]
```

**Lista** (`GET /proposicoes`, TRM-014 e TRM-028): parâmetros novos `ordem: Literal["padrao",
"movimentacao"] = "padrao"` (TRM-014) e `fase: list[FaseOuNaoSabemos] | None`, `desfecho:
list[Desfecho] | None`, `apensada: bool | None` (TRM-028). `fase=X` significa `fase == X AND
desfecho IS NULL`.

**Erros**: 404 `{"detail": "Proposição não encontrada"}` (padrão existente); 503 `{"detail": "Mapa de
tramitação indisponível"}` quando `carregar_mapa` levanta `MapaIndisponivel`/`MapaInvalido` nos
endpoints que dependem do mapa (`/tramitacao/*`, `/proposicoes/{id}/tramitacao`); `ProposicaoRead`
nunca falha por causa do mapa — campos `*_texto`/`*_rotulo` saem nulos e o erro vai para o log.

**Datas e horas** (pedido de UI/UX: `dataBR` fatia a string). `date` sai como `"AAAA-MM-DD"`, sem
fuso — quem exibe não pode passar isso por `new Date()` (o "Apresentada em" com um dia a menos é
esse bug, no frontend). Todo `datetime` dos contratos novos sai **com fuso de Brasília**,
`"2025-05-09T12:35:00-03:00"`, por dois tipos anotados em `apps/api/schemas/__init__.py`:

```python
SP = ZoneInfo("America/Sao_Paulo")
# Campos vindos da Câmara (dataHora sem fuso = horário de Brasília): ultima_movimentacao_em, data_hora
HorarioCamara = Annotated[datetime, PlainSerializer(lambda d: d.replace(tzinfo=SP).isoformat(), return_type=str)]
# Campos gravados pelo ZIL (datetime.utcnow(), padrão do projeto): detalhe_sincronizado_em,
# conferido_em, norma.verificada_em, fase_calculada_em
InstanteUTC = Annotated[datetime, PlainSerializer(
    lambda d: d.replace(tzinfo=timezone.utc).astimezone(SP).isoformat(), return_type=str)]
```

Todo `agora` gravado pelos módulos novos é `datetime.utcnow()` (UTC ingênuo, como `created_at` e
`IngestionRun`); só "hoje" para janelas e R9 usa `America/Sao_Paulo` (§0).

**Total da lista** (achado de UI/UX: a lista mostra só 100 das 240). `GET /proposicoes` passa a
devolver o cabeçalho `X-Total-Count` com o total filtrado (TRM-014), e o `CORSMiddleware` de
`apps/api/main.py` ganha `expose_headers=["X-Total-Count"]`. O corpo continua sendo a lista.

---

## 2. Esquema dos arquivos `data/tramitacao/`

### 2.1 Regras gerais

1. **Pydantic 2 com `extra="forbid"`** em todo modelo; `str_strip_whitespace=True`; listas que são
   conjuntos validadas sem duplicata. Erro de esquema cita arquivo e caminho
   (`fases.yml: regras[3].situacoes_camara[0].desfecho`).
2. **Estado de revisão fora do conteúdo** (spec §6.2, decisão D8): `data/tramitacao/revisao.yml`,
   escrito só por `scripts/revisar_tramitacao.py` e `scripts/aprovar_tramitacao.py` (TRM-023). Os
   arquivos de conteúdo **não têm** campo de revisão. Entrada ausente de `revisao.yml` = `rascunho`.
3. **Unidade de revisão** = entrada, identificada por `<arquivo>/<chave>` (contrato da spec §6.2):

| Arquivo | Entradas | Formato da chave | Exemplos |
| --- | --- | --- | --- |
| `fases.yml` | 9 fases, 7 desfechos, `apensada`, regras R1–R10 | `fase_<fase>`, `desfecho_<desfecho>`, `apensada`, `regra_<id>` | `fases/fase_comissoes`, `fases/desfecho_arquivada`, `fases/regra_R7` |
| `marcos.yml` | cada código de tramitação mapeado | Câmara: `<cod>`; Senado (TRM-050): `sf_<sigla_minuscula>` | `marcos/320`, `marcos/251` |
| `ritos.yml` | cada rito (espécie × Casa iniciadora) e o bloco "depois da lei" | `<ESPECIE>_<CD\|SF\|CN>`, `pos_lei` | `ritos/PL_CD`, `ritos/MPV_CN`, `ritos/pos_lei` |
| `glossario.yml` | cada termo | `snake_case`, `^[a-z][a-z0-9_]{2,59}$` | `glossario/aguardando_despacho_chancela`, `glossario/regime_urgencia` |

   **As situações oficiais mapeadas moram dentro das regras** (`regra_R3.situacoes_camara`, etc.):
   são revisadas junto com a regra que as trata (lote L2 da spec §6.12). Assim cada código de
   situação tem exatamente um dono, e "a regra que casou" é uma entrada só.
4. **Hash e publicação** (spec §6.2/§6.8): `hash_entrada(entrada: dict) -> str` =
   `hashlib.sha256(json.dumps(entrada, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()[:12]`,
   sobre o mapeamento da entrada **como o `yaml.safe_load` devolve** (antes do Pydantic). Conteúdo
   não tem campo de data: se tiver, `json.dumps` falha — por desenho. `entradas_publicaveis(conteudo:
   dict[str, dict], revisao: ArquivoRevisao) -> frozenset[str]` devolve os ids com `estado ==
   "aprovado"` e `hash == hash_entrada(conteudo[id])`. **Só ids publicáveis decidem fase, rótulo,
   frase, título de marco, rito ou texto de glossário em produção.**
5. **Versão**: `versao_publicada` (int, em `revisao.yml`) sobe a cada aprovação e é o que "Como
   sabemos" mostra e o que `fase_versao_publicada` grava (spec §6.2; substitui o `mapa_versao` do
   brief).
6. **Campos de procedência** (spec §6.3), em toda entrada de conteúdo:
   - `base_legal: list[BaseLegal]` — `{norma, dispositivo, url}`; `dispositivo` é o "artigo" do brief
     (art., §, inciso ou alínea). Obrigatória e não vazia, **ou** `base_legal_motivo: str` (≥ 20
     caracteres) para critério interno do ZIL (ex.: os 90 dias da R9). Ter os dois é erro.
   - `fontes: list[HttpUrl]` (≥ 1) — URLs efetivamente consultadas.
   - `casos: list[Caso]` — proposições reais que exercitam a entrada; obrigatório (≥ 1) em regra e
     marco (spec §6.3-5).
   - `descricao_oficial: str` — em toda entrada que espelha um código oficial; igual ao `nome` do
     snapshot (TRM-020) depois de `strip()`.
   - `pendente: str | None` — o que falta conferir; com valor, a entrada não pode sair de
     `rascunho` (V-R9).
7. **URL de base legal**: `https`, host em `HOSTS_NORMA = {"www.planalto.gov.br", "planalto.gov.br",
   "www2.camara.leg.br", "www.camara.leg.br", "legis.senado.leg.br", "www25.senado.leg.br",
   "www.congressonacional.leg.br", "normas.leg.br", "portal.stf.jus.br", "noticias.stf.jus.br"}`.
   `norma` é chave do catálogo `normas_base` de `fases.yml`.
8. **Textos** (rótulos, frases, títulos, glossário) seguem o guia de redação de TRM-022 (UI/UX). O
   validador barra os termos de disc. §6.5: `TERMOS_VEDADOS = ("parada há", "% concluída", "em breve",
   "deve ser votada", "engavetad", "travad")` (comparação sem acento e sem caixa).
9. **Só `aprovado` vai a produção** — garantido por construção em três pontos: (a) `Mapa.publicavel(id)`
   é a única porta usada por `derivar_fase`, pela API e pelo sync; (b) `Mapa.com_tudo_publicavel()`
   (para testes de lógica, para o validador e para a projeção de TRM-027) é proibido fora de `tests/`,
   `scripts/validar_tramitacao.py` e `apps/workers/tramitacao/relatorio.py::simular_fases` (que não grava)
   — teste de árvore sintática em TRM-024; (c) `/tramitacao/mapa` devolve texto nulo para o não
   publicável (teste de contrato em TRM-028).

### 2.2 Tipos comuns (`packages/tramitacao/mapa.py`)

```python
class Estrito(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

class BaseLegal(Estrito):
    norma: str = Field(pattern=r"^[A-Z0-9][A-Z0-9-]{1,30}$")   # chave de normas_base
    dispositivo: str = Field(min_length=4, max_length=80)        # "art. 66, § 1º"
    url: HttpUrl
    nota: Optional[str] = None

class Caso(Estrito):
    casa: Casa
    fonte_id: str = Field(pattern=r"^[0-9]+$")
    rotulo: str                                                  # "PL 2/2024"
    nota: Optional[str] = None                                   # "seq. 66, despacho com 'Transformado na Lei…'"

class Procedencia(Estrito):
    base_legal: list[BaseLegal] = []
    base_legal_motivo: Optional[str] = Field(default=None, min_length=20)
    fontes: list[HttpUrl] = Field(min_length=1)
    pendente: Optional[str] = None
    # model_validator: exatamente um de (base_legal não vazia, base_legal_motivo)

Marcador = Literal["na_casa", "da_casa", "membros", "orgao", "desde", "orgao_desde", "data",
                   "norma_com_artigo", "na_lei", "principal_com_artigo", "frase_principal"]

class ModeloFrase(Estrito):
    """Template da frase de "Onde está agora" (marcadores da spec de UI/UX, backlog-interface §2.9).

    Escolha: o primeiro modelo, na ordem, cujos filtros casam e cujos marcadores de `quando` têm
    valor. Todo marcador usado em `modelo` tem de estar em `quando` (validador). O último modelo de
    cada lista não tem filtro nem `quando` — é a variante "sem o dado".
    """
    casa: Optional[Casa] = None          # só vale com esta Casa atual (ex.: "No Senado." × "Na Câmara.")
    especie: Optional[Especie] = None    # só vale para esta espécie (ex.: MPV)
    veto_parcial: Optional[bool] = None  # só vale com (True) ou sem (False) veto parcial na norma
    quando: list[Marcador] = []
    modelo: str = Field(min_length=5, max_length=280)

# Valores dos marcadores (packages/tramitacao/frase.py):
#   na_casa "na Câmara"/"no Senado"; da_casa "da Câmara"/"do Senado"; membros "deputados"/"senadores"
#   (pela Casa atual); orgao "Comissão de Finanças e Tributação (CFT)" ou só a sigla sem nome;
#   desde = fase_desde e orgao_desde = chegada ao órgão (dd/mm/aaaa); data = data do marco decisivo
#   (remessa, veto, terminal); norma_com_artigo "a Lei 14.871/2024", "a Lei Complementar 214/2025",
#   "o Decreto Legislativo 147/2026", "a Emenda Constitucional 135/2024"; na_lei "na Lei 14.000/2020";
#   principal_com_artigo "o PL 5941/2013", "a PEC 45/2019" (a: PEC e MPV; o: PL, PLP, PDL);
#   frase_principal = a frase já montada da cabeça da cadeia.

class NaoMapeado(Estrito):
    cod: str
    descricao_oficial: str
    motivo: str = Field(pattern=r"^(sem_evidencia|fora_do_escopo|inativo|codigo_novo_\d{4}-\d{2}-\d{2})$")
    nota: Optional[str] = None                                   # obrigatória se motivo == fora_do_escopo
```

`nao_mapeados` (e `ignorados` de marcos) **não passam por aprovação** (spec §6.2): levam a
`nao_sabemos` ou a "não é marco", o caminho conservador.

### 2.3 `fases.yml`

```python
class NormaBase(Estrito):
    nome: str
    url: HttpUrl

class FaseDef(Procedencia):
    chave: Fase
    ordem: int = Field(ge=1, le=9)
    rotulo: str = Field(max_length=32)           # texto do FaseSelo; ≤ 32 (nunca trunca, TRM-031)
    rotulo_por_especie: dict[Especie, str] = {}  # cada valor ≤ 32
    rotulo_por_casa: dict[Casa, str] = {}        # chave = Casa atual; cada valor ≤ 32
    rotulo_por_motivo: dict[Literal["recem_apresentada"], str] = {}   # só em `apresentada`: "Recém-apresentada"
    pergunta: str
    glossario: Optional[str] = None              # chave de glossário, sem prefixo
    frases: list[ModeloFrase] = Field(min_length=1)   # a última tem quando: []

class DesfechoDef(Procedencia):
    chave: Desfecho
    rotulo: str = Field(max_length=32)
    glossario: Optional[str] = None              # sem campo "reversível": na Câmara o desarquivamento
                                                 # a pedido foi revogado (RICD art. 105, § 1º; A21); no
                                                 # Senado existe (RISF art. 332). O texto diz isso por Casa.
    frases: list[ModeloFrase] = Field(min_length=1)

class ApensadaDef(Procedencia):
    rotulo: str
    glossario: Optional[str] = None
    frases: list[ModeloFrase] = Field(min_length=1)   # ex.: "Tramita junto com {principal_com_artigo}, …"

class SituacaoTratada(Estrito):
    cod: str
    descricao_oficial: str
    fase: Optional[Fase] = None                  # R6: sancao | veto_congresso | promulgacao
    desfecho: Optional[Desfecho] = None          # R3
    motivo: Optional[Motivo] = None              # R10: sinais_conflitantes

class RegraDef(Procedencia):
    id: RegraId                                  # R1..R10 (R0 é guarda em código, sem entrada)
    tipo: Literal["norma", "marco_terminal", "situacao_terminal", "apensacao", "outra_casa",
                  "pos_congresso", "orgao", "pre_despacho", "recem_apresentada", "fallback"]
    descricao: str                               # frase de "Como sabemos"
    parametros: dict[str, Union[int, str, list[str]]] = {}
    situacoes_camara: list[SituacaoTratada] = []
    situacoes_senado: list[SituacaoTratada] = []  # vazias até TRM-050
    casos: list[Caso] = Field(min_length=1)

class ArquivoFases(Estrito):
    versao_esquema: Literal[1]
    normas_base: dict[str, NormaBase]
    fases: list[FaseDef]                         # exatamente as 9
    desfechos: list[DesfechoDef]                 # exatamente os 7
    apensada: ApensadaDef
    regras: list[RegraDef]                       # exatamente R1..R10, nesta ordem
```

Consistência tipo × campos (validador): `situacao_terminal` exige `desfecho` em cada situação;
`pos_congresso` exige `fase ∈ {sancao, veto_congresso, promulgacao}`; `fallback` exige `motivo`;
os demais tipos não aceitam `fase`/`desfecho`/`motivo` nas situações. Cada código de situação
aparece **uma vez** somando todas as regras e `nao_mapeados.yml` (§2.4.1). Parâmetros obrigatórios:
R4 `{max_niveis: 10}`; R7 `{siglas_plenario: ["PLEN"], tipos_orgao_comissao: [...]}` (códigos
presentes no snapshot `camara-tipos-orgao.json`); R9 `{dias_max: 90}`.

Exemplo (trechos reais do v0; valores de URL completos):

```yaml
# data/tramitacao/fases.yml — fases, desfechos, apensação e regras R1–R10.
# Esquema: packages/tramitacao/mapa.py (ArquivoFases). Validar:
#   .venv/bin/python scripts/validar_tramitacao.py
# O estado de revisão NÃO mora aqui: data/tramitacao/revisao.yml (scripts de TRM-023).
versao_esquema: 1

normas_base:
  CF: {nome: Constituição Federal, url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
  RICD: {nome: Regimento Interno da Câmara dos Deputados, url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
  RCD-33-2022: {nome: Resolução da Câmara 33/2022, url: "https://www2.camara.leg.br/legin/int/rescad/2022/resolucaodacamaradosdeputados-33-4-agosto-2022-793091-publicacaooriginal-165882-pl.html"}
  RISF: {nome: Regimento Interno do Senado Federal, url: "https://legis.senado.leg.br/norma/563958/publicacao/16433779"}
  RCN-1-2002: {nome: Resolução do Congresso 1/2002, url: "https://www2.camara.leg.br/legin/fed/rescon/2002/resolucao-1-8-maio-2002-497942-normaatualizada-pl.html"}
  LC-95-1998: {nome: Lei Complementar 95/1998, url: "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp95.htm"}
  LINDB: {nome: Lei de Introdução às Normas do Direito Brasileiro, url: "https://www.planalto.gov.br/ccivil_03/decreto-lei/del4657compilado.htm"}
  DEC-12002-2024: {nome: Decreto 12.002/2024, url: "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/decreto/D12002.htm"}

fases:
  - chave: comissoes
    ordem: 2
    rotulo: Nas comissões
    rotulo_por_especie: {MPV: Na comissão mista}
    pergunta: Quem analisa e dá parecer
    glossario: fase_comissoes
    frases:                    # conteúdo de backlog-interface.md §2.9 (UI/UX); aqui só a forma
      - especie: MPV
        quando: [orgao_desde]
        modelo: "Na comissão mista do Congresso desde {orgao_desde}."
      - especie: MPV
        modelo: "Na comissão mista do Congresso."
      - quando: [da_casa, orgao, orgao_desde]
        modelo: "Nas comissões {da_casa}. Está na {orgao} desde {orgao_desde}."
      - quando: [da_casa, orgao]
        modelo: "Nas comissões {da_casa}. Está na {orgao}."
      - quando: [da_casa]
        modelo: "Nas comissões {da_casa}."
      - modelo: "Nas comissões."
    base_legal:
      - {norma: RICD, dispositivo: "art. 24, II", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
      - {norma: RICD, dispositivo: "art. 139", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]

regras:
  - id: R1
    tipo: norma
    descricao: >-
      Virou norma: há um marco de transformação em norma no histórico (códigos 251 ou 1012), ou a
      normaGerada do Senado, ou a situação "Transformado em Norma Jurídica". O marco vence o último
      registro, que às vezes é um ofício posterior.
    situacoes_camara:
      - {cod: "1140", descricao_oficial: Transformado em Norma Jurídica}
    base_legal:
      - {norma: CF, dispositivo: "art. 66", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2600838/tramitacoes"]
    casos:
      - {casa: camara, fonte_id: "2600838", rotulo: PL 278/2026, nota: "situação nula; marco 251 na seq. 62"}
      - {casa: camara, fonte_id: "2269745", rotulo: PL 327/2021, nota: "último registro é ofício do veto; marco 1012 na seq. 160"}
  - id: R2
    tipo: marco_terminal
    descricao: >-
      Encerrada por um marco: o marco terminal mais recente (arquivamento, retirada, prejudicialidade,
      perda de eficácia) não foi seguido de desarquivamento nem de movimento que mude de fase.
    base_legal:
      - {norma: RICD, dispositivo: "arts. 104, 105, 163 e 164", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2384947/tramitacoes"]
    casos:
      - {casa: camara, fonte_id: "2384947", rotulo: PL 4272/2023, nota: "situação 'Aguardando Encaminhamento'; 502 com 'fica prejudicada'"}
  - id: R3
    tipo: situacao_terminal
    descricao: A situação oficial é terminal.
    situacoes_camara:
      - {cod: "923", descricao_oficial: Arquivada, desfecho: arquivada}
      - {cod: "950", descricao_oficial: Retirado pelo(a) Autor(a), desfecho: retirada}
      - {cod: "1292", descricao_oficial: Perdeu a Eficácia, desfecho: perdeu_eficacia}
    base_legal:
      - {norma: RICD, dispositivo: "art. 105", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
      - {norma: CF, dispositivo: "art. 62, § 3º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao"]
    casos: [{casa: camara, fonte_id: "<MPV que perdeu a eficácia, gravada em TRM-002>", rotulo: "MPV …"}]
  - id: R4
    tipo: apensacao
    descricao: >-
      Tramita em conjunto: segue a cadeia de proposições principais até a cabeça (até 10 níveis,
      com detecção de ciclo) e herda a fase dela.
    parametros: {max_niveis: 10}
    situacoes_camara:
      - {cod: "925", descricao_oficial: Tramitando em Conjunto}
      - {cod: "927", descricao_oficial: Aguardando Apensação}
    base_legal:
      - {norma: RICD, dispositivo: "arts. 142 e 143", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2482075"]
    casos: [{casa: camara, fonte_id: "2482075", rotulo: PL 5/2025, nota: "cadeia de 4 níveis até o PL 5941/2013"}]
  - id: R5
    tipo: outra_casa
    descricao: >-
      Na outra Casa: com processo do Senado, vale a situação de lá; sem ele, "Aguardando Apreciação
      pelo Senado Federal" põe a proposição no Senado, sem órgão.
    situacoes_camara:
      - {cod: "926", descricao_oficial: Aguardando Apreciação pelo Senado Federal}
    base_legal:
      - {norma: CF, dispositivo: "art. 65", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao"]
    casos: [{casa: camara, fonte_id: "<uma das 5 do banco nessa situação>", rotulo: "…"}]
  - id: R6
    tipo: pos_congresso
    descricao: Fora das Casas: sanção, veto em análise no Congresso ou promulgação, pela situação oficial.
    situacoes_camara:
      - {cod: "1150", descricao_oficial: Aguardando Sanção, fase: sancao}
    base_legal:
      - {norma: CF, dispositivo: "art. 66, §§ 1º a 7º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2600838/tramitacoes"]
    casos: [{casa: camara, fonte_id: "2600838", rotulo: PL 278/2026, nota: "eventos com 'Aguardando Sanção' antes do marco 251"}]
  - id: R7
    tipo: orgao
    descricao: >-
      Pelo órgão onde está: Plenário → no Plenário; comissão (permanente, especial, mista, de MPV,
      temporária) → nas comissões. Quando o órgão da situação oficial é administrativo (Mesa,
      Coordenação de Comissões Permanentes), vale o último Plenário ou comissão do histórico. Na Casa
      revisora, vira "na outra Casa"; de volta à Casa de origem depois de emendas da revisora, vira
      "de volta".
    parametros:
      siglas_plenario: [PLEN]
      tipos_orgao_comissao: ["2", "3", "6", "9", "21", "13000", "81002"]
    situacoes_camara:
      - {cod: "915", descricao_oficial: Aguardando Parecer}
      - {cod: "907", descricao_oficial: Aguardando Designação de Relator(a)}
      - {cod: "1170", descricao_oficial: Aguardando Designação - Aguardando Devolução de Relator(a) que deixou de ser Membro}
      - {cod: "924", descricao_oficial: Pronta para Pauta}
    base_legal:
      - {norma: RICD, dispositivo: "art. 24, II", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/referencias/orgaos/codTipoOrgao"]
    casos: [{casa: camara, fonte_id: "2426923", rotulo: PL 1264/2024, nota: "907 na CFT (codTipoOrgao 2)"}]
  - id: R8
    tipo: pre_despacho
    descricao: Ainda não distribuída: situações anteriores ao despacho do Presidente da Câmara.
    situacoes_camara:
      - {cod: "1201", descricao_oficial: Aguardando Despacho do Presidente da Câmara dos Deputados (Chancela)}
      - {cod: "1221", descricao_oficial: Aguardando Despacho do Presidente da Câmara dos Deputados (Autorização)}
      - {cod: "1091", descricao_oficial: Ag. Análise de Inconstitucionalidade}
      - {cod: "1200", descricao_oficial: Aguardando Autorização do Despacho}
    base_legal:
      - {norma: RICD, dispositivo: "art. 137", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao"]
    casos: [{casa: camara, fonte_id: "<PDL em Chancela gravado em TRM-002>", rotulo: "PDL …"}]
  - id: R9
    tipo: recem_apresentada
    descricao: >-
      A Câmara não informa a situação. Sem distribuição às comissões e apresentada há até 90 dias, é
      recém-apresentada; com histórico, vale o último marco que muda de fase (por exemplo, a
      distribuição às comissões).
    parametros: {dias_max: 90}
    base_legal_motivo: >-
      Critério do ZIL: 29% dos PLs de 2026 chegam sem situação antes do despacho (disc. §1.2); 90 dias
      cobrem o despacho usual sem tratar como "recente" o que está parado na fonte.
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes?siglaTipo=PL&ano=2026"]
    casos: [{casa: camara, fonte_id: "<PL de 2026 com situação nula, gravado em TRM-002>", rotulo: "PL …/2026"}]
  - id: R10
    tipo: fallback
    descricao: Nenhuma regra decidiu com segurança. Dizemos que não sabemos, com o motivo.
    situacoes_camara:
      - {cod: "910", descricao_oficial: Aguardando Encaminhamento, motivo: sinais_conflitantes}
    base_legal_motivo: >-
      Princípio editorial do ZIL: na dúvida, não sabemos, com motivo — nunca palpite (spec §3, P6).
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2384947"]
    casos: [{casa: camara, fonte_id: "2384947", rotulo: PL 4272/2023, nota: "910 só é desfecho por R2"}]
```

### 2.4 `marcos.yml`

```python
TipoMarco = Literal[
    "apresentacao", "distribuicao", "apensacao", "designacao_relator", "parecer",
    "parecer_aprovado", "urgencia_aprovada", "votacao_plenario", "aprovacao_plenario",
    "remessa_outra_casa", "recebimento_outra_casa", "aprovacao_outra_casa", "retorno_emendas",
    "remessa_sancao", "norma", "norma_veto_parcial", "veto_total", "remessa_promulgacao",
    "arquivamento", "desarquivamento", "retirada", "prejudicialidade", "perda_eficacia", "devolucao",
]

class Variante(Estrito):
    padrao_despacho: str                         # regex Python, re.IGNORECASE; testada contra `despacho`
    marco: Optional[TipoMarco] = None            # sobrescreve o da entrada
    titulo: Optional[str] = Field(default=None, max_length=60)
    fase_resultante: Optional[Fase] = None
    terminal: Optional[Desfecho] = None

class MarcoDef(Procedencia):
    cod: str = Field(pattern=r"^[0-9]+$")
    casa: Casa
    descricao_oficial: str
    marco: TipoMarco
    titulo: str = Field(max_length=60)           # linguagem simples, para a linha do tempo
    fase_resultante: Optional[Fase] = None       # a fase em que a proposição entra com este marco
    terminal: Optional[Desfecho] = None
    reabre: list[Desfecho] = []                  # desarquivamento: [arquivada]
    condicao_despacho: Optional[str] = None      # regex; sem casar (e sem variante casando) a linha não é marco
    variantes: list[Variante] = []               # a primeira que casar vence
    extrai_norma: bool = False                   # só 251 e 1012 (consistência com packages/tramitacao/normas.py)
    linha_do_tempo: bool = True
    casos: list[Caso] = Field(min_length=1)

class Ignorado(Estrito):
    cod: str
    descricao_oficial: str
    nota: str                                    # por que não é marco ("publicação em avulso")

class ArquivoMarcos(Estrito):
    versao_esquema: Literal[1]
    marcos: list[MarcoDef]                       # cod único por casa
    ignorados: list[Ignorado]                    # decisão humana: "conferido, não é marco"
```

Classificação de uma linha (`packages/tramitacao/marcos.py::classificar_linha(linha: dict, casa:
Casa, mapa: Mapa) -> MarcoClassificado | None`): acha o `MarcoDef` pelo código; testa `variantes` na
ordem (a primeira que casar sobrescreve campos); sem variante, se há `condicao_despacho` e não casa,
devolve `None`; senão devolve o marco. A classificação **não** filtra por publicável (a tabela guarda
`marco_entrada` para auditoria); quem publica decide (motor e API).

```yaml
versao_esquema: 1
marcos:
  - cod: "100"
    casa: camara
    descricao_oficial: Apresentação de Proposição
    marco: apresentacao
    titulo: Apresentada
    fase_resultante: apresentada
    condicao_despacho: '^apresenta[cç][aã]o d[oa] (PL|PLP|PEC|PDL|MPV|PLV)\b'
    base_legal:
      - {norma: CF, dispositivo: "art. 61", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2416804/tramitacoes"]
    casos:
      - {casa: camara, fonte_id: "2416804", rotulo: PL 2/2024, nota: "seq. 1 é marco; seq. 65 (ofício) não é"}
  - cod: "500"
    casa: camara
    descricao_oficial: Recebimento
    marco: recebimento_outra_casa
    titulo: Chegou à Câmara para revisão
    fase_resultante: outra_casa
    condicao_despacho: 'submete [àa] revis[aã]o'
    variantes:
      - {padrao_despacho: 'substitutivo do senado|emendas? do senado', marco: retorno_emendas, titulo: "Voltou do Senado com mudanças", fase_resultante: retorno}
    base_legal:
      - {norma: CF, dispositivo: "art. 65", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2454704/tramitacoes"]
    casos:
      - {casa: camara, fonte_id: "2454704", rotulo: PL 1847/2024, nota: "seq. 1: 'submete à revisão'"}
      - {casa: camara, fonte_id: "2196833", rotulo: PEC 45/2019, nota: "seq. 393: 'Substitutivo do Senado'"}
  - cod: "1012"
    casa: camara
    descricao_oficial: Transformado em Norma Jurídica com Veto Parcial
    marco: norma_veto_parcial
    titulo: Virou lei, com veto parcial
    fase_resultante: norma
    extrai_norma: true
    base_legal:
      - {norma: CF, dispositivo: "art. 66, § 1º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2416804/tramitacoes"]
    casos:
      - {casa: camara, fonte_id: "2416804", rotulo: PL 2/2024, nota: "seq. 66, Lei 14.871/2024"}
      - {casa: camara, fonte_id: "2430143", rotulo: PLP 68/2024, nota: "seq. 172, LC 214/2025"}
  - cod: "502"
    casa: camara
    descricao_oficial: Arquivamento
    marco: arquivamento
    titulo: Arquivada
    terminal: arquivada
    variantes:
      - {padrao_despacho: '\bfica(m)?\s+prejudicad', marco: prejudicialidade, titulo: "Declarada prejudicada", terminal: prejudicada}
    base_legal:
      - {norma: RICD, dispositivo: "art. 105", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
      - {norma: RICD, dispositivo: "art. 163", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2384947/tramitacoes"]
    casos: [{casa: camara, fonte_id: "2384947", rotulo: PL 4272/2023, nota: "seq. 16, 'fica prejudicada, na forma do art. 191'"}]
  - cod: "1243"
    casa: camara
    descricao_oficial: Encaminhamento (Plenário)
    marco: remessa_outra_casa
    titulo: Aprovada; segue para o Senado
    fase_resultante: outra_casa
    condicao_despacho: 'vai ao senado federal'
    variantes:
      - {padrao_despacho: 'vai [àa] san[cç][aã]o', marco: remessa_sancao, titulo: "Enviada à sanção", fase_resultante: sancao}
    base_legal:
      - {norma: CF, dispositivo: "art. 65", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://dadosabertos.camara.leg.br/api/v2/proposicoes/2416804/tramitacoes"]
    casos:
      - {casa: camara, fonte_id: "2416804", rotulo: PL 2/2024, nota: "seq. 55"}
      - {casa: camara, fonte_id: "2196833", rotulo: PEC 45/2019, nota: "seq. 352 ('vai ao segundo turno') NÃO é marco; seq. 385 é"}
ignorados:
  - {cod: "604", descricao_oficial: Publicação de Proposição, nota: "publicação em avulso e no DCD; não muda a fase"}
```

### 2.4.1 `nao_mapeados.yml` (mantido por script, sem aprovação)

Os códigos ainda sem tratamento ficam num arquivo próprio, ordenado por código, que o script de
TRM-020 reescreve inteiro (com `yaml.safe_dump`) quando aparece código novo — o que não dá para
fazer nos arquivos editados à mão sem perder comentários (o repositório só tem `pyyaml`, spec §6.2).
Mover um código daqui para uma regra ou marco é edição humana em PR.

```python
class ArquivoNaoMapeados(Estrito):
    versao_esquema: Literal[1]
    situacoes_camara: list[NaoMapeado]
    situacoes_senado: list[NaoMapeado]
    tramitacao_camara: list[NaoMapeado]
```

```yaml
# data/tramitacao/nao_mapeados.yml — códigos sem tratamento (viram nao_sabemos ou "não é marco").
# Reescrito por scripts/atualizar_referencias_tramitacao.py. Pode ser editado à mão para REMOVER
# um código ao mapeá-lo em fases.yml ou marcos.yml.
versao_esquema: 1
situacoes_camara:
  - {cod: "1230", descricao_oficial: Transformado em nova proposição, motivo: sem_evidencia, nota: "conferir MPV → PLV com gravação antes de mapear"}
  - {cod: "1250", descricao_oficial: Inativa Sinopse (Carga Jan/2001), motivo: inativo}
  - {cod: "1310", descricao_oficial: Em tramitação no Conselho de Ética, motivo: fora_do_escopo, nota: "processo disciplinar; não ocorre em PL, PLP, PEC, MPV ou PDL"}
situacoes_senado:
  - {cod: "TNJR", descricao_oficial: TRANSFORMADA EM NORMA JURÍDICA, motivo: sem_evidencia, nota: "mapear em TRM-050"}
tramitacao_camara:
  - {cod: "1236", descricao_oficial: Rejeição de Proposição (Plenário), motivo: sem_evidencia, nota: "também marca rejeição de requerimento e de emenda (PL 2/2024 seq. 30 e 51); só mapear com condicao_despacho testada"}
```

### 2.5 `ritos.yml`

```python
class EtapaRito(Procedencia):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,40}$")
    fase: Fase                                   # única dentro do rito
    casa: Optional[CasaRito] = None
    nome: str = Field(max_length=60)
    o_que_acontece: str = Field(max_length=400)
    quem_decide: Optional[str] = Field(default=None, max_length=160)   # "O Presidente da Câmara, ouvidos os líderes"
    classe_prazo: Optional[ClassePrazo] = None
    prazo_texto: Optional[str] = None            # "15 dias úteis; o silêncio importa sanção"
    opcional: bool = False                       # pode ser pulada (estado "pulada")
    pulada_quando: Optional[Literal["apreciacao_conclusiva", "sem_emendas_da_revisora",
                                    "sem_veto_total", "mpv_sem_alteracao", "mpv_alterada",
                                    "sancionada"]] = None   # chave para máquina
    condicao: Optional[str] = Field(default=None, max_length=120)      # texto: "Só se 52 deputados recorrerem"
    nota_pulada: Optional[str] = Field(default=None, max_length=80)    # vira etapas[].nota quando "pulada"

class DesfechoRito(Procedencia):
    desfecho: Desfecho
    a_partir_de: Union[list[str], Literal["qualquer"]]   # ids de etapa do mesmo rito, ou "qualquer"
    texto: str = Field(max_length=300)

class Rito(Procedencia):
    especie: Especie
    casa_iniciadora: CasaRito                    # camara | senado | congresso (MPV)
    nome: str
    etapas: list[EtapaRito] = Field(min_length=3)
    desfechos: list[DesfechoRito]
    notas: list[str] = []

class EspecieDef(Estrito):
    sigla: Especie
    nome: str                                    # "Projeto de lei ordinária"
    glossario: Optional[str] = None

class ItemPosLei(Procedencia):
    id: Literal["publicacao", "vigencia", "regulamentacao"]
    nome: str
    texto: str = Field(max_length=400)
    classe_prazo: Optional[ClassePrazo] = None

class PosLei(Procedencia):
    itens: list[ItemPosLei] = Field(min_length=3, max_length=3)

class ArquivoRitos(Estrito):
    versao_esquema: Literal[1]
    especies: list[EspecieDef]                   # as 5
    ritos: list[Rito]                            # chave derivada: f"{especie}_{CD|SF|CN}"
    pos_lei: PosLei                              # entrada "ritos/pos_lei"
```

Validação: chave de rito única; `MPV` só com `congresso`; fases das etapas em ordem não
decrescente pela `ordem` de `fases.yml`; PEC e PDL sem etapa `sancao` (CF 60 §3º; CF 49); `a_partir_de`
aponta para etapa existente; última etapa é `norma`.

Exemplo — PL iniciado na Câmara (`ritos/PL_CD`), do disc. §2.1:

```yaml
ritos:
  - especie: PL
    casa_iniciadora: camara
    nome: Projeto de lei ordinária iniciado na Câmara
    base_legal:
      - {norma: CF, dispositivo: "arts. 61 a 66", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
    etapas:
      - id: apresentacao
        fase: apresentada
        casa: camara
        nome: Apresentação e despacho
        o_que_acontece: >-
          A proposição é apresentada e o Presidente da Câmara decide a quais comissões ela vai e se
          tramita junto com outra parecida.
        classe_prazo: X
        base_legal:
          - {norma: CF, dispositivo: "art. 61", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
          - {norma: RICD, dispositivo: "art. 139", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
        fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
      - id: comissoes_camara
        fase: comissoes
        casa: camara
        nome: Comissões da Câmara
        o_que_acontece: Cada comissão designa um relator, que apresenta parecer; a comissão vota o parecer.
        classe_prazo: "D*"
        prazo_texto: 5, 10 ou 40 sessões, conforme o regime
        base_legal:
          - {norma: RICD, dispositivo: "art. 52", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
          - {norma: RICD, dispositivo: "art. 54", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
        fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
      - id: plenario_camara
        fase: plenario
        casa: camara
        nome: Plenário da Câmara
        o_que_acontece: >-
          Votação por todos os deputados. Quando a apreciação é conclusiva, só acontece se 52
          deputados recorrerem em 5 sessões.
        classe_prazo: X
        opcional: true
        pulada_quando: apreciacao_conclusiva
        base_legal:
          - {norma: CF, dispositivo: "art. 47", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
          - {norma: RICD, dispositivo: "art. 58, § 1º, e art. 132, § 2º", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
        fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
      - id: senado
        fase: outra_casa
        casa: senado
        nome: Senado
        o_que_acontece: O Senado aprova, rejeita ou emenda. Se emendar, o projeto volta à Câmara.
        classe_prazo: X
        base_legal:
          - {norma: CF, dispositivo: "art. 65", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
          - {norma: RISF, dispositivo: "art. 91", url: "https://legis.senado.leg.br/norma/563958/publicacao/16433779"}
        fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
      - id: retorno_camara
        fase: retorno
        casa: camara
        nome: De volta à Câmara
        o_que_acontece: A Câmara só aceita ou rejeita as mudanças feitas pelo Senado.
        opcional: true
        pulada_quando: sem_emendas_da_revisora
        base_legal:
          - {norma: CF, dispositivo: "art. 65, parágrafo único", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
        fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
      - id: sancao
        fase: sancao
        casa: presidencia
        nome: Sanção ou veto
        o_que_acontece: O Presidente da República sanciona ou veta, no todo ou em parte.
        classe_prazo: D
        prazo_texto: 15 dias úteis; sem resposta, a sanção é tácita
        base_legal:
          - {norma: CF, dispositivo: "art. 66, §§ 1º a 3º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
        fontes: ["https://www.congressonacional.leg.br/materias/vetos/entenda-a-tramitacao-do-veto"]
      - id: veto_congresso
        fase: veto_congresso
        casa: congresso
        nome: Veto total no Congresso
        o_que_acontece: Deputados e senadores, em sessão conjunta, mantêm ou derrubam o veto total.
        classe_prazo: "D*"
        prazo_texto: 30 dias
        opcional: true
        pulada_quando: sem_veto_total
        base_legal:
          - {norma: CF, dispositivo: "art. 66, §§ 4º a 6º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
        fontes: ["https://www.congressonacional.leg.br/materias/vetos/entenda-a-tramitacao-do-veto"]
      - id: promulgacao
        fase: promulgacao
        casa: presidencia
        nome: Promulgação após veto derrubado
        o_que_acontece: Se o veto total for derrubado, a lei é promulgada.
        classe_prazo: D
        prazo_texto: 48 horas
        opcional: true
        pulada_quando: sancionada
        base_legal:
          - {norma: CF, dispositivo: "art. 66, §§ 5º e 7º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
        fontes: ["https://www.congressonacional.leg.br/materias/vetos/entenda-a-tramitacao-do-veto"]
      - id: norma
        fase: norma
        casa: null
        nome: Virou lei
        o_que_acontece: A lei é publicada no Diário Oficial da União.
        classe_prazo: D
        base_legal:
          - {norma: CF, dispositivo: "art. 84, IV", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
        fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
    desfechos:
      - desfecho: arquivada
        a_partir_de: [apresentacao, comissoes_camara, plenario_camara, senado, retorno_camara]
        texto: >-
          Na Câmara, ao fim da legislatura, só vai ao arquivo a proposição que já tramitou três
          legislaturas completas, entre outras regras; o desarquivamento a pedido do autor foi
          revogado em 2022. Também é arquivada a que recebe parecer contrário de todas as comissões.
        base_legal:
          - {norma: RICD, dispositivo: "art. 105, caput e VI (redação da RCD 33/2022)", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
          - {norma: RICD, dispositivo: "art. 133", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
        fontes: ["https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"]
        # art. 105 conferido no texto compilado em 2026-10-30 (A21): caput e inciso VI com a redação
        # da RCD 33/2022; § 1º (antigo parágrafo único, desarquivamento) revogado.
      - desfecho: rejeitada
        a_partir_de: [comissoes_camara, plenario_camara, senado]
        texto: Rejeitada, a mesma matéria só volta na mesma sessão legislativa por maioria absoluta.
        base_legal:
          - {norma: CF, dispositivo: "art. 67", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
        fontes: ["https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"]
      # retirada, prejudicada, vetada, devolvida — idem (TRM-021 §v0)
```

Exemplo — MPV (`ritos/MPV_CN`), do disc. §2.3/§4.2:

```yaml
  - especie: MPV
    casa_iniciadora: congresso
    nome: Medida provisória
    base_legal:
      - {norma: CF, dispositivo: "art. 62", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]
    notas:
      - "Vale desde a publicação. Prazo de 60 + 60 dias, suspenso no recesso (CF art. 62, §§ 3º, 4º e 7º)."
      - "Tranca a pauta da Casa em que estiver a partir do 45º dia (CF art. 62, § 6º; STF, MS 27.931)."
    etapas:
      - {id: edicao, fase: apresentada, casa: presidencia, nome: Edição pelo Presidente da República, o_que_acontece: "A medida provisória é publicada e passa a valer como lei, por tempo limitado.", classe_prazo: D, base_legal: [{norma: CF, dispositivo: "art. 62, caput e § 3º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]}
      - {id: comissao_mista, fase: comissoes, casa: congresso, nome: Comissão mista, o_que_acontece: "Deputados e senadores examinam a MPV e aprovam um parecer.", classe_prazo: "D*", base_legal: [{norma: CF, dispositivo: "art. 62, § 9º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}, {norma: RCN-1-2002, dispositivo: "arts. 2º a 6º", url: "https://www2.camara.leg.br/legin/fed/rescon/2002/resolucao-1-8-maio-2002-497942-normaatualizada-pl.html"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"], pendente: "conferir os artigos da RCN 1/2002"}
      - {id: plenario_camara, fase: plenario, casa: camara, nome: Plenário da Câmara, o_que_acontece: "A votação começa pela Câmara.", classe_prazo: D, base_legal: [{norma: CF, dispositivo: "art. 62, § 8º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]}
      - {id: plenario_senado, fase: outra_casa, casa: senado, nome: Senado, o_que_acontece: "O Senado vota o texto aprovado pela Câmara.", classe_prazo: D, base_legal: [{norma: CF, dispositivo: "art. 62, § 8º", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]}
      - {id: sancao, fase: sancao, casa: presidencia, nome: Sanção do projeto de lei de conversão, o_que_acontece: "Se o Congresso alterou o texto, ele vira projeto de lei de conversão e vai à sanção.", classe_prazo: D, opcional: true, pulada_quando: mpv_sem_alteracao, base_legal: [{norma: CF, dispositivo: "art. 62, § 12", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]}
      - {id: promulgacao, fase: promulgacao, casa: congresso, nome: Promulgação, o_que_acontece: "Aprovada sem alteração, a MPV é promulgada pelo Presidente do Congresso.", opcional: true, pulada_quando: mpv_alterada, base_legal: [{norma: RCN-1-2002, dispositivo: "art. 12", url: "https://www2.camara.leg.br/legin/fed/rescon/2002/resolucao-1-8-maio-2002-497942-normaatualizada-pl.html"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"], pendente: "conferir o artigo da RCN 1/2002"}
      - {id: norma, fase: norma, nome: Convertida em lei, o_que_acontece: "A lei de conversão é publicada.", base_legal: [{norma: CF, dispositivo: "art. 62, § 12", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]}
    desfechos:
      - {desfecho: perdeu_eficacia, a_partir_de: [comissao_mista, plenario_camara, plenario_senado], texto: "Não votada em 120 dias (descontado o recesso), perde a eficácia desde a edição.", base_legal: [{norma: CF, dispositivo: "art. 62, §§ 3º e 11", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]}
      - {desfecho: rejeitada, a_partir_de: [plenario_camara, plenario_senado], texto: "Rejeitada, perde a eficácia; o Congresso disciplina os efeitos por decreto legislativo.", base_legal: [{norma: CF, dispositivo: "art. 62, §§ 3º e 11", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}], fontes: ["https://www.congressonacional.leg.br/materias/medidas-provisorias/entenda-a-tramitacao-da-medida-provisoria"]}
```

### 2.6 `glossario.yml` (esquema de Arquitetura; guia de redação e textos de UI/UX — TRM-022)

```python
class CodigoRef(Estrito):
    casa: Casa
    cod: str

class Exemplo(Estrito):
    proposicao: str                              # "PL 1264/2024"
    casa: Casa
    fonte_id: str = Field(pattern=r"^[0-9]+$")
    nota: Optional[str] = Field(default=None, max_length=200)

class EntradaGlossario(Procedencia):
    chave: str = Field(pattern=r"^[a-z][a-z0-9_]{2,59}$")   # âncora: /como-vira-lei/situacoes#termo-<chave> (prefixo do DS, evita colisão com ids de seção)
    tipo: Literal["situacao", "regime", "apreciacao", "fase", "desfecho", "apensada",
                  "etapa", "especie", "conceito"]
    termo: str = Field(max_length=120)           # o termo oficial, como a fonte escreve
    texto_curto: str = Field(min_length=20, max_length=160)  # inline / tooltip
    texto: str = Field(min_length=40, max_length=900)        # 1 a 3 parágrafos
    codigos: list[CodigoRef] = []                # obrigatório (≥ 1) se tipo == "situacao"; descricao_oficial do snapshot vira `termo`
    descricao_oficial: Optional[str] = None      # obrigatória se tipo == "situacao" e igual ao snapshot
    fase: Optional[Fase] = None                  # fase típica (informativa) para tipo "situacao"
    exemplos: list[Exemplo] = []
    relacionados: list[str] = []                 # chaves existentes

class ArquivoGlossario(Estrito):
    versao_esquema: Literal[1]
    aviso: str                                   # "Texto do ZIL, não oficial."
    entradas: list[EntradaGlossario]
```

Regras do validador para o glossário: chave única; `base_legal` obrigatória (sem `base_legal_motivo`)
para `regime`, `apreciacao`, `desfecho`, `etapa`; `tipo: situacao` aceita `base_legal_motivo` quando
a situação é administrativa e não tem dispositivo próprio (pedido de UI/UX, ex.: 910 "Aguardando
Encaminhamento"), com o texto padronizado `"Situação administrativa da Câmara, sem dispositivo próprio
no Regimento"` (o validador confere o texto exato — é o que a interface mostra); cada `(casa, cod)` de
`codigos` em no máximo uma entrada; `relacionados` e todo `glossario:` citado em
`fases.yml`/`ritos.yml` existem (aviso enquanto TRM-022 não terminou; erro com `--estrito`).

Chaves fixas que a API usa: regimes e apreciação (TRM-014, tabela de normalização) —
`regime_ordinaria`, `regime_prioridade`, `regime_urgencia`, `regime_urgencia_constitucional`,
`regime_medida_provisoria`, `regime_urgencia_acordo_internacional`, `regime_concessao_radiodifusao`,
`apreciacao_conclusiva`, `apreciacao_plenario`, `apreciacao_conclusiva_com_urgencia`; e
`fase_<fase>`, `desfecho_<desfecho>`, `apensada`, `especie_<sigla minúscula>` (TRM-028).

Três entradas de exemplo (rascunho; o texto final segue o guia de TRM-022):

```yaml
versao_esquema: 1
aviso: Texto do ZIL, não oficial.
entradas:
  - chave: aguardando_parecer
    tipo: situacao
    termo: Aguardando Parecer
    descricao_oficial: Aguardando Parecer
    codigos: [{casa: camara, cod: "915"}]
    fase: comissoes
    texto_curto: Um relator já foi escolhido e prepara o parecer que a comissão vai votar.
    texto: >-
      A proposição está numa comissão, com um relator designado. O relator escreve um parecer — a
      opinião dele sobre aprovar, rejeitar ou mudar o texto — e a comissão vota esse parecer. O
      Regimento fixa prazos para isso, que na prática costumam não ser cumpridos.
    base_legal:
      - {norma: RICD, dispositivo: "art. 52", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
  - chave: regime_urgencia
    tipo: regime
    termo: Urgência (Art. 155, RICD)
    texto_curto: O Plenário da Câmara aprovou votar a proposição sem esperar os prazos das comissões.
    texto: >-
      Com a urgência aprovada pela maioria absoluta dos deputados, a proposição pode entrar na
      pauta do Plenário logo. Os pareceres das comissões podem ser dados no próprio Plenário.
      Urgência não garante votação: quem define a pauta é o Presidente da Câmara, ouvidos os líderes.
    base_legal:
      - {norma: RICD, dispositivo: "art. 155", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
    fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
    exemplos:
      - {proposicao: PL 327/2021, casa: camara, fonte_id: "2269745", nota: "urgência aprovada em 28/11/2023; passou a ir ao Plenário"}
  - chave: apreciacao_conclusiva
    tipo: apreciacao
    termo: Proposição Sujeita à Apreciação Conclusiva pelas Comissões - Art. 24 II
    texto_curto: As comissões decidem sem passar pelo Plenário, salvo recurso de 52 deputados.
    texto: >-
      Para a maioria dos projetos de lei, a decisão da Câmara é das comissões. Se elas aprovam, o
      projeto segue para o Senado sem votação em Plenário — a não ser que um décimo dos deputados
      (52) apresente recurso em até 5 sessões.
    base_legal:
      - {norma: RICD, dispositivo: "art. 24, II", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
      - {norma: RICD, dispositivo: "art. 58, § 1º, e art. 132, § 2º", url: "https://www2.camara.leg.br/legin/fed/rescad/1989/resolucaodacamaradosdeputados-17-21-setembro-1989-320110-normaatualizada-pl.html"}
      - {norma: CF, dispositivo: "art. 58, § 2º, I", url: "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"}
    fontes: ["https://www.camara.leg.br/entenda-o-processo-legislativo/"]
```

### 2.7 `referencias/` (TRM-020)

Quatro arquivos JSON, um por tabela, caminho estável (o histórico é o git):

| Arquivo | Fonte | Chave `cod` |
| --- | --- | --- |
| `camara-situacoes.json` | `GET /referencias/proposicoes/codSituacao` (99) | `cod` |
| `camara-tipos-tramitacao.json` | `GET /referencias/proposicoes/codTipoTramitacao` (235) | `cod` |
| `camara-tipos-orgao.json` | `GET /referencias/orgaos/codTipoOrgao` (55) | `cod` |
| `senado-tipos-situacao.json` | `GET https://legis.senado.leg.br/dadosabertos/processo/tipos-situacao` (175) | `sigla` |

```json
{
  "tabela": "camara.codSituacao",
  "fonte": "https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao",
  "obtido_em": "2026-10-30",
  "total": 99,
  "itens": [
    {"cod": "900", "nome": "Aguardando Autógrafos na Mesa", "sigla": "", "descricao": ""}
  ]
}
```

Itens ordenados por `int(cod)` na Câmara e por `sigla` no Senado (onde guardam também `id`,
`data_inicio`, `data_fim`). `nome` guardado como veio (há espaço sobrando, ex.: cód. 901); toda
comparação usa `strip()`. Serialização: `json.dumps(…, ensure_ascii=False, indent=2) + "\n"`.

### 2.8 `revisao.yml` e `revisoes/` (formato da spec §6.2/§6.5; esquema e verificação aqui)

```python
class EstadoEntrada(Estrito):
    estado: Revisao
    hash: str = Field(pattern=r"^[0-9a-f]{12}$")
    registros: list[str] = []                    # lotes: ["L0"]
    aprovado_em: Optional[date] = None
    revisado_por: list[str] = []                 # escrito pelos scripts: "agente:juridico@<hash8 das instruções>",
                                                 # "maintainer:<git user.name>", "especialista:<nome>"

class ArquivoRevisao(Estrito):
    versao_publicada: int = Field(ge=0)
    publicada_em: Optional[date] = None
    entradas: dict[str, EstadoEntrada]           # chave = "<arquivo>/<chave>"
```

`revisado_por` é acréscimo desta spec ao exemplo do PM (o brief pede o campo); os scripts de TRM-023
o preenchem a partir de `consolidado.yml` e `decisao.yml`. O formato de `revisoes/<lote>/…`
(rodadas, `consolidado.yml`, `decisao.yml`, `relatorio.md`) é do PM; TRM-024 só os lê para as regras
V-R4 a V-R6 e tolera campos extras neles (são escritos por script e podem evoluir — o validador lê
os campos que usa e ignora o resto).

### 2.9 Carga em tempo de execução

```python
class MapaIndisponivel(Exception): ...
class MapaInvalido(Exception):
    def __init__(self, problemas: list[str]): ...

@dataclass(frozen=True)
class Mapa:
    versao_publicada: int
    publicada_em: Optional[date]
    publicaveis: frozenset[str]                  # ids "<arquivo>/<chave>"
    normas_base: Mapping[str, NormaBase]
    fases: Mapping[Fase, FaseDef]
    desfechos: Mapping[Desfecho, DesfechoDef]
    apensada: ApensadaDef
    regras: Mapping[RegraId, RegraDef]
    situacao_por_codigo: Mapping[tuple[Casa, str], tuple[RegraId, SituacaoTratada]]
    nao_mapeados_situacao: Mapping[tuple[Casa, str], NaoMapeado]
    nao_mapeados_tramitacao: Mapping[tuple[Casa, str], NaoMapeado]
    marcos: Mapping[tuple[Casa, str], MarcoDef]
    ignorados: Mapping[tuple[Casa, str], Ignorado]
    ritos: Mapping[str, Rito]                    # "PL_CD"
    especies: Mapping[Especie, EspecieDef]
    pos_lei: PosLei
    glossario: Mapping[str, EntradaGlossario]
    aviso_glossario: str
    conteudo_bruto: Mapping[str, dict]           # id → mapeamento do YAML (para hash e para o validador)

    def publicavel(self, id_entrada: str) -> bool: ...
    def com_tudo_publicavel(self) -> "Mapa": ...  # SÓ testes e validador (teste de AST em TRM-024)

def carregar_mapa(diretorio: Optional[Path] = None) -> Mapa: ...
@functools.lru_cache(maxsize=1)
def carregar_mapa_producao() -> Mapa: ...       # cache por processo; o conteúdo só muda em deploy
```

`carregar_mapa` lê `fases.yml`, `marcos.yml`, `ritos.yml`, `glossario.yml` e `nao_mapeados.yml` com
`yaml.safe_load`, valida com Pydantic (erros acumulados em
`MapaInvalido`), lê `revisao.yml` (ausente = `ArquivoRevisao(versao_publicada=0, entradas={})`),
calcula `publicaveis` com `entradas_publicaveis` e monta os índices. Não chama rede.


---

## 3. Tarefas — E0 e E1 (Status honesto, F0)

### TRM-002 — Fixtures gravadas das APIs (golden) + utilitário de replay

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E0 Fundações · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; Maintainer (lista de casos e, em TRM-025, o `esperado` de cada um)
**Depende de:** — · **Desbloqueia:** TRM-010, TRM-012, TRM-013, TRM-025, TRM-026, TRM-027, TRM-028 (gerador de fixtures do frontend), TRM-050; candidatos a golden da spec §6.4

**Problema** — Os testes atuais trocam `CamaraClient._get` por `MagicMock` com respostas
inventadas (`tests/unit/test_camara_client.py:21-36`, `tests/unit/test_sync_votacoes.py:31-39`).
Respostas inventadas não reproduzem as armadilhas reais (disc. §3.2; A3–A9): linhas fora de ordem,
código 100 em ofício, 502 com "fica prejudicada", situação nula com marco de norma. Sem respostas
reais gravadas, o motor de fase (TRM-025) não tem como provar nada, e o adversarial da spec §6.4
não tem onde guardar contraexemplo.

**Oportunidade** — Um conjunto pequeno de respostas reais, versionado, vira a régua de todo o
trabalho: regex da norma, marcos, motor, sync e idempotência rodam offline, em segundos, na CI.

**Solução** — (1) Os clientes aceitam um transporte `httpx` injetável. (2) Um gravador baixa, pelo
mesmo cliente de produção, as respostas de uma lista de casos e grava um "pacote" JSON por caso.
(3) Um replay serve esses pacotes por `httpx.MockTransport` e falha alto em requisição não gravada.

**Escopo** — Dentro: transporte injetável na Câmara e no Senado; gravador; replay; 16 casos +
sintéticos; fixture pytest. Fora: tabelas de referência (TRM-020, moram em `data/`); `esperado` dos
casos (TRM-025); bloquear rede em testes antigos.

**Critérios de aceite**
1. `CamaraClient(transport=t)` e `SenadoClient(transport=t)` usam `t`; sem o argumento, nada muda
   (os 320 testes atuais passam).
2. Existem os pacotes da tabela abaixo em `tests/fixtures/tramitacao/gravacoes/`, cada um com
   `gravado_em` e só respostas 200, exceto os sintéticos (marcados `"sintetico": true`).
3. Dado um pacote carregado, quando o cliente pede um caminho gravado com os mesmos parâmetros em
   qualquer ordem, então recebe exatamente o corpo e os cabeçalhos gravados.
4. Dado um pacote carregado, quando o cliente pede algo não gravado, então o teste falha com
   `RequisicaoNaoGravada("GET camara /proposicoes/123 {}")` — nunca acessa a rede.
5. Dois envelopes para a mesma requisição são servidos em ordem (o último se repete), o que permite
   simular 429 → 200.
6. `.venv/bin/python scripts/gravar_respostas.py --caso pl-327-2021` regrava o pacote; `--todos`
   regrava todos; sem rede, sai com código 1 e mensagem clara.
7. Total de `tests/fixtures/tramitacao/` ≤ 8 MB (o gravador avisa acima disso).

**Specs técnicas**

Clientes (`packages/camara_client/__init__.py:96-102`, `packages/senado_client/__init__.py:72-78`):

```python
def __init__(self, base_url: str = BASE_URL, *, transport: httpx.BaseTransport | None = None) -> None:
    self.base_url = base_url
    self.client = httpx.Client(base_url=base_url, headers=HEADERS, timeout=30.0, transport=transport)
```

(TRM-012 acrescenta `dormir`, `intervalo_minimo` e o contador a este mesmo construtor.)

Pacote (`tests/fixtures/tramitacao/gravacoes/<slug>.json`, `json.dumps(…, ensure_ascii=False,
indent=1)`):

```json
{
  "formato": 1,
  "caso": "pl-327-2021",
  "gravado_em": "2026-10-31T10:12:00-03:00",
  "sintetico": false,
  "respostas": [
    {
      "host": "camara",
      "metodo": "GET",
      "caminho": "/proposicoes/2269745/tramitacoes",
      "params": {},
      "status": 200,
      "cabecalhos": {"x-total-count": null, "link": null, "retry-after": "30"},
      "corpo": {"dados": [], "links": []},
      "sha256_corpo": "…"
    }
  ]
}
```

`host` ∈ {`camara`, `senado`}, derivado de `request.url.host` (`dadosabertos.camara.leg.br`,
`legis.senado.leg.br`); `caminho` sem o prefixo da base (`/api/v2`, `/dadosabertos`); `params` com
valores `str`, comparados como dicionário. Cabeçalhos guardados: `x-total-count`, `link`,
`retry-after`, `content-type`.

`tests/replay.py`:

```python
class RequisicaoNaoGravada(AssertionError):
    """AssertionError de propósito: o cliente só captura httpx.RequestError/HTTPStatusError."""

class Gravacoes:
    def __init__(self, raiz: Path = RAIZ_GRAVACOES) -> None: ...
    def carregar(self, *slugs: str) -> "Gravacoes": ...      # acumula pacotes; também aceita "candidatos/<id>"
    def transporte(self) -> httpx.MockTransport: ...
    def cliente_camara(self, **kwargs) -> CamaraClient: ... # CamaraClient(transport=self.transporte(), **kwargs)
    def cliente_senado(self) -> SenadoClient: ...
    @property
    def requisicoes_feitas(self) -> list[tuple[str, str, dict]]: ...   # para testar orçamento e cache
    def corpo(self, slug: str, caminho: str, params: dict | None = None) -> Any: ...  # leitura direta (testes puros)
```

`tests/conftest.py` ganha:

```python
@pytest.fixture
def gravacoes() -> Gravacoes:
    from tests.replay import Gravacoes
    return Gravacoes()
```

Gravador `scripts/gravar_respostas.py`: lê `tests/fixtures/tramitacao/casos.yml`, monta um
`CamaraClient(transport=TransporteGravador(httpx.HTTPTransport()))` que copia cada par
requisição/resposta para o pacote, e executa a **receita** do caso:

| Receita | Requisições |
| --- | --- |
| `proposicao_completa` | `/proposicoes/{id}`, `/proposicoes/{id}/tramitacoes`, `/proposicoes/{id}/autores`, `/proposicoes/{id}/relacionadas`, `/orgaos/{id}` do status **e de cada órgão distinto das tramitações** (órgão efetivo, A19), `/deputados/{id do uriUltimoRelator}` (se houver) |
| `proposicao_com_cadeia` | `proposicao_completa` do caso e, seguindo `uriPropPrincipal` até 10 níveis, `proposicao_completa` de cada elo |
| `janela` | todas as páginas de `/proposicoes?dataInicio=&dataFim=&siglaTipo=PL,PLP,PEC,MPV,PDL&itens=100&ordem=ASC&ordenarPor=id` |
| `senado_processo` | `/processo?sigla=&numero=&ano=` e `/processo/{id}` (para TRM-050) |

`casos.yml`:

```yaml
casos:
  - slug: pl-327-2021
    casa: camara
    fonte_id: "2269745"
    rotulo: PL 327/2021
    por_que: Conclusiva que virou Plenário por urgência; emendas do Senado; veto parcial derrubado; último registro é ofício
    receita: proposicao_completa
    hoje: null          # preenchido pelo gravador com a data da gravação (o `hoje` da R9 nos testes)
    esperado: null      # TRM-025 preenche; a maintainer confere
```

Casos (Apêndice B + PLP + PEC exigidos pela spec §6.11-7):

| Slug | Câmara id | Receita | Por que |
| --- | --- | --- | --- |
| `pl-327-2021` | 2269745 | completa (+ `senado_processo` PL 327/2021) | ofício depois do marco; urgência; emendas do Senado; veto |
| `pl-2-2024` | 2416804 | completa | urgência constitucional; Plenário com parecer em Plenário; veto parcial; linhas fora de ordem |
| `pl-528-2020` | 2238434 | completa | Lei 14.993/2024 |
| `pl-1847-2024` | 2454704 | completa (+ `senado_processo`) | iniciado no Senado (A11) |
| `pl-1264-2024` | 2426923 | completa | comissão (CFT), sem relator; regime "Ordinário" (A13) |
| `pl-4272-2023` | 2384947 | completa | "Aguardando Encaminhamento" + 502 "fica prejudicada" (A7) |
| `pl-5-2025` | 2482075 | `proposicao_com_cadeia` | cadeia de 4 níveis até o PL 5941/2013 |
| `pl-278-2026` | 2600838 | completa | situação nula com marco 251 (A8) |
| `pl-359-2025` | 2483457 | completa | pauta em comissão com parecer pela rejeição |
| `plp-68-2024` | 2430143 | completa | PLP; LC 214/2025 com veto parcial (A10) |
| `pec-45-2019` | 2196833 | completa | PEC; 1140 sem marco de norma (A9); substitutivo do Senado |
| `pdl-chancela` | a descobrir | completa | PDL em "(Chancela)" — R8 |
| `mpv-perdeu-eficacia` | a descobrir | completa | MPV — R3 `perdeu_eficacia` |
| `pl-2026-situacao-nula` | a descobrir | completa | R9 |
| `pronta-pauta-plenario` | a descobrir | completa | "Pronta para Pauta" com órgão PLEN — R7 |
| `pl-399-2025` | 2483732 | completa | urgência + apreciação conclusiva (A18) — TRM-014 |
| `pl-3474-2023` | 2373188 | completa (+ `/orgaos/{id}` de todos os órgãos das tramitações) | "Aguardando Designação de Relator(a)" com órgão CCP (A19) — órgão efetivo |
| `pl-4036-2026` | 2640711 | completa | situação nula há 105 dias, último registro "Distribuição" (A20) — R9 pelo histórico |
| `janela-d7` | — | `janela` (`dataFim` = dia da gravação, `dataInicio` = 7 dias antes) | seleção de alvos e orçamento |

"A descobrir": o implementador escolhe e registra `fonte_id` no `casos.yml`, assim: `pdl-chancela` e
`mpv-perdeu-eficacia` pelo banco de desenvolvimento, só leitura —
`SELECT fonte_id FROM proposicoes WHERE tipo='PDL' AND situacao LIKE '%(Chancela)%' ORDER BY fonte_id LIMIT 1`
e `… WHERE tipo='MPV' AND situacao='Perdeu a Eficácia' …`; `pl-2026-situacao-nula`: o primeiro
`siglaTipo=PL&ano=2026` do pacote `janela-d7` cujo detalhe tem `codSituacao` nulo e cuja apresentação
tem menos de 90 dias; `pronta-pauta-plenario`: `… WHERE situacao='Pronta para Pauta'`, conferindo no
detalhe `siglaOrgao == "PLEN"` (se nenhuma das 8 do banco estiver no Plenário, procurar na janela).

Sintéticos (`tests/fixtures/tramitacao/sinteticos/`, `"sintetico": true`, escritos à mão):
`429-retry-after.json` (429 com `retry-after: 2`, depois 200), `503-sem-retry-after.json` (503, 503,
200), `500-persistente.json` (500 × 5), `votacao-minima.json` (`/votacoes/{id}` com
`proposicaoPrincipal` apontando para 2426923, votos e orientações vazios — para o teste de TRM-010).

Diretório `tests/fixtures/tramitacao/candidatos/` criado com `.gitkeep` (contraexemplos do
adversarial, spec §6.4, gravados com `--caso candidatos/<fonte_id> --fonte-id <id>`).

**Testes** — `tests/unit/test_replay.py`: corpo igual ao gravado; parâmetros em outra ordem casam;
requisição não gravada levanta `RequisicaoNaoGravada`; sequência 429 → 200 servida em ordem;
`requisicoes_feitas` conta; nenhum pacote tem `status != 200` sem `sintetico`; `sha256_corpo` confere.
Comando: `.venv/bin/python -m pytest tests/unit/test_replay.py -v`.

**Riscos e perguntas em aberto** — A Câmara pode mudar respostas: o pacote é a verdade **do dia da
gravação** (`gravado_em`), e regravar é decisão explícita (PR próprio, diff revisado). Pacotes
grandes (PEC 45/2019 tem ~394 linhas): aceitável até 8 MB no total.

**Instruções para o agente implementador** — Branch `trm-002-gravacoes`. Ordem: (1) `transport`
nos dois clientes + teste de que o padrão não muda; (2) `tests/replay.py` com os sintéticos e seus
testes; (3) gravador; (4) gravar os casos com rede (intervalo de 0,5 s entre chamadas), preencher os
"a descobrir"; (5) `ruff` e suíte inteira. Prova: lista dos pacotes com tamanho e `gravado_em`.
**Não** editar à mão um pacote gravado; **não** gravar `/materia` do Senado (depreciado, disc. §1.4);
**não** usar `MagicMock` de `_get` nos testes novos de tramitação.

---

### TRM-011 — Persistir `statusProposicao` completo (migration de colunas)

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E1 Status honesto (F0) · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** P
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura
**Depende de:** — · **Desbloqueia:** TRM-010, TRM-013, TRM-014, TRM-026

**Problema** — `Proposicao` guarda só `situacao` (texto) e `ultimo_despacho`
(`apps/api/models/__init__.py:96-98`). O discover descarta `codSituacao`, `regime`, `siglaOrgao`,
`apreciacao`, `uriUltimoRelator`, `uriPropPrincipal` (`scripts/discover_proposicoes.py:215-233`;
disc. §1.3). Não há onde gravar órgão, relator, data da última movimentação nem a lei resultante.
Não existe teste de migration no repositório.

**Oportunidade** — Com o status inteiro guardado, a página mostra órgão, regime, relator e
"última movimentação" sem nova chamada à API, e o motor de fase tem a entrada de que precisa.

**Solução** — Uma migration com as colunas de §1.3 (bloco TRM-011, incluindo as de norma), o
modelo atualizado e o primeiro teste de migration up/down em SQLite.

**Escopo** — Dentro: colunas, índices, modelo, teste de migration, CHANGELOG. Fora: preencher as
colunas (TRM-010/013); colunas de fase (TRM-027).

**Critérios de aceite**
1. `alembic upgrade head` em SQLite temporário cria as 28 colunas e os 3 índices de §1.3;
   `alembic downgrade b81e4c07d2a9` remove todos; novo `upgrade head` funciona.
2. Depois de `upgrade head`, comparar `Base.metadata` com o banco
   (`alembic.autogenerate.compare_metadata`) não mostra tabela, coluna ou índice faltando ou
   sobrando (diferenças de tipo do SQLite são ignoradas).
3. Os testes existentes passam sem mudança.

**Specs técnicas**
- `apps/api/data/migrations/versions/3a9c5e71b2d4_status_e_norma_proposicao.py`
  (`revision` gerado pelo `alembic revision`, `down_revision` = o head atual (`alembic heads`; hoje a migration `b81e4c07…`) ou o head atual). Docstring: por que
  (disc. §1.3, §5.1), que `status_bruto` é auditoria e que a situação por linha de tramitação não é
  histórica (por isso nada de histórico aqui).
- `upgrade()`: `with op.batch_alter_table('proposicoes') as batch:` um `batch.add_column` por coluna,
  tipos exatamente os de §1.3 (`sa.String(length=10)`, `sa.JSON(none_as_null=True)`, …), todas
  `nullable=True`; depois `op.create_index('ix_proposicao_ultima_mov', 'proposicoes',
  ['ultima_movimentacao_em'])`, idem `ix_proposicao_cod_situacao`, `ix_proposicao_principal_fonte`.
- `downgrade()`: `op.drop_index` dos três, depois `batch.drop_column` de cada coluna, em ordem inversa.
- Modelo: as 28 colunas em `Proposicao`, num bloco comentado `# ── Status da Câmara (TRM-011) ──`
  e `# ── Norma resultante (TRM-013) ──`; índices em `__table_args__`.
- Teste novo `tests/integration/test_migrations.py`:

```python
API_DIR = REPO_ROOT / "apps" / "api"

def _config(db_url: str) -> Config:
    cfg = Config(str(API_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_DIR / "data" / "migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg

def test_sobe_desce_sobe(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'm.db'}"
    monkeypatch.setenv("DATABASE_URL", url)          # env.py lê DATABASE_URL na hora
    cfg = _config(url)
    command.upgrade(cfg, "head")
    # inspecionar colunas e índices novos
    command.downgrade(cfg, REVISAO_ANTERIOR)   # o head de antes de TRM-011 (`alembic heads` antes da migration)
    command.upgrade(cfg, "head")

def test_modelo_bate_com_migrations(tmp_path, monkeypatch): ...   # compare_metadata, filtrando
    # ("add_table", "remove_table", "add_column", "remove_column", "add_index", "remove_index")
```

  TRM-026 e TRM-027 acrescentam suas revisões a este mesmo teste.

**Testes** — `.venv/bin/python -m pytest tests/integration/test_migrations.py -v` e a suíte inteira.

**Riscos e perguntas em aberto** — Nunca rodamos as migrations em SQLite; se a inicial
(`6d2a71d15687`) falhar em SQLite, corrigir só o necessário para SQLite sem mudar o efeito em
Postgres, e registrar no PR. `env.py` chama `fileConfig`: inofensivo nos testes.

**Instruções para o agente implementador** — Branch `trm-011-colunas-status`. Ordem: teste de
migration contra o head atual (deve passar) → migration → modelo → teste de bater modelo e banco.
Prova: saída do pytest. **Não** rodar contra o Postgres de desenvolvimento; **não** remover a coluna
`tramitacoes` (TRM-026 só renomeia o atributo); **não** criar coluna de situação por linha.

---

### TRM-010 — `registrar_proposicao` único: sempre busca o detalhe

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E1 Status honesto (F0) · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura
**Depende de:** TRM-011, TRM-002 · **Desbloqueia:** TRM-012, TRM-026, TRM-027

**Problema** — Há três caminhos que criam `Proposicao` na Câmara, e dois não leem o detalhe:
`scripts/sync_votacoes_zil.py:128-154` (cria a partir da votação; **as 5 do placar estão sem status,
4 viraram lei** — disc. §1.2) e `apps/workers/crawlers/camara.py:48-90` (`_upsert_proposicao`,
chamado em :178, que ainda sobrescreve `categorias_zil` de proposição existente com a classificação
só pela ementa). O terceiro (`scripts/discover_proposicoes.py:174-235`) lê o detalhe mas guarda só
dois campos.

**Oportunidade** — Um caminho só, testado, garante por construção que toda proposição nasce com o
status da fonte — ou marcada como "não sincronizada", para o sync diário completar.

**Solução** — `apps/workers/tramitacao/registro.py` com `registrar_proposicao` e `aplicar_detalhe`;
os três chamadores passam a usá-lo; um teste de árvore sintática impede um quarto caminho.

**Escopo** — Dentro: módulo de registro; troca nos três chamadores; consulta de órgão e relator com
cache; `packages/tramitacao/status.py::id_da_uri`; testes. Fora: atualização periódica (TRM-012);
norma (TRM-013); Senado (`apps/workers/crawlers/senado.py:124` continua até TRM-050).

**Critérios de aceite**
1. Dado o pacote de cada uma das 5 do placar (2269745, 2416804, 2238434, 2454704, 2426923), quando
   `registrar_proposicao` roda com o cliente de replay, então `situacao`, `cod_situacao`,
   `sigla_orgao`, `orgao_nome`, `orgao_tipo_cod`, `regime`, `apreciacao`, `ultima_movimentacao_em`,
   `status_bruto` e `detalhe_sincronizado_em` batem com o gravado.
2. Dada uma votação (pacote sintético) cuja proposição não existe, quando
   `sync_votacoes_zil.sync_single_votacao` roda, então a proposição é criada **com** o detalhe
   (critério de F0, disc. §8) e com `categorias_zil = [categoria_hint]`.
3. Dado que o detalhe falha (`FonteIndisponivel`) e há `dados_minimos`, então a proposição é criada
   com `detalhe_sincronizado_em = None` e `origem_registro` preenchido; sem `dados_minimos`, a
   exceção sobe.
4. Proposição existente com `categorias_zil` não vazia não tem a categoria alterada por nenhum
   caminho (mudança intencional em relação a `_upsert_proposicao`).
5. Rodar duas vezes com as mesmas respostas não altera nada na segunda (`alterados == ()`).
6. Teste de AST: nenhum `Proposicao(` fora de `apps/workers/tramitacao/registro.py` e
   `apps/workers/crawlers/senado.py`, em `apps/` e `scripts/`.
7. Órgão e relator: no máximo uma requisição por id na mesma execução (`CacheConsultas`).

**Specs técnicas**

```python
# apps/workers/tramitacao/registro.py
Origem = Literal["descoberta", "votacao", "votacao_zil", "cadeia_apensacao", "manual", "sync"]

@dataclass
class CacheConsultas:
    orgaos: dict[str, dict] = field(default_factory=dict)      # orgao_fonte_id → {"sigla","nome","codTipoOrgao"}
    deputados: dict[str, str | None] = field(default_factory=dict)  # fonte_id → nome

@dataclass(frozen=True)
class ResultadoRegistro:
    proposicao: Proposicao
    criada: bool
    alterados: tuple[str, ...]
    detalhe_lido: bool

def registrar_proposicao(
    db: Session,
    client: CamaraClient,
    fonte_id: str | int,
    *,
    origem: Origem,
    agora: datetime,
    cache: CacheConsultas | None = None,
    detalhe: dict | None = None,           # SÓ se lido nesta execução por client.obter_proposicao_estrito
    dados_minimos: dict | None = None,     # payload da votação: id, siglaTipo, numero, ano, ementa
    na_criacao: dict | None = None,        # categorias_zil, relevancia_zil, classificacao_automatica, contexto_status
    classificar: Callable[[dict], dict] | None = None,  # detalhe → campos de classificação; criação ou categorias vazias
) -> ResultadoRegistro: ...

def aplicar_detalhe(prop: Proposicao, detalhe: dict, *, orgao: dict | None,
                    relator_nome: str | None, agora: datetime) -> list[str]: ...
```

`aplicar_detalhe` grava, a partir de `detalhe` (o `dados` de `GET /proposicoes/{id}`): `tipo`
(`siglaTipo`), `numero`, `ano`, `ementa` (se não vazia), `ementa_detalhada`, `data_apresentacao`
(`dataApresentacao[:10]`), `url_inteiro_teor`, `situacao` (= `descricaoSituacao`, **inclusive nula**:
espelha a fonte), `cod_situacao` (`str(codSituacao)` ou nula), `ultimo_despacho` (`despacho`),
`sigla_orgao`, `orgao_fonte_id` (`id_da_uri(uriOrgao)`), `orgao_nome`/`orgao_tipo_cod` (de `orgao`),
`cod_tipo_tramitacao`, `descricao_tramitacao`, `regime`, `apreciacao`, `status_sequencia`,
`status_url`, `status_bruto`, `ultima_movimentacao_em` (`datetime.fromisoformat(dataHora)`),
`relator_fonte_id` (`id_da_uri(uriUltimoRelator)`), `relator_nome`, `principal_fonte_id`
(`id_da_uri(uriPropPrincipal)`), `detalhe_sincronizado_em = agora`. Devolve os nomes dos campos cujo
valor mudou (comparação antes/depois; `detalhe_sincronizado_em` não conta como mudança). **Nunca**
toca `categorias_zil`, `relevancia_zil`, `classificacao_automatica`, campos de enriquecimento,
`contexto_status`, norma.

`packages/tramitacao/status.py::id_da_uri(uri: str | None) -> str | None` — último segmento numérico
de `…/orgaos/2010`, `…/deputados/220572`, `…/proposicoes/2417912`.

Órgão: `cache.orgaos` ou `client.obter_orgao(id)` (TRM-012 cria o método; até lá, `client._get(f"/orgaos/{id}")`).
Falha na consulta do órgão não derruba o registro: `orgao_nome`/`orgao_tipo_cod` ficam como estavam
e o aviso vai para o log. Relator: `Parlamentar` com `fonte_id` e `fonte == CAMARA`; senão
`GET /deputados/{id}` → `dados.ultimoStatus.nome`; cacheado.

Chamadores:
1. `scripts/sync_votacoes_zil.py:128-154` → `registrar_proposicao(db, client, fonte_prop_id,
   origem="votacao_zil", agora=…, dados_minimos=prop_raw, na_criacao={"categorias_zil":
   [categoria_hint] if categoria_hint else None, "classificacao_automatica": False})`.
2. `apps/workers/crawlers/camara.py`: apagar `_upsert_proposicao` (:48-90); em :178,
   `registrar_proposicao(db, client, prop_raw["id"], origem="votacao", agora=…, dados_minimos=prop_raw,
   classificar=_classificar_pela_ementa)`, onde `_classificar_pela_ementa(detalhe)` devolve
   `{"categorias_zil": cats or None, "relevancia_zil": relevancia or None, "classificacao_automatica": True}`
   com a mesma lógica de hoje (`classificar_proposicao(ementa=…)`, `relevancia_score`).
3. `scripts/discover_proposicoes.py:174-243` → depois de decidir que a proposição entra (com o detalhe
   já lido), `registrar_proposicao(db, client, fonte_id, origem="descoberta", agora=…, detalhe=detalhes,
   na_criacao={"categorias_zil": cats, "relevancia_zil": relevancia, "classificacao_automatica": True,
   "contexto_status": "pendente" if enriquecer else None})`. O `--dry-run` continua sem gravar.

**Testes**
- `tests/unit/test_registro_proposicao.py` (replay): critérios 1, 3, 4, 5, 7; mudança de situação
  entre duas leituras (pacote alterado em memória) aparece em `alterados`.
- `tests/unit/test_sync_votacoes_zil_registro.py`: critério 2, com `pl-1264-2024` + `votacao-minima`.
- `tests/integration/test_crawler_idempotency.py`: ajustar o mock de `obter_votacao_detalhes` para
  continuar sem proposição, e acrescentar um caso com proposição usando o replay.
- `tests/unit/test_registro_unico.py`: critério 6, com `ast.walk` procurando `ast.Call` cujo `func` é
  `Name(id="Proposicao")`.
- Comando: `.venv/bin/python -m pytest tests/unit/test_registro_proposicao.py tests/unit/test_registro_unico.py tests/integration/test_crawler_idempotency.py -v`.

**Riscos e perguntas em aberto** — O crawler `sync_votacoes` cria proposição para **toda** votação do
ano (não só ZIL): agora com uma requisição de detalhe a mais por votação nova (dezenas por dia;
aceitável). A mudança do critério 4 altera comportamento — registrar no CHANGELOG em `Changed`.

**Instruções para o agente implementador** — Branch `trm-010-registrar-proposicao` (depois do merge
de TRM-011). Ordem: `id_da_uri` + `aplicar_detalhe` (puros, testados com os pacotes) →
`registrar_proposicao` → chamadores um a um, cada um com teste → teste de AST. Antes do PR, no banco
de desenvolvimento: `python scripts/sync_votacoes_zil.py --dry-run` e mostrar que não quebra.
**Não** criar proposição sem passar por `registrar_proposicao`; **não** sobrescrever categoria
existente; **não** inventar situação quando a API devolve nula.

---

### TRM-013 — Norma resultante pelo despacho (regex) + URN e links

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E1 Status honesto (F0) · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** P
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura
**Depende de:** TRM-011, TRM-002 · **Desbloqueia:** TRM-014, TRM-053

**Problema** — A lei resultante não está em lugar nenhum do ZIL. `urnFinal` vem sempre nulo (disc.
§1.6; conferido em 2269745: `"urnFinal": null`); o número da lei só aparece no texto do despacho do
marco de norma ("Transformado na Lei Ordinária 14871/2024", disc. §3.2-6), e o último registro
costuma ser um ofício posterior (disc. §3.2-3).

**Oportunidade** — "Virou a Lei 14.871, de 28/05/2024", com link, nas proposições mais visíveis do
site (4 das 5 do placar).

**Solução** — Funções puras em `packages/tramitacao/normas.py` que extraem a norma das linhas de
`/tramitacoes` com código 251 ou 1012 e montam rótulo, URN e links; o sync (TRM-012) chama e grava
nas colunas de norma (§1.3).

**Escopo** — Dentro: regex, rótulo, URN, links, gravação, testes com despachos reais. Fora: veto total
(1013 não gera norma), Senado `normaGerada` e curadoria (TRM-053), conferir links pela rede.

**Critérios de aceite**
1. Com os pacotes: PL 2/2024 → `lei_ordinaria 14871/2024`, data 2024-05-28, veto `parcial`;
   PL 327/2021 → `lei_ordinaria 15103/2025`, 2025-01-22, `parcial`; PL 278/2026 → `lei_ordinaria
   15504/2026`, 2026-09-15, sem veto; PLP 68/2024 → `lei_complementar 214/2025`, `parcial`;
   PEC 45/2019 → nenhuma (situação 1140 sem marco; A9).
2. `url_planalto("lei_ordinaria", 14871, 2024)` = `https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/L14871.htm`
   e `(…, 15103, 2025)` = `…/_ato2023-2026/2025/lei/L15103.htm` (os dois links verificados no disc.
   "Fontes"); `url_normas_leg("lei_ordinaria", 15103, date(2025, 1, 22))` =
   `https://normas.leg.br/?urn=urn:lex:br:federal:lei:2025-01-22;15103` (A14).
3. `rotulo_norma("lei_ordinaria", 14871, 2024)` = `"Lei 14.871/2024"`; LC → `"Lei Complementar 214/2025"`.
4. Texto que não é marco de norma não gera norma: despacho "Altera a Lei nº 8.666/1993" em linha 251
   → `None`; "Vetado totalmente" → `None`; linha com código ≠ 251/1012 nunca é lida.
5. Uma norma gravada com `norma_fonte = "despacho_camara"` não é apagada por uma leitura posterior
   que não ache nada; norma de fonte `senado_norma_gerada` ou `curadoria` nunca é sobrescrita.

**Specs técnicas**

```python
# packages/tramitacao/normas.py
CODIGOS_TRAMITACAO_NORMA = frozenset({"251", "1012"})    # conferir com marcos.yml (`extrai_norma`) em TRM-024

_NORMA_RE = re.compile(
    r"Transformad[oa]\s+n[ao]\s+"
    r"(?P<tipo>Lei\s+Complementar|Lei\s+Ordin[aá]ria|Lei|Decreto\s+Legislativo|"
    r"Emenda\s+Constitucional|Resolu[cç][aã]o)"
    r"\s+(?:n[º°o.]*\s*)?(?P<numero>\d{1,3}(?:\.\d{3})+|\d+)\s*/\s*(?P<ano>\d{4})",
    re.IGNORECASE,
)
_VETO_PARCIAL_RE = re.compile(r"vetad[oa]\s+parcialmente", re.IGNORECASE)

TipoNorma = Literal["lei_ordinaria", "lei_complementar", "lei", "decreto_legislativo",
                    "emenda_constitucional", "resolucao"]

@dataclass(frozen=True)
class NormaExtraida:
    tipo: TipoNorma
    numero: int
    ano: int
    data: date | None          # data da linha (dataHora[:10])
    veto: Literal["parcial"] | None
    sequencia: int | None
    trecho: str                # até 160 caracteres do despacho, para auditoria e log

def extrair_norma_de_texto(texto: str) -> tuple[TipoNorma, int, int] | None: ...
def extrair_norma(tramitacoes: Sequence[dict]) -> NormaExtraida | None: ...
    # só linhas com codTipoTramitacao ∈ CODIGOS_TRAMITACAO_NORMA, da maior `sequencia` para a menor;
    # veto "parcial" se cod == "1012" ou _VETO_PARCIAL_RE casa
def rotulo_norma(tipo: TipoNorma, numero: int, ano: int) -> str: ...
def urn_lex(tipo: TipoNorma, numero: int, data: date | None) -> str | None: ...
    # lei_ordinaria|lei → "lei"; lei_complementar → "lei.complementar";
    # decreto_legislativo → "decreto.legislativo"; emenda_constitucional → "emenda.constitucional";
    # resolucao ou data None → None. Formato: f"urn:lex:br:federal:{t}:{data.isoformat()};{numero}"
def url_normas_leg(tipo: TipoNorma, numero: int, data: date | None) -> str | None: ...
def url_planalto(tipo: TipoNorma, numero: int, ano: int) -> str | None: ...
```

`url_planalto`: `lei_ordinaria`/`lei` com `2004 ≤ ano ≤ 2030` →
`https://www.planalto.gov.br/ccivil_03/_ato{p}/{ano}/lei/L{numero}.htm`, `p` pela tabela
`{2004–2006: "2004-2006", 2007–2010: "2007-2010", 2011–2014: "2011-2014", 2015–2018: "2015-2018",
2019–2022: "2019-2022", 2023–2026: "2023-2026", 2027–2030: "2027-2030"}`; `lei_complementar` →
`https://www.planalto.gov.br/ccivil_03/leis/lcp/Lcp{numero}.htm`; `emenda_constitucional` →
`https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc{numero}.htm`; demais → `None`.
Os links são **montados por padrão, não conferidos** (Planalto dá timeout fora do Brasil, A15):
a API devolve `links_verificados: false`.

Gravação (`apps/workers/tramitacao/sincronizacao.py::aplicar_norma(prop, norma, agora) -> list[str]`,
chamada por TRM-012 com as tramitações já baixadas): regras do critério 5; grava
`norma_tipo/numero/ano/data/veto`, `norma_fonte = "despacho_camara"`, `norma_tramitacao_sequencia`,
`norma_verificada_em = agora`. Se a extração nova difere da gravada (mesma fonte), sobrescreve e
registra aviso em `erro_detalhes` com `etapa: "norma_mudou"` (não conta como erro).

**Testes** — `tests/unit/test_normas.py`: critérios 1–4 com os despachos dos pacotes (lidos por
`gravacoes.corpo`), mais strings literais copiadas dos pacotes para formas raras (`Lei nº 14.871/2024`,
`14.871/2024` com ponto, "Transformada na Lei"); critério 5 em `tests/unit/test_sync_tramitacao.py`.
Comando: `.venv/bin/python -m pytest tests/unit/test_normas.py -v`.

**Riscos e perguntas em aberto** — A data do marco pode não ser a da assinatura em algum caso
(o URN não resolveria): TRM-053 corrige pelo `normaGerada.dataAssinatura` do Senado. EC e decreto
legislativo: o formato do despacho não foi visto em gravação (PEC 45/2019 não tem o marco); se
TRM-002 não trouxer exemplo real, o teste de EC/DL cobre só a regex com texto literal marcado
"forma esperada, não observada". Medir a taxa do disc. §3.2-6 (573/593) fica para o relatório de
TRM-017.

**Instruções para o agente implementador** — Branch `trm-013-norma-despacho`. Funções puras primeiro,
com testes; `aplicar_norma` entra no PR de TRM-012 se este ainda não existir (ou vice-versa — o que
mergear depois chama o outro). **Não** usar `urnFinal`; **não** chamar Planalto nem normas.leg.br;
**não** aplicar a regex fora das linhas 251/1012; **não** inferir norma de veto total.

---

### TRM-012 — `scripts/sync_tramitacao.py`: diário (D-7 ∩ acompanhadas) + reconciliação; `Retry-After`; `IngestionRun`

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E1 Status honesto (F0) · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; Maintainer (ligação ao cron de produção)
**Depende de:** TRM-010, TRM-011, TRM-013; PR #47 só para o último passo (ligar ao `agenda.py`) · **Desbloqueia:** TRM-014 (dados reais), TRM-016, TRM-017, TRM-026, TRM-027

**Problema** — Nada atualiza a situação depois da criação (disc. §1.2-2): o que aparece é a foto do
dia em que a proposição entrou. O cliente da Câmara ignora `Retry-After` (backoff próprio de 2/4/8 s,
`packages/camara_client/__init__.py:104-126`) e, esgotadas as tentativas, **devolve `[]` em silêncio**
(:126) — o chamador não distingue "sem dados" de "fonte fora".

**Oportunidade** — A situação de cada proposição acompanhada fica no máximo um dia atrasada em
relação à Câmara, com registro auditável de cada execução.

**Solução** — Cliente com política de retentativa explícita e métodos "estritos" que levantam erro;
módulo de sincronização com seleção de alvos, orçamento de requisições e registro em
`ingestion_runs`; CLI própria; por último, ligação ao `scripts/agenda.py` depois do merge do PR #47.

**Escopo** — Dentro: cliente (Retry-After, contador, intervalo mínimo, estritos, `listar_movimentadas`);
`sincronizacao.py`; CLI `diario`/`completo`/`uma`; IngestionRun; norma (chama TRM-013); passo do cron.
Fora: gravar tramitações (TRM-026), fase (TRM-027), Senado (TRM-050), agenda/pauta (TRM-051).

**Critérios de aceite**
1. Dado 429 com `retry-after: 2` e depois 200 (sintético), o cliente dorme 2 s (via `dormir`
   injetado) e devolve o 200; dado 503 sem `Retry-After`, dorme 2 e 4 s; dado 500 persistente,
   levanta `FonteIndisponivel` depois de `max_tentativas`; `retry-after` em resposta 200 é ignorado (A1).
2. `listar_movimentadas` lê todas as páginas e confere `x-total-count`; se o total lido não bater,
   levanta `ListagemIncompleta`.
3. `diario` com `hoje` fixo e o pacote `janela-d7`: alvos = (acompanhadas ∩ movimentadas) ∪
   acompanhadas com `detalhe_sincronizado_em` nulo; acompanhadas = Câmara com `categorias_zil` não
   nula (D2: depois de TRM-027, também as cabeças de cadeia).
4. Rodar `completo` duas vezes com as mesmas respostas: a segunda tem `atualizados == 0` e
   `criados == 0`.
5. Cada execução não-dry-run grava uma `IngestionRun` (`tipo` `tramitacao_diaria`,
   `tramitacao_completa` ou `tramitacao_manual`) com `status`, contagens, `finalizado_em` e
   `erro_detalhes` (até 100 itens).
6. Falha de uma proposição não interrompe as outras (`partial`); falha na listagem da janela →
   `failed`, saída 1; erros em mais da metade dos alvos (com ≥ 4 alvos) → `failed`.
7. Orçamento: ao atingir `--orcamento` requisições ou `--tempo-max-min`, para de pegar alvos novos,
   termina o atual, fecha como `partial` com `{"etapa": "orcamento", "nao_processados": N}`.
8. Em desenvolvimento, depois de `completo`, as 5 do placar têm a situação da Câmara do dia e as 4
   que viraram lei têm norma (critério de F0, disc. §8).
9. `--dry-run` lê a API, não grava nada (nem IngestionRun) e imprime o que mudaria.
10. Os chamadores antigos de `CamaraClient._get` continuam recebendo `[]` em falha (comportamento
    preservado; teste).
11. Órgão efetivo (A19): com `pl-3474-2023` (status em CCP), `orgao_efetivo_sigla`/`orgao_efetivo_nome`
    são os da comissão do registro mais recente em comissão; com `pl-1264-2024` (status na CFT), são
    os do próprio status. `TIPOS_ORGAO_COMISSAO = ("2", "3", "6", "9", "21", "13000", "81002")` e
    `SIGLAS_PLENARIO = ("PLEN",)` em `packages/tramitacao/status.py`; o validador (V-E9) exige que os
    parâmetros da R7 em `fases.yml` sejam iguais a essas constantes.

**Specs técnicas**

Cliente (`packages/camara_client/__init__.py`):

```python
class FonteIndisponivel(Exception):
    def __init__(self, caminho: str, status: int | None, tentativas: int, causa: str) -> None: ...
class ListagemIncompleta(FonteIndisponivel): ...
class RecursoNaoEncontrado(Exception): ...           # 404

RETENTAVEIS = frozenset({429, 500, 502, 503, 504})
COM_RETRY_AFTER = frozenset({429, 503})

def segundos_retry_after(valor: str | None, agora: datetime) -> float | None:
    """Inteiro em segundos ou HTTP-date (email.utils.parsedate_to_datetime); None se ausente/ilegível."""

class CamaraClient:
    def __init__(self, base_url: str = BASE_URL, *, transport: httpx.BaseTransport | None = None,
                 dormir: Callable[[float], None] = time.sleep, intervalo_minimo: float = 0.0,
                 max_tentativas: int = 4, espera_max: float = 120.0) -> None: ...
    requisicoes: int                                   # contador de requisições enviadas
    def _resposta(self, path: str, params: dict | None = None) -> httpx.Response: ...
    def _get(self, path: str, params: dict | None = None) -> Any: ...   # legado: _resposta + "dados"; FonteIndisponivel → log + []
    def _get_paginado_estrito(self, path: str, params: dict, max_paginas: int = 60) -> list[dict]: ...
    def obter_proposicao_estrito(self, proposicao_id: int) -> dict: ...
    def obter_tramitacoes_estrito(self, proposicao_id: int) -> list[dict]: ...
    def obter_autores_estrito(self, proposicao_id: int) -> list[dict]: ...
    def obter_orgao(self, orgao_id: str | int) -> dict: ...
    def obter_deputado_estrito(self, deputado_id: str | int) -> dict: ...
    def listar_movimentadas(self, inicio: date, fim: date, tipos: Sequence[str]) -> list[dict]: ...
        # /proposicoes?dataInicio=&dataFim=&siglaTipo=PL,PLP,PEC,MPV,PDL&itens=100&ordem=ASC&ordenarPor=id
```

`_resposta`: espera `intervalo_minimo` desde a requisição anterior; envia; `requisicoes += 1`; se
status ∈ `RETENTAVEIS` e ainda há tentativa: espera = `segundos_retry_after` (só para
`COM_RETRY_AFTER`) ou `2 × 2^tentativa`, limitada a `[1, espera_max]`, via `dormir`; 404 →
`RecursoNaoEncontrado`; outro ≥ 400 → `FonteIndisponivel` sem retentar; `httpx.RequestError` →
retenta com o mesmo backoff; esgotou → `FonteIndisponivel`. Log em nível `WARNING` com caminho,
status e espera — nunca a URL do banco nem cabeçalhos de autenticação (não há).

Sincronização (`apps/workers/tramitacao/sincronizacao.py`):

```python
@dataclass
class Orcamento:
    max_requisicoes: int
    prazo_monotonic: float                 # time.monotonic() + tempo_max
    def esgotado(self, client: CamaraClient) -> bool: ...

@dataclass
class ResultadoSync:
    processados: int = 0
    criados: int = 0                       # TRM-026: linhas de tramitação novas
    atualizados: int = 0                   # proposições com algum campo alterado
    erros: int = 0
    nao_processados: int = 0
    requisicoes: int = 0
    status: Literal["success", "partial", "failed"] = "success"
    erro_detalhes: list[dict] = field(default_factory=list)   # {"fonte_id","etapa","erro"}

def alvos_completo(db: Session) -> list[Proposicao]: ...
def alvos_diario(db: Session, client: CamaraClient, hoje: date, dias: int = 7) -> list[Proposicao]: ...
def sincronizar_proposicao(db: Session, client: CamaraClient, prop: Proposicao, *, agora: datetime,
                           cache: CacheConsultas) -> list[str]: ...
    # F0: detalhe estrito → aplicar_detalhe; tramitações estritas → aplicar_norma e órgão efetivo (A19).
    # orgao_efetivo(status, linhas, tipo_do_orgao) — puro, em packages/tramitacao/status.py:
    #   o órgão do status se sigla == "PLEN" ou tipo ∈ TIPOS_ORGAO_COMISSAO; senão percorre as linhas da maior
    #   para a menor sequência e devolve o primeiro órgão assim; `tipo_do_orgao` consulta o CacheConsultas
    #   (uma requisição por órgão novo; costuma parar em 1 a 3).
    # TRM-026 acrescenta: upsert de eventos. TRM-027: casa iniciadora, cadeia, fase.
def executar(db: Session, client: CamaraClient, modo: Literal["diario", "completo", "uma"], *,
             hoje: date, agora: datetime, dias: int = 7, fonte_id: str | None = None,
             dry_run: bool = False, orcamento: Orcamento, registrar_execucao: bool = True) -> ResultadoSync: ...
```

Ordem dos alvos: `int(fonte_id)` crescente (determinístico). Commit por proposição (progresso
parcial persiste); em `dry_run`, `db.rollback()` no fim. IngestionRun: até o merge do PR #47, criada e
fechada direto no módulo (mesmo padrão de `scripts/sync_votacoes_zil.py:266-310`); depois do merge,
trocar por `apps.workers.execucoes.abrir_execucao`/`fechar_execucao` (`git show
origin/047-deploy-cron:apps/workers/execucoes.py`).

CLI (`scripts/sync_tramitacao.py`, `argparse` com subcomandos, como `scripts/agenda.py` do #47):

```
.venv/bin/python scripts/sync_tramitacao.py diario    [--dias 7] [--orcamento 600]  [--tempo-max-min 30] [--dry-run]
.venv/bin/python scripts/sync_tramitacao.py completo  [--orcamento 1500] [--tempo-max-min 40] [--dry-run]
.venv/bin/python scripts/sync_tramitacao.py uma --fonte-id 2269745 [--dry-run]   # registra se não existir (origem "manual")
```

`hoje` = data em `America/Sao_Paulo`; cliente com `intervalo_minimo=0.25`. Saída 0 para `success`
e `partial`, 1 para `failed`. Resumo impresso: alvos, processados, atualizados, erros, requisições,
duração.

Orçamento de requisições (estimativa conferida com A2):

| Passo | `diario` | `completo` |
| --- | --- | --- |
| Janela D-7 (2.227 itens ÷ 100) | ≈ 23 | — |
| Detalhe + tramitações por alvo | 2 × ~30 = 60 | 2 × ~270 = 540 |
| Órgãos distintos (cache) | ≤ 15 | ≤ 40 |
| Relatores fora de `parlamentares` (cache) | ≤ 10 | ≤ 30 |
| `/autores` (TRM-027, só com casa iniciadora nula) | ~0 | 270 na primeira vez, ~0 depois |
| **Total típico / padrão de `--orcamento`** | **≈ 110 / 600** | **≈ 610 (≈ 880 na 1ª) / 1500** |

Com 0,25 s entre chamadas e ~0,4 s de latência: `diario` < 2 min; `completo` ≈ 7–10 min. Ambos
dentro do `timeout-minutes: 45` do workflow `dados.yml` do PR #47.

**Último passo — ligar ao cron (depois do merge do PR #47):** em `scripts/agenda.py`, passo
`Passo("tramitacao_diaria", _tramitacao("diario"))` no job `diario` **depois** de `proposicoes` e
antes de `scores`; `Passo("tramitacao_completa", _tramitacao("completo"))` no job semanal
`cadastros`; subcomando `tramitacao` para rodar isolado; `_tramitacao` chama `executar(...,
registrar_execucao=False)` (o `agenda.rodar_passo` já abre a IngestionRun) e devolve `Contagem`.
Em `.github/workflows/dados.yml`, `tramitacao` nas opções do `workflow_dispatch`. Teste em
`tests/unit/test_agenda.py`: ordem dos passos no `diario` e no `cadastros`.

**Testes**
- `tests/unit/test_camara_client_retry.py` (sintéticos): critérios 1, 2, 10.
- `tests/unit/test_sync_tramitacao.py` (replay + SQLite): critérios 3–7, 9; `aplicar_norma` (TRM-013 crit. 5).
- Comando: `.venv/bin/python -m pytest tests/unit/test_camara_client_retry.py tests/unit/test_sync_tramitacao.py -v`.
- Prova manual (critério 8): `python scripts/sync_tramitacao.py completo --dry-run`, depois sem
  `--dry-run`, e `SELECT tipo, numero, ano, situacao, sigla_orgao, norma_numero FROM proposicoes WHERE
  fonte_id IN ('2269745','2416804','2238434','2454704','2426923')`.

**Riscos e perguntas em aberto** — A semântica de `dataInicio` foi conferida ao vivo (A2), mas pode
mudar: o teste de seleção usa o pacote gravado, e a reconciliação semanal (`completo`) cobre
qualquer perda. `codSituacao` como filtro de `/proposicoes` parece ignorado (disc. §3.2-7): não usar.

**Instruções para o agente implementador** — Branch `trm-012-sync-tramitacao`. Ordem: cliente
(retentativa, contador, estritos) com testes sintéticos → `sincronizacao.py` → CLI → prova no banco
de desenvolvimento → (PR separado, depois do #47) cron. **Não** tratar `retry-after` de resposta 200
como limite; **não** devolver `[]` em falha nos métodos novos; **não** rodar `completo` no job
diário; **não** chamar o Senado; **não** cair para `completo` quando a janela falhar — falhar alto.

---

### TRM-014 — API: `ProposicaoRead` expõe os campos novos + `url_camara`

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E1 Status honesto (F0) · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** P
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; UI/UX (consumidor do contrato, TRM-015/016)
**Depende de:** TRM-011, TRM-013; TRM-021 (só o carregador do glossário, para `*_texto`); PR #49 (mesmo schema) · **Desbloqueia:** TRM-015, TRM-016, TRM-017. O e2e de TRM-016 só lê `X-Total-Count` se a API falsa de TRM-001 expuser o cabeçalho por CORS (revisão de Arquitetura, item 1)

**Problema** — `ProposicaoRead` (`apps/api/schemas/__init__.py:48-67`) expõe só `situacao`; não há
link para a página da Câmara em nenhuma proposição (disc. §1.5); a lista ordena por "analisadas
primeiro" e não por movimentação (`apps/api/routers/legislativo.py:93`).

**Oportunidade** — A página v0 e a lista v0 (UI/UX) passam a ter tudo o que precisam numa chamada.

**Solução** — Os campos de TRM-014 em §1.5, montados por uma função do router; `ordem=movimentacao`
na lista; textos de regime e apreciação vindos do glossário **só** quando publicáveis (lote L0, spec
§6.12).

**Escopo** — Dentro: schema, montagem, normalização de regime/apreciação, `situacao_estado`,
`url_camara`, `norma`, ordenação, testes de contrato, tipos em `apps/web/lib/api.ts` (só a interface
`Proposicao`, sem uso na interface). Fora: campos de fase (TRM-028); mudança de layout (TRM-015/016).

**Critérios de aceite**
1. `GET /proposicoes` e `GET /proposicoes/{id}` devolvem todos os campos de TRM-014 em §1.5, com os
   tipos declarados (teste de contrato).
2. `url_camara` = `https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={fonte_id}`
   para 100% das proposições da Câmara (critério de F0, disc. §8); nula para o Senado.
3. `situacao_estado`: `nao_sincronizada` se `detalhe_sincronizado_em` nula; `informada` se `situacao`
   não nula; `recem_apresentada` se `data_apresentacao` há ≤ 90 dias; senão `sem_situacao`.
4. `regime_chave`/`apreciacao_chave` pela tabela abaixo; texto oficial sempre presente em `regime`/`apreciacao`.
5. Com `revisao.yml` sem `glossario/regime_urgencia` aprovado, `regime_texto` é nulo; com a entrada
   aprovada e hash conferido (diretório temporário via `ZIL_DATA_DIR`), é o `texto_curto`.
6. `GET /proposicoes?ordem=movimentacao` ordena por `ultima_movimentacao_em` desc, nulos por último,
   empate por `id`; sem `ordem`, a ordem atual não muda.
7. `norma` presente quando há `norma_numero`, com `rotulo`, links e `links_verificados: false`.
8. Falha ao carregar o mapa não derruba `ProposicaoRead`: textos nulos e um `logger.warning` por processo.
9. Com `PL 399/2025` (pacote `pl-399-2025`, urgência + conclusiva) registrado, `apreciacao_chave ==
   "apreciacao_conclusiva_com_urgencia"`; com só `glossario/apreciacao_conclusiva` publicável,
   `apreciacao_texto` é nulo.
10. `GET /proposicoes` devolve `X-Total-Count` com o total filtrado (com `categoria`, `tipo`, `ano`,
    `analise`), exposto no CORS; com 240 acompanhadas e `per_page=100`, o cabeçalho diz 240.
11. `ultima_movimentacao_em` e `detalhe_sincronizado_em` saem com `-03:00` (§1.5, "Datas e horas");
    `data_apresentacao` sai `"AAAA-MM-DD"`.
12. `orgao_efetivo_sigla`/`orgao_efetivo_nome` expostos (TRM-012 os calcula); `principal_url_camara`
    no mesmo padrão de `url_camara`; `situacao_glossario` = chave da entrada cujos `codigos` contêm
    `("camara", cod_situacao)`, ou nula.

**Specs técnicas**
- `packages/tramitacao/status.py`:

```python
def normalizar_regime(regime: str | None) -> str | None: ...
def normalizar_apreciacao(apreciacao: str | None, regime: str | None = None) -> str | None: ...   # regra de urgência abaixo
def situacao_estado(*, situacao: str | None, detalhe_sincronizado_em: datetime | None,
                    data_apresentacao: date | None, hoje: date, dias_recente: int = 90) -> SituacaoEstado: ...
```

| Ordem | Regex (`re.IGNORECASE`) sobre o texto oficial | Chave | Observado (A22) |
| --- | --- | --- | --- |
| 0 | texto vazio ou só pontuação (`^\W*$`, ex.: ".") | `None` — é ausência, não regime; **o campo `regime` também sai nulo na API** (pedido de UI/UX; o banco guarda o texto como veio) | 32 |
| 1 | `\bart\.?\s*155\b` | `regime_urgencia` | 42 |
| 2 | `\bart\.?\s*62\b.*\bCF\b` | `regime_medida_provisoria` | 12 |
| 3 | `\bart\.?\s*64\b.*\bCF\b` ou `\bCF\b.*\bart\.?\s*64\b` | `regime_urgencia_constitucional` | 2 |
| 4 | `\b151\s*,\s*I\b\s*["“]?j` | `regime_urgencia_acordo_internacional` | 9 |
| 5 | `\b151\s*,\s*III\b` | `regime_ordinaria` | 132 |
| 6 | `\b151\s*,\s*II\b` | `regime_prioridade` | 10 |
| 7 | `\bart\.?\s*223\b` | `regime_concessao_radiodifusao` | 1 |
| — | outro | `None` (o texto oficial continua no ar) | — |
| 0 | `^indefinida$` | `None` — ausência; **o campo `apreciacao` também sai nulo na API** | 32 |
| 1 | `conclusiva` | `apreciacao_conclusiva` (inclui "…Conclusiva (Parecer 09/90 - CCJR)") | 140 |
| 2 | `plen[aá]rio` | `apreciacao_plenario` | 68 |

  **Regra de urgência + conclusiva** (A18; RICD art. 24, II, h): se o texto do regime começa com
  "Urgência" (comparação sem acento e sem caixa) **e** a apreciação normalizada é
  `apreciacao_conclusiva`, então `apreciacao_chave = "apreciacao_conclusiva_com_urgencia"` e
  `apreciacao_texto` vem dessa entrada; se ela não for publicável, `apreciacao_texto` é `null` —
  **nunca** o texto da conclusiva pura, que diria algo falso ("segue sem votação no Plenário") nos 9
  casos de hoje. O campo `apreciacao` continua com o texto oficial, inteiro.

  Casos de teste: as 8 formas de regime e as 4 de apreciação de A22, mais "Ordinária (Art. 151, III,
  RICD)" (A13) e o par "Urgência (Art. 155, RICD)" + "Proposição Sujeita à Apreciação Conclusiva pelas
  Comissões - Art. 24 II" → `apreciacao_conclusiva_com_urgencia`.
- `apps/api/routers/legislativo.py`: `def _proposicao_read(p: Proposicao, *, hoje: date, mapa: Mapa
  | None) -> ProposicaoRead` (padrão de `_votacao_to_read`, :33-57); `listar_proposicoes` e
  `obter_proposicao` passam a montar por ela (`response_model` inalterado). `mapa` vem de
  `_mapa_ou_none()`, que chama `carregar_mapa_producao()` e devolve `None` em
  `MapaIndisponivel`/`MapaInvalido`. Texto: `mapa.glossario[chave].texto_curto` se
  `mapa.publicavel(f"glossario/{chave}")`.
- Parâmetro `ordem: Literal["padrao", "movimentacao"] = Query("padrao")`.
- `listar_proposicoes` recebe `response: Response` e grava `response.headers["X-Total-Count"] =
  str(total)`, com `total` de um `select(func.count())` sobre a mesma consulta sem `offset/limit`;
  `apps/api/main.py`: `CORSMiddleware(..., expose_headers=["X-Total-Count"])`.
- Tipos `HorarioCamara` e `InstanteUTC` (§1.5, "Datas e horas") em `apps/api/schemas/__init__.py`,
  usados nos campos novos; campos antigos (`data_apresentacao`, `enriquecido_em` etc.) não mudam.
- `NormaResumo` montado de `norma_*` com as funções de `packages/tramitacao/normas.py`.
- `apps/web/lib/api.ts`: interface `Proposicao` com os campos novos (todos `| null`, exceto
  `situacao_estado` e `apensada`). Nenhum componente muda neste PR.
- Rebase sobre o PR #49 se já mergeado: manter o `model_validator` `_resumo_so_quando_pronto`.

**Testes** — `tests/contract/test_api_schema.py::test_schema_proposicao_read` com os campos novos;
`tests/contract/test_api_proposicao_f0.py` (critérios 2–8; `carregar_mapa_producao.cache_clear()` em
fixture); `tests/unit/test_status.py` (tabela de normalização e `situacao_estado`). Comandos:
`.venv/bin/python -m pytest tests/contract -v`; `cd apps/web && npx tsc --noEmit`.

**Achados de código de UI/UX (conferidos) e onde ficam** — "Apresentada em" com um dia a menos: o
backend manda `data_apresentacao` como `"AAAA-MM-DD"` (correto); o erro é o frontend passar a data por
`new Date()` (UTC) — corrige TRM-015. Lista com só 100 das 240: o frontend pede uma página
(`per_page=100`); TRM-016 pagina, e este TRM-014 acrescenta `X-Total-Count` (critério 10). Erro 500
tratado como proposição: falta `res.ok` no frontend (`apps/web/app/proposicoes/[id]/page.tsx:71-72`);
a API já responde 404/422/500 com status certo — corrige TRM-015. Nenhum exige tarefa nova de backend
(não criei TRM-018).

**Riscos e perguntas em aberto** — `situacao_estado` usa "hoje" do servidor (UTC no Render): a
diferença de horas não muda o resultado em limites de 90 dias de forma relevante; usar
`America/Sao_Paulo` mesmo assim. O "desde" que TRM-015 pede só existe a partir de TRM-027
(`fase_desde`/`orgao_desde`); em F0 a interface usa "Última movimentação em" (`ultima_movimentacao_em`).

**Instruções para o agente implementador** — Branch `trm-014-api-f0`. Ordem: `status.py` + testes →
schema → montagem → `ordem` → contrato → `api.ts`. Prova: `curl localhost:8000/proposicoes/<id>`
de uma do placar, depois do sync. **Não** derivar fase aqui; **não** devolver texto de glossário não
publicável; **não** remover campos existentes.

---

## 4. Tarefas — E2 (Mapa, glossário, motor, histórico e API de tramitação)

### TRM-020 — Snapshots das tabelas de referência + script de atualização com diff

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E2 Mapa e glossário · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** P
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura
**Depende de:** — · **Desbloqueia:** TRM-021, TRM-022, TRM-024 (cobertura), TRM-025

**Problema** — A Câmara tem 99 códigos de situação e 235 tipos de tramitação; o Senado, 175 tipos de
situação (disc. §3.1, §3.3); nenhum tem ordem oficial nem agrupamento por fase. O mapa do ZIL precisa
de uma lista fechada e datada contra a qual provar cobertura, e de um jeito de saber quando a fonte
muda (disc. §9, "Tabelas de código mudam").

**Oportunidade** — Cobertura verificável na CI e mudança da fonte vista num diff de PR, nunca em
produção.

**Solução** — Quatro snapshots JSON em `data/tramitacao/referencias/` (§2.7) e
`scripts/atualizar_referencias_tramitacao.py`, que baixa, compara, mostra a diferença e grava.

**Escopo** — Dentro: snapshots, script, funções puras de diff, `nao_mapeados.yml` para códigos novos.
Fora: mapear códigos (TRM-021); cron (o script muda arquivos do repositório, não o banco — roda por
PR, não no `agenda.py`).

**Critérios de aceite**
1. Os quatro arquivos de §2.7 existem com `total` igual ao número de itens (99, 235, 55, 175 em
   2026-10-30) e itens ordenados.
2. `--verificar` sem diferença sai 0; com diferença imprime novos, removidos e renomeados e sai 2;
   erro de rede sai 1 e não grava nada.
3. Sem `--verificar`: grava os snapshots que mudaram (`obtido_em` = hoje só nesses); acrescenta cada
   código **novo** a `nao_mapeados.yml` com `motivo: codigo_novo_AAAA-MM-DD` (spec §6.10), mantendo a
   ordem; código renomeado: troca o `descricao_oficial` em `fases.yml`/`marcos.yml`/`glossario.yml`/
   `nao_mapeados.yml` por substituição textual da string antiga **exata**, e aborta sem gravar nada se
   o número de substituições não for o esperado; código removido: não mexe em mapeamento (o validador
   acusa) e lista o que precisa de decisão humana.
4. Recusa gravar snapshot com 0 itens ou com mais de 10% a menos que o anterior sem
   `--aceitar-remocoes`.
5. Imprime a lista de entradas afetadas (`<arquivo>/<chave>`) para o lote de revisão (spec §6.10;
   o formato de `lotes.yml` é de TRM-023 — até lá, só imprime).

**Specs técnicas**
- `packages/tramitacao/referencias.py`:

```python
TABELAS: dict[str, tuple[str, str]] = {   # nome do arquivo → (url, campo do código)
    "camara-situacoes.json": ("https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codSituacao", "cod"),
    "camara-tipos-tramitacao.json": ("https://dadosabertos.camara.leg.br/api/v2/referencias/proposicoes/codTipoTramitacao", "cod"),
    "camara-tipos-orgao.json": ("https://dadosabertos.camara.leg.br/api/v2/referencias/orgaos/codTipoOrgao", "cod"),
    "senado-tipos-situacao.json": ("https://legis.senado.leg.br/dadosabertos/processo/tipos-situacao", "sigla"),
}

@dataclass(frozen=True)
class Diferenca:
    novos: tuple[dict, ...]
    removidos: tuple[dict, ...]
    renomeados: tuple[tuple[str, str, str], ...]     # (cod, nome antigo, nome novo), comparados com strip()

def normalizar_itens(arquivo: str, dados: list[dict]) -> list[dict]: ...   # Câmara: cod,nome,sigla,descricao; Senado: cod(=sigla),id,nome(=descricao),data_inicio,data_fim
def carregar_snapshot(diretorio: Path, arquivo: str) -> dict: ...
def diferenca(antigo: list[dict], novo: list[dict]) -> Diferenca: ...
def serializar(snapshot: dict) -> str: ...                                  # json.dumps(ensure_ascii=False, indent=2) + "\n"
```

- Script: `httpx.Client(timeout=30, transport=…)` próprio (não depende do cliente estrito de TRM-012;
  `raise_for_status`), um GET por tabela, intervalo de 1 s. Uso:
  `.venv/bin/python scripts/atualizar_referencias_tramitacao.py [--verificar] [--aceitar-remocoes] [--dir data/tramitacao]`.
- Gerar os snapshots iniciais com o próprio script e commitar.

**Testes** — `tests/unit/test_referencias_tramitacao.py`: `diferenca` (novos, removidos, renomeado com
espaço sobrando não conta como renomeado); `normalizar_itens` para Câmara e Senado; recusa de
snapshot vazio; substituição textual com contagem errada aborta (diretório temporário); script com
`httpx.MockTransport` (sem rede). Comando: `.venv/bin/python -m pytest tests/unit/test_referencias_tramitacao.py -v`.

**Riscos e perguntas em aberto** — Códigos duplicados por nome (905 e 1382 têm a mesma descrição):
a chave é o código, nunca o nome. O Senado pode trocar `sigla`: aparece como removido + novo.

**Instruções para o agente implementador** — Branch `trm-020-referencias`. Funções puras + testes →
script → gerar os quatro arquivos → conferir as contagens. **Não** normalizar o texto gravado (só a
comparação); **não** ligar ao cron de produção.

---

### TRM-021 — Mapa v0 em `data/tramitacao/`: esquema, carga e conteúdo-rascunho com base legal

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E2 Mapa e glossário · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** G — em dois PRs: **021a** esquema + carga + `revisao.py` + esqueleto (M); **021b** conteúdo v0 (M)
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; o conteúdo passa por TRM-023/TRM-029 (agentes + maintainer) antes de publicar
**Depende de:** TRM-020 · **Desbloqueia:** TRM-022 (esquema do glossário), TRM-023 (chaves), TRM-024, TRM-025, TRM-026, TRM-029; TRM-014 (só o carregador)

**Problema** — Não existe ordem oficial das situações nem mapa situação → fase (disc. §4.4). O
discovery propõe fases, regras R1–R10 e ritos, mas como tabela de documento, sem base legal por
entrada, sem cobertura e sem forma de revisão.

**Oportunidade** — O conhecimento sobre o processo legislativo vira dado versionado, citável e
testável — no mesmo espírito de `data/direcoes/`, com o gate de aprovação da spec §6.

**Solução** — (021a) `packages/tramitacao/{tipos,mapa,revisao}.py` com os modelos de §2, o
`Mapa` e `carregar_mapa`; `apps/workers/tramitacao/revisao.py` reexportando; arquivos vazios válidos.
(021b) O conteúdo mínimo v0 abaixo, todo como **rascunho** (nenhuma linha em `revisao.yml`).

**Escopo** — Dentro: esquema, carga, hash, publicáveis, `fases.yml`, `marcos.yml`, `ritos.yml`,
`nao_mapeados.yml`, `revisao.yml` inicial, `glossario.yml` só com o cabeçalho. Fora: textos do
glossário (TRM-022, UI/UX); validador e CI (TRM-024); processo de revisão (TRM-023); mapeamento do
Senado (TRM-050).

**Critérios de aceite**
1. (021a) `carregar_mapa()` carrega os arquivos do repositório sem `MapaInvalido`; com qualquer campo
   desconhecido num YAML de teste, levanta `MapaInvalido` citando arquivo e caminho.
2. (021a) `hash_entrada` segue a fórmula da spec §6.2 (teste com valor fixo calculado à mão);
   `entradas_publicaveis` devolve só `aprovado` com hash igual (teste com três entradas:
   aprovada-igual, aprovada-alterada, revisada).
3. (021a) Diretório inexistente → `MapaIndisponivel`; `ZIL_DATA_DIR` é respeitado.
4. (021b) Conteúdo cobre o mínimo da tabela "Conteúdo mínimo do rascunho v0" abaixo; todos os 99 +
   235 + 175 códigos estão numa regra, num marco, em `ignorados` ou em `nao_mapeados.yml`.
5. (021b) `revisao.yml` = `versao_publicada: 0`, `entradas: {}` — **nada aprovado**; com o mapa de
   produção, `derivar_fase` (quando existir) devolve `nao_sabemos(mapa_nao_aprovado)` para tudo o que
   depender de entrada.
6. (021b) Toda entrada tem `base_legal` (com URL na allowlist) ou `base_legal_motivo`, `fontes`, e —
   regras e marcos — pelo menos um `caso` real; o que não foi conferido na fonte primária leva
   `pendente`.

**Specs técnicas** — esquema e exemplos em §2.1–§2.9. Arquivos:

```
packages/tramitacao/__init__.py
packages/tramitacao/tipos.py
packages/tramitacao/mapa.py
packages/tramitacao/revisao.py            # hash_entrada, entradas_publicaveis, ArquivoRevisao, EstadoEntrada
apps/workers/tramitacao/__init__.py
apps/workers/tramitacao/revisao.py        # from packages.tramitacao.revisao import *  (+ __all__)
data/tramitacao/fases.yml
data/tramitacao/marcos.yml
data/tramitacao/ritos.yml
data/tramitacao/glossario.yml             # versao_esquema: 1, aviso, entradas: []  (TRM-022 preenche)
data/tramitacao/nao_mapeados.yml
data/tramitacao/revisao.yml               # cabeçalho da spec §6.2, versao_publicada: 0, entradas: {}
tests/unit/test_mapa_carga.py
```

```python
# packages/tramitacao/revisao.py — implementação ÚNICA (spec §6.2); scripts importam por
# apps.workers.tramitacao.revisao, a API e o motor por packages.tramitacao.revisao.
def hash_entrada(entrada: dict) -> str:
    texto = json.dumps(entrada, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]

def ids_de_conteudo(fases: dict, marcos: dict, ritos: dict, glossario: dict) -> dict[str, dict]:
    """id "<arquivo>/<chave>" → mapeamento bruto, para todos os arquivos de conteúdo (§2.1-3)."""

def entradas_publicaveis(conteudo: Mapping[str, dict], revisao: "ArquivoRevisao") -> frozenset[str]: ...
```

#### Conteúdo mínimo do rascunho v0 (021b)

Produzido pelo agente implementador como **redator** (spec §6.3): só fontes canônicas, `base_legal`
com URL, `casos` reais (de preferência os pacotes de TRM-002), `pendente` para o que não conferiu.
**Tudo nasce `rascunho`** e entra no processo de TRM-023/TRM-029 (lotes L1–L3, L5–L6; o glossário de
fases e `apensada` é o lote L7, escrito em TRM-022 — spec.md §6.12).

**`fases.yml`**

- `normas_base`: CF, RICD, RCD-33-2022, RISF, RCN-1-2002, LC-95-1998, LINDB, DEC-12002-2024 (URLs do
  disc. "Fontes"); `STF-MS-27931` (`https://noticias.stf.jus.br/?p=42494`) para o trancamento de pauta
  da MPV.
- **Fases** (rótulos pela recomendação D1 da spec §10.2; a decisão é da maintainer no lote L1):

| `chave` | `rotulo` | `rotulo_por_casa` / `rotulo_por_especie` | Base legal mínima |
| --- | --- | --- | --- |
| `apresentada` | Apresentada | motivo: `recem_apresentada` → "Recém-apresentada" | CF art. 61; RICD art. 139 |
| `comissoes` | Nas comissões | espécie: `MPV` → "Na comissão mista" | RICD arts. 24 II, 52; CF art. 62 § 9º |
| `plenario` | No Plenário | casa: "No Plenário da Câmara" / "No Plenário do Senado" | CF art. 47; RICD art. 183 |
| `outra_casa` | Na outra Casa | casa: "Na Câmara" / "No Senado" (sempre o nome concreto) | CF art. 65 |
| `retorno` | De volta à Casa de origem | casa: "De volta à Câmara" / "De volta ao Senado" | CF art. 65, parágrafo único |
| `sancao` | Com o Presidente da República | — | CF art. 66, §§ 1º a 3º |
| `veto_congresso` | Veto em análise no Congresso | — | CF art. 66, §§ 4º a 6º |
| `promulgacao` | Promulgação | — | CF art. 60 § 3º; art. 66 §§ 5º e 7º |
| `norma` | Virou lei | espécie: `PEC` → "Virou emenda constitucional"; `PDL` → "Virou decreto legislativo"; `MPV` → "Convertida em lei" | CF art. 66; art. 84, IV |

  As `frases` de cada fase e desfecho e de `apensada` são as da tabela de `backlog-interface.md` §2.9
  (UI/UX), transcritas para a forma de `ModeloFrase` (§2.2); a última de cada lista sem filtro nem
  `quando`.
- **Desfechos** (disc. §2.2, corrigido por A21): `arquivada` (RICD art. 105, caput e VI, com a
  redação da RCD 33/2022, e art. 133; RISF art. 332 para o Senado). **Nenhum texto diz "pode ser
  desarquivada" para a Câmara**: o antigo parágrafo único do art. 105 virou § 1º e foi revogado pela
  RCD 33/2022; no Senado o desarquivamento existe (RISF art. 332, a conferir com `pendente`) — o
  texto é por Casa. `retirada` (RICD art. 104; RISF art. 256 com `pendente: "conferir artigo do
  RISF"`), `prejudicada` (RICD arts. 163 e 164; RISF art. 334 com `pendente`), `rejeitada` (CF art.
  67), `perdeu_eficacia` (CF art. 62, §§ 3º e 11), `vetada` (CF art. 66, §§ 4º a 6º — veto total
  mantido), `devolvida` (RICD art. 137, §§ 1º e 2º — **conferido no texto compilado em 2026-10-30**:
  a Presidência devolve ao autor a proposição não formalizada, alheia à competência da Câmara,
  evidentemente inconstitucional ou antirregimental; recurso ao Plenário em 5 sessões. Sem
  `pendente`: o ⚠ de disc. §2.2 está resolvido, e a confirmação segue pelo revisor `juridico` no
  fluxo normal). A situação 1120 "Devolvida ao(à) Autor(a)" entra na R3 com `desfecho: devolvida`
  assim que o redator anexar um caso real.
- **`apensada`**: RICD arts. 142 e 143; frases "Tramita junto com {principal_com_artigo}, a
  proposição principal. {frase_principal}" e, sem a frase da principal, só a primeira oração.
- **Regras R1–R10** com as situações abaixo (todas as 16 situações do banco de desenvolvimento —
  disc. Apêndice A — mais "Aguardando Sanção", citada na R6):

| Cód. | Situação oficial | Qtd. no banco (disc. §1.1) | Regra | Campo | Caso |
| --- | --- | --- | --- | --- | --- |
| 1140 | Transformado em Norma Jurídica | 16 | R1 | — | 2269745; 2196833 (sem marco) |
| 923 | Arquivada | 22 | R3 | `desfecho: arquivada` | do banco |
| 950 | Retirado pelo(a) Autor(a) | 1 | R3 | `desfecho: retirada` | do banco |
| 1292 | Perdeu a Eficácia | 8 | R3 | `desfecho: perdeu_eficacia` | `mpv-perdeu-eficacia` |
| 925 | Tramitando em Conjunto | 24 | R4 | — | 2482075 |
| 927 | Aguardando Apensação | 1 | R4 | — | do banco |
| 926 | Aguardando Apreciação pelo Senado Federal | 5 | R5 | — | do banco |
| 1150 | Aguardando Sanção | 0 | R6 | `fase: sancao` | 2600838 (eventos antes do marco 251) |
| 915 | Aguardando Parecer | 50 | R7 | — | do banco |
| 907 | Aguardando Designação de Relator(a) | 43 | R7 | — | 2426923 |
| 1170 | Aguardando Designação - Aguardando Devolução de Relator(a) que deixou de ser Membro | 4 | R7 | — | do banco |
| 924 | Pronta para Pauta | 8 | R7 | — | `pronta-pauta-plenario` |
| 1201 | Aguardando Despacho do Presidente da Câmara dos Deputados (Chancela) | 20 | R8 | — | `pdl-chancela` |
| 1221 | Aguardando Despacho do Presidente da Câmara dos Deputados (Autorização) | 7 | R8 | — | do banco |
| 1091 | Ag. Análise de Inconstitucionalidade | 2 | R8 | — | do banco |
| 1200 | Aguardando Autorização do Despacho | 1 | R8 | — | do banco |
| 910 | Aguardando Encaminhamento | 7 | R10 | `motivo: sinais_conflitantes` | 2384947 (resolvido por R2) |

  "Do banco" = o redator escolhe um `fonte_id` real do banco de desenvolvimento nessa situação e o
  cita em `casos` (com URL de `/proposicoes/{id}` em `fontes`). Candidatos que **só** entram com
  caso real anexado (senão vão para `nao_mapeados.yml` com `sem_evidencia`): 937 "Vetado totalmente" e
  939 "Aguardando Apreciação do Veto" → R6 `veto_congresso`; 1294 "Aguardando Promulgação" → R6
  `promulgacao`; 1222 "Prejudicialidade" → R3 `prejudicada`; 1120 "Devolvida ao(à) Autor(a)" → R3
  `devolvida` (base legal já conferida, A21); 930 "Enviada ao Arquivo" → R3 `arquivada`; 905/1382 "Aguardando Despacho do Presidente
  da Câmara dos Deputados", 1220 "(Análise)", 1110, 906 "Aguardando Distribuição" → R8; 1303 "Enviada
  ao Senado Federal" → R5.

**`marcos.yml`** — os 25 códigos de disc. §4.4 (exigidos pela spec §6.11-4) mais 190, 500 e 503, sem
os quais as armadilhas A5 e de disc. §3.2-4 não se resolvem:

| Cód. | Descrição oficial | `marco` | `fase_resultante` | Terminal / reabre | Condição ou variantes | Caso |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | Apresentação de Proposição | apresentacao | apresentada | — | condição `^apresenta[cç][aã]o d[oa] (PL\|PLP\|PEC\|PDL\|MPV\|PLV)\b` (A5) | 2416804 seq. 1 (e 65 não) |
| 110 | Distribuição | distribuicao | comissoes | — | variante `emendas do senado` → `retorno_emendas`, `retorno` | 2269745 seq. 8 e 125 |
| 112 | Redistribuição | distribuicao | comissoes | — | — | caso real |
| 106 | Apensação | apensacao | — | — | — | 2482075 seq. 16 |
| 129 | Despacho de Apensação | apensacao | — | — | — | 2384947 seq. 7 |
| 504 | Notificação de Apensação | apensacao | — | — | `linha_do_tempo: false` | caso real |
| 320 | Designação de Relator(a) | designacao_relator | — | — | — | 2416804 seq. 9 |
| 322 | Parecer do(a) Relator(a) | parecer | — | — | — | 2416804 seq. 23 |
| 336 | Aprovação do Parecer | parecer_aprovado | — | — | — | caso real |
| 196 | Aprovação de Urgência (154, 155 ou 64 CF) | urgencia_aprovada | — | — | — | 2269745 seq. 36 |
| 1231 | Votação (Plenário) | votacao_plenario | plenario | — | `linha_do_tempo: false` (repetitivo) | 2416804 seq. 40 |
| 1235 | Aprovação de Proposição (Plenário) | aprovacao_plenario | — | — | condição `^aprovad[oa]s?\b.*\b(projeto\|proposta\|proposi[cç][aã]o\|reda[cç][aã]o final\|substitutivo)` | 2416804 seq. 41 e 54; 2196833 seq. 312 |
| 1236 | Rejeição de Proposição (Plenário) | rejeicao (se houver caso) | — | `rejeitada` | só com condição `^rejeitad[oa]\s+(o projeto\|a proposta\|a proposi[cç][aã]o)` **e** caso real; sem caso, fica em `nao_mapeados` (A6) | — |
| 1243 | Encaminhamento (Plenário) | remessa_outra_casa | outra_casa | — | condição `vai ao senado federal`; variante `vai [àa] san[cç][aã]o` → `remessa_sancao`, `sancao` | 2416804 seq. 55; 2196833 seq. 352 (não) e 385 |
| 128 | Remessa ao Senado Federal | remessa_outra_casa | outra_casa | — | — | 2196833 seq. 391 |
| 190 | Expedição de Documento | remessa_outra_casa | outra_casa | — | condição `remessa ao senado federal` (disc. §3.2-4) | 2416804 seq. 64; 2600838 seq. 57 |
| 500 | Recebimento | recebimento_outra_casa | outra_casa | — | condição `submete [àa] revis[aã]o`; variante `substitutivo do senado\|emendas? do senado` → `retorno_emendas`, `retorno` | 2454704 seq. 1; 2196833 seq. 393 |
| 1518 | Aprovação no Senado Federal | aprovacao_outra_casa | — | — | — | caso real |
| 1519 | Aprovação no Senado Federal - Com Emendas | retorno_emendas | retorno | — | — | caso real |
| 127 | Despacho à Sanção | remessa_sancao | sancao | — | — | caso real |
| 609 | Remessa à Sanção | remessa_sancao | sancao | — | — | caso real |
| 251 | Transformação em Norma Jurídica | norma | norma | — | `extrai_norma: true` | 2600838 seq. 62 |
| 1012 | Transformado em Norma Jurídica com Veto Parcial | norma_veto_parcial | norma | — | `extrai_norma: true` | 2416804 seq. 66; 2430143 seq. 172 |
| 1013 | Vetado Totalmente | veto_total | veto_congresso | — | — | caso real |
| 502 | Arquivamento | arquivamento | — | `arquivada` | variante `\bfica(m)?\s+prejudicad` → `prejudicialidade`, `prejudicada` (A7) | 2384947 seq. 16 |
| 200 | Retirada pelo(a) Autor(a) | retirada | — | `retirada` | — | caso real |
| 620 | Perda de eficácia | perda_eficacia | — | `perdeu_eficacia` | — | `mpv-perdeu-eficacia` |
| 503 | Desarquivamento | desarquivamento | — | reabre `[arquivada]` | — | caso real |

  "Caso real": o redator acha uma proposição que tem a linha (no banco ou na API) e cita; sem caso,
  a entrada leva `pendente: "sem caso real"` e não sai de `rascunho`. 1240 e 1241 vão para
  `nao_mapeados.yml` com a nota de A6. `ignorados` (decisão humana, com nota): no mínimo 604, 605,
  606, 611, 1002, 1003, 1004, 1005, 1050, 1521, 1522 (publicação e notificação). Todo o resto dos 235
  vai para `nao_mapeados.yml` (`sem_evidencia`; `inativo` para 997, 998, 999 e 700).

**`ritos.yml`** — `especies` (PL "Projeto de lei", PLP "Projeto de lei complementar", PEC "Proposta de
emenda à Constituição", MPV "Medida provisória", PDL "Projeto de decreto legislativo"); nove ritos:

| Chave | Etapas (fase) | Particularidades com base legal |
| --- | --- | --- |
| `PL_CD` | apresentacao → comissoes_camara → plenario_camara (opcional, `apreciacao_conclusiva`) → senado (`outra_casa`) → retorno_camara (opcional) → sancao → veto_congresso (opcional) → promulgacao (opcional) → norma | exemplo completo em §2.5 |
| `PL_SF` | o espelho: apresentacao (senado) → comissoes_senado → plenario_senado (opcional; decisão terminativa, RISF art. 91) → camara (`outra_casa`) → retorno_senado (opcional) → sancao → veto_congresso → promulgacao → norma | RISF art. 91; CF art. 65 |
| `PLP_CD`, `PLP_SF` | como PL, **sem** plenário opcional | maioria absoluta (CF art. 69); dois turnos na Câmara (RICD art. 148) |
| `PEC_CD`, `PEC_SF` | apresentacao → comissoes (CCJ e comissão especial) → plenario (dois turnos, 3/5) → outra_casa (dois turnos, 3/5) → retorno (opcional) → promulgacao → norma; **sem** sanção | CF art. 60, §§ 2º e 3º; RICD art. 202; RISF arts. 354 a 363 |
| `MPV_CN` | exemplo completo em §2.5 | CF art. 62; RCN 1/2002 (artigos com `pendente`) |
| `PDL_CD`, `PDL_SF` | apresentacao → comissoes → plenario → outra_casa → retorno (opcional) → promulgacao → norma; **sem** sanção | CF art. 49 (competência exclusiva) e art. 48 caput (sem sanção) |

  Desfechos por rito conforme disc. §2.2 (`perdeu_eficacia` só em MPV; `vetada` a partir de
  `veto_congresso`; `devolvida` a partir de `apresentacao`). `pos_lei`: `publicacao` (CF art. 84, IV),
  `vigencia` (LC 95 art. 8º; LINDB art. 1º — 45 dias se a lei for omissa), `regulamentacao` (CF art.
  84, IV; Decreto 12.002/2024 art. 4º, § 2º — sem prazo geral; classe X).

**`nao_mapeados.yml`** — o complemento exato: códigos de situação da Câmara fora das regras
(`fora_do_escopo` com nota para 1298, 1304, 1305, 1310, 1312, 1313, 1314, 1350, 1355; `inativo` para
1250 e 1311; o resto `sem_evidencia`); os 175 do Senado (`inativo` para os 26 com `data_fim`,
`sem_evidencia` com nota "TRM-050" para os demais); tipos de tramitação fora de `marcos` e `ignorados`.

**Testes** — `tests/unit/test_mapa_carga.py`: critérios 1–3 e 5 (com o `revisao.yml` do repositório,
`mapa.publicaveis == frozenset()`); extras proibidos; chave de rito derivada (`PL_CD`, `MPV_CN`);
`ids_de_conteudo` gera os formatos de §2.1-3. O teste de cobertura é de TRM-024. Comando:
`.venv/bin/python -m pytest tests/unit/test_mapa_carga.py -v`.

**Riscos e perguntas em aberto** — Artigos de RISF e RCN não conferidos pelo discovery: marcados
`pendente`, barram a aprovação até o revisor `juridico` (spec §6.4) confirmar. O DoD da v1 (spec
§6.11-4) pede os 25 marcos aprovados; **1236 pode não ter caso real de rejeição de proposição em
Plenário** — se não tiver, a proposta é aceitar 1236 em `nao_mapeados` na v1 (decisão do PM/maintainer).

**Instruções para o agente implementador** — Dois PRs. **021a** (`trm-021a-esquema-mapa`): tipos →
modelos → `revisao.py` (testes do hash) → `carregar_mapa` → arquivos vazios válidos. **021b**
(`trm-021b-mapa-v0`, depois de TRM-020 e de preferência de TRM-002): conteúdo pela tabela acima; rodar
`carregar_mapa()` a cada arquivo; quando TRM-024 existir, `scripts/validar_tramitacao.py`. Prova: a
contagem de cobertura por tabela e a lista de entradas com `pendente`. **Não** escrever em
`revisao.yml` além do arquivo inicial; **não** marcar nada como aprovado; **não** mapear código sem
caso real; **não** inventar artigo (sem conferência → `pendente`); **não** copiar texto do Glossário
Legislativo do Congresso (spec §6.3-1).

---

### TRM-024 — Validador `scripts/validar_tramitacao.py` + teste de cobertura + job na CI

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E2 Mapa e glossário · **Prioridade:** P0 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; Product (regras V-R da spec §6.9)
**Depende de:** TRM-020, TRM-021; TRM-023 (formato de `revisoes/`, `consolidado.yml`, `decisao.yml`) · **Desbloqueia:** TRM-025, TRM-029

**Problema** — Sem validação, um YAML com fase escrita errada, um código esquecido ou uma entrada
aprovada e depois alterada chega à produção em silêncio — o mesmo risco que motivou
`scripts/validar_direcoes.py` (docstring, :1-15).

**Oportunidade** — Cobertura de 100% dos códigos provada a cada PR, e "só o aprovado vai ao ar"
conferido na CI além de na carga.

**Solução** — Validador offline, no estilo de `validar_direcoes.py` (lista de problemas, resumo,
código de saída), com as regras V-E (esquema e consistência), V-C (cobertura) e V-R1–V-R9 (spec §6.9);
um teste pytest que roda a cobertura sobre `data/` real; um job na CI.

**Escopo** — Dentro: script, testes, job, ADR curto. Fora: escrever `revisao.yml` (TRM-023).

**Critérios de aceite**
1. `.venv/bin/python scripts/validar_tramitacao.py` sobre o repositório sai 0 depois de 021b.
2. Cada regra da tabela abaixo tem um teste que a viola num diretório temporário e espera a mensagem.
3. `--cobertura` imprime, por tabela, mapeados / ignorados / não mapeados / total, e `--json` emite o
   mesmo em JSON (insumo do revisor `dados`, spec §6.4).
4. `--hashes` imprime `<id>\t<hash>` de todas as entradas, ordenado.
5. `--estrito` transforma avisos (referência a glossário inexistente, situação observada sem mapa) em erro.
6. Job `validar-tramitacao` na CI, verde.
7. Teste de AST: `com_tudo_publicavel` só aparece em `tests/`, `scripts/validar_tramitacao.py` e
   `apps/workers/tramitacao/relatorio.py`; e esse módulo não chama `add`, `commit`, `flush` nem
   `execute` com `update`/`insert` (a projeção de TRM-027 nunca grava).

| Regra | Erro quando |
| --- | --- |
| V-E1 | esquema Pydantic (§2) falha — mensagem com arquivo e caminho |
| V-E2 | fases ≠ as 9 do contrato; desfechos ≠ os 7; regras ≠ R1..R10 na ordem, ou `tipo` diferente do canônico (§2.3); parâmetro obrigatório ausente |
| V-E3 | código de situação em mais de uma regra, ou numa regra e em `nao_mapeados.yml`; campos da situação incoerentes com o `tipo` da regra |
| V-E4 | `descricao_oficial` diferente do `nome` do snapshot (com `strip()`) |
| V-E5 | marco: código repetido na mesma casa; regex que não compila; `terminal`/`reabre` fora dos desfechos; `extrai_norma` ≠ `CODIGOS_TRAMITACAO_NORMA` |
| V-E6 | rito: chave repetida; MPV fora de `congresso`; fase repetida ou fora de ordem; PEC/PDL com `sancao`; `a_partir_de` inexistente; última etapa ≠ `norma` |
| V-E7 | `base_legal` com host fora de `HOSTS_NORMA` ou `norma` fora de `normas_base`; os dois ou nenhum de `base_legal`/`base_legal_motivo`; regra ou marco sem `casos` |
| V-E8 | frase com marcador fora de `Marcador` ou ausente de `quando`; último modelo da lista com filtro ou `quando`; rótulo > 32 caracteres; termo vedado (§2.1-8) em rótulo, frase, título ou glossário; frase com mais de 25 palavras por período (guia de TRM-022) |
| V-E9 | `tipos_orgao_comissao` com código ausente de `camara-tipos-orgao.json`, ou parâmetros da R7 diferentes de `TIPOS_ORGAO_COMISSAO`/`SIGLAS_PLENARIO` de `packages/tramitacao/status.py` (o órgão efetivo de F0 usa as constantes) |
| V-E10 | glossário: chave repetida; `(casa, cod)` em duas entradas; `tipo: situacao` sem `codigos`/`descricao_oficial`; `regime`/`apreciacao`/`desfecho`/`etapa` sem `base_legal`; referência inexistente (aviso; erro com `--estrito`) |
| V-C1 | código de um snapshot que não está em exatamente um de: regra/marco, `ignorados`, `nao_mapeados.yml` |
| V-C2 | código citado nos YAMLs que não existe no snapshot |
| V-C3 | se existir `data/tramitacao/amostras/situacoes.json` (TRM-027 `relatorio --exportar-situacoes`): situação observada sem regra (aviso; erro com `--estrito`) |
| V-R1…V-R9 | como a spec §6.9 (estado, hash, registros, `aprovado_em`, `bloqueia` sobreposto, base legal, `entradas_publicaveis`, `pendente`), com **V-R7 ampliada** a pedido de UI/UX: `base_legal_motivo` vale para critério interno do ZIL (regras R9, R10) **e** para glossário `tipo: situacao` administrativa, com o texto padronizado de §2.6 |

**Specs técnicas**
- `scripts/validar_tramitacao.py` — funções testáveis: `validar(diretorio: Path, *, estrito: bool =
  False, hoje: date | None = None) -> Relatorio` (`Relatorio`: `erros: list[str]`, `avisos:
  list[str]`, `cobertura: dict`, `estados: dict`), `main(argv: list[str] | None = None) -> int`.
  Usa `packages.tramitacao.mapa` (com `com_tudo_publicavel` para checar o conteúdo inteiro) e
  `packages.tramitacao.revisao`. Lê `revisoes/<lote>/consolidado.yml` e `decisao.yml` só nos campos
  que V-R4–V-R6 precisam; tolera campos extras neles. Saída humana como em `validar_direcoes.py:236-249`.
- `.github/workflows/ci.yml`, novo job:

```yaml
  validar-tramitacao:
    name: Dados — Mapa de tramitação
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
          cache-dependency-path: apps/api/requirements.txt
      - run: pip install -r apps/api/requirements.txt
      - run: python scripts/validar_tramitacao.py --cobertura
```

- `docs/decisions/009-mapa-de-tramitacao.md` (conferir o próximo número livre com `ls docs/decisions`):
  mapa como dado versionado; publicação por estado + hash, conferida na carga e na CI; código de
  domínio em `packages/tramitacao/` por causa do layout do container (§0).

**Testes** — `tests/unit/test_validar_tramitacao.py` (critério 2: diretório mínimo válido montado
pelo teste + uma mutação por regra; V-R com `revisao.yml` e `revisoes/` sintéticos);
`tests/unit/test_cobertura_codigos.py` (roda `validar(Path("data/tramitacao"))` e exige zero erros
V-C — **este é o teste de cobertura**, roda também no job de backend); `tests/unit/test_publicacao_por_construcao.py`
(critério 7; V-R8 como propriedade: para estados e hashes gerados, `entradas_publicaveis` ==
{aprovado ∧ hash igual}). Comando: `.venv/bin/python -m pytest tests/unit/test_validar_tramitacao.py tests/unit/test_cobertura_codigos.py tests/unit/test_publicacao_por_construcao.py -v`.

**Riscos e perguntas em aberto** — V-R3 faz a CI falhar quando uma entrada aprovada muda (spec
§6.8-5): uma correção urgente de texto exige rodada de revisão. É o custo desejado. Snapshot
renomeado por TRM-020 dispara V-E4/V-R3 juntos: a mensagem deve dizer qual veio do snapshot.

**Instruções para o agente implementador** — Branch `trm-024-validador`. Regras V-E e V-C primeiro
(não dependem de TRM-023), depois V-R com fixtures sintéticas no formato da spec §6.5. Prova: saída
do validador no repositório e o job verde. **Não** chamar rede; **não** escrever em nenhum arquivo;
**não** aceitar `com_tudo_publicavel` fora dos lugares permitidos.

---

### TRM-025 — Motor `derivar_fase` (função pura, R1–R10, `nao_sabemos` com motivo) + golden + determinismo

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E2 Mapa e glossário · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** G — em dois PRs: **025a** tipos, regras e testes sintéticos (M); **025b** `montar_entrada` + golden (M)
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; Maintainer (o `esperado` de cada golden)
**Depende de:** TRM-021, TRM-024, TRM-002 · **Desbloqueia:** TRM-027, TRM-029 (lotes L2–L3), TRM-047

**Problema** — A fase hoje não existe: o site mostra a situação crua num `Selo` truncado (disc.
§1.5). As situações oficiais não dizem a fase sem o órgão e o despacho ("Pronta para Pauta",
"Aguardando Encaminhamento", disc. §1.1), e às vezes contradizem o histórico (A8, A9).

**Oportunidade** — Uma fase por proposição, derivada por regra escrita, reproduzível e auditável —
ou "não sabemos", com motivo. Nunca palpite.

**Solução** — `packages/tramitacao/motor.py`: `derivar_fase(entrada: EntradaFase, mapa: Mapa) ->
FaseDerivada`, sem I/O, sem relógio, sem LLM. A primeira regra que casa vence; a regra e a
`versao_publicada` vão junto do resultado. Toda entrada do mapa que decide o resultado tem de ser
publicável; senão, `nao_sabemos(mapa_nao_aprovado)` — sem cair para uma regra de menor precedência.

**Escopo** — Dentro: tipos de entrada e saída, R0–R10, `montar_entrada` (de respostas brutas),
golden, determinismo. Fora: banco (TRM-027), rótulos e frase (TRM-028), Senado real (TRM-050 liga a
`EntradaSenado`).

**Critérios de aceite**
1. Cada regra tem testes sintéticos (mapa mínimo montado no teste, `com_tudo_publicavel()`) para o
   caso que casa, o que não casa e o de entrada não publicável.
2. Golden: para cada caso de `tests/fixtures/tramitacao/casos.yml`, `montar_entrada` + `derivar_fase`
   com o mapa do repositório em `com_tudo_publicavel()` e `hoje = caso.hoje` dá exatamente o `esperado`
   (fase, desfecho, motivo, regra, apensada, herdada_de, casa). ≥ 15 casos, incluindo PLP e PEC
   (spec §6.11-7).
3. Com o mapa de produção (nada aprovado), todo golden dá `nao_sabemos` com motivo
   `mapa_nao_aprovado` — exceto os que caem em R0 ou R10, que não dependem de aprovação.
4. Determinismo: a mesma entrada dá o mesmo resultado (igualdade de dataclass) em duas chamadas e
   com os marcos embaralhados; `motor.py` não importa `datetime.now`, `date.today`, `time`, `random`,
   `os`, `httpx`, `sqlalchemy` (teste de AST).
5. `recem_apresentada` sai como `fase="apresentada"`, `motivo="recem_apresentada"`, regra R9 — conta
   como fase conhecida (meta M5 < 5%: as 16 nulas do banco seriam 6,7% se fossem `nao_sabemos`).

**Specs técnicas**

```python
# packages/tramitacao/motor.py
@dataclass(frozen=True)
class MarcoObservado:
    casa: Casa
    sequencia: Optional[int]
    data: Optional[date]
    cod: str
    marco: TipoMarco
    entrada: str                         # "marcos/251" — para checar publicável
    fase_resultante: Optional[Fase]
    terminal: Optional[Desfecho]
    reabre: tuple[Desfecho, ...] = ()
    sigla_orgao: Optional[str] = None

@dataclass(frozen=True)
class EntradaSenado:                      # preenchida a partir de TRM-050
    sigla_situacao: Optional[str]
    norma_gerada: bool
    tramitando: Optional[bool]

CadeiaStatus = Literal["sem_cadeia", "resolvida", "ciclo", "profunda_demais", "principal_indisponivel"]

@dataclass(frozen=True)
class EntradaFase:
    fonte_id: str
    especie: str                          # siglaTipo, como veio (pode estar fora do escopo)
    casa_fonte: Casa                      # de onde vêm situação e órgão ("camara" até TRM-050)
    casa_iniciadora: Optional[Literal["camara", "senado", "congresso"]]
    detalhe_disponivel: bool              # detalhe_sincronizado_em não nula
    hoje: date                            # injetado; nunca lido do relógio aqui dentro
    data_apresentacao: Optional[date]
    cod_situacao: Optional[str]
    sigla_orgao: Optional[str]                # órgão do statusProposicao (oficial)
    orgao_tipo_cod: Optional[str]
    orgao_efetivo_sigla: Optional[str]        # A19: o do status se for PLEN ou comissão; senão o do registro
    orgao_efetivo_tipo: Optional[str]         #   mais recente (por sequência) em PLEN ou comissão; senão nulo
    orgao_efetivo_sequencia: Optional[int]    #   de onde veio (evidência "orgao_efetivo:CMADS@13")
    principal_fonte_id: Optional[str]
    marcos: tuple[MarcoObservado, ...]
    senado: Optional[EntradaSenado] = None
    cadeia_status: CadeiaStatus = "sem_cadeia"
    cabeca_fonte_id: Optional[str] = None
    cabeca: Optional["FaseDerivada"] = None

@dataclass(frozen=True)
class FaseDerivada:
    fase: Optional[FaseOuNaoSabemos]      # None só com desfecho e "onde parou" desconhecido
    desfecho: Optional[Desfecho]
    motivo: Optional[Motivo]
    regra: RegraId
    versao_publicada: int
    casa: Optional[Casa]
    desde: Optional[date]                 # início da fase atual
    data_marco: Optional[date]            # data do marco decisivo (remessa, veto, terminal) — marcador {data}
    apensada: bool = False
    herdada_de: Optional[str] = None      # fonte_id da cabeça
    evidencias: tuple[str, ...] = ()      # "situacao:1140", "marco:1012@160", "nao_publicavel:marcos/251", "cabeca:R7"
    # __post_init__: fase == "nao_sabemos" ⇔ motivo ∈ MOTIVOS_NAO_SABEMOS e desfecho is None;
    # motivo == "recem_apresentada" ⇒ fase == "apresentada" e regra == "R9"; fase is None ⇒ desfecho is not None

def derivar_fase(entrada: EntradaFase, mapa: Mapa) -> FaseDerivada: ...
```

Ordem dos marcos: chave `(data or date.min, 0 se camara senão 1, sequencia or 0, cod)`; o motor
ordena a tupla recebida (por isso embaralhar não muda nada). `sit = mapa.situacao_por_codigo.get(
(casa_fonte, cod_situacao))` → `(regra_id, SituacaoTratada)` ou nada. `exigir(*ids)`: se algum id não
é publicável, devolve `nao_sabemos("mapa_nao_aprovado")` com a regra que casou e
`nao_publicavel:<id>` nas evidências. **Entradas decisivas** = a regra que casou, a situação ou o
marco que a sustentou, e a `FaseDef`/`DesfechoDef` do resultado (spec §6.8-2).

| # | Casa quando | Resultado | Decisivas | Notas |
| --- | --- | --- | --- | --- |
| R0 | `not detalhe_disponivel` ou `especie ∉ {PL, PLP, PEC, MPV, PDL}` | `nao_sabemos(fonte_indisponivel)` / `nao_sabemos(especie_fora_do_escopo)` | nenhuma | guarda em código; PLV e PLN caem aqui |
| R1 | `senado.norma_gerada`, ou algum marco `norma`/`norma_veto_parcial`, ou `sit` na R1 | `norma`; `data_marco` = data do marco de norma; `casa` nula | `fases/regra_R1`, o marco (ou a situação, se não houver marco), `fases/fase_norma` | o marco vence o último registro (A8, ofícios) |
| R2 | `T` = último marco com `terminal`, e nenhum marco depois de `T` tem `fase_resultante` nem `reabre ∋ T.terminal` | `desfecho = T.terminal` (a variante pode trocar: A7); `fase` = onde parou; `data_marco = T.data` | `fases/regra_R2`, `T.entrada`, `fases/desfecho_<x>` | onde parou: `None` se `principal_fonte_id`; senão `fase_resultante` do último marco antes de `T`; senão a lógica de órgão da R7; senão `None` |
| R3 | `sit` na R3 | `desfecho = sit.desfecho`; onde parou como na R2 | `fases/regra_R3`, `fases/desfecho_<x>` | `data_marco` = último marco com o mesmo `terminal`, se houver |
| R4 | `sit` na R4 ou `principal_fonte_id` | `cadeia_status != "resolvida"` ou `cabeca` nula ou `cabeca.fase == "nao_sabemos"` → `nao_sabemos(principal_nao_resolvida)`; senão herda `fase`, `desfecho`, `casa`, `desde`, `data_marco` da cabeça, com `apensada=True`, `herdada_de=cabeca_fonte_id` | `fases/regra_R4`, `fases/apensada` | a cabeça já passou pelo motor (TRM-027 resolve antes) |
| R5 | `senado` presente e tramitando (TRM-050), ou `sit` na R5 | `outra_casa` se `casa_iniciadora == "camara"`; `retorno` se `"senado"` (a Câmara emendou e devolveu); `casa = "senado"`; `data_marco` = último marco `remessa_outra_casa` | `fases/regra_R5`, `fases/fase_<x>` | `casa_iniciadora` nula → `nao_sabemos(fonte_indisponivel)` |
| R6 | `sit` na R6 | `sit.fase` (`sancao`, `veto_congresso`, `promulgacao`); `casa` nula; `data_marco`/`desde` = último marco com essa `fase_resultante` | `fases/regra_R6`, `fases/fase_<x>` | |
| R7 | `sit` na R7 | pelo **órgão efetivo** (A19): sigla em `siglas_plenario` → `plenario`; tipo em `tipos_orgao_comissao` → `comissoes`; órgão efetivo nulo → segue para R10 com `sinais_conflitantes`. Depois, o **ajuste por Casa** (helper comum a R7 e R9b): `casa_iniciadora == "senado"` → `outra_casa` (a Câmara é revisora); `"camara"` e marco com `fase_resultante == "retorno"` depois do último `remessa_outra_casa` → `retorno`; `casa_iniciadora` nula (exceto MPV) → `nao_sabemos(fonte_indisponivel)`; `casa = "camara"` | `fases/regra_R7`, `fases/fase_<x>` | "Pronta para Pauta" se resolve aqui; status em CCP ou MESA (23 das 240) também |
| R8 | `sit` na R8 | `apresentada`; `casa = casa_fonte`; `desde = data_apresentacao` | `fases/regra_R8`, `fases/fase_apresentada` | |
| R9 | `cod_situacao` nulo e: **(a)** nenhum marco `distribuicao`, `data_apresentacao` não nula e `0 ≤ (hoje − data_apresentacao).days ≤ dias_max`; ou **(b)** há marco com `fase_resultante` (R1/R2 já trataram norma e terminais) | (a) `apresentada`, `motivo = recem_apresentada`, `desde = data_apresentacao`; (b) a `fase_resultante` do último marco com fase, com o ajuste por Casa da R7, `motivo` nulo, evidências `"situacao:nula"` e `"marco:<cod>@<seq>"` | `fases/regra_R9`, o marco de (b), `fases/fase_<x>` | (b) é **acréscimo ao disc. §4.3** (A20: 17 das 20 nulas têm mais de 90 dias, 13 com "Distribuição" como último registro); vai ao lote L2 como parte da R9 |
| R10 | o resto | `nao_sabemos` com: `cod_situacao` nulo → `fonte_indisponivel` (a Câmara não informa); `sit` na R10 → `sit.motivo`; R7 sem decisão → `sinais_conflitantes`; código em `nao_mapeados` ou desconhecido → `situacao_sem_mapa` | nenhuma | caminho conservador; não exige aprovação |

`desde` (fora de R8/R9): data do primeiro marco com `fase_resultante == fase` depois do último marco
com `fase_resultante` diferente; sem marco, nulo.

`packages/tramitacao/entrada.py`:

```python
def montar_entrada(*, detalhe: Optional[dict], tramitacoes: Sequence[dict], autores: Optional[Sequence[dict]],
                   orgao: Optional[dict], mapa: Mapa, hoje: date, casa_fonte: Casa = "camara",
                   cadeia_status: CadeiaStatus = "sem_cadeia", cabeca_fonte_id: Optional[str] = None,
                   cabeca: Optional[FaseDerivada] = None, senado: Optional[EntradaSenado] = None) -> EntradaFase: ...
def casa_iniciadora_dos_autores(especie: str, autores: Optional[Sequence[dict]]) -> Optional[str]: ...
    # MPV → "congresso"; autor com uri terminando em "/orgaos/78" ou nome começando por "Senado Federal" → "senado" (A11);
    # lista não vazia sem isso → "camara"; None/[] → None
```

Golden — `esperado` proposto (o implementador confere contra o pacote; a maintainer aprova no PR de 025b):

| Caso | `fase` | `desfecho` | `motivo` | `regra` | Observação |
| --- | --- | --- | --- | --- | --- |
| `pl-327-2021` | norma | — | — | R1 | marco 1012 seq. 160 |
| `pl-2-2024` | norma | — | — | R1 | |
| `pl-528-2020` | norma | — | — | R1 | |
| `pl-1847-2024` | norma | — | — | R1 | `casa_iniciadora = senado` |
| `pl-1264-2024` | comissoes | — | — | R7 | CFT, `casa = camara` |
| `pl-4272-2023` | `None` | prejudicada | — | R2 | variante de 502 (A7); apensada ⇒ onde parou nulo |
| `pl-5-2025` | a da cabeça | — | — | R4 | `apensada`, `herdada_de` = PL 5941/2013 |
| `pl-278-2026` | norma | — | — | R1 | situação nula (A8) |
| `pl-359-2025` | comissoes | — | — | R7 | conferir no pacote |
| `plp-68-2024` | norma | — | — | R1 | |
| `pec-45-2019` | norma | — | — | R1 | pela situação 1140 (A9) |
| `pdl-chancela` | apresentada | — | — | R8 | |
| `mpv-perdeu-eficacia` | conferir | perdeu_eficacia | — | R2 ou R3 | R2 se houver marco 620 |
| `pl-2026-situacao-nula` | apresentada | — | recem_apresentada | R9 | `hoje` = data da gravação |
| `pronta-pauta-plenario` | plenario | — | — | R7 | |
| `pl-399-2025` | outra_casa | — | — | R5 | "Aguardando Apreciação pelo Senado Federal" |
| `pl-3474-2023` | comissoes | — | — | R7 | status em CCP; órgão efetivo = a comissão do último registro (A19) |
| `pl-4036-2026` | comissoes | — | — | R9 | situação nula, marco 110 (A20) |

**Testes** — `tests/unit/test_motor_regras.py` (sintéticos, critérios 1, 4, 5), `tests/unit/test_motor_golden.py`
(critérios 2, 3; parametrizado por `casos.yml`), `tests/unit/test_motor_puro.py` (AST). Comando:
`.venv/bin/python -m pytest tests/unit/test_motor_regras.py tests/unit/test_motor_golden.py tests/unit/test_motor_puro.py -v`.

**Riscos e perguntas em aberto** — Contraexemplo do revisor `adversarial` (spec §6.4) vira golden em
`candidatos/` e, se confirmado, muda regra ou leva o caso a `nao_sabemos` — nunca a um palpite. O
PLV (conversão de MPV) cai em R0 (`especie_fora_do_escopo`) até haver decisão.

**Instruções para o agente implementador** — Branches `trm-025a-motor` e `trm-025b-golden`. Escreva
os testes de cada regra antes da regra. Prova: tabela golden (caso → resultado) no PR. **Não** ler
relógio, rede ou banco; **não** usar `codSituacao` de linha de tramitação (só o `statusProposicao`);
**não** cair para regra seguinte quando a decisiva não é publicável; **não** devolver fase "provável".

---

### TRM-026 — Tabela `tramitacoes` + ingestão do histórico + marcação de marcos

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E2 Mapa e glossário · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura
**Depende de:** TRM-011, TRM-012, TRM-021 · **Desbloqueia:** TRM-027, TRM-028, TRM-052

**Problema** — `/tramitacoes` já é buscado e jogado fora (`apps/workers/explicacao/coleta.py:138-150`;
disc. §1.3). A coluna JSON `tramitacoes` nunca foi preenchida (`models/__init__.py:103`). Sem histórico
persistido não há linha do tempo, marcos, `desde`, nem entrada para R1/R2.

**Oportunidade** — Linha do tempo com marcos em linguagem simples e "todos os registros" no texto
original, sem chamar a Câmara a cada visita.

**Solução** — Tabela `tramitacoes` (§1.4), upsert idempotente por `(proposicao_id, casa, chave)`
dentro de `sincronizar_proposicao` (as tramitações já são baixadas em TRM-012), marcação de marco com
o mapa, e reclassificação offline quando o mapa muda.

**Escopo** — Dentro: modelo, migration, upsert, marcos, `recalcular` (marcos), testes. Fora: fase
(TRM-027), endpoint (TRM-028), Senado (TRM-050), pipeline de explicação passar a ler a tabela
(candidato a tarefa futura; `coleta.py` continua igual).

**Critérios de aceite**
1. Sincronizar `pl-2-2024` grava 51 linhas, ordenáveis por `sequencia`; a segunda execução com as
   mesmas respostas: 0 criadas, 0 atualizadas.
2. Mudar só `codSituacao`/`descricaoSituacao`/`regime`/`apreciacao`/`uriUltimoRelator` nas linhas
   (pacote alterado em memória) não muda nenhum `hash_conteudo` e conta 0 atualizadas (A4).
3. Nenhuma linha da Câmara tem `cod_situacao` preenchido (teste e `CheckConstraint` não — teste basta).
4. Marcos do pacote `pl-2-2024`: seq. 1 `apresentacao`, seq. 65 nenhum (ofício, A5), seq. 64
   `remessa_outra_casa` (190 com condição), seq. 30 e 51 nenhum (1236 em `nao_mapeados`, A6), seq. 66
   `norma_veto_parcial`; `pl-4272-2023` seq. 16 `prejudicialidade`.
5. Linha que some da resposta ganha `removido_na_fonte_em`; se volta, o campo é limpo; nada é apagado.
6. `sync_tramitacao.py recalcular --apenas-marcos` reclassifica todas as linhas com o mapa atual, sem
   rede, e informa quantas mudaram.

**Specs técnicas**
- Migration `8e47a1c3d5f6_tramitacoes.py` (`down_revision` = head de TRM-011): `op.create_table`
  conforme §1.4, três índices, `UniqueConstraint` nomeada; `downgrade` derruba índices e tabela.
  Acrescentar ao `tests/integration/test_migrations.py`.
- Modelo `Tramitacao` (§1.4); em `Proposicao`: `eventos_tramitacao: Mapped[list["Tramitacao"]] =
  relationship(back_populates="proposicao", order_by="Tramitacao.sequencia")` e o atributo legado
  `tramitacoes_legado = mapped_column("tramitacoes", JSON)`.
- `apps/workers/tramitacao/eventos.py`:

```python
CAMPOS_NAO_HISTORICOS = frozenset({"codSituacao", "descricaoSituacao", "regime", "apreciacao", "uriUltimoRelator"})

def linha_canonica(linha: dict) -> dict: ...      # tira CAMPOS_NAO_HISTORICOS
def hash_linha(canonica: dict) -> str: ...        # sha256 hex de json.dumps(sort_keys=True, ensure_ascii=False)

@dataclass
class ResultadoEventos:
    criados: int = 0
    atualizados: int = 0
    removidos: int = 0
    reaparecidos: int = 0

def upsert_eventos_camara(db: Session, prop: Proposicao, linhas: Sequence[dict], mapa: Mapa,
                          agora: datetime) -> ResultadoEventos: ...
def reclassificar_marcos(db: Session, mapa: Mapa, *, proposicao_ids: Sequence[UUID] | None = None) -> int: ...
```

  `chave = str(sequencia)`; sem `sequencia`, `"h:" + hash_linha(...)[:16]`. Campos gravados:
  `sequencia`, `data_hora`, `sigla_orgao`, `orgao_fonte_id` (`id_da_uri(uriOrgao)`), `orgao_tipo_cod`
  (tabela `orgaos`, consultando `GET /orgaos/{id}` só para órgão novo ou com mais de 30 dias), `cod_tipo`
  (`codTipoTramitacao`), `descricao`, `despacho`, `url`, `tipo_registro = "movimentacao"`, `marco` e
  `marco_entrada` (de `classificar_linha` com o `Mapa` inteiro — a classificação não filtra por
  publicável; quem publica decide), `hash_conteudo`.
- `packages/tramitacao/marcos.py::classificar_linha(linha: dict, casa: Casa, mapa: Mapa) ->
  Optional[MarcoClassificado]` (`MarcoClassificado`: `marco`, `entrada`, `titulo`, `fase_resultante`,
  `terminal`, `reabre`), regras em §2.4.
- `sincronizar_proposicao` (TRM-012) chama `upsert_eventos_camara` com as tramitações já baixadas;
  `ResultadoSync.criados` passa a contar linhas novas.

**Testes** — `tests/unit/test_marcos.py` (classificação, variantes, condição, A5/A6/A7);
`tests/integration/test_eventos_tramitacao.py` (replay + SQLite: critérios 1–5);
`tests/unit/test_sync_tramitacao.py` (critério 6). Comando:
`.venv/bin/python -m pytest tests/unit/test_marcos.py tests/integration/test_eventos_tramitacao.py -v`.

**Riscos e perguntas em aberto** — A Câmara pode reescrever o despacho de uma linha antiga: o hash
detecta e a linha é atualizada (conta em `atualizados`). Lacunas de sequência são normais (disc.
§3.2-2): não são erro.

**Instruções para o agente implementador** — Branch `trm-026-tramitacoes`. Ordem: `classificar_linha`
(puro) → migration + modelo → `upsert_eventos_camara` → integração no sync → `recalcular
--apenas-marcos`. **Não** gravar os campos de `CAMPOS_NAO_HISTORICOS`; **não** ordenar por data;
**não** apagar linha; **não** derivar fase aqui.

---

### TRM-027 — Fase persistida + resolução da cadeia de apensação + recálculo

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E2 Mapa e glossário · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; Maintainer (workflow de produção)
**Depende de:** TRM-025, TRM-026, decisão D2 (spec §10.2); PR #47 só para o workflow de recálculo · **Desbloqueia:** TRM-028, TRM-017 (métricas de fase)

**Problema** — Fase calculada na hora da leitura exigiria o histórico e a cadeia inteira a cada
visita; e uma apensada só tem fase pela cabeça da cadeia (PL 5/2025 → … → PL 5941/2013, disc. §3.2-5).

**Oportunidade** — Fase pronta no banco, filtrável na lista, com a regra e a versão gravadas;
apensadas com página própria e fase herdada (D2).

**Solução** — Colunas de fase (§1.3, bloco TRM-027); casa iniciadora pelos autores; resolução da
cadeia registrando os elos como "contexto" (sem categoria: fora da lista, D2); `recalcular_fases` em
ordem topológica; recálculo automático quando a `versao_publicada` muda.

**Escopo** — Dentro: migration, `fases.py`, integração no sync, comandos `recalcular` e `relatorio`,
gatilhos de recálculo, seleção de alvos incluindo cabeças. Fora: API (TRM-028).

**Critérios de aceite**
1. Com o pacote `pl-5-2025` (receita com cadeia): os elos ausentes são registrados com
   `origem_registro = "cadeia_apensacao"` e `categorias_zil` nula; `cabeca_fonte_id` = id do PL
   5941/2013; `cadeia_status = "resolvida"`; a fase da apensada = a da cabeça, `fase_herdada_de_id` =
   id interno da cabeça.
2. Ciclo sintético (A → B → A) → `cadeia_status = "ciclo"` e `nao_sabemos(principal_nao_resolvida)`;
   11 níveis → `profunda_demais`; `FonteIndisponivel` num elo → `principal_indisponivel`.
3. `casa_iniciadora`: `pl-1847-2024` → `senado`; `pl-2-2024` → `camara`; MPV → `congresso`;
   `/autores` só é chamado quando a coluna está nula.
4. Persistência: `fase`, `desfecho`, `fase_motivo`, `fase_regra`, `fase_versao_publicada`,
   `fase_desde`, `orgao_desde`, `orgao_efetivo_sigla`, `orgao_efetivo_nome`, `fase_casa`,
   `fase_evidencias`, `fase_calculada_em` gravados; segunda execução sem mudança não altera nada
   (nem `fase_calculada_em`). Com `pl-3474-2023` (status em CCP), `orgao_efetivo_sigla` é a comissão
   do último registro em comissão e a fase é `comissoes` (A19).
5. `recalcular` (sem rede) processa cabeças antes das apensadas e recalcula as apensadas de uma
   cabeça que mudou, mesmo que elas não tenham se movido.
6. **Gatilho de aprovação** (pedido do PM): (a) `diario` e `completo` comparam a `versao_publicada`
   do mapa com a maior `fase_versao_publicada` do banco e, se diferente, rodam `recalcular` de todas
   antes de sincronizar; (b) workflow `.github/workflows/tramitacao.yml` roda `validar` + `recalcular`
   em produção a cada push em `main` que toque `data/tramitacao/**` (depois do PR #47).
7. Alvos (TRM-012) passam a incluir as cabeças das acompanhadas (D2); a lista (`categorias_zil IS NOT
   NULL`) continua sem elas.
8. `relatorio` imprime, sobre as acompanhadas: contagem por fase, desfecho, motivo e regra;
   % `nao_sabemos` (M5, spec §2); situações sem mapa com contagem; e com `--exportar-situacoes
   <arquivo>` grava `data/tramitacao/amostras/situacoes.json` (insumo de V-C3 e do revisor `dados`).
9. `relatorio --simular-tudo-publicavel` calcula as fases em memória como se o mapa inteiro estivesse
   aprovado, **sem gravar nada**, e mostra a % de `nao_sabemos` projetada. No banco de
   desenvolvimento, depois de `completo`, a projeção fica abaixo de 5% (M5) — sem o órgão efetivo
   (A19) e a R9 pelo histórico (A20) ela seria ≈ 17%. É a prova de viabilidade da meta antes dos lotes.

**Specs técnicas**
- Migration `a2f6c9e0b7d1_fase_proposicao.py` (`down_revision` = head de TRM-026), colunas e índices
  de §1.3; sem FK nas autorreferências (§1.3). Acrescentar ao teste de migrations.
- `apps/workers/tramitacao/fases.py`:

```python
@dataclass(frozen=True)
class Cadeia:
    status: CadeiaStatus
    principal_id: Optional[UUID]
    cabeca_id: Optional[UUID]
    cabeca_fonte_id: Optional[str]
    elos: tuple[str, ...]                 # fonte_ids, da proposição até a cabeça

def resolver_cadeia(db: Session, client: CamaraClient, prop: Proposicao, *, agora: datetime,
                    cache: CacheConsultas, max_niveis: int = 10) -> Cadeia: ...
# orgao_efetivo: calculado por TRM-012 (packages/tramitacao/status.py) e gravado em proposicoes.orgao_efetivo_*
def orgao_desde(eventos: Sequence[Tramitacao], sigla_orgao: Optional[str]) -> Optional[date]: ...
    # data da linha mais recente com cod_tipo == "500" (Recebimento) e sigla_orgao igual à do órgão efetivo
def entrada_do_banco(prop: Proposicao, eventos: Sequence[Tramitacao], mapa: Mapa, hoje: date, *,
                     cadeia: Cadeia, cabeca: Optional[FaseDerivada]) -> EntradaFase: ...
def fase_persistida(prop: Proposicao) -> Optional[FaseDerivada]: ...      # para servir de `cabeca`
def aplicar_fase(prop: Proposicao, f: FaseDerivada, *, orgao_desde: Optional[date], agora: datetime) -> list[str]: ...
@dataclass
class ResultadoRecalculo:
    recalculadas: int = 0
    mudaram: int = 0
    por_regra: dict[str, int] = field(default_factory=dict)
def recalcular_fases(db: Session, mapa: Mapa, hoje: date, agora: datetime, *,
                     ids: Optional[Sequence[UUID]] = None) -> ResultadoRecalculo: ...
```

  `entrada_do_banco` monta a mesma `EntradaFase` que `montar_entrada` montaria das respostas brutas —
  teste: sincronizar um pacote por replay e comparar as duas.
- Integração no sync: depois do upsert de eventos, `casa_iniciadora` (se nula), `resolver_cadeia`
  (se `principal_fonte_id`), e no fim de `executar` `recalcular_fases(ids = processadas ∪ apensadas
  cujas cabeças foram processadas)`.
- CLI: `sync_tramitacao.py recalcular [--apenas-marcos] [--dry-run]`;
  `sync_tramitacao.py relatorio [--exportar-situacoes data/tramitacao/amostras/situacoes.json]`.
  Formato do arquivo: `{"gerado_em": "AAAA-MM-DD", "ambiente": "desenvolvimento|producao",
  "situacoes": [{"casa": "camara", "cod": "915", "descricao": "Aguardando Parecer", "quantidade": 50}]}`.
- Workflow (depois do PR #47, mesmo padrão de `direcoes.yml` desse PR):

```yaml
name: tramitacao
on:
  push:
    branches: [main]
    paths: ["data/tramitacao/**"]
  workflow_dispatch:
concurrency:
  group: dados-producao
  cancel-in-progress: false
permissions:
  contents: read
jobs:
  recalcular:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    env:
      DATABASE_URL: ${{ secrets.PRODUCAO_DATABASE_URL }}
      ENV: automacao
    steps:
      - name: Conferir o segredo do banco
        run: test -n "$DATABASE_URL" || { echo "::error::segredo PRODUCAO_DATABASE_URL não configurado"; exit 1; }
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12", cache: "pip", cache-dependency-path: apps/api/requirements.txt}
      - run: pip install -r apps/api/requirements.txt
      - run: python scripts/validar_tramitacao.py
      - run: python scripts/sync_tramitacao.py recalcular
```

**Testes** — `tests/integration/test_fase_persistida.py` (critérios 1, 3, 4, 5, 7 com replay e
SQLite), `tests/unit/test_cadeia.py` (critério 2, com banco e cliente de replay sintético),
`tests/unit/test_sync_tramitacao.py` (critério 6a, `relatorio`). Comando:
`.venv/bin/python -m pytest tests/integration/test_fase_persistida.py tests/unit/test_cadeia.py -v`.

**Riscos e perguntas em aberto** — Cabeça no Senado ou fora da Câmara: `principal_indisponivel`
até TRM-050. A cabeça pode ter, ela mesma, `uriPropPrincipal` nulo e situação "Tramitando em
Conjunto" (dado inconsistente): `nao_sabemos(principal_nao_resolvida)`.

**Instruções para o agente implementador** — Branch `trm-027-fase-persistida` (o workflow num PR
separado, depois do #47). Ordem: migration → `casa_iniciadora_dos_autores` (já em 025) → cadeia →
`entrada_do_banco` + teste de equivalência → `recalcular_fases` → integração → CLI → gatilho (a).
Prova: `relatorio` no banco de desenvolvimento antes e depois. **Não** pôr cabeça de contexto na lista;
**não** seguir cadeia além de 10 níveis; **não** gravar fase calculada com mapa inválido.

---

### TRM-028 — API: `GET /proposicoes/{id}/tramitacao`, `/eventos`, `GET /tramitacao/mapa`, contagem e filtro `fase`

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E2 Mapa e glossário · **Prioridade:** P1 · **Horizonte:** Agora · **Estimativa:** M
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; UI/UX e Design System (consumidores: TRM-040–045, TRM-030–035)
**Depende de:** TRM-027, TRM-022 (glossário), TRM-002 (pacotes golden para o gerador de fixtures do frontend, critério 9) · **Desbloqueia:** TRM-040, TRM-041, TRM-042, TRM-043, TRM-044, TRM-045, TRM-051; TRM-046-B (troca as fixtures "reais" pelas geradas — conflito 10 do DS)

**Problema** — Não há endpoint de tramitação, de mapa nem filtro por fase (disc. §1.5, §5.3).

**Oportunidade** — API-first (princípio 6 do projeto): toda a experiência de F1 consome contratos
estáveis; o frontend não deriva nada (spec §3, princípio 9).

**Solução** — Novo router `apps/api/routers/tramitacao.py` com os contratos de §1.5 (forma
reconciliada com UI/UX e Design System); campos de F1 em `ProposicaoRead`; filtros na lista.

**Escopo** — Dentro: endpoints, montagem de etapas, frase e rótulos, recheque de publicável na
leitura, contagem, testes de contrato. Fora: interface; próximos passos agendados (TRM-051); norma
detalhada (`GET /proposicoes/{id}/norma`, TRM-053).

**Critérios de aceite**
1. Os quatro endpoints respondem com os schemas de §1.5; 404 para proposição inexistente; 503 com
   `{"detail": "Mapa de tramitação indisponível"}` quando o mapa não carrega.
2. `fase_rotulo` nunca é nulo em `onde_esta` — matriz de testes: fase normal, desfecho com e sem
   "onde parou", apensada, recém-apresentada, cada motivo de `nao_sabemos`.
3. **Gate de publicação (M7):** em `/tramitacao/mapa`, toda entrada com `publicavel: false` tem
   `texto`, `texto_curto`, `base_legal` vazios/nulos; rito não publicável sai com `etapas: []` e
   `desfechos: []`; `marcos[]` só traz marcos de entrada publicável; `regra_descricao` só se a regra
   é publicável.
4. **Recheque na leitura:** se a `FaseDef`/`DesfechoDef` do resultado persistido deixou de ser
   publicável (conteúdo alterado no deploy), a resposta é `nao_sabemos(mapa_nao_aprovado)`.
5. `etapas[]`: vazias com `fase` nula ou `nao_sabemos`; com desfecho, a etapa de "onde parou" é
   `interrompida` com `nota` = rótulo do desfecho e as seguintes `futura`; opcional sem marco antes
   da atual é `pulada` com `nota = nota_pulada`; em `norma`, a etapa final é `feita`.
6. `GET /proposicoes?fase=comissoes&fase=plenario` filtra `fase IN (...) AND desfecho IS NULL`;
   `desfecho=arquivada`; `fase=nao_sabemos`; `apensada=true`.
7. `GET /proposicoes/{id}/tramitacao/eventos?page=2&per_page=20` pagina do mais recente para o mais
   antigo, sem linhas `removido_na_fonte_em`.
8. `ROTULO_NAO_SABEMOS` igual ao texto de `apps/web/lib/tramitacao/textos.ts` (teste que lê o arquivo;
   `pytest.skip` com motivo enquanto TRM-046 não existir).
9. **Fixtures do frontend geradas pela API** (conflito 10 do DS): `scripts/gerar_fixtures_frontend.py`
   monta um SQLite temporário com os pacotes golden de TRM-002 (replay → `registrar_proposicao` →
   sync → `recalcular_fases`), sobe a API com `TestClient` e grava as respostas de
   `GET /proposicoes/{id}`, `/tramitacao`, `/tramitacao/eventos` e `/tramitacao/mapa` em
   `apps/web/tests/fixtures/api/tramitacao/gerado/<caso>-<recurso>.json` — em dois modos: mapa com
   tudo publicável (diretório temporário com `revisao.yml` aprovando tudo pelo hash) e mapa de
   produção (`mapa_nao_aprovado`). IDs estáveis: na saída, cada UUID interno é trocado por
   `uuid5(NAMESPACE_URL, "zil:camara:" + fonte_id)`; `datetime` gravado pelo ZIL é fixado em
   `2026-10-31T12:00:00-03:00` (o gerador injeta `agora`). Um teste
   (`tests/contract/test_fixtures_frontend.py`) regera em memória e falha se os arquivos versionados
   estiverem diferentes — mudar o contrato sem regerar quebra a CI de backend, não a de frontend.
   Os casos sintéticos da UI/UX continuam escritos à mão, mas validados contra os schemas Pydantic
   pelo mesmo teste (`TramitacaoRead.model_validate`).
10. `situacao_glossario` em `onde_esta`; `herdada_de.acompanhada` (A01 × A02 da matriz de UI/UX).

**Specs técnicas**
- `apps/api/routers/tramitacao.py` (incluído em `apps/api/main.py` depois de `legislativo`):

```python
@router.get("/proposicoes/{proposicao_id}/tramitacao", response_model=TramitacaoRead)
@router.get("/proposicoes/{proposicao_id}/tramitacao/eventos", response_model=EventosPagina)
@router.get("/tramitacao/mapa", response_model=MapaRead)
@router.get("/tramitacao/contagem", response_model=ContagemRead)
```

- Montagem (`packages/tramitacao/`, puro, testável sem API):

```python
# rotulos.py
ROTULO_NAO_SABEMOS = "Fase não identificada"     # texto da matriz de TRM-046 (UI/UX)
def rotulo_fase(mapa: Mapa, f: FaseDerivada, especie: str) -> str: ...      # regra de §1.5
def rotulo_desfecho(mapa: Mapa, d: Desfecho) -> Optional[str]: ...

# etapas.py
def chave_rito(especie: str, casa_iniciadora: Optional[str]) -> Optional[str]: ...   # "PL_CD", "PL_SF", "MPV_CN"
@dataclass(frozen=True)
class EtapaEstado:
    id: str; nome: str; fase: Fase; estado: EstadoEtapa; quando: Optional[date]; casa: Optional[str]; nota: Optional[str]
def montar_etapas(rito: Rito, f: FaseDerivada, inicio_por_fase: Mapping[Fase, date],
                  desfecho_rotulo: Optional[str]) -> list[EtapaEstado]: ...

# frase.py
def valores_marcadores(*, casa: Optional[str], orgao_nome: Optional[str], sigla_orgao: Optional[str],
                       desde: Optional[date], orgao_desde: Optional[date], data_marco: Optional[date],
                       norma: Optional[NormaExtraida], especie: str, principal: Optional[tuple[str, int, int]],
                       frase_principal: Optional[str]) -> dict[str, Optional[str]]: ...
def montar_frase(modelos: Sequence[ModeloFrase], valores: Mapping[str, Optional[str]], *,
                 casa: Optional[str], especie: str, veto_parcial: Optional[bool]) -> Optional[str]: ...
```

  Frase: modelos da `DesfechoDef` (se desfecho), da `ApensadaDef` (se apensada; `frase_principal` =
  frase da cabeça) ou da `FaseDef`; `nao_sabemos` → `None`. Datas em `dd/mm/aaaa`.
- `como_sabemos.fontes`: `{"rotulo": "Câmara — situação atual", "url":
  "https://dadosabertos.camara.leg.br/api/v2/proposicoes/{fonte_id}"}`, `{"rotulo": "Câmara —
  tramitações", "url": ".../tramitacoes"}`, `{"rotulo": "Mapa de fases do ZIL, versão {n}", "url":
  f"{settings.REPO_URL}/blob/main/data/tramitacao/fases.yml"}` e, se apensada, as duas da cabeça.
  `REPO_URL` nova em `core/config.py` com padrão `https://github.com/melissa-pereira-deel/manifesto-zil`.
- `marcos[]`: linhas com `marco` não nulo, `marco_entrada` publicável, `linha_do_tempo` verdadeiro,
  não removidas, em ordem de `sequencia`; `titulo` = título da variante ou do marco; `votacao_id` =
  `Votacao` da proposição com `date(data) == date(data_hora)` quando o marco é `votacao_plenario` ou
  `aprovacao_plenario` (a primeira por `data`).
- `onde_esta.sigla_orgao`/`orgao_nome` = órgão **efetivo** (`orgao_efetivo_*`, A19); a situação
  oficial continua inteira em `situacao_oficial`, e `ProposicaoRead.sigla_orgao` (F0) continua sendo o
  do status.
- `relator`: `RelatorRead` com `nome = relator_nome`; `partido`, `uf`, `parlamentar_id` de
  `parlamentares` pelo `relator_fonte_id`, se existir.
- `/tramitacao/contagem` com os filtros `categoria`, `tipo`, `ano` (mesma semântica da lista).
- `ProposicaoRead`: campos de F1 (§1.5) montados em `_proposicao_read` a partir das colunas de
  TRM-027, com o recheque do critério 4.

**Testes** — `tests/contract/test_api_tramitacao.py` (critérios 1–8, com proposições semeadas e
mapas em diretório temporário via `ZIL_DATA_DIR`, aprovando entradas com `revisao.yml` gerado pelo
teste com `hash_entrada`); `tests/unit/test_etapas.py`, `tests/unit/test_frase.py`,
`tests/unit/test_rotulos.py` (puros). Comando: `.venv/bin/python -m pytest tests/contract/test_api_tramitacao.py tests/unit/test_etapas.py tests/unit/test_frase.py tests/unit/test_rotulos.py -v`.

**Riscos e perguntas em aberto** — `fase` nula com desfecho (apensada prejudicada): os tipos de
UI/UX e DS declaram `fase` não nula — eles precisam aceitar `null` quando `desfecho != null` (o
`FaseSelo` usa o desfecho; o link vai para `/como-vira-lei#desfechos`, regra de UI/UX §1.4). UI/UX disse que conta no cliente e não
precisa de `/tramitacao/contagem`: o endpoint fica, porque `/como-vira-lei` mostra "N proposições
estão aqui agora" por etapa sem baixar a lista inteira.

**Instruções para o agente implementador** — Branch `trm-028-api-tramitacao`. Ordem: funções puras
(rótulos, etapas, frase) → schemas → endpoints → filtros → contrato. Prova: `curl` de
`/proposicoes/<PL 2/2024>/tramitacao` e de `/tramitacao/mapa` com o mapa de produção (tudo não
publicável) e com um mapa de teste aprovado. **Não** calcular fase na leitura (só ler a persistida e
rechecar publicável); **não** devolver texto não publicável; **não** usar LLM; **não** devolver
`fase_rotulo` nulo.

---

## 5. Tarefas — E5 (Depois)

### TRM-050 — Migração do `senado_client` para `/processo*` e `/votacao`

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E5 Depois · **Prioridade:** P3 · **Horizonte:** Depois · **Estimativa:** G (quebrar: cliente; ingestão de votações; vínculo e fase)
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; mapeamento do Senado pelo processo de TRM-023
**Depende de:** TRM-002 (pacotes `senado_processo`), TRM-012 (padrão de retentativa), TRM-026/027 (integração) · **Desbloqueia:** TRM-051 (Senado), TRM-053; R5 completa; D3 (descobrir proposições iniciadas no Senado)

**Problema** — O cliente usa `/materia/*`, depreciado (sunset em 01/02/2026, já passado), e espera um
formato que a API não devolve mais: descarta todas as matérias (`packages/senado_client/__init__.py:202-230`;
banco com 0 do Senado); `/votacao/senador/{id}` dá 404 (disc. §1.4).

**Solução** — Métodos novos no `SenadoClient`, com transporte injetável e a política de retentativa de
TRM-012: `buscar_processos(sigla, numero, ano)`, `obter_processo(id)`, `listar_votacoes(id_processo)`
(`/votacao?idProcesso=`), `obter_prazos(id_processo)` (`/processo/prazo?idProcesso=`),
`listar_tipos_situacao()`. Vínculo Câmara↔Senado por `/processo?sigla=&numero=&ano=` e
`outrosNumeros` (disc. §3.3). Colunas `senado_processo_id`, `senado_codigo_materia`,
`senado_sigla_situacao` (migration depois de 027). Linhas do Senado em `tramitacoes`: `situacoes`
(com `inicio`/`fim` e `cod_situacao` — histórico real) e `informesLegislativos` (`tipo_registro =
"informe"`). `EntradaSenado` liga R1 (`normaGerada`) e R5 (`siglaSituacaoAtual` mapeada em
`regra_R5.situacoes_senado` etc., saindo de `nao_mapeados.yml`). `normaGerada` grava norma com
`norma_fonte = "senado_norma_gerada"`, que tem precedência sobre o despacho.

**Critérios de aceite** — Zero chamadas a `/materia` (o replay falha se houver); as Leis 14.871,
15.103, 14.993 e 14.973 batem com `normaGerada` (disc. §8, F3); falha do Senado não derruba o passo
da Câmara (passo separado no cron, erros por proposição); situações do Senado mapeadas só depois de
aprovadas (lote próprio de TRM-029); `crawlers/senado.py` reescrito sobre os métodos novos.

**Não fazer** — Usar MCP comunitário em produção (disc. §3.6); descobrir proposições do Senado antes
da decisão D3 mudar.

### TRM-051 — Próximos passos agendados (eventos + pauta, Câmara e Senado)

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E5 Depois · **Prioridade:** P3 · **Horizonte:** Depois · **Estimativa:** G (quebrar: Câmara; Senado; prazos)
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; UI/UX (texto "estar na pauta não garante votação")
**Depende de:** TRM-028; TRM-050 para o Senado · **Desbloqueia:** "O que vem depois" (disc. §6.1-4)

**Problema** — Não há como dizer "na pauta da CME em 04/11" (disc. §3.1); a matéria vem em
`proposicaoRelacionada_`, e `proposicao_` costuma ser o parecer.

**Solução** — Tabela `agenda_itens` (`proposicao_id` FK, `casa`, `evento_fonte_id`, `inicio`,
`sigla_orgao`, `situacao_evento`, `titulo`, `url`, `obtido_em`; único `(proposicao_id, casa,
evento_fonte_id)`); passo no sync: `GET /eventos?dataInicio=hoje&dataFim=hoje+14&idOrgao=` só nos
órgãos onde estão as acompanhadas, `GET /eventos/{id}/pauta`, casando por `proposicaoRelacionada_`;
Senado `/plenario/agenda/dia/{data}` e `/comissao/agenda/{ini}/{fim}`. Prazos D com início oficial
(sanção, CF 66 § 1º; MPV, CF 62) como `{inicio, base_legal, texto}` — **sem** calcular data final
em dias úteis. API: `onde_esta.proximos = {previstas[], agendadas[], prazos[]}` (disc. §5.3).

**Critérios de aceite** — Nenhuma data futura sem evento ou prazo legal com fonte (disc. §8, F2);
evento cancelado ou realizado sai de `agendadas`; orçamento ≤ 1 + nº de órgãos + nº de eventos por
dia; teste com pauta gravada em que `proposicao_` é parecer.

### TRM-052 — Rota prevista pelo despacho (parser)

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E5 Depois · **Prioridade:** P3 · **Horizonte:** Depois · **Estimativa:** G
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura
**Depende de:** TRM-011, TRM-026 · **Desbloqueia:** "Faltam pareceres da CME e da CCJC" (disc. §6.1-4)

**Problema** — O despacho de distribuição traz o roteiro em texto livre ("Às Comissões de Indústria,
Comércio e Serviços; Ciência, Tecnologia e Inovação e Constituição e Justiça e de Cidadania (Art. 54,
RICD). Proposição Sujeita à Apreciação Conclusiva pelas Comissões - Art. 24 II", disc. §3.1).

**Solução** — `packages/tramitacao/rota.py::extrair_rota(despacho: str, comissoes: Mapping[str, str])
-> RotaPrevista | None` (`comissoes_merito`, `comissoes_art54`, `apreciacao_chave`, `regime_chave`,
`trecho`), com nome → sigla vindo de um snapshot novo `referencias/camara-comissoes.json` (`GET
/orgaos?codTipoOrgao=2`, TRM-020); coluna `rota_prevista` JSON(none_as_null=True); pareceres dados =
órgãos com marco `parecer_aprovado` depois da última distribuição; "faltam" = rota − dados.

**Critérios de aceite** — ≥ 90% de uma amostra fixa de 200 despachos de distribuição (cód. 110, 2024–
2026, sorteio com semente registrada) com rota extraída; o resto como "rota não identificada" (disc.
§8, F2); testes com os despachos reais dos pacotes (2269745 seq. 8 e 26; 2416804 seq. 11).

### TRM-053 — Normas, vetos e regulamentação (vides do Senado + curadoria)

**Revisão:** PM (processo) pendente · UI/UX e DS consultados

**Épico:** E5 Depois · **Prioridade:** P3 · **Horizonte:** Depois · **Estimativa:** G (quebrar: tabelas e migração da norma; vetos; regulamentação e curadoria)
**Dono da spec:** Arquitetura · **Revisões obrigatórias:** Arquitetura; Maintainer (curadoria em `data/normas/`)
**Depende de:** TRM-050, TRM-013, D4 (só as 4 leis do placar) · **Desbloqueia:** TRM-054; bloco "Depois da lei" (disc. §6.1-7)

**Problema** — O número da lei (TRM-013) é o começo da cadeia; vetos, derrubadas e regulamentação
não estão em lugar nenhum. O único vínculo lei → decreto estruturado é o `vides` da API de
legislação do Senado (disc. §3.4).

**Solução** — Tabelas `normas`, `vetos`, `regulamentacoes` (disc. §5.1), com `fonte_dado` e
`verificado_em`; migração das colunas `norma_*` de `proposicoes` para uma linha em `normas` +
`norma_id` (dados copiados na migration; colunas antigas removidas numa migration seguinte);
`GET /legislacao/{tipo}/{num}/{ano}` do Senado (vides "Declaração de Regulamentação Permanente de
Norma"; `urlDocumento` confirma o URN e liga `links_verificados`); curadoria em `data/normas/*.yml`
com `scripts/validar_normas.py` (barra linguagem causal, disc. §7) e `scripts/apply_normas.py` (padrão
de `apply_direcoes.py`); `GET /proposicoes/{id}/norma` com `estado` ∈ `nao_verificada`,
`sem_regulamentacao_conhecida`, `com_atos_vinculados`, `autoaplicavel_declarada`.

**Critérios de aceite** — Disc. §8, F3/F4: Lei 14.871 mostra os Decretos 12.175 e 12.242 e o PDL
367/2024; Lei 15.103 mostra "sem regulamentação conhecida" com as fontes consultadas e a data; todo
vínculo com fonte e `verificado_em`; nenhum efeito sobre o Score ZIL.

---

## 6. Ordem de implementação, paralelismo e PR #47

Alinhada às ondas da spec §5.1 (as ondas contam a partir do merge das dependências).

| Onda | Arquitetura — agente A | Arquitetura — agente B | Por quê |
| --- | --- | --- | --- |
| 0 | TRM-011 (colunas + teste de migration) | TRM-002 (clientes com transporte, replay, gravações) e TRM-020 (snapshots) | sem dependências; 021a também pode começar aqui (só esquema) |
| 1 | TRM-010 (registrar), depois TRM-013 (norma) | TRM-021a (esquema, carga, `revisao.py`) → TRM-021b (conteúdo v0) | 010 e 013 precisam de 011 + 002; 021b precisa de 020 |
| 2 | TRM-012 (cliente estrito, sync, IngestionRun) | TRM-024 (V-E/V-C já; V-R quando o formato de TRM-023 estiver mergeado) e TRM-014 (API F0) | **F0 de dados completa no fim desta onda** |
| 3 | TRM-026 (tabela `tramitacoes`) | TRM-025a → TRM-025b (motor + golden) | 026 precisa de 012; 025 de 021b + 024 + 002 |
| 4 | TRM-027 (fase persistida, cadeia, gatilhos) | — (ou revisão dos lotes L2–L3 de TRM-029 com o motor) | junta 025 e 026 |
| 5 | TRM-028 (API de tramitação e gerador de fixtures do frontend) | — | precisa de 027, do glossário (TRM-022) e dos pacotes de TRM-002; entrega as fixtures geradas para TRM-046-B |
| D | TRM-050 → TRM-053; TRM-052; TRM-051 | | Depois |

**Caminhos críticos** — F0: 011 → 010 → 012 e 011 → 013 → 014. F1: 020 → 021 → 024 → 025 → 027 → 028
(o gargalo de calendário é humano: os lotes de TRM-029, spec §5.2).

**Arquivos quentes (um PR por vez, rebase a cada merge)** — `apps/api/models/__init__.py` e
`apps/api/schemas/__init__.py`: 011 → 014 → 026 → 027 → 028; migrations: 011 → 026 → 027 (→ 050 →
053); `packages/camara_client/__init__.py`: 002 → 012; `apps/workers/tramitacao/sincronizacao.py`:
012 → 013 (`aplicar_norma`) → 026 → 027; `apps/api/routers/legislativo.py`: PR #48/#49 → 014 → 028.

**PR #47 (cron) — desacoplamento.** Nada de E1/E2 espera o #47:
1. `scripts/sync_tramitacao.py` roda sozinho (local ou contra produção com `DATABASE_URL`) e grava a
   própria `IngestionRun`, como `scripts/sync_votacoes_zil.py` faz hoje.
2. Depois do merge do #47, dois PRs pequenos: (a) último passo de TRM-012 — passos `tramitacao_diaria`
   no job `diario` (depois de `proposicoes`, antes de `scores`) e `tramitacao_completa` no `cadastros`
   semanal, `IngestionRun` via `apps/workers/execucoes.py`, opção `tramitacao` no `dados.yml`;
   (b) workflow `tramitacao.yml` de TRM-027 (recálculo a cada aprovação mergeada).
3. Até (b) existir, o gatilho (a) de TRM-027 — o sync compara `versao_publicada` e recalcula — já
   garante que uma aprovação chega às fases no próximo sync.

**PR #48 e #49** — tocam `apps/api/routers/legislativo.py` e (o #49) `ProposicaoRead`: TRM-014 e
TRM-028 rebaseiam neles e preservam o `model_validator` do #49.

---

## 7. O que UI/UX, Design System e Product precisam respeitar (decisões de esquema)

1. **Fonte única dos textos**: rótulos, frases, títulos de marco, etapas/desfechos de rito e glossário
   vêm da API, a partir de `data/tramitacao/`, e **só se publicáveis** (estado `aprovado` + hash). O
   rótulo de `nao_sabemos` ("Fase não identificada") é a única constante de texto na API, copiada da
   matriz de TRM-046, com teste de igualdade.
2. **`fase_rotulo` nunca nulo** em `onde_esta` (precedência em §1.5); ≤ 32 caracteres (validador).
3. **`fase` pode ser nula** só com `desfecho` não nulo e "onde parou" desconhecido (apensada
   prejudicada). Os tipos de UI/UX e DS precisam aceitar isso; `etapas` vem vazia nesse caso.
4. **`recem_apresentada`** = `fase: "apresentada"` + `fase_motivo: "recem_apresentada"` (R9); nunca `nao_sabemos`.
5. **Nomes de campo**: `fase_motivo` (não `motivo`); `como_sabemos.versao_publicada` (int, não
   `mapa_versao`); `como_sabemos.regra_descricao`; `como_sabemos.fontes[]` = `{rotulo, url}`;
   `etapas[].nota`; `etapas[].fase`; `relator` = `{nome, partido, uf, parlamentar_id}`;
   `herdada_de` = `{id, fonte_id, rotulo, url_camara, acompanhada}`; `TramitacaoRead.rito` = `{chave,
   especie, casa_iniciadora}`; `ProposicaoRead.casa_iniciadora`; `situacao_glossario` (em
   `ProposicaoRead` e `onde_esta`: a chave do glossário da situação oficial — não casar por `termo`);
   `orgao_efetivo_sigla/nome` e `principal_url_camara` em `ProposicaoRead` (F0).
6. **`/tramitacao/mapa`**: etapa `{id, fase, nome, casa, o_que_acontece, quem_decide, prazo:
   {classe, texto} | null, base_legal: {rotulo, url, norma, dispositivo}[], opcional, condicao}`;
   desfecho `{desfecho, rotulo, texto, base_legal, a_partir_de: string[] | "qualquer"}`; rito com
   `publicavel` e `revisao` (não publicável → `etapas: []`); `especies[].descricao` vem de
   `glossario/especie_<sigla>`; `MapaRead.versao_publicada` (DS usava `versao`).
7. **Glossário**: chave `snake_case` (`^[a-z][a-z0-9_]{2,59}$`), que vira âncora em
   `/como-vira-lei/situacoes#termo-<chave>`; `texto_curto` ≤ 160, `texto` ≤ 900; `tipo` ∈ {situacao,
   regime, apreciacao, fase, desfecho, apensada, etapa, especie, conceito} (o "termo" de UI/UX é
   `conceito`); `codigos[]` e o atalho `codigo`; chaves fixas: as dez de regime e apreciação de §2.6
   (inclui `apreciacao_conclusiva_com_urgencia`, `regime_medida_provisoria`,
   `regime_urgencia_acordo_internacional`, `regime_concessao_radiodifusao`), `fase_<fase>`,
   `desfecho_<desfecho>`, `apensada`, `especie_<sigla>`; situação administrativa sem artigo usa
   `base_legal_motivo` com o texto padronizado.
7a. **Datas e horas**: `date` = `"AAAA-MM-DD"` (nunca passar por `new Date()`); `datetime` sempre com
   `-03:00`. **Lista**: `X-Total-Count` no cabeçalho de `GET /proposicoes`. **Mapa**:
   `situacoes_camara[] = {codigo: string, descricao, glossario, tratada}`.
8. **Frases**: marcadores `na_casa`, `da_casa`, `membros`, `orgao`, `desde`, `orgao_desde`, `data`,
   `norma_com_artigo`, `na_lei`, `principal_com_artigo`, `frase_principal`; filtros por `casa`,
   `especie`, `veto_parcial`; para "Está na CFT desde…" use `{orgao_desde}` (chegada ao órgão), não
   `{desde}` (início da fase).
9. **Eventos**: `?page=&per_page=` e `{items, total, page, per_page, pages}` (convenção do
   repositório), do mais recente para o mais antigo.
10. **Product (TRM-023)**: estado em `revisao.yml` com o campo extra `revisado_por`; `hash_entrada`
    e `entradas_publicaveis` implementados em `packages/tramitacao/revisao.py` e reexportados em
    `apps/workers/tramitacao/revisao.py` (o caminho da spec), porque a API no container não enxerga
    `apps.workers`; situações oficiais revisadas dentro das regras (`fases/regra_R7` etc.); entradas
    extras `ritos/pos_lei` e `glossario/especie_<sigla>` para os lotes L5/L6; `nao_mapeados` em
    `nao_mapeados.yml`, reescrito pelo script de TRM-020 (sem aprovação); o marco 1236 pode não ter
    caso real de rejeição de proposição — proposta: aceitá-lo em `nao_mapeados` no DoD da v1 (§6.11-4).

---

## 8. Resumo

Escrevi `specs/013-tramitacao/backlog-dados.md`: modelo de dados (28 colunas de status e norma em
`proposicoes` por TRM-011, tabela `tramitacoes` por TRM-026, 16 colunas de fase por TRM-027),
contratos Pydantic completos (`ProposicaoRead`, tramitação, eventos, mapa, contagem), o esquema de
`data/tramitacao/` (Pydantic `extra="forbid"`, `base_legal {norma, dispositivo, url}`, `fontes`,
`casos`, `pendente`, estado em `revisao.yml` com hash), exemplos reais (R1–R10, rito PL_CD e MPV_CN,
três termos do glossário), o conteúdo mínimo do rascunho v0, e as 13 tarefas detalhadas mais 4 de
Depois, com ordem e desacoplamento do PR #47. Não criei tarefa nova: a ligação ao cron é o último
passo de TRM-012 (TRM-017 e TRM-029 já são do PM).

Vinte e dois fatos conferidos ao vivo mudaram o desenho (§0.1) — entre eles: `retry-after` vem em toda
resposta; código 100 marca ofícios; 1236 marca rejeição de requerimento; 502 pode ser
"prejudicada"; PEC 45/2019 virou norma sem marco nem número; a janela D-7 funciona (2.227 itens, 23
páginas).

Conflitos para resolver: (1) tipos de UI/UX e DS precisam aceitar `fase` nula com desfecho; (2) nomes
reconciliados entre UI/UX e DS em `/tramitacao/mapa` (§7-6) — os dois devem adotar os desta spec;
(3) `versao_publicada` substitui `mapa_versao` nos tipos de frontend; (4) `revisao.py` mora em
`packages/` (reexportado no caminho do PM) por causa do container; (5) PM: DoD da v1 com 1236 sem caso
real; entradas extras `ritos/pos_lei` e `glossario/especie_*`; (6) UI/UX: "desde" só em F1, e a frase
de comissões deve usar `{orgao_desde}`.

**Rodada 2 (pedidos de UI/UX e DS, conferidos):** regra urgência + conclusiva
(`apreciacao_conclusiva_com_urgencia`, 9 casos confirmados); regimes ampliados e "."/"Indefinida"
como nulo; `datetime` com `-03:00`; `X-Total-Count`; `situacoes_camara` no mapa; âncora
`termo-<chave>`; V-R7 aceita situação administrativa; `arquivada` sem "pode ser desarquivada" e
`devolvida` pelo RICD art. 137 (texto compilado conferido); **órgão efetivo** já em F0 e na R7 (23 das
240 tinham o status em CCP/MESA) e **R9 pelo histórico** (17 nulas antigas) — sem os dois, `nao_sabemos`
projetado ≈ 17%, acima da meta de 5%. Achados de código da UI/UX são do frontend (nenhum TRM-018).
Revisão das specs de interface em `revisoes/arquitetura-sobre-interface-e-ds.md`.

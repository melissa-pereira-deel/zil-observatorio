# Evidência do RFC-005

O instrumento e os dados por trás da seção 4 de
[`005-rfc-destino-das-categorias.md`](../005-rfc-destino-das-categorias.md).

Está aqui, e não em `scripts/`, porque não é ferramenta operacional do projeto:
é a prova de uma decisão datada. O `scripts/` é a caixa documentada no
`CLAUDE.md` (curadoria, painel, sync, infra), e manter um experimento de RFC lá
criaria obrigação de manutenção para código que existe para sustentar um
argumento, não para rodar no dia a dia.

```
exp_taxonomia.py       o harness
baseline.txt           o portão: 20/28/12/12 candidatas, regressão 9/9 vazias
med-saude.txt          vocabulário de saúde      → 2 candidatas em 4 anos
med-instrumentos.txt   vocabulário de instrumentos → 4 candidatas, 0 matérias novas
corpus/*.jsonl         1.140 votações com voto nominal, 2023-2026 (656 KB)
```

## Como refazer

```bash
# do repositório, com o .venv do projeto
D=docs/decisions/005-rfc-destino-das-categorias

# 1. O PORTÃO VEM PRIMEIRO — sem ele, nenhum número abaixo vale
.venv/bin/python $D/exp_taxonomia.py --baseline --ano 2023 2024 2025 2026
diff <(...) $D/baseline.txt          # deve ser idêntico

# 2. os vocabulários candidatos
.venv/bin/python $D/exp_taxonomia.py --vocab saude        --ano 2023 2024 2025 2026
.venv/bin/python $D/exp_taxonomia.py --vocab instrumentos --ano 2023 2024 2025 2026

# 3. recoletar da API (só se quiser conferir se a fonte mudou — ver abaixo)
.venv/bin/python $D/exp_taxonomia.py --coletar --ano 2023 2024 2025 2026
```

Nada aqui precisa de `ANTHROPIC_API_KEY` nem de banco. `--coletar` precisa de
rede; os outros modos rodam offline sobre o corpus committado.

## Quatro coisas que não se leem nos arquivos

**O portão é o que torna a medição confiável, e ele pegou um erro real.** Rodar
com a taxonomia do repositório inalterada tem de reproduzir as varreduras
guardadas — mesmos IDs, mesmos escores, em ordem. A primeira versão da checagem
de regressão usava `classificar_texto_com_evidencia` (casamento cru) onde a
suíte afirma sobre `classificar_texto` (que aplica a regra de keyword forte), e
por isso acusou 6 regressões inexistentes **na taxonomia inalterada**. Era erro
do medidor, não do medido. Sem o portão, aquele número teria entrado no RFC.

**`--coletar` sobrescreve o corpus, e isso é proposital.** Recoletar e olhar o
`git diff` responde uma pergunta que nada mais no projeto responde hoje: a API da
Câmara mudou o que devolve para estas votações? O corpus committado é o estado
em 2026-10-21/22.

**As 9 afirmações de "não classifica" são extraídas por AST**, não copiadas, de
`tests/unit/test_classifier.py` — cada uma é um falso positivo que o projeto já
pagou para descobrir (`pesquisa clínica com seres humanos`, `Tarifa Social de
Água e Esgoto`, atletas do Mercosul, a LGPD dentro do projeto de homicídio
qualificado). Se a suíte mudar, a checagem acompanha sem ninguém lembrar de
sincronizar.

**A troca de taxonomia em memória é frágil, e está declarada como tal.**
`aplicar_taxonomia()` reatribui globais do classificador (`_taxonomia`,
`_patterns_com_keyword`, `_patterns`, `KEYWORDS_FRACAS`) porque o módulo as monta
em código de topo, não numa função — não há builder a chamar. Se
`apps/workers/classifiers/__init__.py:66-92` mudar, essa réplica sai de sincronia
— e o portão é o que acusa.

## O corpus não é dado editorial

`corpus/*.jsonl` é dado público derivado da API de Dados Abertos da Câmara:
`fonte_id`, descrição da votação, data, placar, ementa e identificação da
proposição. Não passa pela governança de `data/`, não é curado e não entra no
Score ZIL. Por isso não mora em `data/`.

## Relacionado

- [RFC-006](../006-rfc-pipeline-de-texto-e-classificacao.md) — como o
  classificador funciona e o que fazer com o texto integral. Trata da mesma
  máquina por outro ângulo, e as medições dele (§3.1) estão descritas em prosa,
  sem código committado; se virarem artefato, esta pasta serve de forma.
- [issue #27](https://github.com/melissa-pereira-deel/zil-observatorio/issues/27)
  — a indexação da Câmara participa da classificação e não é persistida. É por
  causa dela que a seção 4 do RFC-005 **não** mede o efeito no banco.

**Procedência:** o harness e a medição são de Claude; a decisão do RFC é da
maintainer.

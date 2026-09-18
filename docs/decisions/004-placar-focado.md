# ADR-004: Placar focado em vez de índice abrangente

**Data:** 2026-09-18
**Status:** Aceito

## Contexto

A v1 foi especificada como um **índice abrangente**: Score ZIL calculado para os
594 parlamentares (513 deputados + 81 senadores), em 9 categorias, a partir de
todas as votações relevantes. A métrica de sucesso no PRD e no ROADMAP era
"100% dos 513 deputados; 80%+ dos 81 senadores".

O motor foi construído e funciona. O que não existe é a matéria-prima que ele
consome.

O Score ZIL só considera votações com `direcao_esperada` definida — e definir
essa direção é um **juízo editorial**, nunca automático: exige entender a
matéria, ler o texto legal e avaliar o impacto na soberania industrial. Isso
custa horas por votação.

Em 2026-09-18 existem **7 classificações**, todas marcadas
`validacao: nao-validado`, todas da Câmara, todas na mesma direção. Com essa
base o ranking não discrimina: a maioria dos parlamentares empata na mesma nota.

O gargalo, portanto, nunca foi código. É **julgamento editorial em volume** — e
o projeto tem um maintainer ativo (ver `docs/GOVERNANCE.md`, "Estado atual da
governança"). Abrangência exige capacidade editorial industrial que não existe
e que nenhuma ferramenta cria sozinha: mesmo o painel de agentes proposto em
`docs/PRD-PAINEL.md` precisa de validação humana, que é justamente o recurso
escasso.

Manter a meta de abrangência tem dois custos. O primeiro é prático: ela não é
atingível, então o produto nunca sai. O segundo é de credibilidade: enquanto a
meta permanecer escrita, a pressão é publicar um índice raso para cumpri-la — e
um ranking de base fina publicado em período eleitoral é o cenário de maior
risco para um projeto cujo ativo é ser confiável sobre fatos.

## Decisão

**Trocar abrangência por profundidade.** O produto deixa de ser um índice de
todos os parlamentares e passa a ser um **placar focado**:

> Como cada parlamentar votou nas ~10 votações que mais importaram para a
> soberania industrial.

| Dimensão | Antes | Agora |
|---|---|---|
| Universo de votações | Todas as classificadas como ZIL | ~10 selecionadas e bem pesquisadas |
| Meta de cobertura | 100% dos deputados, 80%+ dos senadores | Não há meta de cobertura |
| Critério de qualidade | Quantidade de votações classificadas | Profundidade da justificativa de cada uma |
| Unidade de trabalho | Classificar em lote | Pesquisar uma votação por vez |

**O Score ZIL permanece** como número de −10 a +10, com a mesma fórmula e o
mesmo motor. O que muda é o universo sobre o qual ele opera, e a promessa
associada a ele.

### O que isto não é

Não é abandono da ambição de cobertura. É o reconhecimento de que cobertura é
consequência de capacidade editorial, não premissa de produto — e que a
sequência correta é conquistar a capacidade antes de prometer o resultado.

## Consequências

- **Positivo:** o produto passa a ser entregável por uma pessoa. Dez
  classificações bem pesquisadas é trabalho de dias, não de um ano.
- **Positivo:** mais defensável. Cada classificação com justificativa densa
  resiste a escrutínio melhor do que centenas espalhadas e rasas.
- **Positivo:** mais citável. Imprensa usa placar focado; índice abrangente com
  ressalvas ninguém cita.
- **Positivo:** desacopla o produto do painel de agentes
  (`docs/PRD-PAINEL.md`). O painel volta a ser ferramenta de escala para quando
  houver escala — não pré-requisito para existir.
- **Negativo:** a promessa da missão encolhe. O PRD dizia "saber em 30 segundos
  se seu deputado trabalha pela soberania industrial"; o placar responde isso
  **para as votações selecionadas**, não em geral. A diferença precisa estar
  visível na plataforma, não só aqui.
- **Negativo:** a seleção das ~10 votações passa a ser a decisão editorial mais
  carregada do projeto. Quem escolhe o que "mais importou" exerce um juízo que
  antes ficava diluído no volume. O critério de seleção precisa ser publicado
  junto com o resultado.

### Revogado por este ADR

- Métrica de sucesso "100% dos 513 deputados; 80%+ dos 81 senadores"
  (`docs/PRD.md`, `docs/ROADMAP.md`)
- "Parlamentares cobertos v1.0: 594" como restrição de produto
  (`.specify/memory/constitution.md`, *Key constraints* — registrado como fato,
  sem alterar a norma, pelo mesmo caminho da nota de 2026-09-17)
- "Ranking completo de parlamentares" como descrição do produto v1

### Deixado em aberto, deliberadamente

**O destino das 9 categorias ZIL.** Elas fazem sentido como taxonomia de um
índice; com ~10 votações, nove categorias viram nove baldes quase vazios. Podem
virar dois ou três eixos, ou serem substituídas por "a pauta desta votação".

Isso é uma decisão de produto que ainda não foi tomada, e alterá-las hoje
exigiria RFC com quórum inexistente (`docs/GOVERNANCE.md`). Fica registrado como
a **próxima** decisão, não como parte desta.

### Estado que este ADR não altera

As 7 classificações existentes continuam `validacao: nao-validado`. Este ADR
muda o alvo do produto, não a qualidade do dado atual — e o ranking segue fora
do ar (`NEXT_PUBLIC_RANKING_PUBLICO`, ver `docs/DEPLOY.md`) até que a curadoria
o sustente.

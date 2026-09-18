# ZIL Observatório — Governança v1

**Versão:** 1.2
**Última atualização:** 2026-09-18
**Escopo:** governança para a fase v1 — plataforma pública de leitura, sem
contas de usuário. Desde o [ADR-004](decisions/004-placar-focado.md), o produto
da v1 é um **placar focado em ~10 votações**, não um índice de todos os
parlamentares; as regras abaixo governam a curadoria desse placar.

> **Retificação (v1.1).** Este documento descrevia um processo de governança
> colegiada que nunca ocorreu. A v1.1 **não altera nenhuma regra** — mantém a
> norma como está e acrescenta o registro factual de que ela não é cumprida,
> mais o protocolo que de fato se aplica enquanto isso durar. Ver a seção
> seguinte.

---

## Estado atual da governança

**Data de apuração: 2026-09-17.** Esta seção registra fatos verificáveis no
próprio repositório, não intenções. Ela existe porque afirmar processo que não
acontece é representar algo falso a terceiros — e o Score ZIL só tem valor se a
alegação que o sustenta for verdadeira.

O documento distingue três tipos de frase, e nunca as mistura:

### 1. Norma (inalterada)

As regras deste documento continuam valendo como escritas. Dados editoriais
exigem 2 aprovações de maintainers; decisões arquiteturais, 2 aprovações; nova
categoria ZIL, aprovação de todos os maintainers ativos. **Nada disso foi
rebaixado.**

### 2. Fato: a norma não é cumprida

| Alegação | Realidade apurada |
|---|---|
| Maintainers: 2–5 pessoas | **1 pessoa.** A identidade `ZIL Observatório <zil@zilobservatorio.org>` no histórico git é a conta institucional da mesma maintainer, não uma segunda pessoa |
| Dados editoriais exigem 2 aprovações de maintainers distintos do proponente | **Nenhum PR do projeto (#1–#13) teve aprovação formal registrada.** Os commits que criaram `data/direcoes/` foram feitos direto em `main` |
| Proposta e discussão prévias no Discord | **O Discord ainda não existe** — está previsto e será criado, mas nenhuma discussão prévia aconteceu nele até hoje |
| "O histórico git de `data/` é o log de auditoria público" | O repositório é **privado**, com 0 watchers. O log existe e é íntegro, mas não é público |
| Enforcement técnico do processo | **Nenhum.** Não há CODEOWNERS, template de PR nem branch protection — esta última é indisponível em repositório privado no plano gratuito |

Isso vale desde a fundação do projeto (2026-03-31): não é uma degradação
recente, é a distância entre o documento e o mundo desde o primeiro dia.

### 3. Protocolo enquanto a norma não for cumprida

Não havendo segunda pessoa para revisar, não existe controle que produza
revisão independente. O que existe são obrigações que a maintainer única
assume sobre si mesma, e cuja observância fica registrada no repositório:

| # | Obrigação | Por quê |
|---|---|---|
| P1 | Justificativa escrita e específica em todo PR de dado editorial | Raciocínio auditável depois, mesmo sem revisor no momento |
| P2 | Separação temporal: não mergear dado editorial no mesmo dia em que a justificativa foi redigida | Reler a frio pega erro que a leitura no embalo não pega |
| P3 | Proveniência registrada por classificação: quem decidiu, quando, e o estado de validação | É o que permite a quem chegar depois saber o peso de cada entrada |
| P4 | Nenhuma alegação de colegialidade em documento, dado ou interface | Foi exatamente essa alegação que tornou necessária esta retificação |

**O que estas obrigações não são:** substituto de revisão independente. Elas
reduzem erro por descuido; não produzem contraditório. Enquanto houver uma
pessoa, o projeto não tem revisão editorial independente — e isso deve ser
declarado a quem lê a plataforma, não compensado com processo de aparência.

---

## Princípio central

> A v1 é gerenciada via código e PRs. Processos leves, decisões reversíveis, histórico auditável no git.

Complexidade de governança cresce com a plataforma. Em v1, não há usuários, não há curadoria comunitária e não há deliberação formal — portanto, não há necessidade de sistemas elaborados para essas camadas.

O que existe em v1, na prática: **código versionado + PRs + uma maintainer**.
O Discord ainda não existe (está previsto), e "rough consensus entre
maintainers" pressupõe um plural que não existe (ver "Estado atual da
governança").

---

## Papéis v1

### Maintainers

**Composição-alvo: 2–5 pessoas. Composição atual: 1.**

Responsáveis por tudo: código, dados editoriais, infraestrutura, decisões de produto.

**Responsabilidades:**
- Revisar e fazer merge de PRs (código e dados)
- Definir `direcao_esperada` de votações via YAML
- Atualizar indicadores da Bússola ZIL
- Gerenciar infraestrutura e deployments
- Moderar os canais públicos do projeto, quando existirem

**Como se torna maintainer:** convite de maintainer existente + aprovação unânime dos demais.

*Nota factual:* com uma única maintainer, "os demais" é conjunto vazio e a
cláusula é satisfeita trivialmente. Recrutar não está bloqueado por quórum —
está limitado por tempo e por não haver candidatos convidados até aqui.

### Comitê Editorial (subconjunto dos maintainers)

Em v1, o "comitê editorial" não é um órgão separado — é qualquer maintainer com contexto técnico suficiente para propor a `direcao_esperada` de uma votação específica.

A separação formal entre maintainers técnicos e comitê editorial ocorre em v2, quando a curadoria comunitária for implementada.

### Contribuidores

Qualquer pessoa que abre issues ou envia PRs de código ou dados. PRs de código
precisam de 1 aprovação de maintainer; PRs de dados editoriais, de 2 aprovações.

*Fato:* nenhuma dessas duas regras foi cumprida em nenhum PR do projeto até
2026-09-17. Contribuições externas de terceiros teriam, hoje, uma única
revisora — e isso deve ser dito a quem se dispuser a contribuir.

---

## Processo de decisão

### Decisões operacionais

**Rough consensus:** se nenhum maintainer objeta em 48h, a decisão é tomada.
Inclui: correções de bug, melhorias de UX, adição de keywords em categoria
existente, atualização de indicadores da Bússola.

*Fato:* com uma maintainer, "ninguém objetou" é vacuamente verdadeiro — a
regra não filtra nada. Enquanto durar, a decisão operacional é simplesmente
individual, e vale dizer isso em vez de manter a aparência de deliberação.

### Decisões de dados editoriais

**Norma.** Qualquer decisão que afeta o Score ZIL de parlamentares requer:

1. **Proposta pública** — issue no GitHub descrevendo a votação, a direção
   proposta e a justificativa técnica
2. **Discussão** — mínimo 24h; qualquer pessoa com acesso pode comentar
3. **Consenso** — 2 maintainers concordam explicitamente
4. **PR** — `data/direcoes/[ano].yml` com justificativa no body
5. **Merge** — 2 aprovações de maintainers diferentes da proposta original

**Fato.** Os passos 1, 2, 3 e 5 nunca foram executados. As 7 direções que hoje
produzem 100% do Score ZIL foram criadas num único commit em 2026-04-02, direto
em `main`, por uma pessoa — e estão marcadas `validacao: nao-validado` nos
próprios arquivos.

**Enquanto houver uma maintainer**, o que se aplica são as obrigações P1–P4 da
seção "Estado atual da governança": justificativa escrita, separação temporal,
proveniência registrada e nenhuma alegação de colegialidade. O passo 1 continua
sendo feito como issue pública **quando houver a quem se dirigir**; em
repositório privado, uma issue é registro datado, não escrutínio, e não deve ser
apresentada como se fosse.

**Princípio operacional: na dúvida, não classificar.** É melhor um score baseado em menos votações do que incluir uma votação com direção genuinamente controversa.

### Decisões arquiteturais

Mudanças de stack, novos serviços, mudanças de schema: abertas como issues com
label `arch-decision`, discussão por ≥ 72h, merge com 2 aprovações. Registradas
em `docs/decisions/` como ADRs.

*Fato:* o quórum de 2 não é atingível hoje; o registro em ADR é, e é o que se
exige na prática.

### Mudanças nas categorias ZIL

As 9 categorias são imutáveis sem RFC. Para nova categoria, renomeação ou remoção:

1. RFC pública como issue no GitHub por ≥ 7 dias
2. Aprovação de todos os maintainers ativos — *nota: com uma maintainer, esta
   cláusula é satisfeita trivialmente e não representa revisão alguma*
4. Registro em `docs/decisions/`

---

## Gestão editorial via código

### Estrutura de arquivos

```
data/
├── taxonomia/
│   └── categorias.yml         # keywords por categoria ZIL
├── direcoes/
│   ├── 2024.yml               # direcao_esperada por votacao
│   ├── 2025.yml
│   └── 2026.yml
└── bussula/
    └── marcos.yml             # indicadores estratégicos
```

### Como definir a direção esperada de uma votação

1. Identifique a votação pelo `fonte_id` e `fonte`
2. Abra uma issue pública com a justificativa técnica
3. Adicione ao YAML (a norma pede consenso prévio; ver "Estado atual"):

```yaml
# data/direcoes/2024.yml
- fonte_id: "12345"
  fonte: camara
  direcao: sim          # "sim" = votar SIM é pró-soberania
  peso: 3.0
  validacao: nao-validado   # nao-validado | revisado-por-<handle>
  justificativa: >
    PL 1234/2024 exige processamento local de nióbio antes de exportação.
    Votar sim é pró-soberania (ZIL-MIN).
  categoria_principal: ZIL-MIN
```

**Não escreva "consenso editorial" na justificativa.** A justificativa registra o
raciocínio sobre a votação; quem decidiu e sob qual revisão é o que o campo
`validacao` e o histórico git registram. Afirmar consenso onde houve uma pessoa
foi exatamente o problema que a v1.1 deste documento retificou.

4. Aplique ao banco: `python scripts/apply_direcoes.py`
5. Scores recalculados automaticamente na próxima execução do scoring engine

### Transparência e auditabilidade

- Todo PR de dados editoriais deve ter justificativa em português
- O histórico git de `data/` é o log de auditoria — **íntegro, mas não público
  enquanto o repositório for privado.** A frase anterior dizia "log de auditoria
  público", o que não é verdade hoje
- Decisões são registradas como PR ou ADR, nunca só em conversa
- Nenhuma classificação é irreversível: `git log -- data/direcoes/` mostra quem
  mudou o quê. *Ressalva:* os commits de `data/` estão assinados pela identidade
  institucional `ZIL Observatório`, não por pessoa física — o log responde
  "quando" e "o quê" melhor do que "quem"

---

## Canais de comunicação v1

| Canal | Propósito | Existe hoje? |
|-------|-----------|--------------|
| GitHub Issues | Discussões editoriais e técnicas, propostas de classificação | Sim — mas privadas, enquanto o repositório for privado |
| GitHub PRs | Revisão de código e dados | Sim |
| `docs/decisions/` | Registro permanente de ADRs | Sim |
| Discord | Conversa em tempo real, dúvidas, coordenação | **Ainda não.** Será criado; o convite será publicado aqui e no `CONTRIBUTING.md` assim que existir. Versões anteriores deste documento o tratavam como canal obrigatório sem que ele existisse |

---

## Condições para a norma voltar a ser cumprida

Esta seção existe para que o estado atual não se torne permanente por inércia, e
para que a saída dele não seja gamificável.

**A norma volta a ser cumprida quando houver um segundo maintainer ativo.**
"Ativo" não é contagem de nomes: nomear alguém nominalmente não restabelece
revisão nenhuma, e um documento que aceitasse isso estaria criando a próxima
regra de papel. O teste é comportamental:

> Um segundo maintainer é considerado ativo quando tiver registrado revisão em
> pelo menos 3 PRs, das quais ao menos 1 com pedido de alteração. Revisão que
> apenas aprova não demonstra contraditório.

**Não há prazo nem compromisso de recrutamento.** Esta seção descreve a
condição, não promete cumpri-la — foi a promessa sem lastro que criou o
problema que a v1.1 retifica.

### Como participar, e o que muda quando houver gente

Quem quiser contribuir hoje tem dois caminhos, ambos funcionando:

- **GitHub Issues** — propostas de classificação, dúvidas, discussão técnica.
  É onde fica o registro.
- **Discord** — será o canal de conversa em tempo real. **Ainda não existe**;
  o convite será publicado aqui e no [CONTRIBUTING.md](../CONTRIBUTING.md)
  assim que for criado.

**As regras deste documento não são definitivas.** Elas foram escritas por uma
pessoa, para um projeto de uma pessoa — o que é uma limitação, não uma virtude.

Quando houver um grupo de contribuidores ativos, **as diretrizes e regras
passam a ser revistas em conjunto**: quórum para dados editoriais, formato e
periodicidade de reuniões, critério de seleção das votações do placar, e a
própria forma de decidir. Nada disso está fechado, e quem chegar cedo participa
de defini-lo em vez de herdá-lo pronto.

O que **não** muda por deliberação: os princípios da
[constituição](../.specify/memory/constitution.md) — dados públicos,
apartidarismo, transparência radical. Esses têm rito próprio de emenda, e
existem justamente para não dependerem de quem está na sala.

### Limitação enquanto o repositório for privado

Vários controles de governança que este documento poderia adotar são
tecnicamente indisponíveis hoje:

- **Branch protection** e **CODEOWNERS** exigem repositório público no plano
  gratuito (a API retorna 403)
- **Escrutínio externo** — qualquer mecanismo do tipo "janela para terceiros
  objetarem" pressupõe terceiros com acesso de leitura. Não há

Consequência a registrar: enquanto o repositório for privado e a plataforma não
estiver no ar, **nenhum controle de revisão externa é possível**, e nenhum
documento deste projeto deve prometer um. Abrir o repositório destravaria os
três itens acima de uma vez.

---

## Governança v2+ (visão)

Quando a plataforma tiver usuários, a governança evoluirá para incluir:

- **Comitê Editorial formal** (5–9 pessoas, mandato 12 meses, diversidade regional e técnica)
- **Sistema de contestação** (usuários propõem reclassificações, comitê decide)
- **RFCs com votação pública** para mudanças significativas
- **Deliberação Polis** para decisões estratégicas (ao estilo vTaiwan — identifica consenso transversal entre grupos politicamente opostos)
- **Rotação obrigatória** de mantainers e comitê editorial

Ver [docs/ROADMAP.md](ROADMAP.md) para cronograma.

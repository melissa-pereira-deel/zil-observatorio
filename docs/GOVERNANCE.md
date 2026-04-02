# ZIL Observatório — Governança v1

**Versão:** 1.0
**Última atualização:** 2026-04-02
**Escopo:** governança para a fase v1 (plataforma pública de leitura, sem contas de usuário)

---

## Princípio central

> A v1 é gerenciada por maintainers via código e Discord. Processos leves, decisões reversíveis, histórico auditável no git.

Complexidade de governança cresce com a plataforma. Em v1, não há usuários, não há curadoria comunitária e não há deliberação formal — portanto, não há necessidade de sistemas elaborados para essas camadas.

O que existe em v1: **código aberto + PRs + Discord + rough consensus entre maintainers**.

---

## Papéis v1

### Maintainers (2–5 pessoas)

Responsáveis por tudo: código, dados editoriais, infraestrutura, decisões de produto.

**Responsabilidades:**
- Revisar e fazer merge de PRs (código e dados)
- Definir `direcao_esperada` de votações via YAML
- Atualizar indicadores da Bússola ZIL
- Gerenciar infraestrutura e deployments
- Moderar o Discord

**Como se torna maintainer:** convite de maintainer existente + aprovação unânime dos demais.

### Comitê Editorial (subconjunto dos maintainers)

Em v1, o "comitê editorial" não é um órgão separado — é qualquer maintainer com contexto técnico suficiente para propor a `direcao_esperada` de uma votação específica.

A separação formal entre maintainers técnicos e comitê editorial ocorre em v2, quando a curadoria comunitária for implementada.

### Contribuidores

Qualquer pessoa que abre issues, envia PRs de código ou dados, ou participa do Discord. PRs de código precisam de 1 aprovação de maintainer. PRs de dados editoriais precisam de 2 aprovações.

---

## Processo de decisão

### Decisões operacionais

**Rough consensus:** se nenhum maintainer objeta no Discord em 48h, a decisão é tomada. Inclui: correções de bug, melhorias de UX, adição de keywords em categoria existente, atualização de indicadores da Bússola.

### Decisões de dados editoriais

Qualquer decisão que afeta o Score ZIL de parlamentares requer:

1. **Proposta no Discord** — descrever a votação, a direção proposta, a justificativa técnica
2. **Discussão** — mínimo 24h; qualquer pessoa pode comentar
3. **Consenso** — 2 maintainers concordam explicitamente
4. **PR** — `data/direcoes/[ano].yml` com justificativa no body
5. **Merge** — 2 aprovações de maintainers diferentes da proposta original

**Princípio operacional: na dúvida, não classificar.** É melhor um score baseado em menos votações do que incluir uma votação com direção genuinamente controversa.

### Decisões arquiteturais

Mudanças de stack, novos serviços, mudanças de schema: abertas como issues com label `arch-decision`, discussão no Discord por ≥ 72h, merge com 2 aprovações. Registradas em `docs/decisions/` como ADRs.

### Mudanças nas categorias ZIL

As 9 categorias são imutáveis sem RFC. Para nova categoria, renomeação ou remoção:

1. RFC pública como issue no GitHub por ≥ 7 dias
2. Notificação no Discord
3. Aprovação de todos os maintainers ativos
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
2. Proponha no Discord com justificativa técnica
3. Após consenso, adicione ao YAML:

```yaml
# data/direcoes/2024.yml
- fonte_id: "12345"
  fonte: camara
  direcao: sim          # "sim" = votar SIM é pró-soberania
  peso: 3.0
  justificativa: >
    PL 1234/2024 exige processamento local de nióbio antes de exportação.
    Votar sim é pró-soberania (ZIL-MIN). Consenso editorial em 2026-04-01.
  categoria_principal: ZIL-MIN
```

4. Aplique ao banco: `python scripts/apply_direcoes.py`
5. Scores recalculados automaticamente na próxima execução do scoring engine

### Transparência e auditabilidade

- Todo PR de dados editoriais deve ter justificativa em português
- O histórico git de `data/` é o log de auditoria público
- Decisões tomadas no Discord são registradas como PR ou ADR
- Nenhuma classificação é irreversível: `git log -- data/direcoes/` mostra quem mudou o quê

---

## Canais de comunicação v1

| Canal | Propósito |
|-------|-----------|
| Discord | Discussões editoriais, decisões operacionais, coordenação |
| GitHub Issues | Bugs, features, discussões técnicas públicas |
| GitHub PRs | Revisão de código e dados |
| `docs/decisions/` | Registro permanente de ADRs |

---

## Governança v2+ (visão)

Quando a plataforma tiver usuários, a governança evoluirá para incluir:

- **Comitê Editorial formal** (5–9 pessoas, mandato 12 meses, diversidade regional e técnica)
- **Sistema de contestação** (usuários propõem reclassificações, comitê decide)
- **RFCs com votação pública** para mudanças significativas
- **Deliberação Polis** para decisões estratégicas (ao estilo vTaiwan — identifica consenso transversal entre grupos politicamente opostos)
- **Rotação obrigatória** de mantainers e comitê editorial

Ver [docs/ROADMAP.md](ROADMAP.md) para cronograma.

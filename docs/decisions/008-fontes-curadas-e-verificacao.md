# ADR-008: Fontes externas curadas e verificação de alegações

**Data:** 2026-10-22
**Status:** Proposto — vira Aceito depois da calibração com chamada real (Fase C)

## Contexto

Os pipelines de agentes liam três hosts: Câmara, Senado e Planalto. O slot
`contexto_economico`, que o economista declara como insumo, nunca foi
preenchido. Quando ele perguntava "quem paga e por quanto tempo", respondia
de memória do modelo, a única fonte que não dá para auditar.

O pedido foi dar a alguns agentes acesso a fontes curadas (Selic, juros,
população, transparência), com checagem de fatos, cruzamento de dados e
redução de viés de avaliação.

O risco central: dar uma ferramenta a um agente é dar a ele a **escolha do
que buscar**. Escolha de busca é o vetor de viés mais silencioso que existe.
Um economista ortodoxo-cético com acesso livre a séries acha a série que
confirma a leitura dele. Uma allowlist de hosts impede fonte duvidosa, mas
não impede escolha enviesada entre fontes boas.

## Decisão

1. **Allowlist como dado editorial.** `data/fontes/catalogo.yml` lista as
   fontes, sob a governança de `data/`. Toda fonte declara `natureza` e
   `vies_declarado`, porque "oficial" não é "neutro". Toda fonte diz se é
   `primaria`; secundária nunca conta como evidência independente.
2. **A allowlist é aplicada na rede.** O transporte do httpx recusa qualquer
   host fora do catálogo antes de a requisição sair. Inclui redirects.
3. **Contexto pré-registrado, sem ferramenta.** `data/fontes/planos/por_tema.yml`
   decide antes de qualquer consulta quais séries entram, por tema. Todas as
   lentes recebem o mesmo bloco. Os valores são os já publicados na data de
   apresentação da proposição. Nenhuma lente busca nada.
4. **Um agente, uma ferramenta, uma etapa.** Só o `verificador` usa
   ferramenta, e só `consultar_serie`. Ele recebe uma alegação sem saber de
   quem é, e só pode consultar as séries que o código resolveu como
   candidatas. O resto é recusado e registrado.
5. **Extração cega e simétrica.** Afirmações de todas as lentes e parágrafos
   da justificação entram no mesmo saco, com ids opacos, embaralhados por
   hash do conteúdo. O mesmo critério vale para todos.
6. **A conta vale mais que o julgamento.** Para alegação numérica, o
   veredito sai da comparação entre o valor alegado e a observação que o
   harness consultou. Se o modelo discordar, prevalece a conta e a
   divergência fica registrada. Número que o código não viu não é confirmado.
7. **Fato não é interpretação.** Alegação causal não chega ao verificador.
   Fica como `nao_verificavel_por_dado` e continua no texto como argumento.
8. **Contradição sobrevive.** A síntese tem de citar toda alegação
   contradita como contradita, e o número contradito não entra no resumo
   didático. Contradita e fontes divergentes vão para uma fila humana.
9. **Nenhum número sem origem.** Todo número dos textos finais tem de estar
   no texto, na ficha, no contexto ou nas verificações. A instrução "não
   traga de memória" sozinha não vale nada; esta conta é o que a torna
   verificável.

## Consequências

- **"Verificado" é atributo de cada número, nunca selo da explicação.** A
  maior parte das alegações legislativas é causal e não tem série que a
  teste. A fração de alegações verificáveis é medida e deve ser publicada.
- **Custo.** A v2 soma uma chamada de extração e até 12 conversas de
  verificação por proposição, cada uma com até 6 rodadas. Medir na Fase C.
- **Cobertura estreita, de propósito.** Habilitadas: BCB SGS, IBGE e IPEA,
  verificadas com consulta real em 2026-10-21. Tesouro/SICONFI, Comex Stat e
  Portal da Transparência ficam catalogados e desabilitados até terem
  adaptador. Alegação sem série vira `sem_fonte_curada`, nunca palpite.
- **Vintage é aproximado.** As APIs devolvem o valor publicado hoje, não o
  vigente na época. Série revisável ganha tolerância maior e um aviso.
- **v1 continua existindo** para comparação lado a lado com a v2.

## Fora de escopo

Busca na web; URL livre; ferramenta para as lentes; agregadores de terceiros
como fonte; verificar alegação causal com dado. Qualquer um desses exige
novo ADR.

## Critério de go/no-go (Fase C)

| # | Métrica | Meta |
|---|---|---|
| 10 | Números sem origem na saída | 0 |
| 11 | Alegações plantadas detectadas nos casos construídos | 100% |
| 12 | Taxa de contradição por origem, lote de 30 | sem assimetria acima de 2× |
| 13 | Fração de alegações verificáveis | registrada e publicada |
| 14 | Recusas da ferramenta | registradas; acima de 0 em produção pede inspeção |
| 15 | Mesmo `contexto_hash` → mesmos números | 100% |

Código: `apps/workers/fontes/`, `apps/workers/explicacao/verificacao.py`,
`apps/workers/agentes/fronteira.py`. Testes: `tests/unit/test_fontes.py`,
`tests/unit/test_verificacao.py`.

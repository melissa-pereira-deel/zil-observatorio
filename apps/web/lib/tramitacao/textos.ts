import { especieConhecida, nomeEspeciePlural } from "./especies";

/**
 * Textos de interface da tramitação: a coluna "textos.ts" da matriz em
 * specs/013-tramitacao/backlog-interface.md §4. Mudança de texto começa na §4,
 * no mesmo PR. Fase e desfecho não moram aqui: vêm prontos da API.
 */

const NOVA_ABA = "(abre em nova aba)";
const TENTAR_DE_NOVO = "Tentar de novo";
const NAO_SABEMOS = "Não sabemos em que fase está";
// A API copia este texto como `fase_rotulo`; um teste de TRM-028 confere a igualdade.
const FASE_NAO_IDENTIFICADA = "Fase não identificada";
const LIMPAR_FILTROS = "Limpar filtros";
const ANDAM_JUNTAS = (rotulo: string) =>
  `${rotulo} é a proposição principal. As duas andam juntas e recebem um parecer só; por isso, a fase mostrada aqui é a da principal.`;
const CHAPEU_COMO_FUNCIONA = "Como funciona";
const TEXTO_NAO_OFICIAL = "Texto do ZIL, não oficial";

export const TEXTOS = {
  I03: {
    titulo: "Não foi possível carregar a proposição",
    corpo: "A API não respondeu. Confira a conexão e tente de novo em instantes.",
    acao: TENTAR_DE_NOVO,
  },
  I04: "Carregando a tramitação",
  I05: {
    titulo: "Não conseguimos carregar a fase agora",
    corpo: "Abaixo está a situação oficial da Câmara, que vem de outra consulta.",
    acao: TENTAR_DE_NOVO,
  },
  I07: {
    tituloCaminho: "Não conseguimos carregar o caminho agora",
    tituloExplicacoes: "Não conseguimos carregar as explicações agora",
    corpo: "Tente de novo em instantes. A situação oficial de cada proposição continua disponível.",
    acao: TENTAR_DE_NOVO,
  },
  I10: {
    titulo: "A lista está incompleta",
    corpo: (d: { n: number }) =>
      `Carregamos ${d.n} proposições, mas a API não respondeu ao pedir o resto. A contagem e os filtros consideram só essas.`,
    acao: TENTAR_DE_NOVO,
  },
  I12: {
    semFase: {
      titulo: "Nenhuma proposição com esses filtros",
      corpo: "Tente outra pauta, tipo ou ano, ou busque por outro termo.",
      acao: LIMPAR_FILTROS,
    },
    comFase: {
      titulo: "Nenhuma proposição nesta fase com esses filtros",
      corpo: "Tente outra fase, pauta, tipo ou ano.",
      acao: LIMPAR_FILTROS,
    },
  },
  I15: "Ainda não identificamos marcos nesta tramitação. Os registros completos da Câmara estão logo abaixo.",
  I16: "A Câmara ainda não registrou movimentações desta proposição.",

  F02: {
    pagina: "Ainda não informada pela Câmara.",
    paginaRecem: (d: { dataApresentacao: string }) => `Recém-apresentada, em ${d.dataApresentacao}.`,
    lista: "Situação na Câmara: ainda não informada.",
  },
  F03: {
    pagina: "Ainda não informada pela Câmara.",
    lista: "Situação na Câmara: ainda não informada.",
  },
  F13: {
    pagina: "Ainda não conferimos a situação desta proposição na Câmara.",
    lista: "Situação na Câmara: ainda não conferida.",
  },
  F04: {
    linha: (d: { prefixo: string; rotulo: string }) => `${d.prefixo}: ${d.rotulo}`,
    vetoParcial: "Sancionada com veto parcial: partes do texto foram vetadas pelo Presidente da República.",
    lerNormasLeg: "Ler o texto no normas.leg.br",
    lerPlanalto: "Ler o texto no Planalto",
    leitor: NOVA_ABA,
  },
  F05: "A Câmara registra que esta proposição virou norma, mas o número não aparece no despacho. Confira no site da Câmara.",
  F06: {
    dt: "Regime e quem decide",
    dd: "Ainda não definidos. São fixados no despacho que distribui a proposição às comissões.",
  },
  F09: (d: { data: string }) => `Conferido na Câmara em ${d.data}`,
  F11: {
    dt: "Tramita junto com",
    link: "Ver a proposição principal na Câmara",
    leitor: NOVA_ABA,
  },
  X01: {
    visivel: "Ver na Câmara",
    leitor: (d: { rotulo: string }) => ` o ${d.rotulo} ${NOVA_ABA}`,
  },

  L02: (d: { movimentacao: string | null; apresentada: string | null }): string | null => {
    const partes = [
      d.movimentacao && `Última movimentação em ${d.movimentacao}`,
      d.apresentada && `Apresentada em ${d.apresentada}`,
    ].filter(Boolean);
    return partes.length > 0 ? partes.join(" · ") : null;
  },
  L03: {
    vazio: "Ordenar",
    movimentacao: "Movimentação mais recente",
    apresentacaoRecente: "Apresentação mais recente",
    apresentacaoAntiga: "Apresentação mais antiga",
  },
  // "As existentes" da §4: singular e "de {total}" são os de app/proposicoes/page.tsx.
  L04: (d: {
    n: number;
    de?: number | null;
    analise?: "analisada" | "pendente" | null;
    faseChip?: string | null;
  }) => {
    const um = d.n === 1;
    const total = d.de == null ? "" : ` de ${d.de}`;
    const analise =
      d.analise === "analisada" ? (um ? " analisada" : " analisadas") : d.analise === "pendente" ? " sem análise" : "";
    const fase = d.faseChip ? ` — fase: ${d.faseChip}` : "";
    return `${d.n}${total} ${um ? "proposição" : "proposições"}${analise}${fase}`;
  },
  L05: {
    grupoPauta: "Pauta",
    grupoFase: "Fase",
    fases: {
      todas: "Todas",
      apresentada: "Apresentadas",
      comissoes: "Nas comissões",
      plenario: "No Plenário",
      outra_casa: "Na outra Casa",
      retorno: "De volta à Casa de origem",
      sancao: "Com o Presidente da República",
      veto_congresso: "Veto em análise",
      promulgacao: "Aguardando promulgação",
      norma: "Viraram norma",
      encerradas: "Encerradas",
      nao_identificada: FASE_NAO_IDENTIFICADA,
    },
    casa: {
      camara: "Começou na Câmara",
      senado: "Começou no Senado",
    },
  },
  L06: "Como uma proposição vira lei",

  R01: "Ainda não informada pela Câmara.",

  A01: {
    titulo: (d: { principalComArtigo: string }) => `Tramita junto com ${d.principalComArtigo}`,
    corpo: (d: { rotulo: string }) => ANDAM_JUNTAS(d.rotulo),
    acao: "Ver a proposição principal",
  },
  A02: {
    titulo: (d: { principalComArtigo: string }) => `Tramita junto com ${d.principalComArtigo}`,
    corpo: (d: { rotulo: string }) => ANDAM_JUNTAS(d.rotulo),
    acao: "Ver a proposição principal na Câmara",
    leitor: NOVA_ABA,
  },

  N00: FASE_NAO_IDENTIFICADA,
  N01: {
    titulo: NAO_SABEMOS,
    corpo: (d: { situacao: string | null; versaoPublicada: number | null }) => {
      const versao = d.versaoPublicada == null ? "" : ` (versão ${d.versaoPublicada})`;
      const inicio = d.situacao
        ? `A situação oficial na Câmara, “${d.situacao}”, ainda`
        : "A situação oficial desta proposição ainda";
      return `${inicio} não está no nosso mapa de fases${versao}. Preferimos não adivinhar.`;
    },
  },
  // Sem variante para situação nula na §4, por isso `situacao` é obrigatória.
  N02: {
    titulo: NAO_SABEMOS,
    corpo: (d: { situacao: string }) =>
      `A situação oficial na Câmara, “${d.situacao}”, e o último despacho não batem entre si. Preferimos não adivinhar: confira o andamento no site da Câmara.`,
  },
  N03: {
    titulo: NAO_SABEMOS,
    corpo: "Esta proposição tramita junto com outra, e a fase dela é a da principal. Não conseguimos identificar a principal nos dados da Câmara.",
  },
  N04: {
    titulo: NAO_SABEMOS,
    corpo: (d: { conferidoEm: string | null }) => {
      const quando = d.conferidoEm ? `, em ${d.conferidoEm}` : "";
      return `Os dados da Câmara não bastam para saber: a situação oficial não foi informada, ou a Câmara não respondeu quando conferimos${quando}. Confira o andamento no site da Câmara.`;
    },
  },
  // Recebe o tipo, e não {especie_plural}: "proposições" do genérico daria
  // "as fases de proposições" no lugar da variante "deste tipo de proposição".
  N05: {
    titulo: NAO_SABEMOS,
    corpo: (d: { tipo: string | null }) =>
      `O ZIL ainda não acompanha as fases ${
        especieConhecida(d.tipo) ? `de ${nomeEspeciePlural(d.tipo)}` : "deste tipo de proposição"
      }.`,
  },
  N06: {
    titulo: "Fase em revisão",
    corpo: "A explicação desta situação ainda está em revisão e só vai ao ar depois de aprovada. Enquanto isso, mostramos a situação oficial da Câmara.",
  },

  T01: "O ZIL não estima quando a proposição vai avançar: isso depende de quem conduz esta etapa.",

  C01: "A fase é uma leitura do ZIL a partir dos dados oficiais; a situação oficial é o texto da Câmara, sem edição.",
  C01_SAIBA_MAIS: "Como chegamos a esta fase",
  C01_FONTE_REGRAS: "Regras do mapa de fases — data/tramitacao/fases.yml",
  C03: "Sem fonte registrada para esta leitura.",

  M01: "Em ordem cronológica",
  M02: {
    fonte: "No texto original da Câmara dos Deputados, do mais recente para o mais antigo",
  },
  M03: (d: { n: number }) => (d.n === 1 ? "Ver o marco anterior" : `Ver os ${d.n} marcos anteriores`),

  K00: {
    intro: (d: { especieIndefinida: string; casa: "camara" | "senado" }) =>
      `O caminho de ${d.especieIndefinida} que começa ${d.casa === "camara" ? "na Câmara" : "no Senado"}. A etapa atual aparece marcada.`,
    introMpv: "O caminho de uma medida provisória. A etapa atual aparece marcada.",
    recolhivel: (d: { n: number }) => `Ver as ${d.n} etapas, com o que acontece em cada uma`,
    botao: "Entender como uma proposição vira lei",
  },
  K01: {
    texto: (d: { especiePlural: string }) =>
      `O caminho de ${d.especiePlural} ainda está em revisão e só aparece depois de aprovado.`,
    link: "Como uma proposição vira lei",
  },
  K02: (d: { especiePlural: string }) => `Ainda não descrevemos o caminho de ${d.especiePlural}.`,
  K03: "Não sabemos em que etapa esta proposição está. O caminho abaixo é o da espécie, sem marcação.",

  V01: {
    chapeu: CHAPEU_COMO_FUNCIONA,
    h1: "Como uma proposição vira lei",
    linhaFina: "O caminho de uma proposição no Congresso: quem decide cada passo, o que diz a regra e onde ela pode parar.",
    aviso: {
      titulo: TEXTO_NAO_OFICIAL,
      corpo: (d: { versaoPublicada: number | null }) => {
        const versao = d.versaoPublicada == null ? "" : ` Mapa de fases versão ${d.versaoPublicada}.`;
        return `Escrito a partir da Constituição e dos regimentos da Câmara e do Senado. Cada etapa cita a regra.${versao}`;
      },
    },
    grupoTipo: "Tipo de proposição",
    grupoComeca: "Começa",
    chips: {
      PL: "Lei (PL)",
      PLP: "Lei complementar (PLP)",
      PEC: "Emenda à Constituição (PEC)",
      MPV: "Medida provisória (MPV)",
      PDL: "Decreto legislativo (PDL)",
      camara: "Na Câmara",
      senado: "No Senado",
    },
    rotuloExtra: "Como a Câmara chama esta etapa",
    h2: {
      caminho: "O caminho",
      outrasSituacoes: "Outras situações da Câmara",
      ondePodeParar: "Onde uma proposição pode parar",
      emConjunto: "Tramitação em conjunto",
      depoisDaLei: "Depois que vira lei",
      comoMontamos: "Como montamos este mapa",
    },
    depoisDaLei: "O ZIL ainda não acompanha a regulamentação das leis.",
    mapa: {
      texto: "Este mapa é do ZIL e é revisado antes de ir ao ar. Como fazemos: Metodologia.",
      linkGithub: "Ver o mapa no GitHub",
      linkSituacoes: "O que quer dizer cada situação",
    },
  },
  V02: {
    chapeu: CHAPEU_COMO_FUNCIONA,
    h1: "Esta página ainda está em revisão",
    corpo: "O mapa das etapas é escrito pelo ZIL e só vai ao ar depois de revisado. Enquanto isso, cada proposição mostra a situação oficial da Câmara, como a Câmara escreve.",
    botaoProposicoes: "Ver proposições",
    botaoMetodologia: "Como o ZIL trabalha",
  },

  S01: {
    chapeu: CHAPEU_COMO_FUNCIONA,
    h1: "O que quer dizer cada situação",
    linhaFina: "A Câmara descreve o andamento de cada proposição com termos do regimento. Aqui está o que cada um quer dizer, em linguagem simples.",
    cobertura: (d: { a: number; t: number }) => `${d.a} de ${d.t} situações da Câmara já têm explicação`,
    aviso: {
      titulo: TEXTO_NAO_OFICIAL,
      corpo: "A situação oficial aparece exatamente como a Câmara escreve. A explicação é do ZIL e só vai ao ar depois de revisada.",
    },
    busca: {
      rotulo: "Buscar situação ou termo",
      placeholder: "Buscar, por exemplo, “Pronta para Pauta”",
    },
    h2: {
      situacoes: "Situações na Câmara",
      regimes: "Regimes de tramitação",
      quemDecide: "Quem decide: comissões ou Plenário",
    },
    chips: {
      situacoes: "Situações",
      regimes: "Regimes",
      quemDecide: "Quem decide",
    },
    recolhivel: (d: { n: number }) => `Ver as ${d.n} situações ainda sem explicação`,
  },
  S02: (d: { n: number }) => (d.n === 1 ? "1 resultado" : `${d.n} resultados`),
  S03: {
    texto: (d: { busca: string }) => `Nenhuma situação ou termo com “${d.busca}”.`,
    acao: "Limpar busca",
  },
} as const;

/**
 * IDs da §4 com fonte textos.ts, mais as duas chaves extras de C01. Duplica a
 * spec de propósito: é com esta lista que o teste compara as chaves de TEXTOS.
 */
export const IDS_MATRIZ = [
  "I03", "I04", "I05", "I07", "I10", "I12", "I15", "I16",
  "F02", "F03", "F13", "F04", "F05", "F06", "F09", "F11",
  "X01",
  "L02", "L03", "L04", "L05", "L06",
  "R01",
  "A01", "A02",
  "N00", "N01", "N02", "N03", "N04", "N05", "N06",
  "T01",
  "C01", "C01_SAIBA_MAIS", "C01_FONTE_REGRAS", "C03",
  "M01", "M02", "M03",
  "K00", "K01", "K02", "K03",
  "V01", "V02",
  "S01", "S02", "S03",
] as const satisfies readonly (keyof typeof TEXTOS)[];

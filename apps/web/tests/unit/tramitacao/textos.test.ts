import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { REGRAS_ESTILO } from "@/lib/tramitacao/estilo";
import { IDS_MATRIZ, TEXTOS } from "@/lib/tramitacao/textos";

const SPEC = resolve(__dirname, "../../../../../specs/013-tramitacao/backlog-interface.md");

type LinhaDaMatriz = { fonte: string; selo: string; texto: string };

/** Linhas da tabela de §4, por ID, com as células que os testes leem. */
function matriz(): Record<string, LinhaDaMatriz> {
  const secao = readFileSync(SPEC, "utf8").split("## 4. Matriz de estados e textos")[1].split("\n## 5.")[0];
  const linhas: Record<string, LinhaDaMatriz> = {};
  for (const linha of secao.split("\n")) {
    const id = /^\| ([A-Z]\d+[a-z]?) \|/.exec(linha)?.[1];
    if (!id) continue;
    const celulas = linha.split(/(?<!\\)\|/).map((c) => c.trim());
    linhas[id] = { selo: celulas[3], texto: celulas[4], fonte: celulas[7] };
  }
  return linhas;
}

/** Os trechos entre aspas retas de uma célula, na ordem. As curvas fazem parte do texto. */
const trechos = (celula: string) => Array.from(celula.matchAll(/"([^"]*)"/g)).map((t) => t[1]);

type Args = Record<string, unknown>;
type Texto = { caminho: string; texto: string };

// O argumento de cada caso é o próprio marcador da §4 ("{data}"): a saída se
// compara direto com a linha da matriz e depois recebe o valor de exemplo.
const m = (marcador: string) => marcador as never;

const CASOS: Record<string, Args[]> = {
  "I10.corpo": [{ n: m("{n}") }],
  "F02.paginaRecem": [{ dataApresentacao: m("{data_apresentacao}") }],
  "F04.linha": [
    { prefixo: m("{prefixo}"), rotulo: m("{norma.rotulo}") },
    { prefixo: null, rotulo: m("{norma.rotulo}") },
  ],
  F09: [{ data: m("{data}") }],
  "X01.leitor": [{ rotulo: m("{rotulo}") }],
  L02: [
    { movimentacao: m("{data}"), apresentada: m("{data}") },
    { movimentacao: m("{data}"), apresentada: null },
    { movimentacao: null, apresentada: m("{data}") },
  ],
  L04: [
    { n: m("{n}") },
    { n: 1 },
    { n: m("{n}"), analise: "analisada" },
    { n: 1, analise: "analisada" },
    { n: m("{n}"), analise: "pendente" },
    { n: m("{n}"), de: 130 },
    { n: m("{n}"), faseChip: m("{rótulo do chip}") },
  ],
  "A01.titulo": [{ principalComArtigo: m("{principal_com_artigo}") }],
  "A01.corpo": [{ rotulo: m("{herdada_de.rotulo}") }],
  "A02.titulo": [{ principalComArtigo: m("{principal_com_artigo}") }],
  "A02.corpo": [{ rotulo: m("{herdada_de.rotulo}") }],
  "N01.corpo": [
    { situacao: m("{situacao}"), versaoPublicada: m("{versao_publicada}") },
    { situacao: null, versaoPublicada: m("{versao_publicada}") },
    { situacao: m("{situacao}"), versaoPublicada: null },
    { situacao: null, versaoPublicada: null },
  ],
  "N02.corpo": [{ situacao: m("{situacao}") }],
  "N04.corpo": [{ conferidoEm: m("{conferido_em}") }, { conferidoEm: null }],
  "N05.corpo": [{ tipo: "PLP" }, { tipo: "REQ" }, { tipo: null }],
  M03: [{ n: m("{n}") }, { n: 1 }],
  "K00.intro": [
    { especieIndefinida: m("{especie_indefinida}"), casa: "camara" },
    { especieIndefinida: m("{especie_indefinida}"), casa: "senado" },
  ],
  "K00.recolhivel": [{ n: m("{n}") }],
  "K01.texto": [{ especiePlural: m("{especie_plural}") }],
  K02: [{ especiePlural: m("{especie_plural}") }],
  "V01.aviso.corpo": [{ versaoPublicada: m("{versao_publicada}") }, { versaoPublicada: null }],
  "S01.cobertura": [{ a: m("{a}"), t: m("{t}") }],
  "S01.recolhivel": [{ n: m("{n}") }],
  S02: [{ n: m("{n}") }, { n: 1 }],
  "S03.texto": [{ busca: m("{busca}") }],
};

const DATA_EXEMPLO = "30/10/2026";
const EXEMPLOS: Record<string, string> = {
  "{n}": "12",
  "{a}": "40",
  "{t}": "99",
  "{data}": DATA_EXEMPLO,
  "{data_apresentacao}": DATA_EXEMPLO,
  "{conferido_em}": DATA_EXEMPLO,
  "{situacao}": "Pronta para Pauta",
  "{versao_publicada}": "3",
  "{prefixo}": "Virou lei",
  "{norma.rotulo}": "Lei 14.871/2024",
  "{rotulo}": "PL 4861/2023",
  "{herdada_de.rotulo}": "PL 5941/2013",
  "{principal_com_artigo}": "o PL 5941/2013",
  "{especie_plural}": "projetos de lei",
  "{especie_indefinida}": "um projeto de lei",
  "{rótulo do chip}": "Nas comissões",
  "{busca}": "pauta",
};

/** Todas as strings de TEXTOS, com as funções chamadas em cada caso de CASOS. */
function coletar(valor: unknown, caminho: string, saida: Texto[], semCaso: string[]) {
  if (typeof valor === "string") {
    saida.push({ caminho, texto: valor });
  } else if (typeof valor === "function") {
    const casos = CASOS[caminho];
    if (!casos) semCaso.push(caminho);
    for (const args of casos ?? []) {
      const texto = (valor as (a: Args) => string)(args);
      saida.push({ caminho: `${caminho}(${JSON.stringify(args)})`, texto });
    }
  } else {
    for (const [chave, filho] of Object.entries(valor as object)) {
      coletar(filho, caminho ? `${caminho}.${chave}` : chave, saida, semCaso);
    }
  }
}

function todos() {
  const saida: Texto[] = [];
  const semCaso: string[] = [];
  coletar(TEXTOS, "", saida, semCaso);
  return { saida, semCaso };
}

const preencher = (texto: string) =>
  Object.entries(EXEMPLOS).reduce((t, [marcador, exemplo]) => t.split(marcador).join(exemplo), texto);

const idDe = (caminho: string) => /^[A-Z]\d+[a-z]?(?:_[A-Z_]+)?/.exec(caminho)![0];
const baseDe = (caminho: string) => caminho.replace(/\(.*$/, "");

/** Strings que casam com a regra, com os marcadores preenchidos, como pede o critério 2. */
function violacoes(regra: string, ajuste: (preenchido: string) => string = (t) => t) {
  const r = REGRAS_ESTILO.find((x) => x.id === regra)!;
  return todos().saida.filter(({ texto }) => r.regex.test(ajuste(preencher(texto))));
}

describe("critério 1: TEXTOS e a matriz", () => {
  // Chaves previstas além dos IDs: C01_SAIBA_MAIS está na própria linha C01.
  // C01_FONTE_REGRAS guarda o terceiro texto de C01.
  const EXTRAS = ["C01_SAIBA_MAIS", "C01_FONTE_REGRAS"];

  it("IDS_MATRIZ e as chaves de TEXTOS são o mesmo conjunto, sem repetição", () => {
    expect(new Set(IDS_MATRIZ).size).toBe(IDS_MATRIZ.length);
    expect([...IDS_MATRIZ].sort()).toEqual(Object.keys(TEXTOS).sort());
  });

  it("IDS_MATRIZ é a lista da §4 com fonte textos.ts (e N00, que a API copia daqui)", () => {
    const daSpec = Object.entries(matriz())
      .filter(([, { fonte }]) => fonte.includes("textos.ts") || fonte.includes("esta matriz"))
      .map(([id]) => id);
    expect(daSpec.length).toBeGreaterThan(40);
    expect([...IDS_MATRIZ].filter((id) => !EXTRAS.includes(id)).sort()).toEqual(daSpec.sort());
  });

  it("não há texto de fase nem de desfecho: esses vêm da API", () => {
    expect(IDS_MATRIZ.filter((id) => /^[PD]\d/.test(id))).toEqual([]);
  });

  it("toda função tem caso de teste", () => {
    expect(todos().semCaso).toEqual([]);
  });
});

// Variantes que a §4 descreve sem escrever por extenso: a saída gerada se compara
// com um valor fixo. A chave é o caminho que `coletar` produz.
const VARIANTES: Record<string, string> = {
  'F04.linha({"prefixo":null,"rotulo":"{norma.rotulo}"})': "{norma.rotulo}",
  'L02({"movimentacao":"{data}","apresentada":null})': "Última movimentação em {data}",
  'L02({"movimentacao":null,"apresentada":"{data}"})': "Apresentada em {data}",
  'L04({"n":1})': "1 proposição",
  'L04({"n":"{n}","analise":"analisada"})': "{n} proposições analisadas",
  'L04({"n":1,"analise":"analisada"})': "1 proposição analisada",
  'L04({"n":"{n}","analise":"pendente"})': "{n} proposições sem análise",
  'L04({"n":"{n}","de":130})': "{n} de 130 proposições",
  'L04({"n":"{n}","faseChip":"{rótulo do chip}"})': "{n} proposições — fase: {rótulo do chip}",
  'N01.corpo({"situacao":"{situacao}","versaoPublicada":null})':
    "A situação oficial na Câmara, “{situacao}”, ainda não está no nosso mapa de fases. Preferimos não adivinhar.",
  'N01.corpo({"situacao":null,"versaoPublicada":null})':
    "A situação oficial desta proposição ainda não está no nosso mapa de fases. Preferimos não adivinhar.",
  'N04.corpo({"conferidoEm":null})':
    "Os dados da Câmara não bastam para saber: a situação oficial não foi informada, ou a Câmara não respondeu quando conferimos. Confira o andamento no site da Câmara.",
  'N05.corpo({"tipo":"PLP"})': "O ZIL ainda não acompanha as fases de projetos de lei complementar.",
  'N05.corpo({"tipo":"REQ"})': "O ZIL ainda não acompanha as fases deste tipo de proposição.",
  'N05.corpo({"tipo":null})': "O ZIL ainda não acompanha as fases deste tipo de proposição.",
  'K00.intro({"especieIndefinida":"{especie_indefinida}","casa":"camara"})':
    "O caminho de {especie_indefinida} que começa na Câmara. A etapa atual aparece marcada.",
  'K00.intro({"especieIndefinida":"{especie_indefinida}","casa":"senado"})':
    "O caminho de {especie_indefinida} que começa no Senado. A etapa atual aparece marcada.",
  'V01.aviso.corpo({"versaoPublicada":null})':
    "Escrito a partir da Constituição e dos regimentos da Câmara e do Senado. Cada etapa cita a regra.",
};

// Trechos entre aspas da linha da §4 que não são texto de TEXTOS.
const FORA_DE_TEXTOS: Record<string, string[]> = {
  // Nome de seção ou de estado, citado para situar o texto.
  I07: ["Onde está agora", "O caminho inteiro"],
  V01: ["Depois que vira lei", "Como montamos este mapa"],
  // Valor de enum, e prefixos que moram em especies.ts (especies.test.ts).
  F04: ["Virou lei", "Convertida em lei", "Virou decreto legislativo", "Virou emenda constitucional", "Virou resolução", "parcial"],
  // A §4 abrevia com "…": o valor inteiro está em VARIANTES.
  L04: ["… analisadas", "… sem análise", " — fase: {rótulo do chip}"],
  N04: ["… quando conferimos. Confira o andamento no site da Câmara."],
  N05: ["O ZIL ainda não acompanha as fases de {especie_plural}.", "deste tipo de proposição"],
  K00: ["O caminho de {especie_indefinida} que começa {na Câmara \\| no Senado}. A etapa atual aparece marcada."],
  // Texto do kit, na mesma linha.
  M02: ["Todos os {n} registros", "1 registro", "{n} registros carregados.", "Tentar de novo", "Mostrando {a}–{b} de {total}"],
  // Só visual, ou endereço.
  L06: ["→"],
  C01: ["/metodologia#tramitacao", "(abre em nova aba)"],
};

// Campos que a §4 escreve por referência: "Mesmo título e corpo", "Título idem".
const TITULO_N = "Não sabemos em que fase está";
const POR_REFERENCIA: Record<string, (linhas: Record<string, LinhaDaMatriz>) => string[]> = {
  A02: (linhas) => trechos(linhas.A01.texto).slice(0, 2),
  N03: () => [TITULO_N],
  N04: () => [TITULO_N],
  N05: () => [TITULO_N],
};

/** O que a §4 manda para o ID: referências, depois os trechos da linha, menos o que não é de TEXTOS. */
function esperadoDaSpec(id: string, linhas: Record<string, LinhaDaMatriz>): string[] {
  const base = id.replace(/_.*/, "");
  // N00 é o único sem texto entre aspas: o rótulo abre a célula do selo.
  if (id === "N00") return [/^(.+?) \(glifo/.exec(linhas.N00.selo)![1]];
  const lista = trechos(linhas[base].texto);
  // Remove a última ocorrência: os nomes de seção repetidos são os citados depois do `h2`.
  for (const fora of FORA_DE_TEXTOS[base] ?? []) lista.splice(lista.lastIndexOf(fora), 1);
  return [...(POR_REFERENCIA[base]?.(linhas) ?? []), ...lista];
}

/** O que TEXTOS gera para os IDs de uma linha da §4 (C01 e suas chaves extras são uma linha só). */
function geradoPorLinha(id: string): string[] {
  return todos()
    .saida.filter(({ caminho }) => idDe(caminho).replace(/_.*/, "") === id && !(caminho in VARIANTES))
    .map(({ texto }) => texto);
}

describe("os textos são os da §4, sem reescrever", () => {
  const LINHAS_REVISADAS = Array.from(new Set(IDS_MATRIZ.map((id) => id.replace(/_.*/, ""))));

  // Igualdade da lista inteira, na ordem: pega texto truncado, vazio, trocado
  // de lugar ou apagado, nos dois sentidos.
  it.each(LINHAS_REVISADAS)("%s é igual à linha da matriz, trecho a trecho", (id) => {
    expect(geradoPorLinha(id)).toEqual(esperadoDaSpec(id, matriz()));
  });

  it("toda exceção de FORA_DE_TEXTOS existe mesmo na linha", () => {
    const linhas = matriz();
    const fantasmas = Object.entries(FORA_DE_TEXTOS).flatMap(([id, lista]) =>
      lista.filter((t) => !trechos(linhas[id].texto).includes(t)).map((t) => `${id}: ${t}`),
    );
    expect(fantasmas).toEqual([]);
  });

  it("cada variante gera exatamente o valor fixo", () => {
    const geradas = Object.fromEntries(
      todos()
        .saida.filter(({ caminho }) => caminho in VARIANTES)
        .map(({ caminho, texto }) => [caminho, texto]),
    );
    expect(geradas).toEqual(VARIANTES);
  });

  // A ordem não pega par trocado junto com a chave. Aqui o nome do campo decide:
  // nestes, a direção muda o sentido do texto.
  it("cada campo direcional diz o que o nome promete", () => {
    expect(TEXTOS.L03).toEqual({
      vazio: "Ordenar",
      movimentacao: "Movimentação mais recente",
      apresentacaoRecente: "Apresentação mais recente",
      apresentacaoAntiga: "Apresentação mais antiga",
    });
    expect(TEXTOS.L05.casa).toEqual({ camara: "Começou na Câmara", senado: "Começou no Senado" });
    expect(TEXTOS.L05.fases).toEqual({
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
      nao_identificada: "Fase não identificada",
    });
    expect(TEXTOS.V01.chips).toEqual({
      PL: "Lei (PL)",
      PLP: "Lei complementar (PLP)",
      PEC: "Emenda à Constituição (PEC)",
      MPV: "Medida provisória (MPV)",
      PDL: "Decreto legislativo (PDL)",
      camara: "Na Câmara",
      senado: "No Senado",
    });
    expect(TEXTOS.I07.tituloCaminho).toBe("Não conseguimos carregar o caminho agora");
    expect(TEXTOS.I07.tituloExplicacoes).toBe("Não conseguimos carregar as explicações agora");
    expect(TEXTOS.F02.pagina).toBe("Ainda não informada pela Câmara.");
    expect(TEXTOS.F02.lista).toBe("Situação na Câmara: ainda não informada.");
    expect(TEXTOS.F03.pagina).toBe("Ainda não informada pela Câmara.");
    expect(TEXTOS.F03.lista).toBe("Situação na Câmara: ainda não informada.");
    expect(TEXTOS.F13.pagina).toBe("Ainda não conferimos a situação desta proposição na Câmara.");
    expect(TEXTOS.F13.lista).toBe("Situação na Câmara: ainda não conferida.");
    expect(TEXTOS.I12.semFase.titulo).toBe("Nenhuma proposição com esses filtros");
    expect(TEXTOS.I12.comFase.titulo).toBe("Nenhuma proposição nesta fase com esses filtros");
    expect(TEXTOS.F06.dt).toBe("Regime e quem decide");
    expect(TEXTOS.F11.dt).toBe("Tramita junto com");
    expect(TEXTOS.F04.lerNormasLeg).toBe("Ler o texto no normas.leg.br");
    expect(TEXTOS.F04.lerPlanalto).toBe("Ler o texto no Planalto");
    expect(TEXTOS.L05.grupoPauta).toBe("Pauta");
    expect(TEXTOS.L05.grupoFase).toBe("Fase");
    expect(TEXTOS.K00.introMpv).toBe("O caminho de uma medida provisória. A etapa atual aparece marcada.");
    expect(TEXTOS.K00.botao).toBe("Entender como uma proposição vira lei");
    expect(TEXTOS.V01.chapeu).toBe("Como funciona");
    expect(TEXTOS.V01.h1).toBe("Como uma proposição vira lei");
    expect(TEXTOS.V01.grupoTipo).toBe("Tipo de proposição");
    expect(TEXTOS.V01.grupoComeca).toBe("Começa");
    expect(TEXTOS.V01.h2).toEqual({
      caminho: "O caminho",
      outrasSituacoes: "Outras situações da Câmara",
      ondePodeParar: "Onde uma proposição pode parar",
      emConjunto: "Tramitação em conjunto",
      depoisDaLei: "Depois que vira lei",
      comoMontamos: "Como montamos este mapa",
    });
    expect(TEXTOS.V01.mapa.linkGithub).toBe("Ver o mapa no GitHub");
    expect(TEXTOS.V01.mapa.linkSituacoes).toBe("O que quer dizer cada situação");
    expect(TEXTOS.V02.chapeu).toBe("Como funciona");
    expect(TEXTOS.V02.h1).toBe("Esta página ainda está em revisão");
    expect(TEXTOS.V02.botaoProposicoes).toBe("Ver proposições");
    expect(TEXTOS.V02.botaoMetodologia).toBe("Como o ZIL trabalha");
    expect(TEXTOS.S01.chapeu).toBe("Como funciona");
    expect(TEXTOS.S01.h1).toBe("O que quer dizer cada situação");
    expect(TEXTOS.S01.h2).toEqual({
      situacoes: "Situações na Câmara",
      regimes: "Regimes de tramitação",
      quemDecide: "Quem decide: comissões ou Plenário",
    });
    expect(TEXTOS.S01.chips).toEqual({ situacoes: "Situações", regimes: "Regimes", quemDecide: "Quem decide" });
    expect(TEXTOS.S01.busca.rotulo).toBe("Buscar situação ou termo");
  });

  it("título e ação são os que a §4 rotula assim", () => {
    const linhas = matriz();
    const rotulado = (id: string, rotulo: string) => new RegExp(`${rotulo} "([^"]*)"`, "i").exec(linhas[id].texto)?.[1];
    for (const id of ["I03", "I05", "I10", "N01", "N02", "N06"] as const) {
      expect(TEXTOS[id].titulo).toBe(rotulado(id, "título"));
    }
    for (const id of ["I03", "I05", "I07", "I10", "A01", "A02"] as const) {
      expect(TEXTOS[id].acao).toBe(rotulado(id, "ação"));
    }
    expect(TEXTOS.S03.acao).toBe(rotulado("S03", "ação"));
  });
});

describe("marcador nulo nunca vira texto (notas de uso da §4)", () => {
  it("nenhuma variante escreve null, undefined ou travessão solto", () => {
    const ruins = todos().saida.filter(({ texto }) => /\bnull\b|\bundefined\b|\(\s*\)|versão \./.test(texto));
    expect(ruins).toEqual([]);
  });

  it("sem versão, some o parêntese de N01 e a oração de V01", () => {
    expect(TEXTOS.N01.corpo({ situacao: "Pronta para Pauta", versaoPublicada: null })).toBe(
      "A situação oficial na Câmara, “Pronta para Pauta”, ainda não está no nosso mapa de fases. Preferimos não adivinhar.",
    );
    expect(TEXTOS.V01.aviso.corpo({ versaoPublicada: null })).toBe(
      "Escrito a partir da Constituição e dos regimentos da Câmara e do Senado. Cada etapa cita a regra.",
    );
  });
});

describe("critério 2: guia de redação (§2.4)", () => {
  it.each(["V-E1", "V-E2", "V-E3", "V-E4", "V-E5", "V-E6", "V-E8", "V-E9"])("%s: nenhuma string casa", (regra) => {
    expect(violacoes(regra)).toEqual([]);
  });

  // CRITÉRIO 2 NÃO CUMPRIDO: 16 strings casam. Mudar texto ou regra é decisão da
  // maintainer, na §4 e na §2.4. As listas são exatas: um caso novo reprova aqui,
  // e cada caso resolvido obriga a tirar a linha. O merge pede as duas vazias.
  const PENDENTES_V_E7 = ["F02.paginaRecem", "F09", "L02", "N04.corpo"];
  const PENDENTES_V_E10: Record<string, string[]> = {
    API: ["I03.corpo", "I10.corpo"],
    ZIL: [
      "C01",
      "N05.corpo",
      "S01.aviso.titulo",
      "S01.aviso.corpo",
      "T01",
      "V01.aviso.titulo",
      "V01.mapa.texto",
      "V01.depoisDaLei",
      "V02.corpo",
      "V02.botaoMetodologia",
    ],
  };

  it.todo("critério 2 não cumprido: esvaziar PENDENTES_V_E7 e PENDENTES_V_E10, por decisão da maintainer");

  it("são 16 strings pendentes", () => {
    const total = PENDENTES_V_E7.length + Object.values(PENDENTES_V_E10).flat().length;
    expect(total).toBe(16);
  });

  it("PENDENTE V-E7: casam só as strings com marcador de data", () => {
    const achados = Array.from(new Set(violacoes("V-E7").map(({ caminho }) => baseDe(caminho))));
    expect(achados.sort()).toEqual([...PENDENTES_V_E7].sort());
  });

  it("V-E7: sem o valor do marcador, nenhuma data escrita no texto", () => {
    expect(violacoes("V-E7", (t) => t.split(DATA_EXEMPLO).join(""))).toEqual([]);
  });

  it("PENDENTE V-E10: casam só as strings com ZIL ou API", () => {
    const achados: Record<string, string[]> = {};
    for (const { caminho, texto } of violacoes("V-E10")) {
      const siglas = preencher(texto).match(/\b[A-Z]{3,}\b/g) ?? [];
      for (const sigla of siglas.filter((s) => !["PL", "PLP", "PEC", "MPV", "PDL", "PLV"].includes(s))) {
        achados[sigla] = Array.from(new Set([...(achados[sigla] ?? []), baseDe(caminho)]));
      }
    }
    for (const lista of Object.values(achados)) lista.sort();
    expect(achados).toEqual({
      API: [...PENDENTES_V_E10.API].sort(),
      ZIL: [...PENDENTES_V_E10.ZIL].sort(),
    });
  });
});

describe("sem cor nem marcação nos textos", () => {
  it("nenhum nome de classe e nenhum HTML", () => {
    const ruins = todos().saida.filter(({ texto }) => /zil-|text-|bg-|<[a-z/]/.test(texto));
    expect(ruins).toEqual([]);
  });
});

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { REGRAS_ESTILO } from "@/lib/tramitacao/estilo";
import { IDS_MATRIZ, TEXTOS } from "@/lib/tramitacao/textos";

const SPEC = resolve(__dirname, "../../../../../specs/013-tramitacao/backlog-interface.md");

/** Linhas da tabela de §4: { ID: { fonte, linha } }. */
function matriz(): Record<string, { fonte: string; linha: string }> {
  const secao = readFileSync(SPEC, "utf8").split("## 4. Matriz de estados e textos")[1].split("\n## 5.")[0];
  const linhas: Record<string, { fonte: string; linha: string }> = {};
  for (const linha of secao.split("\n")) {
    const id = /^\| ([A-Z]\d+[a-z]?) \|/.exec(linha)?.[1];
    if (id) linhas[id] = { fonte: linha.split(/(?<!\\)\|/)[7].trim(), linha };
  }
  return linhas;
}

type Args = Record<string, unknown>;
type Texto = { caminho: string; texto: string };

// O argumento de cada caso é o próprio marcador da §4 ("{data}"): a saída se
// compara direto com a linha da matriz e depois recebe o valor de exemplo.
const m = (marcador: string) => marcador as never;

const CASOS: Record<string, Args[]> = {
  "I10.corpo": [{ n: m("{n}") }],
  "F02.paginaRecem": [{ dataApresentacao: m("{data_apresentacao}") }],
  "F04.linha": [{ prefixo: m("{prefixo}"), rotulo: m("{norma.rotulo}") }],
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

/** IDs (ou caminhos) cujo texto casa com a regra, com os marcadores preenchidos. */
function violacoes(regra: string) {
  const r = REGRAS_ESTILO.find((x) => x.id === regra)!;
  return todos().saida.filter(({ texto }) => {
    // V-E7 proíbe data escrita no texto. A do marcador vem da API, por `dataBR`
    // (§2.4, "datas só vêm da API"), e sempre casaria.
    const preenchido = preencher(texto);
    return r.regex.test(regra === "V-E7" ? preenchido.split(DATA_EXEMPLO).join("") : preenchido);
  });
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

describe("os textos são os da §4, sem reescrever", () => {
  // Variantes que a §4 descreve em vez de escrever por extenso.
  const DERIVADOS = new Set([
    'L04({"n":"{n}","analise":"analisada"})',
    'L04({"n":1,"analise":"analisada"})',
    'L04({"n":"{n}","analise":"pendente"})',
    'L04({"n":"{n}","de":130})',
    'L04({"n":"{n}","faseChip":"{rótulo do chip}"})',
    'L04({"n":1})',
    'N01.corpo({"situacao":"{situacao}","versaoPublicada":null})',
    'N01.corpo({"situacao":null,"versaoPublicada":null})',
    'N04.corpo({"conferidoEm":null})',
    'N05.corpo({"tipo":"PLP"})',
    'N05.corpo({"tipo":"REQ"})',
    'N05.corpo({"tipo":null})',
    'K00.intro({"especieIndefinida":"{especie_indefinida}","casa":"camara"})',
    'K00.intro({"especieIndefinida":"{especie_indefinida}","casa":"senado"})',
    'V01.aviso.corpo({"versaoPublicada":null})',
  ]);

  // Linhas que a §4 escreve por referência: "Mesmo título e corpo", "Título idem".
  const IDEM: Record<string, string> = { A02: "A01", N03: "N01", N04: "N01", N05: "N01" };

  it("toda string está, letra a letra, na linha do seu ID", () => {
    const linhas = matriz();
    const fora = todos()
      .saida.filter(({ caminho }) => !DERIVADOS.has(caminho))
      .filter(({ caminho, texto }) => {
        const id = idDe(caminho).replace(/_.*/, "");
        return !linhas[id].linha.includes(texto) && !linhas[IDEM[id]]?.linha.includes(texto);
      });
    expect(fora).toEqual([]);
  });

  it("as variantes derivadas dizem o que a §4 manda", () => {
    expect(TEXTOS.L04({ n: 12 })).toBe("12 proposições");
    expect(TEXTOS.L04({ n: 1 })).toBe("1 proposição");
    expect(TEXTOS.L04({ n: 12, analise: "analisada" })).toBe("12 proposições analisadas");
    expect(TEXTOS.L04({ n: 1, analise: "analisada" })).toBe("1 proposição analisada");
    expect(TEXTOS.L04({ n: 12, analise: "pendente" })).toBe("12 proposições sem análise");
    expect(TEXTOS.L04({ n: 12, de: 130 })).toBe("12 de 130 proposições");
    expect(TEXTOS.L04({ n: 12, faseChip: "Nas comissões" })).toBe("12 proposições — fase: Nas comissões");
    expect(TEXTOS.N04.corpo({ conferidoEm: null })).toBe(
      "Os dados da Câmara não bastam para saber: a situação oficial não foi informada, ou a Câmara não respondeu quando conferimos. Confira o andamento no site da Câmara.",
    );
    expect(TEXTOS.N05.corpo({ tipo: "PLP" })).toBe("O ZIL ainda não acompanha as fases de projetos de lei complementar.");
    expect(TEXTOS.N05.corpo({ tipo: "REQ" })).toBe("O ZIL ainda não acompanha as fases deste tipo de proposição.");
    expect(TEXTOS.N05.corpo({ tipo: null })).toBe("O ZIL ainda não acompanha as fases deste tipo de proposição.");
    expect(TEXTOS.K00.intro({ especieIndefinida: "um projeto de lei", casa: "senado" })).toBe(
      "O caminho de um projeto de lei que começa no Senado. A etapa atual aparece marcada.",
    );
    expect(TEXTOS.M03({ n: 1 })).toBe("Ver o marco anterior");
    expect(TEXTOS.S02({ n: 1 })).toBe("1 resultado");
    expect(TEXTOS.L02({ movimentacao: null, apresentada: null })).toBeNull();
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
  it.each(["V-E1", "V-E2", "V-E3", "V-E4", "V-E5", "V-E6", "V-E7", "V-E8", "V-E9"])(
    "%s: nenhuma string casa",
    (regra) => {
      expect(violacoes(regra)).toEqual([]);
    },
  );

  // NÃO CUMPRIDO: os textos da §4 dizem "ZIL" e "API", e o padrão de V-E10
  // casa com as duas palavras. Mudar o texto ou a regra é decisão da
  // maintainer, na §4 e na §2.4. A lista é exata: um caso novo reprova aqui, e
  // cada caso resolvido obriga a tirar a linha.
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

  it("V-E10: só casam os textos pendentes de decisão, e só por ZIL ou API", () => {
    const achados: Record<string, string[]> = {};
    for (const { caminho, texto } of violacoes("V-E10")) {
      const siglas = preencher(texto).match(/\b[A-Z]{3,}\b/g) ?? [];
      for (const sigla of siglas.filter((s) => !["PL", "PLP", "PEC", "MPV", "PDL", "PLV"].includes(s))) {
        const base = caminho.replace(/\(.*$/, "");
        achados[sigla] = Array.from(new Set([...(achados[sigla] ?? []), base]));
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

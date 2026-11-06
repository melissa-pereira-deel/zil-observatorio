import type { NormaResumo, Proposicao } from "../api";

interface NomesDaEspecie {
  nome: string;
  plural: string;
  indefinida: string;
  artigo: "o" | "a";
}

const ESPECIES = new Map<string, NomesDaEspecie>([
  ["PL", { nome: "Projeto de lei", plural: "projetos de lei", indefinida: "um projeto de lei", artigo: "o" }],
  ["PLP", { nome: "Projeto de lei complementar", plural: "projetos de lei complementar", indefinida: "um projeto de lei complementar", artigo: "o" }],
  ["PEC", { nome: "Proposta de emenda à Constituição", plural: "propostas de emenda à Constituição", indefinida: "uma proposta de emenda à Constituição", artigo: "a" }],
  ["MPV", { nome: "Medida provisória", plural: "medidas provisórias", indefinida: "uma medida provisória", artigo: "a" }],
  ["PDL", { nome: "Projeto de decreto legislativo", plural: "projetos de decreto legislativo", indefinida: "um projeto de decreto legislativo", artigo: "o" }],
  ["PRC", { nome: "Projeto de resolução", plural: "projetos de resolução", indefinida: "um projeto de resolução", artigo: "o" }],
  ["PLN", { nome: "Projeto de lei do Congresso Nacional", plural: "projetos de lei do Congresso Nacional", indefinida: "um projeto de lei do Congresso Nacional", artigo: "o" }],
]);

const PROPOSICAO = "Proposição";

/** "Projeto de lei" */
export function nomeEspecie(tipo: string | null): string {
  return ESPECIES.get(tipo ?? "")?.nome ?? PROPOSICAO;
}

/** "projetos de lei" */
export function nomeEspeciePlural(tipo: string | null): string {
  return ESPECIES.get(tipo ?? "")?.plural ?? "proposições";
}

/** "um projeto de lei" */
export function especieIndefinida(tipo: string | null): string {
  return ESPECIES.get(tipo ?? "")?.indefinida ?? "uma proposição";
}

/** A espécie tem nome próprio aqui, ou cairia no genérico "proposições"? */
export function especieConhecida(tipo: string | null): boolean {
  return ESPECIES.has(tipo ?? "");
}

/** "o PL 5941/2013", "a PEC 45/2019". Sem nome conhecido, não chuta o gênero da sigla. */
export function comArtigo(rotulo: string): string {
  if (rotulo === PROPOSICAO) return "a proposição";
  const artigo = ESPECIES.get(rotulo.split(" ")[0])?.artigo;
  return artigo ? `${artigo} ${rotulo}` : `a proposição ${rotulo}`;
}

/** "PL 4861/2023". Dado que falta some do rótulo, em vez de virar "null". */
export function rotuloProposicao(p: Pick<Proposicao, "tipo" | "numero" | "ano">): string {
  const tipo = p.tipo ?? PROPOSICAO;
  if (p.numero === null) return tipo;
  return p.ano === null ? `${tipo} ${p.numero}` : `${tipo} ${p.numero}/${p.ano}`;
}

/** Prefixo da linha F04: "Virou lei", "Convertida em lei"... */
export function prefixoNorma(tipoProposicao: string | null, tipoNorma: NormaResumo["tipo"]): string {
  switch (tipoNorma) {
    case "lei_ordinaria":
    case "lei_complementar":
    case "lei":
      return tipoProposicao === "MPV" ? "Convertida em lei" : "Virou lei";
    case "decreto_legislativo":
      return "Virou decreto legislativo";
    case "emenda_constitucional":
      return "Virou emenda constitucional";
    case "resolucao":
      return "Virou resolução";
  }
}

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { REGRAS_ESTILO, violacoesDeEstilo } from "@/lib/tramitacao/estilo";

const GUIA = resolve(__dirname, "../../../../../specs/013-tramitacao/backlog-interface.md");

/** Lê as linhas V-E da tabela de §2.4: { "V-E1": "padrão como a spec escreve" }. */
function padroesDaSpec(): Record<string, string> {
  const padroes: Record<string, string> = {};
  for (const linha of readFileSync(GUIA, "utf8").split("\n")) {
    const id = /^\| (V-E\d+) \|/.exec(linha)?.[1];
    if (!id) continue;
    const coluna = linha.split(/(?<!\\)\|/)[4];
    padroes[id] = /`([^`]+)`/.exec(coluna)![1].replace(/\\\|/g, "|");
  }
  return padroes;
}

describe("regras de estilo (§2.4)", () => {
  it("são as dez, com o padrão idêntico ao da spec", () => {
    const daSpec = padroesDaSpec();
    expect(Object.keys(daSpec)).toHaveLength(10);
    expect(Object.fromEntries(REGRAS_ESTILO.map((r) => [r.id, r.padrao]))).toEqual(daSpec);
  });

  it.each([
    ["V-E1", "Deve ser votada em breve"],
    ["V-E1", "está prevista para março"],
    ["V-E1", "até o fim do ano"],
    ["V-E2", "Parada há 30 dias"],
    ["V-E2", "há 3 meses na comissão"],
    ["V-E2", "engavetada"],
    ["V-E2", "ATRASADA"],
    ["V-E3", "80% concluída"],
    ["V-E3", "Falta pouco"],
    ["V-E4", "Lei não regulamentada"],
    ["V-E4", "o governo não regulamentou"],
    ["V-E5", "Infelizmente"],
    ["V-E5", "uma votação importante"],
    ["V-E6", "O Presidente decide"],
    ["V-E6", "o Presidente da comissão"],
    ["V-E7", "em 30/10/2026"],
    ["V-E7", "em 30/10"],
    ["V-E8", "tem 15 dias para decidir"],
    ["V-E9", "relator(a)"],
    ["V-E10", "A API respondeu"],
    ["V-E10", "foi ao PLEN"],
  ])("%s casa com %j", (id, texto) => {
    expect(violacoesDeEstilo(texto)).toContain(id);
  });

  it.each([
    ["V-E6", "o presidente da comissão"],
    ["V-E6", "o Presidente da República"],
    ["V-E6", "o Presidente da Câmara"],
    ["V-E6", "o Presidente do Senado"],
    ["V-E6", "o Presidente do Congresso"],
    ["V-E7", "o PL 5941/2013"],
    ["V-E7", "a PEC 45/2019"],
    ["V-E7", "a Lei 14.871/2024"],
    ["V-E8", "15 dias úteis"],
    ["V-E8", "60 dias corridos"],
    ["V-E10", "o PL, o PLP, a PEC, a MPV, o PDL e o PLV"],
    ["V-E10", "api"],
    ["V-E9", "Lei (PL)"],
  ])("%s não casa com %j", (id, texto) => {
    expect(violacoesDeEstilo(texto)).not.toContain(id);
  });

  // Em JS, \b só conhece ASCII; em Python (TRM-024), acento é letra. Sem a
  // tradução, "CÂMARA" casaria "MARA" aqui e não no validador do YAML.
  it("trata letra acentuada como letra, como o regex Python da spec", () => {
    expect(violacoesDeEstilo("CÂMARA")).toEqual([]);
    expect(violacoesDeEstilo("PRESIDÊNCIA")).toEqual([]);
    expect(violacoesDeEstilo("Vice-Presidenteé")).toEqual([]);
    expect(violacoesDeEstilo("água(a)")).toContain("V-E9");
  });

  it("V-E6 e V-E10 dependem de maiúsculas; as outras, não", () => {
    expect(REGRAS_ESTILO.filter((r) => !r.regex.ignoreCase).map((r) => r.id)).toEqual(["V-E6", "V-E10"]);
  });

  it("dá o mesmo resultado em chamadas repetidas (regex sem estado)", () => {
    expect(violacoesDeEstilo("Em breve")).toEqual(violacoesDeEstilo("Em breve"));
    expect(REGRAS_ESTILO.every((r) => !r.regex.global && !r.regex.sticky)).toBe(true);
  });

  it("não acusa texto neutro", () => {
    expect(violacoesDeEstilo("Última movimentação na Câmara dos Deputados.")).toEqual([]);
  });
});

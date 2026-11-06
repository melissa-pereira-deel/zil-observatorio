import { describe, expect, it } from "vitest";

import type { NormaResumo, Proposicao } from "@/lib/api";
import {
  comArtigo,
  especieIndefinida,
  nomeEspecie,
  nomeEspeciePlural,
  prefixoNorma,
  rotuloProposicao,
} from "@/lib/tramitacao/especies";
import { TEXTOS } from "@/lib/tramitacao/textos";

describe("nomes das espécies", () => {
  it.each([
    ["PL", "Projeto de lei", "projetos de lei", "um projeto de lei"],
    ["PLP", "Projeto de lei complementar", "projetos de lei complementar", "um projeto de lei complementar"],
    ["PEC", "Proposta de emenda à Constituição", "propostas de emenda à Constituição", "uma proposta de emenda à Constituição"],
    ["MPV", "Medida provisória", "medidas provisórias", "uma medida provisória"],
    ["PDL", "Projeto de decreto legislativo", "projetos de decreto legislativo", "um projeto de decreto legislativo"],
    ["PRC", "Projeto de resolução", "projetos de resolução", "um projeto de resolução"],
    ["PLN", "Projeto de lei do Congresso Nacional", "projetos de lei do Congresso Nacional", "um projeto de lei do Congresso Nacional"],
  ])("%s", (tipo, nome, plural, indefinida) => {
    expect(nomeEspecie(tipo)).toBe(nome);
    expect(nomeEspeciePlural(tipo)).toBe(plural);
    expect(especieIndefinida(tipo)).toBe(indefinida);
  });

  it.each([["REQ"], [null], [""], ["constructor"]])("espécie desconhecida %j", (tipo) => {
    expect(nomeEspecie(tipo)).toBe("Proposição");
    expect(nomeEspeciePlural(tipo)).toBe("proposições");
    expect(especieIndefinida(tipo)).toBe("uma proposição");
  });
});

describe("comArtigo", () => {
  it.each([
    ["PL 5941/2013", "o PL 5941/2013"],
    ["PLP 68/2024", "o PLP 68/2024"],
    ["PDL 571/2026", "o PDL 571/2026"],
    ["PRC 27/2025", "o PRC 27/2025"],
    ["PLN 4/2024", "o PLN 4/2024"],
    ["PEC 45/2019", "a PEC 45/2019"],
    ["MPV 1196/2023", "a MPV 1196/2023"],
  ])("%s", (rotulo, esperado) => {
    expect(comArtigo(rotulo)).toBe(esperado);
  });

  it("espécie desconhecida vira \"a proposição\", sem chutar o gênero da sigla", () => {
    expect(comArtigo("REQ 12/2024")).toBe("a proposição REQ 12/2024");
    expect(comArtigo("Proposição")).toBe("a proposição");
  });

  it("combina com rotuloProposicao quando falta o tipo", () => {
    expect(comArtigo(rotuloProposicao({ tipo: null, numero: 5, ano: 2020 }))).toBe("a proposição 5/2020");
    expect(comArtigo(rotuloProposicao({ tipo: "", numero: 5, ano: 2020 }))).toBe("a proposição 5/2020");
    expect(comArtigo(rotuloProposicao({ tipo: null, numero: null, ano: null }))).toBe("a proposição");
  });
});

describe("rotuloProposicao", () => {
  it("monta tipo, número e ano", () => {
    expect(rotuloProposicao({ tipo: "PL", numero: 4861, ano: 2023 })).toBe("PL 4861/2023");
  });

  it("nunca escreve null quando falta um dado", () => {
    expect(rotuloProposicao({ tipo: "PL", numero: 4861, ano: null })).toBe("PL 4861");
    expect(rotuloProposicao({ tipo: "PL", numero: null, ano: 2023 })).toBe("PL");
    expect(rotuloProposicao({ tipo: null, numero: null, ano: null })).toBe("Proposição");
  });
});

describe("prefixoNorma (F04)", () => {
  it.each<[NormaResumo["tipo"], string]>([
    ["lei_ordinaria", "Virou lei"],
    ["lei_complementar", "Virou lei"],
    ["lei", "Virou lei"],
    ["decreto_legislativo", "Virou decreto legislativo"],
    ["emenda_constitucional", "Virou emenda constitucional"],
    ["resolucao", "Virou resolução"],
  ])("%s", (tipoNorma, esperado) => {
    expect(prefixoNorma("PL", tipoNorma)).toBe(esperado);
  });

  it.each<[NormaResumo["tipo"]]>([["lei_ordinaria"], ["lei_complementar"], ["lei"]])(
    "MPV que vira %s é \"Convertida em lei\"",
    (tipoNorma) => {
      expect(prefixoNorma("MPV", tipoNorma)).toBe("Convertida em lei");
    },
  );

  it("MPV só troca o prefixo das leis", () => {
    expect(prefixoNorma("MPV", "decreto_legislativo")).toBe("Virou decreto legislativo");
  });

  it("aceita proposição sem tipo", () => {
    expect(prefixoNorma(null, "lei")).toBe("Virou lei");
  });

  // A API pode ampliar o enum antes do front. Sem texto na §4 para isso, o
  // prefixo some (notas de uso: "sem variante, a oração some").
  it("tipo de norma fora do enum não tem prefixo", () => {
    expect(prefixoNorma("PL", "tratado" as unknown as NormaResumo["tipo"])).toBeNull();
    expect(prefixoNorma("MPV", null as unknown as NormaResumo["tipo"])).toBeNull();
  });

  it("sem prefixo, F04 mostra só o rótulo, sem escrever undefined", () => {
    const prefixo = prefixoNorma("PL", "tratado" as unknown as NormaResumo["tipo"]);
    expect(TEXTOS.F04.linha({ prefixo, rotulo: "Lei 14.871/2024" })).toBe("Lei 14.871/2024");
  });
});

// O que vale aqui é o `tsc`, que inclui tests/: os objetos abaixo só compilam
// se os campos novos de `Proposicao` forem opcionais e tiverem os tipos do
// contrato (backlog-dados.md §1.5).
describe("Proposicao (critério 3b)", () => {
  const camposAntigos: Proposicao = {
    id: "00000000-0000-4000-8000-000000000001",
    fonte_id: "2",
    fonte: "camara",
    tipo: "PL",
    numero: 2,
    ano: 2024,
    ementa: null,
    situacao: null,
    data_apresentacao: null,
    categorias_zil: null,
    relevancia_zil: null,
    url_inteiro_teor: null,
    contexto_status: null,
    resumo_simples: null,
    confianca: null,
  };

  const norma: NormaResumo = {
    tipo: "lei_ordinaria",
    rotulo: "Lei 14.871/2024",
    numero: 14871,
    ano: 2024,
    data: "2024-05-28",
    veto: "parcial",
    url_normas_leg: null,
    url_planalto: null,
    links_verificados: false,
    fonte: "despacho_camara",
    verificada_em: "2026-10-30T12:00:00-03:00",
  };

  it("a API antiga, sem os campos novos, continua servindo", () => {
    expect(camposAntigos.situacao_estado).toBeUndefined();
  });

  it("aceita todos os campos de F0", () => {
    const completa: Proposicao = {
      ...camposAntigos,
      cod_situacao: "924",
      situacao_estado: "informada",
      sigla_orgao: "CCP",
      orgao_nome: null,
      orgao_efetivo_sigla: "CME",
      orgao_efetivo_nome: "Comissão de Minas e Energia",
      regime: null,
      regime_chave: null,
      regime_texto: null,
      apreciacao: null,
      apreciacao_chave: null,
      apreciacao_texto: null,
      relator_nome: null,
      ultima_movimentacao_em: "2026-09-01T10:00:00-03:00",
      detalhe_sincronizado_em: "2026-10-30T12:00:00-03:00",
      url_camara: null,
      principal_fonte_id: null,
      principal_url_camara: null,
      situacao_glossario: null,
      norma,
    };
    expect(completa.norma?.rotulo).toBe("Lei 14.871/2024");
  });

  it("recusa valor fora dos enums do contrato", () => {
    // @ts-expect-error situacao_estado só aceita os quatro valores do contrato
    const estado: Proposicao["situacao_estado"] = "recem";
    // @ts-expect-error veto só pode ser "parcial" ou null
    const veto: NormaResumo["veto"] = "total";
    // @ts-expect-error `situacao_estado` opcional não admite null: a API sempre manda
    const nulo: Proposicao["situacao_estado"] = null;
    expect([estado, veto, nulo]).toHaveLength(3);
  });
});

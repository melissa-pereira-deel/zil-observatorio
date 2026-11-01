/** As 27 unidades da federação, em ordem alfabética (seletores, filtros). */
export const UFS = [
  "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
  "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
] as const;

export type UF = (typeof UFS)[number];

/**
 * Posição de cada UF no mapa em grade (ZIL Interface › Mapa por UF): coluna
 * e linha, a partir de 1, numa grade de 7 × 8. Aproxima a geografia sem
 * desenhar fronteiras — estado pequeno ocupa o mesmo espaço que estado
 * grande, que é o que se quer quando o dado é por bancada.
 */
export const GRADE_UF: Record<UF, [coluna: number, linha: number]> = {
  RR: [3, 1], AP: [5, 1],
  AM: [2, 2], PA: [4, 2], MA: [5, 2], CE: [6, 2], RN: [7, 2],
  AC: [1, 3], RO: [2, 3], MT: [3, 3], TO: [4, 3], PI: [5, 3], PE: [6, 3], PB: [7, 3],
  MS: [3, 4], GO: [4, 4], BA: [5, 4], SE: [6, 4], AL: [7, 4],
  SP: [3, 5], DF: [4, 5], MG: [5, 5], ES: [6, 5],
  PR: [3, 6], RJ: [5, 6],
  SC: [3, 7],
  RS: [3, 8],
};

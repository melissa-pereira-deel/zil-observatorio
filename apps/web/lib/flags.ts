/**
 * Flags de publicação.
 *
 * O ranking só deve ir ao ar quando a curadoria editorial o sustentar. Hoje as
 * 7 classificações que alimentam o Score ZIL estão marcadas
 * `validacao: nao-validado` em data/direcoes/ — todas na mesma direção, o que
 * deixa o ranking praticamente sem poder de discriminação.
 *
 * Ver docs/GOVERNANCE.md ("Estado atual da governança") e o cabeçalho de
 * data/direcoes/2024.yml.
 */

/** Ligue com NEXT_PUBLIC_RANKING_PUBLICO=true quando a curadoria sustentar. */
export const rankingPublico = process.env.NEXT_PUBLIC_RANKING_PUBLICO === "true";

/** Rotas que dependem do Score ZIL e ficam fora do ar enquanto o ranking não for público. */
export const ROTAS_DEPENDENTES_DE_SCORE = ["/ranking", "/parlamentar"];

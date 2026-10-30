/**
 * A votação em destaque na home, pelo ID da Câmara (o `id` interno muda de
 * banco para banco; o da Câmara, não).
 *
 * PL 327/2021 (PATEN), emendas do Senado, 18/12/2024: 448 sim × 14 não.
 * Escolhida por ser nominal — tem voto por deputado, ao contrário das
 * simbólicas — e por ser o caso mais fácil de explicar: a Câmara quase
 * inteira na mesma direção numa pauta de transição energética.
 *
 * Trocar é trocar este ID por outro `fonte_id` de `data/direcoes/`.
 */
export const VOTACAO_DESTAQUE = "2269745-144";

/**
 * Endereços externos do projeto.
 *
 * A newsletter do ZIL vai viver no Substack e ainda não foi criada. O
 * endereço entra por `NEXT_PUBLIC_NEWSLETTER_URL` (gravado no bundle no
 * build, como toda `NEXT_PUBLIC_*`); enquanto estiver vazio, o site diz que
 * a newsletter está a caminho em vez de apontar para um link inventado.
 */
export const NEWSLETTER_URL = process.env.NEXT_PUBLIC_NEWSLETTER_URL ?? "";

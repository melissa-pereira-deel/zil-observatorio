/**
 * Endereços externos do projeto.
 *
 * A newsletter do ZIL vai viver no Substack e ainda não foi criada. O
 * endereço entra por `NEXT_PUBLIC_NEWSLETTER_URL` (gravado no bundle no
 * build, como toda `NEXT_PUBLIC_*`); enquanto estiver vazio, o site diz que
 * a newsletter está a caminho em vez de apontar para um link inventado.
 */
export const NEWSLETTER_URL = process.env.NEXT_PUBLIC_NEWSLETTER_URL ?? "";

/** O repositório, como está no remoto hoje. Mudar de organização é mudar aqui. */
export const REPO_URL = "https://github.com/melissa-pereira-deel/zil-observatorio";
export const REPO_ROTULO = "github.com/melissa-pereira-deel/zil-observatorio";
export const ROADMAP_URL = `${REPO_URL}/blob/main/docs/ROADMAP.md`;
export const CONTRIBUIR_URL = `${REPO_URL}/blob/main/CONTRIBUTING.md#curadoria-de-dados`;

/** Documentação da API aberta (FastAPI expõe em /docs). */
export const API_DOCS_URL = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/docs`;

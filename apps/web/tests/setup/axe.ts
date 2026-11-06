import { configureAxe } from "jest-axe";

export const axe = configureAxe({
  rules: {
    // Contraste depende do CSS computado dos temas, que o jsdom não calcula:
    // é verificado no Playwright, nos dois temas.
    "color-contrast": { enabled: false },
    // Componente isolado não está dentro de landmark; landmarks são
    // verificados nas páginas, no Playwright.
    region: { enabled: false },
  },
});

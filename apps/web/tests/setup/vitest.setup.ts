import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { toHaveNoViolations } from "jest-axe";
import { afterEach, expect } from "vitest";

expect.extend(toHaveNoViolations);
// Sem `globals: true`, o Testing Library não registra a limpeza sozinho.
afterEach(() => cleanup());

// O jsdom não tem estas APIs; o kit as usa em efeitos (Segmentado, Revelar).
globalThis.ResizeObserver ??= class {
  observe() {}
  unobserve() {}
  disconnect() {}
};
if (!window.matchMedia) {
  window.matchMedia = (query: string) =>
    ({ matches: false, media: query, onchange: null, addListener() {}, removeListener() {},
       addEventListener() {}, removeEventListener() {}, dispatchEvent: () => false }) as MediaQueryList;
}

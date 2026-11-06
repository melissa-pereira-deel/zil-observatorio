import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const raiz = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  // "@/x" → apps/web/x, como no tsconfig. Regex para não casar "@testing-library".
  resolve: { alias: [{ find: /^@\//, replacement: raiz }] },
  test: {
    environment: "jsdom",
    include: ["tests/componentes/**/*.test.{ts,tsx}", "tests/unit/**/*.test.{ts,tsx}"],
    setupFiles: ["./tests/setup/vitest.setup.ts"],
    css: false,
    restoreMocks: true,
  },
});

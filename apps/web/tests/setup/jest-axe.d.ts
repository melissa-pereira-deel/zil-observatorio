declare module "jest-axe" {
  import type { AxeResults, RunOptions, Spec } from "axe-core";
  export interface OpcoesAxe extends RunOptions {
    globalOptions?: Spec;
    impactLevels?: Array<"minor" | "moderate" | "serious" | "critical">;
  }
  export function configureAxe(opcoes?: OpcoesAxe): (html: Element | string, opcoes?: RunOptions) => Promise<AxeResults>;
  export const axe: ReturnType<typeof configureAxe>;
  export const toHaveNoViolations: {
    toHaveNoViolations(resultado: AxeResults): { pass: boolean; message(): string };
  };
}

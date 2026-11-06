import "vitest";

declare module "vitest" {
  interface Matchers<T = any> {
    toHaveNoViolations(): T;
  }
}

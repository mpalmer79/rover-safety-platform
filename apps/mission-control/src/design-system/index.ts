/**
 * Phase 20 design-system entry point.
 *
 * Components import shared tokens from this module rather than from
 * the raw token files. Adding a new token here requires a matching
 * test in ``tests/design-system.test.ts``.
 */

export * from "./typography";
export * from "./spacing";
export * from "./motion";
export * from "./gradients";
export * from "./accessibility";

export { TOKENS, tokenSet, CSS_VAR, gradient } from "@/styles/tokens";
export type { ThemeName, ThemeTokenSet, CssVarName } from "@/styles/tokens";

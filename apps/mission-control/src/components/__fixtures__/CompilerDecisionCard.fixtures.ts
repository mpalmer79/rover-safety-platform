/**
 * Catalog fixtures for CompilerDecisionCard.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { CompilerDecisionCard } from "@/components/CompilerDecisionCard";


type Props = ComponentProps<typeof CompilerDecisionCard>;

export const STATES: Record<string, Props> = {
  rejected: ({ diagnostics: [{ code: "unsafe_speed", severity: "rejection", message: "too fast" }] }) as Props,
  empty: ({ diagnostics: [] }) as Props,
};

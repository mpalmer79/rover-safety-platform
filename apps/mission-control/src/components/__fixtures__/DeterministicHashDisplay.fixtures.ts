/**
 * Catalog fixtures for DeterministicHashDisplay.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { DeterministicHashDisplay } from "@/components/DeterministicHashDisplay";


type Props = ComponentProps<typeof DeterministicHashDisplay>;

export const STATES: Record<string, Props> = {
  with_hash: ({ label: "plan", hash: "a".repeat(64) }) as Props,
  null_hash: ({ label: "runtime", hash: null }) as Props,
};

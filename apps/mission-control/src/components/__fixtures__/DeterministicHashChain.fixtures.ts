/**
 * Catalog fixtures for DeterministicHashChain.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { DeterministicHashChain } from "@/components/DeterministicHashChain";
import { FIX_REGISTRY_RECORD } from "./_shared";

type Props = ComponentProps<typeof DeterministicHashChain>;

export const STATES: Record<string, Props> = {
  with_files: ({ files: FIX_REGISTRY_RECORD.files }) as Props,
  empty: ({ files: [] }) as Props,
};

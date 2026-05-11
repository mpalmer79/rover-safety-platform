/**
 * Catalog fixtures for EvidenceStatusChip.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { EvidenceStatusChip } from "@/components/EvidenceStatusChip";


type Props = ComponentProps<typeof EvidenceStatusChip>;

export const STATES: Record<string, Props> = {
  simulated: ({ status: "simulated", bagBacked: false }) as Props,
  static_only: ({ status: "static_only", bagBacked: false }) as Props,
  not_evaluated: ({ status: "not_evaluated", bagBacked: false }) as Props,
};

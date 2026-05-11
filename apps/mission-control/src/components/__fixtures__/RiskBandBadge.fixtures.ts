/**
 * Catalog fixtures for RiskBandBadge.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { RiskBandBadge } from "@/components/RiskBandBadge";


type Props = ComponentProps<typeof RiskBandBadge>;

export const STATES: Record<string, Props> = {
  low: ({ band: "low" }) as Props,
  guarded: ({ band: "guarded" }) as Props,
  restricted: ({ band: "restricted" }) as Props,
  blocked: ({ band: "blocked" }) as Props,
};

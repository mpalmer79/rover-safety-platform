/**
 * Catalog fixtures for WhyRejectedDrilldown.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { WhyRejectedDrilldown } from "@/components/WhyRejectedDrilldown";
import { FIX_AUDIT } from "./_shared";

type Props = ComponentProps<typeof WhyRejectedDrilldown>;

export const STATES: Record<string, Props> = {
  rejected: ({ audit: FIX_AUDIT }) as Props,
};

/**
 * Catalog fixtures for ReplayAnalyticsPanel.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ReplayAnalyticsPanel } from "@/components/ReplayAnalyticsPanel";


type Props = ComponentProps<typeof ReplayAnalyticsPanel>;

export const STATES: Record<string, Props> = {
  none: ({ analytics: null }) as Props,
};

/**
 * Catalog fixtures for SupervisorInterventionOverlay.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { SupervisorInterventionOverlay } from "@/components/SupervisorInterventionOverlay";
import { FIX_EVENT_REJECTION, FIX_EVENT_INFO } from "./_shared";

type Props = ComponentProps<typeof SupervisorInterventionOverlay>;

export const STATES: Record<string, Props> = {
  intervention: ({ events: [FIX_EVENT_REJECTION] }) as Props,
  empty: ({ events: [] }) as Props,
};

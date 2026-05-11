/**
 * Catalog fixtures for SupervisorAuthorityPanel.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { SupervisorAuthorityPanel } from "@/components/SupervisorAuthorityPanel";
import { FIX_SUPERVISOR_DECISION } from "./_shared";

type Props = ComponentProps<typeof SupervisorAuthorityPanel>;

export const STATES: Record<string, Props> = {
  rejected: ({ decision: FIX_SUPERVISOR_DECISION }) as Props,
};

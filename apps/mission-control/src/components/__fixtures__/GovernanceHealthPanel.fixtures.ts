/**
 * Catalog fixtures for GovernanceHealthPanel.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { GovernanceHealthPanel } from "@/components/GovernanceHealthPanel";
import { FIX_AUDIT } from "./_shared";

type Props = ComponentProps<typeof GovernanceHealthPanel>;

export const STATES: Record<string, Props> = {
  audit: ({ audits: [FIX_AUDIT], traceability: null }) as Props,
};

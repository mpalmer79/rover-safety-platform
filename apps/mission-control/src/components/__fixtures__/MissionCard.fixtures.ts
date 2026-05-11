/**
 * Catalog fixtures for MissionCard.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { MissionCard } from "@/components/MissionCard";
import { FIX_AUDIT } from "./_shared";

type Props = ComponentProps<typeof MissionCard>;

export const STATES: Record<string, Props> = {
  rejected: ({ audit: FIX_AUDIT }) as Props,
};

/**
 * Catalog fixtures for ZoneBoundaryOverlay.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ZoneBoundaryOverlay } from "@/components/ZoneBoundaryOverlay";
import { FIX_AUDIT } from "./_shared";

type Props = ComponentProps<typeof ZoneBoundaryOverlay>;

export const STATES: Record<string, Props> = {
  audit: ({ audit: FIX_AUDIT }) as Props,
};

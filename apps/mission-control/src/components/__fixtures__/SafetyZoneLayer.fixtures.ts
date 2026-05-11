/**
 * Catalog fixtures for SafetyZoneLayer.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { SafetyZoneLayer } from "@/components/SafetyZoneLayer";
import { FIX_PLAN } from "./_shared";

type Props = ComponentProps<typeof SafetyZoneLayer>;

export const STATES: Record<string, Props> = {
  with_plan: ({ plan: FIX_PLAN }) as Props,
  no_plan: ({ plan: null }) as Props,
};

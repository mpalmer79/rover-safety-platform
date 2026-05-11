/**
 * Catalog fixtures for RouteProgressIndicator.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { RouteProgressIndicator } from "@/components/RouteProgressIndicator";
import { FIX_ROUTE } from "./_shared";
import { buildMissionRoute } from "@/adapters/spatial";

type Props = ComponentProps<typeof RouteProgressIndicator>;

export const STATES: Record<string, Props> = {
  derived: ({ route: FIX_ROUTE }) as Props,
  empty: ({ route: buildMissionRoute(null) }) as Props,
};

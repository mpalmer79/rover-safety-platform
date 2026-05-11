/**
 * Catalog fixtures for MissionRoute.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { MissionRouteList } from "@/components/MissionRoute";
import { FIX_ROUTE } from "./_shared";

type Props = ComponentProps<typeof MissionRouteList>;

export const STATES: Record<string, Props> = {
  derived: ({ route: FIX_ROUTE }) as Props,
};

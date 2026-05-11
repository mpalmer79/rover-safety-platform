/**
 * Catalog fixtures for WaypointOverlay.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { WaypointOverlay } from "@/components/WaypointOverlay";
import { FIX_ROUTE } from "./_shared";

type Props = ComponentProps<typeof WaypointOverlay>;

export const STATES: Record<string, Props> = {
  selected: ({ waypoint: FIX_ROUTE.waypoints[0] }) as Props,
  none: ({ waypoint: null }) as Props,
};

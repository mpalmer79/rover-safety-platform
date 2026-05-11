/**
 * Catalog fixtures for MissionEventMarker.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { MissionEventMarker } from "@/components/MissionEventMarker";


type Props = ComponentProps<typeof MissionEventMarker>;

export const STATES: Record<string, Props> = {
  info: ({ severity: "info", label: "info" }) as Props,
  warning: ({ severity: "warning", label: "warning" }) as Props,
  rejection: ({ severity: "rejection", label: "rejection" }) as Props,
};

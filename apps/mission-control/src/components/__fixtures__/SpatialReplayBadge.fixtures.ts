/**
 * Catalog fixtures for SpatialReplayBadge.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { SpatialReplayBadge } from "@/components/SpatialReplayBadge";


type Props = ComponentProps<typeof SpatialReplayBadge>;

export const STATES: Record<string, Props> = {
  bag_backed: ({ source: "bag_backed" }) as Props,
  fixture: ({ source: "fixture" }) as Props,
  bounded_inputs: ({ source: "bounded_inputs" }) as Props,
  topology_only: ({ source: "topology_only" }) as Props,
  unavailable: ({ source: "unavailable" }) as Props,
};

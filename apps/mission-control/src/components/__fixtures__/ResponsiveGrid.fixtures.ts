/**
 * Catalog fixtures for ResponsiveGrid.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ResponsiveGrid } from "@/components/ResponsiveGrid";


type Props = ComponentProps<typeof ResponsiveGrid>;

export const STATES: Record<string, Props> = {
  stack: ({ shape: "stack", children: "single column" }) as Props,
  auto: ({ shape: "auto", children: "auto-grid" }) as Props,
  mission: ({ shape: "mission", children: "asymmetric mission shape" }) as Props,
};

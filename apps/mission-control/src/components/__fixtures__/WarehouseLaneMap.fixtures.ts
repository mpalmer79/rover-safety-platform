/**
 * Catalog fixtures for WarehouseLaneMap.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { WarehouseLaneMap } from "@/components/WarehouseLaneMap";


type Props = ComponentProps<typeof WarehouseLaneMap>;

export const STATES: Record<string, Props> = {
  default: ({}) as Props,
};

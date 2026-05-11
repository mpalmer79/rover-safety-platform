/**
 * Catalog fixtures for SiteNav.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { SiteNav } from "@/components/SiteNav";


type Props = ComponentProps<typeof SiteNav>;

export const STATES: Record<string, Props> = {
  default: ({}) as Props,
};

/**
 * Catalog fixtures for PageSurface.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { PageSurface } from "@/components/PageSurface";


type Props = ComponentProps<typeof PageSurface>;

export const STATES: Record<string, Props> = {
  default: ({ children: "content" }) as Props,
};

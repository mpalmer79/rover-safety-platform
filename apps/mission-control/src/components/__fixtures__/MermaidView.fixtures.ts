/**
 * Catalog fixtures for MermaidView.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { MermaidView } from "@/components/MermaidView";


type Props = ComponentProps<typeof MermaidView>;

export const STATES: Record<string, Props> = {
  diagram: ({ source: "graph TD; A-->B" }) as Props,
};

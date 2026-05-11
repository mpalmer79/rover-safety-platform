/**
 * Catalog fixtures for GradientPanel.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { GradientPanel } from "@/components/GradientPanel";


type Props = ComponentProps<typeof GradientPanel>;

export const STATES: Record<string, Props> = {
  default: ({ children: "panel body" }) as Props,
  accent: ({ tone: "accent", children: "accent body" }) as Props,
  warning: ({ tone: "warning", children: "warning body" }) as Props,
};

/**
 * Catalog fixtures for ThemeToggle.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ThemeToggle } from "@/components/ThemeToggle";


type Props = ComponentProps<typeof ThemeToggle>;

export const STATES: Record<string, Props> = {
  default: ({}) as Props,
  medium: ({ emphasis: "medium" }) as Props,
};

/**
 * Catalog fixtures for ResponsiveShell.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ResponsiveShell } from "@/components/ResponsiveShell";


type Props = ComponentProps<typeof ResponsiveShell>;

export const STATES: Record<string, Props> = {
  main: ({ children: "main" }) as Props,
};

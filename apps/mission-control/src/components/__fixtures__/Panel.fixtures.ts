/**
 * Catalog fixtures for Panel.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { Panel } from "@/components/Panel";


type Props = ComponentProps<typeof Panel>;

export const STATES: Record<string, Props> = {
  default: ({ eyebrow: "eyebrow", title: "title", children: "body" }) as Props,
};

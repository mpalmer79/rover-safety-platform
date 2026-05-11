/**
 * Catalog fixtures for StatusPill.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { StatusPill } from "@/components/StatusPill";


type Props = ComponentProps<typeof StatusPill>;

export const STATES: Record<string, Props> = {
  completed: ({ label: "completed" }) as Props,
  rejected: ({ label: "rejected" }) as Props,
  aborted: ({ label: "aborted" }) as Props,
};

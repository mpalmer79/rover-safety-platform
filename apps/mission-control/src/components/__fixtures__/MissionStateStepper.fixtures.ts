/**
 * Catalog fixtures for MissionStateStepper.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { MissionStateStepper } from "@/components/MissionStateStepper";


type Props = ComponentProps<typeof MissionStateStepper>;

export const STATES: Record<string, Props> = {
  completed: ({ status: "completed" }) as Props,
  rejected: ({ status: "rejected", failureReason: "unsafe_speed" }) as Props,
};

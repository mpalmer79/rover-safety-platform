/**
 * Catalog fixtures for MissionPlaybackPanel.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { MissionPlaybackPanel } from "@/components/MissionPlaybackPanel";
import { FIX_PLAN, FIX_EVENT_INFO } from "./_shared";

type Props = ComponentProps<typeof MissionPlaybackPanel>;

export const STATES: Record<string, Props> = {
  plan_with_events: ({ plan: FIX_PLAN, events: [FIX_EVENT_INFO] }) as Props,
};

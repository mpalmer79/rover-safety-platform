/**
 * Catalog fixtures for ReplayTimeline.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ReplayTimeline } from "@/components/ReplayTimeline";
import { FIX_EVENT_INFO, FIX_EVENT_REJECTION } from "./_shared";

type Props = ComponentProps<typeof ReplayTimeline>;

export const STATES: Record<string, Props> = {
  two_events: ({ events: [FIX_EVENT_INFO, FIX_EVENT_REJECTION] }) as Props,
};

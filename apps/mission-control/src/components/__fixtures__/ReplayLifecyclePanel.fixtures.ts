/**
 * Catalog fixtures for ReplayLifecyclePanel.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ReplayLifecyclePanel } from "@/components/ReplayLifecyclePanel";
import { FIX_REGISTRY_RECORD } from "./_shared";

type Props = ComponentProps<typeof ReplayLifecyclePanel>;

export const STATES: Record<string, Props> = {
  canonical: ({ record: FIX_REGISTRY_RECORD }) as Props,
  no_record: ({ record: null }) as Props,
};

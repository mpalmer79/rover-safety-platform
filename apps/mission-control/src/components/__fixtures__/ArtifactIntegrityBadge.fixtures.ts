/**
 * Catalog fixtures for ArtifactIntegrityBadge.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { ArtifactIntegrityBadge } from "@/components/ArtifactIntegrityBadge";


type Props = ComponentProps<typeof ArtifactIntegrityBadge>;

export const STATES: Record<string, Props> = {
  passed: ({ integrity: "passed" }) as Props,
  partial: ({ integrity: "partial" }) as Props,
  failed: ({ integrity: "failed" }) as Props,
  missing: ({ integrity: "missing" }) as Props,
  unverified: ({ integrity: "unverified" }) as Props,
};

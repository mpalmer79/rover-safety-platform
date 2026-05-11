/**
 * Catalog fixtures for EvidenceLineageGraph.
 *
 * STATES exports one or more documented prop combinations the
 * catalog page renders. Adding a new state requires no other
 * registry edits — the catalog discovers states by Object.keys.
 */

import type { ComponentProps } from "react";

import { EvidenceLineageGraph } from "@/components/EvidenceLineageGraph";
import { FIX_SPATIAL_ARTIFACT, FIX_REGISTRY_RECORD } from "./_shared";

type Props = ComponentProps<typeof EvidenceLineageGraph>;

export const STATES: Record<string, Props> = {
  fixture: ({ artifact: FIX_SPATIAL_ARTIFACT, record: FIX_REGISTRY_RECORD }) as Props,
};

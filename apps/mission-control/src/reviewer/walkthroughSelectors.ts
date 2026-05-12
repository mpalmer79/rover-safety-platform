/**
 * Phase 20B walkthrough selectors.
 *
 * Pure functions used by the contextual walkthrough overlay to
 * resolve "which mission audit is in focus", "which spatial
 * replay backs it", and "which registry record describes it".
 *
 * The selectors NEVER fabricate values — when nothing matches,
 * they return ``null`` and the walkthrough renders the explicit
 * "no mission selected" branch.
 */

import type {
  ArtifactRegistryRecord,
  RehearsalAudit,
  SpatialReplayArtifact,
} from "@/adapters/types";

export interface WalkthroughSelectionInput {
  audits: readonly RehearsalAudit[];
  spatialByRunId?: Readonly<Record<string, SpatialReplayArtifact>>;
  registryByRunId?: Readonly<Record<string, ArtifactRegistryRecord>>;
  missionId: string | null;
}

export interface WalkthroughSelection {
  audit: RehearsalAudit | null;
  spatial: SpatialReplayArtifact | null;
  registry: ArtifactRegistryRecord | null;
}

export function selectFocusedAudit(
  input: WalkthroughSelectionInput,
): WalkthroughSelection {
  if (input.audits.length === 0) {
    return { audit: null, spatial: null, registry: null };
  }
  const audit =
    input.audits.find((a) => a.request.mission_id === input.missionId) ??
    input.audits[0];
  const runId = audit.request.request_id;
  return {
    audit,
    spatial: input.spatialByRunId?.[runId] ?? null,
    registry: input.registryByRunId?.[runId] ?? null,
  };
}

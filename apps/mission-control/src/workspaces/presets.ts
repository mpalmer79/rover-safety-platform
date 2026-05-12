/**
 * Phase 20 operator workspace presets.
 *
 * Six deterministic presets cover the full review surface. The
 * mapping is intentionally read-only and serialisable so the same
 * shape can be exported / linted by ``tests/workspace.test.tsx``.
 */

import type { WorkspacePreset, WorkspacePresetId } from "./types";

export const MISSION_REVIEW: WorkspacePreset = {
  id: "mission-review",
  title: "Mission Review",
  subtitle: "Validated mission plans against deterministic replay evidence.",
  audience: "Operator + reviewer",
  cameraMode: "follow",
  timelineMode: "scrubber",
  evidenceDensity: "summary",
  telemetryDensity: "operator",
  density: "standard",
  defaultMissionId: "warehouse_pickup_route_alpha",
  panels: [
    { panel: "mission-telemetry", colSpan: 6, rowSpan: 2, minHeight: 320 },
    { panel: "mission-health", colSpan: 6, rowSpan: 2, minHeight: 320 },
    { panel: "event-stream", colSpan: 6, rowSpan: 3 },
    { panel: "replay-clock", colSpan: 6, rowSpan: 1 },
    { panel: "pose-trace", colSpan: 6, rowSpan: 2 },
  ],
};

export const SAFETY_REVIEW: WorkspacePreset = {
  id: "safety-review",
  title: "Safety Review",
  subtitle: "Supervisor authority, rejection lineage, forbidden topics.",
  audience: "Safety case reviewer",
  cameraMode: "top-down",
  timelineMode: "stepper",
  evidenceDensity: "detailed",
  telemetryDensity: "operator",
  density: "standard",
  defaultMissionId: "warehouse_pickup_route_alpha",
  panels: [
    { panel: "supervisor-decision-log", colSpan: 7, rowSpan: 3 },
    { panel: "validation-outcome", colSpan: 5, rowSpan: 2 },
    { panel: "velocity-command", colSpan: 5, rowSpan: 2 },
    { panel: "topic-availability", colSpan: 6, rowSpan: 2 },
    { panel: "mission-health", colSpan: 6, rowSpan: 2 },
  ],
};

export const REPLAY_ANALYSIS: WorkspacePreset = {
  id: "replay-analysis",
  title: "Replay Analysis",
  subtitle: "Deterministic hash chain, scrub timeline, statistics.",
  audience: "Replay engineer",
  cameraMode: "follow",
  timelineMode: "scrubber",
  evidenceDensity: "raw",
  telemetryDensity: "engineer",
  density: "dense",
  defaultMissionId: "warehouse_pickup_route_alpha",
  panels: [
    { panel: "replay-clock", colSpan: 4, rowSpan: 1 },
    { panel: "replay-statistics", colSpan: 8, rowSpan: 2 },
    { panel: "event-stream", colSpan: 6, rowSpan: 3 },
    { panel: "pose-trace", colSpan: 6, rowSpan: 3 },
    { panel: "topic-availability", colSpan: 12, rowSpan: 2 },
  ],
};

export const EVIDENCE_AUDIT: WorkspacePreset = {
  id: "evidence-audit",
  title: "Evidence Audit",
  subtitle: "Artifact registry, integrity, derivation lineage.",
  audience: "Quality + compliance reviewer",
  cameraMode: "fixed",
  timelineMode: "hidden",
  evidenceDensity: "raw",
  telemetryDensity: "engineer",
  density: "dense",
  defaultMissionId: null,
  panels: [
    { panel: "evidence-integrity", colSpan: 8, rowSpan: 3 },
    { panel: "rehearsal-outcome", colSpan: 4, rowSpan: 3 },
    { panel: "validation-outcome", colSpan: 6, rowSpan: 2 },
    { panel: "supervisor-decision-log", colSpan: 6, rowSpan: 2 },
  ],
};

export const FLEET_READINESS: WorkspacePreset = {
  id: "fleet-readiness",
  title: "Fleet Readiness",
  subtitle: "Site-wide readiness derived from rehearsal artefacts.",
  audience: "Fleet operator",
  cameraMode: "top-down",
  timelineMode: "hidden",
  evidenceDensity: "summary",
  telemetryDensity: "summary",
  density: "comfortable",
  defaultMissionId: null,
  panels: [
    { panel: "fleet-overview", colSpan: 12, rowSpan: 2 },
    { panel: "site-map", colSpan: 8, rowSpan: 3 },
    { panel: "mission-queue", colSpan: 4, rowSpan: 3 },
    { panel: "robot-readiness", colSpan: 6, rowSpan: 2 },
    { panel: "zone-status", colSpan: 6, rowSpan: 2 },
  ],
};

export const REVIEWER_WALKTHROUGH: WorkspacePreset = {
  id: "reviewer-walkthrough",
  title: "Reviewer Walkthrough",
  subtitle: "Guided 10-step explanation of one canonical mission.",
  audience: "First-time reviewer",
  cameraMode: "orbit",
  timelineMode: "stepper",
  evidenceDensity: "summary",
  telemetryDensity: "summary",
  density: "comfortable",
  defaultMissionId: "warehouse_pickup_route_alpha",
  panels: [
    { panel: "walkthrough-overlay", colSpan: 12, rowSpan: 6, minHeight: 480 },
  ],
};

export const WORKSPACE_PRESETS: Readonly<
  Record<WorkspacePresetId, WorkspacePreset>
> = {
  "mission-review": MISSION_REVIEW,
  "safety-review": SAFETY_REVIEW,
  "replay-analysis": REPLAY_ANALYSIS,
  "evidence-audit": EVIDENCE_AUDIT,
  "fleet-readiness": FLEET_READINESS,
  "reviewer-walkthrough": REVIEWER_WALKTHROUGH,
};

export const WORKSPACE_PRESET_IDS: readonly WorkspacePresetId[] = [
  "mission-review",
  "safety-review",
  "replay-analysis",
  "evidence-audit",
  "fleet-readiness",
  "reviewer-walkthrough",
] as const;

export function workspacePreset(id: WorkspacePresetId): WorkspacePreset {
  return WORKSPACE_PRESETS[id];
}

export function isWorkspacePresetId(value: string): value is WorkspacePresetId {
  return (WORKSPACE_PRESET_IDS as readonly string[]).includes(value);
}

/**
 * Phase 20B canonical snapshot fixtures.
 *
 * Static fixtures used by the route renderer + tests + docs. The
 * fixtures NEVER include a wall-clock timestamp; every value is a
 * deterministic review reference.
 */

import { serializeWorkspaceSnapshot } from "./serializeWorkspaceSnapshot";
import type { WorkspaceSnapshotV1 } from "./models";

export const MISSION_REVIEW_SNAPSHOT: WorkspaceSnapshotV1 =
  serializeWorkspaceSnapshot({
    presetId: "mission-review",
    missionId: "warehouse_pickup_route_alpha",
    replayRunId: "canonical-fixture",
    selectedEventId: null,
    selectedPanelIds: [
      "mission-telemetry",
      "mission-health",
      "event-stream",
      "replay-clock",
      "pose-trace",
    ],
    walkthroughStep: null,
    cameraMode: "follow",
    evidenceFocus: {
      kind: "spatial-replay",
      ref: "spatial-replay/runs/canonical-fixture/spatial-replay.json",
    },
    theme: "dark",
    density: "standard",
    capturedAtUtc: null,
  });

export const SAFETY_REVIEW_SNAPSHOT: WorkspaceSnapshotV1 =
  serializeWorkspaceSnapshot({
    presetId: "safety-review",
    missionId: "warehouse_pickup_route_alpha",
    replayRunId: "canonical-fixture",
    selectedEventId: null,
    selectedPanelIds: [
      "supervisor-decision-log",
      "validation-outcome",
      "velocity-command",
      "topic-availability",
      "mission-health",
    ],
    walkthroughStep: null,
    cameraMode: "top-down",
    evidenceFocus: {
      kind: "supervisor-decision",
      ref: "mission-rehearsals/audits/warehouse_pickup_route_alpha/decision.json",
    },
    theme: "dark",
    density: "standard",
    capturedAtUtc: null,
  });

export const WALKTHROUGH_STEP_3_SNAPSHOT: WorkspaceSnapshotV1 =
  serializeWorkspaceSnapshot({
    presetId: "reviewer-walkthrough",
    missionId: "warehouse_pickup_route_alpha",
    replayRunId: "canonical-fixture",
    selectedEventId: null,
    selectedPanelIds: ["walkthrough-overlay"],
    walkthroughStep: 3,
    cameraMode: "orbit",
    evidenceFocus: {
      kind: "validation-diagnostics",
      ref: "mission-rehearsals/audits/warehouse_pickup_route_alpha/audit.json",
    },
    theme: "dark",
    density: "comfortable",
    capturedAtUtc: null,
  });

export const CANONICAL_SNAPSHOT_FIXTURES = {
  "mission-review": MISSION_REVIEW_SNAPSHOT,
  "safety-review": SAFETY_REVIEW_SNAPSHOT,
  "walkthrough-step-3": WALKTHROUGH_STEP_3_SNAPSHOT,
} as const;

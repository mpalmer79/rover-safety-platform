/**
 * Phase 20 operator workspace types.
 *
 * Workspaces are deterministic JSON-backed presets. They never carry
 * runtime layout state; the UI consumes the preset shape and
 * renders the declared panels at the declared positions.
 *
 * Honesty rules:
 *   * a preset never claims live telemetry — it points at panels
 *     that consume committed artefacts only;
 *   * a preset never persists drag/drop state — the JSON shape is
 *     the single source of truth.
 */

import type { Density } from "@/design-system/spacing";

export type WorkspacePresetId =
  | "mission-review"
  | "safety-review"
  | "replay-analysis"
  | "evidence-audit"
  | "fleet-readiness"
  | "reviewer-walkthrough";

export type WorkspacePanelId =
  | "mission-telemetry"
  | "supervisor-decision-log"
  | "replay-clock"
  | "event-stream"
  | "velocity-command"
  | "replay-statistics"
  | "mission-health"
  | "pose-trace"
  | "topic-availability"
  | "evidence-integrity"
  | "validation-outcome"
  | "rehearsal-outcome"
  | "fleet-overview"
  | "site-map"
  | "mission-queue"
  | "robot-readiness"
  | "zone-status"
  | "walkthrough-overlay";

export type CameraMode = "follow" | "orbit" | "top-down" | "fixed";
export type TimelineMode = "scrubber" | "stepper" | "stream" | "hidden";
export type EvidenceDensity = "summary" | "detailed" | "raw";
export type TelemetryDensity = "summary" | "operator" | "engineer";

export interface WorkspacePanelLayout {
  panel: WorkspacePanelId;
  /** Column span on desktop (1-12). */
  colSpan: number;
  /** Row span on desktop (1-6). */
  rowSpan: number;
  /** Optional minimum height in pixels. */
  minHeight?: number;
}

export interface WorkspacePreset {
  id: WorkspacePresetId;
  title: string;
  subtitle: string;
  panels: readonly WorkspacePanelLayout[];
  cameraMode: CameraMode;
  timelineMode: TimelineMode;
  evidenceDensity: EvidenceDensity;
  telemetryDensity: TelemetryDensity;
  density: Density;
  /** Default mission id to focus when entering the workspace. */
  defaultMissionId: string | null;
  /** Human-readable hint shown in the breadcrumb / topbar. */
  audience: string;
}

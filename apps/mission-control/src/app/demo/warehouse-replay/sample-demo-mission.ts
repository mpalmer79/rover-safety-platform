/**
 * Canonical demo-mission descriptor.
 *
 * This file is metadata only — it describes the curated public demo
 * mission and the warehouse zone overlays drawn under the trajectory.
 *
 * The mission run id and rehearsal id below MUST resolve to a
 * committed artifact under ``mission-rehearsals/audits/<id>/`` and
 * ``spatial-replay/runs/<id>/``. If either artifact is missing, the
 * server page falls back to the 2D narrative shell rather than
 * rendering an empty 3D scene.
 *
 * Coordinates in zone overlays are illustrative warehouse layout
 * hints. They are NOT surveyed coordinates. The rover position is
 * derived from the committed pose-sample artifact.
 */

export interface DemoMissionDescriptor {
  /** Rehearsal audit id (under mission-rehearsals/audits/). */
  rehearsalId: string;
  /** Spatial-replay run id (under spatial-replay/runs/). */
  spatialRunId: string;
  /** Reviewer-friendly title. */
  title: string;
  /** One-line subtitle. */
  subtitle: string;
  /** Plain-language summary shown above the scene. */
  summary: string;
  /** Zone overlays drawn under the trajectory. */
  zones: ReadonlyArray<{
    id: string;
    label: string;
    tone: "dock" | "aisle" | "exclusion" | "pickup";
    center: { x: number; y: number };
    half: { x: number; y: number };
  }>;
  /** Narrative beats keyed to a fractional position in the replay (0..1). */
  beats: ReadonlyArray<{
    /** Position along the deterministic timeline (0 = start, 1 = end). */
    at: number;
    title: string;
    description: string;
    tone: "info" | "validate" | "supervise" | "complete";
  }>;
}

export const DEMO_MISSION: DemoMissionDescriptor = {
  rehearsalId: "warehouse_pickup_route_alpha",
  spatialRunId: "canonical-fixture",
  title: "Warehouse pickup · route alpha",
  subtitle:
    "Approved bounded-pickup mission, replayed deterministically from committed evidence.",
  summary:
    "A simulated rover is dispatched from a dock pad, traverses an aisle to a pickup point, and returns. The rover only moves after the validator and safety supervisor approve the plan. Position, heading, and event timing come from the committed canonical fixture artifact under spatial-replay/runs/canonical-fixture/.",
  zones: [
    {
      id: "dock",
      label: "Dock A",
      tone: "dock",
      center: { x: 0, y: 0 },
      half: { x: 0.55, y: 0.55 },
    },
    {
      id: "aisle",
      label: "Aisle A",
      tone: "aisle",
      center: { x: 1.5, y: 0 },
      half: { x: 1.7, y: 0.45 },
    },
    {
      id: "pickup",
      label: "Pickup",
      tone: "pickup",
      center: { x: 3.0, y: 0 },
      half: { x: 0.4, y: 0.4 },
    },
    {
      id: "exclusion",
      label: "Restricted · Mezzanine",
      tone: "exclusion",
      center: { x: 1.5, y: 1.6 },
      half: { x: 2.2, y: 0.55 },
    },
  ],
  beats: [
    {
      at: 0.0,
      title: "Mission proposed",
      description:
        "An operator submits the bounded pickup mission. The sanitizer accepts it because no forbidden phrases are present.",
      tone: "info",
    },
    {
      at: 0.08,
      title: "Validator approves",
      description:
        "Each waypoint sits within the rover's ODD profile: bounded distance, bounded angle, bounded speed.",
      tone: "validate",
    },
    {
      at: 0.18,
      title: "Supervisor authorizes",
      description:
        "The runtime safety supervisor signs off the plan and the rehearsal state machine enters ‘rehearsing’.",
      tone: "supervise",
    },
    {
      at: 0.55,
      title: "Pickup waypoint reached",
      description:
        "The rover decelerates inside the pickup zone. The supervisor would intercept any deviation toward the restricted mezzanine.",
      tone: "info",
    },
    {
      at: 0.95,
      title: "Mission completes",
      description:
        "The rover returns to the dock pad. The rehearsal audit is sealed and traceable to its requirements.",
      tone: "complete",
    },
  ],
};

/**
 * Component → catalog group mapping.
 *
 * The catalog page groups components so a reviewer can navigate by
 * concern. Group membership lives here, not in each fixture file,
 * so it is easy to scan + adjust without touching component source.
 *
 * Source links point at the repo's main branch so the catalog's
 * "open in GitHub" links keep working as the working tree drifts.
 */

export type GroupId =
  | "safety_authority"
  | "mission"
  | "replay"
  | "evidence"
  | "spatial"
  | "chrome";

export interface GroupDef {
  id: GroupId;
  label: string;
  description: string;
}

export const GROUPS: ReadonlyArray<GroupDef> = [
  {
    id: "safety_authority",
    label: "Safety-authority components",
    description:
      "These describe or surface the supervisor's authority + the safety boundary. The platform's claim lives here.",
  },
  {
    id: "mission",
    label: "Mission components",
    description:
      "Mission state, lifecycle, and per-rehearsal cards.",
  },
  {
    id: "replay",
    label: "Replay components",
    description:
      "Timeline + scrubber + per-event surfaces over committed rehearsal events.",
  },
  {
    id: "evidence",
    label: "Evidence components",
    description:
      "Audit panels, hash chains, lineage graphs, snapshot readiness — everything that proves the run.",
  },
  {
    id: "spatial",
    label: "Spatial components",
    description:
      "2-D mission map, route lists, and the spatial-replay badge family.",
  },
  {
    id: "chrome",
    label: "Chrome / layout",
    description:
      "Page surfaces, the responsive shell, gradient panels, theme toggle, and similar non-data primitives.",
  },
];

/**
 * Single source of truth for which group each component belongs to.
 * Component names mirror the file basename under src/components/.
 */
export const COMPONENT_GROUP: Readonly<Record<string, GroupId>> = {
  SafetyBoundaryBanner: "safety_authority",
  SupervisorAuthorityPanel: "safety_authority",
  SupervisorInterventionOverlay: "safety_authority",
  CompilerDecisionCard: "safety_authority",
  SafetyZoneLayer: "safety_authority",
  ZoneBoundaryOverlay: "safety_authority",
  WhyRejectedDrilldown: "safety_authority",

  MissionCard: "mission",
  MissionStateStepper: "mission",
  MissionStoryPanel: "mission",
  MissionEventMarker: "mission",
  MissionPlaybackPanel: "mission",
  MissionRoute: "mission",
  MissionSpatialTimeline: "mission",
  MissionMap: "spatial",

  ReplayTimeline: "replay",
  ReplayScrubber: "replay",
  ReplayAnalyticsPanel: "replay",
  ReplayConfidencePanel: "replay",
  ReplayLifecyclePanel: "replay",

  AuditPanel: "evidence",
  CodeCard: "evidence",
  DeterministicHashChain: "evidence",
  DeterministicHashDisplay: "evidence",
  EvidenceLineageGraph: "evidence",
  EvidenceStatusChip: "evidence",
  GovernanceHealthPanel: "evidence",
  RequirementBadge: "evidence",
  RiskBandBadge: "evidence",
  SceneSnapshotPanel: "evidence",
  ArtifactIntegrityBadge: "evidence",
  StatusPill: "evidence",

  RouteProgressIndicator: "spatial",
  SpatialReplayBadge: "spatial",
  WarehouseLaneMap: "spatial",
  WaypointOverlay: "spatial",

  GradientPanel: "chrome",
  MermaidView: "chrome",
  PageSurface: "chrome",
  Panel: "chrome",
  ResponsiveGrid: "chrome",
  ResponsiveShell: "chrome",
  SiteNav: "chrome",
  ThemeToggle: "chrome",
};

export const REPO_MAIN_BLOB =
  "https://github.com/mpalmer79/rover-safety-platform/blob/main";

export function sourceLink(componentName: string): string {
  return `${REPO_MAIN_BLOB}/apps/mission-control/src/components/${componentName}.tsx`;
}

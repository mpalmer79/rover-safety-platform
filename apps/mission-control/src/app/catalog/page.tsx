/**
 * Component catalog (Item 5, permanent).
 *
 * Renders every component under src/components/ with its documented
 * state variants from src/components/__fixtures__/<Name>.fixtures.ts.
 * The Playwright visual-regression suite screenshots each card.
 *
 * Honesty rules:
 *   - The state-variant labels and props come from the fixtures
 *     file VERBATIM. No fixture data is invented at render time.
 *   - The catalog is grouped by concern (see __fixtures__/_groups.ts);
 *     reviewers see safety-authority components first.
 */

import Link from "next/link";
import type { ReactNode } from "react";

import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

import { ArtifactIntegrityBadge } from "@/components/ArtifactIntegrityBadge";
import { AuditPanel } from "@/components/AuditPanel";
import { CodeCard } from "@/components/CodeCard";
import { CompilerDecisionCard } from "@/components/CompilerDecisionCard";
import { DeterministicHashChain } from "@/components/DeterministicHashChain";
import { DeterministicHashDisplay } from "@/components/DeterministicHashDisplay";
import { EvidenceLineageGraph } from "@/components/EvidenceLineageGraph";
import { EvidenceStatusChip } from "@/components/EvidenceStatusChip";
import { GovernanceHealthPanel } from "@/components/GovernanceHealthPanel";
import { MermaidView } from "@/components/MermaidView";
import { MissionCard } from "@/components/MissionCard";
import { MissionEventMarker } from "@/components/MissionEventMarker";
import { MissionMap } from "@/components/MissionMap";
import { MissionPlaybackPanel } from "@/components/MissionPlaybackPanel";
import { MissionRouteList } from "@/components/MissionRoute";
import { MissionSpatialTimeline } from "@/components/MissionSpatialTimeline";
import { MissionStateStepper } from "@/components/MissionStateStepper";
import { MissionStoryPanel } from "@/components/MissionStoryPanel";
import { ReplayAnalyticsPanel } from "@/components/ReplayAnalyticsPanel";
import { ReplayConfidencePanel } from "@/components/ReplayConfidencePanel";
import { ReplayLifecyclePanel } from "@/components/ReplayLifecyclePanel";
import { ReplayScrubber } from "@/components/ReplayScrubber";
import { ReplayTimeline } from "@/components/ReplayTimeline";
import { RequirementBadge } from "@/components/RequirementBadge";
import { ResponsiveGrid } from "@/components/ResponsiveGrid";
import { RiskBandBadge } from "@/components/RiskBandBadge";
import { RouteProgressIndicator } from "@/components/RouteProgressIndicator";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";
import { SafetyZoneLayer } from "@/components/SafetyZoneLayer";
import { SceneSnapshotPanel } from "@/components/SceneSnapshotPanel";
import { SpatialReplayBadge } from "@/components/SpatialReplayBadge";
import { StatusPill } from "@/components/StatusPill";
import { SupervisorAuthorityPanel } from "@/components/SupervisorAuthorityPanel";
import { SupervisorInterventionOverlay } from "@/components/SupervisorInterventionOverlay";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WarehouseLaneMap } from "@/components/WarehouseLaneMap";
import { WaypointOverlay } from "@/components/WaypointOverlay";
import { WhyRejectedDrilldown } from "@/components/WhyRejectedDrilldown";
import { ZoneBoundaryOverlay } from "@/components/ZoneBoundaryOverlay";

import { STATES as GradientPanelStates } from "@/components/__fixtures__/GradientPanel.fixtures";
import { STATES as PageSurfaceStates } from "@/components/__fixtures__/PageSurface.fixtures";
import { STATES as PanelStates } from "@/components/__fixtures__/Panel.fixtures";
import { STATES as ArtifactIntegrityBadgeStates } from "@/components/__fixtures__/ArtifactIntegrityBadge.fixtures";
import { STATES as AuditPanelStates } from "@/components/__fixtures__/AuditPanel.fixtures";
import { STATES as CodeCardStates } from "@/components/__fixtures__/CodeCard.fixtures";
import { STATES as CompilerDecisionCardStates } from "@/components/__fixtures__/CompilerDecisionCard.fixtures";
import { STATES as DeterministicHashChainStates } from "@/components/__fixtures__/DeterministicHashChain.fixtures";
import { STATES as DeterministicHashDisplayStates } from "@/components/__fixtures__/DeterministicHashDisplay.fixtures";
import { STATES as EvidenceLineageGraphStates } from "@/components/__fixtures__/EvidenceLineageGraph.fixtures";
import { STATES as EvidenceStatusChipStates } from "@/components/__fixtures__/EvidenceStatusChip.fixtures";
import { STATES as GovernanceHealthPanelStates } from "@/components/__fixtures__/GovernanceHealthPanel.fixtures";
import { STATES as MermaidViewStates } from "@/components/__fixtures__/MermaidView.fixtures";
import { STATES as MissionCardStates } from "@/components/__fixtures__/MissionCard.fixtures";
import { STATES as MissionEventMarkerStates } from "@/components/__fixtures__/MissionEventMarker.fixtures";
import { STATES as MissionMapStates } from "@/components/__fixtures__/MissionMap.fixtures";
import { STATES as MissionPlaybackPanelStates } from "@/components/__fixtures__/MissionPlaybackPanel.fixtures";
import { STATES as MissionRouteStates } from "@/components/__fixtures__/MissionRoute.fixtures";
import { STATES as MissionSpatialTimelineStates } from "@/components/__fixtures__/MissionSpatialTimeline.fixtures";
import { STATES as MissionStateStepperStates } from "@/components/__fixtures__/MissionStateStepper.fixtures";
import { STATES as MissionStoryPanelStates } from "@/components/__fixtures__/MissionStoryPanel.fixtures";
import { STATES as ReplayAnalyticsPanelStates } from "@/components/__fixtures__/ReplayAnalyticsPanel.fixtures";
import { STATES as ReplayConfidencePanelStates } from "@/components/__fixtures__/ReplayConfidencePanel.fixtures";
import { STATES as ReplayLifecyclePanelStates } from "@/components/__fixtures__/ReplayLifecyclePanel.fixtures";
import { STATES as ReplayScrubberStates } from "@/components/__fixtures__/ReplayScrubber.fixtures";
import { STATES as ReplayTimelineStates } from "@/components/__fixtures__/ReplayTimeline.fixtures";
import { STATES as RequirementBadgeStates } from "@/components/__fixtures__/RequirementBadge.fixtures";
import { STATES as ResponsiveGridStates } from "@/components/__fixtures__/ResponsiveGrid.fixtures";
import { STATES as RiskBandBadgeStates } from "@/components/__fixtures__/RiskBandBadge.fixtures";
import { STATES as RouteProgressIndicatorStates } from "@/components/__fixtures__/RouteProgressIndicator.fixtures";
import { STATES as SafetyBoundaryBannerStates } from "@/components/__fixtures__/SafetyBoundaryBanner.fixtures";
import { STATES as SafetyZoneLayerStates } from "@/components/__fixtures__/SafetyZoneLayer.fixtures";
import { STATES as SceneSnapshotPanelStates } from "@/components/__fixtures__/SceneSnapshotPanel.fixtures";
import { STATES as SpatialReplayBadgeStates } from "@/components/__fixtures__/SpatialReplayBadge.fixtures";
import { STATES as StatusPillStates } from "@/components/__fixtures__/StatusPill.fixtures";
import { STATES as SupervisorAuthorityPanelStates } from "@/components/__fixtures__/SupervisorAuthorityPanel.fixtures";
import { STATES as SupervisorInterventionOverlayStates } from "@/components/__fixtures__/SupervisorInterventionOverlay.fixtures";
import { STATES as ThemeToggleStates } from "@/components/__fixtures__/ThemeToggle.fixtures";
import { STATES as WarehouseLaneMapStates } from "@/components/__fixtures__/WarehouseLaneMap.fixtures";
import { STATES as WaypointOverlayStates } from "@/components/__fixtures__/WaypointOverlay.fixtures";
import { STATES as WhyRejectedDrilldownStates } from "@/components/__fixtures__/WhyRejectedDrilldown.fixtures";
import { STATES as ZoneBoundaryOverlayStates } from "@/components/__fixtures__/ZoneBoundaryOverlay.fixtures";

import {
  COMPONENT_GROUP,
  GROUPS,
  sourceLink,
  type GroupId,
} from "@/components/__fixtures__/_groups";

export const dynamic = "force-static";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type CatalogProps = any;

interface EntryDef {
  name: string;
  description: string;
  Component: (props: CatalogProps) => ReactNode;
  states: Record<string, CatalogProps>;
}

function entry<P>(
  name: string,
  description: string,
  Component: (props: P) => ReactNode,
  states: Record<string, P>,
): EntryDef {
  return {
    name,
    description,
    Component: Component as (props: CatalogProps) => ReactNode,
    states: states as Record<string, CatalogProps>,
  };
}

// Each entry pairs a component with its STATES record. The catalog
// renders each state under its labeled key. Props are typed
// heterogeneously across entries; the per-state shape is enforced
// at the fixture-file level.
const ENTRIES: ReadonlyArray<EntryDef> = [
  // ──────────────────────────────────────────────────────────────────
  // safety_authority
  // ──────────────────────────────────────────────────────────────────
  entry(
    "SafetyBoundaryBanner",
    "Top-of-page banner that asserts the simulation-only boundary.",
    SafetyBoundaryBanner,
    SafetyBoundaryBannerStates,
  ),
  entry(
    "SupervisorAuthorityPanel",
    "Authority panel showing the supervisor decision + rationale.",
    SupervisorAuthorityPanel,
    SupervisorAuthorityPanelStates,
  ),
  entry(
    "SupervisorInterventionOverlay",
    "Lists supervisor + safety rejection events from the rehearsal stream.",
    SupervisorInterventionOverlay,
    SupervisorInterventionOverlayStates,
  ),
  entry(
    "CompilerDecisionCard",
    "Compiler / validator decision card.",
    CompilerDecisionCard,
    CompilerDecisionCardStates,
  ),
  entry(
    "SafetyZoneLayer",
    "Lists safety topic + constraint layers from the mission plan.",
    SafetyZoneLayer,
    SafetyZoneLayerStates,
  ),
  entry(
    "ZoneBoundaryOverlay",
    "Lists boundary-related rejections for the audit.",
    ZoneBoundaryOverlay,
    ZoneBoundaryOverlayStates,
  ),
  entry(
    "WhyRejectedDrilldown",
    "Drilldown explaining why a rejected mission was rejected.",
    WhyRejectedDrilldown,
    WhyRejectedDrilldownStates,
  ),
  // ──────────────────────────────────────────────────────────────────
  // mission
  // ──────────────────────────────────────────────────────────────────
  entry("MissionCard", "Rehearsal mission card.", MissionCard, MissionCardStates),
  entry(
    "MissionStateStepper",
    "Mission lifecycle stepper.",
    MissionStateStepper,
    MissionStateStepperStates,
  ),
  entry(
    "MissionStoryPanel",
    "Narrative walkthrough of a mission's lifecycle.",
    MissionStoryPanel,
    MissionStoryPanelStates,
  ),
  entry(
    "MissionEventMarker",
    "Severity-coded event marker / legend swatch.",
    MissionEventMarker,
    MissionEventMarkerStates,
  ),
  entry(
    "MissionPlaybackPanel",
    "Tactical map + scrubber + progress strip composite.",
    MissionPlaybackPanel,
    MissionPlaybackPanelStates,
  ),
  entry(
    "MissionRoute",
    "Waypoint list rendered from the derived route.",
    MissionRouteList,
    MissionRouteStates,
  ),
  entry(
    "MissionSpatialTimeline",
    "Coloured stripe of event types over the rehearsal duration.",
    MissionSpatialTimeline,
    MissionSpatialTimelineStates,
  ),
  // ──────────────────────────────────────────────────────────────────
  // replay
  // ──────────────────────────────────────────────────────────────────
  entry(
    "ReplayTimeline",
    "Per-event timeline rendered from the audit's event stream.",
    ReplayTimeline,
    ReplayTimelineStates,
  ),
  entry(
    "ReplayScrubber",
    "Deterministic sequence-based scrubber.",
    ReplayScrubber,
    ReplayScrubberStates,
  ),
  entry(
    "ReplayAnalyticsPanel",
    "Per-mission replay analytics summary.",
    ReplayAnalyticsPanel,
    ReplayAnalyticsPanelStates,
  ),
  entry(
    "ReplayConfidencePanel",
    "Confidence band derived from derivation_source + integrity.",
    ReplayConfidencePanel,
    ReplayConfidencePanelStates,
  ),
  entry(
    "ReplayLifecyclePanel",
    "Lifecycle ladder for the registered artefact.",
    ReplayLifecyclePanel,
    ReplayLifecyclePanelStates,
  ),
  // ──────────────────────────────────────────────────────────────────
  // evidence
  // ──────────────────────────────────────────────────────────────────
  entry(
    "AuditPanel",
    "Audit panel with request + decision + safety status.",
    AuditPanel,
    AuditPanelStates,
  ),
  entry("CodeCard", "Skill candidate code card.", CodeCard, CodeCardStates),
  entry(
    "DeterministicHashChain",
    "Per-file sha256 chain for a registered artefact.",
    DeterministicHashChain,
    DeterministicHashChainStates,
  ),
  entry(
    "DeterministicHashDisplay",
    "Display a single deterministic hash with short + long forms.",
    DeterministicHashDisplay,
    DeterministicHashDisplayStates,
  ),
  entry(
    "EvidenceLineageGraph",
    "Source-to-render lineage for a spatial-replay artefact.",
    EvidenceLineageGraph,
    EvidenceLineageGraphStates,
  ),
  entry(
    "EvidenceStatusChip",
    "Evidence status chip preserving bag-backed input verbatim.",
    EvidenceStatusChip,
    EvidenceStatusChipStates,
  ),
  entry(
    "GovernanceHealthPanel",
    "Governance health summary across rehearsal audits.",
    GovernanceHealthPanel,
    GovernanceHealthPanelStates,
  ),
  entry(
    "RequirementBadge",
    "Requirement coverage badge.",
    RequirementBadge,
    RequirementBadgeStates,
  ),
  entry("RiskBandBadge", "Risk band badge.", RiskBandBadge, RiskBandBadgeStates),
  entry(
    "SceneSnapshotPanel",
    "Reviewer scene-snapshot readiness panel.",
    SceneSnapshotPanel,
    SceneSnapshotPanelStates,
  ),
  entry(
    "ArtifactIntegrityBadge",
    "Artifact integrity badge.",
    ArtifactIntegrityBadge,
    ArtifactIntegrityBadgeStates,
  ),
  entry("StatusPill", "Status pill.", StatusPill, StatusPillStates),
  // ──────────────────────────────────────────────────────────────────
  // spatial
  // ──────────────────────────────────────────────────────────────────
  entry(
    "MissionMap",
    "Deterministic 2-D mission map.",
    MissionMap,
    MissionMapStates,
  ),
  entry(
    "RouteProgressIndicator",
    "Horizontal waypoint-progress strip.",
    RouteProgressIndicator,
    RouteProgressIndicatorStates,
  ),
  entry(
    "SpatialReplayBadge",
    "Derivation-source badge.",
    SpatialReplayBadge,
    SpatialReplayBadgeStates,
  ),
  entry(
    "WarehouseLaneMap",
    "Illustrative warehouse lane map (not bag-backed).",
    WarehouseLaneMap,
    WarehouseLaneMapStates,
  ),
  entry(
    "WaypointOverlay",
    "Selected-waypoint detail card.",
    WaypointOverlay,
    WaypointOverlayStates,
  ),
  // ──────────────────────────────────────────────────────────────────
  // chrome
  // ──────────────────────────────────────────────────────────────────
  entry(
    "GradientPanel",
    "Single-source gradient panel; four tones.",
    GradientPanel,
    GradientPanelStates,
  ),
  entry("MermaidView", "Client-side Mermaid renderer with raw-source fallback.", MermaidView, MermaidViewStates),
  entry(
    "PageSurface",
    "Outer page wrapper; mobile-first padding + max-width cap.",
    PageSurface,
    PageSurfaceStates,
  ),
  entry("Panel", "Standard surface for grouped content.", Panel, PanelStates),
  entry(
    "ResponsiveGrid",
    "Predictable responsive grid (three shapes).",
    ResponsiveGrid,
    ResponsiveGridStates,
  ),
  // ResponsiveShell omitted: it renders the entire layout chrome
  // including SiteNav, which already exists on the catalog page.
  // Rendering it inside a card would double-mount the shell.
  // SiteNav rendered separately below for the same reason.
  entry(
    "ThemeToggle",
    "Light / dark toggle.",
    ThemeToggle,
    ThemeToggleStates,
  ),
];

// Static catalog cards for layout primitives whose typed STATES
// would require a circular import (ResponsiveShell renders the
// catalog page; SiteNav lives inside it). Render placeholders.
const CHROME_PLACEHOLDERS: ReadonlyArray<{ name: string; description: string }> = [
  {
    name: "ResponsiveShell",
    description:
      "Sidebar / mobile drawer / responsive shell. Wraps every page; rendered around the catalog itself.",
  },
  {
    name: "SiteNav",
    description:
      "Primary navigation. Visible on the left rail of this page.",
  },
];

function groupForEntry(entryName: string): GroupId {
  return COMPONENT_GROUP[entryName] ?? "chrome";
}

interface CardProps {
  entry: EntryDef;
}

function CatalogCard({ entry }: CardProps) {
  const stateLabels = Object.keys(entry.states);
  const Component = entry.Component;
  return (
    <Panel
      eyebrow="component"
      title={entry.name}
      trailing={
        <Link
          href={sourceLink(entry.name)}
          target="_blank"
          rel="noreferrer"
          className="text-[11px] font-mono underline text-muted"
        >
          source
        </Link>
      }
    >
      <div
        data-testid={`catalog-card-${entry.name}`}
        className="space-y-3"
      >
        <p className="text-muted text-sm">{entry.description}</p>
        {stateLabels.length === 0 ? (
          <div className="rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] p-4">
            <Component />
          </div>
        ) : (
          stateLabels.map((stateName) => (
            <div
              key={stateName}
              data-testid={`catalog-state-${entry.name}-${stateName}`}
              className="rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] p-4"
            >
              <p className="label mb-2">{stateName}</p>
              <Component {...entry.states[stateName]} />
            </div>
          ))
        )}
      </div>
    </Panel>
  );
}

export default function CatalogPage() {
  return (
    <PageSurface>
      <GradientPanel elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="space-y-1">
          <p className="label">Component catalog</p>
          <h1 className="display-1">Components</h1>
          <p className="text-muted text-sm sm:text-base">
            Every component under{" "}
            <code>apps/mission-control/src/components/</code> in its
            documented state variants. State fixtures live next to
            the components at{" "}
            <code>src/components/__fixtures__/&lt;Name&gt;.fixtures.ts</code>;
            adding a new component requires a matching fixture file
            (enforced by <code>tests/honesty.test.ts</code>).
          </p>
        </header>
      </GradientPanel>

      {GROUPS.map((group) => {
        const groupEntries = ENTRIES.filter(
          (e) => groupForEntry(e.name) === group.id,
        );
        if (groupEntries.length === 0 && group.id !== "chrome") return null;
        return (
          <section
            key={group.id}
            data-testid={`catalog-group-${group.id}`}
            className="mt-6"
          >
            <h2 className="display-2">{group.label}</h2>
            <p className="text-muted text-sm">{group.description}</p>
            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {groupEntries.map((e) => (
                <CatalogCard key={e.name} entry={e} />
              ))}
              {group.id === "chrome"
                ? CHROME_PLACEHOLDERS.map((p) => (
                    <Panel
                      key={p.name}
                      eyebrow="component"
                      title={p.name}
                      trailing={
                        <Link
                          href={sourceLink(p.name)}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] font-mono underline text-muted"
                        >
                          source
                        </Link>
                      }
                    >
                      <div data-testid={`catalog-card-${p.name}`}>
                        <p className="text-muted text-sm">{p.description}</p>
                      </div>
                    </Panel>
                  ))
                : null}
            </div>
          </section>
        );
      })}
    </PageSurface>
  );
}

/**
 * Mission Control accessibility gate (Item 3).
 *
 * Imports every component from src/components/ and renders each with
 * a minimal valid props set. axe() must report zero violations on
 * every render.
 *
 * Honesty rules:
 *   * Each component is imported by name; the honesty test in
 *     tests/honesty.test.ts asserts every file in src/components/
 *     is referenced here. This prevents a future component from
 *     escaping the gate.
 *   * A11y violations that cannot be fixed in this session without
 *     a behaviour change are listed in EXCEPTIONS below with the
 *     WCAG rule waived and the reason.
 *
 * Static lint (eslint-plugin-jsx-a11y) is NOT a substitute for a
 * rendered axe pass.
 */

import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { axe } from "jest-axe";
import type { ReactNode } from "react";

// Mock next/navigation so components using `usePathname` (SiteNav,
// ResponsiveShell) render outside the Next.js router context.
// This isolates a11y assertions from router state.
vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

import { ThemeProvider } from "@/lib/theme-provider";

import { ArtifactIntegrityBadge } from "@/components/ArtifactIntegrityBadge";
import { AuditPanel } from "@/components/AuditPanel";
import { CodeCard } from "@/components/CodeCard";
import { CompilerDecisionCard } from "@/components/CompilerDecisionCard";
import { DeterministicHashChain } from "@/components/DeterministicHashChain";
import { DeterministicHashDisplay } from "@/components/DeterministicHashDisplay";
import { EvidenceLineageGraph } from "@/components/EvidenceLineageGraph";
import { EvidenceStatusChip } from "@/components/EvidenceStatusChip";
import { GovernanceHealthPanel } from "@/components/GovernanceHealthPanel";
import { GradientPanel } from "@/components/GradientPanel";
import { MermaidView } from "@/components/MermaidView";
import { MissionCard } from "@/components/MissionCard";
import { MissionEventMarker } from "@/components/MissionEventMarker";
import { MissionMap } from "@/components/MissionMap";
import { MissionPlaybackPanel } from "@/components/MissionPlaybackPanel";
import { MissionRouteList } from "@/components/MissionRoute";
import { MissionSpatialTimeline } from "@/components/MissionSpatialTimeline";
import { MissionStateStepper } from "@/components/MissionStateStepper";
import { MissionStoryPanel } from "@/components/MissionStoryPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";
import { ReplayAnalyticsPanel } from "@/components/ReplayAnalyticsPanel";
import { ReplayConfidencePanel } from "@/components/ReplayConfidencePanel";
import { ReplayLifecyclePanel } from "@/components/ReplayLifecyclePanel";
import { ReplayScrubber } from "@/components/ReplayScrubber";
import { ReplayTimeline } from "@/components/ReplayTimeline";
import { RequirementBadge } from "@/components/RequirementBadge";
import { ResponsiveGrid } from "@/components/ResponsiveGrid";
import { ResponsiveShell } from "@/components/ResponsiveShell";
import { RiskBandBadge } from "@/components/RiskBandBadge";
import { RouteProgressIndicator } from "@/components/RouteProgressIndicator";
import { SafetyBoundaryBanner } from "@/components/SafetyBoundaryBanner";
import { SafetyZoneLayer } from "@/components/SafetyZoneLayer";
import { SceneSnapshotPanel } from "@/components/SceneSnapshotPanel";
import { SiteNav } from "@/components/SiteNav";
import { SpatialReplayBadge } from "@/components/SpatialReplayBadge";
import { StatusPill } from "@/components/StatusPill";
import { SupervisorAuthorityPanel } from "@/components/SupervisorAuthorityPanel";
import { SupervisorInterventionOverlay } from "@/components/SupervisorInterventionOverlay";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WarehouseLaneMap } from "@/components/WarehouseLaneMap";
import { WaypointOverlay } from "@/components/WaypointOverlay";
import { WhyRejectedDrilldown } from "@/components/WhyRejectedDrilldown";
import { ZoneBoundaryOverlay } from "@/components/ZoneBoundaryOverlay";

import {
  BASE_AUDIT,
  REGISTRY_RECORD,
  REHEARSAL_EVENT_INFO,
  REHEARSAL_EVENT_REJECTION,
  SAMPLE_PLAN,
  SAMPLE_ROUTE,
  SPATIAL_ARTIFACT,
  SUPERVISOR_DECISION,
} from "./a11y-fixtures";

interface A11yCase {
  name: string;
  render: () => ReactNode;
  /** Per-component axe rule waivers. Document the rule + reason. */
  waivers?: string[];
}

const wrap = (node: ReactNode): ReactNode => (
  <ThemeProvider>{node}</ThemeProvider>
);

// ---------------------------------------------------------------------
// EXCEPTIONS — documented axe rule waivers.
//
// Format: { component, rule, reason }. The exception list starts
// empty. Adding an entry requires a written reason; do not add
// entries to silence a fixable violation.
// ---------------------------------------------------------------------
const EXCEPTIONS: ReadonlyArray<{
  component: string;
  rule: string;
  reason: string;
}> = [];

function rulesForComponent(name: string): { rules: Record<string, { enabled: boolean }> } {
  const rules: Record<string, { enabled: boolean }> = {};
  for (const ex of EXCEPTIONS) {
    if (ex.component === name) rules[ex.rule] = { enabled: false };
  }
  return { rules };
}

const CASES: A11yCase[] = [
  { name: "ArtifactIntegrityBadge", render: () => <ArtifactIntegrityBadge integrity="passed" /> },
  { name: "AuditPanel", render: () => <AuditPanel audit={BASE_AUDIT} /> },
  { name: "CodeCard", render: () => <CodeCard skill={{
      skill_id: "s",
      skill_type: "move_forward_distance",
      language: "python_ros2",
      title: "title",
      subtitle: "subtitle",
      risk_band: "guarded",
      safety_status: "safe_after_validation",
      generated_at_utc: "",
      code: "publisher.publish(Twist())",
      code_card: { safety_badges: [], animation_steps: [] },
    }} /> },
  { name: "CompilerDecisionCard", render: () => <CompilerDecisionCard diagnostics={[
    { code: "unsafe_speed", severity: "rejection", message: "too fast" },
  ]} /> },
  { name: "DeterministicHashChain", render: () => <DeterministicHashChain files={REGISTRY_RECORD.files} /> },
  { name: "DeterministicHashDisplay", render: () => <DeterministicHashDisplay label="plan" hash={"a".repeat(64)} /> },
  { name: "EvidenceLineageGraph", render: () => <EvidenceLineageGraph artifact={SPATIAL_ARTIFACT} record={REGISTRY_RECORD} /> },
  { name: "EvidenceStatusChip", render: () => <EvidenceStatusChip status="simulated" bagBacked={false} /> },
  { name: "GovernanceHealthPanel", render: () => <GovernanceHealthPanel audits={[BASE_AUDIT]} traceability={null} /> },
  { name: "GradientPanel", render: () => <GradientPanel>panel body</GradientPanel> },
  { name: "MermaidView", render: () => <MermaidView source={"graph TD; A-->B"} /> },
  { name: "MissionCard", render: () => <MissionCard audit={BASE_AUDIT} /> },
  { name: "MissionEventMarker", render: () => <MissionEventMarker severity="warning" label="warning" /> },
  { name: "MissionMap", render: () => <MissionMap route={SAMPLE_ROUTE} /> },
  { name: "MissionPlaybackPanel", render: () => <MissionPlaybackPanel plan={SAMPLE_PLAN} events={[REHEARSAL_EVENT_INFO]} /> },
  { name: "MissionRoute", render: () => <MissionRouteList route={SAMPLE_ROUTE} /> },
  { name: "MissionSpatialTimeline", render: () => <MissionSpatialTimeline events={[REHEARSAL_EVENT_INFO]} /> },
  { name: "MissionStateStepper", render: () => <MissionStateStepper status="completed" /> },
  { name: "MissionStoryPanel", render: () => <MissionStoryPanel audit={BASE_AUDIT} /> },
  { name: "PageSurface", render: () => <PageSurface><p>content</p></PageSurface> },
  { name: "Panel", render: () => <Panel eyebrow="eyebrow" title="title">body</Panel> },
  { name: "ReplayAnalyticsPanel", render: () => <ReplayAnalyticsPanel analytics={null} /> },
  { name: "ReplayConfidencePanel", render: () => <ReplayConfidencePanel artifact={SPATIAL_ARTIFACT} record={REGISTRY_RECORD} /> },
  { name: "ReplayLifecyclePanel", render: () => <ReplayLifecyclePanel record={REGISTRY_RECORD} /> },
  { name: "ReplayScrubber", render: () => <ReplayScrubber events={[REHEARSAL_EVENT_INFO]} /> },
  { name: "ReplayTimeline", render: () => <ReplayTimeline events={[REHEARSAL_EVENT_INFO]} /> },
  { name: "RequirementBadge", render: () => <RequirementBadge reqId="REQ-SAFE-001" status="passed" /> },
  { name: "ResponsiveGrid", render: () => <ResponsiveGrid><div>cell</div></ResponsiveGrid> },
  { name: "ResponsiveShell", render: () => <ResponsiveShell><p>main</p></ResponsiveShell> },
  { name: "RiskBandBadge", render: () => <RiskBandBadge band="guarded" /> },
  { name: "RouteProgressIndicator", render: () => <RouteProgressIndicator route={SAMPLE_ROUTE} /> },
  { name: "SafetyBoundaryBanner", render: () => <SafetyBoundaryBanner /> },
  { name: "SafetyZoneLayer", render: () => <SafetyZoneLayer plan={SAMPLE_PLAN} /> },
  { name: "SceneSnapshotPanel", render: () => <SceneSnapshotPanel runId="r" artifact={SPATIAL_ARTIFACT} record={REGISTRY_RECORD} /> },
  { name: "SiteNav", render: () => <SiteNav /> },
  { name: "SpatialReplayBadge", render: () => <SpatialReplayBadge source="fixture" /> },
  { name: "StatusPill", render: () => <StatusPill label="completed" /> },
  { name: "SupervisorAuthorityPanel", render: () => <SupervisorAuthorityPanel decision={SUPERVISOR_DECISION} /> },
  { name: "SupervisorInterventionOverlay", render: () => <SupervisorInterventionOverlay events={[REHEARSAL_EVENT_REJECTION]} /> },
  { name: "ThemeToggle", render: () => <ThemeToggle /> },
  { name: "WarehouseLaneMap", render: () => <WarehouseLaneMap /> },
  { name: "WaypointOverlay", render: () => <WaypointOverlay waypoint={SAMPLE_ROUTE.waypoints[0]} /> },
  { name: "WhyRejectedDrilldown", render: () => <WhyRejectedDrilldown audit={BASE_AUDIT} /> },
  { name: "ZoneBoundaryOverlay", render: () => <ZoneBoundaryOverlay audit={BASE_AUDIT} /> },
];

describe("axe a11y gate", () => {
  it.each(CASES)("$name has no axe violations", async ({ name, render: r }) => {
    const { container } = render(wrap(r()));
    const results = await axe(container, rulesForComponent(name));
    expect(results).toHaveNoViolations();
  });
});

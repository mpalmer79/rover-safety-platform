import { notFound } from "next/navigation";

import {
  loadArtifactRegistry,
  loadRehearsalAudits,
  loadSpatialReplay,
  loadTraceability,
} from "@/adapters/loader";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  EventStreamPanel,
  EvidenceIntegrityPanel,
  MissionHealthPanel,
  MissionTelemetryPanel,
  PoseTracePanel,
  RehearsalOutcomePanel,
  ReplayClockPanel,
  ReplayStatisticsPanel,
  SupervisorDecisionLog,
  TopicAvailabilityPanel,
  ValidationOutcomePanel,
  VelocityCommandPanel,
} from "@/components/telemetry";
import { ReviewerWalkthroughOverlay } from "@/reviewer/components/ReviewerWalkthroughOverlay";
import {
  CANONICAL_SITE,
  REFERENCE_ZONE_STATUS,
  buildMissionQueue,
  deriveRobotReadiness,
} from "@/site";
import {
  FleetOverviewPanel,
  MissionQueuePanel,
  RobotReadinessCard,
  SiteMapOverview,
  ZoneStatusPanel,
} from "@/site/components";
import {
  WORKSPACE_PRESET_IDS,
  isWorkspacePresetId,
  workspacePreset,
} from "@/workspaces/presets";
import { WorkspaceBreadcrumbs } from "@/workspaces/components/WorkspaceBreadcrumbs";
import { WorkspacePanelGrid } from "@/workspaces/components/WorkspacePanelGrid";
import { WorkspaceShell } from "@/workspaces/components/WorkspaceShell";
import { WorkspaceStatusStrip } from "@/workspaces/components/WorkspaceStatusStrip";
import { WorkspaceTopbar } from "@/workspaces/components/WorkspaceTopbar";
import type { WorkspacePanelId } from "@/workspaces/types";

export const dynamic = "force-static";

export function generateStaticParams() {
  return WORKSPACE_PRESET_IDS.map((id) => ({ preset: id }));
}

interface PageProps {
  params: { preset: string };
}

export default async function WorkspacePresetPage({ params }: PageProps) {
  if (!isWorkspacePresetId(params.preset)) notFound();
  const preset = workspacePreset(params.preset);

  const [audits, traceability, registry] = await Promise.all([
    loadRehearsalAudits(),
    loadTraceability(),
    loadArtifactRegistry(),
  ]);

  const focusedAudit =
    audits.find(
      (a) => a.request.mission_id === preset.defaultMissionId,
    ) ?? audits[0] ?? null;

  const spatial = focusedAudit
    ? await loadSpatialReplay(focusedAudit.request.request_id)
    : null;

  const events = focusedAudit?.runtime?.events ?? [];
  const decisions = audits
    .map((a) => a.decision)
    .filter(Boolean);
  const records = registry?.records ?? [];
  const bagBackedCount = records.filter(
    (r) => r.derivation_source === "bag_backed",
  ).length;

  const robot = CANONICAL_SITE.robots[0];
  const readiness = deriveRobotReadiness({
    robotId: robot.robot_id,
    hasAudit: audits.length > 0,
    finalStatus: focusedAudit ? String(focusedAudit.final_status) : null,
    lastRehearsalId: focusedAudit?.request.request_id ?? null,
    openIssues: focusedAudit?.final_failure_reason
      ? [focusedAudit.final_failure_reason]
      : [],
  });

  const queue = buildMissionQueue({
    siteId: CANONICAL_SITE.site_id,
    generatedAtUtc: focusedAudit?.generated_at_utc ?? "",
    entries: audits.slice(0, 6).map((a) => ({
      missionId: a.request.mission_id,
      description: a.request.description,
      auditRequestId: a.request.request_id,
      readinessState:
        a.final_status === "completed"
          ? "ready_to_rehearse"
          : a.final_status === "rejected"
            ? "blocked"
            : a.final_status === "aborted"
              ? "blocked"
              : "needs_review",
      readinessReason: a.final_failure_reason || a.safety_status,
    })),
  });

  const readyCount = queue.entries.filter(
    (e) => e.readiness === "ready_to_rehearse",
  ).length;
  const blockedCount = queue.entries.filter((e) => e.readiness === "blocked").length;

  const nodes: Partial<Record<WorkspacePanelId, React.ReactNode>> = {
    "mission-telemetry": <MissionTelemetryPanel audit={focusedAudit} />,
    "supervisor-decision-log": <SupervisorDecisionLog decisions={decisions} />,
    "replay-clock": <ReplayClockPanel events={events} cursor={0} />,
    "event-stream": <EventStreamPanel events={events} />,
    "velocity-command": <VelocityCommandPanel plan={focusedAudit?.plan ?? null} />,
    "replay-statistics": (
      <ReplayStatisticsPanel
        bundle={focusedAudit?.replay ?? null}
        analytics={focusedAudit?.analytics ?? null}
      />
    ),
    "mission-health": <MissionHealthPanel audits={audits} />,
    "pose-trace": <PoseTracePanel artifact={spatial} />,
    "topic-availability": <TopicAvailabilityPanel artifact={spatial} />,
    "evidence-integrity": <EvidenceIntegrityPanel records={records} />,
    "validation-outcome": (
      <ValidationOutcomePanel
        diagnostics={focusedAudit?.validation_diagnostics ?? []}
      />
    ),
    "rehearsal-outcome": <RehearsalOutcomePanel audits={audits} />,
    "fleet-overview": (
      <FleetOverviewPanel
        site={CANONICAL_SITE}
        readyCount={readyCount}
        blockedCount={blockedCount}
      />
    ),
    "site-map": <SiteMapOverview site={CANONICAL_SITE} />,
    "mission-queue": <MissionQueuePanel queue={queue} />,
    "robot-readiness": <RobotReadinessCard profile={robot} readiness={readiness} />,
    "zone-status": <ZoneStatusPanel statuses={REFERENCE_ZONE_STATUS} />,
    "walkthrough-overlay": <ReviewerWalkthroughOverlay />,
  };

  return (
    <WorkspaceShell
      preset={preset}
      topbar={<WorkspaceTopbar preset={preset} trailing={<ThemeToggle emphasis="medium" />} />}
      statusStrip={
        <WorkspaceStatusStrip
          rehearsalCount={audits.length}
          bagBackedCount={bagBackedCount}
          requirementCount={traceability?.row_count ?? 0}
          missionId={focusedAudit?.request.mission_id ?? null}
          generatedAtUtc={focusedAudit?.generated_at_utc ?? null}
        />
      }
      breadcrumbs={
        <WorkspaceBreadcrumbs
          entries={[
            { label: "Mission Control", href: "/" },
            { label: "Workspaces", href: "/workspaces" },
            { label: preset.title },
          ]}
        />
      }
    >
      <WorkspacePanelGrid preset={preset} nodes={nodes} />
    </WorkspaceShell>
  );
}

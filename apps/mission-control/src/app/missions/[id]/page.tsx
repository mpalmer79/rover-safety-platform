import Link from "next/link";
import { notFound } from "next/navigation";

import {
  listRehearsalIds,
  loadArtifactRegistryRecord,
  loadRehearsalAudit,
  loadSpatialReplay,
} from "@/adapters/loader";
import { selectMissionRoute } from "@/adapters/spatial";
import { MissionTimelineBridge } from "@/3d/MissionTimelineBridge";
import { ArtifactIntegrityBadge } from "@/components/ArtifactIntegrityBadge";
import { PageSurface } from "@/components/PageSurface";
import { AuditPanel } from "@/components/AuditPanel";
import { CompilerDecisionCard } from "@/components/CompilerDecisionCard";
import { DeterministicHashChain } from "@/components/DeterministicHashChain";
import { EvidenceLineageGraph } from "@/components/EvidenceLineageGraph";
import { EvidenceStatusChip } from "@/components/EvidenceStatusChip";
import { MermaidView } from "@/components/MermaidView";
import { MissionEventMarker } from "@/components/MissionEventMarker";
import { MissionRouteList } from "@/components/MissionRoute";
import { MissionSpatialTimeline } from "@/components/MissionSpatialTimeline";
import { MissionStateStepper } from "@/components/MissionStateStepper";
import { MissionStoryPanel } from "@/components/MissionStoryPanel";
import { Panel } from "@/components/Panel";
import { ReplayAnalyticsPanel } from "@/components/ReplayAnalyticsPanel";
import { ReplayConfidencePanel } from "@/components/ReplayConfidencePanel";
import { ReplayLifecyclePanel } from "@/components/ReplayLifecyclePanel";
import { ReplayTimeline } from "@/components/ReplayTimeline";
import { SceneSnapshotPanel } from "@/components/SceneSnapshotPanel";
import { RiskBandBadge } from "@/components/RiskBandBadge";
import { SafetyZoneLayer } from "@/components/SafetyZoneLayer";
import { StatusPill } from "@/components/StatusPill";
import { SupervisorAuthorityPanel } from "@/components/SupervisorAuthorityPanel";
import { SupervisorInterventionOverlay } from "@/components/SupervisorInterventionOverlay";
import { WhyRejectedDrilldown } from "@/components/WhyRejectedDrilldown";
import { ZoneBoundaryOverlay } from "@/components/ZoneBoundaryOverlay";

export const dynamic = "force-static";

export async function generateStaticParams() {
  const ids = await listRehearsalIds();
  return ids.map((id) => ({ id }));
}

interface MissionPageProps {
  params: { id: string };
}

export default async function MissionPage({ params }: MissionPageProps) {
  const audit = await loadRehearsalAudit(params.id);
  if (!audit) {
    notFound();
  }

  const plan = audit.plan;
  const runtime = audit.runtime;
  const replay = audit.replay;
  // Phase 17C: prefer a spatial-replay artifact (bag_backed or fixture)
  // when one is present. The artifact's derivation_source is rendered
  // verbatim in the map caption + playback badge.
  const spatialReplay = await loadSpatialReplay(params.id);
  // Phase 18: read the canonical registry record for the run so the
  // UI can surface lifecycle, integrity, and registered files.
  const artifactRecord = await loadArtifactRegistryRecord(params.id);
  const route = selectMissionRoute(plan, spatialReplay);

  return (
    <PageSurface>
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <p className="label">{audit.request.request_id}</p>
          <h1 className="display-1">
            {audit.request.description || audit.request.mission_id}
          </h1>
          <p className="text-muted">{audit.request.proposal_source}</p>
        </div>
        <div className="flex flex-row flex-wrap items-start gap-2 sm:flex-col sm:items-end">
          <StatusPill label={String(audit.final_status)} />
          {plan ? <RiskBandBadge band={plan.risk_band} /> : null}
          <EvidenceStatusChip
            status={replay?.evidence_status ?? "not_evaluated"}
            bagBacked={Boolean(replay?.bag_backed)}
          />
        </div>
      </header>

      <Panel eyebrow="Lifecycle" title="State machine">
        <MissionStateStepper
          status={String(audit.final_status)}
          failureReason={audit.final_failure_reason}
        />
      </Panel>

      {runtime ? (
        <Panel
          eyebrow="Mission flow"
          title="Spatial timeline"
          trailing={
            <div className="flex gap-3">
              <MissionEventMarker severity="info" label="info" />
              <MissionEventMarker severity="warning" label="warning" />
              <MissionEventMarker severity="rejection" label="rejection" />
            </div>
          }
        >
          <MissionSpatialTimeline events={runtime.events} />
        </Panel>
      ) : null}

      {audit.final_status === "rejected" ? (
        <WhyRejectedDrilldown audit={audit} />
      ) : null}

      <MissionStoryPanel audit={audit} />

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          {runtime ? (
            <MissionTimelineBridge
              plan={plan}
              events={runtime.events}
              spatialReplay={spatialReplay}
            />
          ) : null}
          {plan ? (
            <Panel eyebrow="Mission route" title="Waypoint inputs">
              <MissionRouteList route={route} />
            </Panel>
          ) : null}
          <ReplayConfidencePanel
            artifact={spatialReplay}
            record={artifactRecord}
          />
          <EvidenceLineageGraph
            artifact={spatialReplay}
            record={artifactRecord}
          />
          {plan ? (
            <Panel
              eyebrow="Mission plan"
              title={plan.mission_id}
              trailing={<RiskBandBadge band={plan.risk_band} />}
            >
              <div className="space-y-3 text-sm">
                <div>
                  <p className="label">Proposal source</p>
                  <p className="mt-1 text-base-800">{plan.proposal_source}</p>
                </div>
                <div>
                  <p className="label">Waypoints</p>
                  <ul className="mt-1 space-y-1 font-mono text-xs text-base-800">
                    {plan.waypoints.map((w) => (
                      <li key={w.waypoint_id}>
                        <span className="text-base-500">{w.waypoint_id}</span>{" "}
                        <span className="text-base-900">{w.label}</span>{" "}
                        <span className="text-base-500">
                          [{w.stage_kind}] dist={w.bounded_distance_m}m,
                          angle={w.bounded_angle_deg}°, speed={w.bounded_speed_mps}m/s
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <p className="label">Requested topics</p>
                    <ul className="mt-1 space-y-0.5 font-mono text-xs">
                      {plan.requested_topics.map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="label text-status-rejected">Forbidden topics</p>
                    <ul className="mt-1 space-y-0.5 font-mono text-xs text-status-rejected">
                      {plan.forbidden_topics.map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                {plan.safety_constraints.length > 0 ? (
                  <div>
                    <p className="label">Safety constraints</p>
                    <ul className="mt-1 space-y-0.5 text-xs text-base-700">
                      {plan.safety_constraints.map((c) => (
                        <li key={c}>• {c}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            </Panel>
          ) : null}

          <CompilerDecisionCard diagnostics={audit.validation_diagnostics} />

          <SupervisorAuthorityPanel decision={audit.decision} />

          {runtime ? (
            <Panel
              eyebrow="Rehearsal runtime"
              title={`Deterministic event stream · ${runtime.events.length} events`}
            >
              <ReplayTimeline events={runtime.events} />
            </Panel>
          ) : (
            <Panel eyebrow="Rehearsal runtime" title="Not executed">
              <p className="body-mono">
                Runtime did not run for this rehearsal. The supervisor or
                validator rejected the plan before the state machine
                reached <code>rehearsing</code>.
              </p>
            </Panel>
          )}

          {runtime ? (
            <Panel eyebrow="State machine" title="Transitions">
              <MermaidView source={runtime.timeline.rendered_mermaid} />
            </Panel>
          ) : null}
        </div>

        <div className="space-y-4">
          <AuditPanel audit={audit} />
          <ReplayLifecyclePanel record={artifactRecord} />
          <SceneSnapshotPanel
            runId={params.id}
            artifact={spatialReplay}
            record={artifactRecord}
          />
          {artifactRecord ? (
            <Panel
              eyebrow="Deterministic hashes"
              title="Registered files"
              trailing={
                <ArtifactIntegrityBadge
                  integrity={artifactRecord.integrity}
                  lifecycle={artifactRecord.lifecycle}
                />
              }
            >
              <DeterministicHashChain files={artifactRecord.files} />
            </Panel>
          ) : null}
          <Panel eyebrow="Safety zones" title="Topic + constraint layers">
            <SafetyZoneLayer plan={plan} />
            <div className="mt-3 border-t border-base-200 pt-3">
              <ZoneBoundaryOverlay audit={audit} />
            </div>
          </Panel>
          {runtime ? (
            <Panel eyebrow="Supervisor activity" title="Interventions">
              <SupervisorInterventionOverlay events={runtime.events} />
            </Panel>
          ) : null}
          <ReplayAnalyticsPanel analytics={audit.analytics} />
          {replay ? (
            <Panel eyebrow="Replay markers" title={`${replay.replay_markers.length} markers`}>
              <ul className="space-y-1 text-xs text-base-700">
                {replay.replay_markers.slice(0, 12).map((m) => (
                  <li key={m.marker_id} className="flex items-baseline gap-2">
                    <span className="font-mono text-base-500">{m.type}/{m.subtype}</span>
                    <span className="text-base-800">{m.description}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          ) : null}
        </div>
      </div>

      <p className="text-muted text-xs">
        ← <Link className="underline" href="/replay">Back to replay index</Link>
      </p>
    </div>
    </PageSurface>
  );
}

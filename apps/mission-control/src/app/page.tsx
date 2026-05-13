import { Activity } from "lucide-react";

import {
  loadLiveRuntimeMaturity,
  loadRehearsalAudits,
  loadTraceability,
} from "@/adapters/loader";
import { GovernanceHealthPanel } from "@/components/GovernanceHealthPanel";
import { GradientPanel } from "@/components/GradientPanel";
import { MissionCard } from "@/components/MissionCard";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";
import { RequirementBadge } from "@/components/RequirementBadge";
import { ResponsiveGrid } from "@/components/ResponsiveGrid";
import { ThemeToggle } from "@/components/ThemeToggle";
import { WarehouseLaneMap } from "@/components/WarehouseLaneMap";
import { formatTimestamp } from "@/lib/utils";

export const dynamic = "force-static";

export default async function DashboardPage() {
  const [audits, traceability, maturity] = await Promise.all([
    loadRehearsalAudits(),
    loadTraceability(),
    loadLiveRuntimeMaturity(),
  ]);

  const sortedAudits = [...audits].sort((a, b) =>
    a.request.mission_id.localeCompare(b.request.mission_id),
  );

  return (
    <PageSurface>
    <div className="space-y-6">
      <GradientPanel elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <p className="label">Mission Control</p>
            <h1 className="display-1">Operator dashboard</h1>
            <p className="text-muted text-sm sm:text-base">
              ProjectBoundary validates robot mission requests before
              simulated execution. It rejects unsafe commands,
              preserves supervisor authority, and records deterministic
              evidence for replay and audit. Every value below comes
              from committed JSON artifacts — nothing is synthesised at
              render time.
            </p>
          </div>
          <div className="flex flex-col items-start gap-2 sm:items-end">
            <ThemeToggle emphasis="medium" />
            <div className="inline-flex items-center gap-2 rounded-full border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-1.5 text-xs text-[color:var(--mc-text)]">
              <Activity aria-hidden className="h-4 w-4 text-[color:var(--mc-accent)]" />
              <span>
                {sortedAudits.length} rehearsal audits ·{" "}
                {traceability?.row_count ?? 0} requirements
              </span>
            </div>
          </div>
        </header>
      </GradientPanel>

      <GovernanceHealthPanel audits={sortedAudits} traceability={traceability} />

      <Panel
        eyebrow="Operations surface"
        title="Tactical layout"
        trailing={
          <span className="text-[11px] text-base-500">
            illustrative · no real coordinates
          </span>
        }
      >
        <WarehouseLaneMap />
      </Panel>

      <ResponsiveGrid shape="mission">
        <Panel
          eyebrow="Recent rehearsals"
          title="Mission cards"
          trailing={<span className="text-xs text-muted">{sortedAudits.length} bundles</span>}
        >
          <div className="grid gap-3">
            {sortedAudits.length === 0 ? (
              <p className="body-mono">
                No rehearsal audits found. Regenerate with{" "}
                <code>rover_ws/tools/generate_rehearsal_examples.py</code>.
              </p>
            ) : (
              sortedAudits.slice(0, 6).map((audit) => (
                <MissionCard key={audit.request.mission_id} audit={audit} />
              ))
            )}
          </div>
        </Panel>

        <div className="space-y-4">
          <Panel eyebrow="Live runtime maturity" title="not_established">
            {maturity ? (
              <dl className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="label">Runs total</dt>
                  <dd className="font-mono text-base-800">{maturity.runs_total}</dd>
                </div>
                <div>
                  <dt className="label">Bag-backed</dt>
                  <dd className="font-mono text-base-800">
                    {maturity.bag_counters.bag_backed ?? 0}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="label">Latest run</dt>
                  <dd className="font-mono text-xs text-base-700">
                    {maturity.latest_run_id ?? "—"} ·{" "}
                    {maturity.latest_run_status}
                  </dd>
                </div>
                <div className="col-span-2">
                  <dt className="label">Runner status</dt>
                  <dd className="font-mono text-xs text-base-700">{maturity.runner_status}</dd>
                </div>
                <div className="col-span-2">
                  <dt className="label">Generated</dt>
                  <dd className="font-mono text-xs text-base-500">
                    {formatTimestamp(maturity.generated_at_utc)}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="body-mono">No live runtime maturity artefact.</p>
            )}
          </Panel>

          <Panel eyebrow="Requirement coverage" title="By phase">
            {traceability ? (
              <div className="space-y-2">
                {Array.from(new Set(traceability.rows.map((r) => r.kind))).map((kind) => {
                  const rows = traceability.rows.filter((r) => r.kind === kind);
                  const passed = rows.filter((r) => r.status === "passed").length;
                  return (
                    <div key={kind} className="flex items-center justify-between gap-2 border-b border-base-200 pb-1 last:border-none">
                      <span className="label">{kind}</span>
                      <span className="font-mono text-xs text-base-700">
                        {passed} / {rows.length} passed
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="body-mono">
                Generate traceability with <code>tools/generate_traceability.py --with-verification</code>.
              </p>
            )}
          </Panel>

          {traceability ? (
            <Panel eyebrow="Requirement spot check" title="Selected REQs">
              <div className="flex flex-wrap gap-1.5">
                {traceability.rows
                  .filter((r) =>
                    [
                      "REQ-SAFE-001",
                      "REQ-LIVE-001",
                      "REQ-MCOMP-001",
                      "REQ-PROPOSAL-001",
                      "REQ-SKILL-001",
                      "REQ-SKILL-LLM-001",
                      "REQ-REHEARSAL-001",
                      "REQ-DESIGN-001",
                      "REQ-SKILL-INTEL-001",
                      "REQ-SNAPSHOT-001",
                    ].includes(r.req_id),
                  )
                  .map((r) => (
                    <RequirementBadge
                      key={r.req_id}
                      reqId={r.req_id}
                      status={r.status}
                      title={r.title}
                    />
                  ))}
              </div>
            </Panel>
          ) : null}
        </div>
      </ResponsiveGrid>
    </div>
    </PageSurface>
  );
}

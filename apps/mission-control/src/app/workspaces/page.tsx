import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";
import { WorkspacePresetSwitcher } from "@/workspaces/components/WorkspacePresetSwitcher";

export const dynamic = "force-static";

export default function WorkspacesIndexPage() {
  return (
    <PageSurface>
      <div className="space-y-6">
        <header className="space-y-1">
          <p className="label">Operator workspaces</p>
          <h1 className="display-1">Choose a deterministic workspace preset</h1>
          <p className="text-muted text-sm sm:text-base">
            Each workspace presents the same deterministic mission
            evidence through a different operational lens. Panels are
            populated from committed artifacts only — no live
            telemetry, no fake state.
          </p>
        </header>

        <Panel eyebrow="What this proves" title="One evidence base, six lenses">
          <ul className="grid gap-1.5 text-sm text-[color:var(--mc-text)] sm:grid-cols-2">
            <li>• <span className="font-semibold">Mission Review</span> — what happened during a mission.</li>
            <li>• <span className="font-semibold">Safety Review</span> — why motion was approved or rejected.</li>
            <li>• <span className="font-semibold">Replay Analysis</span> — whether the event stream can be replayed.</li>
            <li>• <span className="font-semibold">Evidence Audit</span> — what artifacts support each claim.</li>
            <li>• <span className="font-semibold">Fleet Readiness</span> — which missions and zones are currently ready.</li>
            <li>• <span className="font-semibold">Reviewer Walkthrough</span> — guided explanation for first-time visitors.</li>
          </ul>
        </Panel>
        <Panel
          eyebrow="Available presets"
          title="Six operator workspaces"
          trailing={
            <span className="text-xs text-muted">
              illustrative · simulation-only
            </span>
          }
        >
          <WorkspacePresetSwitcher active="mission-review" />
        </Panel>
      </div>
    </PageSurface>
  );
}

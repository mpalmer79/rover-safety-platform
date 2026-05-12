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
            Each preset is a JSON-backed layout. Panels are populated from
            committed artefacts only — no live telemetry, no fake state.
          </p>
        </header>
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

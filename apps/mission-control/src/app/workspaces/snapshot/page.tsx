import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";
import { CANONICAL_SNAPSHOT_FIXTURES } from "@/workspaces/snapshot";
import {
  WorkspaceSnapshotExportButton,
  WorkspaceSnapshotImportCard,
  WorkspaceSnapshotPanel,
  WorkspaceSnapshotSummary,
} from "@/workspaces/snapshot/components";

export const dynamic = "force-static";

export default function WorkspaceSnapshotPage() {
  const fixtures = Object.values(CANONICAL_SNAPSHOT_FIXTURES);
  const primary = fixtures[0];
  return (
    <PageSurface>
      <div className="space-y-6">
        <header className="space-y-1">
          <p className="label">Workspace snapshot</p>
          <h1 className="display-1">Reviewer handoff snapshot</h1>
          <p className="text-muted text-sm sm:text-base">
            A deterministic JSON capture of operator review state. No server,
            no database, no network. Copy the JSON below and hand it to
            another reviewer.
          </p>
        </header>

        <Panel
          eyebrow="Active snapshot"
          title={primary.presetId}
          trailing={<WorkspaceSnapshotExportButton snapshot={primary} />}
        >
          <div className="space-y-3">
            <WorkspaceSnapshotSummary snapshot={primary} />
            <WorkspaceSnapshotPanel snapshot={primary} />
          </div>
        </Panel>

        <Panel
          eyebrow="Canonical fixtures"
          title="Snapshot library"
          trailing={
            <span className="text-xs text-muted">{fixtures.length} fixtures</span>
          }
        >
          <div className="grid gap-3 lg:grid-cols-2">
            {fixtures.slice(1).map((snapshot) => (
              <WorkspaceSnapshotSummary
                key={snapshot.snapshotHash}
                snapshot={snapshot}
              />
            ))}
          </div>
        </Panel>

        <Panel
          eyebrow="Import"
          title="Validate a snapshot from JSON"
          trailing={
            <span className="text-xs text-muted">
              read-only · no network
            </span>
          }
        >
          <WorkspaceSnapshotImportCard />
        </Panel>
      </div>
    </PageSurface>
  );
}

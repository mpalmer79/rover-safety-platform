import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";
import { ReviewerWalkthroughOverlay } from "@/reviewer/components/ReviewerWalkthroughOverlay";

export const dynamic = "force-static";

export default function WalkthroughPage() {
  return (
    <PageSurface>
      <div className="space-y-4">
        <header className="space-y-1">
          <p className="label">Reviewer walkthrough</p>
          <h1 className="display-1">Guided pipeline tour</h1>
          <p className="text-base-700">
            ProjectBoundary turns a mission request into a deterministic
            audit bundle. Unsafe proposals are rejected before motion
            authority. Approved missions are simulated, replayed, and
            tied to traceable evidence. This walkthrough steps a
            reviewer through that flow end to end.
          </p>
        </header>
        <Panel eyebrow="What this proves" title="Reviewer summary">
          <ul className="space-y-1.5 text-sm text-base-700">
            <li>• Each step is anchored to a real audit artifact, not narrative.</li>
            <li>• Safety-supervisor authority is asserted at every gate.</li>
            <li>• The narrative ends with evidence the reviewer can open directly.</li>
          </ul>
        </Panel>
        <ReviewerWalkthroughOverlay />
      </div>
    </PageSurface>
  );
}

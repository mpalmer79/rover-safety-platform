import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

export default function DashboardLoading() {
  return (
    <PageSurface>
      <GradientPanel elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="space-y-1">
          <p className="label">Operator console</p>
          <h1 className="display-1">Mission Control Dashboard</h1>
          <p className="text-muted text-sm sm:text-base">
            Loading committed artifacts…
          </p>
        </header>
      </GradientPanel>
      <div
        role="status"
        aria-live="polite"
        data-testid="route-loading"
        className="mt-6 space-y-4"
      >
        <Panel eyebrow="Loading" title="Governance health">
          <p className="body-mono text-muted">
            Reading <code>verification/traceability.json</code> +
            recent rehearsal audits…
          </p>
        </Panel>
        <Panel eyebrow="Loading" title="Mission cards">
          <p className="body-mono text-muted">
            Reading <code>mission-rehearsals/audits/</code>…
          </p>
        </Panel>
      </div>
    </PageSurface>
  );
}

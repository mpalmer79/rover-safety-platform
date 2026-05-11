import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

export default function RouteLoading() {
  return (
    <PageSurface>
      <GradientPanel elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="space-y-1">
          <p className="label">Mission proposal workbench</p>
          <h1 className="display-1">Loading…</h1>
          <p className="text-muted text-sm sm:text-base">
            Loading committed artefacts…
          </p>
        </header>
      </GradientPanel>
      <div
        role="status"
        aria-live="polite"
        data-testid="route-loading"
        className="mt-6 space-y-4"
      >
        <Panel eyebrow="Loading" title="Mission library">
          <p className="body-mono text-muted">Reading mission-rehearsals/examples/…</p>
        </Panel>
        <Panel eyebrow="Loading" title="Skill library">
          <p className="body-mono text-muted">Reading skill-library/audits/…</p>
        </Panel>
      </div>
    </PageSurface>
  );
}

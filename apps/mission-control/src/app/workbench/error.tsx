"use client";

import { useEffect } from "react";

import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

interface RouteErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function RouteError({ error, reset }: RouteErrorProps) {
  useEffect(() => {
    if (typeof window !== "undefined") {
      const payload = {
        route: "/workbench",
        digest: error.digest ?? "",
        message: error.message,
        ts: new Date().toISOString(),
      };
      // eslint-disable-next-line no-console
      console.warn("mc-route-error", JSON.stringify(payload));
    }
  }, [error]);

  return (
    <PageSurface>
      <GradientPanel tone="rejected" elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="space-y-1">
          <p className="label">Mission proposal workbench</p>
          <h1 className="display-1">Artefact failed to load</h1>
          <p className="text-muted text-sm sm:text-base">
            The adapter raised a non-ENOENT error while reading
            committed JSON. The static export and safety-supervisor
            authority are unaffected.
          </p>
        </header>
      </GradientPanel>
      <Panel eyebrow="Diagnostics" title="Error details" className="mt-6">
        <dl data-testid="route-error" className="grid gap-2 text-sm sm:grid-cols-[12rem_1fr]">
          <dt className="label">route</dt>
          <dd className="font-mono">/workbench</dd>
          <dt className="label">digest</dt>
          <dd
            data-testid="route-error-digest"
            className="font-mono break-all text-[12px]"
          >
            {error.digest || "(none)"}
          </dd>
        </dl>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={reset}
            data-testid="route-error-retry"
            className="inline-flex items-center rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-3 py-1.5 text-sm font-medium text-[color:var(--mc-text)] hover:border-[color:var(--mc-border-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]"
          >
            Retry
          </button>
        </div>
      </Panel>
    </PageSurface>
  );
}

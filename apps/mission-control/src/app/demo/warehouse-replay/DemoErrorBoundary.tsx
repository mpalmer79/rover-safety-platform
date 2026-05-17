"use client";

import Link from "next/link";
import { Component } from "react";

import type { MissionPlan, RehearsalEvent, SpatialReplayArtifact } from "@/adapters/types";
import { GradientPanel } from "@/components/GradientPanel";
import { Panel } from "@/components/Panel";

import type { DemoMissionDescriptor } from "./sample-demo-mission";
import { WarehouseReplayDemo } from "./WarehouseReplayDemo";

interface DemoErrorBoundaryProps {
  descriptor: DemoMissionDescriptor;
  plan: MissionPlan | null;
  events: readonly RehearsalEvent[];
  spatialReplay: SpatialReplayArtifact | null;
  evidenceLinks: ReadonlyArray<{ label: string; href: string }>;
}

interface CaughtError {
  message: string;
  name: string;
  stack: string;
}

interface State {
  hasError: boolean;
  error: CaughtError | null;
}

const isDev =
  typeof process !== "undefined" && process.env?.NODE_ENV !== "production";

export class DemoErrorBoundary extends Component<DemoErrorBoundaryProps, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error: {
        message: error?.message ?? String(error),
        name: error?.name ?? "Error",
        stack: error?.stack ?? "",
      },
    };
  }

  componentDidCatch(error: Error, info: { componentStack?: string }) {
    if (typeof window !== "undefined") {
      // eslint-disable-next-line no-console
      console.error(
        "[demo/warehouse-replay] 3D render error:",
        error,
        info?.componentStack ?? "",
      );
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <StaticDemoSummary
          {...this.props}
          caughtError={this.state.error}
        />
      );
    }
    return (
      <WarehouseReplayDemo
        descriptor={this.props.descriptor}
        plan={this.props.plan}
        events={this.props.events}
        spatialReplay={this.props.spatialReplay}
        evidenceLinks={this.props.evidenceLinks}
      />
    );
  }
}

function StaticDemoSummary({
  descriptor,
  events,
  spatialReplay,
  evidenceLinks,
  caughtError,
}: DemoErrorBoundaryProps & { caughtError: CaughtError | null }) {
  const sampleCount = spatialReplay?.samples?.length ?? 0;
  const segmentCount = spatialReplay?.segments?.length ?? 0;
  const errorLabel = caughtError ? "3D scene render error" : "3D scene unavailable";
  return (
    <div
      className="space-y-6"
      data-testid="demo-static-summary"
      data-fallback-reason={caughtError ? "render-error" : "unavailable"}
      data-fallback-error={caughtError?.message ?? ""}
    >
      <GradientPanel tone="accent" elevated className="px-5 py-5 sm:px-6 sm:py-6">
        <p className="label">Mission Replay Demo</p>
        <h1 className="display-1">{descriptor.title}</h1>
        <p className="text-base text-[color:var(--mc-text)]">
          {descriptor.subtitle}
        </p>
      </GradientPanel>

      <div className="grid gap-5 lg:grid-cols-[1.45fr_1fr]">
        <Panel
          eyebrow="Mission narrative"
          title="Approved bounded-pickup mission"
        >
          <p className="text-sm text-[color:var(--mc-text)]">
            {descriptor.summary}
          </p>
          <ol className="mt-4 space-y-2 text-sm">
            {descriptor.beats.map((beat) => (
              <li key={beat.title} className="flex gap-3">
                <span className="font-mono text-[color:var(--mc-text-muted)]">
                  {Math.round(beat.at * 100).toString().padStart(2, "0")}%
                </span>
                <div>
                  <p className="font-semibold text-[color:var(--mc-text)]">
                    {beat.title}
                  </p>
                  <p className="text-[color:var(--mc-text-muted)]">
                    {beat.description}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </Panel>

        <div className="space-y-4">
          <Panel eyebrow="Replay evidence" title="Deterministic artifact stats">
            <ul className="space-y-1.5 text-sm font-mono text-[color:var(--mc-text)]">
              <li>Mission · {descriptor.rehearsalId}</li>
              <li>Spatial run · {descriptor.spatialRunId}</li>
              <li>Pose samples · {sampleCount}</li>
              <li>Trajectory segments · {segmentCount}</li>
              <li>Recorded events · {events.length}</li>
              <li>
                Derivation source ·{" "}
                {spatialReplay?.derivation_source ?? "unavailable"}
              </li>
            </ul>
            <p className="mt-3 text-xs text-[color:var(--mc-text-muted)]">
              {caughtError
                ? "The 3D scene hit a runtime render error; the underlying deterministic replay artifacts above are unaffected."
                : "The 3D scene is unavailable in this browser; the underlying deterministic replay artifacts above are unaffected."}
            </p>
            {isDev && caughtError ? (
              <pre
                data-testid="demo-static-summary-error-detail"
                className="mt-3 overflow-x-auto rounded border border-rose-400/40 bg-rose-500/5 p-2 text-[10px] text-rose-100"
              >
                {errorLabel}: {caughtError.name}: {caughtError.message}
                {caughtError.stack ? `\n\n${caughtError.stack}` : ""}
              </pre>
            ) : null}
          </Panel>

          {evidenceLinks.length > 0 ? (
            <Panel eyebrow="Evidence & audit" title="Open the supporting artifacts">
              <ul className="space-y-1.5 text-sm">
                {evidenceLinks.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </Panel>
          ) : null}
        </div>
      </div>
    </div>
  );
}

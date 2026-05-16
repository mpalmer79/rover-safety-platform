"use client";

import Link from "next/link";
import { Component, type ReactNode } from "react";

import type { MissionPlan, RehearsalEvent, SpatialReplayArtifact } from "@/adapters/types";
import { GradientPanel } from "@/components/GradientPanel";
import { Panel } from "@/components/Panel";

import type { DemoMissionDescriptor } from "./sample-demo-mission";
import { WarehouseReplayDemo } from "./WarehouseReplayDemo";

interface Props {
  descriptor: DemoMissionDescriptor;
  plan: MissionPlan | null;
  events: readonly RehearsalEvent[];
  spatialReplay: SpatialReplayArtifact | null;
  evidenceLinks: ReadonlyArray<{ label: string; href: string }>;
}

interface State {
  hasError: boolean;
}

/**
 * Client-side error boundary that keeps the demo route from ever
 * surfacing the route-level error.tsx in production.
 *
 * Any render-time throw inside WarehouseReplayDemo (3D scene, WebGL
 * init, font atlas load, anything downstream of @react-three/fiber)
 * is captured here and replaced with a static 2D summary so the page
 * stays usable. The route-level error boundary becomes unreachable
 * for this demo.
 */
export class DemoErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    if (typeof window !== "undefined") {
      // eslint-disable-next-line no-console
      console.warn(
        "[demo/warehouse-replay] client render error caught:",
        error?.message ?? String(error),
      );
    }
  }

  render() {
    if (this.state.hasError) {
      return <StaticDemoSummary {...this.props} />;
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
}: Props) {
  const sampleCount = spatialReplay?.samples?.length ?? 0;
  const segmentCount = spatialReplay?.segments?.length ?? 0;
  return (
    <div className="space-y-6" data-testid="demo-static-summary">
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
              The 3D scene is unavailable in this browser; the underlying
              deterministic replay artifacts above are unaffected.
            </p>
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

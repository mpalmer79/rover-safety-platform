"use client";

import Link from "next/link";
import { useEffect } from "react";

import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

import { DEMO_MISSION } from "./sample-demo-mission";

interface RouteErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

/**
 * Last-resort route error boundary for /demo/warehouse-replay.
 *
 * Inner client error boundary (DemoErrorBoundary) already catches
 * render errors and shows a static summary, so reaching this point
 * is unexpected. We still degrade gracefully: render the mission
 * narrative + evidence links rather than a diagnostic crash screen,
 * so the reviewer-facing demo route is never a dead end.
 */
export default function RouteError({ error, reset }: RouteErrorProps) {
  useEffect(() => {
    if (typeof window !== "undefined") {
      // eslint-disable-next-line no-console
      console.warn(
        "[demo/warehouse-replay] route boundary reached:",
        JSON.stringify({
          route: "/demo/warehouse-replay",
          digest: error.digest ?? "",
          message: error.message,
        }),
      );
    }
  }, [error]);

  return (
    <PageSurface variant="hero">
      <div className="space-y-6">
        <GradientPanel tone="accent" elevated className="px-5 py-5 sm:px-6 sm:py-6">
          <p className="label">Mission Replay Demo</p>
          <h1 className="display-1">{DEMO_MISSION.title}</h1>
          <p className="text-base text-[color:var(--mc-text)]">
            {DEMO_MISSION.subtitle}
          </p>
        </GradientPanel>

        <div className="grid gap-5 lg:grid-cols-[1.45fr_1fr]">
          <Panel
            eyebrow="Mission narrative"
            title="Approved bounded-pickup mission"
          >
            <p className="text-sm text-[color:var(--mc-text)]">
              {DEMO_MISSION.summary}
            </p>
            <ol className="mt-4 space-y-2 text-sm">
              {DEMO_MISSION.beats.map((beat) => (
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
            <Panel eyebrow="Reviewer paths" title="What to do next">
              <ul className="space-y-1.5 text-sm">
                <li>
                  •{" "}
                  <Link
                    href={`/missions/${DEMO_MISSION.rehearsalId}`}
                    className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
                  >
                    Open the mission audit
                  </Link>
                </li>
                <li>
                  •{" "}
                  <Link
                    href="/safety"
                    className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
                  >
                    Inspect the Safety Authority chain
                  </Link>
                </li>
                <li>
                  •{" "}
                  <Link
                    href="/walkthrough"
                    className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
                  >
                    Open the Reviewer Walkthrough
                  </Link>
                </li>
                <li>
                  •{" "}
                  <Link
                    href="/evidence"
                    className="text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
                  >
                    Open the Evidence &amp; Audit explorer
                  </Link>
                </li>
              </ul>
              <button
                type="button"
                onClick={reset}
                data-testid="route-error-retry"
                className="mt-4 inline-flex items-center rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-3 py-1.5 text-sm font-medium text-[color:var(--mc-text)] hover:border-[color:var(--mc-border-strong)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--mc-accent)]"
              >
                Reload 3D scene
              </button>
            </Panel>
          </div>
        </div>
      </div>
    </PageSurface>
  );
}

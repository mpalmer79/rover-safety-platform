import Link from "next/link";

import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

const REVIEWER_LINKS = [
  {
    href: "/start",
    label: "Start Here",
    description: "What ProjectBoundary demonstrates and where to click first.",
  },
  {
    href: "/demo/warehouse-replay",
    label: "Mission Replay Demo",
    description: "3D walkthrough of an approved warehouse mission.",
  },
  {
    href: "/safety",
    label: "Safety Authority",
    description: "How motion authority flows through deterministic gates.",
  },
  {
    href: "/walkthrough",
    label: "Reviewer Walkthrough",
    description: "Guided tour of the deterministic mission pipeline.",
  },
  {
    href: "/evidence",
    label: "Evidence & Audit",
    description: "Traceable JSON artifacts behind every claim.",
  },
] as const;

export default function NotFound() {
  return (
    <PageSurface>
      <GradientPanel elevated className="px-4 py-4 sm:px-5 sm:py-5">
        <header className="space-y-1">
          <p className="label">Mission Control</p>
          <h1 className="display-1">This page is not part of the public demo</h1>
          <p className="text-muted text-sm sm:text-base">
            The route you tried to open is not available in the reviewer
            build. Use one of the links below to return to a curated
            section of the demonstration.
          </p>
        </header>
      </GradientPanel>
      <Panel
        eyebrow="Reviewer paths"
        title="Recommended next clicks"
        className="mt-6"
      >
        <ul
          data-testid="route-not-found"
          className="grid gap-3 sm:grid-cols-2"
        >
          {REVIEWER_LINKS.map((item) => (
            <li
              key={item.href}
              className="rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-3"
            >
              <Link
                href={item.href}
                className="block font-semibold text-[color:var(--mc-accent)] underline-offset-2 hover:underline"
              >
                {item.label}
              </Link>
              <p className="mt-1 text-xs text-[color:var(--mc-text-muted)]">
                {item.description}
              </p>
            </li>
          ))}
        </ul>
      </Panel>
    </PageSurface>
  );
}

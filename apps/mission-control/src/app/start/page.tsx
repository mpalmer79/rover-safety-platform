import Link from "next/link";
import {
  ArrowRight,
  Compass,
  FileSearch,
  Grid3x3,
  Layers,
  PlayCircle,
  Route,
  ShieldCheck,
} from "lucide-react";

import { GradientPanel } from "@/components/GradientPanel";
import { PageSurface } from "@/components/PageSurface";
import { Panel } from "@/components/Panel";

export const dynamic = "force-static";

export const metadata = {
  title: "ProjectBoundary · Reviewer entry point",
  description:
    "Reviewer entry point: what ProjectBoundary demonstrates and where to click first.",
};

const PRIMARY_CTAS = [
  {
    href: "/demo/warehouse-replay",
    label: "View Mission Replay Demo",
    description:
      "3D walkthrough of an approved warehouse mission, driven by deterministic replay artifacts.",
    icon: PlayCircle,
  },
  {
    href: "/safety",
    label: "Review Safety Authority",
    description:
      "Who can authorize motion and which gates a request must clear first.",
    icon: ShieldCheck,
  },
  {
    href: "/walkthrough",
    label: "Open Guided Walkthrough",
    description:
      "Step-by-step reviewer tour of the deterministic mission pipeline.",
    icon: Compass,
  },
  {
    href: "/evidence",
    label: "Inspect Evidence & Audit",
    description:
      "Requirement coverage, traceability, and the JSON artifacts behind every claim.",
    icon: FileSearch,
  },
  {
    href: "/workspaces",
    label: "Open Workspaces",
    description:
      "Same evidence, six operator lenses for reviewing missions.",
    icon: Grid3x3,
  },
  {
    href: "/workbench",
    label: "Open Proposal Workbench",
    description:
      "Accepted vs. rejected intents, with the supervisor decision trail.",
    icon: Layers,
  },
] as const;

const REVIEWER_PATH = [
  { href: "/start", label: "Start Here", note: "You are here." },
  { href: "/demo/warehouse-replay", label: "Mission Replay Demo", note: "10 seconds of visual context." },
  { href: "/safety", label: "Safety Authority", note: "Why supervisor authority matters." },
  { href: "/walkthrough", label: "Reviewer Walkthrough", note: "Pipeline, end to end." },
  { href: "/evidence", label: "Evidence & Audit", note: "Trace claims to artifacts." },
  { href: "/workspaces", label: "Workspaces", note: "Same evidence, six operator lenses." },
  { href: "/workbench", label: "Proposal Workbench", note: "Accepted vs. rejected intents." },
] as const;

const WHAT_PROVES = [
  "Unsafe motion requests are rejected before they reach motion authority.",
  "Approved missions are deterministically replayable from committed artifacts.",
  "Evidence is traceable to requirements, validators, and audit bundles.",
  "Generated or proposed actions cannot bypass the safety supervisor.",
] as const;

export default function ReviewerStartPage() {
  return (
    <PageSurface variant="hero">
      <div className="space-y-6">
        <GradientPanel tone="accent" elevated className="px-5 py-6 sm:px-7 sm:py-7">
          <div className="flex flex-col gap-3">
            <p className="label">Reviewer entry point</p>
            <h1 className="display-1">What ProjectBoundary demonstrates</h1>
            <p className="text-base sm:text-lg text-[color:var(--mc-text)]">
              ProjectBoundary is a{" "}
              <span className="font-semibold text-[color:var(--mc-accent)]">
                simulation-only mission-validation and safety-supervisor
                demonstration platform
              </span>
              . It validates robot mission requests, rejects unsafe
              commands before motion authority, preserves supervisor
              authority on every path, and records deterministic
              evidence for replay and audit. It does not control real
              hardware and is not safety-certified.
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Link
                href="/demo/warehouse-replay"
                data-testid="start-cta-demo"
                className="inline-flex items-center gap-2 rounded-md border border-[color:var(--mc-accent)] bg-[color:var(--mc-accent-soft)] px-4 py-2 text-sm font-semibold text-[color:var(--mc-accent)] transition-colors hover:bg-[color:var(--mc-accent)] hover:text-[color:var(--mc-text-inverse)]"
              >
                <PlayCircle aria-hidden className="h-4 w-4" />
                See the 3D mission replay
                <ArrowRight aria-hidden className="h-4 w-4" />
              </Link>
              <Link
                href="/safety"
                className="inline-flex items-center gap-2 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-4 py-2 text-sm text-[color:var(--mc-text)] hover:border-[color:var(--mc-accent)]"
              >
                <ShieldCheck aria-hidden className="h-4 w-4" />
                Review safety authority
              </Link>
            </div>
          </div>
        </GradientPanel>

        <Panel
          eyebrow="What this proves"
          title="Outcomes a reviewer can verify in this build"
          trailing={
            <Route aria-hidden className="h-4 w-4 text-[color:var(--mc-accent)]" />
          }
        >
          <ul
            data-testid="start-what-proves"
            className="space-y-2 text-sm text-[color:var(--mc-text)]"
          >
            {WHAT_PROVES.map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span aria-hidden className="mt-1 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--mc-accent)]" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel
          eyebrow="Reviewer paths"
          title="Recommended next clicks"
          trailing={<span className="text-xs text-muted">~3 minutes</span>}
        >
          <div className="grid gap-3 md:grid-cols-2">
            {PRIMARY_CTAS.map(({ href, label, description, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                data-testid={`start-cta-${href.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "")}`}
                className="group flex items-start gap-3 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-4 py-3 transition-colors hover:border-[color:var(--mc-accent)]"
              >
                <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[color:var(--mc-accent-soft)] text-[color:var(--mc-accent)]">
                  <Icon aria-hidden className="h-4 w-4" />
                </span>
                <span className="flex-1 space-y-1">
                  <span className="block text-sm font-semibold text-[color:var(--mc-text)] group-hover:text-[color:var(--mc-accent)]">
                    {label}
                  </span>
                  <span className="block text-xs leading-snug text-[color:var(--mc-text-muted)]">
                    {description}
                  </span>
                </span>
                <ArrowRight
                  aria-hidden
                  className="mt-1 h-4 w-4 shrink-0 text-[color:var(--mc-text-muted)] transition-transform group-hover:translate-x-0.5 group-hover:text-[color:var(--mc-accent)]"
                />
              </Link>
            ))}
          </div>
        </Panel>

        <Panel eyebrow="Recommended path" title="A 3-minute reviewer flow">
          <ol className="space-y-2 text-sm">
            {REVIEWER_PATH.map((step, idx) => (
              <li key={step.href} className="flex items-start gap-3">
                <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] font-mono text-[11px] text-[color:var(--mc-text)]">
                  {idx + 1}
                </span>
                <span className="flex-1">
                  <Link
                    href={step.href}
                    className="font-semibold text-[color:var(--mc-text)] underline-offset-2 hover:text-[color:var(--mc-accent)] hover:underline"
                  >
                    {step.label}
                  </Link>
                  <span className="ml-2 text-xs text-[color:var(--mc-text-muted)]">
                    {step.note}
                  </span>
                </span>
              </li>
            ))}
          </ol>
        </Panel>
      </div>
    </PageSurface>
  );
}

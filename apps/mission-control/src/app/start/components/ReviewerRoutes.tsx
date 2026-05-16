import {
  Compass,
  FileSearch,
  Grid3x3,
  Layers,
  PlayCircle,
  ShieldCheck,
} from "lucide-react";
import Link from "next/link";

interface Route {
  href: string;
  label: string;
  hint: string;
  icon: typeof PlayCircle;
}

const ROUTES: readonly Route[] = [
  {
    href: "/demo/warehouse-replay",
    label: "Mission Replay Demo",
    hint: "3D mission, deterministic artifacts.",
    icon: PlayCircle,
  },
  {
    href: "/safety",
    label: "Safety Authority",
    hint: "Who can authorise motion, and how.",
    icon: ShieldCheck,
  },
  {
    href: "/walkthrough",
    label: "Reviewer Walkthrough",
    hint: "Pipeline end to end.",
    icon: Compass,
  },
  {
    href: "/evidence",
    label: "Evidence & Audit",
    hint: "Requirements · traceability · artifacts.",
    icon: FileSearch,
  },
  {
    href: "/workspaces",
    label: "Workspaces",
    hint: "Same evidence, six operator lenses.",
    icon: Grid3x3,
  },
  {
    href: "/workbench",
    label: "Proposal Workbench",
    hint: "Accepted vs. rejected intents.",
    icon: Layers,
  },
];

export function ReviewerRoutes() {
  return (
    <section
      data-testid="reviewer-routes"
      className="rounded-2xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-5 py-6 sm:px-7 sm:py-7"
    >
      <header className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="label">All reviewer routes</p>
          <h2 className="display-2">Where to look next</h2>
        </div>
        <p className="text-xs text-[color:var(--mc-text-muted)]">
          Every link below is a working route in this build.
        </p>
      </header>
      <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {ROUTES.map(({ href, label, hint, icon: Icon }) => (
          <li key={href}>
            <Link
              href={href}
              data-testid={`reviewer-route-${href.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "")}`}
              className="group flex items-center gap-3 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-2.5 transition-colors hover:border-cyan-400/40"
            >
              <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-cyan-400/10 text-cyan-200">
                <Icon aria-hidden className="h-3.5 w-3.5" />
              </span>
              <span className="flex-1">
                <span className="block text-sm font-semibold text-[color:var(--mc-text)] group-hover:text-cyan-200">
                  {label}
                </span>
                <span className="block text-[11px] text-[color:var(--mc-text-muted)]">
                  {hint}
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

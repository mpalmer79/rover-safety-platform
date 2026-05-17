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
  tier: "primary" | "secondary";
}

const ROUTES: readonly Route[] = [
  {
    href: "/demo/warehouse-replay",
    label: "Mission Replay Demo",
    hint: "Full 3D mission · play, pause, scrub.",
    icon: PlayCircle,
    tier: "primary",
  },
  {
    href: "/safety",
    label: "Safety Authority",
    hint: "Who can authorise motion, and how.",
    icon: ShieldCheck,
    tier: "primary",
  },
  {
    href: "/evidence",
    label: "Evidence & Audit",
    hint: "Requirements · traceability · artifacts.",
    icon: FileSearch,
    tier: "primary",
  },
  {
    href: "/walkthrough",
    label: "Reviewer Walkthrough",
    hint: "Mission pipeline, end to end.",
    icon: Compass,
    tier: "secondary",
  },
  {
    href: "/workspaces",
    label: "Workspaces",
    hint: "Same evidence, six operator lenses.",
    icon: Grid3x3,
    tier: "secondary",
  },
  {
    href: "/workbench",
    label: "Proposal Workbench",
    hint: "Accepted vs. rejected intents.",
    icon: Layers,
    tier: "secondary",
  },
];

const primary = ROUTES.filter((r) => r.tier === "primary");
const secondary = ROUTES.filter((r) => r.tier === "secondary");

export function ReviewerRoutes() {
  return (
    <section
      data-testid="reviewer-routes"
      className="rounded-2xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-5 py-6 sm:px-7 sm:py-7"
    >
      <header className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="label">Reviewer path</p>
          <h2 className="display-2">Where to look next</h2>
        </div>
        <p className="text-xs text-[color:var(--mc-text-muted)]">
          Three core routes · three supporting routes.
        </p>
      </header>

      <ol className="grid gap-2 sm:grid-cols-3">
        {primary.map(({ href, label, hint, icon: Icon }, i) => (
          <li key={href}>
            <Link
              href={href}
              data-testid={`reviewer-route-${href.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "")}`}
              className="group flex h-full items-start gap-3 rounded-lg border border-cyan-400/20 bg-cyan-400/5 px-3 py-3 transition-all hover:-translate-y-0.5 hover:border-cyan-400/50 hover:shadow-[0_8px_20px_-12px_rgba(60,180,168,0.45)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
            >
              <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-cyan-400/30 bg-cyan-400/15 text-cyan-200">
                <Icon aria-hidden className="h-4 w-4" />
              </span>
              <span className="flex-1">
                <span className="flex items-center justify-between gap-2">
                  <span className="text-sm font-semibold text-[color:var(--mc-text)] group-hover:text-cyan-200">
                    {label}
                  </span>
                  <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-cyan-300/70">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                </span>
                <span className="mt-0.5 block text-[11px] text-[color:var(--mc-text-muted)]">
                  {hint}
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ol>

      <p className="mt-5 mb-2 font-mono text-[10px] uppercase tracking-[0.16em] text-[color:var(--mc-text-muted)]">
        Also worth a click
      </p>
      <ul className="grid gap-2 sm:grid-cols-3">
        {secondary.map(({ href, label, hint, icon: Icon }) => (
          <li key={href}>
            <Link
              href={href}
              data-testid={`reviewer-route-${href.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "")}`}
              className="group flex items-center gap-3 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-2.5 transition-colors hover:border-cyan-400/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
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

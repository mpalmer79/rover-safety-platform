import {
  ActivitySquare,
  GitBranch,
  Layers,
  Radar,
  ShieldAlert,
  TestTube2,
} from "lucide-react";

interface Proof {
  title: string;
  copy: string;
  icon: typeof Radar;
}

const PROOFS: readonly Proof[] = [
  {
    title: "Deterministic replay",
    copy: "Approved missions are reconstructed byte-for-byte from committed pose-sample and event artifacts.",
    icon: Radar,
  },
  {
    title: "Safety-supervisor authority",
    copy: "Motion authority lives behind a supervisor state machine. No bypass path from validator or LLM proposals.",
    icon: ShieldAlert,
  },
  {
    title: "Evidence-backed audit trail",
    copy: "Every event is hash-chained. Replay bundles map back to requirements and tests.",
    icon: GitBranch,
  },
  {
    title: "Mission-control UI",
    copy: "Operator-grade panels for plan validation, rehearsal review, and replay analysis.",
    icon: ActivitySquare,
  },
  {
    title: "Verification artifacts",
    copy: "Requirements, traceability, validator suites, and rehearsal audits are all version-controlled JSON.",
    icon: TestTube2,
  },
  {
    title: "Simulation environment",
    copy: "Simulation-only. The platform does not control real hardware and is not safety-certified.",
    icon: Layers,
  },
];

export function ProofPoints() {
  return (
    <section
      data-testid="proof-points"
      className="rounded-2xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-5 py-6 sm:px-7 sm:py-7"
    >
      <header className="mb-5">
        <p className="label">Technical credibility</p>
        <h2 className="display-2">What makes this credible engineering</h2>
      </header>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {PROOFS.map((p) => {
          const Icon = p.icon;
          return (
            <div
              key={p.title}
              className="flex items-start gap-3 rounded-lg border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-4 py-3 transition-colors hover:border-cyan-400/40"
            >
              <span className="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-cyan-400/25 bg-cyan-400/10 text-cyan-200">
                <Icon aria-hidden className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-semibold text-[color:var(--mc-text)]">
                  {p.title}
                </p>
                <p className="mt-0.5 text-xs leading-snug text-[color:var(--mc-text-muted)]">
                  {p.copy}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

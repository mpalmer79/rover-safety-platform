import { PageSurface } from "@/components/PageSurface";

import { MissionChallengeCards } from "./components/MissionChallengeCards";
import { MissionHero } from "./components/MissionHero";
import { MissionJourney } from "./components/MissionJourney";
import { ProofPoints } from "./components/ProofPoints";
import { ReviewerRoutes } from "./components/ReviewerRoutes";
import { SafetyAuthorityPreview } from "./components/SafetyAuthorityPreview";

export const dynamic = "force-static";

export const metadata = {
  title: "ProjectBoundary · Autonomous rover mission control",
  description:
    "Watch an autonomous rover mission get approved, rejected, and replayed through a safety-supervised control stack. Simulation only · not safety-certified.",
};

const WHAT_PROVES = [
  "Unsafe motion requests are rejected before they reach motion authority.",
  "Approved missions are deterministically replayable from committed artifacts.",
  "Evidence is traceable to requirements, validators, and audit bundles.",
  "Generated or proposed actions cannot bypass the safety supervisor.",
] as const;

export default function ReviewerStartPage() {
  return (
    <PageSurface variant="hero">
      <div className="space-y-7">
        <MissionHero />

        <MissionJourney />

        <MissionChallengeCards />

        <SafetyAuthorityPreview />

        <section className="rounded-2xl border border-[color:var(--mc-border)] bg-[color:var(--mc-surface)] px-5 py-6 sm:px-7 sm:py-7">
          <header className="mb-4">
            <p className="label">What this proves</p>
            <h2 className="display-2">Outcomes a reviewer can verify</h2>
          </header>
          <ul
            data-testid="start-what-proves"
            className="grid gap-2 text-sm text-[color:var(--mc-text)] sm:grid-cols-2"
          >
            {WHAT_PROVES.map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 rounded-md border border-[color:var(--mc-border)] bg-[color:var(--mc-surface-overlay)] px-3 py-2.5"
              >
                <span
                  aria-hidden
                  className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-300"
                />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <ProofPoints />

        <ReviewerRoutes />

        <p className="text-center text-xs text-[color:var(--mc-text-muted)]">
          ProjectBoundary is a simulation-only mission-validation and
          safety-supervisor demonstration platform. It does not control real
          hardware and is not safety-certified.
        </p>
      </div>
    </PageSurface>
  );
}

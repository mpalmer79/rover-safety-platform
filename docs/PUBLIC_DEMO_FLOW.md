# Public Demo Flow

The deployed `apps/mission-control` site is the public-facing surface
of ProjectBoundary. This document records the recommended reviewer
flow, what each page is supposed to prove, and a short demo script
suitable for recruiter and technical-screen settings.

## Recommended path

| Step | Route | What it proves |
|------|-------|----------------|
| 1 | `/start` | What ProjectBoundary is and the simulation-only boundary in plain English |
| 2 | `/demo/warehouse-replay` | A polished 3D mission replay driven by deterministic artifacts |
| 3 | `/safety` | The safety supervisor is the only authority that can produce `/cmd_vel_authorized` |
| 4 | `/walkthrough` | Step-by-step pipeline tour: proposal → validation → supervision → replay → evidence |
| 5 | `/evidence` | Requirement coverage and the JSON traceability matrix |
| 6 | `/workspaces` | Same evidence, six operator lenses |
| 7 | `/workbench` | Accepted vs rejected mission intents |

Total time: roughly 3 minutes for a recruiter, 10 minutes for a
technical screener.

## What each page proves

- **`/start`** — ProjectBoundary is a simulation-only mission-validation
  and safety-supervisor demonstration platform. The page lists what is
  in scope, what is not claimed, and what a reviewer can verify.
- **`/demo/warehouse-replay`** — Mission progress can be reconstructed
  from committed replay artifacts. Approved missions move only after
  validation and supervisor approval. Safety events are surfaced in
  context. Evidence is linked.
- **`/safety`** — The authority chain is intentionally narrow. Only
  the safety supervisor authorizes motion. Validator-rejected plans
  never reach the supervisor.
- **`/walkthrough`** — Each pipeline step is anchored to a real audit
  artifact. The walkthrough never narrates without referencing the
  bytes on disk.
- **`/evidence`** — Public claims are traceable to requirements,
  tests, and committed artifacts. The matrix is rendered verbatim
  from the deterministic traceability run.
- **`/workspaces`** — Six operator presets present the same
  deterministic evidence base through different lenses.
- **`/workbench`** — Accepted intents flow through validation;
  rejected intents are blocked before motion authority.

## Demo script (3 minutes)

> "ProjectBoundary is a simulation-only mission validation and
> safety-supervisor demonstration platform. It validates robot
> mission requests before simulated execution, rejects unsafe
> commands before motion authority, preserves supervisor authority
> on every path, and records deterministic evidence for replay and
> audit. It does not control real hardware and is not safety
> certified."
>
> *Open `/demo/warehouse-replay`.*
>
> "Here's a polished mission replay. The rover only moves after the
> validator and the safety supervisor sign off. Position and event
> timing come from a committed pose-sample artifact — nothing is
> generated at render time."
>
> *Open `/safety`.*
>
> "Here is the authority chain. Only the supervisor can produce
> `/cmd_vel_authorized`. Anything else — sanitizer rejection,
> validator rejection, supervisor refusal — is recorded with a
> verbatim reason."
>
> *Open `/evidence`.*
>
> "And here is the requirement coverage matrix. Every claim above
> traces to a requirement, an implementation file, a test, and an
> evidence artifact on disk."

## Honesty boundaries enforced in the public flow

- The simulation-only banner is rendered at the root layout for every
  route.
- The 3D demo route is bound to a committed canonical artifact and
  surfaces the derivation source in the scene overlay.
- Bag-backed evidence is reported as `not_established` verbatim from
  the live-runtime maturity artifact; the demo never claims live
  telemetry.
- Generated skill candidates are surfaced as data only — the UI never
  executes them.

## Artifacts the public flow depends on

- `mission-rehearsals/audits/warehouse_pickup_route_alpha/` — the
  canonical approved-mission audit driving the demo route.
- `spatial-replay/runs/canonical-fixture/` — the canonical pose-sample
  artifact rendered in the 3D scene.
- `evidence/` — the traceability matrix surfaced on `/evidence`.

If any of those artifacts are missing, the corresponding public route
falls back to a labeled 2D / informational state rather than an empty
panel.

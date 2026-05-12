# Reviewer Walkthrough Mode

> Understand the platform end-to-end in 3-5 minutes.

## Why this mode exists

Mission Control is a dense operator console. The reviewer walkthrough
is a guided overlay that walks a first-time reviewer through every
stage of the deterministic pipeline, in order, with the artefacts
each stage produces and the safety boundary it enforces.

The walkthrough is purely a presentation layer. It does not invoke
any runtime, fabricate any state, or grant any authority.

## Ten deterministic steps

| # | Step                       | Evidence                                                |
| - | -------------------------- | ------------------------------------------------------- |
| 1 | Operator request           | `rehearsal_audit.request`                               |
| 2 | Proposal generation        | `mission_proposals/<id>/proposal.json`                  |
| 3 | Sanitizer decision         | `sanitizer_audit.json`                                  |
| 4 | Compiler result            | `mission_plan.json`                                     |
| 5 | Validator result           | `rehearsal_audit.validation_diagnostics`                |
| 6 | Supervisor decision        | `rehearsal_audit.decision`                              |
| 7 | Rehearsal execution        | `rehearsal_audit.runtime.events`                        |
| 8 | Replay evidence            | `replay_bundle.json` + spatial-replay artefact          |
| 9 | Analytics outcome          | `rehearsal_analytics.json`                              |
| 10 | Unresolved limitations    | `rehearsal_audit.disclaimer`, `live_runtime_maturity`   |

The full script lives in
`apps/mission-control/src/reviewer/steps.ts`. The
`tests/walkthrough.test.tsx` suite pins the step count, ordering, and
copy.

## Component composition

| Component                       | Role                                                  |
| ------------------------------- | ----------------------------------------------------- |
| `ReviewerWalkthroughOverlay`    | Container with next / back / reset controls           |
| `WalkthroughProgress`           | 10-segment progress bar                               |
| `WalkthroughStepCard`           | Title + narrative for the active step                 |
| `WalkthroughNarrativePanel`     | Long-form description + outcome                       |
| `WalkthroughEvidencePanel`      | Hard-coded list of evidence references                |
| `WalkthroughSafetyPanel`        | Safety boundary callout for the step                  |
| `WalkthroughOutcomePanel`       | Outcome statement (what the step produces)            |

## Where to reach it

* `/walkthrough` — full-page walkthrough wrapped in `PageSurface`.
* `/workspaces/reviewer-walkthrough` — the same walkthrough rendered
  inside the workspace shell with sidebar nav.

## Honesty rules

The walkthrough must NEVER:

* invent evidence references that do not exist on disk,
* claim the platform is safety-certified,
* claim live runtime authority,
* skip step 10 (unresolved limitations) when the reviewer reaches
  the end.

The walkthrough must ALWAYS:

* leave the reviewer with the limitations list visible,
* render the safety banner at the page root,
* preserve the step order from `WALKTHROUGH_STEPS`.

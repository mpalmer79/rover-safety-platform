# Contextual Reviewer Walkthrough

> The ten-step walkthrough now binds to the selected mission.

## Why

Phase 20's walkthrough was informational only. Phase 20B upgrades
it to mission-contextual: every step now renders evidence from the
currently-selected mission audit, with explicit limitations when
evidence is missing.

## Architecture

`apps/mission-control/src/reviewer/contextualWalkthrough.ts` exposes
`buildStepBindings(input)` — a pure function that returns one
`StepBinding` per walkthrough step.

A `StepBinding` carries:

| Field            | Meaning                                              |
| ---------------- | ---------------------------------------------------- |
| `step`           | Walkthrough step id (1..10)                          |
| `status`         | `ok` / `rejected` / `partial` / `unavailable` / `not_evaluated` |
| `headline`       | Single-line summary                                  |
| `artifactRef`    | Repo path the step references (verbatim)             |
| `artifactStatus` | Verbatim status string from the artefact             |
| `derivation`     | `simulated` / `fixture` / `topology_only` / `bounded_inputs` / `unavailable` / `bag_backed` |
| `limitations`    | Explicit limitation notes                            |
| `nextProof`      | What the reviewer should do next                     |

## Selectors

`walkthroughSelectors.ts::selectFocusedAudit(input)` chooses the
focused audit from the loaded artefacts:

* matches by `missionId` when supplied;
* falls back to the first audit on disk;
* returns `audit=null` when no audits exist.

## Components

| Component                         | Role                                |
| --------------------------------- | ----------------------------------- |
| `ContextualWalkthroughOverlay`    | 10-step navigable container         |
| `WalkthroughMissionFocus`         | Shows the focused mission audit     |
| `WalkthroughEvidenceFocus`        | Step-bound evidence summary         |
| `WalkthroughLimitationCard`       | Explicit limitations for the step   |
| `WalkthroughProofStep`            | Next required proof                 |
| `WalkthroughSceneCue`             | Scene cue tied to the step          |

## Step → binding map

| Step                       | Source artefact                                       |
| -------------------------- | ----------------------------------------------------- |
| operator-request           | `rehearsal_audit.request`                             |
| proposal-generation        | `mission_proposals/<id>/proposal.json`                |
| sanitizer-decision         | `rehearsal_audit.plan` presence                       |
| compiler-result            | `rehearsal_audit.plan`                                |
| validator-result           | `rehearsal_audit.validation_diagnostics`              |
| supervisor-decision        | `rehearsal_audit.decision`                            |
| rehearsal-execution        | `rehearsal_audit.runtime`                             |
| replay-evidence            | `rehearsal_audit.replay` + registry record            |
| analytics-outcome          | `rehearsal_audit.analytics` + spatial replay          |
| unresolved-limitations     | rolled-up: every missing input                        |

## Honesty rules

* Each step renders evidence verbatim. Missing inputs become
  limitations, never silent zeros.
* A fixture replay NEVER renders as `bag_backed`. The
  unresolved-limitations step states `derivation_source · fixture`
  inline.
* Rejected missions remain rejected at every relevant step.
* The walkthrough never claims live runtime authority.

## Tests

`apps/mission-control/tests/contextual-walkthrough.test.tsx` pins:

* one binding per step;
* `ok` status when an audit is supplied;
* `unavailable` for every step when no audit;
* `rejected` propagation through the sanitizer step;
* `derivation_source` preservation;
* fixture-never-becomes-bag-backed at the limitations step;
* selector fallback behaviour;
* overlay navigation (next / back / reset).

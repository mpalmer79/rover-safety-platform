# Telemetry-Density Panel Guidelines

> All telemetry derives from committed artefacts. Nothing streams.

## Panel inventory

Twelve panels under `apps/mission-control/src/components/telemetry/`:

| Panel                       | Source artefact                                   |
| --------------------------- | ------------------------------------------------- |
| `MissionTelemetryPanel`     | `rehearsal_audit.runtime`                         |
| `SupervisorDecisionLog`     | `rehearsal_audit.decision`                        |
| `ReplayClockPanel`          | `rehearsal_audit.runtime.events`                  |
| `EventStreamPanel`          | `rehearsal_audit.runtime.events`                  |
| `VelocityCommandPanel`      | `mission_plan.waypoints`                          |
| `ReplayStatisticsPanel`     | `replay_bundle.json` + `rehearsal_analytics.json` |
| `MissionHealthPanel`        | rolled up `rehearsal_audit.*`                     |
| `PoseTracePanel`            | spatial-replay artefact                           |
| `TopicAvailabilityPanel`    | spatial-replay artefact                           |
| `EvidenceIntegrityPanel`    | artefact registry                                 |
| `ValidationOutcomePanel`    | `rehearsal_audit.validation_diagnostics`          |
| `RehearsalOutcomePanel`     | rolled up `rehearsal_audit.final_status`          |

Each panel uses the shared `TelemetryPanelFrame` chrome to render:

* a kicker line (audience-facing label),
* a single-line title,
* the derivation source (`derivation`), verbatim,
* optional integrity indicator (passed / partial / rejected /
  not_evaluated).

## Density modes

The design-system exposes three operator-density modes:

* `comfortable` — mobile + reviewer (walkthrough);
* `standard` — desktop default;
* `dense` — replay-analysis cockpit.

Each density resolves to a Tailwind padding scale via
`densitySpec()` in `@/design-system/spacing`. Panels should NEVER
hard-code padding; they consume the density spec exposed by the
parent workspace preset.

## Honesty rules for every telemetry panel

* Never use the words "live", "streaming", or "realtime".
* Always render the `derivation` field. If the field is absent on
  disk, the panel renders an em-dash, NOT a synthesised value.
* Never hard-code `bag_backed: true`. Always read the input.
* Empty / null states must explicitly say "no artefact" or "no
  events" rather than rendering zeros that look like real data.
* `/cmd_vel` is always rendered as a forbidden topic. The platform
  never publishes to it directly.

## Verification

`tests/telemetry.test.tsx` covers the rendered output and honest
empty-state behaviour. `tests/phase20-honesty.test.ts` enforces the
"no live", "no streaming", "no realtime" rule on every file in
`components/telemetry/`.

## Phase 20B — recipe-driven derivation

Panels can now consume a declarative recipe from
`apps/mission-control/src/telemetry-recipes/`. See
[`TELEMETRY_RECIPE_SYSTEM.md`](TELEMETRY_RECIPE_SYSTEM.md) for the
recipe model. Each recipe returns explicit `unavailable` results
when required inputs are missing; recipes never fabricate.

# Telemetry Recipe System

> Panels derive values from declared artifact recipes.
> Recipes never fabricate. Missing inputs become explicit
> unavailable states.

## Why

Phase 20 introduced twelve telemetry panels. Phase 20B factors the
artifact-query logic out of the panels into deterministic recipes.
This keeps panels composable, keeps the artifact contract explicit,
and makes the unavailable behaviour testable in isolation.

## Module layout

`apps/mission-control/src/telemetry-recipes/`

```
models.ts                    types: RecipeInput, RecipeOutput, TelemetryRecipe
recipeRegistry.ts            central registry: id → recipe
missionHealthRecipe.ts       rollup over rehearsal_audit.final_status
supervisorDecisionRecipe.ts  rollup over rehearsal_audit.decision
replayClockRecipe.ts         start/end ns from rehearsal_runtime.events
eventStreamRecipe.ts         severity counts from rehearsal_runtime.events
velocityCommandRecipe.ts     bounded waypoint values + /cmd_vel boundary
topicAvailabilityRecipe.ts   present/missing topics from spatial-replay
evidenceIntegrityRecipe.ts   passed/partial/rejected + bag-backed counts
validationOutcomeRecipe.ts   severity counts from validation_diagnostics
rehearsalOutcomeRecipe.ts    completed/rejected/aborted from audits
```

## Recipe shape

```ts
interface TelemetryRecipe {
  recipeId: string;
  requires: readonly RecipeArtifactKind[];
  optional: readonly RecipeArtifactKind[];
  compatibility: readonly string[];
  limitationNotes: readonly string[];
  derive: (input: RecipeInput) => RecipeOutput;
}

interface RecipeOutput {
  recipeId: string;
  status: "ok" | "partial" | "unavailable" | "rejected" | "not_evaluated";
  limitations: readonly string[];
  sources: readonly RecipeArtifactKind[];
  fields: Readonly<Record<string, string | number | boolean | null>>;
}
```

## Honesty rules

* Recipes NEVER fabricate values. Missing inputs ⇒ status `unavailable`.
* Recipes preserve `derivation_source` and `bag_backed` verbatim.
* The `velocity-command` recipe always names `/cmd_vel` as forbidden,
  even when no plan is loaded.
* Recipes never throw. Every recipe handles an empty input.

## Tests

`apps/mission-control/tests/telemetry-recipes.test.ts` pins:

* nine canonical recipes exposed by the registry;
* unavailable behaviour for every required-missing case;
* derivation_source + bag_backed preservation;
* never-throw guarantee.

## Future work

Panel components currently hold their own rendering logic. The next
phase should migrate panels to consume recipe output directly so
adding a panel is a recipe-and-component change rather than two
parallel data paths.

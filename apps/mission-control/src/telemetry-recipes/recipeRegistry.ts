/**
 * Phase 20B telemetry recipe registry.
 *
 * Central registry of declared recipes. Panels consult the registry
 * to obtain a recipe; adding a new recipe requires registering it
 * here AND adding a test in ``tests/telemetry-recipes.test.ts``.
 */

import { EVENT_STREAM_RECIPE } from "./eventStreamRecipe";
import { EVIDENCE_INTEGRITY_RECIPE } from "./evidenceIntegrityRecipe";
import { MISSION_HEALTH_RECIPE } from "./missionHealthRecipe";
import { REHEARSAL_OUTCOME_RECIPE } from "./rehearsalOutcomeRecipe";
import { REPLAY_CLOCK_RECIPE } from "./replayClockRecipe";
import { SUPERVISOR_DECISION_RECIPE } from "./supervisorDecisionRecipe";
import { TOPIC_AVAILABILITY_RECIPE } from "./topicAvailabilityRecipe";
import { VALIDATION_OUTCOME_RECIPE } from "./validationOutcomeRecipe";
import { VELOCITY_COMMAND_RECIPE } from "./velocityCommandRecipe";

import type { TelemetryRecipe } from "./models";

export const RECIPE_REGISTRY: Readonly<Record<string, TelemetryRecipe>> = {
  "mission-health": MISSION_HEALTH_RECIPE,
  "supervisor-decision": SUPERVISOR_DECISION_RECIPE,
  "replay-clock": REPLAY_CLOCK_RECIPE,
  "event-stream": EVENT_STREAM_RECIPE,
  "velocity-command": VELOCITY_COMMAND_RECIPE,
  "topic-availability": TOPIC_AVAILABILITY_RECIPE,
  "evidence-integrity": EVIDENCE_INTEGRITY_RECIPE,
  "validation-outcome": VALIDATION_OUTCOME_RECIPE,
  "rehearsal-outcome": REHEARSAL_OUTCOME_RECIPE,
};

export const RECIPE_IDS: readonly string[] = Object.keys(RECIPE_REGISTRY).sort();

export function recipe(id: string): TelemetryRecipe | null {
  return RECIPE_REGISTRY[id] ?? null;
}

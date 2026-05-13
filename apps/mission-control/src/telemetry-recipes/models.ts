/**
 * Phase 20B telemetry recipe model.
 *
 * A recipe is a deterministic declaration of how a telemetry panel
 * derives its output from committed artifacts. Panels MAY consume
 * recipes directly; new panels SHOULD consume recipes.
 *
 * Honesty rules:
 *   * a recipe NEVER fabricates a value;
 *   * a recipe returns an explicit ``unavailable`` result when a
 *     required artifact is missing;
 *   * a recipe preserves derivation_source / bag_backed verbatim.
 */

import type {
  ArtifactRegistryRecord,
  RehearsalAudit,
  RehearsalEvent,
  SpatialReplayArtifact,
  ValidationDiagnostic,
} from "@/adapters/types";

export type RecipeStatus =
  | "ok"
  | "partial"
  | "unavailable"
  | "rejected"
  | "not_evaluated";

export type RecipeArtifactKind =
  | "rehearsal_audit"
  | "rehearsal_runtime"
  | "mission_plan"
  | "supervisor_decision"
  | "replay_bundle"
  | "rehearsal_analytics"
  | "validation_diagnostics"
  | "spatial_replay"
  | "artifact_registry";

export interface RecipeInput {
  audit?: RehearsalAudit | null;
  audits?: readonly RehearsalAudit[];
  events?: readonly RehearsalEvent[];
  diagnostics?: readonly ValidationDiagnostic[];
  spatial?: SpatialReplayArtifact | null;
  registry?: readonly ArtifactRegistryRecord[];
}

export interface RecipeOutput {
  recipeId: string;
  status: RecipeStatus;
  limitations: readonly string[];
  /** Source kinds the recipe consulted. */
  sources: readonly RecipeArtifactKind[];
  /** Output fields, with values preserved verbatim from inputs. */
  fields: Readonly<Record<string, string | number | boolean | null>>;
}

export interface TelemetryRecipe {
  recipeId: string;
  /** Required artifact kinds. */
  requires: readonly RecipeArtifactKind[];
  /** Optional artifact kinds whose absence degrades to ``partial``. */
  optional: readonly RecipeArtifactKind[];
  /** Panel ids this recipe is compatible with. */
  compatibility: readonly string[];
  /** Documentation note (shown by the panel chrome). */
  limitationNotes: readonly string[];
  /** Pure function: input → output. Must never throw. */
  derive: (input: RecipeInput) => RecipeOutput;
}

export const UNAVAILABLE_OUTPUT = (
  recipeId: string,
  sources: readonly RecipeArtifactKind[],
  reason: string,
): RecipeOutput => ({
  recipeId,
  status: "unavailable",
  limitations: [reason],
  sources,
  fields: {},
});

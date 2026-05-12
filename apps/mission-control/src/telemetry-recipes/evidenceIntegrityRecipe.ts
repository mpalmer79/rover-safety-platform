import type { RecipeOutput, TelemetryRecipe } from "./models";

export const EVIDENCE_INTEGRITY_RECIPE: TelemetryRecipe = {
  recipeId: "evidence-integrity",
  requires: ["artifact_registry"],
  optional: [],
  compatibility: ["EvidenceIntegrityPanel"],
  limitationNotes: [
    "bag-backed counts are preserved verbatim from each registry record.",
  ],
  derive(input): RecipeOutput {
    const records = input.registry ?? [];
    if (records.length === 0) {
      return {
        recipeId: "evidence-integrity",
        status: "unavailable",
        limitations: ["No artefact registry record available."],
        sources: ["artifact_registry"],
        fields: {},
      };
    }
    const passed = records.filter((r) => r.integrity === "passed").length;
    const partial = records.filter((r) => r.integrity === "partial").length;
    const rejected = records.filter((r) => r.integrity === "rejected").length;
    const bagBacked = records.filter(
      (r) => r.derivation_source === "bag_backed",
    ).length;
    return {
      recipeId: "evidence-integrity",
      status: rejected > 0 ? "rejected" : partial > 0 ? "partial" : "ok",
      limitations: [],
      sources: ["artifact_registry"],
      fields: {
        total: records.length,
        passed,
        partial,
        rejected,
        bag_backed: bagBacked,
      },
    };
  },
};

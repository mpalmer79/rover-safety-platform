import type { RecipeOutput, TelemetryRecipe } from "./models";

export const MISSION_HEALTH_RECIPE: TelemetryRecipe = {
  recipeId: "mission-health",
  requires: ["rehearsal_audit"],
  optional: [],
  compatibility: ["MissionHealthPanel"],
  limitationNotes: [
    "Counters reflect only rehearsal audits on disk.",
    "Live runtime maturity remains not_established.",
  ],
  derive(input): RecipeOutput {
    const audits = input.audits ?? [];
    if (audits.length === 0) {
      return {
        recipeId: "mission-health",
        status: "unavailable",
        limitations: ["No rehearsal audits on disk."],
        sources: ["rehearsal_audit"],
        fields: {},
      };
    }
    const completed = audits.filter((a) => a.final_status === "completed").length;
    const rejected = audits.filter((a) => a.final_status === "rejected").length;
    const aborted = audits.filter((a) => a.final_status === "aborted").length;
    const needsReview = audits.filter(
      (a) => a.safety_status === "requires_review",
    ).length;
    const status =
      rejected + aborted > 0 ? "partial" : completed > 0 ? "ok" : "not_evaluated";
    return {
      recipeId: "mission-health",
      status,
      limitations: [],
      sources: ["rehearsal_audit"],
      fields: {
        total: audits.length,
        completed,
        rejected,
        aborted,
        needs_review: needsReview,
      },
    };
  },
};

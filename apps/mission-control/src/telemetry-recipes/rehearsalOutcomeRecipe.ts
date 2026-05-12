import type { RecipeOutput, TelemetryRecipe } from "./models";

export const REHEARSAL_OUTCOME_RECIPE: TelemetryRecipe = {
  recipeId: "rehearsal-outcome",
  requires: ["rehearsal_audit"],
  optional: ["rehearsal_analytics"],
  compatibility: ["RehearsalOutcomePanel"],
  limitationNotes: [
    "Outcome counts are rolled up from rehearsal_audit.final_status.",
  ],
  derive(input): RecipeOutput {
    const audits = input.audits ?? [];
    if (audits.length === 0) {
      return {
        recipeId: "rehearsal-outcome",
        status: "unavailable",
        limitations: ["No audits on disk."],
        sources: ["rehearsal_audit"],
        fields: {},
      };
    }
    const completed = audits.filter((a) => a.final_status === "completed").length;
    const rejected = audits.filter((a) => a.final_status === "rejected").length;
    const aborted = audits.filter((a) => a.final_status === "aborted").length;
    return {
      recipeId: "rehearsal-outcome",
      status:
        rejected + aborted > 0
          ? "partial"
          : completed > 0
            ? "ok"
            : "not_evaluated",
      limitations: [],
      sources: ["rehearsal_audit"],
      fields: { total: audits.length, completed, rejected, aborted },
    };
  },
};

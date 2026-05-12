import type { RecipeOutput, TelemetryRecipe } from "./models";

export const VALIDATION_OUTCOME_RECIPE: TelemetryRecipe = {
  recipeId: "validation-outcome",
  requires: ["validation_diagnostics"],
  optional: [],
  compatibility: ["ValidationOutcomePanel"],
  limitationNotes: [
    "Diagnostics are surfaced verbatim from rehearsal_audit.validation_diagnostics.",
  ],
  derive(input): RecipeOutput {
    const diagnostics = input.diagnostics ?? [];
    if (diagnostics.length === 0) {
      return {
        recipeId: "validation-outcome",
        status: "not_evaluated",
        limitations: ["No diagnostics emitted."],
        sources: ["validation_diagnostics"],
        fields: {
          rejection: 0,
          warning: 0,
          info: 0,
        },
      };
    }
    const rejection = diagnostics.filter((d) => d.severity === "rejection").length;
    const warning = diagnostics.filter((d) => d.severity === "warning").length;
    const info = diagnostics.filter((d) => d.severity === "info").length;
    return {
      recipeId: "validation-outcome",
      status: rejection > 0 ? "rejected" : warning > 0 ? "partial" : "ok",
      limitations: [],
      sources: ["validation_diagnostics"],
      fields: { rejection, warning, info, total: diagnostics.length },
    };
  },
};

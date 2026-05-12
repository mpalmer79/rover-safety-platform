import type { RecipeOutput, TelemetryRecipe } from "./models";

export const SUPERVISOR_DECISION_RECIPE: TelemetryRecipe = {
  recipeId: "supervisor-decision",
  requires: ["supervisor_decision"],
  optional: [],
  compatibility: ["SupervisorDecisionLog"],
  limitationNotes: [
    "Decisions are surfaced verbatim from rehearsal_audit.decision.",
  ],
  derive(input): RecipeOutput {
    const audits = input.audits ?? [];
    const decisions = audits.map((a) => a.decision).filter(Boolean);
    if (decisions.length === 0) {
      return {
        recipeId: "supervisor-decision",
        status: "unavailable",
        limitations: ["No supervisor decisions on disk."],
        sources: ["supervisor_decision"],
        fields: {},
      };
    }
    const rejected = decisions.filter((d) => d.decision_status === "rejected").length;
    const needsReview = decisions.filter(
      (d) => d.decision_status === "needs_review",
    ).length;
    return {
      recipeId: "supervisor-decision",
      status: rejected > 0 ? "rejected" : needsReview > 0 ? "partial" : "ok",
      limitations: [],
      sources: ["supervisor_decision"],
      fields: {
        total: decisions.length,
        rejected,
        needs_review: needsReview,
        approved:
          decisions.length - rejected - needsReview,
      },
    };
  },
};

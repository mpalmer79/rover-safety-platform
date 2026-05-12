import type { RecipeOutput, TelemetryRecipe } from "./models";

export const EVENT_STREAM_RECIPE: TelemetryRecipe = {
  recipeId: "event-stream",
  requires: ["rehearsal_runtime"],
  optional: [],
  compatibility: ["EventStreamPanel"],
  limitationNotes: [
    'The word "stream" describes the layout, not a live source.',
  ],
  derive(input): RecipeOutput {
    const events = input.events ?? [];
    if (events.length === 0) {
      return {
        recipeId: "event-stream",
        status: "unavailable",
        limitations: ["No events on disk for the selected audit."],
        sources: ["rehearsal_runtime"],
        fields: {},
      };
    }
    const rej = events.filter((e) => e.severity === "rejection").length;
    const warn = events.filter((e) => e.severity === "warning").length;
    return {
      recipeId: "event-stream",
      status: rej > 0 ? "rejected" : warn > 0 ? "partial" : "ok",
      limitations: [],
      sources: ["rehearsal_runtime"],
      fields: {
        total: events.length,
        rejection: rej,
        warning: warn,
        info: events.length - rej - warn,
      },
    };
  },
};

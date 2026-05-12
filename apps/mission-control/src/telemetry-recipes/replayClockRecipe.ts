import type { RecipeOutput, TelemetryRecipe } from "./models";

export const REPLAY_CLOCK_RECIPE: TelemetryRecipe = {
  recipeId: "replay-clock",
  requires: ["rehearsal_runtime"],
  optional: [],
  compatibility: ["ReplayClockPanel"],
  limitationNotes: [
    "Clock is parent-controlled. The recipe never ticks on its own.",
  ],
  derive(input): RecipeOutput {
    const events = input.events ?? [];
    if (events.length === 0) {
      return {
        recipeId: "replay-clock",
        status: "unavailable",
        limitations: ["No events on disk."],
        sources: ["rehearsal_runtime"],
        fields: {},
      };
    }
    const start = events[0].event_time_ns;
    const end = events[events.length - 1].event_time_ns;
    return {
      recipeId: "replay-clock",
      status: "ok",
      limitations: [],
      sources: ["rehearsal_runtime"],
      fields: {
        event_count: events.length,
        start_ns: start,
        end_ns: end,
        span_ns: Math.max(0, end - start),
      },
    };
  },
};

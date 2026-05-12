import type { RehearsalEvent } from "@/adapters/types";

import type { SceneCue } from "./sceneCueModel";

export function resolveEventFocus(
  events: readonly RehearsalEvent[],
  eventId: string | null,
): SceneCue | null {
  if (!eventId || events.length === 0) return null;
  const target = events.find((e) => e.event_id === eventId);
  if (!target) return null;
  return {
    kind: "trajectory_follow",
    cameraMode: "follow",
    focusTarget: target.event_subtype,
    focusRef: target.event_id,
    rationale: `Follow event ${target.event_id} (${target.severity}) at t=${target.event_time_ns}ns.`,
    order: 0,
  };
}

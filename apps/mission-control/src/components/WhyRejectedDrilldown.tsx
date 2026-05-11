import type { RehearsalAudit } from "@/adapters/types";
import { Panel } from "./Panel";
import { RequirementBadge } from "./RequirementBadge";

interface WhyRejectedDrilldownProps {
  audit: RehearsalAudit;
}

const REASON_NOTES: Record<string, { explainer: string; reqs: readonly string[] }> = {
  unsafe_speed: {
    explainer:
      "Speed exceeded the SAFETY_LIMITS.max_linear_speed_mps cap (0.5 m/s). " +
      "The validator rejects the plan before the supervisor sees it.",
    reqs: ["REQ-REHEARSAL-003", "REQ-MVIS-004"],
  },
  restricted_zone: {
    explainer:
      "Proposal source referenced a restricted corridor or forbidden zone. " +
      "Phase 16 safety scan rejects the plan; rehearsal never enters the " +
      "rehearsing state.",
    reqs: ["REQ-REHEARSAL-003", "REQ-MVIS-005"],
  },
  direct_actuator_command: {
    explainer:
      "Plan referenced /cmd_vel directly. The platform's authority chain " +
      "only permits /cmd_vel_requested for motion requests.",
    reqs: ["REQ-SAFE-001", "REQ-REHEARSAL-001"],
  },
  safety_override: {
    explainer:
      "Proposal source attempted to disable or bypass the safety " +
      "supervisor. The sanitizer rejects this verbatim.",
    reqs: ["REQ-PROPOSAL-003", "REQ-REHEARSAL-003"],
  },
  unbounded_loop: {
    explainer:
      "Mission referenced `while True` or `forever`. Every motion plan " +
      "must be duration-bounded.",
    reqs: ["REQ-REHEARSAL-002", "REQ-MVIS-006"],
  },
  missing_stop_condition: {
    explainer:
      "Motion plan did not end in a stop or dock waypoint. The validator " +
      "requires every motion-bearing plan to terminate explicitly.",
    reqs: ["REQ-REHEARSAL-003"],
  },
  out_of_range_parameter: {
    explainer:
      "A bounded parameter (distance, angle, speed) fell outside its " +
      "Phase 16 SAFETY_LIMITS envelope.",
    reqs: ["REQ-REHEARSAL-003"],
  },
};

export function WhyRejectedDrilldown({ audit }: WhyRejectedDrilldownProps) {
  if (audit.final_status !== "rejected") {
    return null;
  }
  const reason = audit.final_failure_reason || "unspecified";
  const note = REASON_NOTES[reason];

  return (
    <Panel
      eyebrow="Why this mission was rejected"
      title={`Failure reason: ${reason}`}
    >
      <div className="space-y-3 text-sm">
        <p className="leading-snug text-base-800">
          {note?.explainer ??
            "The validator or supervisor rejected this plan. See the " +
            "diagnostics below for the verbatim rejection codes."}
        </p>
        {audit.validation_diagnostics.length > 0 ? (
          <div>
            <p className="label mb-1">Validator diagnostics</p>
            <ul className="space-y-1">
              {audit.validation_diagnostics
                .filter((d) => d.severity === "rejection")
                .map((d, idx) => (
                  <li
                    key={`why-${idx}-${d.code}`}
                    className="font-mono text-xs text-status-rejected"
                  >
                    {d.code} — <span className="text-base-800">{d.message}</span>
                  </li>
                ))}
            </ul>
          </div>
        ) : null}
        {audit.decision.rejected_reasons.length > 0 ? (
          <div>
            <p className="label mb-1">Supervisor rejected reasons</p>
            <ul className="space-y-1">
              {audit.decision.rejected_reasons.map((r) => (
                <li key={r} className="font-mono text-xs text-status-rejected">
                  {r}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {note?.reqs && note.reqs.length > 0 ? (
          <div>
            <p className="label mb-1">Related requirements</p>
            <div className="flex flex-wrap gap-1.5">
              {note.reqs.map((req) => (
                <RequirementBadge
                  key={req}
                  reqId={req}
                  status="passed"
                  title="Linked requirement"
                />
              ))}
            </div>
          </div>
        ) : null}
        <p className="text-xs text-base-500">
          The state machine refused to enter <code>rehearsing</code>;
          no simulated motion events were generated for this plan.
        </p>
      </div>
    </Panel>
  );
}

import type { RehearsalAudit } from "@/adapters/types";
import { Panel } from "./Panel";

interface MissionStoryPanelProps {
  audit: RehearsalAudit;
}

interface StoryStep {
  eyebrow: string;
  title: string;
  description: string;
  status: "ok" | "warn" | "fail" | "info";
}

const STATUS_TONE: Record<StoryStep["status"], string> = {
  ok: "border-status-completed bg-status-completed/5 text-base-800",
  warn: "border-status-pending bg-status-pending/5 text-base-800",
  fail: "border-status-rejected bg-status-rejected/5 text-base-800",
  info: "border-base-300 bg-base-100 text-base-700",
};

/**
 * Mission narrative panel.
 *
 * Walks the operator through the lifecycle of one mission:
 * proposal → validation → approval → rehearsal → intervention →
 * completion / rejection → replay review → evidence verification.
 *
 * The story is derived entirely from the audit; it never invents
 * a step that the audit does not justify.
 */
export function MissionStoryPanel({ audit }: MissionStoryPanelProps) {
  const steps = buildSteps(audit);
  return (
    <Panel
      eyebrow="Mission narrative"
      title="What happened"
      trailing={
        <span className="text-[11px] font-mono text-base-500">
          {steps.length} steps
        </span>
      }
    >
      <ol
        data-testid="mission-story-panel"
        className="space-y-2 text-[12px]"
      >
        {steps.map((step, idx) => (
          <li
            key={`${idx}-${step.title}`}
            data-testid={`story-step-${idx}`}
            data-status={step.status}
            className={`rounded border-l-2 px-3 py-2 ${STATUS_TONE[step.status]}`}
          >
            <p className="font-mono text-[10px] uppercase tracking-wide text-base-500">
              {step.eyebrow}
            </p>
            <p className="font-medium text-base-900">{step.title}</p>
            <p className="text-base-700">{step.description}</p>
          </li>
        ))}
      </ol>
    </Panel>
  );
}

function buildSteps(audit: RehearsalAudit): StoryStep[] {
  const steps: StoryStep[] = [];
  steps.push({
    eyebrow: "1. Proposal",
    title: audit.request.description || audit.request.mission_id,
    description: `Operator: ${audit.request.operator || "—"}. Source: ${
      audit.request.proposal_source || "(not provided)"
    }.`,
    status: "info",
  });

  const rejections = audit.validation_diagnostics.filter(
    (d) => d.severity === "rejection",
  );
  steps.push({
    eyebrow: "2. Validation",
    title:
      rejections.length === 0
        ? "Validator accepted the plan"
        : `Validator rejected the plan (${rejections.length} rejection${rejections.length === 1 ? "" : "s"})`,
    description:
      rejections.length === 0
        ? "All bounded-input constraints + topic-allowlist checks passed."
        : rejections
            .slice(0, 3)
            .map((r) => `${r.code}: ${r.message}`)
            .join("; "),
    status: rejections.length === 0 ? "ok" : "fail",
  });

  steps.push({
    eyebrow: "3. Supervisor authority",
    title:
      audit.decision.decision_status === "approved"
        ? "Supervisor approved the plan"
        : audit.decision.decision_status === "rejected"
          ? "Supervisor rejected the plan"
          : "Supervisor flagged the plan for review",
    description:
      audit.decision.rationale.slice(0, 2).join(" · ") ||
      "No supervisor rationale recorded.",
    status:
      audit.decision.decision_status === "approved"
        ? "ok"
        : audit.decision.decision_status === "rejected"
          ? "fail"
          : "warn",
  });

  if (audit.runtime) {
    const interventions = audit.runtime.events.filter(
      (e) => e.severity === "rejection" || e.event_type === "supervisor",
    );
    steps.push({
      eyebrow: "4. Rehearsal",
      title: `${audit.runtime.events.length} deterministic events`,
      description: `Started ${audit.runtime.started_at_utc}; finished ${audit.runtime.finished_at_utc}.`,
      status: "info",
    });
    if (interventions.length > 0) {
      steps.push({
        eyebrow: "5. Intervention",
        title: `${interventions.length} supervisor intervention${interventions.length === 1 ? "" : "s"}`,
        description: interventions
          .slice(0, 3)
          .map((e) => `${e.event_subtype}: ${e.description}`)
          .join("; "),
        status: "warn",
      });
    }
  } else {
    steps.push({
      eyebrow: "4. Rehearsal",
      title: "Rehearsal not executed",
      description:
        "The validator or supervisor rejected the plan before runtime.",
      status: "fail",
    });
  }

  const finalIsBad =
    audit.final_status === "rejected" || audit.final_status === "aborted";
  steps.push({
    eyebrow: finalIsBad ? "Outcome" : `${audit.runtime ? "6" : "5"}. Outcome`,
    title:
      audit.final_status === "completed"
        ? "Mission completed deterministically"
        : audit.final_status === "rejected"
          ? `Mission rejected: ${audit.final_failure_reason || "(no reason)"}`
          : audit.final_status === "aborted"
            ? `Mission aborted: ${audit.final_failure_reason || "(no reason)"}`
            : `Final state: ${audit.final_status}`,
    description: `Safety status: ${audit.safety_status}.`,
    status: finalIsBad ? "fail" : "ok",
  });

  if (audit.replay) {
    steps.push({
      eyebrow: "Replay",
      title: `${audit.replay.replay_markers.length} replay markers · review ${audit.replay.review_status}`,
      description: `Evidence: ${audit.replay.evidence_status}; bag-backed: ${audit.replay.bag_backed ? "yes" : "no"}.`,
      status: audit.replay.bag_backed ? "ok" : "warn",
    });
  }
  return steps;
}

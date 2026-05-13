/**
 * Phase 20B contextual walkthrough.
 *
 * Upgrades the informational walkthrough so each step binds to the
 * currently selected mission. The selectors below convert a
 * ``RehearsalAudit`` (+ optional registry record + spatial replay)
 * into per-step evidence, status, and limitation notes.
 *
 * Honesty rules:
 *   * a step never claims evidence it cannot reference verbatim;
 *   * missing evidence becomes an explicit limitation;
 *   * rejected missions remain visibly rejected at every step.
 */

import type {
  ArtifactRegistryRecord,
  RehearsalAudit,
  SpatialReplayArtifact,
} from "@/adapters/types";

import type { WalkthroughStepId } from "./steps";

export type StepBindingStatus =
  | "ok"
  | "rejected"
  | "partial"
  | "unavailable"
  | "not_evaluated";

export type DerivationFlavor =
  | "simulated"
  | "fixture"
  | "topology_only"
  | "bounded_inputs"
  | "unavailable"
  | "bag_backed";

export interface StepBinding {
  step: WalkthroughStepId;
  status: StepBindingStatus;
  /** Human-readable headline. */
  headline: string;
  /** Optional artifact path referenced by the step. */
  artifactRef: string | null;
  /** Verbatim status string from the artifact when available. */
  artifactStatus: string | null;
  /** Derivation flavor — preserves spatial-replay distinctions. */
  derivation: DerivationFlavor;
  /** Limitation notes (rendered as a bulleted list). */
  limitations: readonly string[];
  /** Next required proof step (the thing a reviewer should do next). */
  nextProof: string | null;
}

export interface ContextualInputs {
  audit: RehearsalAudit | null;
  registry: ArtifactRegistryRecord | null;
  spatial: SpatialReplayArtifact | null;
}

/** Build a binding for every walkthrough step, in order. */
export function buildStepBindings(input: ContextualInputs): readonly StepBinding[] {
  return [
    bindOperatorRequest(input),
    bindProposalGeneration(input),
    bindSanitizer(input),
    bindCompiler(input),
    bindValidator(input),
    bindSupervisor(input),
    bindRehearsalExecution(input),
    bindReplayEvidence(input),
    bindAnalytics(input),
    bindUnresolvedLimitations(input),
  ];
}

function bindOperatorRequest({ audit }: ContextualInputs): StepBinding {
  if (!audit) {
    return unavailable(
      "operator-request",
      "No rehearsal audit selected",
      "Select a mission with a committed audit to populate this step.",
    );
  }
  return {
    step: "operator-request",
    status: "ok",
    headline: `request_id · ${audit.request.request_id}`,
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: audit.request.proposal_source,
    derivation: "simulated",
    limitations: [],
    nextProof: "Open the proposal and confirm the request signature.",
  };
}

function bindProposalGeneration({ audit }: ContextualInputs): StepBinding {
  if (!audit) return missing("proposal-generation");
  return {
    step: "proposal-generation",
    status: "ok",
    headline: `source · ${audit.request.proposal_source}`,
    artifactRef:
      "mission-proposals/" + audit.request.mission_id + "/proposal.json",
    artifactStatus: null,
    derivation: "simulated",
    limitations: audit.plan
      ? []
      : ["No compiled plan attached — proposal was rejected upstream."],
    nextProof: "Inspect the proposal payload for forbidden topics.",
  };
}

function bindSanitizer({ audit }: ContextualInputs): StepBinding {
  if (!audit) return missing("sanitizer-decision");
  const status: StepBindingStatus = audit.plan ? "ok" : "rejected";
  return {
    step: "sanitizer-decision",
    status,
    headline: audit.plan ? "sanitizer passed" : "sanitizer rejected",
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: audit.plan ? "sanitized" : "rejected",
    derivation: "simulated",
    limitations: audit.plan
      ? []
      : ["Sanitizer rejection truncates the downstream pipeline."],
    nextProof: "Confirm forbidden_topics contains /cmd_vel.",
  };
}

function bindCompiler({ audit }: ContextualInputs): StepBinding {
  if (!audit) return missing("compiler-result");
  if (!audit.plan) {
    return {
      step: "compiler-result",
      status: "unavailable",
      headline: "no compiled plan",
      artifactRef: null,
      artifactStatus: null,
      derivation: "unavailable",
      limitations: ["Compiler did not emit a plan for this audit."],
      nextProof: "Re-run the compiler against a sanitized proposal.",
    };
  }
  return {
    step: "compiler-result",
    status: "ok",
    headline: `risk_band · ${audit.plan.risk_band}`,
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: audit.plan.deterministic_hash.slice(0, 12),
    derivation: "simulated",
    limitations: [],
    nextProof: "Verify deterministic_hash matches the registry record.",
  };
}

function bindValidator({ audit }: ContextualInputs): StepBinding {
  if (!audit) return missing("validator-result");
  const rejection = audit.validation_diagnostics.filter(
    (d) => d.severity === "rejection",
  ).length;
  const warning = audit.validation_diagnostics.filter(
    (d) => d.severity === "warning",
  ).length;
  const status: StepBindingStatus =
    rejection > 0 ? "rejected" : warning > 0 ? "partial" : "ok";
  return {
    step: "validator-result",
    status,
    headline: `${rejection} rejection · ${warning} warning`,
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: rejection > 0 ? "rejected" : "passed",
    derivation: "simulated",
    limitations:
      audit.validation_diagnostics.length === 0
        ? ["No diagnostics emitted by the validator."]
        : [],
    nextProof: "Read each diagnostic message verbatim.",
  };
}

function bindSupervisor({ audit }: ContextualInputs): StepBinding {
  if (!audit) return missing("supervisor-decision");
  const decision = audit.decision;
  const status: StepBindingStatus =
    decision.decision_status === "rejected"
      ? "rejected"
      : decision.decision_status === "needs_review"
        ? "partial"
        : "ok";
  return {
    step: "supervisor-decision",
    status,
    headline: `decision · ${decision.decision_status}`,
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: decision.safety_status,
    derivation: "simulated",
    limitations: decision.requires_human_review
      ? ["Human review required before any further action."]
      : [],
    nextProof: "Compare allowed_topics + forbidden_topics with the plan.",
  };
}

function bindRehearsalExecution({ audit }: ContextualInputs): StepBinding {
  if (!audit) return missing("rehearsal-execution");
  if (!audit.runtime) {
    return {
      step: "rehearsal-execution",
      status: "unavailable",
      headline: "no rehearsal runtime",
      artifactRef: null,
      artifactStatus: audit.final_status,
      derivation: "unavailable",
      limitations: ["Rehearsal did not execute — supervisor blocked or aborted."],
      nextProof: "Resolve the supervisor decision before re-attempting.",
    };
  }
  return {
    step: "rehearsal-execution",
    status:
      audit.runtime.final_status === "completed"
        ? "ok"
        : audit.runtime.final_status === "rejected"
          ? "rejected"
          : "partial",
    headline: `events · ${audit.runtime.events.length}`,
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: audit.runtime.final_status,
    derivation: "simulated",
    limitations: [],
    nextProof: "Inspect each event's deterministic_hash for drift.",
  };
}

function bindReplayEvidence({ audit, registry }: ContextualInputs): StepBinding {
  if (!audit) return missing("replay-evidence");
  if (!audit.replay) {
    return {
      step: "replay-evidence",
      status: "unavailable",
      headline: "no replay bundle",
      artifactRef: null,
      artifactStatus: null,
      derivation: "unavailable",
      limitations: ["No replay bundle was produced for this audit."],
      nextProof: "Regenerate the replay bundle from the rehearsal runtime.",
    };
  }
  const derivation: DerivationFlavor = audit.replay.bag_backed
    ? "bag_backed"
    : "simulated";
  return {
    step: "replay-evidence",
    status: audit.replay.review_status === "passed" ? "ok" : "partial",
    headline: `evidence_status · ${audit.replay.evidence_status}`,
    artifactRef:
      registry?.files[0]?.relative_path ??
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: audit.replay.review_status,
    derivation,
    limitations: audit.replay.bag_backed
      ? []
      : ["bag_backed is false — replay is simulated, not bag-derived."],
    nextProof: "Confirm bag_backed matches the registry derivation_source.",
  };
}

function bindAnalytics({ audit, spatial }: ContextualInputs): StepBinding {
  if (!audit) return missing("analytics-outcome");
  const derivation: DerivationFlavor = spatial
    ? (spatial.derivation_source as DerivationFlavor)
    : "unavailable";
  if (!audit.analytics) {
    return {
      step: "analytics-outcome",
      status: "unavailable",
      headline: "no analytics",
      artifactRef: null,
      artifactStatus: null,
      derivation,
      limitations: ["No analytics rollup was produced."],
      nextProof: "Run the analytics aggregator over committed audits.",
    };
  }
  return {
    step: "analytics-outcome",
    status: audit.analytics.deterministic_replay_stable ? "ok" : "partial",
    headline: `rehearsals · ${audit.analytics.rehearsal_count}`,
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: audit.analytics.deterministic_replay_stable
      ? "stable"
      : "drifted",
    derivation,
    limitations:
      derivation === "bag_backed"
        ? []
        : ["Analytics reflect simulated runs only."],
    nextProof: "Compare deterministic_replay_stable across two runs.",
  };
}

function bindUnresolvedLimitations(input: ContextualInputs): StepBinding {
  const { audit, spatial } = input;
  if (!audit) {
    return unavailable(
      "unresolved-limitations",
      "No mission selected",
      "Select a mission with a committed audit.",
    );
  }
  const limitations: string[] = [];
  if (!audit.replay) limitations.push("No replay bundle attached.");
  if (!audit.runtime) limitations.push("No rehearsal runtime attached.");
  if (!spatial) limitations.push("No spatial-replay artifact for this run.");
  else if (spatial.derivation_source !== "bag_backed") {
    limitations.push(
      `derivation_source · ${spatial.derivation_source} — never claim bag-backed.`,
    );
  }
  return {
    step: "unresolved-limitations",
    status: limitations.length === 0 ? "ok" : "partial",
    headline:
      limitations.length === 0
        ? "no unresolved limitations"
        : `${limitations.length} unresolved limitation(s)`,
    artifactRef:
      "mission-rehearsals/audits/" + audit.request.request_id + "/audit.json",
    artifactStatus: audit.disclaimer,
    derivation: spatial
      ? (spatial.derivation_source as DerivationFlavor)
      : "unavailable",
    limitations,
    nextProof:
      "Leave the limitations list visible to the reviewer at the end.",
  };
}

function missing(step: WalkthroughStepId): StepBinding {
  return unavailable(
    step,
    "No mission selected",
    "Select a mission with a committed audit.",
  );
}

function unavailable(
  step: WalkthroughStepId,
  headline: string,
  proof: string,
): StepBinding {
  return {
    step,
    status: "unavailable",
    headline,
    artifactRef: null,
    artifactStatus: null,
    derivation: "unavailable",
    limitations: [headline],
    nextProof: proof,
  };
}

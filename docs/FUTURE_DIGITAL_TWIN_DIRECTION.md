# Future Digital Twin Direction

The platform is **not safety-certified.** This document describes
where Phase 16 could go if a follow-up phase wires the rehearsal
pipeline into a richer digital twin or, eventually, into a real
robot. Phase 16 itself implements none of this; the rehearsal
runtime is simulation-only and deterministic.

## 1. What Phase 16 already provides

* a deterministic mission plan + validator + supervisor + state
  machine + event stream + replay bundle + analytics result + audit
  bundle;
* an honest layer of failure modes (validator-rejected,
  supervisor-rejected, aborted, completed) with per-cause
  failure-reason codes;
* a filesystem schema that mirrors the Phase 7 / Phase 8 replay
  + analytics layout, so downstream programme-review tooling can
  consume rehearsal artifacts directly.

## 2. What a future phase MUST add

1. **Higher-fidelity simulator.** Replace the deterministic
   "simulated motion" events with a Gazebo Harmonic rehearsal run
   inside the existing self-hosted Jazzy workflow
   (`docs/SELF_HOSTED_JAZZY_RUNNER_SETUP.md`). The Phase 13 live
   runtime maturity layer already defines the bag-backed contract;
   the new phase plugs Phase 16 into the live workflow.
2. **Bag-backed replay handoff.** Replace
   `bag_backed=False` with the real classification produced by
   `app.live_runtime.bag_manifest.inspect_bag_directory`. The
   honesty rule remains: no bag artifact, no bag-backed claim.
3. **Programme-review aggregation.** Aggregate per-rehearsal
   analytics into the existing programme-review trends with an
   `origin_mix_label` that distinguishes Phase 16 (simulated)
   counts from real bag-backed counts.
4. **Operator-in-the-loop UI.** The audit bundle already carries
   code-card-style metadata in the replay-review Markdown; a UI
   could render it. Phase 16 deliberately does not ship a UI.

## 3. What a future phase MUST NOT do

* publish to `/cmd_vel` directly;
* skip the safety supervisor;
* mutate the safety supervisor state from inside the rehearsal
  layer;
* call cloud APIs;
* mark Phase 16 rehearsal artifacts as bag-backed;
* mix Phase 16 analytics with bag-backed analytics without explicit
  origin labelling.

## 4. Suggested order of operations

1. Land an ADR documenting the digital-twin scope and the
   rollback plan.
2. Implement the new transport (Gazebo runner, bag capture,
   replay-review attachment) behind an env-var gate so the default
   CI lane still uses the deterministic rehearsal runtime.
3. Run the existing Phase 16 test suite — it must continue to
   pass.
4. Demonstrate rollback by switching back to the deterministic
   runtime and confirming the same rehearsal bundles are
   produced.

## 5. The default remains deterministic

Even after a future digital-twin transport is added, the default
rehearsal runtime must remain the deterministic state machine.
The deterministic-replay-stable guarantee is the project's
foundation for honest analytics.

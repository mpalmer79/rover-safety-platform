# Deferred Phases

The platform is **not safety-certified.** This document captures the
follow-up phases that are intentionally *not* implemented today. Each
section describes what the current phase ships, what a future phase
must add, what it must never do, and the suggested order of
operations.

Use the anchors below when linking from requirements or runbooks:

- [LLM mission proposal layer](#1-llm-mission-proposal-layer) — anchor: `llm-mission-proposal-layer`
- [Local LLM skill provider](#2-local-llm-skill-provider) — anchor: `local-llm-skill-provider`
- [Local model operations](#3-local-model-operations) — anchor: `local-model-operations`
- [Digital twin direction](#4-digital-twin-direction) — anchor: `digital-twin-direction`

---

## 1. LLM mission proposal layer
<a id="llm-mission-proposal-layer"></a>

What a follow-up phase would need to add if it ever wires up a real
LLM provider to the Phase 14B mission proposal seam. Phase 14B does
**not** implement any of it.

### What Phase 14B already provides

* a typed `ProposalProvider` interface (`backend/app/mission_proposal/provider.py`),
* a deterministic `MockProposalProvider` for offline tests,
* the `external_provider_disabled_response()` helper that any CLI
  must call when an external mode is requested,
* a sanitizer that rejects unsafe / off-task text,
* an adapter that funnels sanitized text into the Phase 14A
  deterministic compiler,
* an audit bundle layout with a fixed disclaimer.

A future external provider plugs into the same seam.

### What a future external-provider phase MUST add

1. **Provider implementation** that satisfies the `ProposalProvider`
   protocol and emits a `MissionProposal` value object. The
   implementation must be the only module that imports an LLM SDK,
   and it must not be imported by tests that run on the
   GitHub-hosted CI lane.
2. **Network egress boundary**: the provider's network call must be
   the only network call in `backend/app/mission_proposal/`. The
   adapter, sanitizer, validator, and audit must remain offline.
3. **Provenance fields**: every external proposal must record
   `provider_endpoint`, `provider_model`, `provider_request_id`, and
   `provider_response_id` in `raw_response` (or in additional
   audit fields).
4. **Cost + rate-limiting**: a budget cap with deterministic
   `not_configured` fall-back. Exceeding the cap must produce
   `final_outcome: provider_budget_exceeded`, never silent retries.
5. **An ADR** documenting the choice of provider, the privacy
   policy, the data-retention story, and the rollback plan.
6. **Updated tests**: the existing tests must keep passing
   unchanged; new tests must exercise the network-disabled fall-back
   and the budget cap.
7. **Updated docs**:
   - `docs/LLM_MISSION_PROPOSAL_LAYER.md` — mention the new mode
   - `docs/LLM_SAFETY_BOUNDARY.md` — record the new boundary
   - this section — strike the "aspirational" disclaimer

### What a future phase MUST NOT do

* publish to `/cmd_vel` or `/cmd_vel_authorized` from any path,
* mutate safety supervisor state,
* remove or weaken any sanitizer rule,
* skip the deterministic Phase 14A compiler,
* mark a proposal `compiled_validation_passed` without the compiler
  having actually returned `compile_ok` or `compile_ok_with_warnings`,
* fabricate runtime evidence,
* re-use a previous audit bundle as if it were a new run.

### Order of operations for the future phase

1. Land an ADR.
2. Implement the new provider in isolation.
3. Wire it into `resolve_provider`.
4. Add provider tests behind an env-var gate so they do not run on
   GitHub-hosted CI.
5. Run the existing offline test suite — it must continue to pass.
6. Demonstrate the rollback by switching the provider back to
   `mock` or `external_disabled`.
7. Update the Phase 14B requirements registry to point to the new
   tests; do not retire the existing REQ-PROPOSAL-* requirements.

### The default remains offline

Even after a future external provider is added, the default
`--provider` argument on every CLI must remain `mock`. External
modes must be opt-in, documented, and audited.

The runtime safety supervisor remains the only path to authorised
motion. No future LLM integration changes that.

---

## 2. Local LLM skill provider
<a id="local-llm-skill-provider"></a>

What a follow-up phase would have to add if it ever wires up a local
LLM (Ollama, llama.cpp, vLLM, or similar) to *propose* skill
candidates. Phase 15A does **not** implement any of it.

### What Phase 15A already provides

* a deterministic intent parser
  (`backend/app/skill_authoring/intent_parser.py`);
* a closed template catalog (`catalog.py` + `templates.py`);
* a safety validator (`validator.py`) that rejects unsafe rendered
  code regardless of where the candidate came from;
* a safety review + audit bundle + code card payload;
* CLIs that operate offline and never execute generated code.

A future local-LLM provider plugs into the *front* of this
pipeline. The validator and audit layer remain authoritative.

### What a future provider MUST add

1. A provider implementation that wraps Ollama / llama.cpp / vLLM
   in an interface compatible with the parser: it must produce a
   structured `SkillCandidate`-like proposal, not free text.
2. A sanitizer step that rejects model outputs whose proposed
   parameters fall outside catalog bounds (distance > 25 m, speed
   > 0.5 m/s, etc.).
3. Provenance fields recorded into the audit bundle: model name,
   model digest, context-window settings, prompt hash, response
   hash.
4. An offline-default mode: even with a local LLM available, the
   default behaviour must remain the deterministic parser.
5. Tests that prove:
   - the deterministic parser still catches every Phase 15A
     rejection case if the LLM is removed;
   - the validator still rejects forbidden code;
   - the LLM never invents waypoint names that the catalog does
     not know about.

### What a future provider MUST NOT do

* call OpenAI / Anthropic / Cohere / Vertex / Replicate (no
  external SDKs);
* open a network socket from `backend/app/skill_authoring/`;
* mutate the safety supervisor;
* publish to `/cmd_vel` or `/cmd_vel_authorized`;
* execute generated code;
* skip the validator;
* remove the safety review;
* replace the deterministic catalog with model-generated templates.

### Why the deterministic parser stays

A local LLM is useful for *paraphrase tolerance*: "could you have
the robot scoot ahead by about a metre" is the kind of phrasing the
deterministic parser will reject as ambiguous. A future LLM would
translate that into a canonical `SkillCandidate` shape; the
catalog and the validator stay authoritative.

The local LLM never gets to invent waypoint names, override
distance bounds, or weaken the comment header. Anything outside
the catalog produces an `unsupported_instruction` diagnostic, even
when the LLM is on.

### Suggested order of operations

1. Land an ADR documenting model choice, local hardware
   requirements, and rollback plan.
2. Implement the provider in isolation under
   `backend/app/skill_authoring/providers/local/...`.
3. Add provider tests behind an env-var gate so they do not run on
   the default CI lane.
4. Run the existing Phase 15A test suite — it must continue to
   pass unchanged.
5. Demonstrate the rollback by switching `--provider` back to
   `deterministic` (or whatever the default flag name becomes).

### Phase 15B status

Phase 15B (Local LLM Skill Candidate Provider) is implemented as
a *disabled-by-default* seam. See
[`LOCAL_LLM_SKILL_PROVIDER.md`](LOCAL_LLM_SKILL_PROVIDER.md),
[`LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md`](LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md),
and section 3 below for the operational plan a follow-up phase
must satisfy before a real local model is wired up. Phase 15B
does **not** call cloud APIs, does **not** open a network
socket, and does **not** execute generated code.

---

## 3. Local model operations
<a id="local-model-operations"></a>

The operational plan a follow-up phase must satisfy before wiring
up a real local LLM (Ollama, llama.cpp, vLLM, or similar) to the
Phase 15B provider seam.

**Phase 19 update:** the readiness check, capability registry, and
ranking layers shipped in Phase 19 (see
`docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md`). What remains
aspirational is **enabling a real local provider in production**:
the provider remains disabled by default and the capability
registry's `qualified` flag is `False` for every real model until
a reviewer signs the local qualification checklist.

### What Phase 15B already provides

* a stable `SkillLLMProvider` interface;
* a deterministic fixture provider used by tests;
* three policy-only stubs (`local_http`, `ollama`, `llama_cpp`)
  that exercise the opt-in check, the endpoint policy, and the
  `not_configured` envelope without opening a socket;
* a sanitizer that rejects unsafe candidate text;
* a validator bridge that hands sanitized candidates to the Phase
  15A skill validator;
* an audit bundle with the verbatim disclaimer.

A future phase that adds real model inference plugs into the same
seam. The validator and audit layer remain authoritative.

### What a future phase MUST add

1. **Real provider implementation**, e.g.
   `backend/app/skill_llm_provider/transports/ollama_transport.py`,
   that satisfies the existing `SkillLLMProvider` interface and is
   the only module that imports the model SDK or opens a socket.
2. **Loopback-only enforcement at the transport layer.** The
   `require_local_endpoint` policy check in `config.py` already
   rejects cloud hosts, but the transport must double-check before
   it issues the call.
3. **Timeout + budget cap.** A bounded per-request timeout, a
   cumulative cost / token budget, and a deterministic
   `provider_budget_exceeded` envelope when the cap is hit.
4. **Provenance fields** recorded into the candidate's
   `raw_provider_payload` (model digest, request id, response id,
   prompt hash) so the audit lets a reviewer trace any accepted
   snippet back to the model version that proposed it.
5. **Rollback plan.** A documented switch back to `mode=fixture`
   or `mode=disabled` for any reason — including operator stress,
   model drift, or regulatory request.
6. **An ADR** documenting the choice of model, the privacy /
   data-retention policy, the hardware requirements, and the
   rollback plan.
7. **Updated tests** that exercise the transport layer behind an
   env-var gate so they do not run on the default CI lane.
8. **Updated docs**:
   - `docs/LOCAL_LLM_SKILL_PROVIDER.md` — mention the live mode;
   - `docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md` — record the new
     boundary;
   - this section — strike the "aspirational" preamble.

### What a future phase MUST NOT do

* call OpenAI / Anthropic / Cohere / Vertex / Replicate;
* open a network socket to anything that is not loopback;
* mutate the safety supervisor;
* publish to `/cmd_vel` or `/cmd_vel_authorized`;
* execute generated code;
* skip the sanitizer or the Phase 15A validator;
* mark a candidate accepted without the validator having actually
  passed it;
* fabricate runtime evidence;
* re-use a previous audit as if it were a new run;
* remove the verbatim Phase 15B disclaimer.

### Suggested order of operations

1. Land an ADR.
2. Implement the transport in isolation under
   `backend/app/skill_llm_provider/transports/...`.
3. Run the existing Phase 15B test suite — it must continue to
   pass.
4. Add transport-only tests behind `ROVER_SKILL_LLM_E2E=1` (or
   similar env-var gate).
5. Demonstrate the rollback by flipping `mode` back to `fixture`
   or `disabled` and confirming downstream tools still work.
6. Update the Phase 15B requirements registry to point to the new
   tests; do NOT retire the existing REQ-SKILL-LLM-* requirements.

### The default remains offline

Even after a future local model is wired up, the default
`--provider` argument on every CLI must remain `disabled`. Local
modes must be opt-in (CLI flag + config flag + loopback endpoint).
The runtime safety supervisor remains the only path to actuator
authority.

### Phase 16 hand-off

Phase 16 (Governed Mission-to-Rehearsal Pipeline) already
consumes the deterministic skill validator path. A future local
model is therefore one input among several into the rehearsal
runtime; see `docs/GOVERNED_MISSION_REHEARSAL.md` for the
mission-to-rehearsal contract and section 4 below for the path to
a real-robot digital twin.

---

## 4. Digital twin direction
<a id="digital-twin-direction"></a>

Where Phase 16 could go if a follow-up phase wires the rehearsal
pipeline into a richer digital twin or, eventually, into a real
robot. Phase 16 itself implements none of this; the rehearsal
runtime is simulation-only and deterministic.

### What Phase 16 already provides

* a deterministic mission plan + validator + supervisor + state
  machine + event stream + replay bundle + analytics result + audit
  bundle;
* an honest layer of failure modes (validator-rejected,
  supervisor-rejected, aborted, completed) with per-cause
  failure-reason codes;
* a filesystem schema that mirrors the Phase 7 / Phase 8 replay
  + analytics layout, so downstream programme-review tooling can
  consume rehearsal artifacts directly.

### What a future phase MUST add

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

### What a future phase MUST NOT do

* publish to `/cmd_vel` directly;
* skip the safety supervisor;
* mutate the safety supervisor state from inside the rehearsal
  layer;
* call cloud APIs;
* mark Phase 16 rehearsal artifacts as bag-backed;
* mix Phase 16 analytics with bag-backed analytics without explicit
  origin labelling.

### Suggested order of operations

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

### The default remains deterministic

Even after a future digital-twin transport is added, the default
rehearsal runtime must remain the deterministic state machine.
The deterministic-replay-stable guarantee is the project's
foundation for honest analytics.

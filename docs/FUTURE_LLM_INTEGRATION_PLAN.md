# Future LLM Integration Plan

The platform is **not safety-certified.** This document describes
what a follow-up phase would need to add if it ever wires up a real
LLM provider. It is intentionally aspirational; Phase 14B does
**not** implement any of it.

## 1. What Phase 14B already provides

* a typed `ProposalProvider` interface (`backend/app/mission_proposal/provider.py`),
* a deterministic `MockProposalProvider` for offline tests,
* the `external_provider_disabled_response()` helper that any CLI
  must call when an external mode is requested,
* a sanitizer that rejects unsafe / off-task text,
* an adapter that funnels sanitized text into the Phase 14A
  deterministic compiler,
* an audit bundle layout with a fixed disclaimer.

A future external provider plugs into the same seam.

## 2. What a future external-provider phase MUST add

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
   - this file — strike the "intentionally aspirational" disclaimer

## 3. What a future phase MUST NOT do

* publish to `/cmd_vel` or `/cmd_vel_authorized` from any path,
* mutate safety supervisor state,
* remove or weaken any sanitizer rule,
* skip the deterministic Phase 14A compiler,
* mark a proposal `compiled_validation_passed` without the compiler
  having actually returned `compile_ok` or `compile_ok_with_warnings`,
* fabricate runtime evidence,
* re-use a previous audit bundle as if it were a new run.

## 4. Order of operations for the future phase

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

## 5. The default remains offline

Even after a future external provider is added, the default
`--provider` argument on every CLI must remain `mock`. External
modes must be opt-in, documented, and audited.

The runtime safety supervisor remains the only path to authorised
motion. No future LLM integration changes that.

# Future Local Model Operations

The platform is **not safety-certified.** This document describes
the operational plan a follow-up phase must satisfy before wiring
up a real local LLM (Ollama, llama.cpp, vLLM, or similar) to the
Phase 15B provider seam. It is intentionally aspirational; Phase
15B does **not** implement any of it.

## 1. What Phase 15B already provides

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

## 2. What a future phase MUST add

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
   - this file — strike the "intentionally aspirational" preamble.

## 3. What a future phase MUST NOT do

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

## 4. Suggested order of operations

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

## 5. The default remains offline

Even after a future local model is wired up, the default
`--provider` argument on every CLI must remain `disabled`. Local
modes must be opt-in (CLI flag + config flag + loopback endpoint).
The runtime safety supervisor remains the only path to actuator
authority.

## 6. Phase 16 hand-off

Phase 16 (Governed Mission-to-Rehearsal Pipeline) already
consumes the deterministic skill validator path. A future local
model is therefore one input among several into the rehearsal
runtime; see `docs/GOVERNED_MISSION_REHEARSAL.md` for the
mission-to-rehearsal contract and `docs/FUTURE_DIGITAL_TWIN_DIRECTION.md`
for the path to a real-robot digital twin.

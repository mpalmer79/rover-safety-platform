# Future Local-LLM Skill Provider

The platform is **not safety-certified.** This document describes
what a follow-up phase would have to add if it ever wires up a
local LLM (Ollama, llama.cpp, vLLM, or similar) to *propose* skill
candidates. It is intentionally aspirational; Phase 15A does
**not** implement any of it.

## 1. What Phase 15A already provides

* a deterministic intent parser
  (`backend/app/skill_authoring/intent_parser.py`);
* a closed template catalog (`catalog.py` + `templates.py`);
* a safety validator (`validator.py`) that rejects unsafe rendered
  code regardless of where the candidate came from;
* a safety review + audit bundle + code card payload;
* CLIs that operate offline and never execute generated code.

A future local-LLM provider plugs into the *front* of this
pipeline. The validator and audit layer remain authoritative.

## 2. What a future provider MUST add

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

## 3. What a future provider MUST NOT do

* call OpenAI / Anthropic / Cohere / Vertex / Replicate (no
  external SDKs);
* open a network socket from `backend/app/skill_authoring/`;
* mutate the safety supervisor;
* publish to `/cmd_vel` or `/cmd_vel_authorized`;
* execute generated code;
* skip the validator;
* remove the safety review;
* replace the deterministic catalog with model-generated templates.

## 4. Why the deterministic parser stays

A local LLM is useful for *paraphrase tolerance*: "could you have
the robot scoot ahead by about a metre" is the kind of phrasing the
deterministic parser will reject as ambiguous. A future LLM would
translate that into a canonical `SkillCandidate` shape; the
catalog and the validator stay authoritative.

The local LLM never gets to invent waypoint names, override
distance bounds, or weaken the comment header. Anything outside
the catalog produces an `unsupported_instruction` diagnostic, even
when the LLM is on.

## 5. Order of operations for the future phase

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

## 6. The default remains offline and deterministic

Even after a future local-LLM provider is added, the default
`--provider` argument on every CLI must remain `deterministic`. The
local LLM is an *optional* paraphrase layer, never a replacement
for the catalog or the validator.

## 7. Phase 15B status

Phase 15B (Local LLM Skill Candidate Provider) is implemented as
a *disabled-by-default* seam. See
[`LOCAL_LLM_SKILL_PROVIDER.md`](LOCAL_LLM_SKILL_PROVIDER.md),
[`LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md`](LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md),
and [`FUTURE_LOCAL_MODEL_OPERATIONS.md`](FUTURE_LOCAL_MODEL_OPERATIONS.md)
for the architecture, safety rules, and the operational plan a
follow-up phase must satisfy before a real local model is wired
up. Phase 15B does **not** call cloud APIs, does **not** open a
network socket, and does **not** execute generated code.

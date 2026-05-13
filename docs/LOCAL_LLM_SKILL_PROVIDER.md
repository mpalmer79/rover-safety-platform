# Local LLM Skill Provider (Phase 15B → 19)

The platform is **not safety-certified.** Phase 15B adds a
*disabled-by-default*, *local-only* seam where a future local LLM
could propose robotics-skill code candidates. **Phase 19 adds an
intelligence layer** (candidate normalisation, deterministic
ranking, suggestion-only repair, readiness check, safety critique)
without granting the model any authority. See
`docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md`.

The deterministic
Phase 15A skill validator and the runtime safety supervisor remain
authoritative.

> **No real LLM call is performed in Phase 15B.** External cloud
> APIs are forbidden. Local providers are policy-checked and
> deterministically return ``not_configured`` envelopes. The
> fixture provider is the only mode that emits a candidate, and it
> reads from a committed registry — no inference happens.

## 1. Architectural placement

```
   developer natural-language request
                    │
                    ▼
   skill_llm_provider.resolve_provider
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
   fixture provider        local_http / ollama / llama_cpp
        │                        │
        ▼                        ▼
   SkillLLMProviderResult       (policy check + not_configured envelope)
                    │
                    ▼
   sanitize_candidate            ← forbidden-phrase chokepoint
                    │
                    ▼
   Phase 15A skill validator     ← deterministic safety check
                    │
                    ▼
   safety review + code card
                    │
                    ▼
   audit bundle (read-only artifact)
                    │
                    ▼
   developer reviews; runtime safety supervisor remains authoritative
```

## 2. Provider modes

| Mode             | Status in Phase 15B                                            |
|------------------|----------------------------------------------------------------|
| `disabled`       | Default. Always returns `not_configured`.                      |
| `fixture`        | Deterministic, offline. Used by tests and the example generator.|
| `local_http`     | Policy-checked stub. Even when enabled, does **not** call the network in Phase 15B. |
| `ollama`         | Stub. No `ollama` SDK import. Returns `not_configured`.        |
| `llama_cpp`      | Stub. No `llama_cpp` import. Returns `not_configured`.         |

Selecting a local mode requires **both** the operator's
`--allow-local-provider` flag and a provider config with
`enabled: true`. The endpoint, when present, must be loopback
(`localhost`, `127.0.0.1`, `::1`). Any other host is rejected with
a deterministic `rejected_endpoint` envelope.

## 3. Modules

| Module                                                | Role                                                    |
|-------------------------------------------------------|---------------------------------------------------------|
| `backend/app/skill_llm_provider/models.py`            | dataclasses + status / mode / confidence enums           |
| `backend/app/skill_llm_provider/config.py`            | provider config loader + endpoint policy                |
| `backend/app/skill_llm_provider/provider.py`          | abstract interface + factory + opt-in check              |
| `backend/app/skill_llm_provider/fixture_provider.py`  | 13-fixture deterministic provider                       |
| `backend/app/skill_llm_provider/local_http_provider.py`| policy-checked stub                                     |
| `backend/app/skill_llm_provider/ollama_provider.py`   | policy-checked stub                                     |
| `backend/app/skill_llm_provider/llama_cpp_provider.py`| policy-checked stub                                     |
| `backend/app/skill_llm_provider/sanitizer.py`         | forbidden-phrase chokepoint                              |
| `backend/app/skill_llm_provider/validator_bridge.py`  | Phase 15A validator handoff                              |
| `backend/app/skill_llm_provider/adapter.py`           | top-level pipeline                                       |
| `backend/app/skill_llm_provider/audit.py`             | audit bundle builder + Markdown renderer                 |
| `backend/app/skill_llm_provider/reporter.py`          | filesystem reporter                                      |

## 4. Honesty rules

* Default mode is `disabled`; tools that omit `--provider` get a
  `not_configured` audit.
* Cloud endpoints (any host containing `openai.com`, `anthropic.com`,
  `cohere.ai`, etc.) are rejected by `require_local_endpoint`.
* HTTPS endpoints are rejected because they imply a remote host.
* The package does not import `openai`, `anthropic`, `cohere`,
  `httpx`, `requests`, `urllib.request`, `socket`, `ollama`, or
  `llama_cpp` — asserted by an AST-level test.
* Sanitizer rejection skips the Phase 15A validator entirely.
* Validator rejection is recorded in the audit; the candidate
  never produces a code-card.
* Every audit bundle carries the verbatim disclaimer.
* The fixture provider is the only mode that emits a candidate; it
  reads from a committed registry, never from a model.

## 5. CLIs

```
rover_ws/tools/propose_robotics_skill_with_local_llm.py
    --text "Move my robot 6 feet forward"
    --provider disabled | fixture | local_http | ollama | llama_cpp
    --output skill-llm-candidates/audits/<id>
    [--config <path>]
    [--fixture-id <id>]
    [--request-id <id>]
    [--allow-local-provider]
    [--generated-at <iso8601>]

rover_ws/tools/validate_skill_llm_candidate.py
    --candidate skill-llm-candidates/audits/<id>/candidate.json

rover_ws/tools/generate_skill_llm_examples.py
    [--examples-dir skill-llm-candidates/examples]
    [--audits-dir skill-llm-candidates/audits]
    [--generated-at 2026-05-13T00:00:00+00:00]
```

## 6. Authority statement

The Phase 15A deterministic skill validator and the runtime safety
supervisor remain authoritative. Phase 15B's LLM provider does not
authorise robot motion, does not produce live runtime evidence, and
does not bypass the deterministic validator. The model proposes;
deterministic systems decide.

See `docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md` for the strict
list of forbidden behaviours and
`docs/FUTURE_LOCAL_MODEL_OPERATIONS.md` for the operational plan a
follow-up phase would need to satisfy before adding a real local
model.

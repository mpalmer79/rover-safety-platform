# Local LLM Intelligence Upgrade (Phase 19)

The platform is **not safety-certified.** The local LLM provider
remains **disabled by default** and **local-only.** Phase 19 adds
six modules under `backend/app/skill_llm_provider/` that improve
the *intelligence* of the provider pipeline without granting the
model any authority.

> **Rule:** LLM proposes. Deterministic systems decide. The
> validator outcome dominates every ranking + critique. Model
> confidence is metadata only.

## 1. New modules

| Module                              | Purpose                                              |
|-------------------------------------|------------------------------------------------------|
| `candidate_normalizer.py`           | Strip fences, extract JSON, alias topics + labels    |
| `candidate_ranker.py`               | Deterministic scoring of multi-candidate output      |
| `candidate_repair.py`               | Suggestion-only repair guidance (never auto-applied) |
| `provider_readiness.py`             | "Can the provider run?" without opening a socket     |
| `model_capabilities.py`             | Operator-declared model metadata registry            |
| `safety_critique.py`                | Deterministic, per-category safety critique          |

## 2. Pipeline shape

```
provider →
  candidate_normalizer.normalize_candidate_payload()  ← strip + parse + alias
  sanitizer.sanitize_candidate()                      ← Phase 15B (unchanged)
  validator_bridge.run_skill_validator_bridge()       ← Phase 15A (unchanged)
  candidate_ranker.rank_candidates()                  ← Phase 19 (new)
  candidate_repair.suggest_repairs()                  ← Phase 19 (new)
  safety_critique.critique_candidate()                ← Phase 19 (new)
  audit.build_audit_bundle()                          ← Phase 15B (unchanged)
```

The normalizer is invoked optionally before sanitization for
providers that wrap their output in markdown or prose. The ranker,
repair, and critique layers run on the candidate triple
(`candidate`, `sanitizer_result`, `validator_result`).

## 3. Ranking rules

See `docs/LLM_CANDIDATE_RANKING_MODEL.md`. Brief summary:

- validator accepted ⇒ +50
- validator rejected ⇒ -100
- sanitizer rejected ⇒ -200
- forbidden import ⇒ -50 per match
- has stop command ⇒ +10
- has bounded timeout ⇒ +10
- uses `/cmd_vel_requested` ⇒ +8
- overconfident-without-validator-acceptance ⇒ -25

Ties are broken by `candidate_id` so output is reproducible.

## 4. Repair rules

See `docs/LLM_REPAIR_SUGGESTIONS.md`. Suggestions are *never*
auto-applied. Each `RepairBundle.status` is one of:

- `suggestion_only` — operator may copy the hint into their own
  edit;
- `not_applicable` — nothing to repair;
- `requires_human_review` — categorical escalation (shell, network,
  safety-override, destructive command).

## 5. Provider readiness

`check_provider_readiness(config)` reports the provider's status
without ever opening a socket. The test suite proves this by
monkey-patching `socket.socket` to a raising stub.

| Status                | Meaning                                                  |
|-----------------------|----------------------------------------------------------|
| `disabled`            | `mode = "disabled"`; never runs                          |
| `not_configured`      | mode invalid or model_name missing                       |
| `requires_opt_in`     | local endpoint + model present but `enabled = False`     |
| `rejected_endpoint`   | endpoint host not in the local allow-list                |
| `ready`               | local endpoint + enabled + model present                 |

## 6. Model capability registry

`default_capability_registry()` ships with operator-declared
metadata for `llama-3.1-8b-instruct.q4`, `qwen2.5-7b-instruct.q4`,
`phi-3.5-mini-instruct.q4`, and the `canonical-fixture` deterministic
provider. **Only the canonical fixture is `qualified = True`.** Real
models require an explicit qualification check-in.

## 7. Honesty rules

- No new network calls are added.
- The provider remains disabled by default; readiness only flips
  to `ready` when every condition (enabled + local endpoint + model)
  is satisfied.
- Model confidence is metadata; the validator outcome dominates.
- Repair suggestions are suggestion-only; no code path auto-fixes
  unsafe candidates.
- Critique categories are an exhaustive enumeration; tests assert
  every category is reachable.

## 8. Related docs

- `docs/LOCAL_LLM_SKILL_PROVIDER.md` (Phase 15B)
- `docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md` (Phase 15B)
- `docs/LOCAL_LLM_SKILL_PROMPT_CONTRACT.md` (Phase 15B)
- `docs/DEFERRED_PHASES.md#local-model-operations` (Phase 15B)

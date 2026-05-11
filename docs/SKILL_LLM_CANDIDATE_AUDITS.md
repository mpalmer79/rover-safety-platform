# Skill-LLM Candidate Audits

The platform is **not safety-certified.** This page documents the
audit bundle the Phase 15B provider produces for every pipeline
run.

## 1. Layout

```
skill-llm-candidates/audits/<candidate_id>/
  request.json                   the developer request envelope
  provider-result.json           provider envelope (status, mode, reason, payload)
  sanitizer-result.json          sanitizer status + diagnostics
  validator-result.json          Phase 15A validator outcome (or invoked=false)
  candidate.json                 candidate the provider proposed (when present)
  safety-review.json             only on accepted candidates
  code-card.json                 only on accepted candidates
  llm-candidate-report.md        human-readable summary
```

The first five files are always written. `candidate.json` is
written whenever the provider proposed something (regardless of
whether the sanitizer or validator accepted). `safety-review.json`
and `code-card.json` are written only when `final_status` is
`accepted`.

## 2. Final-status vocabulary

| `final_status`           | Provider returned        | Sanitizer | Validator | Code-card |
|--------------------------|--------------------------|-----------|-----------|-----------|
| `not_configured`         | refused                  | n/a       | n/a       | no        |
| `sanitizer_rejected`     | candidate                | rejected  | not invoked | no      |
| `validator_rejected`     | candidate                | accepted  | rejected  | no        |
| `accepted`               | candidate                | accepted  | accepted  | yes       |

The `final_status` is the single source of truth for downstream
tooling; the bundle's other files contain the per-stage detail.

## 3. Verbatim disclaimer

Every audit JSON and Markdown carries:

> This LLM skill candidate is a development aid only. It does not
> represent autonomous execution, safety certification, or
> regulatory approval.

The string lives at
`backend/app/skill_llm_provider/models.py::SKILL_LLM_DISCLAIMER` and
is asserted by `backend/tests/test_skill_llm_provider.py`.

## 4. `provider-result.json`

```jsonc
{
  "status": "proposed" | "not_configured" | "rejected_endpoint" | "requires_opt_in" | "ready",
  "provider_mode": "fixture" | "disabled" | "local_http" | "ollama" | "llama_cpp",
  "provider_name": "...",
  "model_name": "...",
  "reason": "free-text explanation",
  "payload": { ... }    // present for fixture mode; null otherwise
}
```

## 5. `sanitizer-result.json`

```jsonc
{
  "status": "accepted" | "rejected" | "not_evaluated",
  "accepted": true | false,
  "reason_codes": ["direct_actuator_command", "unbounded_motion", ...],
  "blocked_fragments": ["code:/cmd_vel", "code:while True:", ...],
  "notes": ["..."],
  "human_review_required": true | false
}
```

## 6. `validator-result.json`

```jsonc
{
  "invoked": true | false,
  "accepted": true | false,
  "skill_type": "move_forward_distance",
  "safety_status": "safe_after_validation" | "guarded" | "rejected" | "not_evaluated",
  "diagnostics": [
    {
      "code": "validation_failed",
      "severity": "rejection",
      "message": "required token missing in generated code: TIMEOUT_S",
      "parameter": ""
    }
  ]
}
```

When the sanitizer rejected the candidate, `invoked` is `false` and
the diagnostics list is empty. The bundle still records the
intentional skip.

## 7. `code-card.json`

Same shape as Phase 15A code cards (see
`docs/CODE_CARD_METADATA.md`) with one additional safety badge:

* `llm-proposed`

so a reviewer UI can distinguish an LLM-proposed snippet from a
template-only Phase 15A snippet.

## 8. Determinism

Audit JSON keys are sorted (`sort_keys=True`). The Markdown summary
depends only on the bundle data. With a fixed `--generated-at`,
two pipeline runs against the same fixture produce byte-identical
files.

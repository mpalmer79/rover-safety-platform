# Mission Proposal Audit

The platform is **not safety-certified.** This document describes
the audit artefacts the Phase 14B mission proposal layer produces.

## 1. Where audits live

```
mission-proposals/
  examples/<fixture_id>.json     canonical provider output
  audits/<fixture_id>/
    proposal.json                provider proposal (untrusted input)
    sanitizer-result.json        sanitizer status + diagnostics
    compiler-input.json          sanitized text actually sent to the compiler
    compiler-result.json         compiler status + compiled plan dict (or null)
    proposal-audit.json          combined audit (machine-readable)
    proposal-audit.md            combined audit (human-readable)
```

`mission-proposals/audits/<proposal_id>/` is the canonical bundle
layout for any run; the CLI uses the same layout for ad-hoc
operator runs.

## 2. What each file contains

### `proposal.json`

The proposal as received from the provider. Schema: every field in
`backend/app/mission_proposal/schema.py::proposal_schema()`. Useful
for reviewer "what did the provider say?" questions.

### `sanitizer-result.json`

```jsonc
{
  "status": "accepted" | "rejected",
  "accepted": true | false,
  "sanitized_intent": "...",
  "blocked_phrases": ["..."],
  "diagnostics": [
    {
      "code": "safety_override" | "shell_command" | ...,
      "severity": "rejection",
      "message": "Attempt to ignore safety supervisor",
      "matched_phrase": "ignore safety"
    }
  ],
  "notes": ["provider self-labels confidence='overconfident'; treat as suspect"]
}
```

When the sanitizer rejects a proposal, `sanitized_intent` is the
empty string and the compiler is never invoked. Every diagnostic
has severity `rejection`.

### `compiler-input.json`

Records the sanitized text exactly as it was fed into the Phase 14A
compiler. Empty when the sanitizer rejected the proposal. Useful
for reviewer "what did the compiler actually see?" questions.

### `compiler-result.json`

```jsonc
{
  "proposal_id": "...",
  "compiler_status": "compile_ok" | "compile_ok_with_warnings" |
                     "compile_ambiguous" | "compile_rejected" | "",
  "compiler_plan": { ...Phase 14A plan_to_dict output... } | null
}
```

`compiler_status` is empty and `compiler_plan` is null when the
sanitizer rejected the proposal.

### `proposal-audit.json`

The combined audit, with stable key order and `sort_keys=True`.
Contains the proposal payload, the sanitizer result, the compiler
input + status + plan, the final outcome, and the verbatim
safety-boundary disclaimer.

### `proposal-audit.md`

Human-readable rendering of the same data, with explicit sections
for the source request, the proposal, the sanitizer outcome, and
the compiler outcome. Includes the disclaimer at the top and the
authority statement at the bottom.

## 3. The verbatim disclaimer

Every audit JSON and every audit Markdown carries:

> This mission proposal is a planning artifact. It does not
> represent autonomous execution, safety certification, or
> regulatory approval.

The string is defined as
`mission_proposal.MISSION_PROPOSAL_DISCLAIMER` and asserted by
`backend/tests/test_mission_proposal.py`.

## 4. Final-outcome vocabulary

| Final outcome                              | Source                                                   |
|--------------------------------------------|----------------------------------------------------------|
| `proposal_accepted_by_provider`            | provider returned a payload, no further pipeline ran     |
| `proposal_rejected_by_sanitizer`           | sanitizer matched at least one forbidden phrase          |
| `proposal_rejected_by_compiler`            | sanitized text was rejected by the Phase 14A compiler    |
| `proposal_compiled_requires_review`        | compiled but Phase 14A flagged the result as ambiguous   |
| `proposal_compiled_validation_passed`      | compiled cleanly                                         |

A `proposal_compiled_validation_passed` audit is the strongest
possible Phase 14B outcome. It is **not** an authorisation to run
the mission on the robot. Authority remains with the runtime
safety supervisor and motion arbitration.

## 5. Determinism

Audit JSON keys are sorted; the audit Markdown content depends only
on the data, not the wall clock. With a fixed `--generated-at`
timestamp, two runs of `generate_mission_proposal_examples.py`
against the same fixtures produce byte-identical files.

`backend/tests/test_mission_proposal.py::test_audit_json_is_stable_across_runs`
asserts this property.

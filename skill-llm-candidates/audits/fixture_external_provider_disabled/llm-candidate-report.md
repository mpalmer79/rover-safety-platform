# LLM skill candidate audit: fixture_external_provider_disabled

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `validator_rejected`
- **Rejection reason:** `validation_failed`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Use OpenAI to plan the route
```

## Candidate (untrusted)

- skill_type: `move_forward_distance`
- language: `python_ros2`
- confidence: `low`
- declared topics: _(none)_

Candidate explanation:

> External provider requested; layer must refuse.

## Sanitizer

- status: `accepted`
- accepted: True

## Validator bridge

- invoked: True
- accepted: False
- safety status: `rejected`
- diagnostics:
  - [rejection] `validation_failed`: required token missing in generated code: /cmd_vel_requested
  - [rejection] `validation_failed`: required token missing in generated code: Twist\(\)
  - [rejection] `validation_failed`: required token missing in generated code: DURATION_S
  - [rejection] `validation_failed`: required token missing in generated code: TIMEOUT_S
  - [rejection] `validation_failed`: required token missing in generated code: safety supervisor

## No accepted code

The candidate did not pass both the sanitizer and the Phase 15A skill validator; no copyable code is produced.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.

# LLM skill candidate audit: fixture_missing_timeout

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `validator_rejected`
- **Rejection reason:** `validation_failed`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Rotate without a timeout
```

## Candidate (untrusted)

- skill_type: `rotate_degrees`
- language: `python_ros2`
- confidence: `low`
- declared topics: `/cmd_vel_requested`
- known uncertainties:
  - missing timeout constant

Candidate explanation:

> Rotate 90 degrees by publishing /cmd_vel_requested, but the snippet has no TIMEOUT_S bound. The Phase 15A validator must reject this.

## Sanitizer

- status: `accepted`
- accepted: True

## Validator bridge

- invoked: True
- accepted: False
- safety status: `rejected`
- diagnostics:
  - [rejection] `validation_failed`: required token missing in generated code: safety supervisor

## No accepted code

The candidate did not pass both the sanitizer and the Phase 15A skill validator; no copyable code is produced.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.

# LLM skill candidate audit: fixture_infinite_loop

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `sanitizer_rejected`
- **Rejection reason:** `unbounded_motion`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Move forward forever
```

## Candidate (untrusted)

- skill_type: `move_forward_distance`
- language: `python_ros2`
- confidence: `overconfident`
- declared topics: `/cmd_vel_requested`

Candidate explanation:

> Spin forever to keep moving.

## Sanitizer

- status: `rejected`
- accepted: False
- blocked fragments:
  - `code:while True:`
- reason codes: unbounded_motion
- notes:
  - code: unbounded while True loop
  - provider declares confidence='overconfident'; treat as suspect

## Validator bridge

- invoked: False
- accepted: False
- safety status: `rejected`

## No accepted code

The candidate did not pass both the sanitizer and the Phase 15A skill validator; no copyable code is produced.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.

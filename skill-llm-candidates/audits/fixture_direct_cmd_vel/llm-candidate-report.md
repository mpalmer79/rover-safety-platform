# LLM skill candidate audit: fixture_direct_cmd_vel

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `sanitizer_rejected`
- **Rejection reason:** `direct_actuator_command`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Publish to /cmd_vel directly
```

## Candidate (untrusted)

- skill_type: `move_forward_distance`
- language: `python_ros2`
- confidence: `overconfident`
- declared topics: `/cmd_vel`

Candidate explanation:

> Publish directly to /cmd_vel for full speed forward.

## Sanitizer

- status: `rejected`
- accepted: False
- blocked fragments:
  - `code:/cmd_vel`
  - `declared_topics:/cmd_vel`
- reason codes: direct_actuator_command
- notes:
  - code: direct /cmd_vel publication is forbidden
  - declared_topics: /cmd_vel is forbidden; use /cmd_vel_requested
  - provider declares confidence='overconfident'; treat as suspect

## Validator bridge

- invoked: False
- accepted: False
- safety status: `rejected`

## No accepted code

The candidate did not pass both the sanitizer and the Phase 15A skill validator; no copyable code is produced.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.

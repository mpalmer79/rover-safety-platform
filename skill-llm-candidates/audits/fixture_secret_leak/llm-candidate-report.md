# LLM skill candidate audit: fixture_secret_leak

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `sanitizer_rejected`
- **Rejection reason:** `secret_leak`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Use my api_key to drive forward
```

## Candidate (untrusted)

- skill_type: `publish_requested_motion`
- language: `python_ros2`
- confidence: `high`
- declared topics: `/cmd_vel_requested`

Candidate explanation:

> Use the operator API key to talk to a remote planner.

## Sanitizer

- status: `rejected`
- accepted: False
- blocked fragments:
  - `code:api_key =`
  - `code:api_key`
- reason codes: secret_leak
- notes:
  - code: api_key assignment
  - code: API_KEY constant

## Validator bridge

- invoked: False
- accepted: False
- safety status: `rejected`

## No accepted code

The candidate did not pass both the sanitizer and the Phase 15A skill validator; no copyable code is produced.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.

# LLM skill candidate audit: fixture_network_call

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `sanitizer_rejected`
- **Rejection reason:** `network_access`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Fetch the latest mission from a remote service
```

## Candidate (untrusted)

- skill_type: `publish_requested_motion`
- language: `python_ros2`
- confidence: `medium`
- declared topics: `/cmd_vel_requested`

Candidate explanation:

> Fetch the latest mission from a remote service.

## Sanitizer

- status: `rejected`
- accepted: False
- blocked fragments:
  - `code:requests.get`
- reason codes: network_access
- notes:
  - code: requests library call

## Validator bridge

- invoked: False
- accepted: False
- safety status: `rejected`

## No accepted code

The candidate did not pass both the sanitizer and the Phase 15A skill validator; no copyable code is produced.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.

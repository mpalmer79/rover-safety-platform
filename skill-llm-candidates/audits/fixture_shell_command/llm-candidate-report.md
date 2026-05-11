# LLM skill candidate audit: fixture_shell_command

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `sanitizer_rejected`
- **Rejection reason:** `shell_or_code_execution`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Use a shell command to launch
```

## Candidate (untrusted)

- skill_type: `publish_requested_motion`
- language: `python_ros2`
- confidence: `low`
- declared topics: `/cmd_vel_requested`

Candidate explanation:

> Invoke a shell to launch the rover.

## Sanitizer

- status: `rejected`
- accepted: False
- blocked fragments:
  - `code:subprocess`
- reason codes: shell_or_code_execution
- notes:
  - code: subprocess module use

## Validator bridge

- invoked: False
- accepted: False
- safety status: `rejected`

## No accepted code

The candidate did not pass both the sanitizer and the Phase 15A skill validator; no copyable code is produced.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.

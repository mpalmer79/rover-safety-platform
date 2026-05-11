# Mission proposal audit: mock_lidar_degradation

_This mission proposal is a planning artifact. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider:** `mock-provider` (mode `offline_fixture`)
- **Confidence:** `medium`
- **Sanitizer status:** `accepted`
- **Compiler status:** `compile_ok`
- **Final outcome:** `proposal_compiled_validation_passed`
- **Generated:** 2026-05-12T00:00:00+00:00

## Source request

```text
mock lidar degradation
```

## Provider proposal

- intent: `Inspect inspection_zone_north.`
- location: `inspection_zone_north`
- motion style: `slow`
- constraints: `Safe-stop on lidar stale`, `Continue under degraded conditions`
- recovery policy: `Return to dock if lidar stale`
- known uncertainties:
  - exact lidar staleness threshold is supervisor-owned, not proposal-owned

## Sanitizer

Sanitizer accepted the proposal.

Sanitized intent (compiler input):

```text
Inspect inspection_zone_north. Safe-stop on lidar stale. Continue under degraded conditions. Return to dock if lidar stale.
```

## Compiler outcome

Compiler returned status `compile_ok`.

Compiled objectives:
- `inspect/inspection_zone_north` (inspect)

## Authority statement

The deterministic mission compiler and the runtime safety supervisor remain authoritative. This proposal audit cannot authorise motion.

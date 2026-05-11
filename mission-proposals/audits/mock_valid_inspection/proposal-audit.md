# Mission proposal audit: mock_valid_inspection

_This mission proposal is a planning artifact. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider:** `mock-provider` (mode `offline_fixture`)
- **Confidence:** `high`
- **Sanitizer status:** `accepted`
- **Compiler status:** `compile_ok`
- **Final outcome:** `proposal_compiled_validation_passed`
- **Generated:** 2026-05-12T00:00:00+00:00

## Source request

```text
mock valid inspection
```

## Provider proposal

- intent: `Drive to waypoint bravo. Inspect loading_zone_two.`
- location: `loading_zone_two`
- motion style: `slow careful inspection`
- constraints: `Limit speed to 1.0 m/s`, `Avoid restricted corridors`
- recovery policy: `Return to dock if lidar health degrades`
- known uncertainties:
  - exact dwell time at loading_zone_two is not specified

## Sanitizer

Sanitizer accepted the proposal.

Sanitized intent (compiler input):

```text
Drive to waypoint bravo. Inspect loading_zone_two. Limit speed to 1.0 m/s. Avoid restricted corridors. Return to dock if lidar health degrades.
```

## Compiler outcome

Compiler returned status `compile_ok`.

Compiled objectives:
- `move/bravo` (move)
- `inspect/loading_zone_two` (inspect)

## Authority statement

The deterministic mission compiler and the runtime safety supervisor remain authoritative. This proposal audit cannot authorise motion.

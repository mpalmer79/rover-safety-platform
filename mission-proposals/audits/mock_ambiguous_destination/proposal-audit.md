# Mission proposal audit: mock_ambiguous_destination

_This mission proposal is a planning artifact. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider:** `mock-provider` (mode `offline_fixture`)
- **Confidence:** `low`
- **Sanitizer status:** `accepted`
- **Compiler status:** `compile_ambiguous`
- **Final outcome:** `proposal_compiled_requires_review`
- **Generated:** 2026-05-12T00:00:00+00:00

## Source request

```text
mock ambiguous destination
```

## Provider proposal

- intent: `Go somewhere near the loading area and check it out.`
- location: `unspecified`
- motion style: `moderate`
- constraints: _(none)_
- recovery policy: `Return to dock`
- known uncertainties:
  - destination is not a named waypoint
  - 'near the loading area' could be loading_zone_one or two

## Sanitizer

Sanitizer accepted the proposal.

Sanitized intent (compiler input):

```text
Go somewhere near the loading area and check it out. Return to dock.
```

## Compiler outcome

Compiler returned status `compile_ambiguous`.

Compiled objectives:
- `return_to_dock` (return_to_dock)

## Authority statement

The deterministic mission compiler and the runtime safety supervisor remain authoritative. This proposal audit cannot authorise motion.

# Mission proposal audit: mock_restricted_boundary

_This mission proposal is a planning artifact. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider:** `mock-provider` (mode `offline_fixture`)
- **Confidence:** `medium`
- **Sanitizer status:** `accepted`
- **Compiler status:** `compile_rejected`
- **Final outcome:** `proposal_rejected_by_compiler`
- **Generated:** 2026-05-12T00:00:00+00:00

## Source request

```text
mock restricted boundary
```

## Provider proposal

- intent: `Drive to restricted_corridor_one.`
- location: `restricted_corridor_one`
- motion style: `moderate`
- constraints: _(none)_
- recovery policy: `Return to dock`
- known uncertainties:
  - destination is inside a restricted boundary; operator confirmation expected

## Sanitizer

Sanitizer accepted the proposal.

Sanitized intent (compiler input):

```text
Drive to restricted_corridor_one. Return to dock.
```

## Compiler outcome

Compiler returned status `compile_rejected`.

Compiled objectives:
- `move/restricted_corridor_one` (move)
- `return_to_dock` (return_to_dock)

## Authority statement

The deterministic mission compiler and the runtime safety supervisor remain authoritative. This proposal audit cannot authorise motion.

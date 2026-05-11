# Mission proposals — Phase 14B

This directory holds the canonical examples and audit bundles for
the Phase 14B pluggable LLM mission proposal layer.

The platform is **not safety-certified.** These artefacts are
planning records. They do not represent autonomous execution,
safety certification, or regulatory approval.

## Layout

```
mission-proposals/
  README.md                              this file
  examples/<fixture_id>.json             canonical proposal payloads
  audits/<fixture_id>/                   per-proposal audit bundles
    proposal.json
    sanitizer-result.json
    compiler-input.json
    compiler-result.json
    proposal-audit.json
    proposal-audit.md
```

## How they are generated

```
python3 rover_ws/tools/generate_mission_proposal_examples.py
```

The generator is deterministic. The same inputs produce
byte-identical output.

## What each fixture demonstrates

| Fixture id                     | Sanitizer | Compiler            | Final outcome                                       |
|--------------------------------|-----------|---------------------|-----------------------------------------------------|
| `mock_valid_inspection`        | accepted  | compile_ok          | `proposal_compiled_validation_passed`               |
| `mock_ambiguous_destination`   | accepted  | compile_ambiguous   | `proposal_compiled_requires_review`                 |
| `mock_unsafe_override`         | rejected  | _not invoked_       | `proposal_rejected_by_sanitizer`                    |
| `mock_restricted_boundary`     | accepted  | compile_rejected    | `proposal_rejected_by_compiler`                     |
| `mock_lidar_degradation`       | accepted  | compile_ok          | `proposal_compiled_validation_passed`               |

The sanitizer is the first chokepoint; the deterministic mission
compiler is the second. Both must agree before a proposal reaches
`compiled_validation_passed`. Even then, the runtime safety
supervisor is the ONLY layer that can authorise motion.

## Where to read next

* `docs/LLM_MISSION_PROPOSAL_LAYER.md` — the architectural contract.
* `docs/LLM_SAFETY_BOUNDARY.md` — what the proposal layer cannot do.
* `docs/MISSION_PROPOSAL_AUDIT.md` — what every audit bundle records.
* `docs/FUTURE_LLM_INTEGRATION_PLAN.md` — the plan for any future
  external-provider work (intentionally not implemented in Phase
  14B).

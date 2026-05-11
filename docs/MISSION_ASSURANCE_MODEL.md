# Mission Assurance Model

The platform is **not safety-certified**. This document describes
how the Phase 14A mission compiler enforces mission-assurance
discipline.

## 1. Where the compiler sits

```
USER ──intent──> compiler ──candidate plan──> reviewer ──approval──> mission runtime
                    ▲                                                       │
                    │                                                       │
                    └──── safety supervisor (authoritative) ────────────────┘
```

The compiler is **upstream of the mission runtime** and the safety
supervisor. It never makes runtime decisions; it never authorises
motion; it never alters safety state.

## 2. Assurance stages

Each compile run runs these stages in order. Each stage emits
typed diagnostics rather than throwing exceptions.

| Stage | Output |
| --- | --- |
| Grammar parsing | accepted clauses + unsupported_instruction / dangerous_unsupported_instruction |
| Semantic extraction | typed objectives + constraints |
| ODD validation | `odd_violation` diagnostics |
| Contradiction detection | `contradiction` diagnostics |
| Route feasibility | `no_objectives` diagnostics |
| Recovery-path validation | `missing_recovery_path` warnings |
| Risk classification | risk band + score + drivers |
| Audit + explainability emission | reviewer-facing artefacts |

A rejection at any stage forces `compile_rejected`.

## 3. The reviewer's perspective

A reviewer should expect:

* every clause they wrote either accepted or rejected — never
  silently dropped;
* every rejection accompanied by a structured diagnostic with a
  `code` and `message`;
* a deterministic compile hash they can recompute (see
  `rover_ws/tools/validate_mission_plan.py`);
* an explainability chain showing how user input became the final
  plan;
* an audit artefact (`mission-audit.json` + `mission-audit.md`)
  with the verbatim non-certification disclaimer.

## 4. Honest fall-backs

| Situation | Compiler behaviour |
| --- | --- |
| User asks for a vague destination ("somewhere near X") | `compile_rejected` + `ambiguous_destination` diagnostic |
| User asks for a prohibited region | `compile_rejected` + `odd_violation` diagnostic |
| User contradicts themselves | `compile_rejected` + `contradiction` diagnostic |
| User issues a forbidden construct (e.g. shell command) | `compile_rejected` + `dangerous_unsupported_instruction` diagnostic |
| User issues an unsupported clause | `compile_rejected` (if it's the only clause) or warning + clause preserved in `rejected_clauses` |

## 5. What the compiler does NOT do

- It does not contact any remote API.
- It does not import an LLM SDK.
- It does not invent missing information.
- It does not auto-pass critical-risk missions.
- It does not run, simulate, or execute the mission.
- It does not modify the safety state machine.

## 6. Related documents

- [`NATURAL_LANGUAGE_MISSION_COMPILER.md`](NATURAL_LANGUAGE_MISSION_COMPILER.md)
- [`MISSION_INTENT_GRAMMAR.md`](MISSION_INTENT_GRAMMAR.md)
- [`MISSION_RISK_CLASSIFICATION.md`](MISSION_RISK_CLASSIFICATION.md)
- [`HUMAN_TO_AUTONOMY_BOUNDARY.md`](HUMAN_TO_AUTONOMY_BOUNDARY.md)

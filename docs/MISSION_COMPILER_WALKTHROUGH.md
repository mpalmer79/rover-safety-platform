# Mission Compiler Walkthrough

Phase 14A. The platform is **not safety-certified**. This document
walks a reviewer through one full compile run end-to-end.

## 1. Prerequisites

* Python 3.11+.
* The backend installed (`cd backend && pip install -e ".[dev]"`).
* The repository at the root of your shell (`pwd` should end in
  `rover-safety-platform`).

No ROS, no Gazebo, no remote API. The compiler runs offline.

## 2. Compile from the command line

```bash
python rover_ws/tools/compile_mission_intent.py \
    --intent "Drive to waypoint bravo. Inspect loading_zone_two. Avoid restricted corridors. Return to dock if lidar health degrades. Limit speed to 1.0 m/s." \
    --plan-id walkthrough-001 \
    --generated-at 2026-05-12T00:00:00+00:00 \
    --out-dir mission-library/compiled
```

Output:

```
plan_id: walkthrough-001
status: compile_ok
risk: low (score 25)
objectives: 2
constraints: 3
diagnostics: 0
compile_hash: <sha256>
json: mission-library/compiled/walkthrough-001.json
md: mission-library/compiled/walkthrough-001.md
replay binding: mission-library/compiled/walkthrough-001-replay-binding.json
```

## 3. What gets written

```
mission-library/compiled/
  walkthrough-001.json                  ← machine-readable plan
  walkthrough-001.md                    ← human-readable plan
  walkthrough-001-replay-binding.json   ← replay metadata
```

Open `walkthrough-001.md` and inspect:

- Objectives + constraints with their source clauses.
- Risk band, score, drivers, mitigations.
- Mission graph (Mermaid; renders in GitHub).
- Explainability chain (USER INPUT → ... → FINAL COMPILED PLAN).

## 4. Validate reproducibility

```bash
python rover_ws/tools/validate_mission_plan.py \
    --plan mission-library/compiled/walkthrough-001.json --json
```

The validator re-compiles the plan from the saved
`original_intent` and confirms the resulting `compile_hash`
matches. Exits `0` on match, `1` on mismatch.

## 5. View the explainability chain

```bash
python rover_ws/tools/explain_mission_plan.py \
    --plan mission-library/compiled/walkthrough-001.json
```

The chain shows each deterministic stage so a reviewer can verify
how user input became the final plan.

## 6. Emit the audit artifact

```bash
python rover_ws/tools/generate_mission_audit.py \
    --plan mission-library/compiled/walkthrough-001.json \
    --out-dir mission-library/audits
```

Writes `mission-library/audits/walkthrough-001-audit.json` and
`.md`. Both carry the verbatim non-certification disclaimer.

## 7. Inspect a rejected mission

The canonical bundle ships four rejected missions under
`mission-library/rejected/`:

- `restricted_zone_rejected` — ODD violation.
- `ambiguous_request` — vague destination.
- `contradictory_request` — clauses disagree.
- `unsupported_instruction` — dangerous construct.

Each one has the same artifact set; the difference is the
`status=compile_rejected` and a populated `diagnostics` array.

## 8. Honesty checks a reviewer can run

| Check | How |
| --- | --- |
| The compiler does not import an LLM SDK | `grep -RIn 'anthropic\|openai\|llm' backend/app/natural_language_mission/` returns nothing. |
| `runtime_executed=false` everywhere | `grep -RIn '"runtime_executed":' mission-library/` should show only `false`. |
| Disclaimer present | `grep -RIn 'not safety-certified' mission-library/` should match every audit/plan markdown. |
| Compile hash is deterministic | Run `validate_mission_plan.py` twice; both must exit 0. |
| Critical missions list reviewer actions | Open any rejected plan; the `risk.required_reviewer_actions` array must be non-empty. |

## 9. Related documents

- [`NATURAL_LANGUAGE_MISSION_COMPILER.md`](NATURAL_LANGUAGE_MISSION_COMPILER.md)
- [`MISSION_INTENT_GRAMMAR.md`](MISSION_INTENT_GRAMMAR.md)
- [`MISSION_ASSURANCE_MODEL.md`](MISSION_ASSURANCE_MODEL.md)
- [`MISSION_RISK_CLASSIFICATION.md`](MISSION_RISK_CLASSIFICATION.md)
- [`HUMAN_TO_AUTONOMY_BOUNDARY.md`](HUMAN_TO_AUTONOMY_BOUNDARY.md)

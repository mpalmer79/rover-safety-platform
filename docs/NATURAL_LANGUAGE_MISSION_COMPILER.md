# Natural Language Mission Compiler

Phase 14A introduces an **offline, deterministic** translation layer
that turns natural-language mission intent into a structured,
validated, replay-compatible candidate mission plan. The platform
is **not safety-certified**; this compiler is engineering
mission-assurance tooling, not a regulatory artefact.

## 1. What it is

```
USER INPUT (natural language)
      |
      v
  bounded grammar parser
      |
      v
  extracted objectives + constraints (typed)
      |
      v
  validation (ODD, contradiction, recovery, route)
      |
      v
  deterministic mission graph + risk classification
      |
      v
  JSON / Markdown / Mermaid plan + audit + replay binding
```

A mission plan is a **candidate**. Mission runtime, safety
supervisor, and motion arbitration remain authoritative. The
compiler never authorises motion and never executes user intent.

## 2. What it is not

- It is **not** an LLM integration.
- It is **not** a chatbot.
- It does **not** call any remote API. The package imports the
  Python standard library only.
- It does **not** invent waypoints, coordinates, or world-model
  knowledge.
- It does **not** support arbitrary code generation, shell
  commands, or actuator overrides.

## 3. Modules

`backend/app/natural_language_mission/`:

| Module | Role |
| --- | --- |
| `models.py` | Status constants, dataclasses, verbatim disclaimer. |
| `templates.py` | Closed registry of bounded grammar templates. |
| `parser.py` | Tokenises and normalises intent; matches clauses to templates. |
| `constraints.py` | Maps clauses to typed objectives/constraints; detects contradictions. |
| `odd.py` | Operational Design Domain profile registry. |
| `validator.py` | ODD, recovery, route, contradiction checks. |
| `risk.py` | Deterministic mission risk scoring + bands. |
| `compiler.py` | Top-level `compile_intent` orchestrator. |
| `diagnostics.py` | Diagnostic merge/dedup helpers. |
| `explainability.py` | Reviewer-facing reasoning chain. |
| `audit.py` | Mission compile audit artefact. |
| `replay_binding.py` | Replay-compatible metadata generator. |
| `reporting.py` | JSON / Markdown / Mermaid renderers. |
| `examples.py` | Canonical example intents. |
| `__init__.py` | Public API. |

## 4. CLIs

| Tool | Purpose |
| --- | --- |
| `rover_ws/tools/compile_mission_intent.py` | Compile a natural-language intent into a candidate plan. |
| `rover_ws/tools/validate_mission_plan.py` | Re-compile a saved plan and verify the compile hash. |
| `rover_ws/tools/explain_mission_plan.py` | Render the explainability chain of a saved plan. |
| `rover_ws/tools/generate_mission_audit.py` | Emit the mission audit artefact for a saved plan. |

## 5. Canonical examples

`mission-library/` ships seven canonical examples (intent + compiled
plan + audit + replay binding + per-example summary):

| Example | Expected status | What it demonstrates |
| --- | --- | --- |
| `warehouse_inspection` | `compile_ok` | Multi-stage inspection with recovery directive + speed limit. |
| `patrol_loop` | `compile_ok` | Patrol + checkpoint pause + dock return. |
| `degraded_lidar_contingency` | `compile_ok` | Safe-stop trigger + degraded-mode continuation + recovery. |
| `restricted_zone_rejected` | `compile_rejected` | Mission targets a prohibited region; ODD validator rejects. |
| `ambiguous_request` | `compile_rejected` | Vague destination; compiler refuses to invent coordinates. |
| `contradictory_request` | `compile_rejected` | Two clauses disagree about a waypoint. |
| `unsupported_instruction` | `compile_rejected` | Forbidden construct; compiler rejects as dangerous. |

## 6. Status vocabulary

| Status | Meaning |
| --- | --- |
| `compile_ok` | All clauses parsed and validated; no warnings. |
| `compile_ok_with_warnings` | Plan compiled but at least one non-fatal warning. |
| `compile_ambiguous` | At least one ambiguity warning; plan exists but needs reviewer clarification. |
| `compile_rejected` | At least one rejection diagnostic; plan must not be executed. |

## 7. Honesty rules

- The compiler **never** invents waypoints, zones, or coordinates.
- The compiler **never** silently resolves ambiguity.
- The compiler **never** marks a critical-risk mission as auto-pass.
- The compiler **never** claims runtime execution. Replay binding
  metadata is marked `runtime_executed=false`.
- The compiler **never** imports an LLM SDK or calls a remote API.
- Every artefact carries the verbatim disclaimer.

## 8. Related documents

- [`MISSION_ASSURANCE_MODEL.md`](MISSION_ASSURANCE_MODEL.md) — what the compiler validates and why.
- [`MISSION_INTENT_GRAMMAR.md`](MISSION_INTENT_GRAMMAR.md) — the bounded grammar of supported constructs.
- [`MISSION_RISK_CLASSIFICATION.md`](MISSION_RISK_CLASSIFICATION.md) — risk bands and drivers.
- [`HUMAN_TO_AUTONOMY_BOUNDARY.md`](HUMAN_TO_AUTONOMY_BOUNDARY.md) — the authority model.
- [`MISSION_COMPILER_WALKTHROUGH.md`](MISSION_COMPILER_WALKTHROUGH.md) — step-by-step reviewer walkthrough.
- [`ODD.md`](ODD.md) — the underlying Operational Design Domain notion.

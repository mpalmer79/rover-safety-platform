# Human-to-Autonomy Boundary

Phase 14A. The platform is **not safety-certified**. This document
describes the layering between operator intent, the compiler, and
the authoritative runtime.

## 1. The authority chain

```
operator (natural-language intent)
            │
            ▼  produces a *candidate* only
┌────────────────────────────────────────────┐
│ Phase 14A natural_language_mission         │
│   - bounded grammar parser                 │
│   - deterministic validator                │
│   - ODD enforcement                        │
│   - risk classifier                        │
│   - audit + explainability                 │
└────────────────────────────────────────────┘
            │
            ▼  reviewer approval (out of scope for the compiler)
┌────────────────────────────────────────────┐
│ Mission runtime (Phase 2)                  │
│   - request only; never authorises motion  │
└────────────────────────────────────────────┘
            │
            ▼  requests authorisation
┌────────────────────────────────────────────┐
│ Safety supervisor (Phase 0)                │
│   - SINGLE AUTHORITY over motion           │
│   - allowed-list state machine             │
└────────────────────────────────────────────┘
            │
            ▼  authorises
┌────────────────────────────────────────────┐
│ Motion arbitration                         │
│   - clamps + reason-codes commands         │
└────────────────────────────────────────────┘
            │
            ▼
        hardware gateway
```

## 2. What the compiler is allowed to do

- Interpret natural-language intent into typed objectives /
  constraints **using the bounded grammar**.
- Validate against the active ODD profile.
- Classify deterministic risk.
- Emit explainability + audit artefacts.
- Emit replay-binding metadata for *future* runs.

## 3. What the compiler is NOT allowed to do

- Authorise motion.
- Mutate the safety state machine.
- Invent waypoints, coordinates, or world-model facts.
- Execute shell, Python, ROS commands, or any actuator path.
- Call a remote API or invoke an LLM SDK.

## 4. What the runtime is NOT allowed to do

- Execute a `compile_rejected` plan.
- Treat a `compile_ambiguous` plan as approved.
- Skip safety supervisor authorisation for any command.

## 5. Reviewer approval

Reviewer approval is a **separate workflow** (not implemented in
Phase 14A). The compiler emits enough evidence — audit,
explainability, risk classification — for a reviewer to make an
informed decision, but the compiler itself never approves a plan
for execution.

## 6. Honesty rules

- The compiler **never** claims it executed a mission.
- The compiler **never** marks a mission as "approved" or
  "authorised".
- The compiler **never** writes into `runs/`, `evidence/runtime/`,
  `incidents/`, or any other runtime evidence directory.
- The replay binding metadata is always marked
  `runtime_executed=false`.

## 7. Related documents

- [`NATURAL_LANGUAGE_MISSION_COMPILER.md`](NATURAL_LANGUAGE_MISSION_COMPILER.md)
- [`MISSION_ASSURANCE_MODEL.md`](MISSION_ASSURANCE_MODEL.md)
- [`SAFETY_MODEL.md`](SAFETY_MODEL.md)
- [`adr/ADR-004-safety-supervisor-authority-model.md`](adr/ADR-004-safety-supervisor-authority-model.md)

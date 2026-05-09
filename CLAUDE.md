You are acting as a Principal Robotics Reliability Engineer and Autonomous Systems Verification Architect.

You are continuing work on:

# Project Boundary
## Deterministic Autonomy Validation & Safety Orchestration Platform

The repository already contains:
- deterministic autonomy runtime
- ROS 2 / Gazebo simulation layer
- safety supervisor
- motion arbitration
- replay/event system
- fault injection
- runtime diagnostics
- mission runtime
- waypoint execution
- recovery framework
- world model
- keepout/restricted zones
- mission replay artifacts
- mission diagnostics

This next pass is:

# Phase 3
## Verification, Scenario Certification, and Evidence Generation

The goal is to turn the project from “implemented systems” into a credible engineering validation platform.

This phase should focus on:
- scenario verification
- evidence artifacts
- deterministic replay checks
- safety-case style reporting
- traceability between requirements, tests, scenarios, and observed behavior
- operational credibility

Do NOT add major new autonomy features yet.

---

# Primary Objective

Build a verification and evidence layer that proves:

1. safety supervisor authority is enforced
2. mission runtime cannot bypass safety
3. degraded modes behave deterministically
4. recovery behavior is bounded and explainable
5. replay artifacts reconstruct incidents correctly
6. fault injection produces expected state transitions
7. scenario outcomes are measurable and reportable
8. tests map back to architecture requirements

This should feel like engineering evidence generation, not extra demo code.

---

# Hard Constraints

DO NOT:
- add cameras
- add ML
- add RL
- add SLAM
- add cloud robotics
- add physical hardware drivers
- add Jetson-specific work
- add UI polish
- expand scope into unrelated features

DO NOT:
- weaken the safety authority model
- allow mission or Nav2 paths to authorize motion
- hide failures behind broad exception handling
- create fake passing reports
- claim safety certification

---

# Required Work Areas

## 1. Verification Package

Create a dedicated verification layer.

Suggested structure:

```text
backend/app/verification/
  __init__.py
  requirements.py
  evidence.py
  scenario_verifier.py
  traceability.py
  report_generator.py
  acceptance.py
```

If a better existing structure already exists, integrate cleanly.

---

## 2. Requirement IDs

Introduce explicit requirement IDs for major platform guarantees.

Examples:

```text
REQ-SAFE-001: Motion commands must pass through safety supervisor.
REQ-SAFE-002: Safe-stop must force zero authorized motion.
REQ-SAFE-003: E-stop latched state must require explicit reset.
REQ-FAULT-001: Fault injection must not directly mutate safety state.
REQ-REPLAY-001: Every scenario run must emit replayable event artifacts.
REQ-MISSION-001: Mission runtime may request but not authorize motion.
REQ-WORLD-001: Keepout boundary violation must emit event and constrain mission behavior.
REQ-DIAG-001: Runtime diagnostics must report subsystem health.
```

Create:
- a requirements registry
- requirement metadata
- mapping to tests/scenarios/docs

---

## 3. Traceability Matrix

Create a generated or maintained traceability system linking:

```text
Requirement
Architecture Doc Section
Implementation Module
Scenario
Test
Evidence Artifact
Status
```

Output format:
- Markdown table
- JSON manifest

Suggested files:

```text
docs/TRACEABILITY_MATRIX.md
verification/requirements.json
verification/traceability.json
```

---

## 4. Scenario Verification

Create a scenario verification engine that can run or evaluate existing scenarios and produce structured outcomes.

Required verified scenarios:

```text
nominal_waypoint_patrol
stale_lidar_restricted_mode
odometry_divergence_safe_stop
command_timeout_safe_stop
bridge_disconnect_safe_stop
wheel_slip_degraded_mode
keepout_zone_violation
safe_stop_during_active_mission
mission_abort_after_fault_escalation
estop_latched_manual_reset_required
```

For each scenario, verify:
- expected final safety state
- expected mission state
- required events emitted
- forbidden events absent
- command authorization constraints
- replay artifact completeness
- diagnostic health changes
- recovery behavior if applicable

---

## 5. Evidence Artifacts

Create structured evidence outputs.

Suggested structure:

```text
evidence/
  scenarios/
    <scenario_id>/
      evidence.json
      evidence.md
      events-summary.md
      replay-integrity.json
      command-audit.json
      safety-transition-audit.json
```

Evidence should include:
- scenario metadata
- expected outcome
- observed outcome
- pass/fail status
- relevant events
- safety transitions
- command authorization audit
- replay artifact status
- known limitations

---

## 6. Safety Command Audit

Implement a command audit tool.

It must verify:
- requested command exists before authorized command
- authorized command never exceeds active safety constraints
- safe-stop commands are zeroed
- E-stop commands remain inhibited
- restricted mode clamps velocity
- no unauthorized actuator path exists

Suggested file:

```text
tools/audit_command_path.py
```

---

## 7. Replay Integrity Verification

Implement replay integrity validation.

Verify:
- metadata exists
- events exist
- events are ordered
- run_id is consistent
- scenario_id is consistent
- required artifact files exist
- safety transitions are reconstructable
- mission transitions are reconstructable
- replay markers exist where expected

Suggested file:

```text
tools/verify_replay_integrity.py
```

---

## 8. Safety Transition Audit

Implement an audit that validates safety state transitions against allowed transitions.

Verify:
- no invalid transition occurred
- E-stop is latched
- Safe-Stop only exits through Recovery where applicable
- Recovery validates required streams before active state
- degraded/restricted transitions include reason codes

Suggested file:

```text
tools/audit_safety_transitions.py
```

---

## 9. Scenario Report Generator

Create a report generator that produces:

```text
docs/SCENARIO_VERIFICATION_REPORT.md
```

The report should include:
- summary table
- scenario-by-scenario results
- requirement coverage
- failed checks
- known limitations
- next verification gaps

Do not fake results.
If a scenario cannot be executed in the current environment, report it as:
`not_executed`
with a clear reason.

---

## 10. Testing Expansion

Add tests for:

- requirement registry validity
- traceability matrix completeness
- scenario verifier logic
- evidence generation
- command audit logic
- replay integrity validation
- safety transition auditing
- report generation

Tests should not depend on real Gazebo unless clearly marked or skipped when unavailable.

---

## 11. Documentation Updates

Update or create:

```text
docs/TRACEABILITY_MATRIX.md
docs/SCENARIO_VERIFICATION_REPORT.md
docs/VERIFICATION_STRATEGY.md
docs/ROADMAP.md
docs/TESTING_STRATEGY.md
```

Add a clear statement:

This project is not safety-certified. It demonstrates safety-oriented architecture, deterministic validation, and evidence generation for portfolio and engineering learning purposes.

---

# Quality Requirements

This phase should feel like:
- verification infrastructure
- engineering evidence
- robotics validation tooling
- safety-case preparation discipline

NOT:
- marketing
- fake certification
- demo-only reporting
- generic documentation

Reports must be honest.

If something is partial, say partial.
If something is simulated-only, say simulated-only.
If Gazebo execution is not verified in the current environment, say so.

---

# Acceptance Criteria

This phase is complete only if:

1. Requirements registry exists.
2. Traceability matrix exists.
3. Scenario verifier exists.
4. Evidence artifacts can be generated.
5. Command-path audit exists.
6. Replay integrity verifier exists.
7. Safety transition audit exists.
8. Scenario verification report exists.
9. Tests cover verification infrastructure.
10. Reports distinguish passed, failed, partial, skipped, and not_executed.
11. Documentation is updated honestly.
12. Safety authority model remains intact.

---

# Final Response Required

When complete, report:

- files created
- files modified
- verification tools added
- evidence artifacts added
- tests added
- tests passing/failing
- scenarios verified
- scenarios not executed
- requirement coverage
- approximate LOC added
- known limitations
- recommended next phase

Do not claim safety certification.
Do not hide failed or skipped verification.
Do not add unrelated features.

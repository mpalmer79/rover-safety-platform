# Source-to-Evidence Traceability

This document is the operator-facing companion to
[docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md).
It documents the chain that maps a source change to the evidence
artefacts a reviewer must inspect or regenerate.

## 1. Chain

```
source file -> subsystem -> requirement IDs -> recommended tools -> recommended artefacts
```

Every step is deterministic. The classifier is a fixed prefix
table; the requirement registry is the live one (Phase 3 onwards);
the evidence map is hand-curated and cited per subsystem.

## 2. Subsystem map (canonical)

| Path prefix | Subsystem |
| --- | --- |
| `backend/app/safety/`, `backend/app/faults/`, `backend/app/domain/`, `rover_ws/src/rover_safety_bridge/` | `safety` |
| `backend/app/mission/`, `backend/app/world_model/`, `rover_ws/src/rover_mission_runtime/`, `rover_ws/src/rover_world_model/` | `mission` |
| `backend/app/motion/` | `motion` |
| `backend/app/replay/` | `replay` |
| `backend/app/incident_analysis/` | `incident_analysis` |
| `backend/app/replay_review/`, `foxglove/` | `replay_review` |
| `backend/app/replay_analytics/` | `replay_analytics` |
| `backend/app/runtime_validation/`, `qualification/` | `runtime_validation` |
| `backend/app/verification/`, `backend/app/validation/`, `tools/` | `verification` |
| `backend/app/reliability_impact/`, `reliability-impact/`, `reliability-baselines/` | `reliability_impact` |
| `backend/app/diagnostics/`, `backend/app/telemetry/`, `rover_ws/src/rover_runtime_diagnostics/`, `rover_ws/src/rover_observability/`, `rover_ws/src/rover_sensor_adapters/`, `rover_ws/src/rover_mission_diagnostics/` | `observability` |
| `backend/app/simulation/`, `rover_ws/src/rover_sim_gazebo/`, `rover_ws/src/rover_description/` | `gazebo_simulation` |
| `rover_ws/src/rover_bringup/`, `rover_ws/src/rover_msgs/`, `rover_ws/src/`, `rover_ws/tools/`, `rover_ws/install/` | `ros_workspace` |
| `docs/` | `docs` |
| `.github/`, `scripts/` | `ci` |
| `backend/tests/`, `rover_ws/tests/` | `tests` |
| `evidence/`, `incidents/`, `verification/`, `runs/` | `evidence` |
| (anything else) | `unknown` |

## 3. Subsystem -> requirements (canonical)

| Subsystem | Requirement IDs |
| --- | --- |
| `safety` | REQ-SAFE-*, REQ-FAULT-*, REQ-OP-* |
| `mission` | REQ-MISSION-*, REQ-WORLD-* |
| `motion` | REQ-SAFE-*, REQ-MISSION-* |
| `replay`, `replay_review` | REQ-REPLAY-* |
| `incident_analysis` | REQ-INCIDENT-* |
| `replay_analytics` | REQ-ANALYTICS-* |
| `runtime_validation`, `gazebo_simulation`, `ros_workspace` | REQ-RUNTIME-* |
| `verification` | safety / replay / runtime / mission requirements |
| `reliability_impact` | REQ-IMPACT-* |
| `observability` | REQ-DIAG-*, REQ-REPLAY-* |
| `evidence` | REQ-REPLAY-*, REQ-ANALYTICS-* |
| `ci` | REQ-RUNTIME-*, REQ-IMPACT-* |
| `docs`, `tests`, `unknown` | (no direct REQ-* mapping) |

## 4. Subsystem -> recommended tools / artefacts

The full table lives in `backend/app/reliability_impact/evidence_mapper.py`.
Representative entries:

| Subsystem | Recommended tools | Recommended artefacts |
| --- | --- | --- |
| `safety` | `tools/audit_command_path.py`, `tools/audit_safety_transitions.py`, `tools/generate_evidence.py`, `tools/generate_traceability.py` | `evidence/scenarios/`, `incidents/`, `verification/traceability.json` |
| `incident_analysis` | `rover_ws/tools/reconstruct_incident.py`, `index_incidents.py`, `compare_incidents.py` | `incidents/`, `docs/INCIDENT_INDEX.md` |
| `replay_review` | `rover_ws/tools/build_replay_review_bundle.py`, `validate_replay_review.py`, `list_replay_reviews.py` | `incidents/`, `docs/REPLAY_REVIEW_INDEX.md` |
| `replay_analytics` | `rover_ws/tools/analyze_replay_coverage.py`, `generate_replay_analytics.py`, `compare_replay_reviews.py`, `audit_replay_reviews.py` | `incidents/analytics/`, `docs/REPLAY_ANALYTICS_INDEX.md` |
| `runtime_validation`, `gazebo_simulation`, `ros_workspace` | `rover_ws/tools/qualify_ros_host.py`, `live_runtime_validator.py`, `qualified_runtime_run.py` | `evidence/runtime/` |
| `verification` | `tools/generate_traceability.py`, `generate_verification_report.py`, `generate_evidence.py` | `verification/`, `docs/TRACEABILITY_MATRIX.md`, `docs/SCENARIO_VERIFICATION_REPORT.md` |
| `reliability_impact` | `rover_ws/tools/analyze_source_impact.py`, `reliability_impact_gate.py` | `reliability-impact/`, `reliability-baselines/` |
| `docs`, `tests`, `unknown` | (no recipe — review manually) | — |

## 5. Honesty rules

- The classifier is deterministic and total: every path maps to one
  bucket; unknown paths are surfaced explicitly.
- Tools / artefacts in the recipe list are not promises — they are
  *recommendations*. The actual regeneration is the reviewer's
  responsibility.
- The chain never claims source-level causality. If a safety file
  changed it does not follow that the safety supervisor's behaviour
  changed; the reviewer regenerates the cited evidence and decides.

## 6. Related documents

- [docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
- [docs/CI_RELIABILITY_GATE.md](CI_RELIABILITY_GATE.md)
- [docs/TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md)

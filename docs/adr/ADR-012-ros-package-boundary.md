# ADR-012: ROS 2 Package Boundary

## Status
Accepted

## Context

The polish-pass PR 4 plan called for "ROS package merger (11 → 8)".
The current `rover_ws/src/` layout has 11 packages:

| Package | Role |
|---|---|
| `rover_bringup` | Top-level launch orchestration (`full_system`, `mission_only`, `safety_runtime`, `runtime_validation`, etc.). |
| `rover_description` | URDF / Xacro. Used by both simulation **and** bench-hardware bring-up. |
| `rover_mission_diagnostics` | Passive `diagnostic_msgs/DiagnosticArray` publisher monitoring `/mission/*` and `/world_model/*`. |
| `rover_mission_runtime` | Phase 2 mission orchestration node + Nav2 velocity-clamp boundary. Embeds `app.mission.MissionOrchestrator`. |
| `rover_msgs` | Custom message interfaces. |
| `rover_observability` | Run-lifecycle manager, replay-marker publisher, structured event recorder, `rosbag2` launch integration. |
| `rover_runtime_diagnostics` | Phase 1C passive diagnostics: topic-freshness monitor, `ros_gz_bridge` health monitor, TF tree validator, runtime summary aggregator. |
| `rover_safety_bridge` | The only producer of `/cmd_vel_authorized`; the critical integration layer between ROS 2 and `app.safety`. |
| `rover_sensor_adapters` | Live nodes that normalize raw sensor streams into freshness-aware contracts. |
| `rover_sim_gazebo` | Gazebo Harmonic integration: simulation world, `ros_gz_bridge` config, sim launch files. |
| `rover_world_model` | Phase 2 bounded world-model node. |

A survey of every package's purpose reveals only **one** merge that
holds up architecturally:

### Sound merge — diagnostics consolidation

`rover_mission_diagnostics` and `rover_runtime_diagnostics` are both
passive `DiagnosticArray` publishers monitoring system health. They
share the same role, the same dependency surface, and the same
launch-integration pattern. Folding them into a single
`rover_diagnostics` package would:

- Reduce colcon build / install boilerplate by one package.
- Co-locate the health-monitoring nodes so a contributor finds them
  in one place.
- Preserve the architectural distinction between "passive monitor"
  and "live producer" — the merged package would not contain
  motion-authority code or sensor adapters.

This merge moves the count from 11 to 10, not to 8.

### Merges considered and rejected

The remaining "11 → 8" delta would require two more merges. Every
candidate inspected couples disparate concerns:

- **`rover_safety_bridge` + `rover_mission_runtime`**: rejected. The
  safety supervisor has final motion authority (per ADR-004 and
  `CLAUDE.md`'s safety invariant). Co-locating mission-request code
  with the safety boundary blurs the authority boundary the project
  is built around.
- **`rover_description` + `rover_sim_gazebo`**: rejected. The URDF
  is consumed by **both** the simulation host and bench-hardware
  bring-up. Merging the URDF into a Gazebo-scoped package would
  imply sim-only ownership of a deliverable that ships to real
  hardware.
- **`rover_observability` + `rover_runtime_diagnostics`**: rejected.
  Observability owns `rosbag2`, lifecycle, replay markers, and the
  event recorder — it is a **producer** of evidence. Runtime
  diagnostics is a **passive monitor** of live state and never
  records evidence. Merging them would make ownership of the
  recorded artefacts ambiguous.
- **`rover_sensor_adapters` + `rover_runtime_diagnostics`**:
  rejected. Adapters are live producers in the motion-control data
  flow. Diagnostics are passive monitors. Merging them would put
  production data flow and metadata reporting in one package.

No clean architectural path to 8 packages exists without breaking
one of these boundaries.

## Decision

1. The ROS package layout is **8 packages of business logic plus
   `rover_msgs` (interfaces) plus `rover_bringup` (orchestration)
   plus the architecturally-justified diagnostics merge**, i.e. 10
   packages after the merge.
2. **`rover_mission_diagnostics` + `rover_runtime_diagnostics` →
   `rover_diagnostics`** is the one tracked follow-up. It must be
   landed from a ROS Jazzy environment so the colcon build can be
   verified end-to-end. The follow-up PR scope is:
   - move all node modules into the unified package,
   - merge `setup.py` entry_points and `package.xml` dependencies,
   - consolidate the two `*_diagnostics.launch.py` files,
   - update `rover_bringup/launch/{full_system,mission_only,safety_runtime,runtime_validation}.launch.py`,
   - update `rover_ws/tests/test_package_manifests.py::REQUIRED_PACKAGES`
     and the diagnostic-specific tests,
   - update `backend/app/runtime_validation/expected_nodes.py`,
     `host_qualification.py`, and `static_validator.py`,
   - update `backend/app/verification/requirements.py` and
     `backend/app/reliability_impact/subsystem_classifier.py`,
   - update `ARCHITECTURE.md`, `TRACEABILITY_MATRIX.md`,
     `SOURCE_TO_EVIDENCE_TRACEABILITY.md`, `SYSTEM_CONTEXT.md`.
3. The "11 → 8" framing is **closed**. The architecturally correct
   count is 10 (after the diagnostics merge).

The follow-up PR is intentionally not landed from this sandbox: the
`ros-jazzy-runtime` and `ros-jazzy-replay-review` jobs run on
self-hosted ROS Jazzy runners and are triggered manually
(`workflow_dispatch`), so PR-time CI cannot validate the colcon
build. The merge should be executed where colcon + rclpy +
ament_python are available.

## Consequences

### Positive

- Future contributors see one consolidated diagnostics package
  instead of two near-duplicates, but no architectural boundary
  (safety / mission / sensor / observability / URDF / simulation /
  world model) is collapsed into another.
- The "11 → 8" goal stops driving misformulated mergers. The ADR
  is the authoritative answer to the "why not consolidate?"
  question.

### Negative

- Two packages of duplicated launch / setup boilerplate remain in
  place until the diagnostics-merge follow-up lands. The
  duplication is small (PR 4a already deleted the orphan `config/`
  globs in the two `setup.py` files).

## References

- `CLAUDE.md` — safety authority invariant.
- ADR-004 — safety-supervisor authority model.
- ADR-010, ADR-011 — sister "close the consolidation task" ADRs
  for the validator packages and the post-run analysis packages.
- `rover_ws/src/`.
- `rover_ws/tests/test_package_manifests.py`.

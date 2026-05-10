"""Requirement registry.

Each platform-level guarantee is declared here as a :class:`Requirement`
with a stable ``REQ-*`` ID, a human description, and pointers to:

* the architecture-doc section that justifies it,
* the implementation module(s) that satisfy it,
* the scenarios that exercise it (if any),
* the tests that assert it,
* the evidence artefacts produced when verification runs.

Requirements never move — the IDs are stable across releases. Adding
a new requirement requires a corresponding architecture doc reference
and at least one test or scenario binding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RequirementKind(str, Enum):
    SAFETY = "safety"
    FAULT = "fault"
    REPLAY = "replay"
    MISSION = "mission"
    WORLD = "world"
    DIAGNOSTICS = "diagnostics"
    OPERATOR = "operator"
    RUNTIME = "runtime"
    INCIDENT = "incident"
    ANALYTICS = "analytics"
    IMPACT = "impact"
    PROGRAMME = "programme"


@dataclass(frozen=True)
class Requirement:
    req_id: str
    kind: RequirementKind
    title: str
    description: str
    architecture_refs: tuple[str, ...] = ()
    """Human-readable references to ``docs/`` sections (e.g.
    ``docs/SAFETY_MODEL.md#section-3``). Free text; not parsed."""

    implementation_refs: tuple[str, ...] = ()
    """Module / file references that implement the requirement."""

    scenario_refs: tuple[str, ...] = ()
    """Scenario IDs that exercise the requirement."""

    test_refs: tuple[str, ...] = ()
    """Pytest ``module::test`` references that assert the requirement."""

    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_id": self.req_id,
            "kind": self.kind.value,
            "title": self.title,
            "description": self.description,
            "architecture_refs": list(self.architecture_refs),
            "implementation_refs": list(self.implementation_refs),
            "scenario_refs": list(self.scenario_refs),
            "test_refs": list(self.test_refs),
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Registry.
#
# Adding a requirement:
# 1. Pick the next free ID in its category (e.g. REQ-SAFE-009).
# 2. Add at least one architecture_refs entry.
# 3. Add at least one test_refs entry that asserts the requirement.
# 4. Add scenario_refs if a scenario exercises it.
# 5. Run ``pytest backend/tests/test_requirements_registry.py`` to
#    confirm the registry remains internally consistent.
# ---------------------------------------------------------------------------


REQUIREMENTS: tuple[Requirement, ...] = (
    Requirement(
        req_id="REQ-SAFE-001",
        kind=RequirementKind.SAFETY,
        title="Motion authority is centralised on the safety supervisor",
        description=(
            "All actuator-bound motion must flow through the safety "
            "supervisor's arbiter. No other module may produce an "
            "AuthorizedMotionCommand value or publish to "
            "/cmd_vel_authorized."
        ),
        architecture_refs=(
            "ARCHITECTURE.md#2-2-safety-centric-autonomy",
            "docs/SAFETY_MODEL.md#3-motion-authorization-rules",
            "docs/adr/ADR-004-safety-supervisor-authority-model.md",
        ),
        implementation_refs=(
            "backend/app/safety/supervisor.py",
            "backend/app/safety/arbitration.py",
            "rover_ws/src/rover_safety_bridge/rover_safety_bridge/safety_bridge_node.py",
        ),
        scenario_refs=(
            "nominal_run",
            "nominal_waypoint_patrol",
            "stale_lidar_restricted_mode",
        ),
        test_refs=(
            "backend/tests/test_simulation_engine.py::test_supervisor_is_only_publisher_of_authorized_motion",
            "backend/tests/test_validation_module.py::test_validate_safety_pipeline",
            "backend/tests/test_orchestrator.py::test_orchestrator_does_not_construct_authorized_motion",
            "rover_ws/tests/test_node_modules.py::test_safety_bridge_node_only_publishes_authorized",
            "rover_ws/tests/test_mission_runtime_packages.py::test_nav2_clamp_does_not_subscribe_to_authorized",
        ),
    ),
    Requirement(
        req_id="REQ-SAFE-002",
        kind=RequirementKind.SAFETY,
        title="SAFE_STOP forces zero authorized motion",
        description=(
            "When the supervisor is in SAFE_STOP, every published "
            "/cmd_vel_authorized must carry zero linear and zero "
            "angular velocity, regardless of any /cmd_vel_requested "
            "input."
        ),
        architecture_refs=(
            "docs/SAFETY_MODEL.md#9-safe-stop-semantics",
        ),
        implementation_refs=(
            "backend/app/safety/arbitration.py",
            "backend/app/safety/supervisor.py",
        ),
        scenario_refs=(
            "stale_lidar_restricted_mode",
            "command_timeout_safe_stop",
            "bridge_disconnect_safe_stop",
            "safe_stop_during_active_mission",
        ),
        test_refs=(
            "backend/tests/test_motion_arbitration.py::test_safe_stop_forces_zero",
            "rover_ws/tests/test_safety_bridge_core.py::test_safe_stop_zeros_motion",
            "backend/tests/test_validation_module.py::test_validate_safety_pipeline",
        ),
    ),
    Requirement(
        req_id="REQ-SAFE-003",
        kind=RequirementKind.SAFETY,
        title="E_STOP_LATCHED requires explicit operator reset",
        description=(
            "Once E_STOP_LATCHED is asserted, the supervisor may not "
            "self-clear. Recovery requires an explicit operator reset "
            "event."
        ),
        architecture_refs=(
            "docs/SAFETY_MODEL.md#10-e-stop-latch-semantics",
        ),
        implementation_refs=(
            "backend/app/safety/supervisor.py",
        ),
        scenario_refs=(
            "estop_latched_manual_reset_required",
        ),
        test_refs=(
            "backend/tests/test_safety_transitions.py::test_estop_latched_only_to_recovery",
            "backend/tests/test_simulation_engine.py::test_estop_does_not_self_clear",
            "rover_ws/tests/test_safety_bridge_core.py::test_estop_latches_until_explicit_reset",
        ),
    ),
    Requirement(
        req_id="REQ-SAFE-004",
        kind=RequirementKind.SAFETY,
        title="Restricted-mode authorized motion is clamped to per-state limits",
        description=(
            "When the supervisor is in ACTIVE_RESTRICTED, ACTIVE_DEGRADED, "
            "or any zone-clamped configuration, the arbiter must clamp "
            "authorized motion to the documented limits and emit a "
            "motion_arbitration.clamped event."
        ),
        architecture_refs=(
            "docs/ODD.md#6-operational-limits",
            "docs/SAFETY_MODEL.md#3-motion-authorization-rules",
        ),
        implementation_refs=(
            "backend/app/safety/arbitration.py",
        ),
        scenario_refs=(
            "restricted_mode_navigation",
        ),
        test_refs=(
            "backend/tests/test_motion_arbitration.py::test_active_restricted_clamps_more_aggressively",
            "backend/tests/test_motion_arbitration.py::test_active_normal_clamps_overspeed",
        ),
    ),
    Requirement(
        req_id="REQ-FAULT-001",
        kind=RequirementKind.FAULT,
        title="Fault injection alters inputs only; never sets safety state",
        description=(
            "The fault injection subsystem may modify sensor frames, "
            "topic timing, and watchdog pets, but must never publish "
            "/safety/state or transition the supervisor's state machine "
            "directly."
        ),
        architecture_refs=(
            "docs/FAULT_INJECTION.md#2-1-faults-alter-inputs-and-timing-not-safety-state",
        ),
        implementation_refs=(
            "backend/app/faults/injector.py",
        ),
        scenario_refs=(
            "stale_lidar_restricted_mode",
            "odometry_divergence_safe_stop",
            "bridge_disconnect_safe_stop",
            "wheel_slip_degraded_mode",
        ),
        test_refs=(
            "backend/tests/test_fault_injection.py::test_injector_does_not_emit_safety_transitions",
            "backend/tests/test_simulation_engine.py::test_fault_injection_does_not_emit_safety_transitions",
            "backend/tests/test_validation_module.py::test_validate_safety_pipeline",
        ),
    ),
    Requirement(
        req_id="REQ-FAULT-002",
        kind=RequirementKind.FAULT,
        title="Every supported fault class has a corresponding scenario",
        description=(
            "Each fault class in docs/FAULT_INJECTION.md has at least "
            "one scenario that exercises its lifecycle (armed -> fired "
            "-> cleared) and asserts the supervisor's reaction."
        ),
        architecture_refs=(
            "docs/FAULT_INJECTION.md#4-supported-mvp-fault-classes",
        ),
        implementation_refs=(
            "backend/scenarios/",
        ),
        scenario_refs=(
            "stale_lidar_restricted_mode",
            "odometry_divergence_safe_stop",
            "command_timeout_safe_stop",
            "bridge_disconnect_safe_stop",
            "wheel_slip_degraded_mode",
        ),
        test_refs=(
            "backend/tests/test_scenario_suite.py::test_full_suite_passes",
        ),
    ),
    Requirement(
        req_id="REQ-REPLAY-001",
        kind=RequirementKind.REPLAY,
        title="Every scenario run emits replayable event artefacts",
        description=(
            "Each scenario run must produce a runs/<run_id>/ directory "
            "containing metadata.json, events.jsonl, states.jsonl, "
            "commands.jsonl, sensor_readings.jsonl, "
            "incident-summary.md, and the Phase 2 mission artefacts. "
            "Every event must validate against the canonical envelope."
        ),
        architecture_refs=(
            "docs/REPLAY_SYSTEM.md#9-storage-layout",
            "docs/EVENT_MODEL.md#3-event-envelope-schema",
        ),
        implementation_refs=(
            "backend/app/telemetry/run_recorder.py",
            "backend/app/replay/recorder.py",
        ),
        scenario_refs=(
            "nominal_run",
            "stale_lidar_restricted_mode",
            "nominal_waypoint_patrol",
            "keepout_zone_violation",
        ),
        test_refs=(
            "backend/tests/test_replay_recorder.py::test_run_directory_layout",
            "backend/tests/test_validation_module.py::test_validate_run_directory_on_real_run",
            "backend/tests/test_mission_replay.py::test_mission_run_directory_has_phase2_artefacts",
        ),
    ),
    Requirement(
        req_id="REQ-REPLAY-002",
        kind=RequirementKind.REPLAY,
        title="Per-producer event ordering is monotonic in sim_time_ns",
        description=(
            "Events emitted by the same (subsystem, node) pair must "
            "appear in events.jsonl in non-decreasing sim_time_ns "
            "order. Cross-producer ordering is best-effort."
        ),
        architecture_refs=(
            "docs/EVENT_MODEL.md#8-event-ordering-rules",
        ),
        implementation_refs=(
            "backend/app/validation/replay_validator.py",
        ),
        scenario_refs=(
            "nominal_run",
            "stale_lidar_restricted_mode",
        ),
        test_refs=(
            "backend/tests/test_validation_module.py::test_validate_run_directory_on_real_run",
        ),
    ),
    Requirement(
        req_id="REQ-MISSION-001",
        kind=RequirementKind.MISSION,
        title="Mission runtime requests motion but never authorises it",
        description=(
            "The mission orchestrator must produce only "
            "RequestedMotionCommand values, never AuthorizedMotionCommand. "
            "This invariant holds for both the deterministic engine "
            "and the ROS 2 mission node, and for the Nav2 velocity-clamp "
            "boundary."
        ),
        architecture_refs=(
            "ARCHITECTURE.md#15c-mission-runtime-and-bounded-navigation-phase-2",
            "docs/ROADMAP.md#3d-phase-2-mission-runtime-deterministic-navigation-orchestration",
        ),
        implementation_refs=(
            "backend/app/mission/orchestrator.py",
            "rover_ws/src/rover_mission_runtime/rover_mission_runtime/mission_node.py",
            "rover_ws/src/rover_mission_runtime/rover_mission_runtime/nav2_velocity_clamp.py",
        ),
        scenario_refs=(
            "nominal_waypoint_patrol",
            "waypoint_timeout_recovery",
            "keepout_zone_violation",
        ),
        test_refs=(
            "backend/tests/test_orchestrator.py::test_orchestrator_does_not_construct_authorized_motion",
            "rover_ws/tests/test_mission_runtime_packages.py::test_mission_node_publishes_only_cmd_vel_requested",
            "rover_ws/tests/test_mission_runtime_packages.py::test_nav2_clamp_does_not_subscribe_to_authorized",
        ),
    ),
    Requirement(
        req_id="REQ-MISSION-002",
        kind=RequirementKind.MISSION,
        title="Recovery is bounded and terminates in MISSION_ABORT",
        description=(
            "The recovery policy enforces a per-waypoint attempt "
            "budget. Exceeding the budget transitions the orchestrator "
            "to MISSION_ABORTING and on the next tick to "
            "MISSION_ABORTED. MISSION_ABORT is terminal."
        ),
        architecture_refs=(
            "docs/ROADMAP.md#3d-phase-2-mission-runtime-deterministic-navigation-orchestration",
        ),
        implementation_refs=(
            "backend/app/mission/recovery.py",
            "backend/app/mission/orchestrator.py",
        ),
        scenario_refs=(
            "waypoint_timeout_recovery",
            "mission_abort_after_fault_escalation",
        ),
        test_refs=(
            "backend/tests/test_recovery_policy.py::test_attempts_exceeded_engages_mission_abort",
            "backend/tests/test_recovery_policy.py::test_mission_abort_is_terminal",
            "backend/tests/test_mission_replay.py::test_recovery_events_recorded_when_mission_aborts",
        ),
    ),
    Requirement(
        req_id="REQ-WORLD-001",
        kind=RequirementKind.WORLD,
        title="Keepout violations emit events and constrain mission behavior",
        description=(
            "Entering a declared keepout zone must emit a "
            "world_model.keepout_violation event and engage the "
            "recovery policy via SAFE_STOP_ESCALATION, transitioning "
            "the mission to MISSION_DEGRADED."
        ),
        architecture_refs=(
            "ARCHITECTURE.md#15c-mission-runtime-and-bounded-navigation-phase-2",
        ),
        implementation_refs=(
            "backend/app/world_model/world_model.py",
            "backend/app/mission/orchestrator.py",
            "backend/app/mission/recovery.py",
        ),
        scenario_refs=(
            "keepout_zone_violation",
        ),
        test_refs=(
            "backend/tests/test_world_model.py::test_world_model_emits_keepout_violation_hazard",
            "backend/tests/test_recovery_policy.py::test_keepout_violation_escalates_to_safe_stop_escalation",
        ),
    ),
    Requirement(
        req_id="REQ-DIAG-001",
        kind=RequirementKind.DIAGNOSTICS,
        title="Runtime diagnostics report subsystem health without owning safety",
        description=(
            "The runtime diagnostics monitors must report topic "
            "freshness, bridge advertisement, and TF tree health "
            "without ever publishing /safety/state or transitioning "
            "the supervisor."
        ),
        architecture_refs=(
            "ARCHITECTURE.md#15b-runtime-validation-and-diagnostics-phase-1c",
        ),
        implementation_refs=(
            "backend/app/diagnostics/topic_monitor.py",
            "backend/app/diagnostics/bridge_health.py",
            "rover_ws/src/rover_runtime_diagnostics/",
        ),
        test_refs=(
            "backend/tests/test_diagnostics_core.py::test_observed_topic_starts_fresh_then_goes_warn_then_error",
            "backend/tests/test_diagnostics_core.py::test_bridge_monitor_unadvertised_topic_is_error",
        ),
    ),
    Requirement(
        req_id="REQ-OP-001",
        kind=RequirementKind.OPERATOR,
        title="Operator E-stop transitions to E_STOP_LATCHED on the same tick",
        description=(
            "An operator E-stop pulse asserted on /operator/estop "
            "must cause the supervisor to enter E_STOP_LATCHED on the "
            "same tick the pulse is observed."
        ),
        architecture_refs=(
            "docs/SAFETY_MODEL.md#10-e-stop-latch-semantics",
        ),
        implementation_refs=(
            "backend/app/safety/supervisor.py",
        ),
        scenario_refs=(
            "estop_latched_manual_reset_required",
        ),
        test_refs=(
            "backend/tests/test_simulation_engine.py::test_estop_scenario_latches",
            "rover_ws/tests/test_safety_bridge_core.py::test_estop_latches_until_explicit_reset",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-001",
        kind=RequirementKind.RUNTIME,
        title="Full system launch must be runtime-verifiable",
        description=(
            "rover_bringup/full_system.launch.py must be invocable on a "
            "ROS 2 Jazzy host and produce the expected node graph + "
            "topic graph. The runtime smoke test asserts process "
            "startup, node presence, and clean shutdown."
        ),
        architecture_refs=(
            "ARCHITECTURE.md#15a-ros-2-integration-layer-phase-1b",
            "rover_ws/tests/manual.md",
            "docs/RUNTIME_VALIDATION_RUNBOOK.md",
        ),
        implementation_refs=(
            "rover_ws/src/rover_bringup/launch/full_system.launch.py",
            "rover_ws/tools/launch_smoke_test.py",
            "rover_ws/tools/live_runtime_validator.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_validation_tooling.py::test_launch_smoke_static_mode_passes",
            "rover_ws/tests/test_launch_files.py::test_full_system_composes_required_launches",
        ),
        notes=(
            "Live execution requires a Jazzy host. CI runs in static-only "
            "mode; live evidence is collected via the runbook procedure."
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-002",
        kind=RequirementKind.RUNTIME,
        title="Required ROS topics must be discoverable and type-checked",
        description=(
            "Every topic listed in app.runtime_validation.expected_topics "
            "must be advertised by the running graph with the documented "
            "message type. The topic probe records advertisement status, "
            "type match, and freshness for each topic."
        ),
        architecture_refs=(
            "docs/REPLAY_SYSTEM.md#7-required-recorded-topics",
            "docs/SYSTEM_CONTEXT.md#8a-ros-2-gazebo-layer-phase-1b",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/expected_topics.py",
            "rover_ws/tools/topic_probe.py",
            "rover_ws/src/rover_sim_gazebo/config/ros_gz_bridge.yaml",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_validation_tooling.py::test_topic_probe_static_mode_lists_expected_topics",
            "rover_ws/tests/test_runtime_validation_tooling.py::test_topic_probe_static_mode_marks_live_checks_not_executed",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-003",
        kind=RequirementKind.RUNTIME,
        title="TF tree must expose expected critical frames",
        description=(
            "The live TF tree must contain odom -> base_link and the "
            "documented sensor / wheel frames. The TF probe asserts "
            "frame presence, single-root structure, and that "
            "static transforms exist for fixed sensor mounts."
        ),
        architecture_refs=(
            "rover_ws/src/rover_description/urdf/rover.urdf.xacro",
            "docs/SYSTEM_CONTEXT.md#8a-ros-2-gazebo-layer-phase-1b",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/expected_tf_frames.py",
            "rover_ws/tools/tf_probe.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_validation_tooling.py::test_tf_probe_static_mode_passes_against_workspace_urdf",
            "rover_ws/tests/test_urdf.py::test_required_links_present",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-004",
        kind=RequirementKind.RUNTIME,
        title="Authorized command path must be verified at runtime",
        description=(
            "The command-path probe must publish a /cmd_vel_requested "
            "stream and observe /cmd_vel_authorized to confirm the "
            "supervisor is the only producer. SAFE_STOP / E_STOP / "
            "expired-command pathways must be exercised and the "
            "authorised stream must zero accordingly. No producer "
            "other than the supervisor may publish on "
            "/cmd_vel_authorized at runtime."
        ),
        architecture_refs=(
            "docs/SAFETY_MODEL.md#3-motion-authorization-rules",
            "docs/adr/ADR-004-safety-supervisor-authority-model.md",
        ),
        implementation_refs=(
            "rover_ws/tools/command_path_probe.py",
            "rover_ws/src/rover_safety_bridge/rover_safety_bridge/safety_bridge_node.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_validation_tooling.py::test_command_path_probe_static_mode_passes",
            "rover_ws/tests/test_node_modules.py::test_safety_bridge_node_only_publishes_authorized",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-005",
        kind=RequirementKind.RUNTIME,
        title="Live validation reports must distinguish status categories",
        description=(
            "RUNTIME_VALIDATION_REPORT.md and the JSON manifest must "
            "carry one of {passed, failed, partial, skipped, "
            "not_executed} per check. A check that requires a Jazzy "
            "host but ran in CI must be reported as not_executed with "
            "an explicit reason; never as passed."
        ),
        architecture_refs=(
            "docs/VERIFICATION_STRATEGY.md#2-status-vocabulary",
            "docs/RUNTIME_VALIDATION_REPORT.md",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/report_renderer.py",
            "backend/app/runtime_validation/static_validator.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_validation_tooling.py::test_runtime_report_distinguishes_status_categories",
            "rover_ws/tests/test_runtime_validation_tooling.py::test_runtime_report_includes_known_limitations",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-006",
        kind=RequirementKind.RUNTIME,
        title="ROS host prerequisites must be qualifiable",
        description=(
            "Before launching the runtime stack, the platform must be "
            "able to qualify the host: Ubuntu version, ROS 2 distro, "
            "Gazebo Harmonic presence, colcon, ros_gz_bridge, the "
            "required ROS packages, the Python backend importability, "
            "and the workspace structure. Each check returns one of "
            "passed / failed / partial / skipped / not_executed with a "
            "machine-readable reason."
        ),
        architecture_refs=(
            "docs/RUNTIME_QUALIFICATION_RUNBOOK.md",
            "docs/SYSTEM_CONTEXT.md#8a-ros-2-gazebo-layer-phase-1b",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/host_qualification.py",
            "rover_ws/tools/qualify_ros_host.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_qualification.py::test_host_qualification_runs_without_ros",
            "rover_ws/tests/test_runtime_qualification.py::test_host_qualification_marks_ros_not_executed",
            "rover_ws/tests/test_runtime_qualification.py::test_host_qualification_distro_parsing",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-007",
        kind=RequirementKind.RUNTIME,
        title="Runtime qualification runs must produce evidence artefacts",
        description=(
            "Each qualified runtime run materialises a complete "
            "evidence directory under evidence/runtime/<run_id>/ with "
            "host-qualification, runtime-validation, topic / TF / node "
            "snapshots, command-path audit, replay-integrity (when "
            "applicable), per-scenario summaries, and a "
            "qualification-summary.md. The evidence index must list "
            "every retained run so reviewers can navigate without ad-hoc "
            "filesystem queries."
        ),
        architecture_refs=(
            "docs/RUNTIME_QUALIFICATION_RUNBOOK.md",
            "docs/EVIDENCE_INDEX.md",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/evidence_index.py",
            "rover_ws/tools/qualified_runtime_run.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_qualification.py::test_qualified_runtime_run_writes_full_evidence_dir",
            "rover_ws/tests/test_runtime_qualification.py::test_evidence_index_lists_runs_in_chronological_order",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-008",
        kind=RequirementKind.RUNTIME,
        title="Runtime evidence must support baseline comparison",
        description=(
            "A baseline captured from a known-good qualification run "
            "must be comparable to subsequent runs. The comparator "
            "emits per-category deltas (topic inventory, TF inventory, "
            "node inventory, event counts, safety-state transitions, "
            "command authorisation, replay artefacts, diagnostic "
            "health) and classifies each delta as expected_difference, "
            "warning, regression, or critical_regression. No regression "
            "is silently auto-ignored."
        ),
        architecture_refs=(
            "docs/RUNTIME_QUALIFICATION_RUNBOOK.md",
            "docs/VERIFICATION_STRATEGY.md#2-status-vocabulary",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/baselines.py",
            "rover_ws/tools/compare_runtime_baseline.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_qualification.py::test_baseline_diff_classifies_expected_differences",
            "rover_ws/tests/test_runtime_qualification.py::test_baseline_diff_flags_missing_topic_as_critical",
            "rover_ws/tests/test_runtime_qualification.py::test_baseline_diff_flags_extra_node_as_warning",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-009",
        kind=RequirementKind.RUNTIME,
        title="Qualification reports must distinguish static vs live runtime checks",
        description=(
            "RUNTIME_QUALIFICATION_REPORT.md and LIVE_RUNTIME_STATUS.md "
            "must label every check as static-source, static-workspace, "
            "or live-runtime. A check that requires a Jazzy host but "
            "ran in static mode is reported as not_executed with an "
            "explicit reason; never rolled up as a live pass."
        ),
        architecture_refs=(
            "docs/RUNTIME_QUALIFICATION_REPORT.md",
            "docs/LIVE_RUNTIME_STATUS.md",
            "docs/VERIFICATION_STRATEGY.md#2-status-vocabulary",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/qualification_report.py",
            "backend/app/runtime_validation/report_renderer.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_qualification.py::test_qualification_report_labels_check_origin",
            "rover_ws/tests/test_runtime_qualification.py::test_live_runtime_status_distinguishes_static_from_live",
        ),
    ),
    Requirement(
        req_id="REQ-RUNTIME-010",
        kind=RequirementKind.RUNTIME,
        title="Runtime regressions must be classified and reportable",
        description=(
            "Runtime regression detection runs as part of the "
            "qualification orchestrator: missing topics, missing nodes, "
            "missing TF frames, stale topics, unexpected safety "
            "transitions, replay corruption, missing replay artefacts, "
            "unexpected command authorisation, and launch instability "
            "are detected with severity (warning / regression / "
            "critical_regression) and each carries an evidence "
            "reference."
        ),
        architecture_refs=(
            "docs/RUNTIME_QUALIFICATION_RUNBOOK.md",
            "docs/VERIFICATION_STRATEGY.md#2-status-vocabulary",
        ),
        implementation_refs=(
            "backend/app/runtime_validation/regression.py",
            "backend/app/runtime_validation/baselines.py",
        ),
        test_refs=(
            "rover_ws/tests/test_runtime_qualification.py::test_regression_detector_classifies_severity",
            "rover_ws/tests/test_runtime_qualification.py::test_regression_detector_emits_evidence_references",
        ),
    ),
    Requirement(
        req_id="REQ-INCIDENT-001",
        kind=RequirementKind.INCIDENT,
        title="Runtime and scenario evidence must be reconstructable into ordered incident timelines",
        description=(
            "The incident analysis layer must load runtime evidence "
            "(evidence/runtime/<run_id>/) and scenario evidence "
            "(evidence/scenarios/<scenario_id>/), normalise the "
            "underlying events, and emit a deterministically ordered "
            "timeline. Out-of-order entries and missing timestamps "
            "must be surfaced as warnings, never silently reordered."
        ),
        architecture_refs=(
            "docs/INCIDENT_RECONSTRUCTION.md",
            "docs/INCIDENT_ANALYSIS_STRATEGY.md",
        ),
        implementation_refs=(
            "backend/app/incident_analysis/loader.py",
            "backend/app/incident_analysis/normalizer.py",
            "backend/app/incident_analysis/timeline.py",
        ),
        test_refs=(
            "backend/tests/test_incident_analysis.py::test_loader_handles_missing_files",
            "backend/tests/test_incident_analysis.py::test_timeline_orders_events_deterministically",
            "backend/tests/test_incident_analysis.py::test_normalizer_preserves_evidence_origin",
        ),
    ),
    Requirement(
        req_id="REQ-INCIDENT-002",
        kind=RequirementKind.INCIDENT,
        title="Incident reports must distinguish direct evidence from inferred causality",
        description=(
            "The causality engine must assign a confidence level to "
            "every link (direct, strong, moderate, weak, inconclusive) "
            "and never fabricate a missing transition. Reports must "
            "label inferred links so reviewers can see the difference "
            "between an observed event chain and an inferred one."
        ),
        architecture_refs=(
            "docs/INCIDENT_RECONSTRUCTION.md",
            "docs/INCIDENT_ANALYSIS_STRATEGY.md",
        ),
        implementation_refs=(
            "backend/app/incident_analysis/causality.py",
            "backend/app/incident_analysis/reporter.py",
        ),
        test_refs=(
            "backend/tests/test_incident_analysis.py::test_causality_stale_lidar_chain",
            "backend/tests/test_incident_analysis.py::test_causality_missing_link_downgrades_confidence",
            "backend/tests/test_incident_analysis.py::test_report_labels_inferred_links",
        ),
    ),
    Requirement(
        req_id="REQ-INCIDENT-003",
        kind=RequirementKind.INCIDENT,
        title="Incident reports must identify missing and contradictory evidence",
        description=(
            "The incident classifier and reporter must surface missing "
            "evidence files, partial runs, static-only runs, and "
            "contradictory artefacts (e.g. a safety_transition_audit "
            "ok=true while events.jsonl reports an unauthorised "
            "publisher). No analysis may report a clean outcome when "
            "evidence contradicts itself."
        ),
        architecture_refs=(
            "docs/INCIDENT_RECONSTRUCTION.md",
            "docs/VERIFICATION_STRATEGY.md#2-status-vocabulary",
        ),
        implementation_refs=(
            "backend/app/incident_analysis/classifier.py",
            "backend/app/incident_analysis/reporter.py",
        ),
        test_refs=(
            "backend/tests/test_incident_analysis.py::test_classifier_flags_missing_evidence",
            "backend/tests/test_incident_analysis.py::test_classifier_flags_contradictory_evidence",
            "backend/tests/test_incident_analysis.py::test_report_includes_missing_evidence_section",
        ),
    ),
    Requirement(
        req_id="REQ-INCIDENT-004",
        kind=RequirementKind.INCIDENT,
        title="Foxglove replay hints must be generated without requiring Foxglove runtime installation",
        description=(
            "The Foxglove integration is metadata + workflow support "
            "only. Tests must not require Foxglove to be installed. "
            "The hints file lists topics, layout, and timeline markers "
            "so an operator can open the recorded bag in Foxglove with "
            "the right context."
        ),
        architecture_refs=(
            "docs/FOXGLOVE_REPLAY_WORKFLOW.md",
        ),
        implementation_refs=(
            "backend/app/incident_analysis/foxglove.py",
            "foxglove/layouts/incident-review-layout.json",
        ),
        test_refs=(
            "backend/tests/test_incident_analysis.py::test_foxglove_hints_emit_topics_and_layout",
            "backend/tests/test_incident_analysis.py::test_foxglove_layout_file_is_valid_json",
        ),
    ),
    Requirement(
        req_id="REQ-INCIDENT-005",
        kind=RequirementKind.INCIDENT,
        title="Incident index must support scenario, severity, outcome, and evidence-status review",
        description=(
            "The incident index lists every retained incident bundle "
            "with filterable fields (scenario_id, severity, outcome, "
            "evidence_status, terminal_safety_state) so reviewers can "
            "navigate without ad-hoc filesystem queries. Filter "
            "functions are pure-logic and tested."
        ),
        architecture_refs=(
            "docs/INCIDENT_INDEX.md",
            "docs/INCIDENT_RECONSTRUCTION.md",
        ),
        implementation_refs=(
            "backend/app/incident_analysis/index.py",
            "rover_ws/tools/index_incidents.py",
        ),
        test_refs=(
            "backend/tests/test_incident_analysis.py::test_incident_index_filters_by_severity",
            "backend/tests/test_incident_analysis.py::test_incident_index_filters_by_outcome",
            "backend/tests/test_incident_analysis.py::test_incident_index_filters_by_evidence_status",
        ),
    ),
    Requirement(
        req_id="REQ-REPLAY-006",
        kind=RequirementKind.REPLAY,
        title="Incident bundles must support replay review manifest generation",
        description=(
            "Each incident bundle must be able to produce a replay "
            "review manifest that lists the required topics, the bag "
            "artefacts available, the timeline markers, and a pointer "
            "to the Foxglove layout. The manifest is read-only with "
            "respect to runtime evidence and never fabricates a bag "
            "inventory."
        ),
        architecture_refs=(
            "docs/REPLAY_REVIEW_RUNBOOK.md",
            "docs/FOXGLOVE_REPLAY_WORKFLOW.md",
        ),
        implementation_refs=(
            "backend/app/replay_review/manifest.py",
            "backend/app/replay_review/bundle.py",
            "rover_ws/tools/build_replay_review_bundle.py",
        ),
        test_refs=(
            "backend/tests/test_replay_review.py::test_manifest_lists_expected_topics",
            "backend/tests/test_replay_review.py::test_manifest_records_missing_topics",
            "backend/tests/test_replay_review.py::test_manifest_includes_known_limitations",
        ),
    ),
    Requirement(
        req_id="REQ-REPLAY-007",
        kind=RequirementKind.REPLAY,
        title="Replay review reports must distinguish missing, partial, static-only, and bag-backed evidence",
        description=(
            "Replay review reports use a controlled status vocabulary "
            "(ready, partial, missing_bag, static_only, not_executed, "
            "failed, passed). A static scenario fixture is never "
            "marked bag-backed; a missing bag never becomes a passing "
            "review. Status downgrades carry an explicit reason."
        ),
        architecture_refs=(
            "docs/REPLAY_REVIEW_RUNBOOK.md",
            "docs/VERIFICATION_STRATEGY.md#2-status-vocabulary",
        ),
        implementation_refs=(
            "backend/app/replay_review/models.py",
            "backend/app/replay_review/reporter.py",
            "backend/app/replay_review/validator.py",
        ),
        test_refs=(
            "backend/tests/test_replay_review.py::test_validator_flags_missing_bag",
            "backend/tests/test_replay_review.py::test_validator_static_only_remains_static_only",
            "backend/tests/test_replay_review.py::test_reporter_includes_status_section",
        ),
    ),
    Requirement(
        req_id="REQ-REPLAY-008",
        kind=RequirementKind.REPLAY,
        title="Timeline markers must preserve evidence origin and confidence",
        description=(
            "Replay markers are derived from incident timeline entries. "
            "Each marker carries the source event id, the source file, "
            "the evidence_origin, and the causality confidence label. "
            "Markers without sim_time_ns are emitted with relative-time "
            "alignment marked partial; markers are never invented when "
            "the timeline has no matching entry."
        ),
        architecture_refs=(
            "docs/REPLAY_REVIEW_RUNBOOK.md",
            "docs/INCIDENT_RECONSTRUCTION.md",
        ),
        implementation_refs=(
            "backend/app/replay_review/marker.py",
        ),
        test_refs=(
            "backend/tests/test_replay_review.py::test_markers_preserve_evidence_origin",
            "backend/tests/test_replay_review.py::test_markers_partial_alignment_when_sim_time_missing",
            "backend/tests/test_replay_review.py::test_markers_never_fabricated",
        ),
    ),
    Requirement(
        req_id="REQ-REPLAY-009",
        kind=RequirementKind.REPLAY,
        title="Foxglove review artefacts must be generated without requiring Foxglove installation in unit tests",
        description=(
            "The Foxglove session bundle is metadata only: layout "
            "pointer, panel hints, marker overlays, recommended data "
            "source. The repository ships a canonical layout JSON; "
            "unit tests parse it as JSON and never require Foxglove "
            "Studio to be installed. The bundle is a plain JSON "
            "document; the repo documents this explicitly rather than "
            "implying an official Foxglove import format."
        ),
        architecture_refs=(
            "docs/FOXGLOVE_REPLAY_WORKFLOW.md",
            "docs/REPLAY_REVIEW_RUNBOOK.md",
        ),
        implementation_refs=(
            "backend/app/replay_review/foxglove_session.py",
            "foxglove/layouts/incident-review-layout.json",
        ),
        test_refs=(
            "backend/tests/test_replay_review.py::test_foxglove_session_is_valid_json",
            "backend/tests/test_replay_review.py::test_foxglove_session_lists_expected_panels",
            "backend/tests/test_replay_review.py::test_foxglove_session_does_not_require_runtime",
        ),
    ),
    Requirement(
        req_id="REQ-REPLAY-010",
        kind=RequirementKind.REPLAY,
        title="Live replay workflows must run only on self-hosted ROS / Gazebo runners",
        description=(
            "The replay-review GitHub workflow is workflow_dispatch "
            "only and uses a self-hosted runner labelled with "
            "ros-jazzy. github-hosted runners cannot drive Gazebo "
            "Harmonic reliably; running there would produce "
            "misleading evidence. The workflow does not run on "
            "github-hosted runners."
        ),
        architecture_refs=(
            "docs/REPLAY_REVIEW_RUNBOOK.md",
            "docs/RUNTIME_QUALIFICATION_RUNBOOK.md",
        ),
        implementation_refs=(
            ".github/workflows/ros-jazzy-replay-review.yml",
        ),
        test_refs=(
            "backend/tests/test_replay_review.py::test_replay_workflow_uses_self_hosted_runner",
            "backend/tests/test_replay_review.py::test_replay_workflow_is_dispatch_only",
        ),
    ),
    Requirement(
        req_id="REQ-ANALYTICS-001",
        kind=RequirementKind.ANALYTICS,
        title="Replay bundles must support deterministic replay coverage analysis",
        description=(
            "The replay analytics layer must derive coverage metrics "
            "(expected_topics_present_pct, marker_alignment_pct, "
            "timeline_alignment_pct, replay_validation_pass_rate, "
            "evidence_completeness_pct, review_artifact_completeness_pct) "
            "from the replay-review bundle alone. The same input must "
            "yield byte-identical metrics on every run."
        ),
        architecture_refs=(
            "docs/REPLAY_ANALYTICS.md",
            "docs/REPLAY_QUALITY_SCORING.md",
        ),
        implementation_refs=(
            "backend/app/replay_analytics/coverage.py",
            "backend/app/replay_analytics/loader.py",
        ),
        test_refs=(
            "backend/tests/test_replay_analytics.py::test_coverage_metrics_are_deterministic",
            "backend/tests/test_replay_analytics.py::test_coverage_unavailable_when_no_inventory",
            "backend/tests/test_replay_analytics.py::test_coverage_marks_metrics_unavailable_honestly",
        ),
    ),
    Requirement(
        req_id="REQ-ANALYTICS-002",
        kind=RequirementKind.ANALYTICS,
        title="Replay quality scoring must degrade honestly when replay artifacts are missing",
        description=(
            "Static-only and missing-bag incidents must never receive "
            "a high replay-quality score. The scoring function is "
            "deterministic, evidence-derived, and rejects "
            "fabricated coverage. Score bands (90-100 / 70-89 / "
            "40-69 / 0-39) match the runbook."
        ),
        architecture_refs=(
            "docs/REPLAY_QUALITY_SCORING.md",
            "docs/REPLAY_GAP_ANALYSIS.md",
        ),
        implementation_refs=(
            "backend/app/replay_analytics/scoring.py",
        ),
        test_refs=(
            "backend/tests/test_replay_analytics.py::test_scoring_static_only_below_40",
            "backend/tests/test_replay_analytics.py::test_scoring_missing_bag_below_60",
            "backend/tests/test_replay_analytics.py::test_scoring_complete_replay_at_or_above_90",
            "backend/tests/test_replay_analytics.py::test_scoring_is_deterministic",
        ),
    ),
    Requirement(
        req_id="REQ-ANALYTICS-003",
        kind=RequirementKind.ANALYTICS,
        title="Cross-incident replay comparisons must preserve evidence-origin distinctions",
        description=(
            "The cross-incident comparator must carry the evidence "
            "origin (scenario-evidence / runtime-evidence / "
            "live-runtime / bag-backed / unknown) for every row so "
            "reviewers cannot confuse static-only with bag-backed "
            "evidence in a comparison report."
        ),
        architecture_refs=(
            "docs/REPLAY_ANALYTICS.md",
        ),
        implementation_refs=(
            "backend/app/replay_analytics/comparison.py",
        ),
        test_refs=(
            "backend/tests/test_replay_analytics.py::test_comparison_preserves_evidence_origin",
            "backend/tests/test_replay_analytics.py::test_comparison_orders_by_quality_score",
        ),
    ),
    Requirement(
        req_id="REQ-ANALYTICS-004",
        kind=RequirementKind.ANALYTICS,
        title="Operator review completion must never be inferred automatically",
        description=(
            "The review audit module recognises completion only via "
            "an explicit `review-audit.json` artefact with the "
            "operator's acknowledgement. If the file is absent the "
            "audit reports `not_started`; the analytics layer never "
            "promotes a missing acknowledgement to `completed`."
        ),
        architecture_refs=(
            "docs/REPLAY_REVIEW_AUDIT.md",
        ),
        implementation_refs=(
            "backend/app/replay_analytics/review_audit.py",
        ),
        test_refs=(
            "backend/tests/test_replay_analytics.py::test_review_audit_absent_metadata_is_not_started",
            "backend/tests/test_replay_analytics.py::test_review_audit_completed_requires_explicit_flag",
            "backend/tests/test_replay_analytics.py::test_review_audit_partial_when_some_steps_done",
        ),
    ),
    Requirement(
        req_id="REQ-ANALYTICS-005",
        kind=RequirementKind.ANALYTICS,
        title="Replay analytics reports must distinguish static-only, missing-bag, partial, and bag-backed incidents",
        description=(
            "The aggregate report and the index file must group "
            "incidents by replay execution status / evidence origin "
            "so a reviewer can see at a glance which incidents have "
            "live bag evidence and which are static-only. The trend "
            "tables never aggregate across origin classes without "
            "labelling the difference."
        ),
        architecture_refs=(
            "docs/REPLAY_ANALYTICS.md",
            "docs/REPLAY_ANALYTICS_INDEX.md",
        ),
        implementation_refs=(
            "backend/app/replay_analytics/reporting.py",
            "backend/app/replay_analytics/index.py",
        ),
        test_refs=(
            "backend/tests/test_replay_analytics.py::test_report_distribution_by_bag_status",
            "backend/tests/test_replay_analytics.py::test_index_filters_by_bag_status",
            "backend/tests/test_replay_analytics.py::test_index_filters_by_quality_score",
        ),
    ),
    Requirement(
        req_id="REQ-IMPACT-001",
        kind=RequirementKind.IMPACT,
        title="Source changes must be classified by impacted subsystem",
        description=(
            "Every changed file in a PR or working tree must be "
            "classified by subsystem (safety, mission, motion, "
            "replay, replay_analytics, runtime_validation, "
            "verification, ros_workspace, gazebo_simulation, docs, "
            "tests, ci, unknown). Unknown files are classified as "
            "`unknown` — never silently ignored."
        ),
        architecture_refs=(
            "docs/RELIABILITY_IMPACT_ANALYSIS.md",
            "docs/SOURCE_TO_EVIDENCE_TRACEABILITY.md",
        ),
        implementation_refs=(
            "backend/app/reliability_impact/subsystem_classifier.py",
            "backend/app/reliability_impact/git_changes.py",
        ),
        test_refs=(
            "backend/tests/test_reliability_impact.py::test_subsystem_classifier_safety_path",
            "backend/tests/test_reliability_impact.py::test_subsystem_classifier_replay_analytics_path",
            "backend/tests/test_reliability_impact.py::test_subsystem_classifier_unknown_path",
        ),
    ),
    Requirement(
        req_id="REQ-IMPACT-002",
        kind=RequirementKind.IMPACT,
        title="Impacted subsystems must map to requirements and evidence artifacts where possible",
        description=(
            "The requirement mapper resolves each impacted subsystem "
            "to the existing requirement IDs that cover it; the "
            "evidence mapper resolves each requirement to the tests "
            "and evidence artefacts that should be regenerated or "
            "inspected. Unmapped subsystems are reported as "
            "`partial` rather than silently dropped."
        ),
        architecture_refs=(
            "docs/SOURCE_TO_EVIDENCE_TRACEABILITY.md",
            "docs/TRACEABILITY_MATRIX.md",
        ),
        implementation_refs=(
            "backend/app/reliability_impact/requirement_mapper.py",
            "backend/app/reliability_impact/evidence_mapper.py",
        ),
        test_refs=(
            "backend/tests/test_reliability_impact.py::test_requirement_mapper_safety_to_req_safe",
            "backend/tests/test_reliability_impact.py::test_requirement_mapper_replay_analytics_to_req_analytics",
            "backend/tests/test_reliability_impact.py::test_evidence_mapper_safety_recommends_command_audit",
            "backend/tests/test_reliability_impact.py::test_requirement_mapper_unknown_is_unmapped",
        ),
    ),
    Requirement(
        req_id="REQ-IMPACT-003",
        kind=RequirementKind.IMPACT,
        title="Replay analytics deltas must be compared against an explicit baseline when available",
        description=(
            "The analytics delta engine compares the current "
            "replay-quality-index.json + replay-analytics-report.json "
            "against a baseline pinned under "
            "`reliability-baselines/`. Score drops, coverage / bag / "
            "review changes, new contradictions, and "
            "honesty violations are classified into "
            "{improvement, neutral, warning, regression, "
            "critical_regression}. A missing baseline is a warning, "
            "never a failure."
        ),
        architecture_refs=(
            "docs/RELIABILITY_IMPACT_ANALYSIS.md",
            "docs/CI_RELIABILITY_GATE.md",
        ),
        implementation_refs=(
            "backend/app/reliability_impact/analytics_delta.py",
            "backend/app/reliability_impact/baseline.py",
        ),
        test_refs=(
            "backend/tests/test_reliability_impact.py::test_analytics_delta_score_drop_warning",
            "backend/tests/test_reliability_impact.py::test_analytics_delta_score_drop_regression",
            "backend/tests/test_reliability_impact.py::test_analytics_delta_new_contradiction_critical",
            "backend/tests/test_reliability_impact.py::test_analytics_delta_missing_baseline_warning",
            "backend/tests/test_reliability_impact.py::test_analytics_delta_static_only_not_regression",
        ),
    ),
    Requirement(
        req_id="REQ-IMPACT-004",
        kind=RequirementKind.IMPACT,
        title="Critical replay or safety evidence regressions must be gateable in CI",
        description=(
            "The CI gate fails on critical regressions only: "
            "critical_regression analytics delta, safety / motion "
            "authority changes with missing required evidence, "
            "replay honesty violations, a failed traceability "
            "matrix, or removed static validation workflows. The "
            "gate never fails solely because live runtime evidence "
            "is missing on a github-hosted runner."
        ),
        architecture_refs=(
            "docs/CI_RELIABILITY_GATE.md",
        ),
        implementation_refs=(
            "backend/app/reliability_impact/ci_gate.py",
            "rover_ws/tools/reliability_impact_gate.py",
            ".github/workflows/reliability-impact.yml",
        ),
        test_refs=(
            "backend/tests/test_reliability_impact.py::test_gate_fails_on_critical_regression",
            "backend/tests/test_reliability_impact.py::test_gate_does_not_fail_on_missing_live_evidence",
            "backend/tests/test_reliability_impact.py::test_gate_warns_on_missing_baseline",
            "backend/tests/test_reliability_impact.py::test_gate_fails_on_static_validation_removal",
        ),
    ),
    Requirement(
        req_id="REQ-IMPACT-005",
        kind=RequirementKind.IMPACT,
        title="Reliability impact reports must distinguish warnings from blocking failures",
        description=(
            "Impact reports surface two outcome surfaces: the gate "
            "decision (passed / warning / failed / not_executed) "
            "and the risk assessment (none / low / moderate / high "
            "/ critical). Both are conservative; warnings never "
            "promote themselves to failures. Reports never treat "
            "missing live runtime evidence as failure in "
            "github-hosted CI."
        ),
        architecture_refs=(
            "docs/RELIABILITY_IMPACT_ANALYSIS.md",
            "docs/CI_RELIABILITY_GATE.md",
        ),
        implementation_refs=(
            "backend/app/reliability_impact/report.py",
            "backend/app/reliability_impact/risk_assessor.py",
        ),
        test_refs=(
            "backend/tests/test_reliability_impact.py::test_report_distinguishes_warning_from_failure",
            "backend/tests/test_reliability_impact.py::test_risk_assessor_safety_changes_high_risk_without_evidence",
            "backend/tests/test_reliability_impact.py::test_risk_assessor_docs_only_low_risk",
            "backend/tests/test_reliability_impact.py::test_risk_assessor_unknown_files_moderate",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-001",
        kind=RequirementKind.PROGRAMME,
        title="Longitudinal aggregation must load every available reliability artefact deterministically",
        description=(
            "The history loader must consume reliability-impact "
            "bundles, replay analytics reports, runtime qualification "
            "reports, replay review reports, and incident reports "
            "without failing the whole aggregation on a single "
            "malformed artefact. Malformed inputs become structured "
            "warnings; missing-history scenarios become "
            "``insufficient_history``, never regression."
        ),
        architecture_refs=(
            "docs/PROGRAMME_REVIEW.md",
            "docs/RELIABILITY_TREND_ANALYSIS.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/history_loader.py",
            "backend/app/programme_review/aggregation.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_history_loader_handles_missing_dir",
            "backend/tests/test_programme_review.py::test_history_loader_isolates_malformed_report",
            "backend/tests/test_programme_review.py::test_history_loader_orders_by_generated_at",
            "backend/tests/test_programme_review.py::test_history_loader_detects_duplicates",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-002",
        kind=RequirementKind.PROGRAMME,
        title="Replay-quality trends must be deterministic and labelled when history is insufficient",
        description=(
            "The trend analyser classifies replay-quality history "
            "into {improving, stable, degrading, volatile, "
            "insufficient_history}. Classification is deterministic "
            "given the same history sequence; one-sample histories "
            "always return ``insufficient_history``."
        ),
        architecture_refs=(
            "docs/RELIABILITY_TREND_ANALYSIS.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/trend_analysis.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_trend_improving",
            "backend/tests/test_programme_review.py::test_trend_degrading",
            "backend/tests/test_programme_review.py::test_trend_stable",
            "backend/tests/test_programme_review.py::test_trend_volatile",
            "backend/tests/test_programme_review.py::test_trend_insufficient_history",
            "backend/tests/test_programme_review.py::test_trend_is_deterministic",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-003",
        kind=RequirementKind.PROGRAMME,
        title="Reliability drift must be classified deterministically with documented rules",
        description=(
            "Drift detectors map history into one of {informational, "
            "warning, regression, critical_regression}. Rules are "
            "documented in `docs/RELIABILITY_TREND_ANALYSIS.md`; the "
            "detector never invents drift when history is missing."
        ),
        architecture_refs=(
            "docs/RELIABILITY_TREND_ANALYSIS.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/drift_detection.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_drift_replay_score_critical",
            "backend/tests/test_programme_review.py::test_drift_increasing_missing_bag",
            "backend/tests/test_programme_review.py::test_drift_increasing_static_only",
            "backend/tests/test_programme_review.py::test_drift_growing_unknown_file_count",
            "backend/tests/test_programme_review.py::test_drift_insufficient_history_is_informational",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-004",
        kind=RequirementKind.PROGRAMME,
        title="Governance health must roll up evidence, replay, CI, traceability, runtime, and review discipline",
        description=(
            "Six discipline categories aggregate into a single "
            "programme-level health: {strong, acceptable, weak, "
            "concerning, critical}. Every category records the "
            "triggering artefacts so the report shows exactly what "
            "produced the rating."
        ),
        architecture_refs=(
            "docs/GOVERNANCE_HEALTH_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/governance_health.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_governance_strong_when_all_disciplines_pass",
            "backend/tests/test_programme_review.py::test_governance_concerning_on_repeat_failures",
            "backend/tests/test_programme_review.py::test_governance_records_triggering_artifacts",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-005",
        kind=RequirementKind.PROGRAMME,
        title="Evidence freshness must be reported, not enforced via wall-clock",
        description=(
            "Freshness compares each artefact's recorded "
            "``generated_at_utc`` against an explicit reference time "
            "supplied by the caller (CI passes UTC ``now``; tests "
            "supply fixture timestamps). Wall-clock fetches inside "
            "the layer are forbidden so tests are not flaky."
        ),
        architecture_refs=(
            "docs/EVIDENCE_FRESHNESS_POLICY.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/freshness.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_freshness_fresh_when_recent",
            "backend/tests/test_programme_review.py::test_freshness_stale_when_older_than_threshold",
            "backend/tests/test_programme_review.py::test_freshness_unknown_when_no_timestamp",
            "backend/tests/test_programme_review.py::test_freshness_uses_supplied_now",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-006",
        kind=RequirementKind.PROGRAMME,
        title="Subsystem risk must aggregate frequency, severity, and recurrence",
        description=(
            "The aggregator counts how often each subsystem appeared "
            "across reliability-impact bundles, the severity "
            "distribution, repeat regression count, gate failure "
            "count, and unresolved warning count. The report ranks "
            "subsystems but never claims causality."
        ),
        architecture_refs=(
            "docs/SUBSYSTEM_RISK_AGGREGATION.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/subsystem_risk.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_subsystem_risk_counts_frequency",
            "backend/tests/test_programme_review.py::test_subsystem_risk_records_repeat_regressions",
            "backend/tests/test_programme_review.py::test_subsystem_risk_ranks_by_severity",
            "backend/tests/test_programme_review.py::test_subsystem_risk_never_infers_causality",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-007",
        kind=RequirementKind.PROGRAMME,
        title="Coverage evolution must preserve evidence origin labels through aggregation",
        description=(
            "Bag status / evidence origin distributions tracked over "
            "time must label mixed-origin samples explicitly. A "
            "static-only baseline never silently combines with "
            "bag-backed history into a single trend line."
        ),
        architecture_refs=(
            "docs/PROGRAMME_REVIEW.md",
            "docs/RELIABILITY_TREND_ANALYSIS.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/coverage_evolution.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_coverage_evolution_preserves_origin",
            "backend/tests/test_programme_review.py::test_coverage_evolution_labels_mixed_origin",
            "backend/tests/test_programme_review.py::test_coverage_evolution_static_only_stays_static_only",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-008",
        kind=RequirementKind.PROGRAMME,
        title="CI gate history must aggregate pass / warning / failure counts and gate volatility",
        description=(
            "The gate-history module records gate outcomes across "
            "every reliability-impact bundle in the history window, "
            "computes a volatility label (steady / oscillating / "
            "regressing / improving), and reports the most recent "
            "transition. The module never fabricates durations when "
            "timestamps are absent."
        ),
        architecture_refs=(
            "docs/PROGRAMME_REVIEW.md",
            "docs/CI_RELIABILITY_GATE.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/gate_history.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_gate_history_counts_outcomes",
            "backend/tests/test_programme_review.py::test_gate_history_volatility_steady",
            "backend/tests/test_programme_review.py::test_gate_history_volatility_oscillating",
            "backend/tests/test_programme_review.py::test_gate_history_unknown_when_no_data",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-009",
        kind=RequirementKind.PROGRAMME,
        title="Programme review reports must distinguish missing history from regression",
        description=(
            "When history is partial the report says so explicitly: "
            "``insufficient_history`` for trends, ``unknown`` for "
            "freshness, ``unknown`` for gate volatility. None of "
            "these states fail CI. Mixed-origin aggregates always "
            "label the origin mix."
        ),
        architecture_refs=(
            "docs/PROGRAMME_REVIEW.md",
            "docs/GOVERNANCE_HEALTH_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/programme_review/reporting.py",
            "backend/app/programme_review/aggregation.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_report_labels_insufficient_history",
            "backend/tests/test_programme_review.py::test_report_labels_mixed_origin",
            "backend/tests/test_programme_review.py::test_report_does_not_fail_on_partial_history",
        ),
    ),
    Requirement(
        req_id="REQ-PROGRAMME-010",
        kind=RequirementKind.PROGRAMME,
        title="Programme review CI workflow must not fail on missing live runtime evidence",
        description=(
            "The github-hosted CI workflow runs the programme review "
            "tools on every dispatch and never fails solely because "
            "live runtime evidence is missing on a github-hosted "
            "runner. Failures are reserved for documented critical "
            "governance conditions."
        ),
        architecture_refs=(
            "docs/PROGRAMME_REVIEW.md",
            "docs/CI_RELIABILITY_GATE.md",
        ),
        implementation_refs=(
            ".github/workflows/programme-review.yml",
            "rover_ws/tools/generate_programme_review.py",
        ),
        test_refs=(
            "backend/tests/test_programme_review.py::test_programme_workflow_is_github_hosted",
            "backend/tests/test_programme_review.py::test_programme_workflow_supports_dispatch",
            "backend/tests/test_programme_review.py::test_programme_workflow_uploads_artifacts",
        ),
    ),
)


class RequirementsRegistry:
    """Lightweight wrapper providing query helpers."""

    def __init__(self, requirements: tuple[Requirement, ...] = REQUIREMENTS) -> None:
        self._reqs: dict[str, Requirement] = {r.req_id: r for r in requirements}
        if len(self._reqs) != len(requirements):
            raise ValueError("duplicate requirement IDs in registry")

    def __iter__(self):
        return iter(self._reqs.values())

    def __len__(self) -> int:
        return len(self._reqs)

    def __contains__(self, req_id: str) -> bool:
        return req_id in self._reqs

    def get(self, req_id: str) -> Requirement:
        if req_id not in self._reqs:
            raise KeyError(f"unknown requirement: {req_id!r}")
        return self._reqs[req_id]

    def by_kind(self, kind: RequirementKind) -> tuple[Requirement, ...]:
        return tuple(r for r in self._reqs.values() if r.kind == kind)

    def by_scenario(self, scenario_id: str) -> tuple[Requirement, ...]:
        return tuple(r for r in self._reqs.values() if scenario_id in r.scenario_refs)

    def to_dict(self) -> dict[str, Any]:
        return {"requirements": [r.to_dict() for r in self._reqs.values()]}


def requirement_by_id(req_id: str) -> Requirement:
    """Module-level convenience accessor."""

    return RequirementsRegistry().get(req_id)

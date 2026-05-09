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

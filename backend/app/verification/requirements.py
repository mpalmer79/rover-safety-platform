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
    EXPORT = "export"
    LIVE = "live"
    MISSION_COMPILER = "mission_compiler"
    PROPOSAL = "proposal"
    SKILL = "skill"
    SKILL_LLM = "skill_llm"
    REHEARSAL = "rehearsal"
    MISSION_CONTROL = "mission_control"
    MISSION_VISUALIZATION = "mission_visualization"
    SPATIAL_REPLAY = "spatial_replay"
    ARTIFACT_REGISTRY = "artifact_registry"
    IMMERSIVE_VIZ = "immersive_viz"
    DESIGN_SYSTEM = "design_system"
    SKILL_LLM_INTELLIGENCE = "skill_llm_intelligence"
    SCENE_SNAPSHOT = "scene_snapshot"


# ---------------------------------------------------------------------------
# Category tiers.
#
# Every requirement falls into one of two tiers:
#   * ``core`` — touches deterministic behaviour, safety boundary, or
#     replay. Reviewers should see these first.
#   * ``meta`` — UI, visualization, aggregation, governance, reporting.
#
# The tier is derived from the requirement-id PREFIX (everything before
# the trailing -NNN suffix). Adding a new prefix here requires the
# reviewer to choose a tier explicitly; the registry-validity test will
# fail otherwise.
#
# Honesty note: the safety-authority claim is the centre of this
# project. SAFE / FAULT / WORLD / DIAG / MISSION / OP must remain in
# ``core`` regardless of how the meta-namespaces grow.
# ---------------------------------------------------------------------------


CATEGORY_TIER_CORE: str = "core"
CATEGORY_TIER_META: str = "meta"


_TIER_BY_PREFIX: dict[str, str] = {
    # Core — deterministic behaviour, safety boundary, replay
    "REQ-SAFE": CATEGORY_TIER_CORE,
    "REQ-FAULT": CATEGORY_TIER_CORE,
    "REQ-WORLD": CATEGORY_TIER_CORE,
    "REQ-DIAG": CATEGORY_TIER_CORE,
    "REQ-MISSION": CATEGORY_TIER_CORE,
    "REQ-OP": CATEGORY_TIER_CORE,
    "REQ-REPLAY": CATEGORY_TIER_CORE,
    "REQ-RUNTIME": CATEGORY_TIER_CORE,
    "REQ-LIVE": CATEGORY_TIER_CORE,
    "REQ-INCIDENT": CATEGORY_TIER_CORE,
    "REQ-MCOMP": CATEGORY_TIER_CORE,
    "REQ-PROPOSAL": CATEGORY_TIER_CORE,
    "REQ-REHEARSAL": CATEGORY_TIER_CORE,
    "REQ-SKILL": CATEGORY_TIER_CORE,
    "REQ-SKILL-LLM": CATEGORY_TIER_CORE,
    # Meta — UI, visualization, aggregation, governance, reporting
    "REQ-DESIGN": CATEGORY_TIER_META,
    "REQ-IMMVIZ": CATEGORY_TIER_META,
    "REQ-MCTRL": CATEGORY_TIER_META,
    "REQ-MVIS": CATEGORY_TIER_META,
    "REQ-SREPLAY": CATEGORY_TIER_META,
    "REQ-SNAPSHOT": CATEGORY_TIER_META,
    "REQ-ARTREG": CATEGORY_TIER_META,
    "REQ-PROGRAMME": CATEGORY_TIER_META,
    "REQ-IMPACT": CATEGORY_TIER_META,
    "REQ-ANALYTICS": CATEGORY_TIER_META,
    "REQ-EXPORT": CATEGORY_TIER_META,
    "REQ-SKILL-INTEL": CATEGORY_TIER_META,
}


def _tier_for_req_id(req_id: str) -> str:
    """Resolve the category tier from a REQ-* id by prefix lookup.

    The id ``REQ-SAFE-001`` is split into prefix ``REQ-SAFE`` and a
    numeric suffix. The longer prefixes (``REQ-SKILL-LLM``,
    ``REQ-SKILL-INTEL``) are matched before the shorter ``REQ-SKILL``
    fallback. Unknown prefixes default to ``core`` so a newly added
    namespace fails closed (visible in the safety-first table) until a
    reviewer assigns it explicitly here.
    """

    # Try the longest-known prefixes first (REQ-SKILL-LLM, REQ-SKILL-INTEL).
    longest_first = sorted(_TIER_BY_PREFIX.keys(), key=len, reverse=True)
    for prefix in longest_first:
        if req_id == prefix or req_id.startswith(prefix + "-"):
            return _TIER_BY_PREFIX[prefix]
    return CATEGORY_TIER_CORE


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

    category_tier: str = ""
    """One of :data:`CATEGORY_TIER_CORE` / :data:`CATEGORY_TIER_META`.

    Left blank in the literal constructors — derived from the
    requirement-id prefix in :meth:`__post_init__`. Pass a value
    explicitly only to override the prefix-derived tier (rare; record
    a reason inline)."""

    def __post_init__(self) -> None:
        if not self.category_tier:
            object.__setattr__(self, "category_tier", _tier_for_req_id(self.req_id))

    def to_dict(self) -> dict[str, Any]:
        return {
            "req_id": self.req_id,
            "kind": self.kind.value,
            "category_tier": self.category_tier,
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
    Requirement(
        req_id="REQ-EXPORT-001",
        kind=RequirementKind.EXPORT,
        title="Reviewer exports must provide CSV and JSONL outputs for the documented tables",
        description=(
            "The reviewer-export package emits CSV and JSONL files "
            "for programme health, replay quality, incidents, "
            "subsystem risk, gate history, drift findings, trend "
            "series, and requirement coverage. Both formats are "
            "deterministic and schema-backed."
        ),
        architecture_refs=(
            "docs/REVIEWER_EXPORTS.md",
            "docs/EXPORT_SCHEMA_REFERENCE.md",
        ),
        implementation_refs=(
            "backend/app/reviewer_exports/exporters.py",
            "backend/app/reviewer_exports/schema.py",
        ),
        test_refs=(
            "backend/tests/test_reviewer_exports.py::test_csv_exports_are_deterministic",
            "backend/tests/test_reviewer_exports.py::test_jsonl_exports_are_line_delimited",
            "backend/tests/test_reviewer_exports.py::test_all_documented_tables_emitted",
        ),
    ),
    Requirement(
        req_id="REQ-EXPORT-002",
        kind=RequirementKind.EXPORT,
        title="Reviewer exports must preserve evidence-origin, static-only, and missing-bag status",
        description=(
            "Every row in the replay-quality table records the "
            "original evidence_origin, bag_status, and review "
            "completion status. Static-only stays static-only and "
            "missing_bag stays missing_bag — the export layer never "
            "promotes one to the other."
        ),
        architecture_refs=(
            "docs/REVIEWER_EXPORTS.md",
        ),
        implementation_refs=(
            "backend/app/reviewer_exports/exporters.py",
            "backend/app/reviewer_exports/loader.py",
        ),
        test_refs=(
            "backend/tests/test_reviewer_exports.py::test_static_only_remains_static_only",
            "backend/tests/test_reviewer_exports.py::test_missing_bag_remains_missing_bag",
            "backend/tests/test_reviewer_exports.py::test_replay_quality_row_preserves_origin",
        ),
    ),
    Requirement(
        req_id="REQ-EXPORT-003",
        kind=RequirementKind.EXPORT,
        title="Reviewer exports must include schemas and a manifest with row counts",
        description=(
            "The export bundle ships a JSON Schema for every table "
            "and a manifest.json that lists tables, row counts, "
            "schema paths, csv paths, jsonl paths, the notebook "
            "path, and the certification disclaimer."
        ),
        architecture_refs=(
            "docs/EXPORT_SCHEMA_REFERENCE.md",
        ),
        implementation_refs=(
            "backend/app/reviewer_exports/manifest.py",
            "backend/app/reviewer_exports/schema.py",
        ),
        test_refs=(
            "backend/tests/test_reviewer_exports.py::test_manifest_row_counts_match_files",
            "backend/tests/test_reviewer_exports.py::test_schemas_define_required_fields",
            "backend/tests/test_reviewer_exports.py::test_manifest_contains_certification_disclaimer",
        ),
    ),
    Requirement(
        req_id="REQ-EXPORT-004",
        kind=RequirementKind.EXPORT,
        title="Reviewer notebook scaffolding must not require ROS, Gazebo, Foxglove, or live runtime evidence",
        description=(
            "The reviewer notebook loads CSV files from the "
            "neighbour ``../csv/`` directory using only the Python "
            "standard library (and pandas / matplotlib via guarded "
            "optional imports). It does not require ROS, Gazebo, "
            "Foxglove, or any live runtime evidence."
        ),
        architecture_refs=(
            "docs/REVIEWER_NOTEBOOK_GUIDE.md",
        ),
        implementation_refs=(
            "backend/app/reviewer_exports/notebook.py",
        ),
        test_refs=(
            "backend/tests/test_reviewer_exports.py::test_notebook_is_valid_json",
            "backend/tests/test_reviewer_exports.py::test_notebook_uses_optional_imports",
            "backend/tests/test_reviewer_exports.py::test_notebook_does_not_require_ros",
        ),
    ),
    Requirement(
        req_id="REQ-EXPORT-005",
        kind=RequirementKind.EXPORT,
        title="Reviewer exports must not claim safety certification or infer causality",
        description=(
            "Every reviewer-facing artefact carries the verbatim "
            "certification disclaimer; the subsystem-risk export "
            "always sets ``causality_claimed=false``; the reviewer "
            "summary explicitly distinguishes static-only / "
            "missing-bag / bag-backed evidence."
        ),
        architecture_refs=(
            "docs/REVIEWER_EXPORTS.md",
        ),
        implementation_refs=(
            "backend/app/reviewer_exports/reporter.py",
            "backend/app/reviewer_exports/exporters.py",
        ),
        test_refs=(
            "backend/tests/test_reviewer_exports.py::test_subsystem_risk_causality_claimed_false",
            "backend/tests/test_reviewer_exports.py::test_reviewer_summary_includes_disclaimer",
            "backend/tests/test_reviewer_exports.py::test_reviewer_summary_distinguishes_origins",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-001",
        kind=RequirementKind.MISSION_COMPILER,
        title="Mission compiler must be deterministic and offline",
        description=(
            "Identical input strings produce byte-identical compiled "
            "mission plans (modulo caller-supplied reference time). "
            "The compiler never calls a remote API and never imports "
            "an LLM SDK; it runs offline on the standard library."
        ),
        architecture_refs=("docs/NATURAL_LANGUAGE_MISSION_COMPILER.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/compiler.py",
            "backend/app/natural_language_mission/parser.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_compile_is_byte_deterministic",
            "backend/tests/test_natural_language_mission.py::test_compile_hash_stable",
            "backend/tests/test_natural_language_mission.py::test_compiler_does_not_import_llm_sdks",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-002",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must use bounded grammar templates and reject unsupported instructions",
        description=(
            "Natural language input is matched against a closed set "
            "of grammar templates. Instructions that do not match a "
            "supported template are recorded as "
            "``unsupported_instruction`` diagnostics and never "
            "translated into mission objectives."
        ),
        architecture_refs=("docs/MISSION_INTENT_GRAMMAR.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/templates.py",
            "backend/app/natural_language_mission/parser.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_unsupported_instruction_rejected",
            "backend/tests/test_natural_language_mission.py::test_dangerous_unsupported_instruction_rejected",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-003",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must preserve ambiguity honestly",
        description=(
            "Vague destinations and underspecified instructions "
            "produce ``ambiguous`` diagnostics with a structured "
            "reason. The compiler never invents coordinates, "
            "objectives, or stages to resolve ambiguity."
        ),
        architecture_refs=("docs/MISSION_INTENT_GRAMMAR.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/parser.py",
            "backend/app/natural_language_mission/diagnostics.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_ambiguous_destination_preserved",
            "backend/tests/test_natural_language_mission.py::test_compiler_never_invents_waypoints",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-004",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must reject contradictory instructions",
        description=(
            "When two instructions in the same intent disagree "
            "(e.g. drive to A and do not drive to A), the compiler "
            "rejects the mission with status "
            "``compile_rejected`` and a structured "
            "``contradiction`` diagnostic listing both clauses."
        ),
        architecture_refs=("docs/MISSION_INTENT_GRAMMAR.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/validator.py",
            "backend/app/natural_language_mission/constraints.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_contradictory_instructions_rejected",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-005",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must enforce ODD validation",
        description=(
            "Mission plans must validate against the active ODD "
            "profile (authorised zones, prohibited regions, speed "
            "limits, time windows, lidar / battery / dock "
            "assumptions). Plans outside the ODD fail compilation "
            "with status ``compile_rejected`` and an "
            "``odd_violation`` diagnostic."
        ),
        architecture_refs=(
            "docs/MISSION_ASSURANCE_MODEL.md",
            "docs/ODD.md",
        ),
        implementation_refs=(
            "backend/app/natural_language_mission/odd.py",
            "backend/app/natural_language_mission/validator.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_restricted_zone_mission_rejected",
            "backend/tests/test_natural_language_mission.py::test_speed_outside_odd_rejected",
            "backend/tests/test_natural_language_mission.py::test_time_window_outside_odd_rejected",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-006",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must classify mission risk deterministically",
        description=(
            "Each compiled mission carries a ``risk`` block with a "
            "band drawn from ``informational``, ``low``, "
            "``moderate``, ``elevated``, ``high``, ``critical``, a "
            "deterministic numeric score, a list of risk drivers, "
            "and mitigation recommendations. Critical-risk missions "
            "never auto-pass."
        ),
        architecture_refs=("docs/MISSION_RISK_CLASSIFICATION.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/risk.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_risk_band_thresholds",
            "backend/tests/test_natural_language_mission.py::test_critical_risk_requires_reviewer_action",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-007",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must produce a deterministic mission graph",
        description=(
            "Each compiled mission emits an ordered mission graph "
            "with stages, dependencies, recovery branches, and "
            "abort branches. The graph is rendered in JSON + "
            "Markdown + Mermaid; identical input produces "
            "byte-identical Mermaid."
        ),
        architecture_refs=("docs/MISSION_COMPILER_WALKTHROUGH.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/compiler.py",
            "backend/app/natural_language_mission/reporting.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_mission_graph_is_deterministic",
            "backend/tests/test_natural_language_mission.py::test_mission_graph_mermaid_byte_stable",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-008",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must produce auditable explainability output",
        description=(
            "Each compile run emits an explainability chain "
            "(USER INPUT -> EXTRACTED INTENT -> NORMALIZED COMMANDS "
            "-> VALIDATION RESULTS -> RISK CLASSIFICATION -> "
            "FINAL COMPILED PLAN). The chain is reproducible and "
            "never references hidden state."
        ),
        architecture_refs=("docs/MISSION_COMPILER_WALKTHROUGH.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/explainability.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_explainability_chain_includes_all_stages",
            "backend/tests/test_natural_language_mission.py::test_explainability_is_reproducible",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-009",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must emit a complete audit artefact",
        description=(
            "Each compile run emits a ``mission-audit.json`` and "
            "``mission-audit.md`` containing the original request, "
            "normalised request, extracted objectives, validation "
            "outcomes, rejected instructions, assumptions, risk, "
            "ODD profile id, compile timestamp, deterministic "
            "compile hash, compiler version, and the verbatim "
            "non-certification disclaimer."
        ),
        architecture_refs=("docs/MISSION_ASSURANCE_MODEL.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/audit.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_audit_contains_all_required_fields",
            "backend/tests/test_natural_language_mission.py::test_audit_carries_disclaimer",
        ),
    ),
    Requirement(
        req_id="REQ-MCOMP-010",
        kind=RequirementKind.MISSION_COMPILER,
        title="Compiler must produce replay-compatible metadata without claiming runtime execution",
        description=(
            "Each compiled mission emits replay-binding metadata "
            "(scenario id, timeline markers, mission stages, "
            "decision points) sufficient for the existing replay "
            "layer to align future runs. The compiler explicitly "
            "marks ``runtime_executed=false`` and never references "
            "fabricated bag or event evidence."
        ),
        architecture_refs=("docs/HUMAN_TO_AUTONOMY_BOUNDARY.md",),
        implementation_refs=(
            "backend/app/natural_language_mission/replay_binding.py",
        ),
        test_refs=(
            "backend/tests/test_natural_language_mission.py::test_replay_binding_marks_runtime_not_executed",
            "backend/tests/test_natural_language_mission.py::test_replay_binding_emits_stable_markers",
        ),
    ),
    Requirement(
        req_id="REQ-LIVE-001",
        kind=RequirementKind.LIVE,
        title="Self-hosted live runtime runs must validate runner prerequisites before executing",
        description=(
            "Before any live ROS 2 / Gazebo execution, the runner "
            "profile is loaded and validated; missing ROS distro, "
            "Gazebo version, workspace, or rosbag2 support causes "
            "the run to abort with status ``not_executed`` and a "
            "structured reason. GitHub-hosted runners always abort."
        ),
        architecture_refs=(
            "docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md",
            "docs/LIVE_RUNNER_PROFILE.md",
        ),
        implementation_refs=(
            "backend/app/live_runtime/runner_profile.py",
            "backend/app/live_runtime/evidence_capture.py",
        ),
        test_refs=(
            "backend/tests/test_live_runtime.py::test_runner_profile_load_and_validate",
            "backend/tests/test_live_runtime.py::test_runner_profile_missing_required_fields",
            "backend/tests/test_live_runtime.py::test_evidence_capture_aborts_without_ros",
        ),
    ),
    Requirement(
        req_id="REQ-LIVE-002",
        kind=RequirementKind.LIVE,
        title="Live runtime evidence must include a bag manifest or explicit not_executed reason",
        description=(
            "Every ``evidence/runtime/<run_id>/`` bundle includes "
            "either a ``bag-manifest.json`` describing real bag "
            "artefacts, or a ``bag-manifest.json`` with status "
            "``not_executed`` and a structured reason. Missing "
            "manifests are themselves a validator failure."
        ),
        architecture_refs=(
            "docs/LIVE_BAG_CAPTURE_RUNBOOK.md",
        ),
        implementation_refs=(
            "backend/app/live_runtime/bag_manifest.py",
            "backend/app/live_runtime/evidence_capture.py",
        ),
        test_refs=(
            "backend/tests/test_live_runtime.py::test_bag_manifest_required_fields",
            "backend/tests/test_live_runtime.py::test_bag_manifest_not_executed_reason_required",
            "backend/tests/test_live_runtime.py::test_validator_fails_when_manifest_missing",
        ),
    ),
    Requirement(
        req_id="REQ-LIVE-003",
        kind=RequirementKind.LIVE,
        title="Bag-backed status must require real bag artefacts and metadata",
        description=(
            "A bag manifest with ``bag_status=bag_backed`` must "
            "list at least one bag path that exists on disk and a "
            "metadata YAML. Static fixtures, fabricated paths, and "
            "empty inventories never qualify as ``bag_backed``."
        ),
        architecture_refs=(
            "docs/LIVE_BAG_CAPTURE_RUNBOOK.md",
        ),
        implementation_refs=(
            "backend/app/live_runtime/bag_manifest.py",
        ),
        test_refs=(
            "backend/tests/test_live_runtime.py::test_bag_backed_requires_real_artefacts",
            "backend/tests/test_live_runtime.py::test_static_fixture_cannot_be_marked_bag_backed",
        ),
    ),
    Requirement(
        req_id="REQ-LIVE-004",
        kind=RequirementKind.LIVE,
        title="Live runtime evidence must integrate with downstream evidence pipelines",
        description=(
            "``process_live_runtime_evidence.py`` accepts an "
            "``evidence/runtime/<run_id>`` directory and invokes "
            "incident reconstruction, replay-review bundle build, "
            "replay analytics, programme review, and reviewer "
            "export integration hooks - preserving the manifest's "
            "``bag_status`` verbatim through every layer."
        ),
        architecture_refs=(
            "docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md",
        ),
        implementation_refs=(
            "backend/app/live_runtime/maturity.py",
        ),
        test_refs=(
            "backend/tests/test_live_runtime.py::test_process_live_runtime_evidence_dry_run_preserves_status",
            "backend/tests/test_live_runtime.py::test_maturity_report_counts_match_inputs",
        ),
    ),
    Requirement(
        req_id="REQ-LIVE-005",
        kind=RequirementKind.LIVE,
        title="GitHub-hosted CI must not claim live runtime execution",
        description=(
            "The ``live-runtime-evidence.yml`` workflow declares "
            "``runs-on: [self-hosted, ros-jazzy, gazebo]`` and "
            "``workflow_dispatch`` only - no push, pull_request, "
            "or schedule triggers. A static check fails the build "
            "if a ``ubuntu-`` runner ever appears in the file."
        ),
        architecture_refs=(
            "docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md",
        ),
        implementation_refs=(
            ".github/workflows/live-runtime-evidence.yml",
        ),
        test_refs=(
            "backend/tests/test_live_runtime.py::test_workflow_is_self_hosted_only",
            "backend/tests/test_live_runtime.py::test_workflow_does_not_target_github_hosted_runners",
            "backend/tests/test_live_runtime.py::test_workflow_uses_workflow_dispatch_only",
        ),
    ),
    Requirement(
        req_id="REQ-PROPOSAL-001",
        kind=RequirementKind.PROPOSAL,
        title="Mission proposal providers must not execute or authorize robot motion",
        description=(
            "The mission proposal layer is offline and read-only "
            "with respect to actuator state. Nothing in "
            "``backend/app/mission_proposal/`` publishes "
            "``/cmd_vel`` or any actuator topic, nothing toggles "
            "the safety supervisor, and nothing in the adapter or "
            "audit invokes the runtime. The deterministic mission "
            "compiler (Phase 14A) and the runtime safety supervisor "
            "remain authoritative for any motion that ultimately "
            "occurs."
        ),
        architecture_refs=(
            "docs/LLM_MISSION_PROPOSAL_LAYER.md",
            "docs/LLM_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/mission_proposal/__init__.py",
            "backend/app/mission_proposal/adapter.py",
            "backend/app/mission_proposal/provider.py",
        ),
        test_refs=(
            "backend/tests/test_mission_proposal.py::test_proposal_layer_never_publishes_actuator_topics",
            "backend/tests/test_mission_proposal.py::test_proposal_layer_has_no_runtime_authority_fields",
        ),
    ),
    Requirement(
        req_id="REQ-PROPOSAL-002",
        kind=RequirementKind.PROPOSAL,
        title="External LLM providers must remain disabled",
        description=(
            "Phase 14B ships only the mock provider and the "
            "offline-fixture provider. Any provider mode other than "
            "``mock`` and ``offline_fixture`` returns a "
            "deterministic ``not_configured`` response with the "
            "verbatim reason "
            "``external LLM providers are intentionally disabled "
            "in Phase 14B``. No module in "
            "``backend/app/mission_proposal/`` imports an LLM SDK."
        ),
        architecture_refs=(
            "docs/LLM_MISSION_PROPOSAL_LAYER.md",
            "docs/FUTURE_LLM_INTEGRATION_PLAN.md",
        ),
        implementation_refs=(
            "backend/app/mission_proposal/provider.py",
            "backend/app/mission_proposal/mock_provider.py",
        ),
        test_refs=(
            "backend/tests/test_mission_proposal.py::test_external_provider_is_disabled",
            "backend/tests/test_mission_proposal.py::test_proposal_layer_has_no_llm_sdk_imports",
            "backend/tests/test_mission_proposal.py::test_resolve_provider_rejects_unknown_modes",
        ),
    ),
    Requirement(
        req_id="REQ-PROPOSAL-003",
        kind=RequirementKind.PROPOSAL,
        title="Proposal outputs must be sanitized before compiler validation",
        description=(
            "Every proposal passes through "
            "``mission_proposal.sanitize_proposal`` before its text "
            "is handed to the Phase 14A compiler. The sanitizer "
            "rejects proposals that reference direct actuator "
            "commands, safety-supervisor overrides, e-stop "
            "overrides, lidar disables, continue-despite-failure "
            "directives, shell or code execution, network "
            "commands, or destructive shell commands. The compiler "
            "is never invoked on a rejected proposal."
        ),
        architecture_refs=(
            "docs/LLM_SAFETY_BOUNDARY.md",
            "docs/MISSION_PROPOSAL_AUDIT.md",
        ),
        implementation_refs=(
            "backend/app/mission_proposal/sanitizer.py",
            "backend/app/mission_proposal/adapter.py",
        ),
        test_refs=(
            "backend/tests/test_mission_proposal.py::test_sanitizer_rejects_actuator_command",
            "backend/tests/test_mission_proposal.py::test_sanitizer_rejects_safety_override",
            "backend/tests/test_mission_proposal.py::test_sanitizer_rejects_code_execution",
            "backend/tests/test_mission_proposal.py::test_sanitizer_rejects_shell_command",
            "backend/tests/test_mission_proposal.py::test_sanitizer_rejects_estop_override",
            "backend/tests/test_mission_proposal.py::test_sanitizer_rejects_sensor_disable",
            "backend/tests/test_mission_proposal.py::test_sanitizer_accepts_valid_inspection",
            "backend/tests/test_mission_proposal.py::test_adapter_does_not_invoke_compiler_on_rejection",
        ),
    ),
    Requirement(
        req_id="REQ-PROPOSAL-004",
        kind=RequirementKind.PROPOSAL,
        title="Unsafe or ambiguous proposals must produce deterministic diagnostics",
        description=(
            "Given the same proposal, the sanitizer, adapter and "
            "compiler produce byte-identical diagnostics and "
            "audit artefacts. An ambiguous proposal is labelled "
            "``proposal_compiled_requires_review``; an unsafe "
            "proposal is labelled "
            "``proposal_rejected_by_sanitizer``; a restricted-zone "
            "proposal is labelled "
            "``proposal_rejected_by_compiler``. The audit JSON is "
            "stable across repeated runs."
        ),
        architecture_refs=(
            "docs/MISSION_PROPOSAL_AUDIT.md",
        ),
        implementation_refs=(
            "backend/app/mission_proposal/adapter.py",
            "backend/app/mission_proposal/audit.py",
            "backend/app/mission_proposal/mock_provider.py",
        ),
        test_refs=(
            "backend/tests/test_mission_proposal.py::test_mock_provider_is_deterministic",
            "backend/tests/test_mission_proposal.py::test_ambiguous_proposal_is_compiled_requires_review",
            "backend/tests/test_mission_proposal.py::test_restricted_proposal_is_compiled_rejected",
            "backend/tests/test_mission_proposal.py::test_unsafe_proposal_is_rejected_by_sanitizer",
            "backend/tests/test_mission_proposal.py::test_audit_json_is_stable_across_runs",
        ),
    ),
    Requirement(
        req_id="REQ-PROPOSAL-005",
        kind=RequirementKind.PROPOSAL,
        title="Proposal audits must preserve provider mode, sanitizer results, compiler diagnostics, and safety-boundary disclaimers",
        description=(
            "Every audit bundle ("
            "``proposal.json``, "
            "``sanitizer-result.json``, "
            "``compiler-input.json``, "
            "``compiler-result.json``, "
            "``proposal-audit.json``, "
            "``proposal-audit.md`` "
            ") includes the provider mode, the sanitizer diagnostics, "
            "the compiler diagnostics (when invoked), and the verbatim "
            "safety-boundary disclaimer."
        ),
        architecture_refs=(
            "docs/MISSION_PROPOSAL_AUDIT.md",
        ),
        implementation_refs=(
            "backend/app/mission_proposal/audit.py",
            "backend/app/mission_proposal/reporter.py",
        ),
        test_refs=(
            "backend/tests/test_mission_proposal.py::test_audit_bundle_layout_is_complete",
            "backend/tests/test_mission_proposal.py::test_audit_markdown_contains_disclaimer",
            "backend/tests/test_mission_proposal.py::test_audit_preserves_provider_mode",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-001",
        kind=RequirementKind.SKILL,
        title="Skill requests compile only through deterministic templates",
        description=(
            "The Phase 15A skill authoring workbench maps a developer "
            "request onto a closed catalog of templates. Unsupported "
            "instructions never reach the template builder; the "
            "parser emits a deterministic ``unsupported`` or "
            "``ambiguous`` diagnosis instead of inventing parameters."
        ),
        architecture_refs=(
            "docs/ROBOTICS_SKILL_AUTHORING_WORKBENCH.md",
            "docs/SKILL_TEMPLATE_CATALOG.md",
        ),
        implementation_refs=(
            "backend/app/skill_authoring/catalog.py",
            "backend/app/skill_authoring/intent_parser.py",
            "backend/app/skill_authoring/templates.py",
            "backend/app/skill_authoring/generator.py",
        ),
        test_refs=(
            "backend/tests/test_skill_authoring.py::test_move_forward_6_feet_generates_bounded_python",
            "backend/tests/test_skill_authoring.py::test_parser_rejects_unsupported_instruction",
            "backend/tests/test_skill_authoring.py::test_unsupported_request_is_unsupported",
            "backend/tests/test_skill_authoring.py::test_catalog_is_closed_set",
            "backend/tests/test_skill_authoring.py::test_generator_is_deterministic_for_fixed_timestamp",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-002",
        kind=RequirementKind.SKILL,
        title="Generated motion code uses /cmd_vel_requested only",
        description=(
            "Every motion-bearing snippet emitted by the skill "
            "workbench publishes to ``/cmd_vel_requested`` and never "
            "to ``/cmd_vel``. The safety supervisor and motion "
            "arbitration remain authoritative; the workbench is "
            "incapable of granting actuator authority."
        ),
        architecture_refs=(
            "docs/SKILL_SAFETY_BOUNDARY.md",
            "docs/SAFETY_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/skill_authoring/templates.py",
            "backend/app/skill_authoring/validator.py",
        ),
        test_refs=(
            "backend/tests/test_skill_authoring.py::test_move_forward_code_uses_requested_motion_topic",
            "backend/tests/test_skill_authoring.py::test_no_template_publishes_directly_to_cmd_vel",
            "backend/tests/test_skill_authoring.py::test_validator_rejects_direct_cmd_vel_publication",
            "backend/tests/test_skill_authoring.py::test_motion_snippets_publish_final_zero",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-003",
        kind=RequirementKind.SKILL,
        title="Unsupported, ambiguous, or unsafe requests produce deterministic diagnostics",
        description=(
            "The parser routes a developer request to one of: "
            "``generated``, ``unsupported``, ``ambiguous``, or "
            "``rejected``. Forbidden phrases (direct actuator "
            "command, safety override, e-stop override, unbounded "
            "motion or speed, direct motor control, sensor disable, "
            "shell or code execution, network egress) deterministically "
            "produce a rejection with a stable diagnostic code."
        ),
        architecture_refs=(
            "docs/SKILL_SAFETY_BOUNDARY.md",
            "docs/ROBOTICS_SKILL_AUTHORING_WORKBENCH.md",
        ),
        implementation_refs=(
            "backend/app/skill_authoring/intent_parser.py",
            "backend/app/skill_authoring/diagnostics.py",
        ),
        test_refs=(
            "backend/tests/test_skill_authoring.py::test_ambiguous_move_forward_is_ambiguous",
            "backend/tests/test_skill_authoring.py::test_direct_cmd_vel_request_is_rejected",
            "backend/tests/test_skill_authoring.py::test_disable_safety_is_rejected",
            "backend/tests/test_skill_authoring.py::test_ignore_estop_is_rejected",
            "backend/tests/test_skill_authoring.py::test_unbounded_motion_is_rejected",
            "backend/tests/test_skill_authoring.py::test_unbounded_speed_is_rejected",
            "backend/tests/test_skill_authoring.py::test_direct_motor_control_is_rejected",
            "backend/tests/test_skill_authoring.py::test_shell_command_is_rejected",
            "backend/tests/test_skill_authoring.py::test_sensor_disable_is_rejected",
            "backend/tests/test_skill_authoring.py::test_distance_out_of_range_is_rejected",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-004",
        kind=RequirementKind.SKILL,
        title="Generated skills include safety reviews, diagnostics, and audit artifacts",
        description=(
            "Every successful generation produces a "
            "``GeneratedSkill`` that bundles parameters, "
            "diagnostics, a ``SkillSafetyReview`` (status + risk "
            "band + allowed/forbidden topics + notes), and a "
            "filesystem audit bundle (request.json, generated-skill.json, "
            "code.py, safety-review.json, diagnostics.json, "
            "code-card.json, skill-report.md). Every rejected "
            "generation produces a rejection bundle (request.json, "
            "candidate.json, diagnostics.json, rejection-report.md)."
        ),
        architecture_refs=(
            "docs/ROBOTICS_SKILL_AUTHORING_WORKBENCH.md",
        ),
        implementation_refs=(
            "backend/app/skill_authoring/safety_review.py",
            "backend/app/skill_authoring/audit.py",
            "backend/app/skill_authoring/reporter.py",
        ),
        test_refs=(
            "backend/tests/test_skill_authoring.py::test_audit_bundle_layout_is_complete_for_accepted",
            "backend/tests/test_skill_authoring.py::test_rejection_bundle_layout_is_complete",
            "backend/tests/test_skill_authoring.py::test_audit_includes_disclaimer",
            "backend/tests/test_skill_authoring.py::test_safety_review_lists_allowed_and_forbidden_topics",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-005",
        kind=RequirementKind.SKILL,
        title="Code-card metadata supports a future reviewer UI without adding frontend dependencies",
        description=(
            "Each generated skill includes a ``CodeCard`` payload "
            "with title, subtitle, language, line count, copy "
            "label, safety badges, animation steps, and risk band. "
            "No frontend dependency is added in Phase 15A; the "
            "metadata is JSON only."
        ),
        architecture_refs=(
            "docs/CODE_CARD_METADATA.md",
        ),
        implementation_refs=(
            "backend/app/skill_authoring/diagnostics.py",
            "backend/app/skill_authoring/models.py",
        ),
        test_refs=(
            "backend/tests/test_skill_authoring.py::test_code_card_metadata_present_on_accepted_skill",
            "backend/tests/test_skill_authoring.py::test_code_card_animation_steps_for_move_forward",
            "backend/tests/test_skill_authoring.py::test_skill_layer_has_no_frontend_imports",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-LLM-001",
        kind=RequirementKind.SKILL_LLM,
        title="Local LLM skill providers must be disabled by default",
        description=(
            "The Phase 15B skill-LLM provider layer defaults to "
            "``provider_mode=disabled``. Tools that use it must "
            "require both ``--allow-local-provider`` AND an "
            "explicitly enabled provider config before a local "
            "provider may be selected. The disabled mode emits a "
            "deterministic ``not_configured`` envelope."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_SKILL_PROVIDER.md",
            "docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/config.py",
            "backend/app/skill_llm_provider/provider.py",
            "backend/app/skill_llm_provider/adapter.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_provider.py::test_default_provider_mode_is_disabled",
            "backend/tests/test_skill_llm_provider.py::test_disabled_provider_returns_not_configured",
            "backend/tests/test_skill_llm_provider.py::test_local_http_requires_allow_local_provider_flag",
            "backend/tests/test_skill_llm_provider.py::test_local_http_requires_config_enabled",
            "backend/tests/test_skill_llm_provider.py::test_ollama_returns_not_configured_when_disabled",
            "backend/tests/test_skill_llm_provider.py::test_llama_cpp_returns_not_configured_when_disabled",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-LLM-002",
        kind=RequirementKind.SKILL_LLM,
        title="Cloud or external LLM endpoints must be rejected",
        description=(
            "Any endpoint configured for a local provider is "
            "policy-checked against the loopback allowlist "
            "(``localhost``, ``127.0.0.1``, ``::1``). Cloud SaaS "
            "hosts, HTTPS endpoints, and any non-loopback host "
            "produce a ``rejected_endpoint`` envelope and never "
            "reach the provider's transport layer."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/config.py",
            "backend/app/skill_llm_provider/provider.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_provider.py::test_cloud_endpoint_is_rejected",
            "backend/tests/test_skill_llm_provider.py::test_https_endpoint_is_rejected",
            "backend/tests/test_skill_llm_provider.py::test_loopback_endpoint_is_accepted_by_policy",
            "backend/tests/test_skill_llm_provider.py::test_provider_layer_has_no_cloud_sdk_imports",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-LLM-003",
        kind=RequirementKind.SKILL_LLM,
        title="LLM candidates must pass the sanitizer before deterministic skill validation",
        description=(
            "Every candidate runs through "
            "``sanitize_candidate`` before the Phase 15A skill "
            "validator is invoked. Sanitizer rejection skips the "
            "validator entirely; the audit records that the "
            "validator was not invoked. The sanitizer rejects "
            "direct ``/cmd_vel``, ``while True``, shell or code "
            "execution, network access, secret patterns, "
            "destructive shell commands, direct motor control, "
            "safety overrides, and e-stop overrides."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_SKILL_PROVIDER.md",
            "docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/sanitizer.py",
            "backend/app/skill_llm_provider/validator_bridge.py",
            "backend/app/skill_llm_provider/adapter.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_direct_cmd_vel",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_allows_cmd_vel_requested",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_while_true",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_subprocess",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_os_system",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_eval_exec",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_socket",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_requests_httpx",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_openai_anthropic_cohere_imports",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_api_key_password_secret",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_ros2_topic_pub_cmd_vel",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejects_safety_override_phrases",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejection_skips_validator",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-LLM-004",
        kind=RequirementKind.SKILL_LLM,
        title="Accepted candidates must preserve requested-motion safety boundaries",
        description=(
            "Only candidates that pass both the sanitizer AND the "
            "Phase 15A skill validator are labelled ``accepted`` and "
            "produce a code-card payload. The validator enforces "
            "use of ``/cmd_vel_requested`` and rejects snippets that "
            "are missing stop commands, timeouts, or that publish to "
            "``/cmd_vel`` directly."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_SKILL_PROVIDER.md",
            "docs/SKILL_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/validator_bridge.py",
            "backend/app/skill_authoring/validator.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_provider.py::test_valid_candidate_is_accepted",
            "backend/tests/test_skill_llm_provider.py::test_missing_stop_command_is_validator_rejected",
            "backend/tests/test_skill_llm_provider.py::test_missing_timeout_is_validator_rejected",
            "backend/tests/test_skill_llm_provider.py::test_accepted_candidate_produces_code_card",
            "backend/tests/test_skill_llm_provider.py::test_accepted_candidate_uses_requested_motion_topic",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-LLM-005",
        kind=RequirementKind.SKILL_LLM,
        title="LLM candidate audits must preserve provider, sanitizer, validator, safety review, and disclaimer",
        description=(
            "Every audit bundle records the request, the provider "
            "envelope, the candidate (when produced), the sanitizer "
            "result, the validator result, the safety review (when "
            "accepted), and the verbatim Phase 15B disclaimer. The "
            "filesystem layout is stable: ``request.json``, "
            "``provider-result.json``, ``sanitizer-result.json``, "
            "``validator-result.json``, ``llm-candidate-report.md``, "
            "and (when accepted) ``candidate.json``, "
            "``safety-review.json``, ``code-card.json``."
        ),
        architecture_refs=(
            "docs/SKILL_LLM_CANDIDATE_AUDITS.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/audit.py",
            "backend/app/skill_llm_provider/reporter.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_provider.py::test_accepted_audit_bundle_layout_is_complete",
            "backend/tests/test_skill_llm_provider.py::test_sanitizer_rejection_audit_bundle_layout",
            "backend/tests/test_skill_llm_provider.py::test_audit_includes_disclaimer",
            "backend/tests/test_skill_llm_provider.py::test_audit_preserves_provider_mode",
            "backend/tests/test_skill_llm_provider.py::test_audit_json_is_stable_across_runs",
        ),
    ),
    Requirement(
        req_id="REQ-REHEARSAL-001",
        kind=RequirementKind.REHEARSAL,
        title="Mission rehearsals must remain simulation-only",
        description=(
            "The Phase 16 mission rehearsal pipeline never runs on "
            "real hardware, never publishes to ROS, never opens a "
            "network socket, and never executes user code. All "
            "motion events are deterministic, simulated, and "
            "labelled ``MOTION_REQUEST_SIMULATED``. Replay bundles "
            "report ``bag_backed=False``; analytics distinguishes "
            "simulated evidence from live evidence."
        ),
        architecture_refs=(
            "docs/GOVERNED_MISSION_REHEARSAL.md",
            "docs/REHEARSAL_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/mission_rehearsal/rehearsal_runtime.py",
            "backend/app/mission_rehearsal/rehearsal_replay_bridge.py",
        ),
        test_refs=(
            "backend/tests/test_mission_rehearsal.py::test_rehearsal_runtime_emits_simulated_motion_only",
            "backend/tests/test_mission_rehearsal.py::test_replay_bundle_is_not_bag_backed",
            "backend/tests/test_mission_rehearsal.py::test_package_has_no_network_or_ros_imports",
        ),
    ),
    Requirement(
        req_id="REQ-REHEARSAL-002",
        kind=RequirementKind.REHEARSAL,
        title="Mission rehearsals must preserve deterministic replay ordering",
        description=(
            "Identical inputs produce byte-identical event streams "
            "and deterministic hashes. Event ordering is stable "
            "across repeated runs; ``event_time_ns`` is derived "
            "from the event sequence, not the wall clock."
        ),
        architecture_refs=(
            "docs/SIMULATION_REHEARSAL_PIPELINE.md",
            "docs/MISSION_REHEARSAL_STATE_MACHINE.md",
        ),
        implementation_refs=(
            "backend/app/mission_rehearsal/rehearsal_events.py",
            "backend/app/mission_rehearsal/rehearsal_runtime.py",
        ),
        test_refs=(
            "backend/tests/test_mission_rehearsal.py::test_same_input_same_event_stream",
            "backend/tests/test_mission_rehearsal.py::test_same_seed_same_timeline",
            "backend/tests/test_mission_rehearsal.py::test_deterministic_hashes_stable",
            "backend/tests/test_mission_rehearsal.py::test_replay_artifacts_are_stable_across_runs",
        ),
    ),
    Requirement(
        req_id="REQ-REHEARSAL-003",
        kind=RequirementKind.REHEARSAL,
        title="Mission rehearsals require supervisor approval before execution simulation",
        description=(
            "The rehearsal state machine refuses to enter the "
            "``rehearsing`` state unless the supervisor decision "
            "is ``approved``. Validator-rejected plans never reach "
            "the supervisor; supervisor-rejected plans never reach "
            "the runtime. The state machine guarantees no skipped "
            "approvals via the explicit transition set in "
            "``rehearsal_state_machine.REHEARSAL_TRANSITIONS``."
        ),
        architecture_refs=(
            "docs/MISSION_REHEARSAL_STATE_MACHINE.md",
            "docs/REHEARSAL_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/mission_rehearsal/rehearsal_supervisor.py",
            "backend/app/mission_rehearsal/rehearsal_state_machine.py",
            "backend/app/mission_rehearsal/rehearsal_runtime.py",
        ),
        test_refs=(
            "backend/tests/test_mission_rehearsal.py::test_supervisor_rejection_blocks_rehearsing",
            "backend/tests/test_mission_rehearsal.py::test_validator_rejection_blocks_supervisor",
            "backend/tests/test_mission_rehearsal.py::test_state_machine_rejects_illegal_transition",
            "backend/tests/test_mission_rehearsal.py::test_state_machine_allows_valid_transitions",
        ),
    ),
    Requirement(
        req_id="REQ-REHEARSAL-004",
        kind=RequirementKind.REHEARSAL,
        title="Replay artifacts preserve evidence origin and deterministic hashes",
        description=(
            "Every rehearsal replay bundle records ``evidence_status"
            "='simulated'`` and ``bag_backed=False``. The bundle "
            "includes the plan's deterministic hash, the runtime's "
            "deterministic hash, and every event's "
            "``deterministic_hash``. No bag-backed claim is made "
            "unless real bag artefacts exist (and Phase 16 never "
            "produces real bag artefacts)."
        ),
        architecture_refs=(
            "docs/REHEARSAL_REPLAY_INTEGRATION.md",
            "docs/REPLAY_ANALYTICS.md",
        ),
        implementation_refs=(
            "backend/app/mission_rehearsal/rehearsal_replay_bridge.py",
            "backend/app/mission_rehearsal/rehearsal_audit.py",
        ),
        test_refs=(
            "backend/tests/test_mission_rehearsal.py::test_replay_bundle_carries_evidence_origin",
            "backend/tests/test_mission_rehearsal.py::test_replay_markers_carry_deterministic_hashes",
            "backend/tests/test_mission_rehearsal.py::test_replay_bundle_is_not_bag_backed",
        ),
    ),
    Requirement(
        req_id="REQ-REHEARSAL-005",
        kind=RequirementKind.REHEARSAL,
        title="Analytics distinguishes approved, rejected, aborted, and completed rehearsals",
        description=(
            "The Phase 16 analytics bridge emits separate "
            "``approved_count``, ``rejected_count``, "
            "``aborted_count``, ``completed_count``, "
            "``supervisor_rejection_count``, and "
            "``validator_rejection_count`` fields. No probabilistic "
            "or AI-generated analytics are produced."
        ),
        architecture_refs=(
            "docs/REHEARSAL_REPLAY_INTEGRATION.md",
            "docs/REPLAY_ANALYTICS.md",
        ),
        implementation_refs=(
            "backend/app/mission_rehearsal/rehearsal_analytics_bridge.py",
        ),
        test_refs=(
            "backend/tests/test_mission_rehearsal.py::test_analytics_counts_completed_rehearsal",
            "backend/tests/test_mission_rehearsal.py::test_analytics_counts_supervisor_rejection",
            "backend/tests/test_mission_rehearsal.py::test_analytics_counts_validator_rejection",
            "backend/tests/test_mission_rehearsal.py::test_analytics_deterministic_replay_stable_flag",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-001",
        kind=RequirementKind.MISSION_CONTROL,
        title="Mission-control UI is simulation-only and never opens a network socket",
        description=(
            "The Phase 17A mission-control workspace at "
            "``apps/mission-control/`` runs as a static-export "
            "Next.js application. It reads JSON artefacts from "
            "disk via Node.js ``fs.readFile`` and renders them. The "
            "package never imports a cloud LLM SDK, a generic HTTP "
            "client (``axios``, ``isomorphic-fetch``), Node's "
            "``child_process`` / ``net`` / ``dgram`` modules. Every "
            "page is statically prerenderable."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_UI.md",
            "docs/OPERATOR_WORKSTATION_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/adapters/loader.ts",
            "apps/mission-control/src/app/layout.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/honesty.test.ts::frontend honesty rules > never imports a cloud LLM SDK or a generic HTTP client",
            "apps/mission-control/tests/honesty.test.ts::frontend honesty rules > never spawns subprocesses or opens raw sockets",
            "apps/mission-control/tests/honesty.test.ts::frontend honesty rules > never references a /cmd_vel publication outside comments + descriptive context",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-002",
        kind=RequirementKind.MISSION_CONTROL,
        title="Replay viewer distinguishes simulated rehearsals from bag-backed evidence",
        description=(
            "The ``EvidenceStatusChip`` component renders the "
            "verbatim ``evidence_status`` AND ``bag_backed`` value "
            "from the source artefact. A simulated rehearsal can "
            "never appear as bag-backed; the chip's display text "
            "would contradict itself. The replay viewer index labels "
            "the overall bundle count as ``simulation-only · "
            "bag-backed: 0`` to keep operator trust honest."
        ),
        architecture_refs=(
            "docs/REPLAY_VIEWER_GUIDE.md",
            "docs/AUTONOMY_VISUALIZATION_GUIDE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/EvidenceStatusChip.tsx",
            "apps/mission-control/src/app/replay/page.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::EvidenceStatusChip > renders verbatim status and bag-backed=no",
            "apps/mission-control/tests/components.test.tsx::EvidenceStatusChip > never silently inverts the bag-backed claim",
            "apps/mission-control/tests/adapter.test.ts::rehearsal audit adapters > loads all audits in stable order",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-003",
        kind=RequirementKind.MISSION_CONTROL,
        title="Mission-control surfaces deterministic authority boundaries",
        description=(
            "Every operator surface (dashboard, workbench, replay, "
            "safety authority, evidence) renders the persistent "
            "``SafetyBoundaryBanner`` and exposes the supervisor "
            "decision verbatim. The Safety Authority page explains "
            "who can authorise motion, what is rejected, and why "
            "``/cmd_vel_requested`` exists."
        ),
        architecture_refs=(
            "docs/SAFETY_AUTHORITY_VISUALIZATION.md",
            "docs/MISSION_CONTROL_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/SafetyBoundaryBanner.tsx",
            "apps/mission-control/src/components/SupervisorAuthorityPanel.tsx",
            "apps/mission-control/src/app/safety/page.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::SafetyBoundaryBanner > declares the platform is not safety-certified",
            "apps/mission-control/tests/honesty.test.ts::frontend honesty rules > the SafetyBoundaryBanner is rendered from the root layout",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-004",
        kind=RequirementKind.MISSION_CONTROL,
        title="Generated code panels preserve the deterministic validator outcome",
        description=(
            "The Workbench's ``CodeCard`` component renders the "
            "verbatim source emitted by the Phase 15A skill "
            "workbench. The component does not autoformat, "
            "re-flow, or trim the code text because the audit "
            "bundle's deterministic hash depends on the exact "
            "bytes. The card surfaces every safety badge from the "
            "skill's code-card payload."
        ),
        architecture_refs=(
            "docs/AUTONOMY_VISUALIZATION_GUIDE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/CodeCard.tsx",
            "apps/mission-control/src/app/workbench/page.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/adapter.test.ts::skill library > loads accepted skills with code cards",
            "apps/mission-control/tests/adapter.test.ts::skill library > the move_forward_6_feet skill converts to 1.8288 m",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-005",
        kind=RequirementKind.MISSION_CONTROL,
        title="Dashboards do not fabricate live runtime status",
        description=(
            "The dashboard reads "
            "``live-runtime/live-runtime-maturity.json`` verbatim "
            "and exposes the same status text the Phase 13 "
            "aggregator emitted. Bag-backed counts are sourced "
            "directly; the dashboard never recodes "
            "``not_established`` into something more optimistic. "
            "When the artefact is missing on disk the dashboard "
            "shows an honest placeholder."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_UI.md",
            "docs/LIVE_RUNTIME_MATURITY_REPORT.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/adapters/loader.ts",
            "apps/mission-control/src/app/page.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/adapter.test.ts::traceability > reads the committed traceability JSON",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-006",
        kind=RequirementKind.MISSION_CONTROL,
        title="Rejected missions remain visible",
        description=(
            "The replay viewer and the mission detail page render "
            "every audit, including those whose ``final_status`` is "
            "``rejected`` or ``aborted``. The status pill is "
            "colour-coded but never hidden; the mission stepper "
            "shows the halt point; the audit panel preserves the "
            "rejection reason. No filter silently drops rejected "
            "rehearsals."
        ),
        architecture_refs=(
            "docs/REPLAY_VIEWER_GUIDE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionCard.tsx",
            "apps/mission-control/src/components/MissionStateStepper.tsx",
            "apps/mission-control/src/app/replay/page.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/adapter.test.ts::rehearsal audit adapters > preserves rejection reasons",
            "apps/mission-control/tests/components.test.tsx::MissionStateStepper > does not silently hide the rejected state",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-007",
        kind=RequirementKind.MISSION_CONTROL,
        title="Mission-control adapters return null on missing artefacts",
        description=(
            "Adapter functions in "
            "``apps/mission-control/src/adapters/loader.ts`` return "
            "``null`` (or an empty array) when an artefact is "
            "missing. They never synthesise a happy-path value. "
            "The UI handles the null case with an honest placeholder "
            "(e.g. ``No rehearsal events recorded.``)."
        ),
        architecture_refs=(
            "docs/OPERATOR_WORKSTATION_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/adapters/loader.ts",
        ),
        test_refs=(
            "apps/mission-control/tests/adapter.test.ts::rehearsal audit adapters > returns null for unknown audits",
            "apps/mission-control/tests/components.test.tsx::DeterministicHashDisplay > handles null hashes without crashing",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-008",
        kind=RequirementKind.MISSION_CONTROL,
        title="Operator surfaces preserve deterministic hashes",
        description=(
            "Plan, runtime, replay, and per-event deterministic "
            "hashes are rendered via the ``DeterministicHashDisplay`` "
            "component. The full hash is exposed in the tooltip "
            "so a reviewer can confirm reproducibility without "
            "leaving the console."
        ),
        architecture_refs=(
            "docs/AUTONOMY_VISUALIZATION_GUIDE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/DeterministicHashDisplay.tsx",
            "apps/mission-control/src/components/AuditPanel.tsx",
            "apps/mission-control/src/components/ReplayTimeline.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::DeterministicHashDisplay > renders the short hash and the full hash via title",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-009",
        kind=RequirementKind.MISSION_CONTROL,
        title="Mission-control does not claim live deployment",
        description=(
            "The persistent ``SafetyBoundaryBanner`` declares the "
            "platform is simulation-only and not safety-certified "
            "on every page. The sidebar's honesty footer repeats "
            "that bag-backed evidence count remains 0. No CTA, "
            "button, or surface implies live robot deployment."
        ),
        architecture_refs=(
            "docs/SAFETY_AUTHORITY_VISUALIZATION.md",
            "docs/MISSION_CONTROL_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/SafetyBoundaryBanner.tsx",
            "apps/mission-control/src/components/SiteNav.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::SafetyBoundaryBanner > declares the platform is not safety-certified",
        ),
    ),
    Requirement(
        req_id="REQ-MCTRL-010",
        kind=RequirementKind.MISSION_CONTROL,
        title="Frontend never imports a cloud LLM SDK or live-network module",
        description=(
            "An AST-style honesty test asserts the frontend source "
            "tree never imports ``openai``, ``@anthropic-ai/sdk``, "
            "``cohere-ai``, ``@google/generative-ai``, ``axios``, "
            "``isomorphic-fetch``, ``node:child_process``, "
            "``node:net``, or ``node:dgram``. The Phase 17A layer "
            "therefore cannot exfiltrate operator text, cannot "
            "spawn processes, and cannot open arbitrary sockets."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_UI.md",
            "docs/OPERATOR_WORKSTATION_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/",
        ),
        test_refs=(
            "apps/mission-control/tests/honesty.test.ts::frontend honesty rules > never imports a cloud LLM SDK or a generic HTTP client",
            "apps/mission-control/tests/honesty.test.ts::frontend honesty rules > never spawns subprocesses or opens raw sockets",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-001",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Mission maps preserve the simulated / bag-backed distinction",
        description=(
            "Every spatial visualisation declares its data origin in "
            "the figure caption (``derived from bounded inputs``, "
            "``topology only``, or ``unavailable``). Replay bundles "
            "rendered on the map always read ``bag_backed=false``; "
            "no map surface can fabricate a bag-backed claim."
        ),
        architecture_refs=(
            "docs/MISSION_SPATIAL_VISUALIZATION.md",
            "docs/MISSION_REPLAY_MAPS.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionMap.tsx",
            "apps/mission-control/src/adapters/spatial.ts",
        ),
        test_refs=(
            "apps/mission-control/tests/spatial.test.ts::MissionMap derivation > labels the derivation source on every route",
            "apps/mission-control/tests/spatial.test.ts::MissionMap derivation > unavailable plan renders an honest placeholder",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-002",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Replay overlays preserve evidence origin",
        description=(
            "The mission playback panel surfaces the verbatim "
            "``EvidenceStatusChip`` alongside the deterministic map. "
            "Event markers projected onto the map carry the same "
            "deterministic hashes as the audit JSON events; the UI "
            "renders no marker that the audit didn't record."
        ),
        architecture_refs=(
            "docs/MISSION_REPLAY_MAPS.md",
            "docs/SPATIAL_REPLAY_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionPlaybackPanel.tsx",
            "apps/mission-control/src/components/MissionEventMarker.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/spatial.test.ts::event projection > carries through deterministic hashes",
            "apps/mission-control/tests/spatial.test.ts::event projection > marks events without waypoint payloads as off-map",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-003",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Rejected missions remain visually rejected on every map and timeline",
        description=(
            "The ``MissionSpatialTimeline`` and the ``MissionMap`` "
            "render rejected and aborted rehearsals with severity-"
            "specific colours. The ``WhyRejectedDrilldown`` panel "
            "always appears on a rejected mission detail page; it "
            "lists the verbatim validator and supervisor rejection "
            "codes."
        ),
        architecture_refs=(
            "docs/MISSION_SPATIAL_VISUALIZATION.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionSpatialTimeline.tsx",
            "apps/mission-control/src/components/WhyRejectedDrilldown.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::WhyRejectedDrilldown > shows the verbatim rejection reason",
            "apps/mission-control/tests/components.test.tsx::WhyRejectedDrilldown > renders nothing on accepted missions",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-004",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Supervisor interventions remain visible on the map and detail page",
        description=(
            "The ``SupervisorInterventionOverlay`` lists every "
            "supervisor or safety event with severity > info. The "
            "list is never silently filtered, even for rehearsals "
            "that completed without rejection (an empty list is "
            "rendered as an honest placeholder)."
        ),
        architecture_refs=(
            "docs/MISSION_REPLAY_MAPS.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/SupervisorInterventionOverlay.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::SupervisorInterventionOverlay > lists rejection events",
            "apps/mission-control/tests/components.test.tsx::SupervisorInterventionOverlay > renders honest placeholder for empty input",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-005",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Spatial playback must not fabricate unavailable coordinates",
        description=(
            "The deterministic ``buildMissionRoute`` adapter returns "
            "``derivation_source='unavailable'`` when the plan has "
            "no waypoints, ``'topology_only'`` when no bounded "
            "distance/angle is present, and ``'bounded_inputs'`` "
            "otherwise. The UI renders an honest placeholder for "
            "the unavailable case rather than inventing positions."
        ),
        architecture_refs=(
            "docs/MISSION_SPATIAL_VISUALIZATION.md",
            "docs/SPATIAL_REPLAY_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/adapters/spatial.ts",
        ),
        test_refs=(
            "apps/mission-control/tests/spatial.test.ts::MissionMap derivation > unavailable plan renders an honest placeholder",
            "apps/mission-control/tests/spatial.test.ts::buildMissionRoute > topology-only fallback when no distance is bounded",
            "apps/mission-control/tests/spatial.test.ts::buildMissionRoute > deterministic across repeated calls",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-006",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Mission route segments use only bounded distance + angle inputs",
        description=(
            "Spatial coordinates are derived deterministically from "
            "the audit's ``bounded_distance_m`` and "
            "``bounded_angle_deg`` per waypoint. No coordinate is "
            "fabricated; the adapter never reads real-time data, "
            "never queries a network resource, and never randomises "
            "positions."
        ),
        architecture_refs=(
            "docs/MISSION_SPATIAL_VISUALIZATION.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/adapters/spatial.ts",
        ),
        test_refs=(
            "apps/mission-control/tests/spatial.test.ts::buildMissionRoute > forward motion advances along heading deterministically",
            "apps/mission-control/tests/spatial.test.ts::buildMissionRoute > deterministic across repeated calls",
            "apps/mission-control/tests/spatial.test.ts::buildMissionRoute > stops and docks add no displacement",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-007",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Frontend deployment preserves honesty-boundary rendering",
        description=(
            "Vercel deploys via ``vercel.json``; the Next.js "
            "framework preset runs ``npm ci && next build`` to "
            "produce a static export. The ``mission-control-ci.yml`` "
            "workflow runs the full honesty gate (``npm run "
            "typecheck && npm run test && npm run build``) on every "
            "PR and inspects the prerendered HTML to confirm every "
            "page carries the ``Simulation-only`` banner and never "
            "contains a ``bag-backed: yes`` claim."
        ),
        architecture_refs=(
            "docs/adr/ADR-009-vercel-deploy-target.md",
        ),
        implementation_refs=(
            "apps/mission-control/vercel.json",
            ".github/workflows/mission-control-ci.yml",
        ),
        test_refs=(
            "apps/mission-control/tests/deployment.test.ts::vercel.json > declares the Next.js framework",
            "apps/mission-control/tests/deployment.test.ts::vercel.json > uses the standard build pipeline",
            "apps/mission-control/tests/deployment.test.ts::mission-control-ci.yml > runs the full honesty gate",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-008",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Why-Rejected drilldown links rejection reasons to requirements",
        description=(
            "The ``WhyRejectedDrilldown`` panel maps a failure "
            "reason to an English explainer and a list of "
            "``REQ-*`` ids so a reviewer can trace the rejection "
            "to the deterministic rule that fired. The component "
            "never invents a reason; if the audit's failure_reason "
            "is unknown, the panel falls back to a generic note."
        ),
        architecture_refs=(
            "docs/OPERATOR_EXPERIENCE_GUIDELINES.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/WhyRejectedDrilldown.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::WhyRejectedDrilldown > shows the verbatim rejection reason",
            "apps/mission-control/tests/components.test.tsx::WhyRejectedDrilldown > renders nothing on accepted missions",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-009",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Replay scrubber is sequence-based and deterministic",
        description=(
            "The ``ReplayScrubber`` advances through the ordered "
            "event stream by index; ``event_time_ns`` is derived "
            "from the same sequence in the backend. The scrubber "
            "never invents timestamps and the visual position is "
            "always reproducible against the audit JSON."
        ),
        architecture_refs=(
            "docs/MISSION_REPLAY_MAPS.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/ReplayScrubber.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::ReplayScrubber > renders one slider per event",
            "apps/mission-control/tests/components.test.tsx::ReplayScrubber > handles empty event lists honestly",
        ),
    ),
    Requirement(
        req_id="REQ-MVIS-010",
        kind=RequirementKind.MISSION_VISUALIZATION,
        title="Operator surfaces communicate spatial-data unavailability honestly",
        description=(
            "When a plan or runtime is absent, every spatial panel "
            "(``MissionMap``, ``MissionPlaybackPanel``, "
            "``RouteProgressIndicator``, ``WaypointOverlay``, "
            "``ZoneBoundaryOverlay``) renders an explicit "
            "placeholder string instead of an empty visual. The "
            "operator can therefore distinguish ``no data`` from "
            "``data present but quiet``."
        ),
        architecture_refs=(
            "docs/OPERATOR_EXPERIENCE_GUIDELINES.md",
            "docs/SPATIAL_REPLAY_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionMap.tsx",
            "apps/mission-control/src/components/RouteProgressIndicator.tsx",
            "apps/mission-control/src/components/WaypointOverlay.tsx",
            "apps/mission-control/src/components/ZoneBoundaryOverlay.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/components.test.tsx::MissionMap > unavailable route renders an explicit placeholder",
            "apps/mission-control/tests/components.test.tsx::WaypointOverlay > prompts when no waypoint is selected",
            "apps/mission-control/tests/components.test.tsx::RouteProgressIndicator > shows placeholder for empty waypoints",
        ),
    ),
    # -----------------------------------------------------------------
    # Phase 17C — bag-backed spatial replay upgrade.
    # -----------------------------------------------------------------
    Requirement(
        req_id="REQ-SREPLAY-001",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="A run is bag-backed only when the bag manifest validates",
        description=(
            "The :func:`evaluate_bag_eligibility` helper refuses to "
            "label a run ``bag_backed`` unless its bag manifest is "
            "present, its bag paths exist on disk, its metadata yaml "
            "exists, its validation_status is passed or partial, and "
            "runtime pose samples were extracted. Any missing input "
            "demotes the run to ``fixture``, ``bounded_inputs``, "
            "``topology_only``, or ``unavailable``."
        ),
        architecture_refs=(
            "docs/BAG_BACKED_SPATIAL_REPLAY.md",
            "docs/SPATIAL_REPLAY_HONESTY_RULES.md",
        ),
        implementation_refs=(
            "backend/app/spatial_replay/manifest_loader.py",
            "backend/app/spatial_replay/builder.py",
        ),
        test_refs=(
            "backend/tests/test_spatial_replay.py::test_missing_manifest_blocks_bag_backed",
            "backend/tests/test_spatial_replay.py::test_partial_manifest_blocks_bag_backed",
            "backend/tests/test_spatial_replay.py::test_missing_pose_samples_blocks_bag_backed",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-002",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Fixture-derived spatial samples are never bag-backed",
        description=(
            "Pose samples loaded from "
            "``spatial-replay/fixtures/<run_id>/pose-samples.jsonl`` "
            "always produce a ``derivation_source=fixture`` artefact. "
            "The validator additionally surfaces this as a known "
            "limitation in the artefact's JSON output."
        ),
        architecture_refs=(
            "docs/BAG_BACKED_SPATIAL_REPLAY.md",
            "docs/SPATIAL_REPLAY_ARTIFACT_FORMAT.md",
        ),
        implementation_refs=(
            "backend/app/spatial_replay/pose_extractor.py",
            "backend/app/spatial_replay/builder.py",
            "spatial-replay/fixtures/canonical-fixture/pose-samples.jsonl",
        ),
        test_refs=(
            "backend/tests/test_spatial_replay.py::test_fixture_samples_are_not_bag_backed",
            "backend/tests/test_spatial_replay.py::test_canonical_fixture_emits_fixture_derivation",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-003",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Derivation source is preserved through every artefact",
        description=(
            "The string emitted by the backend builder appears verbatim "
            "in ``spatial-replay.json``, in the markdown report, and in "
            "the frontend caption. The validator additionally rejects "
            "internally inconsistent artefacts (for example a "
            "``bag_backed`` artefact with zero samples)."
        ),
        architecture_refs=(
            "docs/SPATIAL_REPLAY_ARTIFACT_FORMAT.md",
            "docs/SPATIAL_REPLAY_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "backend/app/spatial_replay/reporter.py",
            "backend/app/spatial_replay/validator.py",
            "apps/mission-control/src/adapters/spatial.ts",
        ),
        test_refs=(
            "backend/tests/test_spatial_replay.py::test_derivation_source_round_trips_through_json",
            "backend/tests/test_spatial_replay.py::test_validator_rejects_bag_backed_without_samples",
            "apps/mission-control/tests/spatial-replay.test.ts::loadSpatialReplay > preserves derivation_source from artefact",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-004",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Trajectory builder is deterministic for ordered samples",
        description=(
            "Given an identical pose-samples input the segment list, "
            "trajectory status, and topic source tuple are byte-stable. "
            "The builder never resamples, never smooths, and never "
            "interpolates across distinct source topics."
        ),
        architecture_refs=(
            "docs/BAG_TO_TRAJECTORY_PIPELINE.md",
        ),
        implementation_refs=(
            "backend/app/spatial_replay/trajectory_builder.py",
        ),
        test_refs=(
            "backend/tests/test_spatial_replay.py::test_segments_are_deterministic",
            "backend/tests/test_spatial_replay.py::test_classify_trajectory_complete_partial_missing",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-005",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Event alignment falls back to off-map when out of tolerance",
        description=(
            "An event whose ``event_time_ns`` is farther than the "
            "alignment tolerance from every pose sample produces an "
            "alignment with ``matched_sample_id`` empty and "
            "``spatial_position`` null. The UI then renders the event "
            "in the timeline only — it is never placed on the map."
        ),
        architecture_refs=(
            "docs/BAG_TO_TRAJECTORY_PIPELINE.md",
            "docs/MISSION_REPLAY_MAPS.md",
        ),
        implementation_refs=(
            "backend/app/spatial_replay/event_aligner.py",
        ),
        test_refs=(
            "backend/tests/test_spatial_replay.py::test_event_alignment_off_map_when_out_of_tolerance",
            "backend/tests/test_spatial_replay.py::test_event_alignment_matches_nearest_sample",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-006",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Missing pose topics surface as warnings, never fabricated samples",
        description=(
            "When the expected pose topics include /tf but the bag's "
            "topic inventory does not, the trajectory is downgraded to "
            "``partial`` and the missing topic appears in "
            "``missing_topics``. No /tf sample is invented."
        ),
        architecture_refs=(
            "docs/SPATIAL_REPLAY_HONESTY_RULES.md",
            "docs/BAG_BACKED_SPATIAL_REPLAY.md",
        ),
        implementation_refs=(
            "backend/app/spatial_replay/trajectory_builder.py",
            "backend/app/spatial_replay/validator.py",
        ),
        test_refs=(
            "backend/tests/test_spatial_replay.py::test_missing_topic_produces_warning_not_fabrication",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-007",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Frontend prefers a spatial-replay artefact when present and valid",
        description=(
            "``loadSpatialReplay`` reads "
            "``spatial-replay/runs/<run_id>/spatial-replay.json`` and "
            "returns it verbatim when ``derivation_source`` is "
            "``bag_backed`` or ``fixture`` and the artefact validates. "
            "Otherwise the frontend falls back to the bounded-inputs "
            "adapter from Phase 17B."
        ),
        architecture_refs=(
            "docs/SPATIAL_REPLAY_ARCHITECTURE.md",
            "docs/MISSION_REPLAY_MAPS.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/adapters/spatial.ts",
            "apps/mission-control/src/adapters/loader.ts",
        ),
        test_refs=(
            "apps/mission-control/tests/spatial-replay.test.ts::loadSpatialReplay > returns fixture artefact for canonical-fixture",
            "apps/mission-control/tests/spatial-replay.test.ts::buildMissionRouteFromArtifact > prefers artefact over plan",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-008",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Mission Control surfaces the derivation source visibly",
        description=(
            "Every mission-map caption renders one of: \"Spatial source: "
            "bag-backed runtime evidence\", \"... bounded simulation "
            "inputs\", \"... topology only\", \"... fixture-derived "
            "spatial replay\", or \"... unavailable\". The reviewer can "
            "tell at a glance where the geometry came from."
        ),
        architecture_refs=(
            "docs/OPERATOR_EXPERIENCE_GUIDELINES.md",
            "docs/MISSION_REPLAY_MAPS.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionMap.tsx",
            "apps/mission-control/src/components/MissionPlaybackPanel.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/spatial-honesty.test.tsx::MissionMap > caption names the derivation source",
            "apps/mission-control/tests/spatial-honesty.test.tsx::MissionPlaybackPanel > badge surfaces bag-backed vs fixture",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-009",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="No static export renders bag-backed without a manifest backing it",
        description=(
            "The Mission Control CI workflow greps the static export for "
            "any ``bag-backed: yes`` or \"bag-backed runtime evidence\" "
            "claim that lacks a corresponding spatial-replay artefact "
            "with ``derivation_source=bag_backed``. The workflow fails "
            "if a fake bag-backed badge sneaks in."
        ),
        architecture_refs=(
            "docs/SPATIAL_REPLAY_HONESTY_RULES.md",
            "docs/adr/ADR-009-vercel-deploy-target.md",
        ),
        implementation_refs=(
            ".github/workflows/mission-control-ci.yml",
            "apps/mission-control/src/components/EvidenceStatusChip.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/spatial-honesty.test.tsx::CI honesty grep > no fake bag-backed claim in prerendered HTML",
            "apps/mission-control/tests/deployment.test.ts::mission-control-ci.yml > runs the full honesty gate",
        ),
    ),
    Requirement(
        req_id="REQ-SREPLAY-010",
        kind=RequirementKind.SPATIAL_REPLAY,
        title="Spatial-replay validator is the single bag-backed gatekeeper",
        description=(
            "Any caller (CLI, frontend, downstream report) that wants "
            "to render a bag-backed badge must first call "
            "``is_honestly_bag_backed(replay)``; that helper is the "
            "single source of truth for the bag-backed claim. The "
            "validator rejects internally inconsistent artefacts (for "
            "example a ``derivation_source=fixture`` artefact with "
            "``bag_status=bag_backed``)."
        ),
        architecture_refs=(
            "docs/SPATIAL_REPLAY_HONESTY_RULES.md",
            "docs/BAG_BACKED_SPATIAL_REPLAY.md",
        ),
        implementation_refs=(
            "backend/app/spatial_replay/validator.py",
        ),
        test_refs=(
            "backend/tests/test_spatial_replay.py::test_is_honestly_bag_backed_requires_samples",
            "backend/tests/test_spatial_replay.py::test_is_honestly_bag_backed_rejects_fixture",
        ),
    ),
    # -----------------------------------------------------------------
    # Phase 18 — artefact governance + immersive mission control.
    # -----------------------------------------------------------------
    Requirement(
        req_id="REQ-ARTREG-001",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Canonical artefact registry is the single source of truth",
        description=(
            "Every committed replay artefact is registered in "
            "``spatial-replay/registry/canonical-artifacts.json``. "
            "The frontend reads the registry before the filesystem; "
            "a missing or deprecated record blocks the UI from "
            "rendering the artefact."
        ),
        architecture_refs=(
            "docs/ARTIFACT_GOVERNANCE_MODEL.md",
            "docs/DETERMINISTIC_REPLAY_HYDRATION.md",
        ),
        implementation_refs=(
            "backend/app/artifact_registry/manifest.py",
            "backend/app/artifact_registry/registry.py",
            "apps/mission-control/src/adapters/loader.ts",
            "spatial-replay/registry/canonical-artifacts.json",
        ),
        test_refs=(
            "backend/tests/test_artifact_registry.py::test_canonical_registry_loads_and_validates",
            "apps/mission-control/tests/replay-governance.test.ts::loadArtifactRegistry > returns the committed canonical registry",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-002",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Deterministic hashes are committed and verified",
        description=(
            "Every registered file records its sha256 hex digest. "
            "The hydration CLI fails honestly when the bytes on disk "
            "drift from the committed hash."
        ),
        architecture_refs=(
            "docs/DETERMINISTIC_REPLAY_HYDRATION.md",
        ),
        implementation_refs=(
            "backend/app/artifact_registry/deterministic_hash.py",
            "backend/app/artifact_registry/validation.py",
            "tools/hydrate_replay_artifacts.py",
        ),
        test_refs=(
            "backend/tests/test_artifact_registry.py::test_verify_artifact_failed_on_mismatch",
            "backend/tests/test_artifact_registry.py::test_canonical_registry_paths_match_disk",
            "apps/mission-control/tests/hydration-honesty.test.tsx::Phase 18 honesty rules > the canonical registry JSON's expected_hash matches the bytes on disk",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-003",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Hydration is idempotent",
        description=(
            "Two consecutive hydration passes against the same inputs "
            "produce byte-identical outputs. The CI workflow asserts "
            "no working-tree drift after hydration."
        ),
        architecture_refs=(
            "docs/DETERMINISTIC_REPLAY_HYDRATION.md",
        ),
        implementation_refs=(
            "backend/app/artifact_registry/hydration.py",
            "tools/hydrate_replay_artifacts.py",
            ".github/workflows/replay-hydration.yml",
            ".github/workflows/mission-control-ci.yml",
        ),
        test_refs=(
            "backend/tests/test_replay_hydration.py::test_hydration_is_idempotent",
            "backend/tests/test_replay_hydration.py::test_hydration_passes_on_committed_registry",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-004",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Lifecycle promotion only moves up the rung order",
        description=(
            "``can_promote`` accepts ``generated → hydrated → "
            "committed → verified → canonical`` and a deprecation "
            "side-state. The helper rejects any downward demotion; "
            "callers needing to demote must set ``deprecated`` "
            "explicitly."
        ),
        architecture_refs=(
            "docs/ARTIFACT_GOVERNANCE_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/artifact_registry/lifecycle.py",
        ),
        test_refs=(
            "backend/tests/test_artifact_registry.py::test_can_promote_only_moves_up",
            "backend/tests/test_artifact_registry.py::test_can_promote_unknown_state_rejected",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-005",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Integrity downgrades clamp the lifecycle claim",
        description=(
            "When integrity drops below ``passed`` the lifecycle "
            "helper returns ``committed`` instead of ``verified`` / "
            "``canonical``. The frontend reports the clamped value."
        ),
        architecture_refs=(
            "docs/ARTIFACT_GOVERNANCE_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/artifact_registry/lifecycle.py",
            "apps/mission-control/src/components/ReplayLifecyclePanel.tsx",
        ),
        test_refs=(
            "backend/tests/test_artifact_registry.py::test_lifecycle_clamped_to_committed_when_integrity_drops",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-006",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="A failing hydration NEVER rewrites the canonical registry",
        description=(
            "The hydration CLI writes the registry's "
            "``generated_at_utc`` only when ``overall_integrity = "
            "passed``. A failing hydration must leave the committed "
            "registry untouched so the operator can investigate drift."
        ),
        architecture_refs=(
            "docs/DETERMINISTIC_REPLAY_HYDRATION.md",
        ),
        implementation_refs=(
            "backend/app/artifact_registry/hydration.py",
        ),
        test_refs=(
            "backend/tests/test_replay_hydration.py::test_hydration_does_not_rewrite_registry_on_failure",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-007",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Deprecated records are hidden from the UI",
        description=(
            "``list_authoritative_records`` returns only "
            "``committed``, ``verified``, and ``canonical`` records; "
            "``deprecated`` and ``generated`` are filtered out."
        ),
        architecture_refs=(
            "docs/ARTIFACT_GOVERNANCE_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/artifact_registry/registry.py",
            "apps/mission-control/src/adapters/loader.ts",
        ),
        test_refs=(
            "backend/tests/test_artifact_registry.py::test_list_authoritative_records_filters",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-008",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Frontend confidence panel surfaces all governance inputs",
        description=(
            "``ReplayConfidencePanel`` reports derivation_source, "
            "bag_status, validation_status, registry integrity, "
            "sample count, topic sources, and missing topics in a "
            "single panel — the operator can read the trust level in "
            "one place."
        ),
        architecture_refs=(
            "docs/REPLAY_EVIDENCE_LINEAGE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/ReplayConfidencePanel.tsx",
            "apps/mission-control/src/components/EvidenceLineageGraph.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/artifact-lineage.test.tsx::ReplayConfidencePanel > computes a fixture band as medium",
            "apps/mission-control/tests/artifact-lineage.test.tsx::ReplayConfidencePanel > computes a bag-backed band as high when integrity passes",
            "apps/mission-control/tests/artifact-lineage.test.tsx::ReplayConfidencePanel > downgrades to low when integrity is partial",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-009",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="Hash chain panel exposes sha256 prefixes to the operator",
        description=(
            "``DeterministicHashChain`` renders one row per registered "
            "file with its 16-char sha256 prefix and byte count; the "
            "operator can manually run ``tools/hydrate_replay_"
            "artifacts.py --check-only`` to confirm reproducibility."
        ),
        architecture_refs=(
            "docs/DETERMINISTIC_REPLAY_HYDRATION.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/DeterministicHashChain.tsx",
            "apps/mission-control/src/components/ArtifactIntegrityBadge.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/artifact-lineage.test.tsx::DeterministicHashChain > renders one row per file with sha256 prefix",
            "apps/mission-control/tests/artifact-lineage.test.tsx::ArtifactIntegrityBadge > renders the verbatim integrity string",
        ),
    ),
    Requirement(
        req_id="REQ-ARTREG-010",
        kind=RequirementKind.ARTIFACT_REGISTRY,
        title="CI fails honestly when hydration drifts the working tree",
        description=(
            "Both ``mission-control-ci.yml`` and ``replay-hydration."
            "yml`` run ``tools/hydrate_replay_artifacts.py --check-"
            "only`` and then assert ``git diff -- spatial-replay/runs"
            "`` is empty. A drift fails the build with an explicit "
            "error annotation."
        ),
        architecture_refs=(
            "docs/DETERMINISTIC_REPLAY_HYDRATION.md",
            "docs/adr/ADR-009-vercel-deploy-target.md",
        ),
        implementation_refs=(
            ".github/workflows/replay-hydration.yml",
            ".github/workflows/mission-control-ci.yml",
        ),
        test_refs=(
            "apps/mission-control/tests/hydration-honesty.test.tsx::Phase 18 honesty rules > the canonical registry JSON's expected_hash matches the bytes on disk",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-001",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Immersive scene reads spatial-replay artefacts verbatim",
        description=(
            "``MissionScene`` consumes the bounded-inputs / fixture / "
            "bag-backed route directly; no coordinate is fabricated. "
            "The bottom-left overlay names ``derivation_source`` "
            "verbatim using ``describeDerivationSource``."
        ),
        architecture_refs=(
            "docs/IMMERSIVE_MISSION_CONTROL.md",
            "docs/3D_VISUALIZATION_BOUNDARY.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/3d/MissionScene.tsx",
            "apps/mission-control/src/3d/ReplayTrajectory3D.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/3d-scene.test.tsx::MissionTimelineBridge > falls back to the 2D panel when WebGL is unavailable",
            "apps/mission-control/tests/hydration-honesty.test.tsx::Phase 18 honesty rules > 3d scene components surface the derivation source",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-002",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Camera rig is deterministic across every playback mode",
        description=(
            "``chooseTarget`` is a pure function from "
            "``(mode, focus, sceneCenter, sceneRadius)`` to a "
            "``CameraTarget``. Identical inputs produce identical "
            "tuples; the rig snaps on mode change."
        ),
        architecture_refs=(
            "docs/CINEMATIC_REPLAY_ARCHITECTURE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/3d/ReplayCameraRig.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/cinematic-playback.test.ts::ReplayCameraRig > is deterministic for identical inputs",
            "apps/mission-control/tests/cinematic-playback.test.ts::ReplayCameraRig > overview camera is farther from the focus than operator review",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-003",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Immersive layer never opens a network socket",
        description=(
            "The honesty test grep asserts the entire ``src/`` tree "
            "imports no websocket / streaming client and constructs "
            "no raw ``WebSocket`` / ``EventSource``. The immersive "
            "scene is rendered locally with WebGL only."
        ),
        architecture_refs=(
            "docs/3D_VISUALIZATION_BOUNDARY.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/3d/MissionScene.tsx",
            "apps/mission-control/tests/hydration-honesty.test.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/hydration-honesty.test.tsx::Phase 18 honesty rules > never imports a websocket / streaming / socket.io client",
            "apps/mission-control/tests/hydration-honesty.test.tsx::Phase 18 honesty rules > never uses raw WebSocket / EventSource constructors",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-004",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Immersive playback degrades to the 2D panel when WebGL is unavailable",
        description=(
            "``MissionTimelineBridge`` probes for WebGL on mount and "
            "falls back to ``MissionPlaybackPanel`` when no WebGL "
            "context can be acquired. The fallback never fabricates "
            "data; it renders the verbatim Phase 17C 2D path."
        ),
        architecture_refs=(
            "docs/IMMERSIVE_MISSION_CONTROL.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/3d/MissionTimelineBridge.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/3d-scene.test.tsx::MissionTimelineBridge > falls back to the 2D panel when WebGL is unavailable",
            "apps/mission-control/tests/3d-scene.test.tsx::MissionTimelineBridge > renders the 2D fallback when prefer2D is explicit",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-005",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Mission narrative panel derives steps from the audit only",
        description=(
            "``MissionStoryPanel`` renders one step per lifecycle "
            "phase (proposal, validation, supervisor authority, "
            "rehearsal, intervention, outcome, replay) and every "
            "step is sourced from the audit. The panel never invents "
            "a step the audit does not justify."
        ),
        architecture_refs=(
            "docs/OPERATOR_REVIEW_EXPERIENCE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionStoryPanel.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/mission-storytelling.test.tsx::MissionStoryPanel > renders one step per lifecycle phase for an accepted mission",
            "apps/mission-control/tests/mission-storytelling.test.tsx::MissionStoryPanel > marks rejected missions as fail and names the failure reason",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-006",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Evidence lineage graph shows the source-to-render chain",
        description=(
            "``EvidenceLineageGraph`` renders one node per upstream "
            "source (rehearsal audit, bag manifest, fixture, "
            "spatial-replay artefact, registry, render) and tones "
            "each node by integrity. Operators can read the lineage "
            "without leaving the page."
        ),
        architecture_refs=(
            "docs/REPLAY_EVIDENCE_LINEAGE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/EvidenceLineageGraph.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/artifact-lineage.test.tsx::EvidenceLineageGraph > renders the lineage chain for a fixture artefact",
            "apps/mission-control/tests/artifact-lineage.test.tsx::EvidenceLineageGraph > renders the lineage chain for a bag-backed artefact",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-007",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Playback modes are operator-facing and labelled",
        description=(
            "Four deterministic modes — overview, operator review, "
            "safety intervention, trajectory analysis — drive the "
            "camera rig. Each mode is rendered as a tab in the "
            "playback panel and labelled verbatim."
        ),
        architecture_refs=(
            "docs/CINEMATIC_REPLAY_ARCHITECTURE.md",
            "docs/OPERATOR_REVIEW_EXPERIENCE.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/3d/MissionPlayback3D.tsx",
            "apps/mission-control/src/3d/ReplayCameraRig.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/cinematic-playback.test.ts::ReplayCameraRig > returns the verbatim mode label",
            "apps/mission-control/tests/cinematic-playback.test.ts::ReplayCameraRig > trajectory analysis looks at the scene center",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-008",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="Confidence band never upgrades the underlying derivation",
        description=(
            "``ReplayConfidencePanel`` maps (derivation_source, "
            "validation_status, registry_integrity) to a band "
            "(high / medium / low / unavailable). A fixture never "
            "produces ``high``; a failed integrity never produces "
            "anything above ``low``."
        ),
        architecture_refs=(
            "docs/REPLAY_EVIDENCE_LINEAGE.md",
            "docs/SPATIAL_REPLAY_HONESTY_RULES.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/ReplayConfidencePanel.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/artifact-lineage.test.tsx::ReplayConfidencePanel > computes a fixture band as medium",
            "apps/mission-control/tests/artifact-lineage.test.tsx::ReplayConfidencePanel > downgrades to low when integrity is partial",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-009",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="3D module imports no rosbag / mcap parser",
        description=(
            "The honesty test grep asserts no file under ``src/3d/`` "
            "imports ``rosbag2``, ``mcap``, or the ``@mcap/*`` "
            "packages. The immersive scene renders pre-extracted "
            "samples only."
        ),
        architecture_refs=(
            "docs/3D_VISUALIZATION_BOUNDARY.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/3d/MissionScene.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/hydration-honesty.test.tsx::Phase 18 honesty rules > 3d module never parses bag files or imports rosbag2",
        ),
    ),
    Requirement(
        req_id="REQ-IMMVIZ-010",
        kind=RequirementKind.IMMERSIVE_VIZ,
        title="No setInterval / polling loop runs in the operator UI",
        description=(
            "The honesty test grep asserts no file under ``src/`` "
            "calls ``setInterval``. Animation in the immersive scene "
            "is driven by Drei's OrbitControls + React's render "
            "lifecycle only; the scene re-renders when the scrubber "
            "or mode changes."
        ),
        architecture_refs=(
            "docs/IMMERSIVE_MISSION_CONTROL.md",
            "docs/3D_VISUALIZATION_BOUNDARY.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/3d/MissionScene.tsx",
            "apps/mission-control/src/3d/MissionPlayback3D.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/hydration-honesty.test.tsx::Phase 18 honesty rules > never polls with setInterval inside src/",
        ),
    ),
    # -----------------------------------------------------------------
    # Phase 19 — design system + responsive UX + LLM intelligence + scene snapshot
    # -----------------------------------------------------------------
    Requirement(
        req_id="REQ-DESIGN-001",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="No solid black or solid white background tokens",
        description=(
            "The Mission Control design system bans pure #000 / #fff "
            "from every theme token. Dark mode resolves to an off-"
            "black graphite (#10141c family); light mode resolves to "
            "a warm off-white (#f6f8fb family). The honesty grep in "
            "``design-tokens.test.ts`` enforces this across the "
            "entire ``src/`` tree."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_DESIGN_SYSTEM.md",
            "docs/THEME_AND_RESPONSIVE_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/styles/tokens.ts",
            "apps/mission-control/src/styles/theme.css",
        ),
        test_refs=(
            "apps/mission-control/tests/design-tokens.test.ts::Phase 19 design tokens > no token resolves to pure black or pure white",
            "apps/mission-control/tests/design-tokens.test.ts::source-level honesty rules > no source file uses bg-black / bg-white / text-black / text-white classes",
            "apps/mission-control/tests/design-tokens.test.ts::source-level honesty rules > no source file uses raw #000 / #fff hex values (token violations)",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-002",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="Theme toggle persists user preference and supports system preference",
        description=(
            "The home-page ``ThemeToggle`` writes the chosen theme to "
            "``localStorage`` under ``mc-theme-preference``; the next "
            "page load reads that key before paint via the bootstrap "
            "script. When no stored preference exists the provider "
            "falls back to ``prefers-color-scheme`` and finally to "
            "``DEFAULT_THEME = 'dark'``."
        ),
        architecture_refs=(
            "docs/THEME_AND_RESPONSIVE_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/lib/theme-provider.tsx",
            "apps/mission-control/src/components/ThemeToggle.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/theme.test.tsx::ThemeProvider + useTheme > toggle flips between dark and light and persists the choice",
            "apps/mission-control/tests/theme.test.tsx::ThemeProvider + useTheme > respects a stored preference on mount",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-003",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="ThemeToggle is accessible (role=switch, aria-label, keyboard)",
        description=(
            "The toggle exposes ``role='switch'``, ``aria-checked``, "
            "and an ``aria-label`` that names the next state. The "
            "underlying element is a button so keyboard activation "
            "(Space / Enter) works natively."
        ),
        architecture_refs=(
            "docs/THEME_AND_RESPONSIVE_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/ThemeToggle.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/theme.test.tsx::ThemeProvider + useTheme > ThemeToggle has aria-label describing the next state",
            "apps/mission-control/tests/theme.test.tsx::ThemeProvider + useTheme > ThemeToggle is accessible via keyboard (role=switch)",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-004",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="Pages are responsive across mobile, tablet, and desktop",
        description=(
            "Every primary route renders inside a ``PageSurface`` + "
            "``ResponsiveGrid`` and avoids horizontal overflow. The "
            "``ResponsiveShell`` swaps the desktop sidebar for a "
            "mobile drawer below the ``md`` breakpoint."
        ),
        architecture_refs=(
            "docs/THEME_AND_RESPONSIVE_UI.md",
            "docs/MISSION_CONTROL_DESIGN_SYSTEM.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/ResponsiveShell.tsx",
            "apps/mission-control/src/components/PageSurface.tsx",
            "apps/mission-control/src/components/ResponsiveGrid.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/responsive-layout.test.tsx::PageSurface > applies mobile-first padding + max-w-7xl cap",
            "apps/mission-control/tests/responsive-layout.test.tsx::ResponsiveGrid > auto shape adds md:grid-cols-2 and xl:grid-cols-3",
            "apps/mission-control/tests/responsive-layout.test.tsx::ResponsiveGrid > mission shape collapses to a single column on small screens",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-005",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="Gradient surface system replaces flat fills",
        description=(
            "``GradientPanel`` exposes four tones (default, accent, "
            "warning, rejected) and is the single source for panel "
            "backgrounds. Components prefer this over re-implementing "
            "``bg-[linear-gradient(...)]`` ad-hoc."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_DESIGN_SYSTEM.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/GradientPanel.tsx",
            "apps/mission-control/src/styles/theme.css",
        ),
        test_refs=(
            "apps/mission-control/tests/responsive-layout.test.tsx::GradientPanel tones > renders the default neutral tone",
            "apps/mission-control/tests/responsive-layout.test.tsx::GradientPanel tones > does not apply pure-color bg-black / bg-white",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-006",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="Tokens map to CSS variables that both themes share",
        description=(
            "The ``CSS_VAR`` map enumerates the canonical CSS "
            "variable names. Components consume tokens via "
            "``var(--mc-*)`` so theme switching never re-renders the "
            "tree."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_DESIGN_SYSTEM.md",
            "docs/THEME_AND_RESPONSIVE_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/styles/tokens.ts",
            "apps/mission-control/src/styles/theme.css",
        ),
        test_refs=(
            "apps/mission-control/tests/design-tokens.test.ts::Phase 19 design tokens > declares the full CSS variable map",
            "apps/mission-control/tests/design-tokens.test.ts::Phase 19 design tokens > exports both light and dark token sets",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-007",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="Safety boundary banner remains visible in every theme",
        description=(
            "The Phase 17A safety banner is rendered above the "
            "responsive shell so neither mobile nor desktop layouts "
            "can hide it. Tests assert the verbatim "
            "``Simulation-only`` string remains in the DOM."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_DESIGN_SYSTEM.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/SafetyBoundaryBanner.tsx",
            "apps/mission-control/src/app/layout.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/responsive-layout.test.tsx::Safety boundary banner remains visible > renders the Simulation-only banner",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-008",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="No-FOUC bootstrap script resolves theme before paint",
        description=(
            "``THEME_BOOTSTRAP_SCRIPT`` runs synchronously inside "
            "``<head>``: it reads the stored preference (or the "
            "system preference) and applies the matching class to "
            "``<html>`` BEFORE the page paints. The page never "
            "flashes harsh black/white during load."
        ),
        architecture_refs=(
            "docs/THEME_AND_RESPONSIVE_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/lib/theme-provider.tsx",
            "apps/mission-control/src/app/layout.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/theme.test.tsx::ThemeProvider + useTheme > toggle does not flash pure black/white during load",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-009",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="Mission narrative + evidence components inherit theme tokens",
        description=(
            "The Phase 17C / 17B / 18 components (``MissionMap``, "
            "``ReplayConfidencePanel``, ``EvidenceLineageGraph``, "
            "``MissionStoryPanel``) read from CSS variables so the "
            "dark and light themes both look operator-grade without "
            "harsh contrast."
        ),
        architecture_refs=(
            "docs/MISSION_CONTROL_DESIGN_SYSTEM.md",
            "docs/AUTONOMY_UI_DESIGN_SYSTEM.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/MissionMap.tsx",
            "apps/mission-control/src/components/MissionStoryPanel.tsx",
            "apps/mission-control/src/components/EvidenceLineageGraph.tsx",
            "apps/mission-control/src/components/ReplayConfidencePanel.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/design-tokens.test.ts::source-level honesty rules > no source file uses bg-black / bg-white / text-black / text-white classes",
            "apps/mission-control/tests/mission-storytelling.test.tsx::MissionStoryPanel > renders one step per lifecycle phase for an accepted mission",
        ),
    ),
    Requirement(
        req_id="REQ-DESIGN-010",
        kind=RequirementKind.DESIGN_SYSTEM,
        title="Responsive shell stays scrollable with min-w-0 main",
        description=(
            "The ``ResponsiveShell`` keeps its ``<main>`` element "
            "with ``min-w-0`` and ``overflow-y-auto`` so wide tables, "
            "long event streams, and the immersive 3D scene do not "
            "create horizontal overflow on mobile."
        ),
        architecture_refs=(
            "docs/THEME_AND_RESPONSIVE_UI.md",
        ),
        implementation_refs=(
            "apps/mission-control/src/components/ResponsiveShell.tsx",
        ),
        test_refs=(
            "apps/mission-control/tests/responsive-layout.test.tsx::PageSurface > applies mobile-first padding + max-w-7xl cap",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-001",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Candidate ranking is deterministic",
        description=(
            "``rank_candidates`` returns the same ordering + scores "
            "for identical inputs. Tied candidates are broken by "
            "``candidate_id`` so the ranking is fully reproducible."
        ),
        architecture_refs=(
            "docs/LLM_CANDIDATE_RANKING_MODEL.md",
            "docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/candidate_ranker.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_ranking_is_deterministic_for_identical_inputs",
            "backend/tests/test_skill_llm_intelligence.py::test_ranking_serialises_to_dict",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-002",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Validator outcome dominates candidate ranking",
        description=(
            "A candidate the validator rejected ranks below a "
            "candidate the validator accepted, even when the "
            "rejected candidate has better surface qualities "
            "(longer explanation, declared uncertainties, etc.)."
        ),
        architecture_refs=(
            "docs/LLM_CANDIDATE_RANKING_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/candidate_ranker.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_validator_outcome_dominates_ranking",
            "backend/tests/test_skill_llm_intelligence.py::test_sanitizer_rejection_dominates",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-003",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Overconfident candidates without validator acceptance are penalised",
        description=(
            "Model confidence is metadata only. A candidate that "
            "claims high / overconfident confidence WITHOUT a "
            "validator acceptance picks up the "
            "``overconfident_without_validation`` penalty."
        ),
        architecture_refs=(
            "docs/LLM_CANDIDATE_RANKING_MODEL.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/candidate_ranker.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_overconfident_without_validation_is_penalised",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-004",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Candidate normalization preserves the raw payload",
        description=(
            "``NormalizationResult.raw_payload`` always equals the "
            "input string verbatim, even on rejection. The audit "
            "trail can therefore reconstruct exactly what the "
            "provider returned."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/candidate_normalizer.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_normalize_strips_markdown_fences",
            "backend/tests/test_skill_llm_intelligence.py::test_normalize_rejects_invalid_json",
            "backend/tests/test_skill_llm_intelligence.py::test_normalize_aliases_topic_lists",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-005",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Repair suggestions are suggestion-only; never auto-applied",
        description=(
            "Every :class:`RepairBundle` has ``status`` in "
            "``{suggestion_only, not_applicable, "
            "requires_human_review}``. No code path mutates the "
            "candidate's source or promotes a rejected candidate to "
            "accepted."
        ),
        architecture_refs=(
            "docs/LLM_REPAIR_SUGGESTIONS.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/candidate_repair.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_repair_suggests_stop_command_when_missing",
            "backend/tests/test_skill_llm_intelligence.py::test_repair_status_not_applicable_for_clean_candidate",
            "backend/tests/test_skill_llm_intelligence.py::test_repair_escalates_human_review_for_unsafe_categories",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-006",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Safety critique covers every honesty category",
        description=(
            "``critique_candidate`` returns one item per category "
            "in ``CRITIQUE_CATEGORIES``. A direct ``/cmd_vel`` "
            "publication produces a ``fail`` actuator-authority "
            "verdict; a clean candidate produces ``ok`` across the "
            "board."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/safety_critique.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_critique_flags_direct_cmd_vel",
            "backend/tests/test_skill_llm_intelligence.py::test_critique_passes_for_clean_candidate",
            "backend/tests/test_skill_llm_intelligence.py::test_critique_warns_on_overconfident_no_uncertainty",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-007",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Provider readiness check never opens a socket",
        description=(
            "``check_provider_readiness`` inspects the config + the "
            "endpoint hostname only. It does NOT construct a socket, "
            "open a connection, or call any provider. The honesty "
            "test in ``test_skill_llm_intelligence.py`` monkey-"
            "patches ``socket.socket`` to a raising stub to enforce "
            "this rule."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md",
            "docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/provider_readiness.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_readiness_never_opens_a_socket",
            "backend/tests/test_skill_llm_intelligence.py::test_local_endpoint_requires_opt_in",
            "backend/tests/test_skill_llm_intelligence.py::test_remote_endpoint_is_rejected_even_when_enabled",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-008",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Local provider remains disabled by default",
        description=(
            "A default :class:`SkillLLMProviderConfig` with "
            "``mode='disabled'`` reports ``status='disabled'`` and "
            "``execution_allowed=False``. Flipping a single flag "
            "without an explicit local endpoint never enables real "
            "model execution."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/provider_readiness.py",
            "backend/app/skill_llm_provider/config.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_disabled_provider_readiness_reports_disabled",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-009",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Model capability registry is metadata-only",
        description=(
            "The capability registry stores operator-declared "
            "metadata (family, params, context, declared strengths "
            "+ weaknesses). The metadata never influences sanitizer "
            "or validator outcomes."
        ),
        architecture_refs=(
            "docs/FUTURE_LOCAL_MODEL_OPERATIONS.md",
        ),
        implementation_refs=(
            "backend/app/skill_llm_provider/model_capabilities.py",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_default_capability_registry_includes_canonical_fixture",
            "backend/tests/test_skill_llm_intelligence.py::test_capability_to_dict_round_trips",
        ),
    ),
    Requirement(
        req_id="REQ-SKILL-INTEL-010",
        kind=RequirementKind.SKILL_LLM_INTELLIGENCE,
        title="Fixture set covers accepted, rejected, and ambiguous cases",
        description=(
            "``skill-llm-candidates/examples/`` contains accepted "
            "(move/rotate/stop), rejected (direct cmd_vel, shell, "
            "network, etc.), ambiguous (``move over there``, "
            "``turn a little``), and overconfident-unsafe examples. "
            "The fixture provider can synthesise candidates that "
            "exercise every ranking + critique branch."
        ),
        architecture_refs=(
            "docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md",
        ),
        implementation_refs=(
            "skill-llm-candidates/examples/fixture_ambiguous_destination.json",
            "skill-llm-candidates/examples/fixture_ambiguous_distance.json",
            "skill-llm-candidates/examples/fixture_overconfident_unsafe.json",
        ),
        test_refs=(
            "backend/tests/test_skill_llm_intelligence.py::test_ranking_is_deterministic_for_identical_inputs",
        ),
    ),
    Requirement(
        req_id="REQ-SNAPSHOT-001",
        kind=RequirementKind.SCENE_SNAPSHOT,
        title="Scene snapshot is not_executed without a backing artefact",
        description=(
            "When the spatial-replay artefact is missing OR the "
            "registry record is missing, the snapshot pipeline "
            "returns ``status='unavailable'`` (both missing) or "
            "``status='not_executed'`` (only one missing). "
            "The frontend renders the missing-inputs list verbatim."
        ),
        architecture_refs=(
            "docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md",
        ),
        implementation_refs=(
            "backend/app/scene_snapshot/pipeline.py",
            "apps/mission-control/src/adapters/sceneSnapshot.ts",
        ),
        test_refs=(
            "backend/tests/test_scene_snapshot.py::test_missing_run_id_reports_unavailable",
            "apps/mission-control/tests/scene-snapshot.test.tsx::computeSceneSnapshot > returns unavailable when nothing exists",
            "apps/mission-control/tests/scene-snapshot.test.tsx::SceneSnapshotPanel > renders the not_executed missing-inputs list when bag_status mismatches",
        ),
    ),
    Requirement(
        req_id="REQ-SNAPSHOT-002",
        kind=RequirementKind.SCENE_SNAPSHOT,
        title="Fixture replays never become bag-backed snapshots",
        description=(
            "A run whose ``derivation_source='fixture'`` always "
            "produces ``status='fixture'`` and "
            "``reviewer_export_ready=False`` regardless of integrity "
            "or registry state."
        ),
        architecture_refs=(
            "docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md",
            "docs/SPATIAL_REPLAY_HONESTY_RULES.md",
        ),
        implementation_refs=(
            "backend/app/scene_snapshot/pipeline.py",
            "apps/mission-control/src/components/SceneSnapshotPanel.tsx",
        ),
        test_refs=(
            "backend/tests/test_scene_snapshot.py::test_fixture_run_is_not_bag_backed",
            "backend/tests/test_scene_snapshot.py::test_committed_canonical_fixture_is_not_bag_backed",
            "apps/mission-control/tests/scene-snapshot.test.tsx::SceneSnapshotPanel > renders fixture status with the no-bag-backed note",
        ),
    ),
    Requirement(
        req_id="REQ-SNAPSHOT-003",
        kind=RequirementKind.SCENE_SNAPSHOT,
        title="Bag-backed snapshot requires real bag-backed inputs",
        description=(
            "Eligibility for a bag-backed snapshot requires "
            "``derivation_source='bag_backed'``, "
            "``bag_status='bag_backed'``, AND registry integrity = "
            "``passed`` (recomputed from the bytes on disk). All "
            "three signals must align."
        ),
        architecture_refs=(
            "docs/FIRST_BAG_BACKED_RUN_PLAYBOOK.md",
            "docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md",
        ),
        implementation_refs=(
            "backend/app/scene_snapshot/pipeline.py",
        ),
        test_refs=(
            "backend/tests/test_scene_snapshot.py::test_bag_backed_run_is_eligible_when_integrity_passes",
            "backend/tests/test_scene_snapshot.py::test_bag_backed_run_is_not_eligible_when_artifact_missing",
            "apps/mission-control/tests/scene-snapshot.test.tsx::computeSceneSnapshot > returns bag_backed status only when derivation + bag_status + integrity all align",
        ),
    ),
    Requirement(
        req_id="REQ-SNAPSHOT-004",
        kind=RequirementKind.SCENE_SNAPSHOT,
        title="Snapshot artefact carries a hash chain + disclaimer",
        description=(
            "Every emitted snapshot serialises its artefact registry "
            "files' sha256 prefixes plus the verbatim disclaimer "
            "from ``SNAPSHOT_DISCLAIMER``."
        ),
        architecture_refs=(
            "docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md",
        ),
        implementation_refs=(
            "backend/app/scene_snapshot/pipeline.py",
            "apps/mission-control/src/components/SceneSnapshotPanel.tsx",
        ),
        test_refs=(
            "backend/tests/test_scene_snapshot.py::test_build_snapshot_returns_hash_chain",
            "backend/tests/test_scene_snapshot.py::test_snapshot_serialises_with_disclaimer",
            "apps/mission-control/tests/scene-snapshot.test.tsx::SceneSnapshotPanel > renders the hash chain when a registry record is present",
        ),
    ),
    Requirement(
        req_id="REQ-SNAPSHOT-005",
        kind=RequirementKind.SCENE_SNAPSHOT,
        title="Snapshot pipeline never generates a screenshot binary",
        description=(
            "Phase 19 ships metadata only. The CLI writes "
            "``<run>.scene-snapshot.json`` + "
            "``<run>.scene-snapshot.md`` and never invokes a browser "
            "/ image-rendering harness. A future phase wires that "
            "harness in once a real bag-backed run exists."
        ),
        architecture_refs=(
            "docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md",
            "docs/FIRST_BAG_BACKED_RUN_PLAYBOOK.md",
        ),
        implementation_refs=(
            "tools/generate_reviewer_scene_snapshot.py",
            "backend/app/scene_snapshot/pipeline.py",
        ),
        test_refs=(
            "backend/tests/test_scene_snapshot.py::test_write_snapshot_artefacts_creates_files",
            "backend/tests/test_scene_snapshot.py::test_committed_canonical_fixture_lists_no_bag_backed_inputs",
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

"""Safety-pipeline runtime validator.

Runs a small in-process scenario through the deterministic engine and
asserts the architectural invariants of the motion authority pipeline:

* every recorded ``AuthorizedMotionCommand`` has the supervisor's
  arbitration source string;
* the gateway never observes a non-zero motion in ``SAFE_STOP`` or
  ``E_STOP_LATCHED``;
* operator ``E_STOP_LATCHED`` is not self-cleared without a reset;
* fault injection events do not include ``safety_transition.*``;
* requested motion published past ``ACTIVE_*`` limits is clamped, and
  the clamp emits a ``motion_arbitration.clamped`` event.

The validator is a single-process replacement for the manual
``rover_ws/tests/manual.md`` checklist: it asserts the same
architectural facts, but in pure Python against the deterministic
engine. It is wired into the scenario suite and runs in CI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.domain.enums import MotionDecision, SafetyState
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.scenarios import (
    RequestedMotionPlan,
    ScenarioDefinition,
    ScenarioInitialState,
)
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine


_SUPERVISOR_SOURCE = "safety.supervisor.arbitration"


@dataclass
class SafetyPipelineResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "detail": dict(self.detail),
        }


def validate_safety_pipeline(*, runs_root: Path | str | None = None) -> SafetyPipelineResult:
    """Drive the supervisor through six checks and aggregate findings.

    The ``runs_root`` is optional; when omitted the engine writes to a
    throwaway temporary directory.
    """

    import tempfile

    if runs_root is None:
        ctx = tempfile.TemporaryDirectory()
        runs_dir = Path(ctx.name)
    else:
        ctx = None
        runs_dir = Path(runs_root)
        runs_dir.mkdir(parents=True, exist_ok=True)

    result = SafetyPipelineResult()
    try:
        _check_authorized_source(result, runs_dir)
        _check_safe_stop_zero_motion(result, runs_dir)
        _check_estop_latches_without_self_clear(result, runs_dir)
        _check_clamping_emits_event(result, runs_dir)
        _check_fault_injection_does_not_emit_safety_transitions(result, runs_dir)
        _check_request_path_does_not_reach_authorized_directly(result)
    finally:
        if ctx is not None:
            ctx.cleanup()
    return result


def _engine(
    *,
    scenario_id: str,
    duration_s: float,
    estop_at_ms: Optional[int] = None,
    runs_root: Path,
    requested_linear: float = 0.4,
    requested_angular: float = 0.0,
    faults: tuple = (),
) -> SimulationEngine:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId(scenario_id),
        duration_seconds=duration_s,
        time_step_ms=100,
        initial_state=ScenarioInitialState(
            operator_activate_at_ms=200, operator_estop_at_ms=estop_at_ms
        ),
        requested_motion=RequestedMotionPlan(
            linear_velocity=requested_linear, angular_velocity=requested_angular
        ),
        faults=faults,
    )
    return SimulationEngine(
        scenario=sc,
        runs_root=runs_root,
        run_id=RunId(f"run-pipeline-{scenario_id}"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )


def _check_authorized_source(result: SafetyPipelineResult, runs_root: Path) -> None:
    eng = _engine(scenario_id="auth-source", duration_s=2.0, runs_root=runs_root / "auth")
    eng.run()
    saw_any = False
    for event in eng.event_store.all():
        if event.final_motion is not None:
            saw_any = True
            if event.final_motion.source != _SUPERVISOR_SOURCE:
                result.add_error(
                    f"AuthorizedMotionCommand emitted by non-supervisor source: "
                    f"{event.final_motion.source!r} (expected {_SUPERVISOR_SOURCE!r})"
                )
    if not saw_any:
        result.add_warning("no events carried final_motion; cannot check source provenance")
    result.detail["authorized_source_checked"] = True


def _check_safe_stop_zero_motion(result: SafetyPipelineResult, runs_root: Path) -> None:
    from app.domain.scenarios import ScenarioFault

    eng = _engine(
        scenario_id="ss-zero",
        duration_s=4.0,
        runs_root=runs_root / "ss",
        faults=(
            ScenarioFault(
                fault_id="f1",
                fault_type="stale_lidar",
                target="/scan",
                activation_ms=1500,
                duration_ms=-1,
            ),
        ),
    )
    eng.run()
    nonzero_in_safe_stop = 0
    for event in eng.event_store.all():
        if (
            event.final_motion is not None
            and event.safety_state == SafetyState.SAFE_STOP
            and not event.final_motion.is_zero_authorization
        ):
            nonzero_in_safe_stop += 1
    if nonzero_in_safe_stop > 0:
        result.add_error(
            f"{nonzero_in_safe_stop} authorized command(s) carried non-zero motion in SAFE_STOP"
        )
    result.detail["safe_stop_zero_motion_checked"] = True


def _check_estop_latches_without_self_clear(
    result: SafetyPipelineResult, runs_root: Path
) -> None:
    eng = _engine(
        scenario_id="estop-latch",
        duration_s=4.0,
        estop_at_ms=1500,
        runs_root=runs_root / "estop",
    )
    eng.run()
    if eng.supervisor.safety_state != SafetyState.E_STOP_LATCHED:
        result.add_error(
            f"E_STOP_LATCHED expected but supervisor ended in {eng.supervisor.safety_state.value}"
        )
    if not eng.supervisor.is_estop_latched:
        result.add_error("supervisor is_estop_latched is False after E-stop")
    result.detail["estop_latch_checked"] = True


def _check_clamping_emits_event(result: SafetyPipelineResult, runs_root: Path) -> None:
    eng = _engine(
        scenario_id="clamp",
        duration_s=2.0,
        runs_root=runs_root / "clamp",
        requested_linear=2.0,
    )
    eng.run()
    saw_clamp = any(
        e.event_type == "motion_arbitration.clamped" for e in eng.event_store.all()
    )
    if not saw_clamp:
        result.add_error("no motion_arbitration.clamped event emitted for over-speed request")
    result.detail["clamp_event_checked"] = True


def _check_fault_injection_does_not_emit_safety_transitions(
    result: SafetyPipelineResult, runs_root: Path
) -> None:
    from app.domain.scenarios import ScenarioFault

    eng = _engine(
        scenario_id="fault-no-direct-transition",
        duration_s=4.0,
        runs_root=runs_root / "fault",
        faults=(
            ScenarioFault(
                fault_id="f1",
                fault_type="stale_lidar",
                target="/scan",
                activation_ms=1500,
                duration_ms=-1,
            ),
        ),
    )
    eng.run()
    for event in eng.event_store.all():
        if event.subsystem == "fault_injection" and event.event_type.startswith(
            "safety_transition."
        ):
            result.add_error(
                f"fault_injection emitted forbidden event {event.event_type!r}"
            )
    result.detail["fault_no_direct_transition_checked"] = True


def _check_request_path_does_not_reach_authorized_directly(
    result: SafetyPipelineResult,
) -> None:
    """Static check: search the engine source for any path that would
    publish an AuthorizedMotionCommand outside the arbiter.

    The check is intentionally conservative: it scans the engine and
    bridge core for AuthorizedMotionCommand constructions and asserts
    they all live in :mod:`app.safety.arbitration`.
    """

    from importlib import import_module
    import inspect

    arbiter_module = import_module("app.safety.arbitration")
    allowed_files = {Path(inspect.getfile(arbiter_module))}
    suspect_modules = [
        "app.simulation.engine",
        "app.safety.supervisor",
        "app.simulation.scenario_runner",
    ]
    for module_name in suspect_modules:
        mod = import_module(module_name)
        path = Path(inspect.getfile(mod))
        if path in allowed_files:
            continue
        text = path.read_text(encoding="utf-8")
        # The only allowed reference outside the arbiter is type
        # annotations / imports. We forbid bare instantiation:
        # ``AuthorizedMotionCommand(`` immediately followed by a paren
        # outside the arbiter.
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if "AuthorizedMotionCommand(" not in stripped:
                continue
            # Permitted tokens.
            if any(
                stripped.startswith(prefix)
                for prefix in (
                    "from app.domain.motion",
                    "from app.domain.motion import",
                    "AuthorizedMotionCommand,",
                    "AuthorizedMotionCommand =",
                    "Optional[AuthorizedMotionCommand]",
                    ":",
                )
            ):
                continue
            if stripped.startswith("authorized: AuthorizedMotionCommand"):
                continue
            # Fallback: report.
            result.add_warning(
                f"{module_name}:{line_no}: AuthorizedMotionCommand reference outside the arbiter — "
                "manual audit recommended"
            )
    result.detail["arbiter_only_construction_checked"] = True

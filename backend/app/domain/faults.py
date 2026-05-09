"""Fault models used by the fault injection subsystem.

Fault profiles describe *what* a fault does. The runtime state is held
separately so the profile itself remains a value object.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any, Optional

from app.domain.enums import FaultStatus, FaultType


@dataclass(frozen=True, slots=True)
class FaultProfile:
    """Declarative description of a fault to inject during a scenario.

    ``activation_ms`` is the simulator time at which the fault transitions
    from ``ARMED`` to ``FIRED``. ``duration_ms`` defines how long it stays
    fired before transitioning to ``CLEARED``. Set ``duration_ms`` to a
    negative value to mean "until end of scenario".
    """

    fault_id: str
    fault_type: FaultType
    target: str
    activation_ms: int
    duration_ms: int
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.fault_id:
            raise ValueError("fault_id must be non-empty")
        if not self.target:
            raise ValueError("target must be non-empty")
        if self.activation_ms < 0:
            raise ValueError("activation_ms must be non-negative")
        if math.isnan(self.activation_ms):  # pragma: no cover - defensive
            raise ValueError("activation_ms must be a number")

    @property
    def runs_until_end_of_scenario(self) -> bool:
        return self.duration_ms < 0

    def expected_clear_ms(self, scenario_duration_ms: int) -> int:
        """When this fault is expected to clear in scenario time."""
        if self.runs_until_end_of_scenario:
            return scenario_duration_ms
        return self.activation_ms + self.duration_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_id": self.fault_id,
            "fault_type": self.fault_type.value,
            "target": self.target,
            "activation_ms": self.activation_ms,
            "duration_ms": self.duration_ms,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True, slots=True)
class FaultRuntimeState:
    """Current lifecycle state of a fault during a run."""

    profile: FaultProfile
    status: FaultStatus = FaultStatus.CONFIGURED
    fired_at_ms: Optional[int] = None
    cleared_at_ms: Optional[int] = None

    def transition(self, *, new_status: FaultStatus, now_ms: int) -> "FaultRuntimeState":
        if new_status == FaultStatus.FIRED and self.status not in {FaultStatus.ARMED, FaultStatus.CONFIGURED}:
            raise ValueError(f"Cannot transition fault {self.profile.fault_id} to FIRED from {self.status}")
        if new_status == FaultStatus.CLEARED and self.status != FaultStatus.FIRED:
            raise ValueError(
                f"Cannot transition fault {self.profile.fault_id} to CLEARED from {self.status}"
            )
        if new_status == FaultStatus.ARMED and self.status != FaultStatus.CONFIGURED:
            raise ValueError(
                f"Cannot transition fault {self.profile.fault_id} to ARMED from {self.status}"
            )
        return replace(
            self,
            status=new_status,
            fired_at_ms=now_ms if new_status == FaultStatus.FIRED else self.fired_at_ms,
            cleared_at_ms=now_ms if new_status == FaultStatus.CLEARED else self.cleared_at_ms,
        )

    @property
    def is_active(self) -> bool:
        return self.status == FaultStatus.FIRED

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict(),
            "status": self.status.value,
            "fired_at_ms": self.fired_at_ms,
            "cleared_at_ms": self.cleared_at_ms,
        }

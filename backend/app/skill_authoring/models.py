"""Dataclasses, status enums, and the verbatim disclaimer.

The platform is **not safety-certified**. Every status enum and
dataclass is exposed via :mod:`app.skill_authoring` so callers do
not have to reach into private modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional


SKILL_AUTHORING_VERSION: str = "phase15a-1"

SKILL_AUTHORING_DISCLAIMER: str = (
    "This generated skill is an engineering development aid. It "
    "does not represent autonomous execution, safety certification, "
    "or regulatory approval."
)


# ---------------------------------------------------------------------
# Skill type catalog. Adding to this enum is a deliberate change.
# ---------------------------------------------------------------------


class SkillType(str, Enum):
    MOVE_FORWARD_DISTANCE = "move_forward_distance"
    ROTATE_DEGREES = "rotate_degrees"
    STOP_IMMEDIATELY = "stop_immediately"
    PUBLISH_REQUESTED_MOTION = "publish_requested_motion"
    KEYBOARD_FORWARD_BINDING = "keyboard_forward_binding"
    CONTROLLER_BUTTON_BINDING = "controller_button_binding"
    WAYPOINT_REQUEST = "waypoint_request"
    PATROL_ROUTE_TEMPLATE = "patrol_route_template"
    SAFE_STOP_WRAPPER = "safe_stop_wrapper"


SKILL_TYPES: tuple[str, ...] = tuple(s.value for s in SkillType)


# ---------------------------------------------------------------------
# Output languages.
# ---------------------------------------------------------------------


class SkillLanguage(str, Enum):
    PYTHON_ROS2 = "python_ros2"
    PSEUDO_CODE = "pseudo_code"
    CPP_ROS2 = "cpp_ros2"


SKILL_LANGUAGES: tuple[str, ...] = tuple(s.value for s in SkillLanguage)


# ---------------------------------------------------------------------
# Statuses + risk bands.
# ---------------------------------------------------------------------


class SkillGenerationStatus(str, Enum):
    GENERATED = "generated"
    REJECTED = "rejected"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"
    VALIDATION_FAILED = "validation_failed"


SKILL_GENERATION_STATUSES: tuple[str, ...] = tuple(
    s.value for s in SkillGenerationStatus
)


class SkillSafetyStatus(str, Enum):
    SAFE_TEMPLATE = "safe_template"
    GUARDED = "guarded"
    UNSAFE_REJECTED = "unsafe_rejected"
    NEEDS_REVIEW = "needs_review"


class SkillRiskBand(str, Enum):
    LOW = "low"
    GUARDED = "guarded"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class SkillRejectionReason(str, Enum):
    DIRECT_ACTUATOR_COMMAND = "direct_actuator_command"
    SAFETY_OVERRIDE = "safety_override"
    ESTOP_OVERRIDE = "estop_override"
    UNBOUNDED_MOTION = "unbounded_motion"
    UNBOUNDED_SPEED = "unbounded_speed"
    SHELL_OR_CODE_EXECUTION = "shell_or_code_execution"
    DIRECT_MOTOR_CONTROL = "direct_motor_control"
    SENSOR_DISABLE = "sensor_disable"
    NETWORK_ACCESS = "network_access"
    UNSUPPORTED_INSTRUCTION = "unsupported_instruction"
    AMBIGUOUS_REQUEST = "ambiguous_request"
    UNKNOWN_LOCATION = "unknown_location"
    OUT_OF_RANGE_PARAMETER = "out_of_range_parameter"


# ---------------------------------------------------------------------
# Models.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SkillDiagnostic:
    code: str
    severity: str  # "info" | "warning" | "rejection"
    message: str
    parameter: str = ""


@dataclass(frozen=True)
class SkillParameter:
    name: str
    value: object
    units: str = ""


@dataclass(frozen=True)
class SkillAuthoringRequest:
    request_id: str
    text: str
    language: str  # SkillLanguage value
    requested_at_utc: str = ""


@dataclass(frozen=True)
class SkillTemplate:
    skill_type: str  # SkillType value
    language: str  # SkillLanguage value
    title: str
    subtitle: str
    required_parameters: tuple[str, ...]
    default_parameters: Mapping[str, object]
    safety_constraints: tuple[str, ...]
    generated_topics: tuple[str, ...]
    forbidden_topics: tuple[str, ...]
    timeout_required: bool
    stop_command_required: bool
    risk_band: str  # SkillRiskBand value
    review_notes: tuple[str, ...]


@dataclass(frozen=True)
class SkillCandidate:
    """One parser result.

    A candidate may either point at a supported template (``status =
    generated``) or carry a rejection / ambiguity diagnosis.
    """

    skill_type: Optional[str]
    parameters: tuple[SkillParameter, ...]
    diagnostics: tuple[SkillDiagnostic, ...]
    status: str  # SkillGenerationStatus value
    rejection_reason: str = ""
    normalised_text: str = ""


@dataclass(frozen=True)
class CodeCard:
    title: str
    subtitle: str
    language: str  # SkillLanguage value
    skill_type: str
    code: str
    line_count: int
    copy_label: str
    safety_badges: tuple[str, ...]
    animation_steps: tuple[str, ...]
    risk_band: str
    diagnostics: tuple[SkillDiagnostic, ...]


@dataclass(frozen=True)
class SkillSafetyReview:
    safety_status: str  # SkillSafetyStatus value
    risk_band: str  # SkillRiskBand value
    allowed_topics: tuple[str, ...]
    forbidden_topics: tuple[str, ...]
    reason_codes: tuple[str, ...]
    human_review_required: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class GeneratedSkill:
    skill_id: str
    skill_type: str  # SkillType value
    language: str  # SkillLanguage value
    title: str
    subtitle: str
    code: str
    parameters: tuple[SkillParameter, ...]
    diagnostics: tuple[SkillDiagnostic, ...]
    code_card: CodeCard
    safety_review: SkillSafetyReview
    generated_at_utc: str
    request_text: str
    normalised_text: str
    disclaimer: str = SKILL_AUTHORING_DISCLAIMER


@dataclass(frozen=True)
class SkillAuditBundle:
    request: SkillAuthoringRequest
    candidate: SkillCandidate
    generated_skill: Optional[GeneratedSkill]
    status: str  # SkillGenerationStatus value
    rejection_reason: str
    diagnostics: tuple[SkillDiagnostic, ...]
    disclaimer: str = SKILL_AUTHORING_DISCLAIMER


@dataclass(frozen=True)
class SkillGenerationResult:
    """Convenience wrapper returned by :func:`generate_skill`."""

    request: SkillAuthoringRequest
    candidate: SkillCandidate
    generated_skill: Optional[GeneratedSkill]
    diagnostics: tuple[SkillDiagnostic, ...]
    status: str
    rejection_reason: str

    @property
    def accepted(self) -> bool:
        return self.status == SkillGenerationStatus.GENERATED.value

"""Declared expectations for the live TF tree.

The list mirrors the URDF declarations in
``rover_ws/src/rover_description/urdf/rover.urdf.xacro`` and the
documented TF tree in
``rover_ws/src/rover_description/urdf/rover.materials.xacro``.

The TF probe asserts the expected parent / child relationships are
present in the live ``tf2`` buffer at runtime. Static-only mode
asserts the equivalent links / joints are present in the URDF.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FrameExpectation:
    name: str
    parent: Optional[str]
    """``None`` for the root frame."""

    is_static: bool
    """True when the transform is fixed (sensor mounts, wheel offsets);
    static transforms must appear on ``/tf_static``. False for
    transforms that the simulator publishes on ``/tf`` continuously
    (the odom -> base_link edge)."""

    required: bool = True


EXPECTED_ROOT_FRAME = "odom"


EXPECTED_FRAMES: tuple[FrameExpectation, ...] = (
    FrameExpectation(name="odom", parent=None, is_static=False),
    FrameExpectation(name="base_footprint", parent="odom", is_static=False),
    FrameExpectation(name="base_link", parent="base_footprint", is_static=True),
    FrameExpectation(name="lidar_link", parent="base_link", is_static=True),
    FrameExpectation(name="imu_link", parent="base_link", is_static=True),
    FrameExpectation(name="contact_link", parent="base_link", is_static=True),
    FrameExpectation(name="left_wheel_link", parent="base_link", is_static=False),
    FrameExpectation(name="right_wheel_link", parent="base_link", is_static=False),
    FrameExpectation(name="caster_link", parent="base_link", is_static=True, required=False),
)

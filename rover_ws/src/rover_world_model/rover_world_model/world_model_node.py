"""ROS 2 world model node.

Subscribes to ``/odom`` (for pose) and ``/scan`` (for forward
clearance), feeds them into :class:`app.world_model.WorldModel`, and
publishes :class:`rover_msgs/WorldModelState` and one
:class:`rover_msgs/HazardReport` per active hazard each tick.

The keepout / restricted-speed / operational-boundary configuration
is loaded from a JSON file at startup. The same JSON shape is used by
the deterministic engine's mission plans so the two paths share a
single declarative source.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from app.domain.enums import SensorStatus, SensorType
from app.domain.sensors import LiDARReading, SensorFrame
from app.world_model.boundaries import OperationalBoundary
from app.world_model.keepout import KeepoutZone, RestrictedZone
from app.world_model.world_model import WorldModel, WorldModelInputs
from rover_msgs.msg import HazardReport, WorldModelState


def _default_allowed_root() -> Path:
    """Return the repository root, used as the allow-list anchor for
    filesystem-path parameters (#19).

    The repo root is computed as the third parent of this module file:
    ``<repo>/rover_ws/src/rover_world_model/rover_world_model/world_model_node.py``.
    """

    return Path(__file__).resolve().parents[4]


def _validated_filepath(
    raw_path: str, *, allowed_root: Path, logger: Any
) -> str:
    """Resolve ``raw_path`` and refuse anything outside ``allowed_root``.

    On rejection: logs at ERROR and raises ``ValueError``. The node's
    ``main`` catches that and exits non-zero (#19).
    """

    p = Path(raw_path).expanduser()
    resolved = p.resolve()
    root_resolved = allowed_root.resolve()
    if not resolved.is_relative_to(root_resolved):
        logger.error(
            "rejected filesystem parameter %r: resolves to %s outside %s"
            % (raw_path, resolved, root_resolved)
        )
        raise ValueError(
            f"path {raw_path!r} resolves outside allowed root {root_resolved}"
        )
    return str(resolved)


class WorldModelNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_world_model")
        self.declare_parameter("run_id", "unknown")
        self.declare_parameter("scenario_id", "unknown")
        self.declare_parameter("zones_path", "")
        self.declare_parameter("evaluation_period_ms", 200)

        # #19: any filesystem-path parameter must resolve under a
        # documented allowed root. Default to the workspace root
        # (parent of the package source tree). A launch with an absolute
        # or traversing zones_path is misconfigured.
        zones_path_raw = str(self.get_parameter("zones_path").value)
        zones_path = _validated_filepath(
            zones_path_raw,
            allowed_root=_default_allowed_root(),
            logger=self.get_logger(),
        ) if zones_path_raw else ""
        keepouts, restricted, boundaries = _load_zones(zones_path) if zones_path else ((), (), ())
        self._world = WorldModel(
            keepouts=keepouts,
            restricted=restricted,
            boundaries=boundaries,
        )
        self._latest_pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._latest_scan: LaserScan | None = None
        self._scan_seq = 0

        self._state_pub = self.create_publisher(
            WorldModelState, "/world_model/state", 10
        )
        self._hazard_pub = self.create_publisher(
            HazardReport, "/world_model/hazards", 50
        )

        self.create_subscription(Odometry, "/odom", self._on_odom, 20)
        self.create_subscription(LaserScan, "/scan", self._on_scan, 10)

        period_s = max(0.05, float(self.get_parameter("evaluation_period_ms").value) / 1000.0)
        self._timer = self.create_timer(period_s, self._tick)
        self.get_logger().info(
            "rover_world_model active. zones=%s",
            zones_path or "<none>",
        )

    def _on_odom(self, msg: Odometry) -> None:
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        self._latest_pose = (
            float(msg.pose.pose.position.x),
            float(msg.pose.pose.position.y),
            yaw,
        )

    def _on_scan(self, msg: LaserScan) -> None:
        self._latest_scan = msg
        self._scan_seq += 1

    def _tick(self) -> None:
        sim_ns = self.get_clock().now().nanoseconds
        frame = self._build_frame()
        snapshot = self._world.update(
            WorldModelInputs(
                pose_x=self._latest_pose[0],
                pose_y=self._latest_pose[1],
                heading_rad=self._latest_pose[2],
                sim_time_ns=sim_ns,
                sensor_frame=frame,
            )
        )
        state = WorldModelState()
        state.stamp = self.get_clock().now().to_msg()
        state.run_id = str(self.get_parameter("run_id").value)
        state.scenario_id = str(self.get_parameter("scenario_id").value)
        state.pose_x = float(snapshot.pose_x)
        state.pose_y = float(snapshot.pose_y)
        state.heading_rad = float(snapshot.heading_rad)
        state.forward_clearance_m = float(snapshot.forward_clearance_m)
        state.forward_sector_clear = bool(snapshot.forward_sector_clear)
        state.inside_keepout = list(snapshot.inside_keepout)
        state.near_keepout = list(snapshot.near_keepout)
        state.inside_restricted_speed = list(snapshot.inside_restricted)
        state.boundary_violations = list(snapshot.boundary_violations)
        state.speed_limit_linear = (
            float(snapshot.speed_limit_linear)
            if snapshot.speed_limit_linear is not None
            else -1.0
        )
        state.speed_limit_angular = (
            float(snapshot.speed_limit_angular)
            if snapshot.speed_limit_angular is not None
            else -1.0
        )
        self._state_pub.publish(state)

        for hazard in self._world.latest_hazards:
            hr = HazardReport()
            hr.stamp = state.stamp
            hr.run_id = state.run_id
            hr.scenario_id = state.scenario_id
            hr.kind = hazard.kind.value
            hr.reason_code = hazard.reason_code
            hr.severity = hazard.severity
            hr.summary = hazard.summary
            zone_id = hazard.attributes.get("zone_id") or hazard.attributes.get("boundary_id")
            hr.zone_id = str(zone_id) if zone_id else ""
            metric = (
                hazard.attributes.get("clearance_m")
                or hazard.attributes.get("distance_outside_m")
            )
            hr.metric_m = float(metric) if isinstance(metric, (int, float)) else -1.0
            self._hazard_pub.publish(hr)

    # ------------------------------------------------------------------
    def _build_frame(self) -> SensorFrame:
        if self._latest_scan is None:
            return SensorFrame()
        scan = self._latest_scan
        ranges = [r for r in scan.ranges if math.isfinite(r) and r > 0.0]
        point_count = len(ranges)
        if point_count == 0:
            return SensorFrame()
        min_range = min(ranges)
        max_range = max(ranges)
        mean_range = sum(ranges) / point_count
        timestamp_ms = int(scan.header.stamp.sec) * 1000 + int(scan.header.stamp.nanosec) // 1_000_000
        reading = LiDARReading(
            sensor_id="rover/lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=timestamp_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="ros.scan",
            sequence_number=self._scan_seq,
            min_range_m=min_range,
            max_range_m=max_range,
            mean_range_m=mean_range,
            point_count=point_count,
        )
        return SensorFrame(lidar=reading)


def _load_zones(path: str) -> tuple[
    tuple[KeepoutZone, ...],
    tuple[RestrictedZone, ...],
    tuple[OperationalBoundary, ...],
]:
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    if "mission_plan" in data:
        data = data["mission_plan"]
    keepouts = tuple(
        KeepoutZone(
            zone_id=z["zone_id"],
            min_x=float(z["min_x"]),
            min_y=float(z["min_y"]),
            max_x=float(z["max_x"]),
            max_y=float(z["max_y"]),
            margin_m=float(z.get("margin_m", 0.30)),
        )
        for z in data.get("keepout_zones", [])
    )
    restricted = tuple(
        RestrictedZone(
            zone_id=z["zone_id"],
            min_x=float(z["min_x"]),
            min_y=float(z["min_y"]),
            max_x=float(z["max_x"]),
            max_y=float(z["max_y"]),
            max_linear_velocity=float(z["max_linear_velocity"]),
            max_angular_velocity=float(z["max_angular_velocity"]),
        )
        for z in data.get("restricted_zones", [])
    )
    boundaries = tuple(
        OperationalBoundary(
            boundary_id=b["boundary_id"],
            min_x=float(b["min_x"]),
            min_y=float(b["min_y"]),
            max_x=float(b["max_x"]),
            max_y=float(b["max_y"]),
        )
        for b in data.get("operational_boundaries", [])
    )
    return keepouts, restricted, boundaries


def main() -> None:
    rclpy.init()
    node = WorldModelNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

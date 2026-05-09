"""ROS 2 mission diagnostics node.

Subscribes to /mission/state, /mission/progress, /mission/recovery,
/world_model/state, /world_model/hazards. Publishes:

* ``/diagnostics/mission`` (``diagnostic_msgs/DiagnosticArray``)
* ``/diagnostics/mission_summary`` (``std_msgs/String``, JSON)

Severity vocabulary mirrors EVENT_MODEL.md (DEBUG..CRITICAL) mapped
to DiagnosticStatus.level (0=OK, 1=WARN, 2=ERROR, 3=STALE).
"""

from __future__ import annotations

import json

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from std_msgs.msg import String

from rover_msgs.msg import (
    HazardReport,
    MissionState,
    RecoveryEvent,
    WaypointStatus,
    WorldModelState,
)


_OK = DiagnosticStatus.OK
_WARN = DiagnosticStatus.WARN
_ERROR = DiagnosticStatus.ERROR


class MissionDiagnosticsNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_mission_diagnostics")
        self.declare_parameter("evaluation_period_ms", 500)
        self._latest_state: MissionState | None = None
        self._latest_progress: WaypointStatus | None = None
        self._latest_world: WorldModelState | None = None
        self._recovery_count = 0
        self._waypoint_timeout_count = 0
        self._latest_hazards: list[HazardReport] = []

        self._diag_pub = self.create_publisher(
            DiagnosticArray, "/diagnostics/mission", 10
        )
        self._summary_pub = self.create_publisher(
            String, "/diagnostics/mission_summary", 10
        )

        self.create_subscription(MissionState, "/mission/state", self._on_state, 10)
        self.create_subscription(WaypointStatus, "/mission/progress", self._on_progress, 10)
        self.create_subscription(RecoveryEvent, "/mission/recovery", self._on_recovery, 50)
        self.create_subscription(WorldModelState, "/world_model/state", self._on_world, 10)
        self.create_subscription(HazardReport, "/world_model/hazards", self._on_hazard, 50)

        period_s = max(0.25, float(self.get_parameter("evaluation_period_ms").value) / 1000.0)
        self._timer = self.create_timer(period_s, self._tick)

    # ------------------------------------------------------------------
    def _on_state(self, msg: MissionState) -> None:
        self._latest_state = msg

    def _on_progress(self, msg: WaypointStatus) -> None:
        self._latest_progress = msg
        if msg.status == "timed_out":
            self._waypoint_timeout_count += 1

    def _on_recovery(self, msg: RecoveryEvent) -> None:
        if msg.phase == "engaged":
            self._recovery_count += 1

    def _on_world(self, msg: WorldModelState) -> None:
        self._latest_world = msg

    def _on_hazard(self, msg: HazardReport) -> None:
        self._latest_hazards.append(msg)
        # Keep the buffer bounded.
        if len(self._latest_hazards) > 32:
            self._latest_hazards = self._latest_hazards[-32:]

    # ------------------------------------------------------------------
    def _tick(self) -> None:
        statuses: list[DiagnosticStatus] = []

        # Mission state.
        state_status = DiagnosticStatus()
        state_status.name = "mission:state"
        state_status.hardware_id = "rover"
        if self._latest_state is None:
            state_status.level = bytes([_WARN])
            state_status.message = "no /mission/state observed yet"
        else:
            level = _level_for_state(self._latest_state.state)
            state_status.level = bytes([level])
            state_status.message = (
                f"{self._latest_state.state}"
                + (
                    f" (progress {self._latest_state.mission_progress:.2f})"
                    if self._latest_state.mission_progress >= 0.0
                    else ""
                )
            )
            state_status.values = [
                KeyValue(key="mission_id", value=self._latest_state.mission_id),
                KeyValue(key="reason_code", value=self._latest_state.reason_code),
                KeyValue(key="safety_state", value=self._latest_state.safety_state),
            ]
        statuses.append(state_status)

        # Active waypoint progress.
        wp_status = DiagnosticStatus()
        wp_status.name = "mission:waypoint"
        wp_status.hardware_id = "rover"
        if self._latest_progress is None:
            wp_status.level = bytes([_OK])
            wp_status.message = "no waypoint active"
        else:
            wp = self._latest_progress
            level = _OK
            if wp.elapsed_ms > 0 and wp.timeout_ms > 0 and wp.elapsed_ms > 0.7 * wp.timeout_ms:
                level = _WARN
            wp_status.level = bytes([level])
            wp_status.message = (
                f"{wp.waypoint_id} {wp.status} "
                f"d={wp.distance_to_goal_m:.2f}m elapsed={wp.elapsed_ms}/{wp.timeout_ms}ms"
            )
            wp_status.values = [
                KeyValue(key="waypoint_index", value=str(wp.waypoint_index)),
                KeyValue(key="waypoint_total", value=str(wp.waypoint_total)),
                KeyValue(key="distance_to_goal_m", value=f"{wp.distance_to_goal_m:.3f}"),
                KeyValue(key="heading_error_rad", value=f"{wp.heading_error_rad:.3f}"),
            ]
        statuses.append(wp_status)

        # Recovery counter.
        recovery_status = DiagnosticStatus()
        recovery_status.name = "mission:recovery"
        recovery_status.hardware_id = "rover"
        if self._recovery_count == 0:
            recovery_status.level = bytes([_OK])
            recovery_status.message = "no recovery engagements"
        elif self._recovery_count <= 2:
            recovery_status.level = bytes([_WARN])
            recovery_status.message = f"{self._recovery_count} recovery engagement(s)"
        else:
            recovery_status.level = bytes([_ERROR])
            recovery_status.message = f"{self._recovery_count} recovery engagement(s)"
        recovery_status.values = [
            KeyValue(key="waypoint_timeouts", value=str(self._waypoint_timeout_count))
        ]
        statuses.append(recovery_status)

        # World-model hazards.
        hazard_status = DiagnosticStatus()
        hazard_status.name = "world_model:hazards"
        hazard_status.hardware_id = "rover"
        if self._latest_world is not None and self._latest_world.inside_keepout:
            hazard_status.level = bytes([_ERROR])
            hazard_status.message = (
                f"inside keepout: {','.join(self._latest_world.inside_keepout)}"
            )
        elif self._latest_world is not None and self._latest_world.near_keepout:
            hazard_status.level = bytes([_WARN])
            hazard_status.message = (
                f"approaching keepout: {','.join(self._latest_world.near_keepout)}"
            )
        elif self._latest_world is not None and self._latest_world.boundary_violations:
            hazard_status.level = bytes([_ERROR])
            hazard_status.message = (
                f"boundary violation: {','.join(self._latest_world.boundary_violations)}"
            )
        else:
            hazard_status.level = bytes([_OK])
            hazard_status.message = "no zone hazards"
        statuses.append(hazard_status)

        # Publish DiagnosticArray.
        diag = DiagnosticArray()
        diag.header.stamp = self.get_clock().now().to_msg()
        diag.status = statuses
        self._diag_pub.publish(diag)

        # Publish JSON summary for Foxglove and replay.
        summary = String()
        summary.data = json.dumps(
            {
                "components": [
                    {
                        "name": s.name,
                        "level": int(s.level[0]),
                        "message": s.message,
                        "values": {kv.key: kv.value for kv in s.values},
                    }
                    for s in statuses
                ]
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        self._summary_pub.publish(summary)


def _level_for_state(state: str) -> int:
    if state in {"MISSION_ABORTED", "MISSION_ABORTING"}:
        return _ERROR
    if state in {"MISSION_DEGRADED", "MISSION_RECOVERY"}:
        return _WARN
    return _OK


def main() -> None:
    rclpy.init()
    node = MissionDiagnosticsNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

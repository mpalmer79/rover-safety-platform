"""ROS 2 mission orchestrator node.

Embeds :class:`app.mission.MissionOrchestrator`. Subscribes to
``/odom``, ``/safety/state``, ``/world_model/state``, and operator
topics; publishes ``/cmd_vel_requested`` (the only motion-bearing
topic the mission layer is ever allowed to produce), plus the
mission-state and mission-event topics.

The Nav2 boundary lives in :mod:`nav2_velocity_clamp`; this node owns
the deterministic motion request path. When Nav2 is in the loop, the
operator launches both nodes; the orchestrator is the source of
mission state and the clamp is the source of motion requests.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

import rclpy
from builtin_interfaces.msg import Time as RosTime
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Bool, String

from app.domain.enums import SafetyState
from app.domain.identifiers import RunId, ScenarioId, UuidIdGenerator
from app.domain.sensors import SensorFrame
from app.domain.time import SimulationClock, Timestamp
from app.mission.mission_plan import MissionPlan
from app.mission.orchestrator import MissionOrchestrator, OrchestratorInputs
from rover_msgs.msg import (
    HazardReport,
    MissionState as MissionStateMsg,
    RecoveryEvent,
    SafetyState as SafetyStateMsg,
    WaypointEvent,
    WaypointStatus,
    WorldModelState,
)


_REQUESTED_TOPIC = "/cmd_vel_requested"
_MISSION_STATE_TOPIC = "/mission/state"
_MISSION_EVENTS_TOPIC = "/mission/events"
_MISSION_PROGRESS_TOPIC = "/mission/progress"
_MISSION_RECOVERY_TOPIC = "/mission/recovery"
_MISSION_WAYPOINTS_TOPIC = "/mission/waypoints"


class _RosClock:
    """Adapter from :class:`rclpy.Node`'s clock to :class:`SimulationClock`."""

    def __init__(self, node: Node) -> None:
        self._node = node
        self._sim_ns = 0

    def now_ns(self) -> int:
        return self._node.get_clock().now().nanoseconds

    def now_ms(self) -> int:
        return self.now_ns() // 1_000_000

    def advance_ms(self, delta_ms: int) -> None:  # pragma: no cover - n/a
        raise RuntimeError("ROS clock cannot be advanced manually")

    def stamp(self) -> Timestamp:
        from datetime import datetime, timezone

        ns = self.now_ns()
        wall = (
            datetime.now(tz=timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        return Timestamp(wall=wall, sim_time_ns=ns)


class MissionRuntimeNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_mission_runtime")
        self.declare_parameter("run_id", "unknown")
        self.declare_parameter("scenario_id", "unknown")
        self.declare_parameter("mission_plan_path", "")
        self.declare_parameter("evaluation_period_ms", 100)
        self.declare_parameter("command_lifetime_ms", 500)

        run_id = RunId(str(self.get_parameter("run_id").value))
        scenario_id = ScenarioId(str(self.get_parameter("scenario_id").value))
        plan_path = str(self.get_parameter("mission_plan_path").value)
        if not plan_path:
            raise RuntimeError("mission_plan_path parameter is required")
        plan_dict = json.loads(Path(plan_path).read_text(encoding="utf-8"))
        if "mission_plan" in plan_dict:
            plan_dict = plan_dict["mission_plan"]
        self._plan = MissionPlan.from_dict(plan_dict)

        self._clock = _RosClock(self)
        self._ids = UuidIdGenerator()
        self._orchestrator = MissionOrchestrator(
            plan=self._plan,
            run_id=run_id,
            scenario_id=scenario_id,
            clock=self._clock,
            id_generator=self._ids,
        )

        latched = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )

        # Publishers.
        self._cmd_pub = self.create_publisher(Twist, _REQUESTED_TOPIC, 10)
        self._mission_state_pub = self.create_publisher(
            MissionStateMsg, _MISSION_STATE_TOPIC, latched
        )
        self._mission_events_pub = self.create_publisher(
            String, _MISSION_EVENTS_TOPIC, 50
        )
        self._waypoints_pub = self.create_publisher(
            WaypointEvent, _MISSION_WAYPOINTS_TOPIC, 50
        )
        self._progress_pub = self.create_publisher(
            WaypointStatus, _MISSION_PROGRESS_TOPIC, 10
        )
        self._recovery_pub = self.create_publisher(
            RecoveryEvent, _MISSION_RECOVERY_TOPIC, 10
        )

        # Latest inputs from subscribers.
        self._latest_safety_state = SafetyState.BOOT
        self._latest_confidence = 0.0
        self._latest_pose: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._operator_start = False
        self._operator_pause = False
        self._operator_resume = False
        self._operator_abort = False
        self._operator_recovery = False

        # Subscriptions. The mission node deliberately does not
        # subscribe to /scan, /imu, etc.: the supervisor's freshness
        # gates own those. We trust /safety/state for sensor health.
        self.create_subscription(Odometry, "/odom", self._on_odom, 20)
        self.create_subscription(SafetyStateMsg, "/safety/state", self._on_safety, 10)
        self.create_subscription(Bool, "/operator/mission_start", lambda m: self._set_op("start", m), 10)
        self.create_subscription(Bool, "/operator/mission_pause", lambda m: self._set_op("pause", m), 10)
        self.create_subscription(Bool, "/operator/mission_resume", lambda m: self._set_op("resume", m), 10)
        self.create_subscription(Bool, "/operator/mission_abort", lambda m: self._set_op("abort", m), 10)
        self.create_subscription(Bool, "/operator/recovery", lambda m: self._set_op("recovery", m), 10)

        period_s = max(0.05, float(self.get_parameter("evaluation_period_ms").value) / 1000.0)
        self._timer = self.create_timer(period_s, self._tick)
        self.get_logger().info(
            "rover_mission_runtime active. run_id=%s scenario_id=%s mission_id=%s",
            str(run_id),
            str(scenario_id),
            self._plan.mission_id,
        )

    # ------------------------------------------------------------------
    # Subscriber callbacks.
    # ------------------------------------------------------------------
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

    def _on_safety(self, msg: SafetyStateMsg) -> None:
        try:
            self._latest_safety_state = SafetyState(msg.state)
        except ValueError:
            self.get_logger().warn(f"unknown safety state {msg.state!r}")
            return
        if msg.confidence_score >= 0.0:
            self._latest_confidence = float(msg.confidence_score)

    def _set_op(self, kind: str, msg: Bool) -> None:
        if not bool(msg.data):
            return
        if kind == "start":
            self._operator_start = True
        elif kind == "pause":
            self._operator_pause = True
        elif kind == "resume":
            self._operator_resume = True
        elif kind == "abort":
            self._operator_abort = True
        elif kind == "recovery":
            self._operator_recovery = True

    # ------------------------------------------------------------------
    # Tick.
    # ------------------------------------------------------------------
    def _tick(self) -> None:
        now_ms = self._clock.now_ms()
        sim_ns = self._clock.now_ns()
        # We do not have a SensorFrame on the ROS side. The supervisor
        # owns sensor freshness; we pass an empty frame. The
        # orchestrator's constraint evaluator falls back to operator
        # paused / safety state inhibits motion when the frame is
        # empty.
        empty_frame = SensorFrame()
        evaluation = self._orchestrator.evaluate(
            OrchestratorInputs(
                pose_x=self._latest_pose[0],
                pose_y=self._latest_pose[1],
                heading_rad=self._latest_pose[2],
                sensor_frame=empty_frame,
                confidence_score=self._latest_confidence,
                safety_state=self._latest_safety_state,
                operator_start=self._operator_start,
                operator_pause=self._operator_pause,
                operator_resume=self._operator_resume,
                operator_abort=self._operator_abort,
                operator_recovery=self._operator_recovery,
                now_ms=now_ms,
                sim_time_ns=sim_ns,
                command_lifetime_ms=int(
                    self.get_parameter("command_lifetime_ms").value
                ),
            )
        )
        # Drop one-shot pulses after the orchestrator sees them.
        self._operator_start = False
        self._operator_pause = False
        self._operator_resume = False
        self._operator_abort = False
        self._operator_recovery = False

        # Publish the requested motion (or zero if none was produced).
        twist = Twist()
        if evaluation.requested_motion is not None:
            twist.linear.x = float(evaluation.requested_motion.linear_velocity)
            twist.angular.z = float(evaluation.requested_motion.angular_velocity)
        self._cmd_pub.publish(twist)

        # Publish mission state.
        state_msg = MissionStateMsg()
        state_msg.stamp = self.get_clock().now().to_msg()
        state_msg.run_id = str(self.get_parameter("run_id").value)
        state_msg.scenario_id = str(self.get_parameter("scenario_id").value)
        state_msg.mission_id = self._plan.mission_id
        state_msg.state = evaluation.mission_state.value
        state_msg.reason_code = (
            evaluation.events[-1].reason_code if evaluation.events else "tick"
        )
        state_msg.safety_state = self._latest_safety_state.value
        state_msg.mission_progress = float(self._orchestrator.progress_fraction)
        self._mission_state_pub.publish(state_msg)

        # Publish progress.
        if evaluation.progress is not None:
            wp = evaluation.progress.waypoint
            ws = WaypointStatus()
            ws.stamp = self.get_clock().now().to_msg()
            ws.run_id = state_msg.run_id
            ws.scenario_id = state_msg.scenario_id
            ws.mission_id = self._plan.mission_id
            ws.waypoint_id = wp.waypoint_id
            ws.status = evaluation.progress.status.value
            ws.distance_to_goal_m = float(evaluation.progress.distance_to_goal_m)
            ws.heading_error_rad = float(evaluation.progress.heading_error_rad)
            ws.elapsed_ms = int(evaluation.progress.elapsed_ms)
            ws.timeout_ms = int(wp.timeout_seconds * 1000)
            ws.waypoint_index = self._orchestrator.queue.completed_count
            ws.waypoint_total = self._orchestrator.queue.total
            self._progress_pub.publish(ws)

        # Fan out events.
        for event in evaluation.events:
            self._publish_event(event)

    # ------------------------------------------------------------------
    def _publish_event(self, event) -> None:
        # Always publish the canonical JSON event so /mission/events
        # remains schema-compatible with /safety/events.
        out = String()
        out.data = event.to_json()
        self._mission_events_pub.publish(out)

        if event.event_type.startswith("mission_waypoint."):
            we = WaypointEvent()
            we.stamp = self.get_clock().now().to_msg()
            we.run_id = str(event.run_id)
            we.scenario_id = str(event.scenario_id)
            we.mission_id = self._plan.mission_id
            we.phase = event.event_type.split(".", 1)[1]
            we.reason_code = event.reason_code
            we.waypoint_id = str(event.attributes.get("waypoint_id", ""))
            self._waypoints_pub.publish(we)
        elif event.event_type.startswith("mission_recovery."):
            re = RecoveryEvent()
            re.stamp = self.get_clock().now().to_msg()
            re.run_id = str(event.run_id)
            re.scenario_id = str(event.scenario_id)
            re.mission_id = self._plan.mission_id
            re.phase = event.event_type.split(".", 1)[1]
            re.reason_code = event.reason_code
            re.recovery_behavior = str(event.attributes.get("recovery_behavior", ""))
            re.waypoint_id = str(event.attributes.get("waypoint_id") or "")
            re.attempt_count = int(event.attributes.get("attempt_count") or 0)
            re.message = event.message
            self._recovery_pub.publish(re)


def main() -> None:
    rclpy.init()
    node = MissionRuntimeNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

"""rclpy node for the safety bridge.

Wires :class:`SafetyBridgeCore` to ROS topics. The node:

* subscribes to ``/cmd_vel_requested`` (the only motion request channel),
* subscribes to ``/scan``, ``/imu``, ``/odom``, ``/rover/sensors/contact/asserted``,
* subscribes to ``/operator/activate``, ``/operator/estop``,
  ``/operator/recovery``, ``/operator/reset`` (``std_msgs/Bool``),
* publishes ``/cmd_vel_authorized`` (``geometry_msgs/Twist``),
* publishes ``/safety/state`` (:class:`rover_msgs/SafetyState`),
* publishes ``/safety/motion_authorization`` (:class:`rover_msgs/MotionAuthorization`),
* publishes ``/safety/events`` (``std_msgs/String`` carrying JSON for now;
  see TODO in :func:`_publish_event`).

The node ticks at a configured rate (default 10 Hz). Each tick it
builds a :class:`SensorFrame`, calls the supervisor, and publishes the
result.

This module is kept thin on purpose: all decisions live in
:class:`SafetyBridgeCore` and in the deterministic supervisor it wraps.
"""

from __future__ import annotations

from typing import Optional

import rclpy
from builtin_interfaces.msg import Time as RosTime
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import Bool, String

from app.domain.identifiers import RunId, ScenarioId
from rover_msgs.msg import (
    FaultEvent,
    MotionAuthorization,
    SafetyState as SafetyStateMsg,
    SensorHealth,
    SystemHealth,
)

from rover_safety_bridge.safety_bridge_core import (
    HostedClock,
    IncomingContact,
    IncomingImu,
    IncomingOdom,
    IncomingRequestedMotion,
    IncomingScan,
    OperatorPulses,
    OutboundPublication,
    SafetyBridgeCore,
)

import json
import math


_AUTHORIZED_TOPIC = "/cmd_vel_authorized"
_REQUESTED_TOPIC = "/cmd_vel_requested"
_SAFETY_STATE_TOPIC = "/safety/state"
_MOTION_AUTH_TOPIC = "/safety/motion_authorization"
_SAFETY_EVENTS_TOPIC = "/safety/events"
_SYSTEM_HEALTH_TOPIC = "/system/health"


class SafetyBridgeNode(Node):
    """The ROS 2 facade around the deterministic safety supervisor."""

    def __init__(self) -> None:
        super().__init__("rover_safety_bridge")
        self.declare_parameter("run_id", "unknown")
        self.declare_parameter("scenario_id", "unknown")
        self.declare_parameter("evaluation_period_ms", 100)
        self.declare_parameter("authorized_publish_period_ms", 50)
        self.declare_parameter("command_lifetime_ms", 500)

        run_id = RunId(str(self.get_parameter("run_id").value))
        scenario_id = ScenarioId(str(self.get_parameter("scenario_id").value))

        self._clock_proxy = HostedClock()
        self._core = SafetyBridgeCore(
            run_id=run_id,
            scenario_id=scenario_id,
            clock=self._clock_proxy,
        )

        latched_qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )

        # Publishers.
        self._auth_pub = self.create_publisher(Twist, _AUTHORIZED_TOPIC, 10)
        self._safety_state_pub = self.create_publisher(
            SafetyStateMsg, _SAFETY_STATE_TOPIC, latched_qos
        )
        self._motion_auth_pub = self.create_publisher(
            MotionAuthorization, _MOTION_AUTH_TOPIC, 10
        )
        self._events_pub = self.create_publisher(String, _SAFETY_EVENTS_TOPIC, 50)
        self._system_health_pub = self.create_publisher(
            SystemHealth, _SYSTEM_HEALTH_TOPIC, 10
        )

        # Subscriptions.
        self._req_sub = self.create_subscription(
            Twist, _REQUESTED_TOPIC, self._on_requested, 10
        )
        self._scan_sub = self.create_subscription(
            LaserScan, "/scan", self._on_scan, 10
        )
        self._imu_sub = self.create_subscription(Imu, "/imu", self._on_imu, 20)
        self._odom_sub = self.create_subscription(
            Odometry, "/odom", self._on_odom, 20
        )
        self._contact_sub = self.create_subscription(
            Bool, "/rover/sensors/contact/asserted", self._on_contact, 10
        )

        # Operator pulses.
        self._operator: OperatorPulses = OperatorPulses()
        self._op_activate_sub = self.create_subscription(
            Bool, "/operator/activate", lambda m: self._set_pulse("activate", m), 10
        )
        self._op_estop_sub = self.create_subscription(
            Bool, "/operator/estop", lambda m: self._set_pulse("estop", m), 10
        )
        self._op_recovery_sub = self.create_subscription(
            Bool, "/operator/recovery", lambda m: self._set_pulse("recovery", m), 10
        )
        self._op_reset_sub = self.create_subscription(
            Bool, "/operator/reset", lambda m: self._set_pulse("reset", m), 10
        )

        # Counters.
        self._scan_seq = 0
        self._imu_seq = 0
        self._odom_seq = 0
        self._contact_seq = 0
        # Last-emit time (ms, receive-clock) per sensor for the stamp
        # skew diagnostic (#15). Rate-limited to one event per second
        # per sensor so a flapping publisher cannot spam the log.
        self._last_skew_emit_ms: dict[str, int] = {}
        # Last-emit time per topic for the invalid-input diagnostic
        # (#16). Same rate-limit policy.
        self._last_invalid_emit_ms: dict[str, int] = {}

        # Emit boot event immediately so observers have a marker.
        self._publish_event(self._core.emit_boot_event())

        # Tick.
        period_s = max(0.01, float(self.get_parameter("evaluation_period_ms").value) / 1000.0)
        self._timer = self.create_timer(period_s, self._tick)

        self.get_logger().info(
            "rover_safety_bridge active. run_id=%s scenario_id=%s period=%.3fs",
            str(run_id),
            str(scenario_id),
            period_s,
        )

    # ------------------------------------------------------------------
    # Subscriber callbacks. Each one converts the ROS message to one of
    # the IncomingX dataclasses and hands it to the core.
    # ------------------------------------------------------------------
    def _on_requested(self, msg: Twist) -> None:
        now_ms = self._now_ms()
        self._core.cache_request(
            IncomingRequestedMotion(
                timestamp_ms=now_ms,
                linear_velocity=msg.linear.x,
                angular_velocity=msg.angular.z,
                lifetime_ms=int(self.get_parameter("command_lifetime_ms").value),
            )
        )

    def _on_scan(self, msg: LaserScan) -> None:
        self._scan_seq += 1
        ranges = [r for r in msg.ranges if math.isfinite(r) and r > 0.0]
        if ranges:
            min_range = min(ranges)
            max_range = max(ranges)
            mean_range = sum(ranges) / len(ranges)
            point_count = len(ranges)
        else:
            min_range = float(msg.range_min) if msg.range_min > 0 else 0.0
            max_range = float(msg.range_max)
            mean_range = 0.0
            point_count = 0
        # #15: freshness uses receive-time at the subscriber. The
        # sender's header.stamp is retained for diagnostics only.
        now_ms = self._now_ms()
        sender_ms = _stamp_to_ms(msg.header.stamp)
        self._check_stamp_skew("scan", now_ms=now_ms, sender_ms=sender_ms)
        self._core.cache_scan(
            IncomingScan(
                timestamp_ms=now_ms,
                sequence_number=self._scan_seq,
                min_range_m=min_range,
                max_range_m=max_range,
                mean_range_m=mean_range,
                point_count=point_count,
                sender_stamp_ms=sender_ms,
            )
        )

    def _on_imu(self, msg: Imu) -> None:
        self._imu_seq += 1
        # Quaternion -> yaw (small-angle robust enough for sim).
        q = msg.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        now_ms = self._now_ms()
        sender_ms = _stamp_to_ms(msg.header.stamp)
        self._check_stamp_skew("imu", now_ms=now_ms, sender_ms=sender_ms)
        self._core.cache_imu(
            IncomingImu(
                timestamp_ms=now_ms,
                sequence_number=self._imu_seq,
                angular_velocity_z=msg.angular_velocity.z,
                linear_accel_x=msg.linear_acceleration.x,
                linear_accel_y=msg.linear_acceleration.y,
                orientation_rad=yaw,
                sender_stamp_ms=sender_ms,
            )
        )

    def _on_odom(self, msg: Odometry) -> None:
        self._odom_seq += 1
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        now_ms = self._now_ms()
        sender_ms = _stamp_to_ms(msg.header.stamp)
        self._check_stamp_skew("odom", now_ms=now_ms, sender_ms=sender_ms)
        self._core.cache_odom(
            IncomingOdom(
                timestamp_ms=now_ms,
                sequence_number=self._odom_seq,
                derived_linear_velocity=msg.twist.twist.linear.x,
                derived_angular_velocity=msg.twist.twist.angular.z,
                pose_x=msg.pose.pose.position.x,
                pose_y=msg.pose.pose.position.y,
                heading_rad=yaw,
                sender_stamp_ms=sender_ms,
            )
        )

    def _on_contact(self, msg: Bool) -> None:
        self._contact_seq += 1
        # /rover/sensors/contact/asserted carries no header; receive
        # time is the only timestamp available.
        self._core.cache_contact(
            IncomingContact(
                timestamp_ms=self._now_ms(),
                sequence_number=self._contact_seq,
                asserted=bool(msg.data),
            )
        )

    def _set_pulse(self, name: str, msg: Bool) -> None:
        # Operator pulses are level-triggered: as long as the topic
        # carries True, the supervisor receives the pulse on the next
        # tick. After the tick the level resets to False.
        self._operator = OperatorPulses(
            activate=name == "activate" and bool(msg.data) or self._operator.activate,
            estop=name == "estop" and bool(msg.data) or self._operator.estop,
            recovery=name == "recovery" and bool(msg.data) or self._operator.recovery,
            reset=name == "reset" and bool(msg.data) or self._operator.reset,
        )

    # ------------------------------------------------------------------
    # Tick.
    # ------------------------------------------------------------------
    def _tick(self) -> None:
        now_ns = self._now_ns()
        self._core.update_clock(now_ns=now_ns)
        outbound = self._core.evaluate(operator=self._operator)
        # Drop one-shot pulses after the supervisor sees them.
        self._operator = OperatorPulses()
        self._publish(outbound)

    # ------------------------------------------------------------------
    # Outbound publication.
    # ------------------------------------------------------------------
    def _publish(self, outbound: OutboundPublication) -> None:
        twist = Twist()
        twist.linear.x = float(outbound.authorized.linear_velocity)
        twist.angular.z = float(outbound.authorized.angular_velocity)
        self._auth_pub.publish(twist)

        ss = SafetyStateMsg()
        ss.stamp = self.get_clock().now().to_msg()
        ss.run_id = str(self.get_parameter("run_id").value)
        ss.scenario_id = str(self.get_parameter("scenario_id").value)
        ss.state = outbound.safety_state.value
        ss.reason_code = (
            outbound.transition_events[-1].reason_code
            if outbound.transition_events
            else "hold"
        )
        ss.confidence_score = float(outbound.confidence_score)
        ss.estop_latched = bool(outbound.estop_latched)
        ss.lifecycle_state = outbound.lifecycle_state.value
        self._safety_state_pub.publish(ss)

        ma = MotionAuthorization()
        ma.stamp = self.get_clock().now().to_msg()
        ma.run_id = str(self.get_parameter("run_id").value)
        ma.scenario_id = str(self.get_parameter("scenario_id").value)
        ma.decision = outbound.authorized.decision.value
        ma.reason_code = outbound.authorized.constraint_reason.value
        ma.safety_state = outbound.safety_state.value
        if outbound.requested_motion is not None:
            ma.requested.linear.x = float(outbound.requested_motion.linear_velocity)
            ma.requested.angular.z = float(outbound.requested_motion.angular_velocity)
        ma.authorized.linear.x = float(outbound.authorized.linear_velocity)
        ma.authorized.angular.z = float(outbound.authorized.angular_velocity)
        ma.was_clamped = bool(outbound.authorized.was_clamped)
        ma.confidence_score = float(outbound.confidence_score)
        self._motion_auth_pub.publish(ma)

        for evt in outbound.all_events:
            self._publish_event(evt)

    def _publish_event(self, event) -> None:
        out = String()
        # Reuse the event's canonical JSON serialiser for replay parity.
        out.data = event.to_json()
        self._events_pub.publish(out)

    # ------------------------------------------------------------------
    # Helpers.
    # ------------------------------------------------------------------
    def _now_ns(self) -> int:
        return self.get_clock().now().nanoseconds

    def _now_ms(self) -> int:
        return self._now_ns() // 1_000_000

    def _check_stamp_skew(self, sensor: str, *, now_ms: int, sender_ms: int) -> None:
        """Emit a rate-limited diagnostic when sender-stamp skew exceeds 1s.

        Never rejects the message — receive-time is the authoritative
        clock for freshness (#15). The diagnostic only flags
        misconfigured publishers.
        """

        if sender_ms == 0:
            return  # no stamp present
        skew_ms = abs(now_ms - sender_ms)
        if skew_ms <= 1000:
            return
        last = self._last_skew_emit_ms.get(sensor, -10_000)
        if now_ms - last < 1000:
            return
        self._last_skew_emit_ms[sensor] = now_ms
        self.get_logger().warn(
            "sensor.stamp_skew_excessive sensor=%s skew_ms=%d "
            "(receive-time used for freshness; sender stamp is diagnostic)"
            % (sensor, skew_ms)
        )

    def _emit_invalid_input_event(
        self, *, topic: str, field: str, error: str
    ) -> None:
        """Rate-limited safety.invalid_input event (#16).

        Publishes a structured String event on ``/safety/events`` so the
        replay layer captures the rejection. Rate-limited to 10/sec per
        topic to avoid log floods from a stuck publisher.
        """

        now_ms = self._now_ms()
        last = self._last_invalid_emit_ms.get(topic, -10_000)
        if now_ms - last < 100:
            return
        self._last_invalid_emit_ms[topic] = now_ms
        payload = {
            "event_type": "safety.invalid_input",
            "severity": "WARNING",
            "topic": topic,
            "field": field,
            "error": error,
            "now_ms": now_ms,
        }
        msg = String()
        msg.data = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        self._events_pub.publish(msg)
        self.get_logger().warn(
            "safety.invalid_input topic=%s field=%s error=%s"
            % (topic, field, error)
        )


def _stamp_to_ms(stamp: RosTime) -> int:
    return int(stamp.sec) * 1000 + int(stamp.nanosec) // 1_000_000


_SROS2_WARNING = (
    "running without SROS2; DDS domain is trusted-implicit. "
    "Set ROS_SECURITY_ENABLE=true for enclave enforcement."
)


def _warn_if_sros2_disabled(node: Node) -> None:
    """Emit a single WARNING when ROS_SECURITY_ENABLE is unset (#14 + #18).

    Do not refuse to start — portfolio reviewers run without keystores.
    """

    import os

    if os.environ.get("ROS_SECURITY_ENABLE", "").lower() not in {"true", "1"}:
        node.get_logger().warn(_SROS2_WARNING)


def main() -> None:
    rclpy.init()
    node = SafetyBridgeNode()
    _warn_if_sros2_disabled(node)
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()

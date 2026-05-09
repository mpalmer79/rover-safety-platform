"""Wheel odometry adapter.

Consumes ``/odom`` from the diff_drive plugin and publishes a
freshness summary plus a forwarded message on
``/rover/sensors/odom/normalized``.
"""

from __future__ import annotations

from nav_msgs.msg import Odometry

from rover_sensor_adapters.base_adapter import BaseAdapter, spin_node


class OdometryAdapter(BaseAdapter):
    SENSOR_TYPE = "wheel_encoder"

    def __init__(self) -> None:
        super().__init__("odometry_adapter", "wheel_encoder")
        self.declare_parameter("input_topic", "/odom")
        self.declare_parameter("normalized_topic", "/rover/sensors/odom/normalized")
        self.declare_parameter("warn_ms", 200)
        self.declare_parameter("safe_stop_ms", 600)
        self._sub = self.create_subscription(
            Odometry,
            str(self.get_parameter("input_topic").value),
            self._on_odom,
            20,
        )
        self._pub = self.create_publisher(
            Odometry,
            str(self.get_parameter("normalized_topic").value),
            20,
        )

    def _on_odom(self, msg: Odometry) -> None:
        self.record_message(msg.header.stamp)
        self._pub.publish(msg)


def main() -> None:
    spin_node(OdometryAdapter)


if __name__ == "__main__":
    main()

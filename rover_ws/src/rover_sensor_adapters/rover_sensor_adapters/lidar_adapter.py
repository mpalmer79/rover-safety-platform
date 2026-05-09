"""LiDAR adapter.

Subscribes to the bridged ``/scan`` (sensor_msgs/LaserScan) and
publishes ``/sensors/lidar/health`` plus a forwarded scan on
``/rover/sensors/lidar/normalized``. The forwarded scan adds no new
geometry; it exists so downstream consumers (the safety bridge,
recording, Foxglove layouts) subscribe to a stable namespaced topic
that will not change if the underlying bridge name moves.
"""

from __future__ import annotations

from sensor_msgs.msg import LaserScan

from rover_sensor_adapters.base_adapter import BaseAdapter, spin_node


class LidarAdapter(BaseAdapter):
    SENSOR_TYPE = "lidar"

    def __init__(self) -> None:
        super().__init__("lidar_adapter", "lidar")
        self.declare_parameter("input_topic", "/scan")
        self.declare_parameter("normalized_topic", "/rover/sensors/lidar/normalized")
        self._sub = self.create_subscription(
            LaserScan,
            str(self.get_parameter("input_topic").value),
            self._on_scan,
            10,
        )
        self._pub = self.create_publisher(
            LaserScan,
            str(self.get_parameter("normalized_topic").value),
            10,
        )

    def _on_scan(self, msg: LaserScan) -> None:
        self.record_message(msg.header.stamp)
        # Forward unchanged. Adapters do not modify perception payloads.
        self._pub.publish(msg)


def main() -> None:
    spin_node(LidarAdapter)


if __name__ == "__main__":
    main()

"""IMU adapter."""

from __future__ import annotations

from sensor_msgs.msg import Imu

from rover_sensor_adapters.base_adapter import BaseAdapter, spin_node


class ImuAdapter(BaseAdapter):
    SENSOR_TYPE = "imu"

    def __init__(self) -> None:
        super().__init__("imu_adapter", "imu")
        self.declare_parameter("input_topic", "/imu")
        self.declare_parameter("normalized_topic", "/rover/sensors/imu/normalized")
        self.declare_parameter("warn_ms", 200)
        self.declare_parameter("safe_stop_ms", 600)
        self._sub = self.create_subscription(
            Imu,
            str(self.get_parameter("input_topic").value),
            self._on_imu,
            20,
        )
        self._pub = self.create_publisher(
            Imu,
            str(self.get_parameter("normalized_topic").value),
            20,
        )

    def _on_imu(self, msg: Imu) -> None:
        self.record_message(msg.header.stamp)
        self._pub.publish(msg)


def main() -> None:
    spin_node(ImuAdapter)


if __name__ == "__main__":
    main()

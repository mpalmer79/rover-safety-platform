"""Contact / bumper adapter.

Subscribes to the bridged Gazebo contact stream
(``ros_gz_interfaces/Contacts``) and publishes a freshness summary
plus a normalised :class:`std_msgs/Bool` indicating whether the
bumper is currently asserted. The deterministic supervisor uses the
boolean topic; the structured ``ros_gz_interfaces/Contacts`` stream
is preserved for replay.
"""

from __future__ import annotations

from std_msgs.msg import Bool

# The ros_gz_interfaces.msg.Contacts type is bridged by ros_gz_bridge.
# Import lazily so unit tests can stub this when the package is not
# present.
try:
    from ros_gz_interfaces.msg import Contacts
except ImportError:  # pragma: no cover - test environment without ros_gz_interfaces
    Contacts = None  # type: ignore[assignment]

from rover_sensor_adapters.base_adapter import BaseAdapter, spin_node


class ContactAdapter(BaseAdapter):
    SENSOR_TYPE = "contact"

    def __init__(self) -> None:
        super().__init__("contact_adapter", "contact")
        self.declare_parameter("input_topic", "/contact")
        self.declare_parameter("normalized_topic", "/rover/sensors/contact/asserted")
        self.declare_parameter("warn_ms", 500)
        self.declare_parameter("safe_stop_ms", 1500)
        self._asserted_pub = self.create_publisher(
            Bool,
            str(self.get_parameter("normalized_topic").value),
            10,
        )
        if Contacts is not None:
            self._sub = self.create_subscription(
                Contacts,
                str(self.get_parameter("input_topic").value),
                self._on_contact,
                10,
            )
        else:  # pragma: no cover
            self.get_logger().warn(
                "ros_gz_interfaces not available; contact adapter is inactive."
            )

    def _on_contact(self, msg) -> None:
        # Use ROS clock for the recorded stamp because Gazebo's contact
        # type does not always carry a header in older versions of
        # ros_gz_interfaces; the supervisor's freshness gate runs on the
        # adapter's tick clock.
        self.record_message(self.get_clock().now().to_msg())
        asserted = bool(msg.contacts) if hasattr(msg, "contacts") else False
        out = Bool()
        out.data = asserted
        self._asserted_pub.publish(out)


def main() -> None:
    spin_node(ContactAdapter)


if __name__ == "__main__":
    main()

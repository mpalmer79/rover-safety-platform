# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

MISSION_TOPIC = "/mission/waypoint_request"
WAYPOINT_ID = "alpha"


def main() -> None:
    rclpy.init()
    node = Node("waypoint_requester")
    # NOTE: publishes a mission request, not an actuator command.
    publisher = node.create_publisher(String, MISSION_TOPIC, 10)
    msg = String()
    msg.data = WAYPOINT_ID
    publisher.publish(msg)
    node.get_logger().info(f"requested waypoint {WAYPOINT_ID}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

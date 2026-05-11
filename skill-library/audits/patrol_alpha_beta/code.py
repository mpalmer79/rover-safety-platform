# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

MISSION_TOPIC = "/mission/patrol_request"
WAYPOINTS = ["alpha","beta"]


def main() -> None:
    rclpy.init()
    node = Node("patrol_requester")
    # NOTE: publishes a mission request, not an actuator command.
    publisher = node.create_publisher(String, MISSION_TOPIC, 10)
    msg = String()
    msg.data = json.dumps({"waypoints": WAYPOINTS})
    publisher.publish(msg)
    node.get_logger().info("requested patrol route")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

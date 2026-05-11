# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


def main() -> None:
    rclpy.init()
    node = Node("requested_motion_publisher")
    # NOTE: /cmd_vel_requested, not /cmd_vel.
    publisher = node.create_publisher(Twist, "/cmd_vel_requested", 10)
    msg = Twist()
    msg.linear.x = 0.20
    msg.angular.z = 0.00
    publisher.publish(msg)
    node.get_logger().info("requested-motion command published")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

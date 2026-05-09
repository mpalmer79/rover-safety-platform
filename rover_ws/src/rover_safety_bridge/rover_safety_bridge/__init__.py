"""rover_safety_bridge: ROS 2 integration for the deterministic supervisor.

This package exposes :class:`SafetyBridgeCore`, the pure-logic core that
turns observed ROS messages into supervisor inputs and supervisor
evaluations into outbound ROS publications. The :mod:`safety_bridge_node`
module wires it to ``rclpy``. Tests exercise the core directly without
ROS dependencies.
"""

__version__ = "0.1.0"

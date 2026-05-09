"""rover_world_model: ROS 2 bounded world model.

The node embeds :class:`app.world_model.WorldModel`. It does not
implement SLAM or probabilistic mapping; it maintains the declared
keepout / restricted-speed / boundary regions, derives a coarse
forward-clearance summary from the bridged LiDAR scan, and publishes
:class:`rover_msgs/WorldModelState` and :class:`rover_msgs/HazardReport`.
"""

__version__ = "0.1.0"

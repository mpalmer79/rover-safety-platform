"""rover_sensor_adapters: ROS to deterministic-runtime sensor adapters.

Each adapter subscribes to a raw ROS sensor topic, validates the
incoming message against documented freshness thresholds, and
publishes a normalised :class:`rover_msgs/SensorHealth` summary plus a
forwarded raw message on a namespaced topic. Adapters do not own
safety logic; the deterministic supervisor in
:mod:`app.safety.supervisor` is the only authority that interprets
freshness as a state transition.
"""

__version__ = "0.1.0"

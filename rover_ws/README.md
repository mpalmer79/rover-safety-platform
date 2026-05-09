# rover_ws — ROS 2 workspace

Phase 1B colcon workspace for the Autonomous Safety Validation Rover Platform.

This workspace integrates ROS 2 Jazzy and Gazebo Harmonic with the
deterministic Python autonomy runtime under `../backend/`. The
deterministic runtime is **authoritative**. ROS and Gazebo are
infrastructure layers that publish, subscribe, simulate, and bridge.
They do not own safety logic.

## Packages

| Package | Role |
|---|---|
| `rover_msgs` | Custom interfaces (`SafetyState`, `MotionAuthorization`, `SystemHealth`, `SensorHealth`, `FaultEvent`, `ReplayMarker`). |
| `rover_description` | Differential-drive rover URDF/Xacro with LiDAR, IMU, contact, wheel joints. |
| `rover_sim_gazebo` | Gazebo Harmonic world, ros_gz_bridge YAML, simulation launch. |
| `rover_sensor_adapters` | Adapter nodes that normalize raw ROS sensor streams into the runtime contract. |
| `rover_safety_bridge` | The critical integration node. Hosts the deterministic `SafetySupervisor` from `app.safety` and is the **only** producer of `/cmd_vel_authorized`. |
| `rover_observability` | Run lifecycle manager, replay marker publisher, and rosbag2 launch integration. |
| `rover_bringup` | Top-level launches (`full_system`, `simulation`, `safety_runtime`, `observability`, `rover_spawn`). |

## Authority Model (binding)

```
Mission / teleop / Nav2  ──►  /cmd_vel_requested
                                       │
                                       ▼
                          rover_safety_bridge
                          (hosts app.safety.SafetySupervisor)
                                       │
                                       ▼
                          /cmd_vel_authorized   ──►  ros_gz_bridge  ──►  Gazebo diff-drive
```

The hardware/Gazebo gateway never subscribes to `/cmd_vel_requested`.
The bridge YAML only forwards `/cmd_vel_authorized` to Gazebo. This is
enforced at the topic layer (separate names) and at the YAML layer
(only authorized motion is bridged).

See `../docs/SAFETY_MODEL.md` and `../docs/adr/ADR-004-safety-supervisor-authority-model.md`.

## Building

```bash
# 1. Install the deterministic runtime as a Python package so ROS nodes can import it.
cd ../backend
pip install -e .

# 2. Build the workspace.
cd ../rover_ws
colcon build --symlink-install

# 3. Source the workspace.
source install/setup.bash
```

## Launching

```bash
# Full system: simulation + safety runtime + observability + recording.
ros2 launch rover_bringup full_system.launch.py

# Just simulation + sensors (no safety runtime).
ros2 launch rover_bringup simulation.launch.py

# Just safety runtime against a stubbed simulation.
ros2 launch rover_bringup safety_runtime.launch.py
```

See `rover_bringup/launch/` for parameters (run_id, scenario_id,
record_bag).

## Testing in this environment

Phase 1B's tests under `tests/` are runnable **without** ROS 2 / Gazebo
installed. They validate the static structure of the workspace —
package manifests, URDF/Xacro syntax, bridge YAML, and the safety
bridge's pure-logic core (with `rclpy` stubbed). End-to-end tests that
actually launch Gazebo and run colcon-built nodes are documented in
`tests/manual.md` and require a Jazzy host.

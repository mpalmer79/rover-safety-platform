# Manual / host validation steps

The pytest suite under `rover_ws/tests/` runs in a CI sandbox without
ROS 2 or Gazebo Harmonic. The checks below require a real ROS 2 Jazzy
host with Gazebo Harmonic and `ros_gz_*` installed. They are the
acceptance gates for Phase 1B end-to-end behaviour.

## Prerequisites

```
sudo apt install -y \
  ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-interfaces \
  ros-jazzy-rosbag2-storage-mcap ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher
pip install -e ../backend          # makes app.* importable to ROS nodes
```

## Build

```
cd rover_ws
colcon build --symlink-install
source install/setup.bash
```

Expected: clean build for all seven packages.

## 1. Gazebo + bridge

```
ros2 launch rover_bringup simulation.launch.py
```

Expected:
- Gazebo Harmonic GUI opens with the validation world.
- The rover spawns at the origin.
- `ros2 topic list` shows `/scan`, `/imu`, `/odom`, `/contact`,
  `/joint_states`, `/clock`, `/tf`, `/tf_static`, `/cmd_vel_authorized`.
- `ros2 topic hz /scan` reports ~10 Hz.
- `ros2 run tf2_tools view_frames` produces an `odom -> base_footprint
  -> base_link -> {lidar_link, imu_link, contact_link, ...}` tree.

## 2. Full system

```
ros2 launch rover_bringup full_system.launch.py \
  scenario_id:=ros_smoke_v1 \
  runs_root:=$(pwd)/runs \
  record_bag:=true
```

Expected:
- `runs/<run_id>/metadata.json` is created.
- `/safety/state` publishes `BOOT` then `INACTIVE`.
- `ros2 topic pub --once /operator/activate std_msgs/Bool '{data: true}'`
  drives `/safety/state` to `ACTIVE_NORMAL`.
- `ros2 topic pub /cmd_vel_requested geometry_msgs/Twist
  '{linear: {x: 0.4}}' --rate 5` causes the rover to drive forward.
- After the run, `runs/<run_id>/events.jsonl` contains a stream of
  events with the expected `safety_transition.entered` reasons.
- `runs/<run_id>/bags/` contains an MCAP file.

## 3. Authority enforcement

```
ros2 topic pub --once /cmd_vel std_msgs/Empty '{}'   # should NOT move the rover
```

Expected: nothing happens. The diff_drive plugin only subscribes to
`/cmd_vel_authorized`. The bridge YAML deliberately does not forward
`/cmd_vel` or `/cmd_vel_requested` to Gazebo.

## 4. E-stop

While the rover is driving, run:

```
ros2 topic pub --once /operator/estop std_msgs/Bool '{data: true}'
```

Expected: `/safety/state` transitions to `E_STOP_LATCHED`,
`/cmd_vel_authorized` immediately publishes zero, and subsequent
`/cmd_vel_requested` traffic is ignored. Even after the underlying
condition clears, `/safety/state` remains `E_STOP_LATCHED` until:

```
ros2 topic pub --once /operator/reset std_msgs/Bool '{data: true}'
```

is published. The state then goes to `RECOVERY` and on through
revalidation.

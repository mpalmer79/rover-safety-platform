# Incident Timeline — `canonical-static-qualification`

- **Entry count:** 20
- **First fault:** -
- **First safety transition:** -
- **First command intervention:** -
- **Terminal entry:** #19 (?, `host_qualification.bridge_config_present`)

| # | t (ms) | Category | Event | Severity | Safety | Reason | Source |
|---|---|---|---|---|---|---|---|
| 0 | ? | `runtime_validation` | `runtime_validation.check[static.bridge_yaml_valid]` | `INFO` | `-` | - | `runtime-validation.json` |
| 1 | ? | `runtime_validation` | `runtime_validation.check[static.required_topics_declared]` | `INFO` | `-` | - | `runtime-validation.json` |
| 2 | ? | `runtime_validation` | `runtime_validation.check[static.urdf_tf_tree]` | `INFO` | `-` | - | `runtime-validation.json` |
| 3 | ? | `runtime_validation` | `runtime_validation.check[static.full_system_launch_composes_required_packages]` | `INFO` | `-` | - | `runtime-validation.json` |
| 4 | ? | `runtime_validation` | `runtime_validation.check[static.node_modules_present]` | `INFO` | `-` | - | `runtime-validation.json` |
| 5 | ? | `runtime_validation` | `runtime_validation.check[static.safety_bridge_authority_invariant]` | `INFO` | `-` | - | `runtime-validation.json` |
| 6 | ? | `runtime_validation` | `runtime_validation.check[static.runtime_validation_runbook_complete]` | `INFO` | `-` | - | `runtime-validation.json` |
| 7 | ? | `runtime_validation` | `runtime_validation.check[launch_smoke_test]` | `INFO` | `-` | rclpy not importable: No module named 'rclpy' | `runtime-validation.json` |
| 8 | ? | `runtime_validation` | `runtime_validation.check[topic_probe]` | `INFO` | `-` | rclpy not importable: No module named 'rclpy' | `runtime-validation.json` |
| 9 | ? | `runtime_validation` | `runtime_validation.check[tf_probe]` | `INFO` | `-` | rclpy not importable: No module named 'rclpy' | `runtime-validation.json` |
| 10 | ? | `runtime_validation` | `runtime_validation.check[command_path_probe]` | `INFO` | `-` | rclpy not importable: No module named 'rclpy' | `runtime-validation.json` |
| 11 | ? | `qualification` | `host_qualification.ubuntu_version` | `INFO` | `-` | - | `host-qualification.json` |
| 12 | ? | `qualification` | `host_qualification.ros2_distro` | `INFO` | `-` | source /opt/ros/jazzy/setup.bash before invoking the qualifier; CI runs without ROS and reports this check as not_executed | `host-qualification.json` |
| 13 | ? | `qualification` | `host_qualification.gazebo_harmonic` | `INFO` | `-` | install Gazebo Harmonic for Ubuntu 24.04 / Jazzy | `host-qualification.json` |
| 14 | ? | `qualification` | `host_qualification.colcon_available` | `INFO` | `-` | install python3-colcon-common-extensions for Jazzy | `host-qualification.json` |
| 15 | ? | `qualification` | `host_qualification.required_ros_packages` | `INFO` | `-` | source ROS to enumerate available packages | `host-qualification.json` |
| 16 | ? | `qualification` | `host_qualification.python_backend_importable` | `INFO` | `-` | - | `host-qualification.json` |
| 17 | ? | `qualification` | `host_qualification.workspace_structure` | `WARN` | `-` | run `colcon build --symlink-install` before live qualification | `host-qualification.json` |
| 18 | ? | `qualification` | `host_qualification.required_launch_files` | `INFO` | `-` | - | `host-qualification.json` |
| 19 | ? | `qualification` | `host_qualification.bridge_config_present` | `INFO` | `-` | - | `host-qualification.json` |

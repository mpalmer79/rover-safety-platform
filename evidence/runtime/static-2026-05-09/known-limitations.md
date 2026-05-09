# Known limitations

Run id: `static-2026-05-09`. Mode: `static-only`.

- The platform is **not** safety-certified. This report demonstrates engineering verification discipline, not regulatory compliance.
- Live ROS 2 / Gazebo evidence is collected only on a Jazzy host. Runs in environments that lack rclpy / Gazebo Harmonic surface their checks as `not_executed` with a reason; never as `passed`.
- Static-only mode validates the workspace artefacts (launch files, URDF, bridge YAML, node modules). It does not exercise the safety bridge against a live actuator stream.
- Closed-loop verification of the Nav2 velocity-clamp boundary requires a Jazzy host. The static-only path asserts the boundary at the source level only.

# Skill Template Catalog

The platform is **not safety-certified.** This page documents each
template the Phase 15A workbench can emit.

Every template:

* publishes to `/cmd_vel_requested` (or a mission-request topic),
  never directly to `/cmd_vel`;
* has bounded parameters with explicit safety constraints;
* renders a final zero ``Twist`` when motion is involved;
* mentions the safety supervisor in a comment header.

## move_forward_distance

| Field                     | Value                                                                       |
|---------------------------|-----------------------------------------------------------------------------|
| Required parameters       | `distance_meters`                                                           |
| Default parameters        | `linear_speed_mps=0.25`, `publish_rate_hz=10.0`, `timeout_safety_margin=1.5` |
| Generated topics          | `/cmd_vel_requested`                                                        |
| Forbidden topics          | `/cmd_vel`                                                                  |
| Timeout required          | yes                                                                          |
| Stop command required     | yes                                                                          |
| Risk band                 | `guarded`                                                                   |
| Safety constraints        | `distance_meters > 0 and <= 25.0 m`, `linear_speed_mps > 0 and <= 0.5 m/s`  |

## rotate_degrees

| Field                     | Value                                                                       |
|---------------------------|-----------------------------------------------------------------------------|
| Required parameters       | `angle_degrees`, `direction`                                                |
| Default parameters        | `angular_speed_rad_s=0.4`, `publish_rate_hz=10.0`, `timeout_safety_margin=1.5` |
| Generated topics          | `/cmd_vel_requested`                                                        |
| Forbidden topics          | `/cmd_vel`                                                                  |
| Timeout required          | yes                                                                          |
| Stop command required     | yes                                                                          |
| Risk band                 | `guarded`                                                                   |
| Safety constraints        | `|angle_degrees| > 0 and <= 720`, `angular_speed_rad_s > 0 and <= 1.0 rad/s` |

## stop_immediately

| Field                     | Value                                                |
|---------------------------|------------------------------------------------------|
| Required parameters       | _(none)_                                             |
| Default parameters        | `publish_count=5`, `publish_rate_hz=10.0`            |
| Generated topics          | `/cmd_vel_requested`                                 |
| Forbidden topics          | `/cmd_vel`                                           |
| Timeout required          | no                                                   |
| Stop command required     | yes                                                  |
| Risk band                 | `low`                                                |

## publish_requested_motion

| Field                     | Value                                                |
|---------------------------|------------------------------------------------------|
| Required parameters       | `linear_x_mps`, `angular_z_rad_s`                    |
| Default parameters        | _(none)_                                             |
| Generated topics          | `/cmd_vel_requested`                                 |
| Forbidden topics          | `/cmd_vel`                                           |
| Timeout required          | no                                                   |
| Stop command required     | no                                                   |
| Risk band                 | `guarded`                                            |
| Safety constraints        | `|linear_x_mps| <= 0.5`, `|angular_z_rad_s| <= 1.0`  |

## keyboard_forward_binding

| Field                     | Value                                                            |
|---------------------------|------------------------------------------------------------------|
| Required parameters       | `key`                                                            |
| Default parameters        | `linear_speed_mps=0.2`, `publish_rate_hz=10.0`, `watchdog_seconds=0.5` |
| Generated topics          | `/cmd_vel_requested`                                             |
| Forbidden topics          | `/cmd_vel`                                                       |
| Timeout required          | yes (watchdog)                                                   |
| Stop command required     | yes                                                              |
| Risk band                 | `guarded`                                                        |

## controller_button_binding

| Field                     | Value                                                            |
|---------------------------|------------------------------------------------------------------|
| Required parameters       | `button`                                                         |
| Default parameters        | `linear_speed_mps=0.2`, `publish_rate_hz=10.0`, `watchdog_seconds=0.5` |
| Generated topics          | `/cmd_vel_requested`                                             |
| Forbidden topics          | `/cmd_vel`                                                       |
| Timeout required          | yes (watchdog)                                                   |
| Stop command required     | yes                                                              |
| Risk band                 | `guarded`                                                        |

## waypoint_request

| Field                     | Value                                                |
|---------------------------|------------------------------------------------------|
| Required parameters       | `waypoint_id`                                        |
| Default parameters        | `mission_topic=/mission/waypoint_request`            |
| Generated topics          | `/mission/waypoint_request`                          |
| Forbidden topics          | `/cmd_vel`, `/cmd_vel_requested`                     |
| Timeout required          | no                                                   |
| Stop command required     | no                                                   |
| Risk band                 | `low`                                                |

The snippet publishes a mission request only. Mission runtime
decides whether to act; the safety supervisor authorises motion.

## patrol_route_template

| Field                     | Value                                                |
|---------------------------|------------------------------------------------------|
| Required parameters       | `waypoints`                                          |
| Default parameters        | `mission_topic=/mission/patrol_request`, `max_waypoints=8` |
| Generated topics          | `/mission/patrol_request`                            |
| Forbidden topics          | `/cmd_vel`, `/cmd_vel_requested`                     |
| Timeout required          | no                                                   |
| Stop command required     | no                                                   |
| Risk band                 | `low`                                                |

## safe_stop_wrapper

| Field                     | Value                                                |
|---------------------------|------------------------------------------------------|
| Required parameters       | _(none)_                                             |
| Default parameters        | `publish_count=3`, `publish_rate_hz=10.0`            |
| Generated topics          | `/cmd_vel_requested`                                 |
| Forbidden topics          | `/cmd_vel`                                           |
| Timeout required          | no                                                   |
| Stop command required     | yes (in `finally:` block)                            |
| Risk band                 | `low`                                                |

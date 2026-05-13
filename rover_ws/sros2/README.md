# SROS2 enclaves (#14 + #18)

SROS2 (Secure ROS 2) configuration for the platform. The enclaves under
`enclaves/` declare which DDS identity is allowed to publish on which
topics. The intent is to make the DDS-domain trust assumption explicit
in code rather than implicit in deployment.

## What is enforced (when SROS2 is enabled)

| Topic                         | Publisher identity        |
| ----------------------------- | ------------------------- |
| `/operator/activate`          | `operator_panel`          |
| `/operator/estop`             | `operator_panel`          |
| `/operator/recovery`          | `operator_panel`          |
| `/operator/reset`             | `operator_panel`          |
| `/operator/reset_armed`       | `operator_panel`          |
| `/safety/events`              | `rover_safety_bridge`     |
| `/safety/state`               | `rover_safety_bridge`     |
| `/safety/motion_authorization`| `rover_safety_bridge`     |
| `/cmd_vel_authorized`         | `rover_safety_bridge`     |
| `/cmd_vel_requested`          | `mission_runtime`         |

Every other identity may subscribe but not publish. Default is DENY.

## What is **not** enforced

Without SROS2, the platform trusts every participant on the DDS
domain — anyone who can reach the multicast / unicast group can
publish on any topic, including `/safety/events` and operator pulses.
This is acceptable on a single-host development network and on a
physically isolated test bench. Do not deploy without SROS2 to a
shared network.

## Generating the keystore (do once per deployment)

The keystore is **never** checked in (`keystore/` is gitignored).
Generate it locally with the official tools:

```bash
ros2 security create_keystore rover_ws/sros2/keystore
ros2 security create_enclave rover_ws/sros2/keystore /operator_panel
ros2 security create_enclave rover_ws/sros2/keystore /rover_safety_bridge
ros2 security create_enclave rover_ws/sros2/keystore /mission_runtime

# Copy the permissions XML into each enclave dir:
cp rover_ws/sros2/enclaves/operator_panel/permissions.xml \
   rover_ws/sros2/keystore/enclaves/operator_panel/permissions.xml
# (repeat for the other two)

# Re-sign with the keystore CA:
ros2 security generate_artifacts \
  -k rover_ws/sros2/keystore \
  -e /operator_panel /rover_safety_bridge /mission_runtime
```

## Launching with enclave enforcement

```bash
export ROS_SECURITY_KEYSTORE=$(pwd)/rover_ws/sros2/keystore
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_ENCLAVE_OVERRIDE=/rover_safety_bridge
ros2 run rover_safety_bridge safety_bridge_node
```

Use the matching enclave path per node.

## Without the keystore

The nodes still start; they log a single WARNING on boot stating that
they are running without SROS2 and the DDS domain is trusted-implicit.
This is intentional: portfolio reviewers should be able to run the
demos without first standing up a keystore.

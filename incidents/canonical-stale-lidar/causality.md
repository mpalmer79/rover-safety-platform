# Causality — `canonical-stale-lidar`

## `stale_lidar_chain` — `direct`

stale_lidar -> freshness_violation -> degraded/restricted -> safe_stop -> zero_authorized_motion

```mermaid
flowchart LR
    E7 -- "triggered (direct)" --> E34
    E7 -- "escalated_to (direct)" --> E8
    E8 -- "escalated_to (direct)" --> E19
    E19 -- "zeroed_motion_in (direct)" --> E172
```

This report is an engineering analysis artifact generated from available simulation and runtime evidence. It does not represent safety certification or regulatory approval.

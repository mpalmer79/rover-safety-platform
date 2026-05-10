# Causality — `canonical-estop-latched`

## `operator_estop_chain` — `moderate`

operator_estop -> estop_latched -> motion_inhibited

```mermaid
flowchart LR
    E6 -- "self_latched (moderate, inferred)" --> E6
    E6 -- "motion_inhibited_in (direct)" --> E52
```

**Missing links:**
- operator E-stop event

This report is an engineering analysis artifact generated from available simulation and runtime evidence. It does not represent safety certification or regulatory approval.

# System Flow

The platform is **not safety-certified**. This diagram shows how
the deterministic Python core, the ROS 2 / Gazebo workspace, and
the evidence layers fit together.

```mermaid
flowchart TB
    subgraph SimPython["Deterministic Python core (backend/app)"]
        sim[Scenario engine] --> faults[Fault library]
        faults --> mission[Mission runtime]
        mission -->|requests motion| supervisor((Safety supervisor))
        supervisor -->|authorises motion| arb[Motion arbitration]
        arb --> gw[Hardware gateway]
        supervisor --> evt[Event recorder]
        mission --> evt
    end

    subgraph SimROS["ROS 2 Jazzy / Gazebo workspace (rover_ws)"]
        nodes[Lifecycle nodes] --> bridge[Safety bridge]
        bridge --> supervisor
        nodes --> bag[(Bags)]
    end

    subgraph Evidence["Evidence layer (read-only)"]
        evt --> audits[Audits<br/>command-path / safety-transition / replay-integrity]
        audits --> evidence[(evidence/scenarios)]
        bag --> review[Replay review]
        review --> incidents[(incidents/)]
        incidents --> analytics[Replay analytics]
        analytics --> impact[Reliability impact]
        evidence --> programme[Programme review]
        incidents --> programme
        analytics --> programme
        impact --> programme
        programme --> exporter[Reviewer export]
    end

    exporter --> bundle[(reviewer-export/<br/>CSV + JSONL + schemas + notebook)]

    classDef authority stroke-width:3px;
    class supervisor authority;
```

## Notes

- Only the **safety supervisor** can authorise motion. Mission code
  may request; nothing else may authorise.
- Faults change inputs (sensor readings, command timeouts, bridge
  state, watchdog pets); the supervisor reacts through normal
  mechanisms.
- The ROS 2 side honours the same contracts as the Python core.
  When no Jazzy host is available, the runtime layers fall back to
  `static-only` and label the result honestly.
- The whole evidence layer is **read-only** with respect to runtime
  state: it inspects, classifies, aggregates, and reports — nothing
  more.

See [`ARCHITECTURE_WALKTHROUGH.md`](../ARCHITECTURE_WALKTHROUGH.md)
for the module-by-module narrative.

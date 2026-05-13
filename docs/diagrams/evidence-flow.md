# Evidence Flow

The platform is **not safety-certified**. This diagram shows how
engineering evidence flows from a single scenario run all the way
out to the reviewer-export bundle.

```mermaid
flowchart TB
    subgraph Run["Scenario run"]
        engine[Deterministic engine] --> events[(events.jsonl)]
        engine --> manifest[(manifest.json)]
    end

    subgraph PerScenario["Per-scenario evidence"]
        events --> ci[command-audit]
        events --> sa[safety-transition-audit]
        events --> ri[replay-integrity]
        manifest --> ev[evidence.json / .md]
        ci --> ev
        sa --> ev
        ri --> ev
        ev --> dir[(evidence/scenarios/&lt;id&gt;/)]
    end

    subgraph Trace["Traceability + verification"]
        registry[Requirements registry] --> traceability[(verification/traceability.json)]
        registry --> matrix[(docs/TRACEABILITY_MATRIX.md)]
        ev --> reportgen[Report generator]
        traceability --> reportgen
        reportgen --> svr[(docs/SCENARIO_VERIFICATION_REPORT.md)]
    end

    subgraph Runtime["Runtime + qualification (Phases 4–5)"]
        rcap[Runtime capture] --> rval[(runtime-validation.json)]
        rcap --> qsum[(qualification-summary.json)]
    end

    subgraph IncidentLayer["Incident reconstruction (Phases 6–7)"]
        rval --> recon[Reconstructor]
        qsum --> recon
        recon --> incident[(incident-report.json)]
        incident --> review[Replay review]
        review --> rrr[(replay-review-report.json)]
    end

    subgraph Aggregation["Analytics + impact (Phases 8–9)"]
        rrr --> analytics[Replay analytics]
        analytics --> rar[(replay-analytics-report.json)]
        analytics --> impact[Reliability impact]
        impact --> ir[(impact-report.json)]
    end

    subgraph Programme["Programme review (Phase 10)"]
        traceability --> pr[Programme review]
        rval --> pr
        qsum --> pr
        incident --> pr
        rrr --> pr
        rar --> pr
        ir --> pr
        pr --> programme[(programme-review/*)]
    end

    subgraph Export["Reviewer export (Phase 11)"]
        programme --> exporter[Reviewer export]
        rrr --> exporter
        incident --> exporter
        ir --> exporter
        traceability --> exporter
        exporter --> bundle[(reviewer-export/<br/>CSV + JSONL + schemas + notebook + manifest)]
    end

    classDef artifact fill:#f5f5f5,stroke:#888,stroke-dasharray:3 3;
    class events,manifest,dir,traceability,matrix,svr,rval,qsum,incident,rrr,rar,ir,programme,bundle artifact;
```

## Honesty rules visible in this flow

- **Every layer is read-only with respect to the layer below it.**
  Programme review never mutates incidents; reviewer export never
  mutates programme review.
- **`static_only` and `missing_bag` flags propagate verbatim**
  from the runtime layer all the way to
  `reviewer-export/csv/replay_quality.csv`.
- **Aggregations refuse to claim causality.** Programme review and
  reliability impact use correlation language; the reviewer export
  pins `causality_claimed` to `const: false` at schema level.
- **Missing inputs are reported, not synthesised.** Loaders emit
  structured warnings; reports use `insufficient_history` /
  `unknown` / `not_started`.

## Related documents

- [`docs/EVENT_MODEL.md`](../EVENT_MODEL.md)
- [`docs/REPLAY_SYSTEM.md`](../REPLAY_SYSTEM.md)
- [`docs/VERIFICATION_STRATEGY.md`](../VERIFICATION_STRATEGY.md)
- [`docs/PROGRAMME_REVIEW.md`](../PROGRAMME_REVIEW.md)
- [`docs/REVIEWER_EXPORTS.md`](../REVIEWER_EXPORTS.md)
- [`docs/diagrams/replay-flow.md`](replay-flow.md)

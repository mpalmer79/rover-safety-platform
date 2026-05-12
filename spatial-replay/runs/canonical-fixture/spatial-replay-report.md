# Spatial replay report — canonical-fixture

The platform is **not safety-certified.** This report describes the spatial-replay artefact for one run; it never asserts that real telemetry was captured unless the derivation source is `bag_backed`.

## Summary

- **Run:** `canonical-fixture`
- **Scenario:** `warehouse_pickup_route_alpha`
- **Mission:** `warehouse_pickup_route_alpha`
- **Derivation source:** `fixture`
- **Bag status:** `missing_manifest`
- **Trajectory status:** `complete`
- **Validation status:** `passed`
- **Sample count:** 10
- **Segment count:** 9

Spatial samples are derived from a committed fixture. **These are not bag-backed evidence.** They exist to regression-test the trajectory + alignment code paths.

## Known limitations

- fixture-derived spatial samples; not bag-backed evidence
- bag manifest missing or unparseable

## Next step

Produce a real bag-backed run on a qualified self-hosted runner. Once the bag manifest validates, this run will be labelled `bag_backed` automatically.

# Replay Gap Analysis

This document describes the gap detection and recommendation
generator in `backend/app/replay_analytics/recommendations.py`. The
platform is **not safety-certified**; the gap analysis is
engineering analytics material.

## 1. Principle: cite the evidence

Every gap is grounded in a specific evidence path. Recommendations
cite the artefacts that triggered them. No AI-generated vague
suggestions.

## 2. Gap labels and severity

| Label | Severity | Trigger |
| --- | --- | --- |
| `replay_review_missing` | critical | bundle has no Phase-7 manifest / report |
| `missing_bag` | high | bag indices contain no chunks or metadata |
| `static_only_evidence` | moderate | incident is static-only |
| `missing_topic[<topic>]` | high | a required topic is absent from the bag inventory |
| `markers_missing` | moderate | replay-markers.json absent or empty |
| `poor_marker_alignment` | moderate | <50% of markers are at exact alignment |
| `incident_contradictions` | high | the Phase-6 incident report lists contradictions |
| `incomplete_review_artefacts` | low | the bundle is missing canonical review files |

## 3. Recommendations

The mapping is one-to-one and deterministic:

| Gap | Recommendation |
| --- | --- |
| `replay_review_missing` | run `build_replay_review_bundle.py` |
| `missing_bag` | capture rosbag2 on a Jazzy host; place under `<bundle>/bags/` |
| `static_only_evidence` | rerun the scenario with `qualified_runtime_run.py --ros-launch` |
| `missing_topic[<t>]` | add `<t>` to the rosbag2 record set |
| `markers_missing` | rerun `reconstruct_incident.py`; extend incident_analysis if needed |
| `poor_marker_alignment` | align manually; record corrected offsets in operator notes |
| `incident_contradictions` | reconcile the underlying evidence or annotate the report |
| `incomplete_review_artefacts` | rerun `build_replay_review_bundle.py` / `reconstruct_incident.py` |

## 4. CLI usage

```bash
python3 rover_ws/tools/analyze_replay_coverage.py \
  --incident incidents/<incident_id>
# Writes replay-gaps.json + replay-recommendations.json into the bundle dir.

python3 rover_ws/tools/generate_replay_analytics.py
# Aggregates incidents/analytics/replay-gap-analysis.md.
```

## 5. Honesty rules

- A gap is emitted only when the underlying evidence is genuinely
  missing or inconsistent. No "informational" gaps are added to
  pad the list.
- Recommendations cite at least one evidence path (bundle dir,
  manifest path, markers path, etc.).
- The "no gaps detected" recommendation is itself an explicit
  message: it does not silently disappear when the bundle is
  clean.

## 6. Related documents

- [docs/REPLAY_ANALYTICS.md](REPLAY_ANALYTICS.md)
- [docs/REPLAY_QUALITY_SCORING.md](REPLAY_QUALITY_SCORING.md)
- [docs/REPLAY_REVIEW_AUDIT.md](REPLAY_REVIEW_AUDIT.md)

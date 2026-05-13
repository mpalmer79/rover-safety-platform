# Evidence Freshness Policy

Phase 10's freshness reporter compares each artifact's
`generated_at_utc` against a caller-supplied reference time. The
layer is forbidden from calling `datetime.now()` internally so
tests are deterministic. The platform is **not safety-certified**;
freshness is engineering hygiene material.

## 1. Thresholds (default)

| Record type | Threshold |
| --- | --- |
| reliability-impact bundles | 14 days |
| replay analytics reports | 14 days |
| runtime qualification reports | 30 days |
| replay review reports | 30 days |
| incident reports | 60 days |

Callers can override thresholds per record type. CI never auto-
adjusts thresholds.

## 2. Status vocabulary

| Status | Meaning |
| --- | --- |
| `fresh` | age < threshold |
| `stale` | age ≥ threshold |
| `unknown` | no parseable `generated_at_utc` on the record |

## 3. Reference time

Tests supply fixture timestamps; CI passes UTC `now` explicitly.
The library never reads the system clock.

## 4. Honesty rules

* `unknown` is preferred to a guess when the record has no
  timestamp.
* Wall-clock thresholds are caller-supplied.
* The report records the reference time so a reviewer can
  reproduce the assessment.

## 5. Related documents

- [docs/PROGRAMME_REVIEW.md](PROGRAMME_REVIEW.md)
- [docs/GOVERNANCE_HEALTH_MODEL.md](GOVERNANCE_HEALTH_MODEL.md)

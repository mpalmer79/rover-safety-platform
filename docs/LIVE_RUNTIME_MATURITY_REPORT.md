# Live Runtime Maturity Report

_This project is not safety-certified. Live runtime evidence demonstrates engineering qualification discipline; it is not a regulatory artefact._

- **Generated (UTC):** 2026-05-12T00:00:00+00:00
- **Evidence root:** `evidence/runtime`
- **Runs total:** 2
- **Latest run id:** `static-2026-05-09`
- **Latest run status:** `not_executed`
- **Runner status:** `unknown`

## Run-status counts

| Status | Count |
| --- | --- |
| `not_executed` | 2 |

## Bag counters

| Bag status | Count |
| --- | --- |
| `bag_backed` | 0 |
| `missing_bag` | 0 |
| `partial` | 0 |
| `not_executed` | 2 |
| `invalid` | 0 |

## Downstream integration status

| Pipeline | Status |
| --- | --- |
| Replay review | `not_started` |
| Replay analytics | `integrated` |
| Programme review | `integrated` |

## Known limitations

- no bag-backed evidence on disk; downstream replay review and analytics still consume canonical fixtures
- 2 live runs are marked not_executed (honest fall-back)
- runner profile does not currently certify Jazzy + Gazebo + rosbag2

## Next actions

- provision a self-hosted Jazzy + Gazebo runner
- execute live-runtime-evidence.yml on a self-hosted runner to produce bag-backed artefacts
- feed bag-backed evidence into incident reconstruction and replay analytics so programme review picks up live trends

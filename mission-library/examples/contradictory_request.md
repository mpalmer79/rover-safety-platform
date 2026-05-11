# Example: contradictory_request

_Two clauses disagree about waypoint alpha; compiler rejects._

- Expected status: `compile_rejected`
- Actual status: `compile_rejected`
- Risk: `critical` (score `95`)
- Objectives: 2
- Constraints: 1
- Diagnostics: 1

## Intent

> Drive to waypoint alpha. Do not enter waypoint alpha. Return to dock.

## Files

- plan json: `mission-library/rejected/contradictory_request.json`
- plan md:   `mission-library/rejected/contradictory_request.md`
- audit:     `mission-library/audits/contradictory_request-audit.json`
- replay:    `mission-library/rejected/contradictory_request-replay-binding.json`

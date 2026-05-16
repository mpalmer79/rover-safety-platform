# LLM Candidate Ranking Model (Phase 19)

The platform is **not safety-certified.** This document records the
deterministic scoring used by `candidate_ranker.rank_candidates`.

## 1. Inputs

The ranker scores triples of `(candidate, sanitizer_result,
validator_result)`. Multiple triples can be ranked together.

## 2. Signal table

| Signal                                       | Δ score |
|----------------------------------------------|--------:|
| sanitizer accepted                           |     0   |
| sanitizer rejected                           |   -200  |
| validator invoked + accepted                 |    +50  |
| validator invoked + rejected                 |   -100  |
| code includes a final zero-Twist stop        |    +10  |
| code has a bounded timeout / monotonic clock |    +10  |
| code uses `/cmd_vel_requested`               |     +8  |
| code matches a forbidden import (per match)  |    -50  |
| code mentions bounded speed                  |     +6  |
| code mentions bounded distance               |     +6  |
| explanation provided                         |     +4  |
| disclosed uncertainties                      |     +3  |
| overconfident WITHOUT validator acceptance   |    -25  |

## 3. Tie-breaking

When two candidates resolve to the same total score, the ranker
breaks ties by ascending `candidate_id`. This keeps the ranking
fully reproducible across re-runs.

## 4. Honesty rules

- The ranker never reads `confidence_label` in isolation; it only
  applies a penalty when high/overconfident is unaccompanied by a
  validator acceptance.
- The ranker never decides safety; it only re-orders candidates.
  The accepted candidate is *exactly* the candidate the validator
  accepted; the rank ordering is reviewer guidance.
- The ranker never opens a socket or invokes an external service.
- The signal table is intentionally small + transparent — the
  Phase 19 tests `test_validator_outcome_dominates_ranking` and
  `test_sanitizer_rejection_dominates` lock the dominant signals.

## 5. Forbidden imports list

```
import os
import subprocess
import socket
import requests
from os
from socket
open("/etc/
```

The list lives in `backend/app/skill_llm_provider/candidate_ranker.py`
under `FORBIDDEN_IMPORT_HINTS`. Adding a new pattern requires a
matching test in `backend/tests/test_skill_llm_intelligence.py`.

## 6. Serialisation

`ranking_to_dict()` returns a JSON-friendly dict that includes the
full signal breakdown for every candidate. The audit bundle's
`ranking-result.json` artifact embeds this list.

## 7. Related docs

- `docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md`
- `docs/LLM_REPAIR_SUGGESTIONS.md`
- `docs/LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md`

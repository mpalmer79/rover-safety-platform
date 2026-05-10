# Incident Timeline — `canonical-estop-latched`

- **Entry count:** 54
- **First fault:** -
- **First safety transition:** #2 (0ms, `safety_transition.entered`)
- **First command intervention:** #3 (0ms, `motion_arbitration.zeroed`)
- **Terminal entry:** #6 (1500ms, `safety_transition.entered`)

| # | t (ms) | Category | Event | Severity | Safety | Reason | Source |
|---|---|---|---|---|---|---|---|
| 0 | 0 | `system_lifecycle` | `system_lifecycle.boot` | `INFO` | `BOOT` | boot | `events.jsonl` |
| 1 | 0 | `system_lifecycle` | `system_lifecycle.node_activated` | `INFO` | `BOOT` | scenario_loaded | `events.jsonl` |
| 2 | 0 | `safety_transition` | `safety_transition.entered` | `INFO` | `INACTIVE` | boot_complete | `events.jsonl` |
| 3 | 0 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `INACTIVE` | inactive_zero | `events.jsonl` |
| 4 | 100 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `INACTIVE` | inactive_zero | `events.jsonl` |
| 5 | 200 | `safety_transition` | `safety_transition.entered` | `INFO` | `ACTIVE_NORMAL` | operator_activate | `events.jsonl` |
| 6 | 1500 | `safety_transition` | `safety_transition.entered` | `CRITICAL` | `E_STOP_LATCHED` | operator_estop | `events.jsonl` |
| 7 | 1500 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 8 | 1600 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 9 | 1700 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 10 | 1800 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 11 | 1900 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 12 | 2000 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 13 | 2100 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 14 | 2200 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 15 | 2300 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 16 | 2400 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 17 | 2500 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 18 | 2600 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 19 | 2700 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 20 | 2800 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 21 | 2900 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 22 | 3000 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 23 | 3100 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 24 | 3200 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 25 | 3300 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 26 | 3400 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 27 | 3500 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 28 | 3600 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 29 | 3700 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 30 | 3800 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 31 | 3900 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 32 | 4000 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 33 | 4100 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 34 | 4200 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 35 | 4300 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 36 | 4400 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 37 | 4500 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 38 | 4600 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 39 | 4700 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 40 | 4800 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 41 | 4900 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 42 | 5000 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 43 | 5100 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 44 | 5200 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 45 | 5300 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 46 | 5400 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 47 | 5500 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 48 | 5600 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 49 | 5700 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 50 | 5800 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 51 | 5900 | `motion_arbitration` | `motion_arbitration.zeroed` | `WARNING` | `E_STOP_LATCHED` | e_stop_zero | `events.jsonl` |
| 52 | ? | `motion_arbitration` | `motion_arbitration.summary` | `INFO` | `-` | command_audit_summary | `command-audit.json` |
| 53 | ? | `replay` | `replay.integrity_summary` | `INFO` | `-` | replay_integrity_summary | `replay-integrity.json` |

# Why This Project Exists

The platform is **not safety-certified**. This document explains the
engineering motivation behind it and the gap it tries to close.

## 1. The motivating gap

Most portfolio robotics projects answer "can the robot move?"
Industrial, aerospace, defence-adjacent and warehouse robotics teams
spend their lives on a harder question:

> *When the robot moves, can you prove the autonomy stack could not
> have moved it unsafely — and can you reconstruct exactly what
> happened if something goes wrong?*

That second question is the one that decides whether a system can be
deployed into a regulated, supervised, or shared-space environment.
It needs:

- a safety supervisor with **single-point authority** over actuation,
- **deterministic** decision paths so behaviour is repeatable,
- **structured events** sufficient to reconstruct an incident,
- **traceability** from requirement to test to evidence,
- a **review surface** auditors and reliability engineers can read,
- **honest reporting** of what was executed live, what was simulated,
  what was static, and what is missing.

Project Boundary is built to demonstrate those disciplines end-to-end
on a deliberately small problem (a simulated rover) so the
architecture, not the autonomy, is what stands out.

## 2. What this project is not

It is not:

- a safety-certified system,
- a production rover stack,
- a SLAM / perception research project,
- a reinforcement-learning demo,
- a marketing artefact.

It does not claim ISO 26262, DO-178C, IEC 61508, or any other
certification status. It demonstrates the *patterns* common to those
regimes — separated authority, bounded behaviour, deterministic
execution, replayable state, traceable requirements — without
claiming the formal process artefacts they require.

## 3. Why a simulation-first scope

Real hardware would expand scope without adding architectural
clarity. Sim-first lets the project:

- exercise every safety transition deterministically,
- emit identical evidence on any host (no Jazzy required for the
  Python core),
- run a full programme review in CI without a robot in the loop,
- keep the reviewer's attention on architecture, evidence, and
  honesty rather than on hardware glue.

The ROS 2 / Gazebo workspace is the intentional bridge to runtime —
it shares the same event, motion-authority, fault-injection, and
replay contracts as the Python core, and falls back to static
validation when no Jazzy host is available (and *says so* rather
than skipping the gap).

## 4. The audiences this project tries to serve

| Audience | What they should be able to verify quickly |
| --- | --- |
| Recruiter / non-technical reviewer | The project is real, the scope is honest, the disclaimers are explicit. |
| Senior software engineer | The architecture has invariants, the invariants are tested, the tests produce evidence. |
| Robotics / ROS 2 reviewer | The ROS 2 layer honours the same contracts as the deterministic core, with explicit static-only fall-backs. |
| Verification / reliability reviewer | Requirements, scenarios, tests, and evidence are mechanically linked, and reports distinguish passed / failed / partial / skipped / not_executed. |

See [`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md) for the per-audience reading paths.

## 5. The honesty rules baked into the project

These are non-negotiable across every phase:

1. **No safety-certification claim**, anywhere.
2. **No fake green** — reports use `passed`, `failed`, `partial`,
   `skipped`, or `not_executed`; absences are labelled, not
   silently dropped.
3. **No causal claims** in aggregation layers — frequencies and
   correlations are reported as observations.
4. **Static-only stays static-only** — bag-backed evidence and
   static-only evidence never silently mix.
5. **Missing history is reported** — never synthesised, never
   forecast.
6. **Faults alter inputs, not state** — fault injection mutates
   sensor readings; the supervisor reacts through normal
   mechanisms.
7. **Mission requests, supervisor authorises** — no other path can
   actuate motion.

## 6. What "Phase 13" would have to prove

Phase 12 closes the documentation / portfolio-presentation gap.
Live runtime maturity is a separate question. A future Phase 13
would have to demonstrate:

- live ROS 2 / Gazebo execution on a Jazzy host with bag capture,
- live runtime validation reports (currently static-only fall-back
  is honestly labelled as such),
- live qualification runs producing `evidence/runtime/<id>/...`
  bundles automatically in CI on a Jazzy runner,
- live Foxglove replay sessions producing `replay-review-report.json`
  artefacts from real bags, not canonical fixtures,
- a published reliability impact report against a real source-change
  series, not the canonical fixture.

Until those exist, the platform's runtime claims are exactly what
the docs say they are: simulated, static, or canonical-fixture-driven.

## 7. Related documents

- [`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md) — reading paths by audience
- [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) — one-page overview
- [`ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md) — module tour
- [`PORTFOLIO_CASE_STUDY.md`](PORTFOLIO_CASE_STUDY.md) — narrative arc
- [`LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md) — what is live vs static today

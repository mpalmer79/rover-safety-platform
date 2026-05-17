# LLM Mission Proposal Layer (Phase 14B)

The platform is **not safety-certified.** Phase 14B adds an
*offline, pluggable* seam for a future LLM to propose mission
*candidates*. The deterministic mission compiler (Phase 14A) and
the runtime safety supervisor remain authoritative.

> **No real LLM calls are implemented in Phase 14B.** The provider
> seam exists so a future phase can add one; external provider
> modes return a deterministic ``not_configured`` response.

## 1. Architectural placement

```
natural-language request
       │
       ▼
   ProposalProvider.propose         <-- mock / offline_fixture only
       │
       ▼
   MissionProposal (raw, untrusted)
       │
       ▼
   sanitize_proposal                <-- rejects unsafe / forbidden phrases
       │
       ▼
   adapt_proposal_to_compiler_input
       │
       ▼
   compile_intent (Phase 14A)       <-- deterministic, offline
       │
       ▼
   ProposalAudit                    <-- read-only artifact bundle
```

The proposal layer is bounded above (a sanitizer that rejects unsafe
text before it is interpreted) and below (the deterministic Phase
14A compiler that interprets only sanitized text). Neither side
publishes actuator commands. The runtime safety supervisor remains
the only path to authorised motion.

## 2. Modules

| Module                                              | Role                                                    |
|-----------------------------------------------------|---------------------------------------------------------|
| `backend/app/mission_proposal/models.py`            | dataclasses + status / mode / confidence constants      |
| `backend/app/mission_proposal/schema.py`            | JSON schemas for proposals and audits                   |
| `backend/app/mission_proposal/validator.py`         | structural validation of proposal payloads              |
| `backend/app/mission_proposal/sanitizer.py`         | forbidden-phrase chokepoint                             |
| `backend/app/mission_proposal/provider.py`          | abstract provider interface + external-disabled helper  |
| `backend/app/mission_proposal/mock_provider.py`     | deterministic mock provider + fixture set               |
| `backend/app/mission_proposal/adapter.py`           | sanitize -> compile pipeline                            |
| `backend/app/mission_proposal/audit.py`             | builds the per-proposal audit bundle (JSON + Markdown)  |
| `backend/app/mission_proposal/reporter.py`          | filesystem reporter for audit bundles                   |

## 3. Provider modes

| Mode                | Behaviour                                                                       |
|---------------------|---------------------------------------------------------------------------------|
| `mock`              | Picks a fixture by substring of the request text. Deterministic.                |
| `offline_fixture`   | Returns the fixture matching the supplied ``fixture_id``. Deterministic.        |
| `external_disabled` | Returns the canonical ``not_configured`` response. No network call is made.     |

Any other mode raises ``ProposalProviderError``.

## 4. Provider proposal schema

Required fields:

```text
proposal_id
source_text
provider_name
provider_mode
proposed_intent
proposed_location
proposed_motion_style
proposed_constraints       # list of strings
proposed_recovery_policy
confidence_label           # low | medium | high | overconfident
known_uncertainties        # list of strings
raw_response
```

The validator (``validate_proposal_dict``) refuses any payload that
omits a required field, uses an unknown provider mode, or uses an
unknown confidence label.

## 5. Sanitizer rules

The sanitizer rejects proposals whose text matches any of:

* direct actuator commands (``cmd_vel`` / ``/cmd_vel``)
* safety overrides (``ignore safety``, ``disable safety``,
  ``disable safety supervisor``)
* e-stop overrides
* sensor disables (``disable lidar``)
* continue-despite-failure directives
* shell or code execution requests
* network commands (``curl http``)
* destructive shell commands (``rm -rf``)
* self-declared unknown-location / unsupported-intent strings

Rejection is total: the compiler is never invoked on rejected text.
The sanitizer is the only chokepoint that interprets unsafe phrases
in any form; the compiler then only ever sees sanitized text.

## 6. Adapter outcomes

| Outcome                                | Meaning                                                              |
|----------------------------------------|----------------------------------------------------------------------|
| `proposal_accepted_by_provider`        | provider returned a payload but no further pipeline ran              |
| `proposal_rejected_by_sanitizer`       | sanitizer blocked unsafe phrases; compiler not invoked               |
| `proposal_rejected_by_compiler`        | sanitized text was rejected by the deterministic compiler            |
| `proposal_compiled_requires_review`    | compiled but the compiler flagged the result as ambiguous            |
| `proposal_compiled_validation_passed`  | compiled cleanly; downstream mission runtime can be considered       |

Even ``proposal_compiled_validation_passed`` is **not** an
authorisation to move the robot — that decision still belongs to the
runtime safety supervisor and motion arbitration.

## 7. CLIs

```
rover_ws/tools/propose_mission_from_text.py
    --text "Inspect loading_zone_two slowly"
    --provider mock
    --proposal-id p-001
    --output mission-proposals/audits/p-001
    [--fixture-id mock_valid_inspection]
    [--generated-at <iso8601>]

rover_ws/tools/validate_mission_proposal.py
    --proposal mission-proposals/examples/mock_valid_inspection.json
    [--run-sanitizer]

rover_ws/tools/generate_mission_proposal_examples.py
    [--examples-dir mission-proposals/examples]
    [--audits-dir mission-proposals/audits]
    [--generated-at 2026-05-12T00:00:00+00:00]
```

No CLI calls a remote API. The ``--provider external`` alias (and
any of ``openai``, ``anthropic``, ``cohere``, ``external_disabled``)
deterministically writes the ``not_configured`` response and exits 0
without invoking the compiler.

## 8. Determinism

Identical input yields byte-identical output. The provider, the
sanitizer, the adapter, and the audit all use sorted JSON keys. The
mock provider's fixture selection is deterministic. The Phase 14A
compiler is byte-deterministic. The CLI accepts ``--generated-at``
to pin the timestamp; tests use a fixed timestamp so audit bundles
are stable across runs.

## 9. Not implemented (intentionally)

* real OpenAI / Anthropic / Cohere / Vertex / Replicate calls
* network egress of any kind
* real-time mission execution from a proposal
* publication to ``/cmd_vel`` or any actuator topic
* mutation of the safety supervisor
* fabricated runtime evidence

See `docs/DEFERRED_PHASES.md#llm-mission-proposal-layer` for what a follow-up
phase would need to add (and what it must not).

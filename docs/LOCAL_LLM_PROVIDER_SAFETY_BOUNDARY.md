# Local LLM Provider Safety Boundary

The platform is **not safety-certified.** This document records the
strict separation between the Phase 15B local LLM skill provider
and the runtime safety authority.

## 1. The architecture in one diagram

```
   developer request
         │
         ▼
   Phase 15B LLM provider (disabled by default)
         │
         ▼
   candidate code (untrusted)
         │
         ▼
   sanitizer (forbidden-phrase chokepoint)
         │
         ▼
   Phase 15A skill validator (deterministic)
         │
         ▼
   safety review + code card
         │
         ▼
   developer reviews the bundle
         │
         ▼
   developer runs the snippet on a workstation
         │
         ▼
   snippet publishes /cmd_vel_requested
         │
         ▼
   Safety supervisor  ────────────  authoritative
         │
         ▼
   Motion arbitration
         │
         ▼
   Authorized command  ───────────  /cmd_vel_authorized
```

The Phase 15B layer never publishes anything, never opens a network
socket in this phase, and never grants actuator authority.

## 2. What the LLM provider CAN do

* return a structured candidate (in fixture mode only; other modes
  are policy-checked stubs);
* pass the candidate through the sanitizer;
* invoke the Phase 15A deterministic validator on sanitized code;
* emit an audit bundle and a code-card payload for the future
  reviewer UI.

## 3. What the LLM provider MUST NOT do

| Forbidden                                              | Enforcement                                                  |
|--------------------------------------------------------|--------------------------------------------------------------|
| call OpenAI / Anthropic / Cohere / cloud APIs          | no SDK imports; AST-level test                               |
| import `ollama` or `llama_cpp` SDKs                    | AST-level test asserts no SDK import                         |
| require an API key                                     | no env var or config key for secrets                         |
| open a network socket                                  | local providers are policy-only stubs in this phase          |
| call any non-loopback endpoint                         | `require_local_endpoint` rejects before the provider runs   |
| call HTTPS endpoints                                   | `require_local_endpoint` rejects                              |
| import `socket`, `urllib.request`, `requests`, `httpx` | AST-level test                                                |
| execute generated code                                 | reporter only writes JSON / Markdown; CLI never `exec`s      |
| publish to ROS                                         | no `rclpy` import in the provider package                    |
| bypass the sanitizer                                   | adapter always calls `sanitize_candidate` first              |
| bypass the Phase 15A skill validator                   | accepted candidates ALWAYS pass `validate_generated_code`    |
| claim safety supervisor approval                       | audit emits "not safety-certified" disclaimer                |
| direct `/cmd_vel` publication in accepted code         | sanitizer + Phase 15A validator both reject                  |
| `while True:` in accepted code                         | sanitizer + Phase 15A validator both reject                  |
| shell / code / network commands in accepted code       | sanitizer rejects                                            |
| secret patterns (`api_key=`, `password=`, `secret=`)   | sanitizer rejects                                            |
| safety / e-stop overrides                              | sanitizer rejects                                            |

## 4. Sanitizer rule set

The sanitizer rejects candidates whose code, declared topics,
declared interfaces, declared safety constraints, or raw provider
payload references any forbidden fragment in
`FORBIDDEN_FRAGMENTS`. Specific reasons surface in the audit as
:class:`CandidateRejectionReason` codes:

* `direct_actuator_command` — direct `/cmd_vel`, `ros2 topic pub /cmd_vel`;
* `unbounded_motion` — `while True`;
* `shell_or_code_execution` — `subprocess`, `os.system`, `eval(`, `exec(`;
* `network_access` — raw `socket.socket`, `urllib.request`,
  `requests.get`/`post`, `httpx.*`, `import openai`, `import anthropic`,
  `import cohere`;
* `secret_leak` — `api_key=`, `password=`, `secret=`, `API_KEY`;
* `destructive_command` — `rm -rf`, `sudo`, `chmod`, `chown`;
* `direct_motor_control` — `direct motor` references;
* `safety_override` — disable safety, ignore safety, e-stop override.

The explanation field is allowed to mention `/cmd_vel` in a
descriptive context (e.g. "never publish to /cmd_vel directly")
because the model is supposed to describe the boundary. Code,
topics, and interfaces have no such exemption.

## 5. Validator bridge

After the sanitizer accepts, the bridge invokes
`app.skill_authoring.validator.validate_generated_code` with the
candidate's `skill_type` and `code`. The Phase 15A validator
applies the existing REQUIRED_CODE_TOKENS / forbidden-token rules.
The bridge records `invoked=True` and any rejection diagnostics in
the audit.

When the sanitizer rejects, the bridge records `invoked=False` and
does not call the validator at all. The audit then shows both
sanitizer rejection AND a deliberately-skipped validator.

## 6. Honesty rules

* No artefact in `skill-llm-candidates/` represents a real model
  inference.
* No artefact in `skill-llm-candidates/` represents a runtime
  mission or actuator authorisation.
* No artefact in `skill-llm-candidates/` is generated by a cloud
  LLM call.
* A candidate that reaches `final_status: accepted` is *eligible*
  for developer review. It is not authorised to run on the robot.

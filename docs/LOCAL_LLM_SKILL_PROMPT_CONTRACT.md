# Local LLM Skill Prompt Contract

The platform is **not safety-certified.** This document defines the
JSON-only prompt contract a future local LLM must satisfy when it
proposes a robotics-skill candidate via the Phase 15B provider
seam. Phase 15B does not call the model itself; the contract
exists so a follow-up phase can wire it up without re-litigating
the safety rules.

## 1. The contract in one sentence

> The model returns a single JSON object that describes a candidate
> robotics skill. The validator decides whether the candidate is
> safe. The model never decides.

## 2. Required JSON fields

```jsonc
{
  "language": "python_ros2",                       // SkillLanguage value
  "skill_type": "move_forward_distance",           // Phase 15A SkillType value
  "code": "...",                                    // full snippet text
  "explanation": "Short, neutral description.",
  "declared_topics": ["/cmd_vel_requested"],       // list of strings
  "declared_interfaces": ["geometry_msgs/msg/Twist"],
  "declared_safety_constraints": [
    "distance_meters <= 25.0",
    "linear_speed_mps <= 0.5",
    "final zero Twist must be published"
  ],
  "confidence_label": "medium",                    // low | medium | high | overconfident
  "known_uncertainties": [
    "rover wheel slip may cause actual distance to differ"
  ]
}
```

A `raw_provider_payload` field will be filled in by the provider
transport from the literal text the model returned; the model itself
does not have to set it.

## 3. Required behavioural rules

The model **must**:

* publish only to `/cmd_vel_requested` (or a mission-request topic
  for waypoint / patrol templates);
* include a bounded duration, count, or watchdog;
* include a final zero `Twist` for any motion-bearing snippet;
* mention the safety supervisor in a comment header;
* declare every published topic in `declared_topics`;
* declare every safety constraint it claims to honour in
  `declared_safety_constraints`;
* set `confidence_label` honestly. ``overconfident`` is allowed but
  flags the audit for human review.

The model **must not**:

* publish to `/cmd_vel` directly;
* import `socket`, `urllib.request`, `requests`, `httpx`, `openai`,
  `anthropic`, `cohere`, `subprocess`, or `os.system`;
* use `eval(` or `exec(`;
* use `while True:` (use a bounded loop);
* include API keys, passwords, or secrets;
* execute shell commands;
* claim that the robot has moved or that safety supervisor has
  approved;
* invent waypoint names that the Phase 15A catalog does not know.

## 4. Failure handling

Even if the model violates the contract above, the Phase 15B
sanitizer and Phase 15A validator catch it. The contract documents
the model's *intent*; the sanitizer and validator are the
chokepoints that enforce it.

## 5. JSON only

The model output must be a single JSON object. Free-form text,
Markdown, code fences, or multiple JSON objects MUST be parsed
defensively by the transport. If the transport cannot recover a
single valid object, it emits an
``INVALID_PROVIDER_OUTPUT`` envelope and the candidate is
discarded.

## 6. Example output

```jsonc
{
  "language": "python_ros2",
  "skill_type": "move_forward_distance",
  "code": "# Move forward 1.8288 m by publishing /cmd_vel_requested.\n# Safety supervisor authorises actual motion via /cmd_vel_authorized.\n# Not safety-certified.\nimport rclpy\nfrom rclpy.node import Node\nfrom geometry_msgs.msg import Twist\n\nDISTANCE_M = 1.8288\nLINEAR_SPEED_MPS = 0.25\nDURATION_S = DISTANCE_M / LINEAR_SPEED_MPS\nTIMEOUT_S = DURATION_S * 1.5\n# ... bounded loop, final zero Twist, etc.\n",
  "explanation": "Move forward 6 feet (1.8288 m) at 0.25 m/s by publishing /cmd_vel_requested. Never publish to /cmd_vel directly.",
  "declared_topics": ["/cmd_vel_requested"],
  "declared_interfaces": ["geometry_msgs/msg/Twist"],
  "declared_safety_constraints": [
    "distance_meters <= 25.0",
    "linear_speed_mps <= 0.5",
    "final zero Twist must be published"
  ],
  "confidence_label": "medium",
  "known_uncertainties": ["wheel slip on smooth flooring"]
}
```

## 7. Authority statement

The model proposes; the deterministic skill validator decides; the
safety supervisor remains the only path to actuator authority.

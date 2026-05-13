import { ShieldCheck } from "lucide-react";

import { Panel } from "@/components/Panel";
import { MermaidView } from "@/components/MermaidView";
import { PageSurface } from "@/components/PageSurface";

export const dynamic = "force-static";

const AUTHORITY_DIAGRAM = `flowchart TD
    A([Operator request])
    B([Sanitizer])
    C([Deterministic mission compiler])
    D([Mission validator])
    E([Safety supervisor])
    F([Motion arbitration])
    G([Authorised /cmd_vel_authorized])

    A --> B
    B -->|forbidden phrase| R1([Rejected])
    B --> C
    C -->|unsupported| R2([Unsupported])
    C --> D
    D -->|out of range| R3([Validator rejected])
    D --> E
    E -->|safety overrides| R4([Supervisor rejected])
    E --> F
    F --> G
`;

const AUTHORITY_RULES = [
  {
    label: "Only the safety supervisor authorises motion",
    detail:
      "Mission compiler, validator, skill workbench, and the rehearsal runtime can request motion via /cmd_vel_requested. Only the runtime supervisor produces /cmd_vel_authorized.",
  },
  {
    label: "Validator-rejected plans never reach the supervisor",
    detail:
      "REQ-REHEARSAL-003: the rehearsal state machine refuses to enter the `rehearsing` state unless the supervisor decision is `approved`.",
  },
  {
    label: "Sanitizer rejection skips the compiler",
    detail:
      "REQ-PROPOSAL-003 and REQ-SKILL-LLM-003: any unsafe phrase (direct /cmd_vel, disable safety, ignore estop, shell, network) short-circuits the pipeline before validation.",
  },
  {
    label: "Local LLM providers are disabled by default",
    detail:
      "REQ-SKILL-LLM-001: cloud endpoints are forbidden; local providers require an explicit operator opt-in flag AND an enabled provider config.",
  },
  {
    label: "Bag-backed evidence requires real bag artefacts",
    detail:
      "REQ-LIVE-001..005 / REQ-REHEARSAL-004: rehearsal replay artefacts always report `bag_backed=False`. The committed live runtime maturity remains `not_established`.",
  },
];

export default function SafetyPage() {
  return (
    <PageSurface>
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="label">Safety authority</p>
        <h1 className="display-1">Who can authorise motion</h1>
        <p className="text-base-700">
          No mission, generated skill, or operator request can directly
          authorize motion. Every path flows through deterministic
          validation and supervisor approval. Every stage records the
          reason it accepted or rejected the request, and every audit
          bundle preserves that decision verbatim.
        </p>
      </header>

      <Panel eyebrow="What this proves" title="Reviewer summary">
        <ul className="space-y-1.5 text-sm text-base-700">
          <li>• Unsafe phrases short-circuit the pipeline before validation.</li>
          <li>• Validator-rejected plans never reach the supervisor.</li>
          <li>• Only the supervisor can produce <code>/cmd_vel_authorized</code>.</li>
          <li>• Bag-backed evidence is gated on real bag artifacts; the demo build reports it as <code>not_established</code> verbatim.</li>
        </ul>
      </Panel>

      <Panel
        eyebrow="Authority chain"
        title="Pipeline diagram"
        trailing={<ShieldCheck className="h-4 w-4 text-accent" aria-hidden />}
      >
        <MermaidView source={AUTHORITY_DIAGRAM} />
      </Panel>

      <div className="grid gap-4 lg:grid-cols-2">
        {AUTHORITY_RULES.map((rule) => (
          <Panel key={rule.label} eyebrow="Rule" title={rule.label}>
            <p className="text-sm leading-relaxed text-base-700">{rule.detail}</p>
          </Panel>
        ))}
      </div>

      <Panel eyebrow="What this layer cannot do" title="Hard boundaries">
        <ul className="space-y-1.5 text-sm text-base-700">
          <li>• Move a real robot.</li>
          <li>• Publish to <code>/cmd_vel</code> directly.</li>
          <li>• Open a network socket from the mission-control UI.</li>
          <li>• Call cloud LLM APIs.</li>
          <li>• Execute generated code.</li>
          <li>• Claim safety certification.</li>
          <li>• Mark a simulated rehearsal as bag-backed.</li>
        </ul>
      </Panel>
    </div>
    </PageSurface>
  );
}

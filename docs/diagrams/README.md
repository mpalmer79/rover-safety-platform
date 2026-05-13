# Diagrams

The platform is **not safety-certified**. These diagrams support
the [`REVIEWER_PLAYBOOK.md`](../REVIEWER_PLAYBOOK.md) and the
[`ARCHITECTURE_WALKTHROUGH.md`](../ARCHITECTURE_WALKTHROUGH.md).

All diagrams are inline Mermaid in markdown so GitHub renders them
without any extra tooling.

| Diagram | Purpose |
| --- | --- |
| [`system-flow.md`](system-flow.md) | High-level system flow across the deterministic core, runtime layer, and evidence layer |
| [`safety-authority.md`](safety-authority.md) | Single-authority motion-command path |
| [`evidence-flow.md`](evidence-flow.md) | How evidence flows from a scenario through audits, programme review, and reviewer export |
| [`replay-flow.md`](replay-flow.md) | Event recording → replay → reconstruction |

## Conventions

- Solid arrows are runtime / authority paths.
- Dashed arrows are evidence / read-only paths.
- A double border on a node means it is the **authority surface**
  (only the safety supervisor authorises motion).
- A dotted box means *generated artifact*, not *executable code*.

If GitHub does not render Mermaid for you, copy the fenced block
into a Mermaid live editor.

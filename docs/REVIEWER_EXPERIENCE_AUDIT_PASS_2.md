# Reviewer Experience Audit

## Purpose

This document reviews the public-facing ProjectBoundary Mission Control experience from the perspective of an external reviewer, recruiter, hiring manager, or technical evaluator.

The goal is not to evaluate whether the underlying engineering is impressive. The goal is to determine whether the deployed portfolio experience clearly communicates the project’s value, guides a first-time visitor through the workflow, and avoids confusing internal implementation details.

ProjectBoundary is technically dense. The current deployment exposes a large amount of audit, replay, safety, and deterministic pipeline detail. That depth is valuable, but the public reviewer experience needs a clearer narrative layer so visitors understand what they are seeing and why it matters.

## Audience

Primary audience:

- Recruiters
- Hiring managers
- Technical screeners
- Engineering managers
- Portfolio reviewers

Secondary audience:

- Senior engineers reviewing system design
- Robotics, autonomy, or safety-focused reviewers
- Future maintainers of the project

## Executive Summary

The current site demonstrates significant technical ambition, especially around deterministic mission validation, supervisor authority, replay evidence, auditability, and simulation-only safety boundaries.

However, the public experience is not yet fully reviewer-ready. The site currently exposes too much internal build terminology, includes at least one broken or incomplete navigation route, references 3D and spatial replay capabilities that are not available in the deployed experience, and lacks a simple “start here” path for non-domain reviewers.

The project has strong foundations, but the deployed UI needs a product narrative pass. The main issue is not lack of engineering. The issue is that the current experience assumes the reviewer already understands the system.

## Severity Model

| Severity | Meaning |
|---|---|
| P0 | Blocks trust or creates a broken public experience |
| P1 | Confuses the reviewer or weakens the product narrative |
| P2 | Reduces polish or makes the project feel unfinished |
| P3 | Future enhancement or quality improvement |

## High-Priority Findings

### P0: Components / Catalog route is broken or incomplete

The left navigation includes a **Components** link. When selected, the deployed site displays a missing artifact page instead of a component catalog or design-system view.

Observed message: `No artifact at this path`

The page states that the platform did not commit a JSON artifact for the route and suggests that the path may be a typo or renamed artifact.

This should not be visible in the public portfolio experience.

#### Why this matters

A broken navigation item reduces reviewer confidence immediately. Even if the underlying system is strong, a recruiter or hiring manager may interpret this as an unfinished project or weak deployment discipline.

#### Recommended fix

Either restore the component catalog route and ensure it is included in the static export, or remove the Components link from public navigation until the route is ready.

Preferred outcome: `/catalog` should render a polished design-system page or should not appear in navigation.

---

### P1: “Phase 19” appears in public navigation without context

The navigation and header repeatedly label the site as **Phase 19**. This appears to be internal build terminology.

The Safety Authority page also references a **Phase 14A compiler**, which adds more internal phase language without explanation.

#### Why this matters

Internal phase labels may make sense during development, but they do not help an external reviewer understand the product. A recruiter may wonder whether they are viewing an unfinished build, a test branch, or a late-stage internal milestone.

#### Recommended fix

Replace public-facing phase labels with product-centered language.

Current: `Mission Control Phase 19`

Better: `ProjectBoundary Mission Control`

Current: `Phase 14A Compiler`

Better: `Deterministic Mission Compiler`

If phase terminology is important, move it into an engineering details panel or documentation section.

---

### P1: Spatial replay and 3D environment expectations are not met

The site references spatial replay, immersive visualization, scene snapshots, and related artifacts. However, the deployed experience repeatedly shows that spatial replay artifacts are missing.

Observed examples include:

- `No spatial artifact`
- `No spatial-replay artifact for this mission.`
- `Reviewer scene snapshot unavailable`
- `No artifact registered for this run.`

The Replay Viewer currently shows simple 2D tactical maps and waypoint scrubbers. These are useful, but they do not deliver the expected 3D or immersive experience.

#### Why this matters

The project appears to promise a stronger visual experience than it currently delivers. If a reviewer expects an impressive replay environment and instead sees “No artifact” panels, the experience feels incomplete.

This is especially important because the project is complex. A strong visual layer would help reviewers understand the system quickly.

#### Recommended fix

Choose one of two directions.

Option 1: Implement a real visual demo route.

- Add a dedicated `/demo` or `/mission-demo` route.
- Include one polished mission replay.
- Show robot position, zones, waypoints, safety events, and supervisor decisions.
- If true 3D is not ready, use a high-quality 2D simulation with animation.

Option 2: Reframe the current state honestly.

- Rename missing 3D sections as “2D fallback mode.”
- Replace “No artifact” messaging with intentional explanatory copy.
- Hide unavailable 3D panels from public reviewer mode.

Preferred outcome: A first-time reviewer should never land on an empty “No artifact” visualization panel without explanation.

---

### P1: The site lacks a clear “Start Here” reviewer path

The site contains a Reviewer Walkthrough, but the overall navigation does not clearly tell a new visitor where to begin.

The project includes many advanced surfaces:

- Dashboard
- Workspaces
- Proposal Workbench
- Replay Viewer
- Safety Authority
- Evidence & Audit
- Components

For a technical reviewer, this is valuable. For a recruiter, it is overwhelming.

#### Why this matters

A portfolio project needs two layers:

1. A simple story for non-domain reviewers.
2. A deep technical path for engineers.

The current deployment jumps directly into the deep technical layer.

#### Recommended fix

Add a prominent landing section or route called **Start Here: What ProjectBoundary Demonstrates**.

This page should explain:

- What the system is
- What problem it solves
- What the reviewer should click first
- What the safety pipeline demonstrates
- What is simulated
- What is intentionally not safety-certified
- What parts are still future work

Suggested reviewer path:

1. Start Here
2. Reviewer Walkthrough
3. Replay Viewer
4. Safety Authority
5. Evidence & Audit
6. Proposal Workbench

---

### P1: Simulation-only disclaimer is correct but visually over-dominant

The simulation-only and not-safety-certified disclaimer is visible across the site. This is appropriate because the project deals with robotics and motion authority.

However, the repeated wording may dominate the user experience without explaining the value of the safety boundary.

#### Why this matters

The disclaimer protects against overclaiming, but it also risks making the product feel less capable if it is not balanced with a clear value statement.

#### Recommended fix

Keep the disclaimer, but pair it with a value-focused explanation.

Better copy:

> Simulation-only platform. ProjectBoundary demonstrates deterministic mission validation, safety-supervisor authority, replay evidence, and audit traceability. It does not control real hardware.

This is clearer than only saying what the system is not.

---

### P2: Several pages expose raw internal artifacts before explaining user value

The Proposal Workbench and Evidence & Audit pages show significant internal detail, including code snippets, requirement identifiers, audit status, artifact names, hashes, and requirement coverage.

This is valuable for senior technical reviewers, but it may be too dense for the primary portfolio audience.

#### Why this matters

Recruiters and hiring managers need the project’s value explained before they are shown raw implementation details.

The current UI often answers: “What data does the system store?”

It should first answer: “Why does this matter?”

#### Recommended fix

Add short “What this proves” summaries to each major page.

Examples:

- This page proves that ProjectBoundary rejects unsafe mission proposals before they reach motion arbitration.
- This page proves that mission outcomes are tied to deterministic evidence and replayable audit records.
- This page proves that public claims are backed by committed JSON artifacts, not live-generated mock data.

---

## Page-by-Page Review

## Dashboard

### Current role

The Dashboard functions as a mission-control overview. It displays governance health, requirements, mission cards, rehearsal counts, and maturity indicators.

### Strengths

- Good high-level operational framing.
- Shows system scale through metrics.
- Reinforces deterministic JSON-backed artifacts.
- Makes safety state and evidence state visible.

### Issues

- “Phase 19” appears without explanation.
- The page assumes the reviewer understands terms like “bag-backed evidence,” “runtime maturity,” and “rehearsal audits.”
- Mission cards are dense and may not communicate immediate value to non-domain reviewers.

### Recommended improvements

Add a top-level summary card:

> ProjectBoundary validates robot mission requests before simulated execution. It rejects unsafe commands, preserves supervisor authority, and records deterministic evidence for replay and audit.

Add three reviewer-friendly proof points:

1. Unsafe motion requests are rejected.
2. Approved missions are replayable.
3. Evidence is traceable to committed artifacts.

---

## Workspaces

### Current role

The Workspaces page provides six operator presets:

- Mission Review
- Safety Review
- Replay Analysis
- Evidence Audit
- Fleet Readiness
- Reviewer Walkthrough

### Strengths

- Strong concept of role-specific views.
- Good separation between operator, reviewer, replay engineer, fleet operator, and compliance reviewer.
- Demonstrates that the system is not a single generic dashboard.

### Issues

- Some workspaces show missing spatial artifacts.
- The role names are useful but need better context.
- The workspace pages can feel repetitive because many panels show similar audit or mission values.

### Recommended improvements

Add a short explanation above the workspace list:

> Each workspace presents the same deterministic mission evidence through a different operational lens.

Add a clearer summary for each workspace:

- Mission Review: What happened during a mission.
- Safety Review: Why motion was approved or rejected.
- Replay Analysis: Whether the event stream can be replayed.
- Evidence Audit: What artifacts support each claim.
- Fleet Readiness: Which missions and zones are currently ready.
- Reviewer Walkthrough: Guided explanation for first-time visitors.

---

## Reviewer Walkthrough

### Current role

The Reviewer Walkthrough explains the system in ten deterministic steps.

### Strengths

- This is one of the strongest public-facing sections.
- It provides a guided explanation of the platform.
- It correctly explains safety boundaries and deterministic evidence.
- It is a good candidate for the primary recruiter path.

### Issues

- It is currently buried as one navigation item among many.
- Some steps still assume familiarity with domain terms.
- The walkthrough does not fully resolve the missing spatial/3D artifact issue.

### Recommended improvements

Make this the default public entry point or add a “Start Here” button from the dashboard.

Add a final summary panel:

> What this proves: ProjectBoundary turns a mission request into a deterministic audit bundle. Unsafe proposals are rejected before motion authority. Approved missions are simulated, replayed, and tied to traceable evidence.

---

## Proposal Workbench

### Current role

The Proposal Workbench displays accepted and rejected mission intents and generated skill/code candidates.

### Strengths

- Shows a strong safety-first design.
- Demonstrates that unsafe intents are rejected.
- Shows that code generation is constrained and reviewed.
- Good evidence of AI-assisted or deterministic skill generation boundaries.

### Issues

- The page is highly technical.
- Code appears before the product narrative is clear.
- Recruiters may not understand why code snippets are being shown.
- The phrase “Phase 15A” or related internal build language should be avoided in public-facing copy.

### Recommended improvements

Add a plain-English intro:

> The workbench shows how ProjectBoundary handles proposed missions and generated skill candidates. Accepted intents can proceed through validation. Rejected intents are blocked before they can affect motion.

Add labels that distinguish public demo mode from engineering detail:

- Reviewer Summary
- Engineering Detail
- Evidence Source

---

## Replay Viewer

### Current role

The Replay Viewer lists rehearsal audit bundles and allows users to open mission-specific detail pages.

### Strengths

- Strong concept.
- Mission cards are useful.
- Lifecycle states are clear.
- Individual mission pages show timelines, narrative events, audit lineage, and route data.

### Issues

- The expected replay experience is mostly static.
- The tactical map is 2D and minimal.
- Missing spatial artifacts reduce the credibility of the replay feature.
- “No artifact” and “Not registered” panels appear too often.

### Recommended improvements

Create one polished canonical demo mission.

Minimum viable improvement: A single animated 2D mission replay with waypoints, robot marker, safety events, and timeline scrubber.

Better improvement: A 3D warehouse replay scene showing the robot, dock, aisle, restricted zone, waypoints, and safety-supervisor events.

If true 3D is not ready, change the UI language.

Current: `No spatial artifact`

Better:

> 2D fallback replay mode. This mission does not include a 3D scene artifact yet, so the replay is rendered from bounded waypoint inputs.

---

## Safety Authority

### Current role

The Safety Authority page explains the motion authorization chain.

### Strengths

- Strong conceptual page.
- The authority diagram clearly shows that motion must pass through validation and supervisor authority.
- The rules communicate safety boundaries.
- This page helps explain why the system matters.

### Issues

- Internal phase terminology appears in the diagram.
- The page could better explain the real-world value of this architecture.
- Some rules are too implementation-specific for first-time reviewers.

### Recommended improvements

Rename internal nodes:

- Phase 14A Compiler -> Deterministic Mission Compiler
- Mission Validator -> Mission Validator
- Safety Supervisor -> Runtime Safety Supervisor
- Motion Arbitration -> Motion Arbitration Layer

Add a summary:

> This page proves that no mission, generated skill, or operator request can directly authorize motion. Every path flows through deterministic validation and supervisor approval.

---

## Evidence & Audit

### Current role

The Evidence & Audit page displays the traceability matrix, requirement coverage, test coverage, and artifact-backed evidence rules.

### Strengths

- Strongest proof of engineering rigor.
- Shows 183 requirements across many categories.
- Demonstrates test coverage and traceability.
- Shows that the project was built with auditability in mind.

### Issues

- Very dense for nontechnical reviewers.
- Requirement kinds and IDs need more explanation.
- The page references spatial replay requirements even though the deployed spatial replay experience is incomplete.

### Recommended improvements

Add a top-level explanation:

> This page proves that ProjectBoundary’s public claims are traceable to requirements, tests, and committed artifacts.

Add a reviewer-friendly filter:

- Recruiter Summary
- Engineering Detail
- Full Traceability Matrix

Add a warning or status note for spatial replay:

> Spatial replay requirements are tracked and tested, but the deployed public export currently falls back to 2D/static replay because no spatial replay artifacts are registered for the sample missions.

---

## Components / Catalog

### Current role

The navigation implies that this page should show reusable UI components or a design system.

### Current behavior

The page displays: `No artifact at this path`

### Severity

P0

### Recommended improvement

Fix or remove before sharing the project publicly.

Preferred route behavior: `/catalog` renders a component gallery showing cards, status badges, replay panels, mission timeline components, safety banners, and evidence widgets.

Alternative: Remove Components from navigation until the catalog is ready.

---

## Missing 3D / Immersive Visualization

### Current state

The site references spatial replay, scene snapshots, artifact registry, immersive visualization, and related requirements. However, no actual 3D environment was found in the deployed UI.

Current visualizations include:

- Static 2D tactical maps
- Timeline scrubbers
- Waypoint lines
- Audit lifecycle bars
- Pipeline diagrams
- Static site maps

### Problem

The UI creates an expectation of immersive visualization but does not deliver it publicly.

### Recommended minimum demo

Add one route: `/demo/warehouse-replay`

This route should show:

- A warehouse floor
- Dock zone
- Aisle zone
- Restricted zone
- Robot marker
- Waypoints
- Timeline scrubber
- Safety-supervisor events
- Rejection examples
- Evidence hashes or audit references

Even a polished 2D or pseudo-3D visual would be better than empty artifact panels.

### Recommended public label

Use: `Mission Replay Demo`

Avoid: `Spatial artifact unavailable`

Better alternatives:

- `2D replay fallback active`
- `3D scene generation is planned. This replay is currently rendered from deterministic waypoint artifacts.`

---

## Public Messaging Improvements

## Current problem

The site tells the truth about limitations, which is good. However, it does not always explain the value before exposing limitations.

## Better pattern

Use this structure consistently:

1. What this page proves
2. What data it uses
3. What is simulated
4. What is not claimed

Example:

> This replay proves that approved missions can be reconstructed from deterministic event artifacts. The replay is simulation-only and does not control real hardware.

---

## Recommended Navigation Order

Current navigation:

1. Dashboard
2. Workspaces
3. Reviewer Walkthrough
4. Proposal Workbench
5. Replay Viewer
6. Safety Authority
7. Evidence & Audit
8. Components

Recommended public navigation:

1. Start Here
2. Mission Replay
3. Safety Authority
4. Reviewer Walkthrough
5. Evidence & Audit
6. Workspaces
7. Proposal Workbench

Hide or move Components until fixed.

---

## Recommended Docs Additions

Add or update these documents:

- `docs/REVIEWER_EXPERIENCE_AUDIT.md`
- `docs/PORTFOLIO_CASE_STUDY.md`
- `docs/PUBLIC_DEMO_FLOW.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/VISUALIZATION_ROADMAP.md`

---

## Portfolio Readiness Checklist

Before sharing broadly with recruiters, the project should meet the following checklist:

- [ ] Public navigation contains no broken routes.
- [ ] Phase labels are removed or explained.
- [ ] Components/Catalog route is fixed or removed.
- [ ] Reviewer Walkthrough is promoted as the primary entry point.
- [ ] Dashboard includes a plain-English project summary.
- [ ] Replay Viewer has at least one polished visual demo.
- [ ] Missing spatial artifacts are reframed as fallback mode or hidden.
- [ ] Each major page includes a “What this proves” section.
- [ ] Simulation-only disclaimer is paired with a value statement.
- [ ] Public copy avoids internal build-stage terminology.
- [ ] Evidence & Audit page distinguishes recruiter summary from engineering detail.

---

## Recommended Next Build Priorities

### Priority 1: Fix public trust blockers

- Fix or remove `/catalog`.
- Remove broken Components link from navigation if catalog is not ready.
- Replace “No artifact at this path” with a professional 404 or fallback page.

### Priority 2: Clarify public narrative

- Rename “Mission Control Phase 19” to “ProjectBoundary Mission Control.”
- Replace internal phase references with product-level names.
- Add a Start Here page.
- Add What This Proves sections to key pages.

### Priority 3: Improve replay visualization

- Build one polished canonical mission replay.
- Use 2D animation if 3D is not ready.
- Hide empty spatial artifact panels from public reviewer mode.
- Add intentional fallback copy.

### Priority 4: Reduce recruiter confusion

- Add recruiter-friendly summaries.
- Move dense engineering content behind detail sections.
- Keep audit depth available but not forced as the first experience.

### Priority 5: Restore the wow factor

- Add a visual mission demo route.
- Show the rover moving through a warehouse-like environment.
- Surface safety events visually.
- Highlight rejected unsafe actions.
- Show evidence hashes as proof, not as the main story.

---

## Final Assessment

ProjectBoundary has strong technical foundations and demonstrates serious thinking around deterministic mission validation, safety-supervisor authority, replay evidence, traceability, and simulation boundaries.

The current weakness is the public-facing reviewer experience. The site exposes the system’s internal complexity before explaining the product story. It also includes broken or incomplete routes and references visual replay capabilities that are not yet available in the deployed experience.

This is fixable. The project does not need less engineering depth. It needs a clearer public narrative, cleaner navigation, and one polished replay experience that quickly shows why the system matters.

The best next move is to treat the deployed site like a product, not a build artifact. That means fixing broken routes, replacing internal phase language, guiding first-time reviewers, and making the replay experience visually compelling.

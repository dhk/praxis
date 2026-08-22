# Contextual Communication Design
## Complete research brief: frameworks, products, evidence, and the shading mechanic

## Purpose

This document consolidates the two related investigations:

1. **Writing assistance as contextual communication design** — the proposition that effective AI writing assistance should diagnose a communication situation and choose an appropriate strategy, not merely apply a tone or format preset.
2. **Shading** — a controlled, iterative mechanism for exploring multiple versions of a communication with different rhetorical textures while preserving substantive content, evidence, and voice.

The central conclusion is that a useful AI writing system should operate above the abstraction level of “style.” It should model the communication situation, form a communication contract, select or recommend a strategy, and allow the user to explore bounded, explainable variations in that strategy.

For Praxis, this can extend the existing deterministic, auditable approach—Parse → Observe → Recommend → Transform → Validate → Report—without abandoning content integrity or voice integrity.

---

# Executive synthesis

## Core finding

Effective writing is best understood as **contextual communication design**, not as a collection of tone settings. Across rhetoric, technical communication, argumentation, health-care safety, crisis communication, instructional design, UX writing, and organizational communication, effective messages are shaped by a shared set of variables:

- What has happened or needs to be communicated.
- Who will receive the message.
- What the recipient already knows and needs to know.
- What the recipient can decide, believe, feel, or do after reading.
- The urgency of the situation.
- The consequences of misunderstanding, delay, disagreement, or inaction.
- The writer-recipient relationship, authority structure, and emotional sensitivity.
- The evidence supporting material claims.
- The medium and genre through which the message will be consumed.

Conventional AI writing tools generally accept these inputs only when a user supplies them in a prompt. Product interfaces still largely foreground tone, length, style, template, audience label, brand voice, or format. This is useful but incomplete.

The proposed system has a stronger conceptual basis: infer or collect a structured brief, choose an appropriate communication strategy, disclose that strategy, and then compose, transform, or evaluate text against it.

## Strongest conceptual precedent

The strongest high-level antecedent is the **rhetorical situation**. In this tradition, effective discourse responds to:

- **Exigence**: the situation, problem, or condition that communication can help alter.
- **Audience**: people capable of being influenced or of taking relevant action.
- **Constraints**: conditions that shape what can responsibly and effectively be said, including evidence, norms, genre, time, organizational context, beliefs, emotions, and medium.

This is already a theory of communication appropriateness. The product opportunity is to make it operational, inspectable, and useful in everyday writing workflows.

## Main product thesis

A system should not ask only, “What tone do you want?” It should ask—or infer and confirm—questions such as:

- What must the reader do after reading?
- What do they know already?
- What is at risk if they misunderstand or delay?
- What is fact, inference, recommendation, or uncertainty?
- How much time and attention does the reader have?
- Is the message an action request, decision brief, explanation, warning, repair attempt, or update?
- Which text and voice characteristics are non-negotiable?

The assistant should then recommend a strategy such as:

- Decision first, then evidence and options.
- Context first, then explanation and example.
- Hazard first, then protective action and update cadence.
- Acknowledge impact, take responsibility, name repair, and establish next steps.
- State situation, background, assessment, and recommendation.

Tone is a downstream output of that strategy—not the strategy itself.

## Main shading thesis

**Shading** is a controlled, inspectable mechanism for exploring communication tradeoffs. It is not a “regenerate” button and not merely a synonym-replacement feature.

A shading system keeps declared content invariants stable while varying a small set of communication dimensions—such as directness, warmth, explanation depth, scanability, evidence visibility, or urgency framing. It should offer one recommended version plus no more than two or three deliberately differentiated alternatives, each labeled with its intended reader effect and tradeoff.

This follows a broader HCI lesson from parallel prototyping: multiple deliberately different alternatives can reduce premature fixation, elicit better critique, and help users identify preferences that they could not specify in advance. It must be bounded, however, because too many or insufficiently distinct options create choice overload.

---

# 1. Framework landscape

## Rhetorical situation and contextual communication

The rhetorical-situation model supplies the top-level logic for contextual writing. A communication is appropriate when it responds to a real situation, addresses an audience able to act, and works within relevant constraints.

| Component | Product translation | Questions the system should ask or infer |
|---|---|---|
| Exigence | Trigger, problem, opportunity, need for communication | What happened? Why communicate now? What could change because of this message? |
| Audience | Primary and secondary readers with different authority, knowledge, and incentives | Who reads first? Who decides? Who acts? Who may object? |
| Constraints | Evidence, time, medium, relationship, policy, risk, genre, shared vocabulary | What cannot change? What must be proven? What could go wrong? |

This framework generalizes across a cover letter, executive decision request, customer proposal, incident update, Substack post, colleague conflict, postmortem, policy explanation, or clinical handoff.

## Audience models

“Audience” should not mean a role label such as “executive,” “customer,” “general audience,” or “technical reader.” Technical communication and user-centered documentation practice model the reader in terms of capabilities, tasks, knowledge, constraints, and information needs.

| Reader dimension | What it controls |
|---|---|
| Authority and decision rights | Whether the message should request action, recommendation approval, awareness, or escalation |
| Prior knowledge | Explanation depth, terminology, assumptions, examples, and definitions |
| Task | Whether the message should teach, inform, enable, persuade, troubleshoot, or obtain a decision |
| Time available | BLUF, information density, headings, length, and supporting-detail placement |
| Incentives and likely objections | Evidence, tradeoffs, counterarguments, and framing |
| Relationship to writer | Directness, formality, deference, warmth, accountability, and disclosure |
| Emotional state or exposure | Empathy, order of information, reassurance, action cues, and amount of detail |
| Channel conditions | Formatting, urgency markers, interaction, response expectations, and verification |

A system should infer some of these as provisional hypotheses but not silently treat them as facts. It should confirm assumptions when they materially alter the proposed strategy.

## Purpose and desired outcome

Communication intent should distinguish the act the writer performs from the desired reader state.

| Intent | Desired reader state | Typical structures |
|---|---|---|
| Inform | Knows a fact, status, or change | BLUF, update, chronology |
| Explain | Has a correct mental model | Concept → mechanism → example |
| Teach | Can reliably perform a task | Steps, worked example, check for understanding |
| Request | Takes a specific action | Ask first → rationale → logistics |
| Recommend | Chooses a preferred option | Recommendation → evidence → tradeoffs → decision required |
| Persuade | Revises a belief or preference | Claim → evidence → warrant → rebuttal |
| Warn | Recognizes a risk and takes protective action | Hazard → consequence → action → uncertainty/update |
| Reassure | Understands reality and next steps without false certainty | Acknowledge → knowns/unknowns → action → update cadence |
| Correct | Replaces an inaccurate belief or process | State correction → evidence → consequence → required adjustment |
| Repair relationship | Feels heard and can re-engage | Acknowledge impact → responsibility → repair → future behavior |
| Demonstrate competence | Trusts the writer’s judgment | Conclusion → evidence → tradeoffs → limits |
| Escalate | Recognizes intervention or decision is required now | Situation → impact/risk → recommendation/request → deadline |

Advertising and creative-brief practice contributes a useful constraint: the **single-minded proposition**. A document should usually have one primary desired reader response, even when it contains secondary information.

## Argument and evidence

The Toulmin model is particularly valuable for an AI system evaluating recommendations, proposals, technical arguments, and high-scrutiny messages.

| Element | Meaning | Product use |
|---|---|---|
| Claim | The conclusion the reader is asked to accept | Identify the actual recommendation or assertion |
| Grounds | Evidence supporting the claim | Detect missing data, examples, metrics, or sources |
| Warrant | Reason the grounds support the claim | Surface hidden assumptions or causal leaps |
| Backing | Support for the warrant | Require policy, expertise, precedent, or method where needed |
| Qualifier | Scope or degree of confidence | Distinguish certainty, probability, and conditionality |
| Rebuttal | Conditions or objections that limit the claim | Flag unaddressed risks or credible counterarguments |

This gives a system a principled way to say: “The recommendation is clear, but it lacks evidence, the connection from evidence to conclusion is assumed, and the relevant caveat is missing.”

## Risk, crisis, and safety communication

Some domains explicitly raise communication rigor as stakes rise. This is a major precedent for a risk-aware writing system.

| Stakes tier | Main failure mode | Recommended system behavior |
|---|---|---|
| Low | Friction, weak impression, ambiguity | Optimize clarity, readability, and voice |
| Moderate | Confusion, delayed decision, poor execution | Clarify purpose, action, structure, ownership, and deadlines |
| High | Operational, contractual, financial, reputational harm | Separate fact from inference; expose assumptions; require support for consequential claims |
| Safety-critical | Injury, care failure, security or legal exposure | Standardize language; specify actor, action, timing, and verification; escalate uncertainty |
| Crisis | Panic, mistrust, misinformation, harmful inaction | Be timely, accurate, credible, empathetic, transparent, and action-oriented |

CDC Crisis and Emergency Risk Communication provides six highly relevant principles: be first, be right, be credible, express empathy, promote action, and show respect/transparency. It is a useful model for messages where time, trust, uncertainty, and public consequences are all present.

Clinical and operational communication offer further patterns:

- **SBAR**: Situation, Background, Assessment, Recommendation.
- **Closed-loop communication**: receiver repeats or confirms critical information; sender confirms understanding.
- **Check-backs and handoffs**: explicit verification of important information and responsibility transfer.
- **Call-outs**: direct announcement of critical facts to a group.

These show that communication quality is sometimes not complete at “good prose.” It includes correct reception, interpretation, ownership, and confirmation.

## Selecting communication structures

No single structure is universally superior. Structure should be selected according to the reader’s task, the decision path, and the degree of shared context.

| Structure | Best for | Avoid when |
|---|---|---|
| BLUF | Time-constrained readers, executive updates, operational requests | The recipient must build shared understanding before the conclusion makes sense |
| Pyramid Principle | Decision briefs, recommendations, executive arguments | The task requires instruction, discovery, or full narrative context |
| SCQA | Strategy narratives, presentations, problem framing | The reader already knows the situation and immediate action is urgent |
| PREP | Short advocacy, meetings, concise persuasion | Evidence is complex or expected objections need substantial treatment |
| SBAR | Escalation, handoff, operational and clinical situations | Long-form exposition or external public explanation |
| Claim–Evidence–Reasoning | Technical, scientific, policy, and analytical claims | Purely transactional communication |
| Situation–Impact–Action | Incident update, status report, escalation | Complex causal analysis or reflective postmortem |
| Chronology | Legal record, incident narrative, audit trail | Executive decision-making where conclusion must lead |
| STAR | Resume bullet, behavioral interview, case study | Strategic recommendation or abstract analysis |

The relevant system behavior is not “teach all templates.” It is “recommend a structure and say why.” For example:

> The recipient is a time-constrained decision-maker who must approve resourcing today. Lead with the request, deadline, and consequence; use a BLUF-plus-recommendation structure; move technical implementation detail below the decision path.

## Distinct communication dimensions

Current AI interfaces often collapse concepts that theory treats separately.

| Dimension | Question answered | Examples |
|---|---|---|
| Artifact / genre | What kind of thing is this? | Cover letter, decision memo, proposal, postmortem, handoff |
| Information architecture | In what order should information appear? | BLUF, pyramid, chronology |
| Argument structure | How is a claim supported? | Toulmin, claim-evidence-reasoning |
| Rhetorical strategy | How should the reader be moved? | Reassure, warn, request, persuade, repair |
| Register | What social or technical language level fits? | Clinical, legal, peer, executive, public |
| Tone | What interpersonal attitude is conveyed? | Direct, calm, warm, candid, formal |
| Voice | What makes the author recognizable? | Cadence, idiolect, preferences, values |
| Evidence standard | What needs substantiation and how? | Sources, links, data, qualification |
| Precision / ambiguity | How much interpretation is acceptable? | Exact instruction versus exploratory framing |
| Medium | How will it be consumed? | Slack, email, report, deck, live handoff |
| Verification | How will accurate receipt or action be confirmed? | Approval, reply-back, read-back, recorded decision |

This distinction is central to the product thesis. Tone is one dimension among many; it should not be used as a proxy for strategy, reader model, stakes, or evidence standard.

---

# 2. Product landscape

## Current AI-writing approach

Most current products offer freeform prompting plus some combination of drafting, rewriting, length adjustment, tone adjustment, brand voice, templates, audience fields, or document-context awareness. They generally do not expose a full communication diagnosis or explain why a specific rhetorical strategy is appropriate.

| Product or product class | What users supply | Audience / purpose support | Strategy support | Evaluation support | Limitation |
|---|---|---|---|---|---|
| ChatGPT | Prompt, pasted draft, project context, instructions | User-specified through prompts | Implicit; Canvas-style editing supports rewrite and refinement | Conversational review of drafts | User must author and maintain the communication brief |
| Claude | Conversation, projects, uploaded material, instructions | Strong follow-up interview potential | Can reason about strategy when prompted, but no dedicated visible model | Conversational critique and transformation | Strategy is prompt-dependent and largely opaque |
| Gemini | Prompts and connected context where available | User-specified | Mostly direct generation and rewriting | Draft review through prompting | Little structured strategic diagnosis |
| Microsoft Copilot | Prompts, document/work context, organization information | Tone, audience, purpose, and length increasingly supported | Organization-specific agents can tailor outputs | Rewrite, summarize, restructure, tone adjustment | Primarily task and document assistance rather than communication-contract planning |
| Grammarly | Draft, goals, audience, tone settings | Explicit audience and goal controls | Reader-impact feedback and tone suggestions | Strong edit and reader-reaction features | Usually optimizes local clarity and reception rather than selecting full structure |
| Grammarly Reader Reactions | Draft plus selected or custom reader profile | Strongest direct reader-model precedent | Assesses likely reception rather than full strategy planning | Yes: expected takeaways and confusion | Does not fully model evidence, stakes, or verification |
| Writer | Brand voice, style guide, terminology, enterprise context | Strong organization and brand context | Style-guide and custom-agent workflows | Yes, especially enterprise governance | More consistent-brand writing than reader-specific situational strategy |
| Jasper / Copy.ai / sales-writing products | Campaign, asset type, brand, audience fields | Marketing segment and funnel-oriented | Template/workflow selected | Variable | Narrower marketing frame |
| Resume / cover-letter tools | Resume, job description, employer target | Employer/job tailoring | Job-specific framing and matching | Yes | Domain-specific, limited general communication model |

### Product precedents

- **Grammarly Reader Reactions** is the closest mass-market implementation of recipient simulation. Users choose a predefined or custom audience and receive feedback about likely takeaways, confusion, and how the message may land.
- **Grammarly AI Writer** supports audience- and goal-tailored suggestions and tone controls.
- **Claude** supports iterative, conversational clarification and can ask questions before creating an artifact. Projects allow persistent context and reference materials.
- **ChatGPT Canvas** popularized collaborative document iteration: rewrite, shorten, expand, alter tone, summarize, and refine in a shared workspace.
- **Microsoft Copilot** increasingly supports task-specific and organization-tuned agents using proprietary organizational knowledge, terminology, standards, purpose, audience, tone, and length.
- **Writer** applies persistent brand voice, style guides, terminology, and organizational standards to generated content and agents.

## Product gap

No prominent general writing product visibly combines all of the following in a single, coherent workflow:

1. Diagnose genre, reader model, intended reader outcome, urgency, stakes, evidence needs, and relationship sensitivity.
2. Ask only questions whose answers materially change strategy.
3. Recommend and disclose a communication strategy, including structure and reader tradeoffs.
4. Raise evidence, uncertainty, precision, and verification requirements as risk increases.
5. Treat voice preservation and protected content as explicit constraints.
6. Support compose, transform, and evaluate as separate first-class modes.
7. Generate a small set of labeled, strategically differentiated alternatives.
8. Explain what changed, why it changed, and what was deliberately preserved.

That is the core white space.

---

# 3. The communication contract

## Definition

A **communication contract** is a compact structured representation of the situation that the assistant uses to select, execute, and evaluate a communication strategy.

It is not an unfamiliar new idea so much as a product synthesis of existing artifacts:

| Field | Related practice |
|---|---|
| Situation / trigger | Rhetorical exigence, issue brief, incident context |
| Reader / stakeholder | Audience analysis, stakeholder map, persona |
| Intended outcome | Communication objective, jobs-to-be-done, commander’s intent |
| Stakes / risk | Risk assessment, escalation protocol, clinical triage |
| Evidence | Argument brief, source plan, decision memo |
| Relationship context | Stakeholder management, conflict resolution, negotiation planning |
| Form / medium | Genre, channel plan, publication assignment |
| Constraints | Requirements, policy, legal language, style guide, deadline |

## Suggested representation

```yaml
artifact:
  genre: executive_decision_request
  medium: email
  length_constraint: under_250_words

situation:
  trigger: deployment delay discovered
  urgency: decision_needed_today
  stakes: high_operational
  consequence_of_failure: missed_customer_commitment

reader:
  primary_reader: VP_Engineering
  authority: approves_resourcing
  prior_knowledge: knows_program_not_incident_detail
  information_need: decision_relevant_risk_and_options
  likely_objection: avoid_unplanned_headcount
  time_available: low

outcome:
  desired_action: approve_two_week_staffing_reallocation
  desired_belief: delay_is_containable_with_action
  decision_deadline: 3_pm_today

relationship:
  sensitivity: moderate
  power_distance: upward
  trust_context: established

evidence:
  available: deployment_logs, capacity_estimate, incident_owner_assessment
  evidence_standard: traceable_operational_claims
  uncertainty: capacity_estimate_is_preliminary

strategy:
  structure: BLUF_plus_recommendation_evidence_options
  opening: decision_and_deadline
  register: executive_operational
  tone: candid_calm_accountable
  verification: explicit_approval_request
```

## What to ask

Ask only questions that can change the chosen strategy, not generic intake questions.

1. Who must read this first, and what can they actually decide or do?
2. What should they think, understand, decide, feel, or do afterward?
3. What do they already know, and what are they likely to question?
4. What happens if they misunderstand, delay, disagree, or take no action?
5. What is known, inferred, uncertain, or still under investigation?
6. Is the reader time-constrained, emotionally affected, or politically sensitive to this issue?
7. What medium will carry the message, and can the reader ask questions or verify receipt?
8. Which facts, phrases, commitments, sources, or voice characteristics are protected?
9. Is the user asking to compose, transform, or evaluate?
10. Does the message require a decision, approval, acknowledgement, escalation, reply-back, or other confirmation?

## What to infer, then confirm

Reasonable provisional inferences:

- Artifact type and medium from the user’s wording and draft shape.
- Existing structure, density, register, claims, evidence, and explicit asks.
- Whether a draft contains a decision request, deadline, owner, source, caveat, or escalation path.
- Potentially high-stakes subject matter from clinical, legal, financial, employment, security, incident, or compliance cues.

Do not silently infer as settled fact:

- Reader beliefs, emotional state, political constraints, or hidden incentives.
- Relationship fragility or trust level.
- Authority to approve or decide.
- Whether a claim is factually true.
- The acceptable consequences of ambiguity.
- Whether age, diagnosis, or demographic labels map to a particular communication need.

Where such assumptions would materially alter output, show them as assumptions and either ask a concise question or require user confirmation.

---

# 4. Shading: the product mechanic

## Definition

**Shading** is controlled exploration of alternative communication strategies applied to the same substantive message.

A useful model is:

\[
\text{Output} = \text{content invariants} + \text{communication strategy} + \text{surface realization}
\]

### Content invariants

These must not change without explicit user approval:

- Facts, figures, dates, names, and commitments.
- Protected text, quotations, legal or safety-required language.
- The writer’s position and requested action.
- Evidence-backed claims, attribution, uncertainty, and confidence statements.
- Voice constraints where preservation is required.

### Communication strategy

These can change deliberately:

- Information order.
- Opening strategy.
- Directness of the recommendation or ask.
- Explanation depth.
- Evidence visibility.
- Explicitness of action, owner, deadline, and escalation.
- Emotional acknowledgement.
- Reader-load management.
- Confidence and caveating presentation, while preserving truth conditions.

### Surface realization

These are downstream effects:

- Vocabulary.
- Sentence length and syntax.
- Information density.
- Paragraphing, headings, bullets, and visual hierarchy.
- Formality and relational language.
- Cadence and local stylistic texture.

The system should not define shading as “replace words with warmer synonyms.” It should identify the underlying rhetorical change.

## Why generate variants?

Writers frequently know the facts but do not know in advance which balance is right among competing objectives:

- Directness versus relationship sensitivity.
- Brevity versus defensibility.
- Warmth versus crisp action orientation.
- Technical precision versus reader accessibility.
- Reassurance versus transparent uncertainty.
- Accountability versus self-protective framing.

A one-shot system forces users to specify every tradeoff before they can see a draft. A blind regenerate button offers variation but no controlled learning. Shading makes a few consequential alternatives visible and comparable.

## Evidence for the mechanic

### Parallel prototyping

The closest empirical evidence comes from HCI research on parallel prototyping. Studies by Steven Dow and colleagues found that creating and sharing multiple alternatives rather than serially refining a single concept can improve exploration, feedback, group rapport, and final results. In their ad-design work, parallel alternatives also produced stronger final performance than comparison conditions.

The direct evidence is from design and advertising rather than business writing. It should therefore be interpreted as evidence for an interaction principle:

- Early drafts create fixation.
- Comparing distinct options reveals tradeoffs.
- Alternatives make critique easier because the group is not defending one polished concept.
- Variation can help a user discover a preference that they could not articulate as an initial requirement.

It does not prove that every message benefits from three drafts. In safety-critical, legally constrained, or straightforward transactional writing, a single protocol-correct version may be preferable.

### Human-AI co-creation

Human-AI co-creation research emphasizes progressive refinement, selective adoption, and user control. When AI output has no visible relationship to the user’s intent, writers can experience diminished ownership or agency. Shading addresses this by connecting each variation to a named and inspectable change dimension.

### Accessibility and cognitive load

Accessibility and UX research support changes such as descriptive headings, short blocks, plain language, reduced working-memory demands, explicit action, and clear sequencing. A scan-first variant has a defensible basis when it means these observable design features—not vague simplification.

### Choice overload

The countervailing evidence is equally important. Too many alternatives can overload users, especially when differences are subtle or evaluation criteria are unclear. The product should therefore recommend one version and present only two or three meaningfully differentiated variants.

## Shades and controls

Avoid a wall of generic numeric sliders. Use named controls whose effects are concrete and inspectable.

| Layer | Example controls | What they change |
|---|---|---|
| Message strategy | Decision-first, explanatory, evidence-forward, action-forward | Order, argument, emphasis, information architecture |
| Relationship | Warmth, formality, deference, accountability | Interpersonal stance without changing facts |
| Reader load | Scan-first, plain language, jargon tolerance, explicitness | Chunking, headings, terms, implied versus explicit steps |
| Stakes | Precision, uncertainty disclosure, verification, escalation | Rigor, evidence, redundancy, confirmation |
| Medium | Slack, email, memo, proposal, report, live handoff | Density, formatting, conventions, response mechanics |
| Voice | Preserve, lightly adapt, match exemplar | Degree of authorial continuity |

### Named shades

| Shade | Primary behavior |
|---|---|
| Neutral | Direct, compact, minimal interpersonal framing |
| Warm | Acknowledge impact or effort; use collaborative framing; avoid false intimacy |
| Reassuring | State knowns, unknowns, actions, and update timing without overpromising |
| Decisive | Lead with conclusion, requested action, deadline, and consequence |
| Evidence-forward | Make claims, sources, confidence, assumptions, and caveats visible |
| Scan-first | Headline, short blocks, bullets, descriptive labels, explicit action |
| Teaching-oriented | Context, causal explanation, example, and check for understanding |
| Relationship-repairing | Acknowledge impact, take responsibility where warranted, name repair actions |

A user should be able to say:

> Start from the recommended draft. Optimize for scanning, add a little warmth, retain the direct decision request, and preserve all factual and commitment language.

## Example

Base message:

> We reviewed the release plan and identified a risk in the data-migration step. We may need additional engineering support, and I’d like to discuss the implications in our next meeting.

Scan-first, decisive shade:

> **Decision needed today:** approve one engineer for the migration work through Friday.
>
> **Risk:** the current migration plan may delay the release by up to one week.
>
> **Why:** validation has identified an unresolved data-integrity issue.
>
> **Next step:** please reply “approved” by 3 p.m. so the team can start tomorrow.

The shade does not merely shorten wording. It changes sequencing, salience, cognitive load, and the path to action.

## Difference maps

Every alternative should include a short explanation of its deltas:

> **Variant B: warmer and more concise**
>
> - Preserved facts, dates, commitments, uncertainty statements, and requested action.
> - Moved the decision request to the opening.
> - Reduced background from three sentences to one.
> - Added one acknowledgement of the recipient’s workload.
> - Removed two hedges that weakened the deadline.
> - Did not change evidence claims or confidence language.

This turns the model from an opaque rewriter into a communication-design instrument.

## Reader adaptation without stereotyping

Requests such as “recognize my manager has ADHD,” “write for an older customer,” or “write for a younger audience” can be legitimate signals, but age and diagnosis should not become simplistic rhetorical presets.

Translate shorthand into observable reader needs.

| User shorthand | Better product interpretation |
|---|---|
| “My manager has ADHD” | Optimize for scanning, low working-memory load, explicit priorities, visible action, short blocks, clear deadline |
| “Older customer” | Ask whether the issue is reading comfort, digital familiarity, domain knowledge, trust, or accessibility—not age itself |
| “Younger customer” | Ask whether the issue is channel norms, product familiarity, brand style, or speed of action—not informality by default |
| “Executive” | Model decision authority, time availability, and required decision |
| “Technical reviewer” | Model implementation/review/troubleshooting task, shared terminology, and evidence scrutiny |
| “Customer under stress” | Model immediate task, likely failure modes, emotional load, and support path |

W3C cognitive-accessibility guidance supports clear language, obvious structure, reduced memory burden, and easier recovery after attention is lost. These practices benefit many readers and should be offered as configurable accessibility and task-support features rather than as a diagnosis-specific mode.

## When variants are appropriate

Generate variants when uncertainty is strategic:

- An urgent request must balance decisiveness with upward-management sensitivity.
- A customer message could prioritize reassurance or policy clarity.
- A proposal needs both an executive and a technical-review version.
- An incident update could lead with immediate action or include fuller causal context.
- A difficult colleague message could be direct, collaborative, or relationship-repairing.

Do not default to variants when:

- Safety, legal, clinical, or regulatory wording is controlled.
- A known protocol defines the necessary structure.
- The ask is simple and unambiguous.
- The user has supplied a clear strategy.
- Differences would be cosmetic rather than material.
- Multiple versions would create delay or uncertainty.

---

# 5. Product design implications

## The three modes

| Mode | Purpose | Output |
|---|---|---|
| Compose | Create new writing from a communication need | Contract, recommended strategy, draft, shades, risk flags |
| Transform | Improve an existing draft while preserving substance | Surgical changes, alternatives, validation, change report |
| Evaluate | Assess fitness without automatically rewriting | Fit scorecard, missing information, risks, likely reader confusion, prioritized recommendations |

Evaluate mode is particularly differentiated. It lets a user ask:

> Is this message fit for this reader, outcome, medium, and level of stakes?

Most tools are optimized to generate or rewrite. A context-aware evaluator can be useful even when the writer does not want new prose.

## What to expose

Expose the information that lets users retain authorship and challenge the model:

- The inferred communication contract, including confidence and assumptions.
- Recommended structure and a concise rationale.
- The reader action or decision the draft is designed to produce.
- Risk classification and its implications for evidence, uncertainty, and verification.
- Distinctions among facts, inferences, recommendations, unknowns, and assumptions.
- The selected shade and its material tradeoff.
- Protected content and voice constraints.
- A “what changed and why” report.
- A fit-for-purpose evaluation scorecard.

## What to keep lightweight or hidden

Avoid surfacing complexity that does not help the user choose:

- Long prompt chains.
- Fine-grained rhetorical terminology without practical value.
- Overconfident predictions of a recipient’s psychology.
- Large pre-drafting intake forms.
- Opaque numerical quality scores with no evidence or criteria.

Use progressive disclosure. Infer a first strategy, state it briefly, ask one high-value question if necessary, and proceed.

## High-stakes safety rails

For high-consequence communication, the system should:

- Require or prominently flag material claims lacking evidence.
- Separate facts, interpretations, recommendations, and unknowns.
- Preserve uncertainty rather than smoothing it away.
- Require an explicit action, owner, deadline, and escalation path where relevant.
- Recommend source links, data references, or provenance records.
- Flag ambiguity in actor, action, timing, scope, or condition.
- Recommend confirmation mechanisms such as approval, reply-back, read-back, or recorded decision.
- Restrict or label changes to controlled legal, clinical, safety, financial, or policy language.

“Warmer” must never mean “less truthful.” “More concise” must never mean “hide the caveat.”

## Evaluation rubric

| Dimension | Evaluation question |
|---|---|
| Outcome clarity | Is the intended reader action, decision, belief, or understanding explicit? |
| Audience fit | Does the message fit reader knowledge, authority, incentives, and available time? |
| Structural fit | Does the information order serve the reader’s task? |
| Evidence fit | Are consequential claims supported at the required standard? |
| Uncertainty integrity | Are assumptions, estimates, unknowns, and confidence limits visible? |
| Risk calibration | Do precision, redundancy, verification, and escalation match the consequences? |
| Relationship fit | Is the stance appropriately direct, respectful, empathetic, and accountable? |
| Medium fit | Does the format fit Slack, email, memo, report, proposal, or handoff? |
| Voice integrity | Does the writing remain recognizably attributable to the author? |
| Actionability | Are next action, owner, deadline, and confirmation mechanics clear? |

## Praxis implementation

Praxis’s existing pipeline provides a credible implementation pattern:

1. **Parse** the draft and proposed communication contract.
2. **Observe** structure, claims, evidence, reader burden, tone, action clarity, and protected spans.
3. **Recommend** one communication strategy and, only where useful, a small set of named shades.
4. **Transform** within explicit permissions and constraints.
5. **Validate** protected content byte-identically where required; validate claims, required terminology, structure, evidence, and risk controls.
6. **Report** all meaningful changes, strategy selection, unverified assumptions, and residual judgment calls.

This protects the product’s honest boundary: genuine rewriting may be human-plus-LLM work, but it occurs inside an auditable framework that preserves the writer’s substance and voice rather than masking generic generation as improvement.

---

# 6. Research landscape

## Established evidence

### Writing and rhetorical theory

The foundational claim—that appropriateness depends on purpose, audience, and constraints—is established in rhetorical theory and professional writing practice. Technical communication operationalizes this through audience analysis and task analysis. Argumentation theory operationalizes it through evidence, warrants, caveats, and rebuttals.

### Risk and safety communication

Crisis communication and health-care teamwork provide mature professional practices in which communication becomes more structured and verifiable as stakes rise. These fields support the central design claim that the product should not treat all writing as equivalent tone-editing tasks.

### Generative AI and writing

Recent reviews of AI-mediated academic writing report potential improvements in grammar, formulation, organization, vocabulary, paraphrase, idea generation, and revision speed. The same literature raises risks around dependency, shallow engagement, reduced metacognition, academic integrity, generic prose, and loss of authentic voice.

The evidence supports AI as a drafting, feedback, and revision partner more confidently than it supports AI as a substitute for authorial reasoning and judgment.

### Voice and homogenization

Recent empirical work on expert-level creative writing suggests that generic model outputs can be perceived as stylistically homogenized and less compelling than human work, while richer conditioning on an author’s corpus can materially improve stylistic fidelity. This reinforces the need for voice constraints, exemplar grounding, and transparent transformation rather than generic rewriting.

### Coaching and interrogative systems

Emerging educational frameworks distinguish prompt optimization from broader prompt literacy: clarifying purpose, specifying reader and scope, evaluating output, reflecting, and revising. Early work on context-aware feedback and bounded AI coaching suggests that genre-aware, interrogative systems can support confidence, craft, and audience awareness.

This is promising but not yet a definitive proof that a prewriting interview universally outperforms direct drafting.

## Limits of current evidence

There is not yet robust causal evidence that:

- A structured prewriting interview consistently produces better real-world workplace communication than direct AI drafting.
- Asking only “materially changing” questions is superior to comprehensive intake or normal conversation.
- An AI can accurately infer reader beliefs, emotional state, or relationship sensitivity from a draft alone.
- Reader-personalized writing reliably improves outcomes without creating bias, manipulation, or stereotyping.
- Text-only quality evaluation predicts real-world success when timing, organizational politics, trust, delivery context, and recipient interaction matter.
- A shading interface produces superior outcomes across genres, rather than simply greater user satisfaction.

These are therefore product research questions, not settled claims.

## Research program

### Study 1: Interaction comparison

Compare:

1. One generated draft.
2. One draft plus blind regenerate.
3. One recommended draft plus two labeled shades.
4. One recommended draft plus two shades and a difference map.

Measure time to approved draft, number and type of edits, preservation of factual constraints, user confidence, perceived control, and ability to state the intended reader effect.

### Study 2: Recipient outcomes

Use realistic scenarios and recruit readers who match relevant roles.

Measure comprehension, recall, decision quality, action accuracy, time to action, perceived clarity, trust, warmth, appropriate confidence, and ability to distinguish fact from inference and uncertainty.

### Study 3: Attention and accessibility

Test scan-first and conventional variants under time pressure and interruption.

Measure time to find the requested action, error rate, recall of owner/deadline/risk, perceived cognitive effort, and ability to resume after interruption.

Do not treat this as a diagnostic test. Measure task performance and accessibility characteristics.

### Study 4: Voice integrity

Run blind comparisons among original writing, conventional AI rewrites, and shading-guided transformations.

Measure writer recognition, perceived ownership, peer ratings of voice continuity, factual preservation, and perceived genericness.

### Study 5: High-stakes use

Test incident updates, executive decision requests, customer bad-news messages, and operational handoffs.

Measure evidence completeness, uncertainty visibility, clarity of action and escalation, unsafe omissions, and recipient interpretation.

---

# 7. Open questions

- Which communication-contract fields create the greatest marginal benefit: reader authority, prior knowledge, stakes, evidence, relationship sensitivity, or medium?
- When should the assistant ask a clarifying question versus make a labeled assumption and proceed?
- What is the smallest set of shades that preserves meaningful strategic exploration without creating choice overload?
- Can recipient simulations be reliable enough to guide revision, and how should uncertainty in those simulations be communicated?
- How can the product adapt to accessibility needs without stereotyping readers by diagnosis, age, profession, or demographic category?
- What metrics best capture communication success: recipient comprehension, action accuracy, decision speed, trust, relationship preservation, error reduction, or writer satisfaction?
- How can a system preserve a writer’s unique voice while legitimately changing structure and rhetorical strategy?
- When do evidence and risk requirements become burdensome enough to discourage useful writing support?
- How should the product identify and resist manipulative, deceptive, coercive, or false-reassurance uses?
- How should context contracts persist, expire, be shared, and be governed in workplace or regulated environments?

---

# 8. Final recommendation

Build a **contextual communication design layer** whose core artifact is a compact, editable communication contract. It should support Compose, Transform, and Evaluate modes; recommend a communication strategy rather than simply taking a tone instruction; and vary rhetoric through a bounded shading mechanic.

The product should:

1. Treat content integrity, evidence integrity, voice integrity, and risk integrity as separate constraints.
2. Infer context cautiously and ask only questions whose answers materially change strategy.
3. Recommend one default communication strategy with a concise explanation.
4. Offer two or three labeled alternatives only when there is a genuine strategic tradeoff.
5. Expose changes and tradeoffs through difference maps.
6. Translate demographic or diagnostic shorthand into explicit task, accessibility, knowledge, and channel requirements.
7. Increase precision, evidence, uncertainty disclosure, and verification as stakes rise.
8. Provide evaluation without compulsory rewriting.
9. Preserve user agency through editable assumptions, protected spans, voice constraints, and audit trails.

The opportunity is not another AI writer. It is an **auditable communication-strategy system**: a tool that helps a writer decide what a message needs to accomplish for this reader, in this situation, at this level of risk—and then helps them explore, construct, transform, and evaluate the communication without losing ownership of its substance or voice.

---

# Annotated bibliography and source links

## Foundational theory and practice

- Lloyd F. Bitzer, “[The Rhetorical Situation](https://www.jstor.org/stable/40236733)” (1968). Foundational formulation of exigence, audience, and constraints. This is the most direct theoretical foundation for situation-aware writing strategy.

- Google, “[Audience](https://developers.google.com/tech-writing/one/audience)” from *Technical Writing One*. Practical audience-analysis guidance grounded in reader knowledge, role, and task.

- Purdue OWL, “[Toulmin Argument](https://owl.purdue.edu/owl/general_writing/academic_writing/historical_perspectives_on_argumentation/toulmin_argument.html).” Clear operational account of claim, grounds, warrant, backing, qualifier, and rebuttal.

- U.S. Agency for Healthcare Research and Quality, “[TeamSTEPPS 3.0](https://www.ahrq.gov/teamstepps-program/index.html).” Evidence-based teamwork and communication system; relevant to high-stakes handoffs, escalation, and verification.

- AHRQ, “[SBAR on an Inpatient Medical Unit](https://www.ahrq.gov/teamstepps-program/resources/additional/sbar-inpatient.html).” Definition and application of Situation, Background, Assessment, Recommendation.

- Centers for Disease Control and Prevention, “[Crisis + Emergency Risk Communication](https://stacks.cdc.gov/view/cdc/25531)” (2014). Official manual covering time-sensitive, uncertain, trust-sensitive public communication.

- W3C Cognitive and Learning Disabilities Accessibility Task Force, “[Making Content Usable for People with Cognitive and Learning Disabilities](https://w3c.github.io/coga/content-usable/).” Guidance on clear language, structure, memory burden, orientation, and personalization.

- Nielsen Norman Group, “[UX Writing: FAQs from Practitioners](https://www.nngroup.com/articles/ux-writing-faqs/).” Practical guidance on readable, scannable, accessible digital writing.

## HCI and interaction design

- Steven P. Dow et al., “[Parallel Prototyping Leads to Better Design Results, More Divergence, and Increased Self-Efficacy](https://aaalab.stanford.edu/assets/papers/2010/Parallel_Prototyping_leads_to_better_design_results.pdf)” (CHI 2010). Strongest direct precedent for presenting multiple intentionally different alternatives rather than serially refining a single early idea.

- Steven P. Dow et al., “[Sharing Multiple Designs Improves Exploration, Group Rapport, and Results](https://hci.stanford.edu/publications/2011/PrototypingDynamics/PrototypingDynamics-CHI2011.pdf)” (CHI 2011). Supports the value of alternatives for critique, collaboration, and outcome quality.

- “Future research directions in choice overload and its moderators” (2024). Useful counterweight: alternatives help only when the number, complexity, differentiation, and decision support are controlled.

## Current product precedents

- Grammarly, “[Reader Reactions](https://www.grammarly.com/ai-agents/reader-reactions).” A direct precedent for reader-profile-driven feedback about likely reception, takeaway, and confusion.

- Grammarly, “[AI Writer](https://www.grammarly.com/a/ai-writer).” Audience- and goal-tailored suggestions with tone adjustment.

- Anthropic, “[Use artifacts to visualize and create AI apps](https://support.anthropic.com/en/articles/11649427-use-artifacts-to-visualize-and-create-ai-apps-without-ever-writing-a-line-of-code).” Documents an interview-before-building pattern, in which Claude asks relevant follow-up questions.

- Anthropic, “[Create and manage projects](https://support.anthropic.com/en/articles/9519177-how-can-i-create-and-manage-projects).” Persistent instructions and reference materials as a basis for stable project context.

- Microsoft, “[Copilot Tuning overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/copilot-tuning-overview).” Organization-tuned agents tailored to organizational knowledge, terminology, tone, audience, purpose, length, and quality standards.

- Writer, “[Customizing your team’s style guide](https://support.writer.com/articles/2607647594-customizing-your-team-s-style-guide).” Persistent application of organizational writing requirements to AI-generated outputs.

## AI-mediated writing research

- A. Sanz-Tejeda et al., “[The impact of generative AI on academic reading and writing: a synthesis of recent evidence (2023–2025)](https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2025.1711718/full)” (2026). Recent synthesis reporting writing-support benefits alongside dependency, metacognition, integrity, and voice concerns.

- T. Chakrabarty et al., “[Can Good Writing Be Generative? Expert-Level AI Writing](https://arxiv.org/html/2601.18353v1)” (2026). Relevant controlled work on human versus AI writing judgments, genericness, and improved stylistic fidelity with richer author conditioning.

- “Context-aware GenAI feedback for fostering student …” (2026). Directly applies rhetorical-situation theory to context-aware generative-AI feedback, emphasizing purpose, audience, and disciplinary constraints.

- “Early Evidence from ConnectInk’s AI-Supported Personal …” (2026). Early evidence that bounded AI coaching paired with genre pedagogy can support confidence, craft, and audience awareness.

- “Prompts to Practice: A Pedagogical Framework for Human …” (2026). Frames prompt literacy as clarification of purpose, audience, scope, evaluation, and iterative refinement—not merely prompt optimization.

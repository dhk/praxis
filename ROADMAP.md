# Praxis Roadmap

Every wave must leave praxis in a state a writer can actually use. A
wave that ends in scaffolding has not ended.

## Where we are (2026-08-22)

| Wave | Status |
|---|---|
| 0 — Transformation harness | **Delivered** — pass model, artifact trail, three packs, validation, CLI, browser viewer |
| 1 — Communication design, MCP-first | **In progress** — contract, strategy, materiality, evaluation, shading audit, HTML artifact, MCP server |
| 2 — Transform mode and voice | Not started |
| 3 — Genre packs and reader models | Not started |
| 4 — Evidence for the mechanic | Not started |
| 5 — Persistence, sharing, governance | Not started |

The design record for wave 1 is
[`spec/RFC-0003-contextual-communication-design.md`](spec/RFC-0003-contextual-communication-design.md).
The research it draws on is
[`docs/research/contextual-communication-design.md`](docs/research/contextual-communication-design.md).

---

## Wave 1 — the MVP

**Usable outcome:** a writer describes a situation, answers at most three
questions, and gets a named communication strategy with its reasons, a
list of what the draft is missing, at most two priced alternatives, and a
page that shows all of it side by side — with proof that no figure,
commitment, or caveat went missing between versions.

### Why this is the first wave and not something else

Three constraints picked it.

**It must be compelling without generating text.** Evaluation is the
mode nobody else ships. Every competitor answers a request for feedback
by producing replacement prose; a writer who wants a second opinion and
not a second draft is unserved. Evaluation also needs no model, so it is
the one differentiated capability that is free to run.

**It must be cheap.** The engine is deterministic Python: no keys, no
inference, no vendor, no per-seat cost. The only inference is the
inference the user's conversation was already paying for.

**It must be visual from the first commit.** A contract, a scorecard,
and two variants with their difference maps are a *comparison*. Narrated
in chat they are noise. `design_render` returns a self-contained page on
day one, publishable as an artifact or served locally — not deferred to
a later "UI wave", because without it the product does not read as a
product.

### In scope

| Capability | Shape |
|---|---|
| Communication contract | 21 fields across seven sections, closed domains on the nine that select strategy, provenance on every value |
| Strategy recommendation | 12 structures scored from a data table; returns the winner, its reasons, the runner-up, and a confidence that is honest when the contract is thin |
| Material questions | Perturbation over each unknown field's domain; a question is asked only if the answers demonstrably split the strategy. At most three |
| Stakes ladder | Cumulative requirements and an evidence standard from `low` to `crisis` |
| Evaluate mode | Ten dimensions, each `pass` / `gap` / `unknown` with the evidence attached. No overall score |
| Shading | Eight named shades; at most two offered, only against a named tension; suppressed entirely where a protocol decides the shape |
| Invariant audit | Verbatim content, commitments, and markers of uncertainty — checked per version against the writer's draft, each violation naming its reference |
| Priced alternatives | The recommendation is submitted with the alternatives and listed first; every alternative's difference map is measured **against the recommendation**, so the writer sees what choosing it costs and what it holds |
| Artifact | One self-contained, theme-aware HTML page; no scripts, no network |
| MCP server | Answer-first and conversational: `design_open`, `design_update`, `design_detail`, `design_shade`, `design_render`, `design_list`, `design_schema` |
| Progressive disclosure | Every reply is the answer, the progress, and one question. Reasoning, full findings, and the contract are one `design_detail` away and never volunteered |
| Knowing when to stop | The progress line counts only questions that would still change the answer, so praxis can say "nothing else you could tell me would change it" |
| CLI | `praxis design` (answer-first, `--why` to drill in), `praxis serve`, `praxis mcp` |

### Deliberately out of scope

- **Composing prose.** Permanently, not for now.
- **Voice modelling.** `voice_integrity` reports `unknown` in wave 1 and
  says why. A fake voice check is worse than an absent one.
- **Recipient simulation.** Predicting how a named human will feel is
  the claim this product is positioned against.
- **The design layer in the browser viewer.** The modules are stdlib-only
  and already ship in the Pyodide bundle; wiring the UI is wave 2.
- **A third alternative.** Two is the choice-overload-safe bound until
  there is evidence for more.

### Done when

- [x] Every asked question provably changes the strategy — enforced by test.
- [x] Every suppressed question provably does not — enforced by test.
- [x] A variant that drops a figure, a deadline, or every uncertainty
      marker fails its check.
- [x] Rewording an ask does *not* fail its check.
- [x] An empty contract produces `unknown`, never `gap`.
- [x] The page renders in both themes with no script and no external URL.
- [x] The engine imports nothing outside the standard library.
- [x] An alternative is compared with the recommendation, not the draft,
      and every delta names its reference.
- [x] A first-run walkthrough that takes a real message end to end
      (`examples/decision_request/`).
- [x] A default reply is the answer and nothing else — under 250 tokens,
      where the first version was about 900.
- [x] Outstanding questions decrease as they are answered, and reaching
      zero is stated rather than left silent.
- [ ] Tool descriptions read as instructions a client model follows
      without a system prompt.

---

## Wave 2 — transform mode and voice

**Usable outcome:** point praxis at a draft you already wrote and get
surgical changes with a change report, not a replacement.

- Transform as a first-class mode alongside compose and evaluate.
- Protected spans: mark a region as untouchable and have it enforced,
  not merely detected.
- Voice integrity as a real check: compare a variant against the
  author's own corpus rather than against nothing.
- The design layer in the browser viewer, sharing the Pyodide bundle it
  is already shipped in.
- Difference maps in the transformation harness's Compare panel.

## Wave 3 — genre packs and reader models

**Usable outcome:** praxis knows what an incident update or a decision
memo is supposed to contain, and says what is missing.

- Genre packs: required elements per artifact type, joining the existing
  `Pack` idea to the contract.
- Reader models as capabilities and constraints, never demographic
  presets — the shorthand-to-observable-need translation the research
  brief argues for.
- Accessibility and task-support requirements as configurable
  constraints rather than a diagnosis-shaped mode.
- Structures for the genres the current twelve do not cover.

## Wave 4 — evidence for the mechanic

**Usable outcome:** claims about praxis are backed by measurement, not
assertion.

- A corpus of real messages with known outcomes.
- Detector precision and recall measured, published, and regression-tested.
- The interaction study: one draft, versus draft-plus-regenerate, versus
  recommended-plus-two-labelled-shades, versus the same with difference
  maps.
- Attention and recovery testing for scan-first variants.
- Calibrate `MAX_ALTERNATIVES`, the stakes ladder, and structure weights
  against results instead of against argument.

## Wave 5 — persistence, sharing, governance

**Usable outcome:** a contract outlives its message and can be handed to
someone else.

- Contract templates and reuse across recurring situations.
- Sharing a design session as a durable artifact.
- Expiry, review, and ownership for contracts used in workplace settings.
- Team-level protected language and controlled-terminology enforcement.

---

## Standing non-goals

Not "later" — never, without a new product argument:

- Generating prose in the engine.
- A single overall quality score.
- Predicting a named individual's reaction.
- Accounts, hosted storage, or server-side document processing.
- A second implementation of the rules in another language.

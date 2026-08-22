# RFC-0003: Contextual communication design

Status: Draft
Version: 0.1
Depends on: RFC-0001

## Abstract

A second layer over the praxis engine that operates above the level of
style. Where RFC-0001's harness fixes mechanical defects with evidence,
this layer decides what a message should *do* for a specific reader at a
specific level of risk, asks only the questions that change that
decision, and audits whatever prose comes back against constraints
declared in advance.

The layer generates no prose. It has no model, no key, and no network.
Prose comes from the model the writer is already talking to, over MCP.

## Problem

The harness in RFC-0001 can prove that `in order to` became `to` and
that no citation year went missing. It cannot say that a decision
request buried its ask in the third paragraph, that a high-stakes claim
sits nowhere near a number, or that the "warmer" rewrite quietly deleted
the word *preliminary*.

Those are the failures that matter in consequential writing, and they
are not sentence-level defects. They are failures of **contextual
communication design**: the message was shaped for the wrong reader,
the wrong task, or the wrong level of risk. The supporting research is
in [`docs/research/contextual-communication-design.md`](../docs/research/contextual-communication-design.md).

The market gap is specific. No general writing product visibly combines
diagnosing the situation, asking only materially-changing questions,
disclosing a recommended strategy, raising rigor as stakes rise,
treating voice and protected content as explicit constraints, and
explaining what changed and what was preserved. Products sell prose;
none sells the decision or guarantees the prose kept it.

## Proposal

Add `praxis.design.design(draft, contract, variants) -> dict`, a second
entry point beside `run_pipeline`, composed of five deterministic parts.

### 1. The communication contract

A compact, editable model of the situation: 21 fields across artifact,
situation, reader, outcome, relationship, evidence, and constraints.

Two properties do the work:

**Every value carries provenance** — `stated` (the writer said so) or
`inferred` (the assistant guessed). An inference is never promoted to
fact, and an inference that moves the recommendation comes back as an
assumption to confirm. This makes the research brief's rule about not
silently assuming reader beliefs, authority, or trust into a data
constraint rather than a habit.

**Nine fields have closed domains.** These are the ones that select the
strategy, and closing them is what makes the next part possible.

### 2. Strategy selection as a scored table

Twelve structures — BLUF, pyramid, SCQA, PREP, SBAR, claim-evidence-
reasoning, situation-impact-action, hazard-first, reassure, repair,
concept-mechanism-example, STAR — each carrying `favors` and `avoids`
weights over contract values, drawn from the "best for / avoid when"
tradition.

Selection sums the matches. The result reports the winner, the three
contract values that produced it, the runner-up, what counted against
the runner-up, and a confidence that is `low` whenever the contract is
too thin to have decided anything. Adding a structure means adding a
row; the scorer is never edited.

### 3. Materiality by perturbation

Everyone states the rule — *ask only questions whose answers materially
change strategy* — and nobody implements it. It is decidable.

Take an unknown field, walk it across its closed domain, re-run the
recommendation for each value, and compare the outcomes. If every value
lands on the same strategy, the question is intake and must not be
asked. If the values split, the split itself is the reason to ask, and
it is shown to the writer: *"low → two priced alternatives; medium or
high → one version."*

The outcome fingerprint spans both halves of the strategy — the
structure *and* whether alternatives are warranted — because a field
that flips a message from "one protocol-correct version" to "two priced
alternatives" has changed the strategy even if the structure holds.

Candidates are the unset selectors **plus the inferred ones**. An
inference that moves the recommendation is exactly the assumption a
human should get the chance to overturn.

This is checked by test in both directions: every question asked splits
the strategy, and no suppressed field would have.

### 4. Evaluate mode

Ten dimensions — outcome clarity, audience fit, structural fit, evidence
fit, uncertainty integrity, risk calibration, relationship fit, medium
fit, voice integrity, actionability — each returning `pass`, `gap`, or
`unknown` with the evidence attached and, for a gap, a concrete fix.

There is deliberately **no overall score**. A number with no criteria
behind it invites the writer to optimise the number.

`unknown` is load-bearing and used often. Detectors are conservative and
recall-oriented; a miss must report `unknown`, never `absent`. An empty
contract yields unknowns, never gaps: absence of contract is not
evidence of a defect.

### 5. Shading, with machine-checked invariants

Eight named shades. At most **two** alternatives, offered only where the
contract contains a named tension (urgency against a fragile
relationship; defensibility against a reader with no time), and
suppressed outright where a protocol already decides the shape —
safety-critical and crisis stakes, or a simple low-stakes ask.

Invariants come in two kinds, and the distinction is what makes the
mechanic usable:

- **Verbatim tokens** — figures, percentages, links, bracketed
  references, citation years. Extracted from both sides by the same rule
  and compared as sets. Substring containment is not sufficient and the
  gap is not academic: `"40%" in "Costs rose 140%"` is true, so a
  containment check certified a changed figure as preserved.
- **Verbatim phrases** — strings the writer declared protected. These are
  free-form, so containment is exactly right: the phrase must appear and
  the wording around it may move.
- **Presence** — that an ask exists, a deadline exists, an owner exists,
  a confirmation exists. These must survive *in any wording*, because
  requiring an ask to survive rephrasing verbatim would forbid the very
  rewriting shading exists to do.

Plus the guarantee the product is actually sold on: **markers of
uncertainty may not be smoothed away.** Losing all of them blocks;
losing some flags for review. Warmer never means less truthful, and
shorter never means the caveat is gone.

Each version returns a difference map: what measurably moved, what was
deliberately held, and whether it is actually the shade it claims to be.
Shade fidelity is reported, never enforced — a variant can be good prose
and a bad example of its label, and conflating those two failures helps
nobody.

**Two references, kept separate.** The invariants come from the writer's
own draft: protected content originates there, and an alternative must
not be allowed to lose a figure just because the recommended version lost
it first. The *difference map*, though, measures each alternative against
the **recommendation** — the writer is choosing between two versions they
could send, not between two edits of a draft they have already decided to
replace, so "how does this differ from the one I would otherwise send" is
the question they are actually asking. Every difference map names its
reference, because the same numbers mean different things under each.

A consequence worth stating: the recommended version is submitted
alongside the alternatives, marked. With no draft at all — a compose
session — the recommendation is the first prose that exists and becomes
the source of invariants, which is also how compose sessions came to be
checked at all rather than silently skipped.

## MCP-first

The server is the primary interface, not an afterthought.

| Tool | Purpose |
|---|---|
| `design_open` | Start a session; get the strategy, the questions, the gaps |
| `design_update` | Record answers, corrections, or a new draft; re-analyse |
| `design_shade` | Submit written variants; get violations and difference maps |
| `design_render` | Get a self-contained HTML page to publish as an artifact |
| `design_list` | Saved sessions |
| `design_schema` | The fields, structures, and shades this server knows |

| `design_detail` | The reasoning, the full findings, or the contract — on request only |

Every response carries `next_step`, which walks the client through
`open → ask → write → check → render` without needing a system prompt.
Tool descriptions and `next_step` are the only instructions the client
model receives; they are product surface, not comments.

### Answer first, and nobody has to finish

The first version of this surface returned every dimension, the
runner-up, the contract and the invariants on every call — about 900
tokens to say something that fits in a sentence, from a layer whose
entire argument is leading with the conclusion and asking only what
changes it. That was advice the interface ignored.

Each reply now carries four things and stops: the **answer** (the shape,
and what is wrong with the draft), the **progress**, **one question** if
one is worth asking, and where to drill in. `design_detail` serves `why`,
`findings`, `contract`, and `questions`. Roughly 160–250 tokens instead
of 900.

There is no interview to complete. The first call answers immediately at
whatever confidence the situation supports and says which; every reply
offers exactly one further question. Stopping is a decision made with the
cost visible rather than a corner the writer is backed into.

The progress line counts questions that would still *change* the answer,
not fields left blank — which is what lets praxis say **"nothing else you
could tell me would change it."** A tool that can tell you when you are
finished is unusual, and it falls straight out of the perturbation
machinery: if every remaining unknown lands on the same strategy, there
is nothing left to ask. `design()` reports `questions_outstanding` as the
true total, because the displayed list is capped at three and a count
frozen at three reads as no progress at all.

The division of labour is the architecture: **praxis decides and audits,
the client writes.** It is what makes the layer free to run, and it is
what makes the audit mean anything — a rewriter grading its own
rewriting is not an audit.

## Artifacts

`praxis.render.document(result)` produces one self-contained,
theme-aware HTML page: contract with provenance badges, strategy with
its reasoning, the questions worth asking and the ones that would change
nothing, the scorecard, the variants side by side with their difference
maps, and what may not move.

No scripts, no fonts, no network — enforced by test. Publishable as an
artifact by an MCP client, or served by `praxis serve` over loopback.

This ships in wave 1 rather than a later UI wave because the output is a
comparison. Narrated in chat it is noise.

## Boundaries

- `praxis/*.py` stays stdlib-only; `scripts/build_site.sh` copies that
  glob into Pyodide. The MCP server and viewer live in `praxis/mcp/`,
  which the non-recursive glob never copies.
- The design layer does not touch `pipeline.py`, `rules.py`, `packs.py`,
  or the six-file artifact contract. RFC-0001 is unchanged.
- Sessions persist the contract, the draft, and the variants. Nothing
  derived is stored, so a rule change never leaves a stale verdict in a
  file.

## Non-goals

- Generating prose, in this layer or anywhere in this repository.
- Predicting how a named individual will feel about a message.
- A single overall quality score.
- Voice modelling — `voice_integrity` reports `unknown` and says why
  until there is a corpus to compare against (wave 2).
- More than three alternatives, ever.

## Known limitations

- **Detectors are regular expressions.** They see structure and marker
  words, not meaning. Precision and recall are unmeasured; wave 4. Known
  corrections so far: modal requests ("could you approve") are excluded
  from uncertainty and bare `if` is not counted as a hedge — both
  inflated the score of courteous drafts and masked real caveat losses;
  "approve by" no longer counts as a confirmation mechanism, being an ask
  and a deadline that already have their own detectors.
- **A detector finding nothing is reported as `unknown`, never as
  `pass`.** `evidence_fit` once returned `pass` when it recognised no
  consequential claim at all, telling a high-stakes draft its claims were
  supported on the strength of having identified none.
- **The evaluator checks what `requirements()` promises.** Raised stakes
  are tier-specific: `high` needs an owner and a confirmation,
  `safety_critical` adds an escalation path, `crisis` adds a named next
  update. Checking only the first two at every tier passed a crisis
  message with no update cadence while the same run told the writer one
  was mandatory.
- **A dimension may only claim to check what it checks.** `actionability`
  asked about four elements and tested two; its question is now scoped to
  the ask and the deadline, with owner and confirmation delegated to
  `risk_calibration`, which is where stakes decide whether they matter.
- **Tension ordering truncates.** With two alternative slots and several
  matching tensions, the first-declared tension wins and later ones are
  masked. Deterministic and documented, but the ordering is currently an
  argument rather than a finding.
- **Structure weights are reasoned, not measured.** They encode a
  defensible reading of the literature. Wave 4 calibrates them.
- **Materiality is measured against strategy only.** A field can leave
  the structure and the shading offer untouched and still change what
  the evaluator asks for. Such fields are reported as "would not change
  the strategy" — a narrower claim than "not worth knowing".

## Open questions

- Which contract fields carry the greatest marginal benefit? The
  perturbation machinery can answer this empirically once there is a
  corpus.
- Is two the right bound on alternatives, or is it three?
- When should an inferred value be confirmed rather than merely shown?
- Can uncertainty-preservation checking be extended from marker words to
  claim-level confidence without becoming unreliable?

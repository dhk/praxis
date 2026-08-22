# Research specification: detector evaluation

**Type:** research specification (see [`AGENTS.md` § Documents](../../../AGENTS.md#documents)).

A *brief* says what to go and find out. A *specification* says what
decision the answer settles, what would count as sufficient evidence, and
what we do under each possible outcome. It is written **before** the
findings arrive, so the research cannot later be read to confirm whatever
we already wanted. `brief.md` and the two handoff prompts are this
document's questions packaged for a recipient — handouts, not documents
in their own right.

**Informs:** [RFC-0005](../../../spec/RFC-0005-detector-measurement.md),
open questions 1–6.
**Brief:** [`brief.md`](brief.md) · **Handoffs:**
[`handoff-prompt.md`](handoff-prompt.md),
[`search-prompt-generation.md`](search-prompt-generation.md)

## The decision this settles

**How much of praxis's detector corpus may be machine-generated, and who
assigns the labels?**

Three candidate positions, and the research picks between them:

| Position | What it means in the corpus |
|---|---|
| **A — Human labels only** | `generated` examples are never scored. The corpus grows at the speed a person writes it. |
| **B — Generate for coverage, human-label the boundaries** | Models supply breadth; a person labels where models disagree. `generated` scored in a separate tier, never in the headline. |
| **C — Two-model adjudication as ground truth** | Where two independent models agree, the label stands. Human attention goes only to disagreements. `generated` counts toward the headline with its provenance stated. |

The current implementation assumes **B** by default — `measure.TRUSTED`
excludes `generated`. That default was chosen by argument, not evidence,
which is what this pass exists to correct.

## Why this cannot be settled internally

praxis's detectors were authored by a language model. So, by default,
would be any corpus generated to test them. The failure mode is not
hypothetical: seven detector faults this session were boundary cases the
author had not imagined, and three fixes introduced the next fault. A
corpus drawn from the same source as the rules cannot be relied on to
contain the cases the rules miss.

We cannot resolve that from inside the session that wrote the rules. Hence
external sources.

## Decision rules, fixed in advance

Written before any findings are read. If a finding does not fit one of
these, say so explicitly in the synthesis rather than stretching a rule to
cover it.

1. **If model annotators are shown to make substantially correlated
   errors** → adopt **A** for boundary cases and **B** for bulk coverage.
   Generated examples stay out of the headline figure permanently.
2. **If two models from different families are shown to err
   independently enough for reliability to be *estimated* without ground
   truth** (Snorkel-style or otherwise) → adopt **C**, with the estimated
   reliability published beside every figure.
3. **If the evidence is mixed or absent** → keep **B**, and record in
   RFC-0005 that it is a default rather than a finding. Do not treat
   absence of evidence as licence.
4. **If chance-corrected agreement (κ and relatives) is shown not to keep
   its conventional interpretation for model annotators** → report raw
   agreement and annotator type instead of a κ, and never a single
   blended number.
5. **If the synthetic-versus-real precision gap is characterised with a
   magnitude** → use that magnitude as a stated discount on any figure
   involving generated examples. If only a direction is known, keep the
   tiers separate rather than discounting by a guess.
6. **If capability-suite prior art (CheckList-style) supersedes the
   current corpus design** → restructure `corpus/detectors.jsonl` to match
   it and cite the source in RFC-0005. Do not keep a bespoke shape for
   its own sake.

## What counts as sufficient evidence

- A **named** method, paper, tool or documented practice — not a general
  impression that something is common.
- A primary source where one exists.
- For any claim about reliability, the **baseline it was measured
  against** and the task it was measured on.
- Explicitly marked inference where a source is reasoning rather than
  reporting.

Insufficient: an assertion with no source; a claim that a practice is
"widely used" without an instance; agreement between our own sources
where neither cites anything.

## Method

Two or more sources answer [`brief.md`](brief.md) **independently**,
without seeing each other's work. Findings land one file per source in
[`findings/`](findings/). A synthesis is written only once at least two
are in, and reports where sources agree, where they conflict and which is
more credible, what only one caught, and what remains open.

The in-session pass (`findings/claude-findings.md`) was written before
either handoff was issued, so it cannot have been anchored by them.

## Done when

- [ ] At least two independent findings files exist.
- [ ] `synthesis.md` is written and maps back to RFC-0005's open questions.
- [ ] One of positions A / B / C is adopted, or rule 3 is invoked
      explicitly.
- [ ] RFC-0005 is updated to record the outcome, including if the outcome
      is "no evidence found, default retained".
- [ ] Any adopted method is cited in RFC-0005 rather than reimplemented
      unattributed.

## Out of scope

Writing-assistant products, rhetoric, communication theory, and LLM prose
quality — covered by the wave-1 pass
([`../contextual-communication-design.md`](../contextual-communication-design.md)).
Calibrating structure weights or voice tolerances, which need a different
kind of evidence and a different specification.

## Known risk in this specification

The decision rules above are themselves a judgment made by the same
session that wrote the detectors. They constrain *how* the findings get
applied, not whether the framing is right. A source that says "you are
asking the wrong question" should be treated as a finding, not as a
failure to answer, and the rules rewritten in the open.

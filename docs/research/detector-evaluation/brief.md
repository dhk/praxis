# Research brief: evaluating LLM-authored text detectors

**Type:** handout — a derived artifact of the specification, not a document in its own right · [document types](../../../AGENTS.md#documents)

**Design doc under research:**
[`spec/RFC-0005-detector-measurement.md`](../../../spec/RFC-0005-detector-measurement.md)
**Topic slug:** `detector-evaluation`

## Why this pass exists

RFC-0005 proposes measuring praxis's regular-expression detectors against
a corpus of examples with known answers. The detectors were authored by a
language model; so, if we are not careful, would be the corpus. Every
question below traces to a numbered open question in that RFC.

Context a source needs, and nothing more: praxis is a deterministic,
stdlib-only Python engine that detects communication signals in prose —
whether a message contains a request, a deadline, an escalation path, a
named next update time. It calls no model at runtime. Twelve detectors,
each a compiled regular expression. Independent review found seven cases
of a detector firing on text it should not; three fixes for those
introduced the next failure.

## Questions

### Q1. Multi-model labelling in place of human labels
*Traces to: RFC-0005 open question 1.*

Is there established practice for using one model to generate examples
and a second, independent model to label them — and what are the
resulting precision/recall figures understood to mean? What is known
about correlated error between model annotators from different families?
Where has this been shown to work, and where to fail?

### Q2. Behavioural / capability test suites
*Traces to: RFC-0005 §Proposal, and open question 2.*

Prior art for testing NLP components by capability rather than by
aggregate accuracy — suites where the *category* supplies the label
rather than an annotator's judgment. What granularity of example do these
use, and how do they decide a suite is adequate?

### Q3. Weak supervision and label denoising
*Traces to: RFC-0005 open question 1.*

Methods for combining several noisy labelling sources into a single
label, and for estimating each source's reliability without ground truth.
What do they assume, and do those assumptions hold when the sources are
language models rather than heuristics or crowdworkers?

### Q4. Agreement statistics for model annotators
*Traces to: RFC-0005 open question 6.*

Which inter-annotator agreement measures are used when the annotators are
models, and does the conventional interpretation of those statistics
survive the substitution? Is there a recommended way to report a figure
whose labels are partly model-derived?

### Q5. Synthetic-corpus distribution shift
*Traces to: RFC-0005 open question 4.*

Evidence on how measured precision and recall move when a component is
evaluated on generated text rather than naturally occurring text. Is the
gap characterised anywhere, and are there mitigations short of collecting
real data?

### Q6. Counterfactual and boundary examples
*Traces to: RFC-0005 §"What this measured on the first run".*

Prior art for minimal-pair examples that differ in exactly the property
under test — praxis's own case being *"respond by 9"* (a deadline) against
*"slipped by 5 days"* (not one). How are such pairs generated and
validated?

### Q7. Spending scarce human attention
*Traces to: RFC-0005 open question 5.*

Given a small human labelling budget, what does the literature say about
where to spend it — annotator disagreement, model uncertainty, decision
boundaries, or downstream consequence?

## Explicitly out of scope

Do not research: writing-assistant products, rhetoric or communication
theory, or LLM prose quality. Those were covered by the wave-1 pass
([`docs/research/contextual-communication-design.md`](../contextual-communication-design.md)).
This pass is about **evaluation methodology only**.

## What a good finding looks like

A named method, paper, tool, or practice; what it actually does; whether
it overlaps something RFC-0005 already proposes; and a verdict. Negative
results are wanted — "this is well studied and the answer is that it does
not work" is a finding.

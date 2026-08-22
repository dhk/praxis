# Handoff prompt

Copy everything below the line into Perplexity (or any research tool).
It is self-contained — the recipient needs no access to this repository.

---

You are doing a **prior-art scan on evaluation methodology**. I need
named methods, papers, tools and established practices, with an honest
verdict on each. Negative results are valuable: "this is well studied and
the answer is that it does not work" is a finding I want.

## The situation

I maintain a deterministic Python tool that detects communication signals
in prose — whether a message contains a request, a deadline, an
escalation path, a named next update time, a marker of uncertainty. There
are twelve detectors and each is a compiled regular expression. The tool
calls no language model at runtime; it is meant to be auditable and
reproducible.

**The problem: those regular expressions were written by a language
model.** Independent review recently found seven cases of a detector
firing on text it should not have — a courtesy phrase ("let me know if
this is not clear") satisfying a safety-critical *escalation path*
requirement, a polite request ("could you approve this?") counting as an
expression of *uncertainty*, "I will update the runbook" satisfying a
requirement for *a named next update time*. Three of the fixes for those
introduced the next failure.

I am now building a corpus of labelled examples to measure the detectors'
precision and recall. The obvious shortcut — have a language model
generate the corpus — risks the corpus inheriting exactly the blind spots
of the model that wrote the detectors. A refinement I am considering is
having one model generate examples and a second, independent model label
them, escalating disagreements to a human.

## Questions

Answer each separately, in this order.

**Q1. Multi-model labelling in place of human labels.** Is there
established practice for one model generating examples and a second
independently labelling them? What are the resulting precision/recall
figures understood to *mean*? What is known about correlated error
between model annotators from different families — do different training
corpora buy genuine independence, or do models share systematic biases?
Where has this been shown to work and where to fail?

**Q2. Behavioural / capability test suites.** Prior art for testing NLP
components by capability rather than aggregate accuracy — suites where
the *category supplies the label* rather than an annotator's judgment
("write twenty sentences that mention updating and name no time"). What
example granularity do these use — sentence, paragraph, document — and
how do their authors decide a suite is adequate rather than merely large?

**Q3. Weak supervision and label denoising.** Methods for combining
several noisy labelling sources into one label, and for estimating each
source's reliability without ground truth. What do those methods assume,
and do the assumptions hold when the sources are language models rather
than heuristics or crowdworkers?

**Q4. Agreement statistics for model annotators.** Which inter-annotator
agreement measures are used when annotators are models? Does the
conventional interpretation of those statistics survive the
substitution? Is there a recommended way to report a precision figure
whose labels are partly model-derived, so a reader knows what they are
looking at?

**Q5. Synthetic-corpus distribution shift.** Evidence on how measured
precision and recall move when a component is evaluated on generated text
rather than naturally occurring text. Is the size of that gap
characterised anywhere? Real messages are hard-wrapped, inconsistently
punctuated, and carry quoted threads and signatures; generated ones tend
to be clean single-paragraph archetypes. Are there mitigations short of
collecting real data?

**Q6. Counterfactual and boundary examples.** Prior art for minimal-pair
examples differing in exactly the property under test. My own case:
"please respond by 9" is a deadline, "the release slipped by 5 days" is
not, and the same four characters appear in both. How are such pairs
generated and validated?

**Q7. Spending scarce human attention.** Given a small human labelling
budget, where does the literature say to spend it — on annotator
disagreement, model uncertainty, decision boundaries, or the detectors
with the greatest downstream consequence?

## Explicitly out of scope

Writing-assistant products, rhetoric or communication theory, and LLM
prose quality. This is about **evaluation methodology only**.

## Output format

One section per question, in the order above. Under each, a table:

| Entry | What it is | Relevance to the situation above | Verdict |
|---|---|---|---|

**Verdict must be one of exactly three values:** `adopt/reference`,
`differentiate`, `ignore`. No other labels, and no rationale inside the
verdict cell — put rationale in a `**Notes:**` block below the table.

**No empty tables.** A question you find nothing for gets a single
`none found` row and the reason in Notes.

End with `## Open gaps` — what you could not answer, and what would be
needed to answer it.

Cite sources with links wherever you can. Prefer primary sources over
summaries. Say when something is your inference rather than something you
found.

# RFC-0005: Measuring the detectors

Status: Draft
Version: 0.1
Depends on: RFC-0003, RFC-0004

## Abstract

Every finding praxis reports rests on the regular expressions in
`signals.py`. This RFC makes their precision and recall a measured
quantity rather than an assumption, using a corpus of examples with known
answers, and states what the resulting numbers may and may not be taken
to mean.

## Problem

RFC-0003 lists as a known limitation: *"Detectors are regular
expressions. They see structure and marker words, not meaning. Precision
and recall are unmeasured."* RFC-0004 adds the same about voice
tolerances: *"reasoned, not calibrated."*

That was tolerable while the rule surface was small. It is not now:

| Rules | Count | Measured |
|---|---|---|
| Detectors | 12 | — |
| Structures, with weighted favours/avoids | 12 | — |
| Shades / tensions | 8 / 7 | — |
| Contract fields | 21 | — |
| Voice tolerances | 9 | — |

Across one working session, independent review found **seven** separate
cases of a detector firing on text it should not have. Each was fixed
against a handful of strings whoever was editing happened to think of,
and three of those fixes introduced the next failure. `UPDATE_CADENCE`
needed three corrections in three commits.

The pattern is not a regex problem. Correctness lives in the cases the
author did not imagine, and an author cannot test for those by imagining
harder.

## Proposal

### 1. A corpus of examples with known answers

`corpus/detectors.jsonl`, one JSON object per line:

```json
{"text": "Could you approve this by 3 p.m.?",
 "present": ["ask", "deadline"], "absent": ["uncertainty"],
 "source": "review", "note": "polite modal read as a hedge"}
```

**Only labelled detectors are scored.** An example names the signals it
is about; the rest are unlabelled and contribute nothing. Filling a
twelve-column matrix by guessing would manufacture agreement, and the
same `unknown`-over-`absent` discipline praxis applies to drafts applies
to its own evidence.

### 2. Provenance, because not all labels are equal

`source` records where an example came from:

| `source` | Weight |
|---|---|
| `hand` | Written by a person, or taken from a real message. Ground truth. |
| `review` | A case a reviewer found praxis getting wrong. Ground truth, and the strongest kind: a failure that actually happened. |
| `corpus` | Written while building the corpus, to pin a boundary the scores exposed. |
| `generated` | Produced by a language model. Excluded from the headline figure. |

The detectors were written by a language model. A corpus written by one
shares its blind spots, which is precisely what the corpus exists to
expose. Generated examples are permitted, scored separately, and never
counted alone.

### 3. Scoring

`praxis.measure.score()` reports precision, recall, and the specific
examples each detector gets wrong. A detector with no labelled example
reports **unmeasured**, never `0.000` — the two must not print the same.

The bar is 1.000 in both directions on the labelled set, and it rises by
*adding examples*, never by lowering the threshold.

## What this measured on the first run

The corpus found a class of failure review had not: detectors that
**miss** rather than over-fire.

```
ask            missed  "May I suggest Thursday?"
deadline       missed  "Please respond by 9."
consequential  recall 0.000
```

`consequential` is what decides whether a high-stakes claim needs
evidence, and it did not recognise *"the migration will fail."* A draft
asserting that was told its claims were supported.

Review found false positives; the corpus found false negatives. They are
complementary, and neither substitutes for the other.

The negatives were added **before** the patterns were touched, so a
recall fix could not be bought with precision: *"slipped by 5 days"* is a
duration, not a deadline; *"the plan will work"* is not a consequence.

## Non-goals

- A benchmark score. The corpus is small and knowingly incomplete; its
  job is to catch regressions and expose blind spots, not to rank praxis
  against anything.
- Measuring whether a *finding* is useful. This measures whether a
  detector agrees with what praxis claims that signal means. Whether the
  claim itself is the right one is a product question.
- Calibrating structure weights or voice tolerances. Those need a
  different kind of evidence and are out of scope here.

## Open questions

These are what the accompanying research pass exists to answer.

1. **Can multi-model generation-plus-adjudication substitute for human
   labels?** One model writes examples, a second independently labels
   them, and disagreement is escalated. This session is weak evidence
   *for* it: an independent model caught seven detector faults a human
   had not looked at. But agreement is not correctness, and two models
   sharing a wrong intuition produce a confident wrong label. What does
   the literature say the resulting numbers mean?
2. **What is the right unit of a labelled example?** A sentence is cheap
   and unambiguous; a whole message is realistic but labels a dozen
   signals at once and invites the guessing this design forbids.
3. **How should provenance tiers appear in a reported figure?** One
   headline number from ground truth with generated coverage alongside,
   or a single number with a stated confidence?
4. **Does synthetic-corpus distribution shift bite here?** Generated
   business prose is clean, single-paragraph and archetypal. Real
   messages are hard-wrapped, inconsistently punctuated, and carry quoted
   threads — the whitespace bug in RFC-0004 was found in a hand-written
   example that happened to wrap.
5. **Where should scarce human labelling attention go?** Disagreement
   sampling, boundary cases, or the detectors with the most downstream
   consequence (`consequential` and `escalation` gate safety-critical
   requirements)?
6. **What agreement statistic is appropriate** when the annotators are
   models rather than people, and does the usual interpretation of it
   survive that substitution?

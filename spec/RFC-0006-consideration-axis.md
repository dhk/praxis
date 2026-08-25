# RFC-0006: The consideration axis

**Type:** RFC · [document types](../AGENTS.md#documents)

Status: Draft
Version: 0.1
Depends on: RFC-0003, RFC-0005
Relates to: [dhk/alexandria](https://github.com/dhk/alexandria) research
`2026-08-13-organizational-writing-by-genre`

## Abstract

praxis ranks structures with weights written by argument. Alexandria
measured, across three models, what ten organizational genres *demand* and
what ten writing techniques *supply*, on one shared axis of ten
considerations. The two systems describe the same space and share no data.

This RFC defines that axis as praxis's join: a **demand profile** derived
from the contract, a **supply profile** carried by structures and packs,
and a match between them that replaces argued weights with recorded ones.
It also states what the corpus cannot yet support, because most of it
cannot.

## Problem

`strategy.rank` scores each `Structure` by summing `favors` and `avoids`
weights against contract values. Those weights are a hand-written
judgement about mechanism. RFC-0005 already names this: twelve structures
with weighted favours and avoids, none measured. ROADMAP Wave 4 commits to
calibrating them "against results instead of against argument".

Meanwhile the recommendation cannot explain itself in the writer's terms.
`recommend()` returns `because` as contract-field phrases — *intent is
request*, *time available is low*. A writer who wants to know why the
answer changes when the message must carry more care, or survive longer as
a record, has no vocabulary to ask in and no lever to pull.

Three things are missing, and they are the same thing:

1. **A shared vocabulary** between what a situation needs and what a
   mechanism does.
2. **Recorded rather than argued** weights.
3. **A lever** — the writer stating that this message needs more of
   something than its genre normally would.

## The axis

Ten considerations, from the alexandria study, unchanged:

`precision` · `brevity` · `scannability` · `actionability` ·
`confidence_calibration` · `empathy` · `persuasive_force` ·
`accountability` · `accessibility` · `durability`

They live in `considerations.py` as data, in the manner AGENTS.md requires
of every rule surface. One of the ten, `actionability`, is already a
dimension in `evaluate.py`; that overlap is evidence the two vocabularies
describe one space, and is not a reason to merge them. **Evaluation
dimensions answer "is this draft any good"; considerations answer "what
does this situation need, and what does this mechanism do about it."**
Keep them separate and named separately.

### Demand: what the situation needs

Alexandria's Matrix A gives a profile per genre, scored `0..+3`.

**`genre` cannot carry this today.** It is a free-text field with
`domain=None`, which means it is not in `SELECTORS`, which means
`material_questions` never asks about it — the perturbation mechanism only
walks fields with a closed domain. A demand profile keyed on genre would
be keyed on something praxis never establishes.

Nor should the domain simply be closed to alexandria's ten. Those ten are
*organizational* genres. praxis covers cover letters and résumés, which are
not among them, and narrowing the field to make a lookup convenient would
shrink the product to fit its data.

So the demand profile is **derived from the contract**, and alexandria's
Matrix A is its calibration set:

> `considerations.demand(contract) -> Profile`

Where the contract corresponds to one of the ten studied genres, the
derived profile must reproduce that genre's published column. That is a
test, not an aspiration — ten fixtures, each asserting the derivation
against `04-normalized`, in the manner of
`test_run_pipeline_matches_cli_artifacts`. A derivation that cannot
reproduce the measurement is wrong, and will say so in CI.

This is also the more praxis-shaped answer: a genre is a shorthand for a
bundle of contract values, and praxis already holds the bundle in more
detail than the label does.

### Supply: what the mechanism does

Alexandria's Matrix B gives a profile per technique, scored `-2..+2` as
published, where negative means the technique actively damages that
consideration. Five of its hundred cells publish no value at all.

The overlap with praxis's mechanisms is **partial, and this is the finding
that shapes the design**:

| Alexandria technique | praxis mechanism |
|---|---|
| BLUF/Army | `bluf` (structure) |
| Minto | `pyramid` (structure) |
| Toulmin | `cer` (structure) |
| ASD-STE100 | `controlled_language` (pack) |
| Hotaling | `concise_scientific_writing` (pack) |
| Amazon memo, ISO 24495-1, Blameless PM, Hemingway, repo skills | none |

Five of sixteen praxis mechanisms have a measured supply profile. Nine
structures — `scqa`, `prep`, `sbar`, `sia`, `hazard_first`, `repair`,
`reassure`, `cme`, `star` — and two packs have none, and five studied
techniques have no praxis counterpart at all.

**An absent profile is `unknown`, never zero.** This is the detector rule
from RFC-0003 applied one level up: a miss must never be reported as an
absence. A structure with no measured profile is not a structure that
supplies nothing.

### The dial

The writer states that this message needs more or less of a consideration
than its situation implies:

```
python -m praxis design draft.md --set intent=request --dial durability=+2
```

A dial is a contract input like any other — stored on the contract,
carried into the session, and never persisted as a derived value.
`considerations.demand` applies dials last, so the writer's override is
always visible as an override rather than folded into the base profile.

Two consequences follow, and both are enforceable:

- **A dialled consideration is never asked about.**
  `material_questions` must exclude any consideration the writer has
  already moved. Asking about something the writer just set is the
  interrogation failure the layer exists to avoid.
- **Perturbation extends to dials.** Ten considerations across a
  `-3..+3` domain is seventy re-runs of `recommend` — cheap, deterministic,
  no network. The material-questions test in both directions applies
  unchanged.

## The match

`strategy.rank` gains a second scorer. For each mechanism with a supply
profile, score the fit between demand and supply; sum with the existing
weighted score.

**The argued weights are not deleted.** They cover mechanisms the corpus
does not, and deleting them would trade a measured minority for an
unmeasured majority. The recorded score is additive and its contribution
is reported separately, so a reader of `because` can see which half of the
recommendation came from measurement and which from argument.

`recommend()` gains:

- `demand` — the resolved profile, with dials marked as overrides.
- `because_measured` — the considerations that decided it, in the
  writer's vocabulary rather than the contract's.
- `unmeasured` — mechanisms ranked without a supply profile, named.
- `contested` — see below.

## What the corpus cannot support

This is the part that decides whether the join is honest.

The study is **silver**, not gold. Its coverage is
`contested-cells-only`: eleven of two hundred cells have votes promoted
into `04-normalized`. The published tables carry all two hundred, and
`validate.py` cross-checks only the eleven. The rest are a median of three
model outputs, transcribed.

It has **no outcome evidence**. Its own analysis says so: *"No technique
here has been shown to improve organizational decision quality, trust
calibration, incident recurrence, or the durability of reasoning."*

And the ablation moved it. Run `r-2026-0814-01` asked the same question
with the brief's framing removed; the commitment-versus-calibration defect
survived, but three confidence-calibration cells swung by up to three
points. **The defect was in the material. The severity was in the brief.**

Three rules follow, and they are the conditions of this RFC:

1. **Every cell carries provenance.** Study slug, run id, and whether the
   cell is contested. A profile value with no source is not admissible.
2. **A recommendation that turns on a contested cell says so.** The study
   viewer already does this; the engine must not do less. Where the margin
   between first and second place is smaller than the spread of a
   contested cell that contributed to it, `confidence` drops and the cell
   is named.
3. **This is not Wave 4.** Importing these numbers replaces an argued
   weight with a better-documented argued weight. It is lateral on
   evidence and large on coherence. Wave 4 remains outstanding, and
   nothing in this RFC may be logged against it.

## Non-goals

- **No model call.** Everything here is table lookup and arithmetic. The
  two tests that enforce a modelless, networkless engine apply unchanged.
- **No new prose surface.** The dial changes what praxis recommends. It
  does not change who writes the sentences, which is still not praxis.
- **Not a score for the draft.** A demand profile is what the situation
  needs. It is not a grade, and must not be rendered as one.
- **No silent widening of `genre`.** If the field's domain is ever
  closed, that is its own change with its own argument, not a side effect
  of wanting a convenient lookup.

## Consequences

The gap VISION names — *"The design layer recommends a structure; it
cannot yet select or enforce a language mechanism"* — narrows. Once a
`Structure` and a `Pack` both carry a supply profile on one axis, a single
match ranks both, and "a BLUF in STE100" becomes a computed pair rather
than a flag the writer has to remember. It does not close: five of
sixteen mechanisms are measured, so the pairing is available where the
corpus reaches and argued elsewhere.

The dependency is new and real. praxis has never depended on alexandria
for anything at runtime. Profiles must be vendored as data with their
provenance, not fetched, so the engine stays offline and a corpus
correction arrives as a reviewable diff.

## Open questions

1. **What derives the demand profile?** A table over contract values, or
   a small set of rules? The ten calibration fixtures constrain it but do
   not determine it.
2. **Is `-3..+3` the dial domain?** The published spreads are `-2..+2`
   for supply and `0..+3` for demand. Neither is a declared range; both
   are what one run happened to produce. A symmetric dial is easier to
   explain and matches neither.
3. **What is the fit function?** Sum of products, penalised distance, and
   worst-case-first all rank differently when a technique is excellent
   overall and damaging on one consideration the situation needs — which
   is exactly the STE100 case the study found.
4. **Do the five unmatched techniques become praxis mechanisms?** Amazon
   memo and ISO 24495-1 are plausible; Hemingway is the one technique in
   the set with no published methodology and probably should not be.

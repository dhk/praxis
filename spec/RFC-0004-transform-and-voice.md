# RFC-0004: Transform mode and voice

**Type:** RFC · [document types](../AGENTS.md#documents)

Status: Draft
Version: 0.1
Depends on: RFC-0003

## Abstract

A third mode for the design layer. Evaluate says what is wrong with a
draft; **transform** says what to change, *where*, and what may not be
touched on the way. Plus a voice check that reports which of the
writer's habits a rewrite kept — and, deliberately, refuses to say
anything about authorship.

The engine still writes nothing. An edit carries a kind, a position, and
an instruction describing what the new text must accomplish. The words
come from the client's model, at the places praxis names.

## Problem

Evaluate mode reports that a message has no deadline. That is a
critique. Acting on it requires knowing where the deadline goes, whether
inserting it would disturb something the writer marked untouchable, and
whether the resulting text still sounds like them.

Those are positional questions, and the layer had no positions in it:
findings carried evidence *strings*, protected content was checked by
containment with no idea where it was, and `voice_integrity` had
reported `unknown` since the layer shipped.

## Proposal

### 1. Spans

`spans.py` locates things: detector matches, sentences, paragraphs,
declared protected phrases, and the point where the message body begins
(below any salutation — a bottom line goes under "Hi Priya,", not above
it). A span is a half-open character range carrying its own text.

Protected phrases are matched **across whitespace**. A writer types
"perhaps we could discuss"; a hard-wrapped draft contains "perhaps we
could\ndiscuss". Exact matching missed it, and missed it *silently* —
reporting the phrase absent while the writer believed it protected. The
same flaw made a rewrite that merely re-wrapped its lines fail its own
invariant check.

### 2. Transform

Each gap the evaluation reports becomes a located edit: `insert` at an
offset, or `revise` / `move` / `cut` over a span, with an instruction
saying what the new text must do.

Three properties matter more than the edit list:

* **Every gap is accounted for.** A reported gap with no located change
  is the failure this mode exists to avoid, so the result separates gaps
  *folded into* another edit from gaps nothing could locate. For a
  conclusion-first structure with no request in the draft, "state the
  action at the top" is simultaneously the structural fix and where the
  deadline goes — three edits at one offset would be one instruction
  split into three, so two of them fold and say so.
* **Protected content is checked before an edit is offered.** An edit
  overlapping a protected span is reported as blocked, never dropped:
  the writer's constraint and the advice are in tension and that is
  theirs to resolve.
* **Transform must be asked for.** "What is wrong" and "what to change"
  are different questions. Answering the second unprompted is the
  rewriting reflex the whole layer exists to avoid, so `mode` is
  explicit and `auto` never selects it.

### 3. Voice, and what was measured out of it

The obvious design is stylometric: compare function-word frequencies
between the draft and the rewrite and report a similarity. That was
built, and then tested against pairs whose answer is already known — two
halves of one document are the same writer, two different documents are
not:

| | cosine on function words | Canberra |
|---|---|---|
| Same writer (document halves) | 0.712 – 0.977 | 0.373 – 0.621 |
| Different writers | 0.609 – 0.883 | 0.151 – 0.492 |

**The groups overlap.** Same-author pairs scored *below* different-author
pairs, so any threshold drawn through that range decides authorship by
coin flip. Stylometry needs thousands of words per sample; an email is
not that.

The similarity number was removed rather than shipped behind a caveat,
because a number in a report is read as a finding no matter what the
caveat says. This table is recorded here so nobody re-adds it without
new evidence.

What survives is what was never inferential: **counts**. Whether the
rewrite kept the writer's semicolons, sentence rhythm, contractions,
first-person rate, paragraph length. Directly observable, checkable by
the writer against the same text, and much closer to what people mean
when they say a rewrite stopped sounding like them.

`voice.compare` therefore never returns a `gap`. A dropped habit may be
exactly what the rewrite was asked to do — a scannable version *wants*
shorter sentences — and reporting that as a fault would be praxis
disagreeing with an instruction it was given. Below about 80 words it
reports `unknown`, because a per-thousand rate computed from one comma
is arithmetic on nothing.

## Surface

| Interface | Addition |
|---|---|
| MCP | `design_transform(session_id, voice_reference)` |
| CLI | `praxis design --transform`, `--voice PATH` |
| Library | `design(..., mode="transform", voice_reference=...)` |
| Artifact | A "Located changes" section, in document order, with blocked edits called out |
| Depths | `brief.at_depth(result, "edits")` |

## Non-goals

- Writing the replacement text. Permanently.
- Applying an edit. praxis locates and audits; the client edits.
- Claiming a rewrite is or is not by the same author.
- A voice `gap`. Habits change for good reasons.

## Deferred from wave 2

Two roadmap items are not in this RFC: the design layer in the browser
viewer, and difference maps in the transformation harness's Compare
panel. Both are `web/` work whose risk is browser behaviour rather than
engine correctness, and neither is needed for the wave's stated outcome.
The engine modules already ship in the Pyodide bundle, so the viewer
work is wiring rather than porting.

## Known limitations

- **Edits are located, not verified.** praxis says where to insert a
  deadline; nothing checks the client put one there until the revised
  draft comes back through evaluate.
- **`move` names a sentence, not a destination ordering.** "Move this to
  the top" is unambiguous; a three-way reordering is not expressible.
- **Habit tolerances are reasoned, not calibrated.** They are set to
  avoid single-token noise, and the thresholds have not been measured
  against a corpus of rewrites people judged as voice-preserving.

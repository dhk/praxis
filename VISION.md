# Praxis Vision

## Product thesis

Every mainstream writing tool sells prose. Ask for help and you get
replacement text — better text, often, but text whose reasoning you
cannot see, cannot argue with, and cannot reuse tomorrow.

Praxis sells the decision behind the prose, and proves the prose kept it.

The claim underneath is narrow and testable: **most of the value in a
consequential message is decided before a word is written.** Who reads
this first. What they can actually approve. What happens if they delay.
What must be proven and what may be asserted. Which figures and
commitments cannot move. Those decisions determine whether the message
works. The sentences are downstream — and they are the part a language
model is already good at.

So praxis does not write. It decides the shape, states what may not
move, and audits whatever text comes back against those constraints.

## What praxis is

An **auditable communication-design instrument**, in two layers over one
Python engine.

| Layer | Question it answers | Status |
|---|---|---|
| **Transformation harness** | Which mechanical defects can be fixed with evidence, and did protected content survive? | Shipped |
| **Design layer** | What should this message do for this reader at this level of risk, and does the draft do it? | Wave 1 |

The harness applies rules. The design layer applies *judgment* — but
holds the judgment in data a human can read and overrule, rather than in
a prompt.

Both produce the same kind of output: an artifact trail. Not a verdict,
not a score, but a record of what was observed, what was recommended,
what changed, and what was deliberately left alone.

## What praxis is not

- **Not an AI writer.** The engine holds no API key, calls no model, and
  reaches no network. It cannot write a sentence, and adding that
  capability would destroy the reason to trust its audits.
- **Not a grammar or style checker.** Sentence-level correctness is a
  solved and crowded problem. Praxis operates above it: order, evidence,
  stakes, verification.
- **Not a tone slider.** Tone is a downstream consequence of a strategy,
  never a substitute for choosing one.
- **Not a hosted service.** No accounts, no backend, no document upload,
  no telemetry.
- **Not a claim of semantic equivalence.** Validation proves specific
  invariants survived. It does not prove a rewrite means the same thing.

## North star

> A writer should be able to hand a colleague the *reasoning* behind a
> message, not just the message — and the colleague should be able to
> disagree with it in one screen.

## Why this is not ChatGPT with extra steps

The distinction is not quality of prose. It is what persists, what is
inspectable, and what is guaranteed.

| | Praxis | General assistants | Grammarly / Writer |
|---|---|---|---|
| Unit of work | An editable **communication contract** | A conversation turn | A document |
| Strategy | Recommended, named, and explained from the contract | Implicit in the prompt; unstable between turns | Not modelled — tone and goal presets |
| Questions asked | Only those whose answers change the recommendation, computed | Whatever the model decides to ask | Fixed intake fields |
| Alternatives | At most two, only against a named tradeoff, each priced | Unbounded regeneration | Suggestion lists |
| Guarantee | Protected content, commitments, and uncertainty markers are **machine-checked** in every variant | None | Local-clarity heuristics |
| Verdict | Gaps with the evidence attached; no overall score | Prose critique | A number |
| Inference cost | **Zero.** The engine runs no model | Per request | Per seat |

The guarantee row is the moat. Anything can produce a warmer draft.
Almost nothing can prove the warmer draft did not quietly drop the
caveat, the deadline, or the 40% — and *that* is the fear that stops
people using AI on the messages that matter.

## The economics

The design layer costs nothing per run. It is deterministic Python over
a contract: no inference, no keys, no vendor.

Where prose is wanted, it comes from the model the writer is already
talking to, through MCP. The conversation was already being paid for;
praxis adds structure to it rather than a second bill. That is also what
makes the audit meaningful — a rewriter grading its own rewriting is not
an audit.

## Product invariants

1. **The engine never writes prose.**
2. **Evidence before assertion** — every finding shows what it saw.
3. **Inference is labelled, never promoted to fact.**
4. **Content, evidence, voice, and risk integrity are separate constraints.**
5. **Warmer never means less truthful; shorter never means the caveat is gone.**
6. **Ask only what changes the answer.**
7. **One recommended version; alternatives only against a real tradeoff.**
8. **No opaque scores.**
9. **Determinism wherever determinism is possible.**
10. **Artifacts at every step, and they must be visual where comparison is the point.**
11. **Usable vertical slices** — every wave ends in something a writer can use.
12. **Local-first**: no accounts, no backend, no document upload, no telemetry.

This list is mirrored in [`AGENTS.md`](AGENTS.md) — same items, same
order; change both together.

## Honest limits

Praxis detects what regular expressions and structure can detect. It can
see that no deadline appears, that a consequential claim sits nowhere
near a number, that every marker of uncertainty vanished between two
drafts. It cannot see whether an argument is sound, whether a figure is
true, or whether a reader will actually feel acknowledged.

That is why the third evaluation status is `unknown` and why it is used
often. A tool that reported confidence it did not have would be exactly
the thing this one exists to replace.

## Long-term outcome

Praxis becomes the layer a writer reaches for when a message has real
consequences: a place to decide what the message must accomplish, borrow
whichever model they like for the sentences, and leave with an artifact
that shows the reasoning, the tradeoffs that were priced, and proof that
nothing that mattered went missing.

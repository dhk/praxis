# The prompt pack

**Type:** guide · [document types](../AGENTS.md#documents)

Eleven review prompts. Copy one, paste it into whatever model you already
use, and put a real draft under it. Nothing to install, no account, no
praxis on your machine.

This is the least you can touch of praxis and still get something from it.
It is also the surface that stays furthest from the engine — see
[What this costs you](#what-this-costs-you).

## Which one

| If you are writing | Use |
|---|---|
| Anything, or you are not sure | [`review-general.md`](review-general.md) |
| A short factual brief | [`review-info-brief.md`](review-info-brief.md) |
| A write-up of what you found | [`review-investigation-summary.md`](review-investigation-summary.md) |
| A pitch for work not yet funded | [`review-research-proposal.md`](review-research-proposal.md) |
| An argument for a course of action | [`review-recommendation.md`](review-recommendation.md) |
| A notice while something is broken | [`review-incident-notification.md`](review-incident-notification.md) |
| An account of something that broke | [`review-postmortem.md`](review-postmortem.md) |
| A periodic update on progress | [`review-status-update.md`](review-status-update.md) |
| A record of what was decided and why | [`review-decision-record.md`](review-decision-record.md) |
| A disagreement you are putting on record | [`review-dissent.md`](review-dissent.md) |
| Documentation meant to be looked things up in | [`review-reference-docs.md`](review-reference-docs.md) |

The general one asks what you are writing before it weighs anything. The
genre ones already know, and carry that genre's weighting — which
considerations matter most, which are irrelevant, which techniques serve it,
and which damage something it needs.

## What they refuse to do

Each prompt forbids four things, as prohibitions rather than preferences:

- **It may not rewrite your prose.** A reviewer that rewrites has answered a
  question you did not ask, and the rewrite arrives without the reasoning
  that produced it.
- **It may not score the draft.** A number replaces a judgement with a figure
  and invites you to optimise the figure.
- **It may not guess.** *"I do not know, and here is the question that would
  settle it"* is a complete answer, and the prompt says so.
- **It may not ask you a form.** One question at a time, each naming what it
  decides between, stopping as soon as nothing further would change the
  reading.

Those refusals are the product. Without them you have a wash of plausible
edits, which is what you already had.

## What they are worth

The weightings are the median of three models scoring independently, from
[the organizational-writing-by-genre investigation](https://github.com/dhk/alexandria/tree/main/research/2026-08-13-organizational-writing-by-genre).
They are judgements about **mechanism**. No technique in that study has been
shown to improve decision quality, trust, or incident recurrence — the
matrices rest on proxies, not outcomes, and the per-model votes for every
contested cell are published rather than averaged away.

Every prompt carries that caveat in its own body, under *Where this standard
comes from*, so it travels with the file rather than staying here.

## What this costs you

**These are a snapshot.** They were generated from the study as published on
2026-08-25 and they do not update. If the investigation is corrected, or
praxis's own rules move, your copy will not know. Nothing in the file tells
you it has gone stale.

That is the trade for needing nothing installed, and it is worth naming
rather than discovering. The two other surfaces close it from opposite ends:
the generator produces a prompt from your situation at the moment you ask,
and the MCP server keeps the engine in the loop while you write.

A machine-checkable version stamp belongs in the prompt body, not in this
file — a stamp here does not help anyone who copied the prompt. It is
deliberately not in this pull request, because adding it means changing the
generator that produces both these files and the study viewer's Review
Prompt tab, and those two must not diverge.

## How these were produced

Byte-identical to what the [study viewer](https://github.com/dhk/alexandria/tree/main/research/2026-08-13-organizational-writing-by-genre/06-viewer)
renders in its Review Prompt tab — verified against the live page for all
eleven, not retyped from it. If you change one here, change it there.

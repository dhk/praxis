# Detector evaluation research

**Type:** guide · [document types](../../../AGENTS.md#documents)

Prior art for RFC-0005: how to measure text detectors whose rules were
written by a language model, without the evaluation inheriting the same
blind spots.

Read in this order:

0. [`specification.md`](specification.md) — what decision this settles,
   what counts as sufficient evidence, and what we do under each possible
   outcome. Written before the findings, so they cannot be read to
   confirm what we already wanted.
1. [`brief.md`](brief.md) — the questions, each traced to an open
   question in [RFC-0005](../../../spec/RFC-0005-detector-measurement.md).
2. [`handoff-prompt.md`](handoff-prompt.md) — the brief and output format
   as one self-contained prompt for a tool with no repo access.
3. [`search-prompt-generation.md`](search-prompt-generation.md) — a narrower
   paste covering only brief questions Q1, Q2, Q3 and Q6: how much of the
   corpus can be machine-generated, and who assigns the labels. Use it when
   the recipient is a search tool rather than a researcher; the full brief
   asks more than a search will usefully answer at once.
4. [`findings/`](findings/) — one file per source, written independently.
5. `synthesis.md` — written once findings are in: where sources agree,
   where they conflict and which is more credible, what only one source
   caught, and what remains unanswered.

Findings stay independent until synthesis. Two sources that have read
each other produce one opinion in two files, and the point of asking
twice is to find where they diverge.

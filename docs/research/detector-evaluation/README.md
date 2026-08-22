# Detector evaluation research

Prior art for RFC-0005: how to measure text detectors whose rules were
written by a language model, without the evaluation inheriting the same
blind spots.

Read in this order:

1. [`brief.md`](brief.md) — the questions, each traced to an open
   question in [RFC-0005](../../../spec/RFC-0005-detector-measurement.md).
2. [`handoff-prompt.md`](handoff-prompt.md) — the brief and output format
   as one self-contained prompt for a tool with no repo access.
3. [`findings/`](findings/) — one file per source, written independently.
4. `synthesis.md` — written once findings are in: where sources agree,
   where they conflict and which is more credible, what only one source
   caught, and what remains unanswered.

Findings stay independent until synthesis. Two sources that have read
each other produce one opinion in two files, and the point of asking
twice is to find where they diverge.

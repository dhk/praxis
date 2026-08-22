# Research

Prior-art passes commissioned to de-risk a design doc before it leaves
Draft. Each topic gets its own folder:

| Document | Type | Answers |
|---|---|---|
| `idea.md` | research idea | A question worth investigating, before it is worth specifying |
| `specification.md` | research specification | What the research settles, what counts as sufficient evidence, and what we do under each outcome — written **before** the findings |
| `findings/` | research results | One file per source, written independently |
| `synthesis.md` | research recommendations | Where sources agree, conflict, or leave a gap — and what to do |

`brief.md` and the handoff prompts are **handouts**: the specification's
questions packaged for a particular recipient. They are derived from it
and carry no decision it does not already carry. The document types are
enumerated in [`AGENTS.md` § Documents](../../AGENTS.md#documents).

The specification is the newer half of the convention and exists because a
brief alone lets findings be read to confirm whatever the author already
preferred. Fixing the decision rules in advance removes that freedom.

| Topic | Informs | Status |
|---|---|---|
| [`detector-evaluation/`](detector-evaluation/) | [RFC-0005](../../spec/RFC-0005-detector-measurement.md) — measuring detectors whose rules an LLM wrote | Brief, full handoff and a narrower search prompt written; findings open |
| [`contextual-communication-design.md`](contextual-communication-design.md) | [RFC-0003](../../spec/RFC-0003-contextual-communication-design.md) — the design layer | Source brief, not a commissioned pass |

Findings stay independent until synthesis: sources that have read each
other produce one opinion in several files.

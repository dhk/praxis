# Research

Prior-art passes commissioned to de-risk a design doc before it leaves
Draft. Each topic gets its own folder:

| Document | Answers |
|---|---|
| `specification.md` | What decision the research settles, what counts as sufficient evidence, and what we do under each possible outcome — written **before** the findings |
| `brief.md` | The questions, each traced to an open question in the design doc |
| `handoff-prompt.md` | The brief as one self-contained paste for a source with no repo access |
| `findings/` | One file per source, written independently |
| `synthesis.md` | Where sources agree, conflict, or leave a gap |

The specification is the newer half of the convention and exists because a
brief alone lets findings be read to confirm whatever the author already
preferred. Fixing the decision rules in advance removes that freedom.

| Topic | Informs | Status |
|---|---|---|
| [`detector-evaluation/`](detector-evaluation/) | [RFC-0005](../../spec/RFC-0005-detector-measurement.md) — measuring detectors whose rules an LLM wrote | Brief, full handoff and a narrower search prompt written; findings open |
| [`contextual-communication-design.md`](contextual-communication-design.md) | [RFC-0003](../../spec/RFC-0003-contextual-communication-design.md) — the design layer | Source brief, not a commissioned pass |

Findings stay independent until synthesis: sources that have read each
other produce one opinion in several files.

# Praxis

> A reference architecture and executable harness for transparent, auditable document transformation pipelines.

Praxis treats document improvement as an engineering workflow rather than a black-box rewrite. A source document moves through named operations that emit observations, recommendations, transformations, validation checks, and reports.

The first vertical slice implements a small **Concise Scientific Writing** transformation pack inspired by evidence-based guidance for concise technical prose. It is deliberately limited: it proves the harness, artifact trail, and validation loop before expanding the architecture.

## Core idea

Every transformation begins as an observation.

```text
Source Document
  -> Parse
  -> Observe
  -> Recommend
  -> Transform
  -> Validate
  -> Report
```

Each run creates an artifact directory containing machine-readable JSON and human-readable Markdown.

## Quick start

```bash
python -m praxis run examples/concise_scientific_writing/input.md --out artifacts/demo
```

Then inspect:

```text
artifacts/demo/
├── observations.json
├── recommendations.json
├── transformations.json
├── validation.json
├── final.md
└── report.md
```

Run the test harness:

```bash
python -m pytest
```

## What this is

- A small executable harness.
- A proof of an auditable transformation pipeline.
- A place to encode writing guidance as transformations, not monolithic prompts.

## What this is not yet

- A general-purpose editor.
- A polished CLI product.
- A model-independent specification.
- A replacement for human review.

## Design principles

1. Observe before changing.
2. Every transformation requires evidence.
3. Preserve meaning unless explicitly instructed otherwise.
4. Validate before acceptance.
5. Emit artifacts at every step.
6. Prefer another operation over another prompt.

## Repository layout

```text
praxis/                  Python harness
packs/concise_scientific_writing/
                             Reference transformation pack
examples/concise_scientific_writing/
                             Golden example input
artifacts/                   Generated outputs, ignored by git
docs/                        Design notes
spec/                        Early RFC/spec documents
tests/                       Regression tests
```

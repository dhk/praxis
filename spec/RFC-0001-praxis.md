# RFC-0001: Praxis

Status: Draft  
Version: 0.1

## Abstract

Praxis is an architecture for converting human guidance into observable, testable transformation pipelines.

A pipeline must emit intermediate artifacts and must validate transformations before accepting them.

## Problem

Many document workflows collapse knowledge, workflow, transformation, and reporting into one opaque instruction. This makes results difficult to audit, reproduce, or improve.

## Proposal

Represent document work as a pipeline of passes:

```text
Parse -> Observe -> Recommend -> Transform -> Validate -> Report
```

Each pass has explicit inputs, outputs, and invariants.

## Principles

- Observe before changing.
- Every transformation requires evidence.
- Preserve meaning unless the user explicitly asks otherwise.
- Validation precedes acceptance.
- Artifacts are first-class outputs.

## Reference implementation

The first reference implementation applies concise scientific writing guidance to Markdown documents.

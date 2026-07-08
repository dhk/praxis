# RFC-0002: Praxis UI

Status: Draft
Version: 0.1
Depends on: RFC-0001

## Abstract

A static web UI that lets a user enter or upload a document, run the Praxis pipeline, and step through each pass with its artifacts. The UI is a viewer for the artifact trail; it adds no transformation logic of its own.

## Goals

- Enter a document by paste, file upload (`.md`, `.txt`), or a bundled example.
- Step through the six passes — Parse, Observe, Recommend, Transform, Validate, Report — one screen per pass.
- Show the evidence chain: click any transformation and trace it back through its recommendation to its observation.
- Download the complete artifact trail (the same six files the CLI writes).
- Deploy as a static site on GitHub Pages or Vercel with no backend.

## Non-goals

- No accounts, persistence, or server-side storage. Documents never leave the browser.
- No editing of transformation packs (view-only in v1).
- No accepting or rejecting individual transformations mid-run (v1 runs the pipeline exactly as the CLI does).
- No LLM calls. The pipeline stays deterministic and auditable.

## Architecture decision: run the Python harness in the browser

The `praxis` package is stdlib-only and small. Run it unchanged in the browser via Pyodide (CPython compiled to WebAssembly).

**Why not a TypeScript port?** A port creates a second implementation of the rules, validation, and metrics. The two drift, and the UI stops being evidence of what the harness does — which defeats the project's purpose. One source of truth outweighs load time.

**Why not a serverless API?** It works on Vercel but not GitHub Pages, adds a network hop and a privacy question, and still requires packaging the same Python code. Client-side execution keeps both deployment targets open.

**Cost:** Pyodide is a one-time ~7 MB download. Mitigations: load it in the background while the user types, cache it via service worker, and show pipeline status ("loading engine") until ready. If load time proves unacceptable, revisit — the UI/engine boundary below makes the engine swappable.

### Engine boundary

The UI calls a single function and receives the full artifact trail:

```ts
interface PraxisResult {
  observations: Observation[];      // observations.json
  recommendations: Recommendation[]; // recommendations.json
  transformations: Transformation[]; // transformations.json
  validation: Validation;           // validation.json
  final: string;                    // final.md
  report: string;                   // report.md
  metrics: { before: Metrics; after: Metrics };
}

runPipeline(source: string): Promise<PraxisResult>
```

TypeScript types mirror the dataclasses in `praxis/models.py` exactly. The engine module (Pyodide bootstrap + a thin Python shim reusing `praxis.cli.run` logic without file I/O) is the only code that knows Python exists.

**Harness prerequisite:** extract the pipeline core from `cli.run` into a `praxis.pipeline.run_pipeline(text: str) -> dict` function that returns the artifacts instead of writing files. The CLI and the UI shim both call it. This is the only change required to the existing package.

## UX

One page, two zones: a persistent **pass stepper** across the top and the **pass panel** below it.

### Pipeline model

The pipeline executes in milliseconds, so the UI does not animate execution. It runs the whole pipeline once, then lets the user step through the completed artifact trail. Stepping is inspection, not execution — consistent with "the artifact trail is the product."

### Stepper

```
[1 Input] → [2 Observe] → [3 Recommend] → [4 Transform] → [5 Validate] → [6 Report]
```

- Before a run: only Input is enabled.
- After a run: all steps enabled, each showing a summary badge (e.g. "12 observations", "9 applied / 3 flagged", "pass"). Free navigation in any order.
- Editing the input invalidates the run: steps 2–6 grey out until re-run.

### Pass panels

**1 — Input.** Textarea with Markdown source, file-upload button (drag-and-drop accepted), "Load example" (bundled `examples/concise_scientific_writing/input.md`), live metrics (characters, words, sentences, avg sentence length), and the pack in effect (id, version, transformation list from `pack.yaml`). Primary action: **Run pipeline**.

**2 — Observe.** Read-only source with each observation's evidence highlighted, colored by safety. Sidebar lists observations grouped by rule; each shows id, evidence, reason, safety badge. Clicking either the highlight or the list entry selects and scrolls to its counterpart.

**3 — Recommend.** Table of recommendations: id, action, before → after, reason, safety. Each row links back to its observation (jumps to step 2 with that observation selected). `review_long_sentence` rows are visually distinct: they propose no text change.

**4 — Transform.** Two tabs:
- *Diff*: original vs. transformed document, word-level inline diff, applied changes colored by safety.
- *Log*: the transformation records — id, rule, before/after, applied yes/no, validation status. Not-applied (`review`) entries shown separately as "flagged for human review."

**5 — Validate.** Overall status (pass/fail), the protected-token check with the token list (URLs, numbers, citations, bracketed references), any missing tokens in red, and the standing caveat: validation is conservative and evidence-based; it does not prove semantic equivalence.

**6 — Report.** Rendered `report.md` (metrics before/after, validation summary, transformation log, final document). Actions: **Copy final document**, **Download final.md**, **Download artifact trail** (zip of the six files, identical to a CLI run's output directory).

### Safety color code

Used consistently in highlights, badges, and diffs:

| Safety | Meaning | Treatment |
| --- | --- | --- |
| `safe` | Applied automatically | green |
| `low_risk` | Applied automatically | amber |
| `review` | Flagged only, never applied | purple, dashed underline |

Colors must meet WCAG AA contrast and be paired with the text label, never color alone.

## Implementation shape

- Vite + React + TypeScript, static build (`vite build` → `dist/`).
- Pyodide from CDN with the `praxis` wheel (or source tree) served as a static asset; a service worker caches both.
- Diffing: a small word-diff library or ~50 lines of LCS; no server.
- Zip download via a client-side zip library.
- Repository layout: `ui/` directory in this repo, deployed by CI (GitHub Actions → Pages, or Vercel project rooted at `ui/`).

## Acceptance checks

1. Pasting the golden example and running produces artifacts byte-identical (JSON/Markdown content) to `python -m praxis run` on the same input.
2. Every transformation in step 4 links to a recommendation in step 3 and an observation in step 2.
3. A document with no matches runs cleanly: empty observation list, no diff, validation pass.
4. A 50 kB document runs without freezing the UI (pipeline executes in a web worker).
5. The site works offline after first load (service worker).

## Future (out of scope for v1)

- Accept/reject individual recommendations before transform (turns the UI into a review tool).
- Pack selection and pack authoring.
- Shareable run permalinks (requires encoding the document in the URL or adding storage — revisit privacy).

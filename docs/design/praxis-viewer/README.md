# Handoff: Praxis artifact-trail viewer (RFC-0002)

**Type:** requirement · [document types](../../../AGENTS.md#documents)

## Overview
Praxis is a deterministic, stdlib-only Python pipeline that rewrites prose for clarity in
six passes. This handoff covers the **web UI** for it: a static, single-page site where a
user enters/uploads a document, runs the pipeline **once**, and then steps through each of
the six passes and its artifacts. The UI **inspects a completed artifact trail** — it adds
no transformation logic of its own.

## About the design files
The files in this bundle are **design references created in HTML** — a prototype of the
intended look, structure, and behavior. They are **not production code to copy directly**.
The task is to **recreate this design in the target codebase's environment** (React, Vue,
Svelte, etc.) using its established patterns, or — since this is greenfield — to pick the
most appropriate stack and build it there.

Two files carry the same spec:
- **`Praxis UX Spec (standalone).html`** — open in a browser to *see* the rendered spec
  (styled, self-contained, works offline). Best for reading and design reference.
- **`Praxis UX Spec.dc.html`** — the editable source. Every layout, color, and size is an
  inline style with exact values — read this to lift precise measurements and tokens.

## Fidelity
**Hi-fi for visual language, wireframe for the app screens.** The spec is rendered in the
final DHK *Electric Cobalt* design language (final colors, type, spacing, components), so
treat those tokens as production-accurate. The six pass panels are drawn as **annotated
wireframes** — they define layout, content, and interaction intent precisely, but the
developer should build the real screens using these as the structural guide, applying the
Electric Cobalt tokens below for styling.

## Product model (read first)
- The pipeline runs in **milliseconds**, so the UI does **not** animate execution. It runs
  the whole pipeline once, then lets the user walk the completed trail.
- **Stepping is inspection, not execution.** "The artifact trail is the product."
- Six passes, one panel each: **1 Input → 2 Observe → 3 Recommend → 4 Transform →
  5 Validate → 6 Report.**
- **No backend, no accounts, no persistence** — documents never leave the browser.
  Deployable as a static site (GitHub Pages / Vercel).

## Screens / views

### Layout — one page, two zones
- **Zone A — persistent pass stepper** (top): six steps, always visible, current step in
  cobalt. Steps carry a summary badge after a run (e.g. "12 observations", "9 applied / 3
  flagged", "pass").
- **Zone B — pass panel**: the content of the active step. Free navigation between steps in
  any order after a run.
- Container: `max-width: 980px`, centered, `padding: 72px 24px 120px`.

### Run lifecycle / stepper states
- **Before a run:** only **Input** is enabled; steps 2–6 dimmed and non-interactive.
- **After a run:** all steps enabled, each with a summary badge; free navigation.
- **On edit:** editing the input **invalidates** the run; steps 2–6 grey out until re-run.

### 1 — Input
Paste or upload source (`.md` / `.txt`), or load a bundled example. Live metrics (chars,
words, sentences, avg words/sentence). Shows the pack in effect
(`concise_scientific_writing · v1.2 · 6 transformations`). Primary **Run pipeline** button.

### 2 — Observe
Read-only source with each observation's evidence highlighted and colored by **safety**.
Sidebar lists observations grouped by rule. Clicking a highlight or a list entry selects and
scrolls to its counterpart.

### 3 — Recommend
Table of recommendations; columns: Rec/Obs, Action, Before → After, Safety. Each row links
back to its observation (jumps to step 2 with it selected). `review_long_sentence` rows are
visually distinct and propose no text change.

### 4 — Transform
Two tabs. **Diff** — original vs. transformed, word-level inline diff, applied changes
colored by safety. **Log** — transformation records; not-applied (`review`) entries shown
separately as "flagged for human review."

### 5 — Validate
Overall status; protected-token check with the token list (URLs, numbers, citations,
bracketed refs); any missing tokens in red; standing caveat that validation is conservative
and evidence-based (does not prove semantic equivalence).

### 6 — Report
Rendered `report.md` — metrics before/after, validation summary, transformation log, final
document. Actions: Copy final document, Download final.md, **Download artifact trail** (zip
of six files, byte-identical to a CLI run's output directory).

## Safety color code
Used consistently across highlights, badges, diffs. **Always paired with a text label —
never color alone.** Must meet WCAG AA contrast.
- **SAFE** — teal (`--accent-teal`). Applied automatically; high-confidence, reversible.
- **LOW RISK** — orange (`--accent-orange`). Applied automatically; worth a glance.
- **REVIEW** — purple (`--accent-purple`). Flagged only, never applied; dashed underline;
  human decides.

## Architecture
Run the existing Python `praxis` package **unchanged in the browser via Pyodide** (CPython
on WebAssembly) so the UI is evidence of what the harness actually does.
- **No TS port** (would be a second implementation that drifts). **No serverless** (rules
  out static hosting, adds a hop + privacy question).
- **Cost:** one-time ~7 MB Pyodide download. Load in background while the user types, cache
  via service worker, show "loading engine" until ready.
- **Engine boundary** — the UI calls one function and gets the whole trail; only this module
  knows Python exists. TS types mirror the dataclasses in `praxis/models.py`:

```ts
interface PraxisResult {
  observations:    Observation[];      // observations.json
  recommendations: Recommendation[];   // recommendations.json
  transformations: Transformation[];   // transformations.json
  validation:      Validation;         // validation.json
  final:           string;             // final.md
  report:          string;             // report.md
  metrics: { before: Metrics; after: Metrics };
}
runPipeline(source: string): Promise<PraxisResult>
```

- **Harness prerequisite** (the only change to the existing package): extract the pipeline
  core from `cli.run` into `praxis.pipeline.run_pipeline(text: str) -> dict` that returns
  the artifacts instead of writing files. The CLI and the UI shim both call it.

## Acceptance checks
1. Pasting the golden example and running produces artifacts byte-identical (JSON/Markdown
   content) to `python -m praxis run` on the same input.
2. Every transformation in step 4 links to a recommendation in step 3 and an observation in
   step 2.
3. A document with no matches runs cleanly: empty observation list, no diff, validation pass.
4. A 50 kB document runs without freezing the UI — pipeline executes in a web worker.
5. The site works offline after first load, via service worker.

## Out of scope for v1
Accept/reject of individual recommendations · pack authoring/selection (view-only, single
pack) · run permalinks (needs URL-encoded docs or storage — revisit privacy first) · LLM
calls (pipeline stays deterministic and auditable).

## Design tokens — DHK Electric Cobalt (light theme only)
Exact values are in `_ds/tokens/*.css`; the essentials:
- **Backgrounds (grey ladder):** `--bg #f5f6fa` (page), `--bg2`, `--bg3` (elevation/hover).
- **Brand accent:** `--accent #2b50e8` (Electric Cobalt), `--accent-hover #1a3bd4`.
- **Semantic accents:** purple = commentary/tools/review; orange = projects/low-risk;
  teal = studies/safe.
- **Border:** hairline `1px` `--border #c8cde0`. **Radius:** `4px` everywhere. **Shadows:**
  none — depth is the grey ladder + hairlines only.
- **Type:** headings + body use the native `system-ui` stack (no webfont, weight 400 min,
  never 300, body line-height 1.75). **DM Mono** (Google Fonts) is reserved strictly for UI
  chrome — tags, dates, nav, code, labels, step numbers — and never body prose. No UI text
  below 11px. Sentence case for prose/headings; UPPERCASE only in mono chrome.
- **Spacing:** 4px-based scale expressed with flex/grid `gap`, never sibling margins.
- **Motion:** `0.15s` on color/background/border; longer expressive easing
  (`cubic-bezier(0.22,1,0.36,1)`, ~1s) only for data reveals. Respect
  `prefers-reduced-motion`.
- **Iconography:** near-iconless. Use Unicode `↗` (external) and `→` (step/flow), the 7px
  brand dot, and ad-hoc thin-stroke inline SVG. No icon library, no emoji.

## Assets
No image assets. The design is type- and rule-driven; the only "imagery" is functional
data-viz drawn in accent colors. Fonts (DM Mono) load from Google Fonts CDN.

## Files in this bundle
- `Praxis UX Spec (standalone).html` — rendered, self-contained spec (open to view).
- `Praxis UX Spec.dc.html` — editable source with exact inline-style values.
- `README.md` — this document (self-sufficient; implementable without the source chat).

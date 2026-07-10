# Handoff: Praxis Viewer — Workflow Layout Fixes

## Overview
Three targeted UX fixes to the Praxis artifact-trail viewer (the 7-step pipeline UI: Input → Observe → Recommend → Transform → Validate → Report → Compare). These address split focus on the Input step, a misordered Report tab set, and a redundant terminal "Compare" step. This is not a new feature — it's a layout/IA correction to an existing flow.

## About the Design Files
The bundled file (`Praxis Viewer.dc.html`) is a **design reference built in HTML** — a working prototype demonstrating the intended layout and behavior, not production code to copy directly. The task is to **recreate this structure in the target codebase's existing environment** (whatever framework/component library the real Praxis viewer is built with) using its established patterns, state management, and styling system — not to ship the HTML as-is.

## Fidelity
**High-fidelity for structure and behavior, illustrative for visuals.** The step order, tab order, control grouping, and interaction rules (locking, invalidation-on-edit, scroll-sync) should be matched exactly. Colors/type follow the "DHK Electric Cobalt" reference system baked into this prototype — restyle to the target app's real design system/tokens; don't port hex values verbatim unless they already match.

## The three changes

### 1. Input step — fix split focus (load controls vs. run action)
**Problem:** "Load"-type controls (upload, load example) sat at the top of the panel while "Run pipeline" sat at the bottom, below a large textarea — forcing the user to look in two places and scroll between them.
**Fix:** Collapse both into a **single toolbar row** at the top of the Input panel: `Upload file` · `Load example ▾` · (spacer) · `Pack: <name> ▾ · <version> · <n> transformations` · `Run pipeline`. The textarea and live metrics (chars/words/sentences/avg) sit below this row. Loading a new example, uploading a file, or changing the pack all mark the current run as stale (see "invalidation" below) exactly like editing the textarea.

### 2. Report step — reorder tabs, output before metrics
**Problem:** Tab order was `Metrics · Validation · Transformation Diff Log · Final Document · Review Prompt` — metrics led, output was buried third-to-last.
**Fix:** Reorder to: **`Final Document → Compare → Validation → Transformation Diff Log → Metrics`**. Rationale: users care about the output first, provenance/trust signals (validation, diff log) next, and metrics last as supporting evidence — not the headline. `Final Document` is the default active tab when Report is opened. (This handoff also drops the "Review Prompt" tab/"Copy review prompt" action as out of scope — confirm with product whether that capability still needs a home elsewhere.)

### 3. Remove step 7 "Compare" as a terminal step; fold it into Report
**Problem:** "Compare" (original vs. final, side-by-side, synced scroll) lived as an isolated 7th pipeline step after Report, implying it was a separate terminal stage rather than a way of looking at the same output.
**Fix:** The pipeline stepper is now **6 steps** (Input, Observe, Recommend, Transform, Validate, Report). The side-by-side before/after compare view — including the Raw/Rendered toggle and proportional synced scrolling between panes — becomes the **"Compare" sub-tab inside Report** (second position, right after Final Document). No functionality is lost; it's a reclassification from "step" to "lens on the output."

## Screens / Views

### Stepper nav (persistent, all steps)
- Layout: flex row, 6 cells, `gap: 6px`, each cell `flex: 1, min-width: 130px`, wraps on narrow viewports.
- Each cell: step number + label (e.g. "1 Input"), and a small mono badge below showing a live summary (e.g. "130 words", "8 observations", "6 applied / 2 flagged", "pass", "ready").
- States:
  - **Active step**: filled accent background, white text.
  - **Unlocked, inactive**: neutral surface, bordered, normal text, pointer cursor.
  - **Locked** (steps 2–6 before first run, or after an edit invalidates the run): 50% opacity, `not-allowed` cursor, not clickable.
- Step 1 is always clickable regardless of run state.

### 1. Input
- Toolbar row (single row, `display:flex; gap:12px; flex-wrap:wrap; align-items:center`):
  - `Upload file` button (ghost variant) — opens a hidden file input (`.md`/`.txt`), reads the file as text into the source.
  - `Load example` select — a dropdown of named examples; selecting one replaces the source text.
  - Spacer (`flex:1`).
  - `Pack` select — dropdown of available transformation packs; shows `<pack name> · <version> · <n> transformations` next to it.
  - `Run pipeline` button (primary variant, accent fill) — runs the pipeline once against current source + pack, then jumps to step 2.
- Below the toolbar: a stale-run notice (shown only when the run is invalidated) — "Source changed since the last run — steps 2–6 are stale. Run again to refresh them."
- Below that: the source textarea (large, monospace, min-height ~320px, resizable vertically).
- Below the textarea: a live metrics row — chars / words / sentences / avg words per sentence — recomputed on every keystroke regardless of run state.

### 2. Observe
- Two-column layout (`1.6fr / 1fr`): left = read-only source text with each detected span highlighted inline (color-coded by safety: teal/safe, orange/low-risk, no-fill dashed-purple/review); right = scrollable list of observation cards (id, safety tag, quoted text, rule description), same order as the highlights.

### 3. Recommend
- A table: `Obs id · Rule · Before → after · Safety`. Review-category rows render on a faint purple tint and show "no text change proposed" instead of an after-value — visually distinct from applied rows.

### 4. Transform
- Inline diff view of the full source: applied changes show strikethrough-original + colored-replacement; review-flagged spans show the original text with a dashed purple underline (unchanged). A summary line below counts "N applied" / "N flagged for review."

### 5. Validate
- A status banner (colored dot + mono status label + one-line note) — pass/fail based on whether all "protected tokens" (numbers, %, $ amounts, URLs, emails, year ranges) detected in the source still appear in the final text.
- A chip list of every protected token found.
- A fixed caveat line: "validation is conservative and evidence-based. It does not prove semantic equivalence."

### 6. Report
- Action row: `Copy final document` (ghost), `Download final.md` (ghost), `Download artifact trail` (primary) — the last downloads a single JSON bundle of source, observations, final text, validation, and before/after metrics (stand-in for the real six-file artifact trail zip).
- Tab row (order matters — see fix #2 above): **Final Document · Compare · Validation · Transformation Diff Log · Metrics**. Active tab = accent-colored text + 2px accent underline.
  - **Final Document**: rendered markdown-like view of the transformed document (headings, bold job-title lines, bullets, paragraphs).
  - **Compare**: Raw/Rendered toggle (small segmented control), then two side-by-side scrollable panes (Original · Final), each labeled with its word count. Scrolling either pane proportionally scrolls the other (ratio-based, not 1:1 pixel, since the two documents may differ in length).
  - **Validation**: same status banner + token chips as step 5, reused verbatim.
  - **Transformation Diff Log**: table of every observation/recommendation with its applied/flagged status — same underlying data as step 3's table, formatted as a log.
  - **Metrics**: a 3-column table (Metric · Before · After) — Characters, Words, Sentences, Avg sentence words.

## Interactions & Behavior
- **Run lifecycle:**
  - Before any run: only step 1 is enabled; steps 2–6 are locked/dimmed.
  - After a run: all steps unlock, each shows a live summary badge; free navigation in any order.
  - **On edit** (textarea change, new example loaded, file uploaded, or pack changed) *after* a run exists: the run is marked stale — steps 2–6 re-lock, the stale-run notice appears, and the stepper forces the user back toward step 1 conceptually (nav to 2–6 is blocked until they re-run).
- **Run pipeline**: synchronous, deterministic — no loading state needed at this fidelity (real backend/engine call may need one).
- **Compare scroll sync**: on scroll in either pane, compute `scrollTop / (scrollHeight - clientHeight)` for the source pane and apply that ratio to the destination pane's equivalent range. Guard against feedback loops with a sync-in-progress flag.
- **Copy final document**: clipboard write of the plain final text.
- **Downloads**: client-side Blob + object URL, no server round-trip required.

## State Management
Minimum state needed:
- `step` (1–6, current active stepper position)
- `source` (string, current document text)
- `packKey` (selected transformation pack)
- `hasRun` (boolean — has the pipeline executed at least once)
- `isEdited` (boolean — has source/pack changed since the last run)
- `result` (nullable — everything produced by the last run: observations/recommendations/transformations list, final text, before/after metrics, validation result)
- `reportTab` (which Report sub-tab is active; default `'final'`)
- `compareView` (`'raw' | 'rendered'`, Compare sub-tab's toggle)

State transitions:
- `runPipeline()` → sets `hasRun:true, isEdited:false, step:2`, computes `result`.
- Any source/pack/example/upload change → `isEdited: hasRun` (only flips true if a run already exists).
- `setStep(n)` → only applies if `n === 1` or `(hasRun && !isEdited)`.

## Design Tokens
This prototype uses the DHK "Electric Cobalt" reference palette — replace with the target app's real tokens, but the semantic mapping should carry over:
- Background ladder: page `#f5f6fa`, elevated surface `#eceef5`, hover/card `#e0e3f0`.
- Borders: default `#c8cde0`, subtle `#d8dbeb`.
- Text: heading/strong `#0d0f1a`, body `#2a2d42`, muted/dim `#5a5d78`.
- Brand accent: `#2b50e8` (hover `#1a3bd4`) — active step, primary buttons, active tab underline.
- Semantic safety colors: teal `#0ea5b0` = safe/applied, orange `#e05c2a` = low-risk, purple `#8b2adc` = review/flagged (never auto-applied).
- Radius: 4px everywhere. No shadows — elevation via the background ladder + hairline borders only.
- Type: system UI sans for body/headings; mono (DM Mono in this prototype) for all UI chrome — tags, labels, step badges, metrics.

## Assets
No image/icon assets — the design is entirely type- and rule-driven (hairlines, flat color, mono labels). No icon library is used.

## Files
- `Praxis Viewer.dc.html` — the full working prototype (single self-contained reference file; open directly in a browser).

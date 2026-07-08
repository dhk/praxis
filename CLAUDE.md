# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

praxis is a deterministic, stdlib-only Python harness that rewrites documents through an auditable pass pipeline (`Parse -> Observe -> Recommend -> Transform -> Validate -> Report`), plus a static web viewer for the resulting artifact trail. Every transformation must trace back to an observation; the CLI and the browser UI share one Python implementation — there is no second (e.g. TypeScript) port of the rules anywhere.

## Commands

```bash
# Run the pipeline (writes six JSON/Markdown files to --out)
python -m praxis run examples/concise_scientific_writing/input.md --out artifacts/demo
python -m praxis run examples/resume/input.md --pack resume_writing --out artifacts/demo --prompt  # also writes prompt.md

# Tests (no network, <1s)
python -m pytest
python -m pytest tests/test_harness.py::test_resume_writing_pack   # single test

# Build the web viewer into dist/ (vendors Pyodide on first run, then cached in .cache/)
bash scripts/build_site.sh
python -m http.server 8000 -d dist   # serve it locally
```

There is no lint/typecheck configured. `pyproject.toml` has no runtime dependencies (stdlib only); `pytest` is the sole test dependency.

## Architecture

### The Python harness (`praxis/`)

`pipeline.py`'s `run_pipeline(text, pack_id) -> dict` is the **one entry point** both the CLI (`cli.py`) and the browser worker call — it returns a dict whose keys are exactly the artifact files (`observations`, `recommendations`, `transformations`, `validation`, `final`, `report`, `metrics`, `pack`), JSON-serializable as-is. `cli.run()` just writes that dict's values to disk; it contains no pipeline logic of its own. When changing the pipeline, change `pipeline.py`/`rules.py`, never duplicate logic in `cli.py`.

Data flows through fixed dataclasses in `models.py` (`Observation` → `Recommendation` → `Transformation`), each carrying a `safety` tier:
- **`safe`** — applied automatically, reversible, no semantic risk (e.g. deleting filler phrases).
- **`low_risk`** — applied automatically, worth a glance (e.g. phrase substitutions).
- **`review`** — never applied; only ever flagged. A human decides.

`rules.py` has exactly two entry points, `observe`/`recommend`/`transform`, generic over whatever `Pack` they're given — packs are pure data, not code. **Adding a new pack means adding a `Pack` to `packs.py`, not touching `rules.py`.** A `Pack` has:
- `phrase_rules`: regex → replacement, applied automatically (`safe`/`low_risk`).
- `flag_rules`: observation-only, never edit anything, always `safety="review"`. Either `kind="long_sentence"` (flags sentences over a word threshold) or a regex `pattern` matched with `IGNORECASE | MULTILINE`.

Three packs exist today: `concise_scientific_writing` (default), `claude_skill_authoring` (rules grounded in the [skill-map](https://github.com/dhk/skill-map) corpus study — see the comment above its definition in `packs.py`), and `resume_writing`. Each pack has a matching `packs/<id>/pack.yaml` (human-readable metadata mirror, not read by the code — keep it in sync by hand) and a bundled example under `examples/`.

`validation.py`'s `protected_tokens()` is the harness's central safety guarantee: URLs, numbers/percentages, bracketed refs, and parenthetical citation-years must appear byte-identical in the final document, regardless of pack. This is what lets `resume_writing` rewrite prose while proving dates/metrics/contact-info were never touched.

`handoff.py`'s `render_prompt(result)` packages a run's `review`-flagged items (only) into a self-contained Markdown prompt meant to be pasted into an LLM by a human — the pipeline itself never calls one. Returns `""` when nothing was flagged. Reachable via CLI `--prompt` or the viewer's Report → Review Prompt tab.

### The web viewer (`web/`)

Static site, no build framework (no bundler, no npm dependencies) — `scripts/build_site.sh` just copies `web/*`, the `praxis/*.py` source files, pack YAML, and bundled examples into `dist/`, and vendors the Pyodide runtime (fetched from the npm registry, cached in `.cache/`) so the deployed site is fully same-origin with no third-party script origins at runtime.

The engine boundary is `web/src/engine.js` + `web/src/worker.js`: the UI calls `runPipeline(source, packId)` and awaits the full trail; **only `worker.js` knows Python exists**. The worker loads Pyodide, writes the `praxis/*.py` source into its virtual filesystem, and imports the real package unchanged — so the browser and CLI are provably running identical logic (verified by a browser-vs-CLI byte-identical check in the e2e suite; see below). The worker also computes the word-level diff (Python `difflib`) and the artifact-trail zip (Python `zipfile`) — never reimplemented in JS.

`web/src/main.js` is a single-file, dependency-free UI: one `state` object, one `render()` dispatcher keyed on `state.step` (1–7), no framework. Each pass panel (`renderInput`, `renderObserve`, ... `renderCompare`) fully replaces `panelEl.innerHTML` and re-attaches its own listeners — panels never diff or persist DOM between renders, only `state` persists. The six passes mirror the harness's stages 1:1; step 7 (Compare) is viewer-only, showing original vs. final with scroll-sync.

`web/sw.js` (service worker) uses **stale-while-revalidate**, not cache-first: every request is answered from cache immediately, but a network fetch always runs in the background and refreshes the cache. This matters — a pure cache-first strategy (what shipped originally) meant a returning visitor could get stuck on an old deploy indefinitely, since the service worker only re-precaches when its own file's bytes change. If you ever touch `sw.js`, bump the `CACHE` version string.

`web/src/markdown.js` is a deliberately minimal Markdown renderer (headings, paragraphs, tables, fenced code, inline emphasis/links) — no lists, no blockquotes. Used for `report.md` and the Compare "Rendered" view. The Report panel's tab splitter (`splitReportSections` in `main.js`) only splits on the four exact section titles `report.py` emits (`Metrics`, `Validation`, `Transformation Diff Log`, `Final Document`) — **not** on any `##`, because the embedded final document can itself contain user H2 headings (a resume's `## Experience`) that must stay inside the Final Document tab rather than being mistaken for a new report section.

### Deploy

`.github/workflows/deploy-pages.yml` builds and deploys to GitHub Pages on every push to `main`. **GitHub Pages Source must be set to "GitHub Actions"** in repo settings (Settings → Pages) — if it's ever on "Deploy from a branch" instead, GitHub silently runs its own separate `pages-build-deployment` workflow that Jekyll-renders `README.md` as the site, and this project's workflow will keep reporting success while something else entirely is being served. `vercel.json` supports deploying the same build to Vercel instead.

`.github/workflows/lock-merged-branch.yml` locks a PR's branch read-only immediately after merge (so a stray later push fails loudly instead of landing silently unreachable commits), but only runs if a `BRANCH_ADMIN_TOKEN` repo secret is configured (fine-grained PAT, Administration: read/write) — it no-ops cleanly otherwise.

## Testing conventions

`tests/test_harness.py` treats `python -m praxis run` as ground truth: `run_pipeline()`'s in-memory result must always match the files a CLI run writes byte-for-byte (`test_run_pipeline_matches_cli_artifacts`). Any browser-side change should preserve this: the standing bar is that the deployed viewer's output is byte-identical to the CLI's, verified via headless-Chromium end-to-end tests (not checked into the repo; run ad hoc against `dist/` with Playwright when changing `web/`).

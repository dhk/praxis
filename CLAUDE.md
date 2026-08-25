# CLAUDE.md

**Type:** guide · [document types](AGENTS.md#documents)

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Engineering rules, product invariants, and working method live in
[`AGENTS.md`](AGENTS.md) — read it first. Product direction is
[`VISION.md`](VISION.md) and [`ROADMAP.md`](ROADMAP.md).

Before writing any document, read [`AGENTS.md` § Documents](AGENTS.md#documents):
every document is one of eight enumerated types and declares which. Both a
document and a type have to earn their keep — the test for a document is
whether someone would decide worse without it, and the test for a new type
is whether it can name what goes wrong in its absence.

## What this is

praxis is a deterministic, stdlib-only Python instrument for auditable written communication. It has two layers over one engine, and neither generates prose:

- **The transformation harness** rewrites documents through an auditable pass pipeline (`Parse -> Observe -> Recommend -> Transform -> Validate -> Report`), plus a static web viewer for the resulting artifact trail. Every transformation must trace back to an observation; the CLI and the browser UI share one Python implementation — there is no second (e.g. TypeScript) port of the rules anywhere.
- **The design layer** (RFC-0003, RFC-0004) decides what a message should do for a given reader at a given level of risk, asks only the questions that change that decision, locates surgical changes in a draft, and audits prose written elsewhere against constraints declared in advance. Its interface is an MCP server; prose comes from the client's model, never from praxis.

## Commands

```bash
# Design layer: analyse a communication situation, write an HTML artifact
python -m praxis design draft.md --set stakes=high --set intent=request --set time_available=low
python -m praxis design draft.md --transform --set intent=request   # located changes, not a critique
python -m praxis design draft.md --transform --voice past-emails.md # which habits the draft keeps
python -m praxis design --set intent=repair            # plan before writing; no draft needed
python -m praxis design draft.md --commission prompt.md  # Perkins: the prompt this situation commissions
python -m praxis corpus                                 # score the detectors against corpus/
python -m praxis corpus --prompt --detector escalation   # commission corpus work elsewhere
python -m praxis serve                                  # browse saved sessions on 127.0.0.1:8765
python -m praxis mcp                                    # MCP server on stdio (needs the `mcp` extra)

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

There is no lint/typecheck configured. `pyproject.toml` has no runtime dependencies: `praxis/*.py` is stdlib-only because `scripts/build_site.sh` copies that glob into Pyodide unchanged. `pytest` is the test dependency; `mcp` is an optional extra used only by `praxis/mcp/`, which the non-recursive glob never copies into the browser bundle.

## Architecture

Full system view, component table, implementation notes (deploy gotchas,
service-worker caching, report-panel tab splitting), artifact contract,
and vocabulary: [docs/architecture.md](docs/architecture.md). The
invariants below are the ones most likely to be broken by an edit that
looks locally correct:

- `pipeline.py`'s `run_pipeline(text, pack_id) -> dict` is the **one
  entry point** both the CLI and the browser worker call. `cli.py` only
  writes its return value to disk — no pipeline logic of its own. Change
  `pipeline.py`/`rules.py`, never duplicate logic in `cli.py`.
- Data flows through fixed dataclasses in `models.py` (`Observation` →
  `Recommendation` → `Transformation`), each carrying a `safety` tier:
  `safe`/`low_risk` apply automatically, `review` never does — a human
  decides. `rules.py` is generic over whatever `Pack` it's given —
  **adding a new pack means adding a `Pack` to `packs.py`, not touching
  `rules.py`.**
- `validation.py`'s `protected_tokens()` is the harness's central safety
  guarantee: URLs, numbers/percentages, bracketed refs, and parenthetical
  citation-years must appear byte-identical in the final document,
  regardless of pack.
- **Only `web/src/worker.js` knows Python exists.** It loads Pyodide,
  writes the `praxis/*.py` source into its virtual filesystem, and
  imports the real package unchanged — the browser and CLI are provably
  running identical logic (verified by a browser-vs-CLI byte-identical
  check in the e2e suite — see Testing conventions below).

Four packs exist today: `concise_scientific_writing` (default),
`claude_skill_authoring` (rules grounded in the
[skill-map](https://github.com/dhk/skill-map) corpus study),
`resume_writing`, and `controlled_language`. Each has a matching
`packs/<id>/pack.yaml` (kept in sync by hand, not read by the code) and a
bundled example under `examples/`.

A pack is the **language** mechanism — which words, how long a sentence,
who is named — where `strategy.py`'s structures are the **order**
mechanism. `controlled_language` is the first pack named after an
external standard (ASD-STE100), and it is titled "STE100-derived" rather
than "STE100" on purpose: it implements the transferable rules and not
the Dictionary of approved words, which is the core of the standard. A
pack that borrows a standard's name owes the reader the part it does not
implement, in the title, where every artifact carries it.

`handoff.py`'s `render_prompt(result)` packages a run's `review`-flagged
items into a self-contained Markdown prompt meant to be pasted into an
LLM by a human — the pipeline itself never calls one. Reachable via CLI
`--prompt` or the viewer's Report → Review Prompt tab.

## Testing conventions

`tests/test_harness.py` treats `python -m praxis run` as ground truth: `run_pipeline()`'s in-memory result must always match the files a CLI run writes byte-for-byte (`test_run_pipeline_matches_cli_artifacts`). Any browser-side change should preserve this: the standing bar is that the deployed viewer's output is byte-identical to the CLI's, verified via headless-Chromium end-to-end tests (not checked into the repo; run ad hoc against `dist/` with Playwright when changing `web/`).

## Design layer invariants

- **`design.py`'s `design(draft, contract, variants) -> dict` is the
  second entry point**, beside `run_pipeline`. The MCP server, the CLI,
  and the HTML renderer all consume its result and none of them
  recomputes anything.
- **The engine never writes prose and never calls a model.** Two tests
  enforce it (`test_the_engine_never_reaches_a_model_or_the_network`,
  and the stdlib-only bundle check). The MCP server's job is to make the
  *client's* model useful, which is why tool descriptions and
  `next_step` are product surface, not comments.
- **Rules are data in both layers.** A structure is a `Structure` in
  `strategy.py`; a shade is a `Shade` in `shading.py`; a contract field
  is a `Field` in `contract.py`; a detector is a compiled pattern in
  `signals.py`. If adding one domain rule requires editing the generic
  machinery, the table is the wrong shape.
- **`strategy.material_questions` decides what to ask by perturbation**,
  not by a hand-maintained list of important fields: walk an unknown
  field across its closed domain, re-run the recommendation, and ask only
  if the outcomes split. Both directions are enforced by test. This is
  the layer's central mechanism — do not replace it with a heuristic.
- **Nothing derived is persisted.** Sessions store the contract, the
  draft, and the variants; strategy and scorecards are recomputed on
  every read so a rule change never leaves a stale verdict in a file.
- **Detectors are conservative.** A miss reports `unknown`, never
  `absent`. `signals.py` is recall-oriented by design — but recall is not
  a licence for false positives that mask real findings (see
  `test_a_polite_request_is_not_an_uncertainty_marker`).
- **Shading has two references and they must not be merged.**
  `shading.check(source, variant, …, compare_to=…)` takes invariants from
  `source` (the writer's draft, so an alternative cannot lose a figure
  just because the recommendation did) and measures the difference map
  against `compare_to` (the recommended version, because that is the
  comparison the writer is making). `design._review` wires this up and
  sorts the recommendation first; every difference map carries
  `compared_to` so a delta is never reported without its reference.
- **Answer first, in every interface.** `brief.py` renders a design
  result at four depths and the default is `answer`: the shape and what
  is wrong, two or three sentences, no reasoning. `design_detail` and the
  CLI's `--why` are the way down. Adding a field to the default MCP reply
  needs an argument for why the writer cannot proceed without it —
  `test_a_reply_is_the_answer_not_the_apparatus` fails otherwise. Offer
  one question, never a list, and report `questions_outstanding` (the
  true total) rather than the capped display list.
- **Transform has to be asked for.** `mode="auto"` picks between compose
  and evaluate; it never selects transform. "What is wrong" and "what to
  change" are different questions, and answering the second unprompted is
  the rewriting reflex the layer exists to avoid.
- **Every gap produces an edit, folds into one, or is named.** A reported
  gap with no located change is the failure transform mode exists to
  avoid, so `folded_into` and `no_edit_for` are both in the result and
  both are checked by test. `FOLDS_INTO` in `transform.py` is the data.
- **A protected span blocks an edit rather than dropping it.** The
  writer's constraint and praxis's advice can conflict; praxis reports
  the conflict and refuses to choose.
- **Protected phrases match across whitespace** (`spans.contains_phrase`).
  A writer types a phrase with spaces and a hard-wrapped draft contains a
  newline; exact matching missed it *silently*, so the writer believed
  something was protected that was not.
- **Voice reports habits, never authorship.** Function-word similarity
  was built and measured out: same-author and different-author pairs
  overlap at email lengths (the table is in RFC-0004). `voice.compare`
  never returns a `gap` — a dropped habit may be exactly what the rewrite
  was for.
- **A detector's claim is data, not a comment** (`signals.MEANINGS`). The
  corpus measures whether a pattern lives up to its stated meaning, so the
  meaning has to be somewhere a person can read without the regex.
- **praxis packages prompts and never sends them.** `handoff.render_prompt`
  does it for a transformation run, `handoff.corpus_prompt` for the
  detector corpus. Both hand a person everything a model would need and
  stop there; adding a call would end the property the whole engine is
  built on.
- **Corpus examples carry provenance and `generated` never counts alone.**
  The detectors were written by a model, so a corpus written by one shares
  their blind spots. `praxis.measure.TRUSTED` is the headline set.

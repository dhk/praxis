# AGENTS.md

## Purpose

This repository contains **praxis**, an auditable communication-design
instrument: a deterministic Python engine, a CLI, a static browser
viewer, and an MCP server.

Praxis analyses, transforms, and evaluates written communication. It
**does not generate prose**, and no change may give it that ability.
Where prose is needed it comes from the model the user is already
talking to, and praxis audits the result.

These instructions apply to all work in this repository unless a more
specific nested `AGENTS.md` overrides them.

## Product invariants

1. **The engine never writes prose.**
2. **Evidence before assertion** — every finding shows what it saw.
3. **Inference is labelled, never promoted to fact.**
4. **Content, evidence, voice, and risk integrity are separate constraints.**
5. **Warmer never means less truthful; shorter never means the caveat is gone.**
6. **Ask only what changes the answer.**
7. **One recommended version; alternatives only against a real tradeoff.**
8. **No opaque scores.**
9. **Determinism wherever determinism is possible.**
10. **Artifacts at every step, and they must be visual where comparison is the point.**
11. **Usable vertical slices** — every wave ends in something a writer can use.
12. **Local-first**: no accounts, no backend, no document upload, no telemetry.
13. **Answer first, detail on request** — including in praxis's own interfaces.

This list is mirrored in [`VISION.md`](VISION.md) — same items, same
order; change both together.

## Working method

Before changing code:

1. Read this file.
2. Read [`README.md`](README.md), [`VISION.md`](VISION.md),
   [`ROADMAP.md`](ROADMAP.md), [`docs/architecture.md`](docs/architecture.md),
   and the relevant RFC under [`spec/`](spec/).
3. Inspect nearby code and its tests.
4. Restate the writer-visible outcome.
5. Identify the smallest complete vertical slice.
6. Make assumptions explicit.

Then: `understand → design → implement → test → review → document`.

Do not make unrelated cleanup changes.

## Architecture

Two layers over one engine. Both are pure functions from inputs to a
JSON-serialisable result; persistence and presentation belong to the
interfaces.

```text
praxis/
  pipeline.py    run_pipeline(text, pack_id)   — transformation harness
  design.py      design(draft, contract, …)    — communication design layer
  mcp/           host-side surfaces (MCP server, local viewer)
```

Four boundaries are load-bearing. Breaking any of them is an
architecture change and must be argued for in an RFC, not slipped into
a feature commit.

- **`praxis/*.py` is stdlib-only.** `scripts/build_site.sh` copies that
  glob into Pyodide unchanged, so a third-party import breaks the
  browser viewer — at runtime, in a browser, not in CI. Host-side code
  with dependencies goes in `praxis/mcp/`, which the non-recursive glob
  never copies. Guarded by
  `test_the_browser_bundle_stays_stdlib_only`.
- **`run_pipeline` and `design` are the only entry points.** The CLI,
  the worker, the MCP server, and the renderer consume their results;
  none of them recomputes anything. A second opinion about the same
  question is how two interfaces start disagreeing.
- **Nothing derived is persisted.** Sessions store the contract, the
  draft, and the variants. Strategy, questions, and scorecards are
  recomputed on every read, so a rule change never leaves a stale
  verdict sitting in a file.
- **The engine reaches no network and no model.** Guarded by
  `test_the_engine_never_reaches_a_model_or_the_network`.

## Rules are data

Both layers are generic over their rule tables, and this is the main
extension point:

| To add | Edit | Never edit |
|---|---|---|
| A transformation pack | `packs.py` (a `Pack`) | `rules.py` |
| A contract field | `contract.py` (a `Field`) | the strategy scorer |
| A structure | `strategy.py` (a `Structure`) | the scoring loop |
| A shade | `shading.py` (a `Shade`) | `check` / `difference_map` |
| A detector | `signals.py` (a compiled pattern) | its callers |

If a change requires editing the generic machinery to add one domain
rule, the table is the wrong shape — fix the table.

## Judgment, and where it is allowed to live

Praxis makes judgment calls. It must make them in **inspectable data**,
never in a prompt and never in a model call.

- A recommendation must be able to say which contract values produced it
  (`because`) and what came second (`runner_up`).
- A question must be asked only because its answers demonstrably split
  the strategy. This is decidable by perturbation and is checked by
  `test_every_asked_question_actually_changes_the_strategy`; do not
  replace it with a hand-maintained list of "important" fields.
- Detectors are recall-oriented and conservative. A miss reports
  `unknown`, never `absent`. Do not tune a detector toward confidence it
  has not earned.

## The interfaces obey the advice

Praxis argues for leading with the conclusion, asking only what changes
it, and letting the reader drill in. An interface of its own that opens
with a wall of structure is advice the tool ignores, and it was shipped
that way once: `design_open` returned every dimension, the runner-up, the
contract and the invariants on every call — about 900 tokens to say
something that fits in a sentence.

So every reply, in every interface, carries four things and stops: the
**answer**, the **progress**, **one question** if one is worth asking,
and where to drill in. `brief.py` renders all four depths;
`design_detail` and the CLI's `--why` are the way down. Adding a field to
the default reply needs an argument for why the writer cannot proceed
without it. `test_a_reply_is_the_answer_not_the_apparatus` is the guard.

Two related rules:

- **Offer one question, never a list.** A writer who has had enough
  should not have to decline three things.
- **Report the true outstanding count, not the displayed one.** The list
  is capped at three; the count is not. Progress that never moves reads
  as no progress, and the count reaching zero — "nothing else you could
  tell me would change it" — is a completion signal almost nothing else
  can give.

## Model use

Praxis calls no model. Ever.

The MCP server's job is to make the *client's* model useful: it supplies
the strategy, the constraints, and the audit, and asks the client for
prose. When editing `praxis/mcp/server.py`, remember that tool
descriptions and `next_step` are the only instructions that model gets —
they are product surface, not comments.

Never use a model for: arithmetic, structure selection, invariant
checking, validation, or anything a table can decide.

## Standard commands

```bash
python -m pip install -e ".[test,mcp]"
python -m pytest

python -m praxis run examples/concise_scientific_writing/input.md --out artifacts/demo
python -m praxis design examples/resume/input.md --set stakes=high --set intent=demonstrate
python -m praxis serve          # browse saved sessions at 127.0.0.1:8765
python -m praxis mcp            # MCP server on stdio

bash scripts/build_site.sh && python -m http.server 8000 -d dist
```

Do not claim checks passed unless they were executed.

## Validating a change

Always run `python -m pytest`. Then add what the change requires:

| Change | Required validation |
|---|---|
| Engine, rules, packs, validation, metrics, reports | Regression tests; the CLI smoke run; inspect the artifacts. Keep `packs/*/pack.yaml` in sync with `packs.py`. |
| Contract fields, structures, shades, detectors | Tests for the new row; re-run the question-materiality and invariant tests; check a rendered page in both themes. |
| Artifact names, shapes, or serialisation | Verify the six CLI files and the browser zip stay byte-identical for the same source and pack. |
| Renderer | Render a session, open it, and check both light and dark; confirm no `<script>` and no external URL appears. |
| MCP surface | Exercise the full loop (`design_open → design_update → design_shade → design_render`) and read the tool descriptions as a client model would. |
| Viewer or browser bridge | Build the site, serve it, and exercise input, pack selection, inspection, and download. |
| Documentation | Run every command the edited text tells a reader to run. |

## Prohibited without an RFC

- Adding a model provider, API key, or network call to the engine.
- Generating prose anywhere in this repository.
- Adding a runtime dependency to `praxis/*.py`.
- Duplicating engine logic in JavaScript.
- Emitting a single overall quality score.
- Raising `MAX_ALTERNATIVES` above three.
- Auto-applying anything marked `review`, or auto-accepting a variant
  that failed its invariant check.

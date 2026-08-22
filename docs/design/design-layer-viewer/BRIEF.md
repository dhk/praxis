# Design requirement: the design layer in the browser viewer

**For:** a UI spec. **Status:** requirement, not a spec.
**Deferred from:** wave 2 ([ROADMAP.md](../../../ROADMAP.md)).

## The one-sentence job

A writer pastes a message into a browser page and finds out what it
needs to do for its reader, what it is missing, and — if they ask —
exactly what to change and where. Nothing leaves their machine.

## What already exists

praxis is a Python engine that runs **unchanged in the browser** under
Pyodide. The viewer at `web/` already does this for the transformation
harness: a dependency-free single-file UI (`web/src/main.js`, 656 lines,
no framework, no build step) driving a web worker that imports the real
Python package.

The design layer's modules already ship in that bundle. Nothing needs
porting. This is a UI that calls one function and renders its result.

**The function:** `design(draft, contract, variants, mode) -> dict`.
Everything below comes out of that one call.

## What the writer is doing

Three modes, and the design has to make the difference obvious because
they answer different questions:

| Mode | The writer's question | Needs a draft? |
|---|---|---|
| **Compose** | "What shape should this be?" | No |
| **Evaluate** | "Is this ready to send?" | Yes |
| **Transform** | "What should I change, and where?" | Yes. **Must be explicitly chosen** |

Transform is never entered automatically. "What is wrong" and "what to
change" are different questions and the product exists partly to stop
tools answering the second unprompted.

## What must be on screen

Grouped by what it answers, not by the data structure it comes from.

1. **The answer.** The recommended shape, and what is wrong. Two or three
   sentences. This is the whole page until the writer asks for more.
2. **Progress.** How much would still change the answer — and, more
   usefully, when *nothing* would. "Nothing else you could tell me would
   change it" is a state worth designing for; almost no tool can say it.
3. **One question at a time.** Never a list, never a form. Each question
   shows what the possible answers decide between. The writer may stop at
   any point.
4. **The contract.** Around 21 fields in seven groups, each marked
   **stated** (the writer said so) or **inferred** (praxis guessed).
   Guesses must be visibly different from facts and must be editable.
5. **The scorecard.** Ten dimensions, each `pass` / `gap` / `unknown`
   with evidence attached. `unknown` is used often and on purpose — it
   must not read as failure or as "not yet loaded". There is deliberately
   **no overall score**.
6. **Located changes** (transform only). Each carries a kind — insert,
   revise, move, cut — a character offset or span into the draft, and an
   instruction. Some are marked **blocked** because they collide with
   content the writer protected.
7. **Versions side by side** (when the writer has written alternatives).
   At most two alternatives, each with a difference map naming what
   changed *against the recommended version*, what was deliberately held,
   and which of the writer's habits moved.

## The design problems worth solving

These are the parts the current HTML renderer does adequately and a real
design could do well:

- **Located changes are positions in a document.** They are currently a
  list with numbers in it. A writer wants to see them *in* their draft.
- **Progressive disclosure without a maze.** Answer first, then reasoning,
  findings, contract, edits — four depths that must feel like one page
  rather than four screens.
- **Protected content and blocked edits.** A conflict between the
  writer's own constraint and praxis's advice. praxis refuses to resolve
  it; the UI has to make the tension legible without alarming.
- **`unknown` as a first-class state.** Neither good nor bad nor pending.
- **The empty state.** A writer arriving with nothing. Compose mode has a
  real answer before a word is written, and the page should show that
  rather than an upload box.

## Hard constraints

Non-negotiable, and each has a reason:

- **No build step, no framework, no dependencies.** The existing viewer
  is plain ES modules served as files. Match it.
- **No network at runtime.** No CDN, no analytics, no web fonts. The
  writer's draft never leaves the browser and the page must work offline.
  This is a privacy guarantee, not a preference.
- **Theme-aware.** Light and dark, both designed, driven by tokens.
- **The engine is the only source of truth.** The UI renders what
  `design()` returns and computes nothing itself. If a number needs to
  appear, the engine must already produce it.
- **Nothing derived is stored.** Reload recomputes.
- **Answer first.** Adding anything to the default view needs an argument
  for why the writer cannot proceed without it.

## Out of scope

Accounts, sharing, storage, collaboration, and any server. praxis has no
backend by design.

## Existing reference

`praxis/render.py` produces a self-contained HTML page with all of this
on it. It is competent and deliberately plain — a starting point to react
to, not a design to refine. `python -m praxis design examples/decision_request/input.md
--transform --set intent=request --set stakes=high` writes one.

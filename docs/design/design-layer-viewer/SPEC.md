# Design Layer Viewer — implementation spec

**Type:** requirement · [document types](../../../AGENTS.md#documents)

**For:** whoever builds the browser surface. **Companion to:**
[`BRIEF.md`](BRIEF.md), which states what the writer needs; this states how
the surface delivers it. Product decisions behind both:
[RFC-0003](../../../spec/RFC-0003-contextual-communication-design.md),
[RFC-0004](../../../spec/RFC-0004-transform-and-voice.md).

**Provenance:** authored in a Claude Design project and carried into the
repository unchanged. Its reference implementation, `Design Layer Viewer.dc.html`,
lives in that project and is **not** in this repo — where this document and
that file disagree, the reference file wins, so anyone implementing from here
should open it too. §12 is the only repository-side addition.

---

## 1. What this surface is

A viewer for how a critique engine ("praxis") reads a piece of writing. It answers one
question at the top, exposes four increasing depths of reasoning below it, and — only when
the user asks — locates the specific changes it would make, inline in their own draft.

Two hard product rules drive the whole layout:

1. **The answer comes first, the reasoning is opt-in.** Depth 01–03 are collapsed by
   default. The user should be able to leave after reading two sentences.
2. **Evaluate and Transform are different acts.** "What is wrong" is given freely.
   "What to change" rewrites the user's words, so it sits behind an explicit gate
   (depth 04) and is never auto-applied.

Nothing is ever mutated on the user's behalf. The transform view *locates* changes; the
user makes them.

---

## 2. Stages

One linear state machine, `stage`:

| Stage | Trigger | What is on screen |
| --- | --- | --- |
| `empty` | initial | Compose view: the answer-in-advance, a stated/unknown counter, a draft textarea |
| `evaluated` | Evaluate this draft / Load an example | The answer, the four-depth map, the question card, the transform gate |
| `transformed` | "Show me the changes" | Everything above, plus the located-changes section |

`Start over` returns to `empty` and clears the draft, question index and selection.
The header shows the stage as `Compose` / `Evaluate` / `Transform`.

Note that `evaluated` content stays mounted in `transformed` — Transform is additive, not
a replacement screen. The user can scroll back up to the answer at any time.

---

## 3. Layout

Single column, centred. Two widths, used consistently:

- **Reading column — 720–780px.** The answer, depth 01 prose, the question card, the
  transform gate. Anything that is sentences.
- **Wide column — 1080px.** The page frame, the depth 02 scorecard grid, the depth 03
  contract grid, the located-changes two-pane.

Page padding is `24px` horizontal. Vertical rhythm between major sections is `64px`
(`52px` between the answer and the depth map, `72px` before the transform sections).
All spacing via flex/grid `gap` or section padding — never sibling margins.

The header is sticky, `z-index: 20`, `background: var(--header-bg)` with
`backdrop-filter: blur(8px)` and a bottom hairline.

### 3.1 Located-changes two-pane

`grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr)`, `gap: 28px`,
`align-items: start`.

- **Left** — the draft, rendered as flowing prose (16px / line-height 1.9) inside a
  bordered `--bg2` card with `34px 38px` padding. Edits are marked in place.
- **Right** — the change list, `position: sticky; top: 84px`. One row per change, in
  draft order, each row `kind · summary · char offset`.

The two panes are one selection: clicking a marker in the prose or a row in the list sets
the same `sel` value, and the corresponding annotation opens under the marker. Clicking
the active one again closes it. Only one annotation is open at a time.

---

## 4. The four depths

Rendered as a flat stack of hairline-separated rows — no cards, no chevrons, no
accordions with visible affordance beyond the hover fill. Each row is a full-width
`<button>`: `padding: 18px 4px`, `border-bottom: 1px solid var(--border-light)`,
hover `background: var(--bg2)`. The container carries `border-top: 1px solid var(--border)`.

> **Known regression to avoid:** do not put a `border-top` on both the divider component
> and its wrapper — it renders a doubled 2px rule. One owner per hairline.

| # | Label | Right-hand meta | Behaviour |
| --- | --- | --- | --- |
| 01 | Why this shape | `3 reasons` | Expands to three arrow-prefixed paragraphs |
| 02 | What is missing | `10 dimensions · 4 unknown` | Expands to the scorecard grid |
| 03 | What praxis thinks you meant | `21 fields · 8 stated` | Expands to the contract grid |
| 04 | What to change, and where | `You have not asked` | **Not a button.** Dimmed row; becomes the transform gate |

Row numbers are mono, cobalt, `min-width: 24px`. Depth 04's number and label are
`--text-dim` until the user passes the gate. This is the one row that reads as unavailable,
and that is deliberate: it advertises that a deeper layer exists without offering it.

### 4.1 Depth 02 — the scorecard

`repeat(auto-fit, minmax(320px, 1fr))` grid with `gap: 1px` over a `--border-light`
background and a 1px border — the DHK "border-gap" pattern. Cells are `--bg2`,
`18px 20px`.

Three verdicts, each a mono uppercase 11px label:

- **Pass** — `--accent-teal`
- **Gap** — `--accent-orange`
- **Unknown** — `--text-dim` with `border-bottom: 1px dashed`

Never show an aggregate score. The subhead states the counts and says so:
`4 pass · 2 gap · 4 unknown · no overall score, by design`.

**Unknown is a first-class verdict, not a loading state and not a failure.** A footnote
under the grid says exactly that. Unknown rows have `--text-muted` titles rather than the
full-strength `--text` used by Pass/Gap, so the grid reads as three tiers of confidence.

### 4.2 Depth 03 — the contract

Seven groups (Reader, Intent, Stakes, Constraints, Relationship, Timing, Form), three
fields each, in a `repeat(auto-fit, minmax(300px, 1fr))` grid, `gap: 32px`. Group names
are mono uppercase cobalt over a hairline.

Each field is a clickable row: mono key (`min-width: 116px`), value, then a right-aligned
8px dot.

- **Stated** — value in `--text`, dot filled `--accent`
- **Inferred** — value in `--text-dim` italic, dot is a 1px `--text-dim` ring

Clicking a row flips it between stated and inferred. A legend above the grid explains both
dots; the inferred one is labelled "Inferred · click to correct".

Field names are placeholders standing in for whatever the real schema exposes. **Do not
ship these strings** — bind them to the actual contract fields.

---

## 5. Edit markers

Five kinds, each with a distinct visual grammar so they are distinguishable without
reading the legend. A legend row sits above the two-pane, mono 11px.

| Kind | Marker in prose | Accent |
| --- | --- | --- |
| **Insert** | Own line: `⌃` + mono label, `border-left: 2px solid var(--accent)`, `padding-left: 12px` | `--accent` |
| **Revise** | Inline span, `border-bottom: 2px solid var(--accent)` | `--accent` |
| **Move** | Inline span, `border-bottom: 1px dashed`, prefixed `⇅` | `--accent-purple` |
| **Cut** | Inline span, `text-decoration: line-through`, text dimmed to `--text-dim` | `--text-dim` |
| **Blocked** | A block, not a span — see below | `--accent-orange` |

Weight carries meaning: a 2px solid underline is a change to the words that are there, a
1px dashed underline is a change to where they are, a strikethrough is removal. Insert is
the only marker that occupies its own line, because it points at a gap between sentences
rather than at existing text.

All markers are `<button>` elements with `font: inherit` and transparent backgrounds, so
they sit in the text baseline without disturbing the line box. Hover shifts colour to
`--accent` (or `--accent-orange` for cuts).

### 5.1 Annotations

Opening a marker reveals a panel directly beneath it: `margin-left: 12px`,
`border-left: 2px solid` in the marker's accent, `background: var(--bg)` (a step *down*
from the `--bg2` card, so it reads as inset), `12px 14px` padding, 14px / 1.7 text.

Each annotation leads with a mono uppercase label naming the kind and the location —
`Revise · chars 214–248` — then one or two sentences of reasoning. The reasoning explains
*why*, never restates the edit.

### 5.2 Blocked

The blocked change is a bordered block in `--accent-orange`, inline in the draft where the
collision is. It states what it wanted to do, shows the protected span (mono, on
`--tint-study`), and offers two ghost buttons: `Release the protection` /
`Keep it as written`.

Copy rule: it says it has not made the change and will not choose. Protected content is
never edited around, silently or otherwise.

### 5.3 Protected spans

Rendered `background: var(--tint-study); border-bottom: 1px solid var(--accent-teal)`.
Teal is the "user asserted this" colour, distinct from every edit accent.

---

## 6. Draft view toggle

Three states in the card header, mono uppercase 11px, separated by a `|` in `--border`:

- `Marked up · 7 changes`
- `Original`

plus a cobalt label to the right stating the current view in plain words —
`With changes in place` / `As you wrote it`.

**This toggle is permanent, not transient.** No hover-to-peek, no press-and-hold. The
comparison is a thing the user does deliberately, and it has to survive them scrolling and
thinking. Original renders as a `<pre>` in mono 13px / 1.85 with `white-space: pre-wrap` —
deliberately unstyled, so it is obvious that nothing has been interpreted.

---

## 7. The question card

One question at a time, never a form. Bordered card on `--bg2` with
`border-left: 2px solid var(--accent)`, `26px` padding.

Structure: mono `One question · 2 of 2 left` → 22px question → a 14px `--text-dim` line
beginning `Decides between:` → stacked option buttons (`gap: 8px`, hover flips border and
text to cobalt) → a mono opt-out, `I would rather stop here →`.

Naming what the question decides is required. A question that cannot state its consequence
should not be asked.

Two terminal states:

- **Complete** — teal-bordered card: "Nothing else you could tell me would change the
  answer." Plus a line on what the answers settled.
- **Stopped** — flat bordered card, one sentence conceding the loss of certainty and an
  `Ask me again →` affordance. Stopping is never punished and never blocks the answer.

---

## 8. Type and colour

Per DHK: `system-ui` for headings and body, **DM Mono for chrome only** — tags, labels,
dates, counts, char offsets, nav, code. Mono never carries prose.

| Role | Size / weight |
| --- | --- |
| Answer h1 | `clamp(28px, 3.2vw, 38px)` / 700 / `-0.02em` / 1.2 |
| Compose h1 | `clamp(30px, 3.6vw, 42px)` / 700 / `-0.02em` / 1.15 |
| Answer body | 18px / 1.7 / `--text-muted` |
| Depth row label | 17px / 600 |
| Question | 22px / 600 |
| Draft prose | 16px / 1.9 |
| Annotation | 14px / 1.7 |
| Chrome label | mono 11px / `0.08–0.1em` / uppercase |

Sentence case everywhere except mono chrome, which is uppercase. No headline is ever
uppercased. Radius is `4px`, universally. Borders are 1px hairlines. **No shadows** —
elevation is the `--bg` → `--bg2` → `--bg3` ladder plus borders. No gradients, no imagery,
no emoji. Unicode arrows (`→`, `↗`, `⌃`, `⇅`, `⊘`) stand in for icons; do not import an
icon set.

Transitions are `0.15s` on `color` / `background` / `border-color`. Focus-visible is a 2px
cobalt outline at `2px` offset, on both buttons and the textarea.

---

## 9. Dark theme

DHK ships light-only. This palette is an **extension**, derived for this surface — flag it
as such in any handoff, and swap this one block if the studio publishes real dark tokens.

Applied by setting `data-dlv-theme="dark"` on `document.documentElement`; every rule is a
token remap, so no component styling changes. Default is light, exposed as a `theme` prop
(`light` | `dark`), with a Light/Dark toggle in the header.

```css
:root { --header-bg: rgba(245,246,250,0.86); }

:root[data-dlv-theme="dark"] {
  --bg:  #0d0f1a;
  --bg2: #15182a;
  --bg3: #1f2338;

  --border:       #2f3452;
  --border-light: #242942;

  --text:       #f2f3f9;
  --text-muted: #c3c7dc;
  --text-dim:   #8b90ab;

  --accent:       #6d86f5;
  --accent-hover: #93a7ff;

  --accent-purple: #b06ef0;
  --accent-orange: #f0834f;
  --accent-teal:   #34c3ce;

  --tint-essay:      rgba(109, 134, 245, 0.16);
  --tint-commentary: rgba(176, 110, 240, 0.16);
  --tint-tool:       rgba(176, 110, 240, 0.16);
  --tint-study:      rgba(52, 195, 206, 0.18);
  --tint-project:    rgba(240, 131, 79, 0.16);

  --header-bg: rgba(13,15,26,0.86);
  color-scheme: dark;
}
```

Reasoning behind the mapping:

- The dark page background is the light theme's `--text` (`#0d0f1a`), so the two themes
  share an axis rather than being separately invented.
- Cobalt `#2b50e8` fails on dark ground, so `--accent` lifts to `#6d86f5` — same hue,
  raised lightness. Hover gets *lighter* in dark, inverting the light-theme direction.
- Secondary accents lift on the same principle. Their semantics are unchanged: purple =
  move/commentary, orange = gap/blocked, teal = pass/protected.
- Tints rise from 10–12% to 16–18% alpha, since low-alpha fills disappear on dark.
- `--text-muted` stays visually lighter than `--text` in both themes — a system rule.

Any hardcoded colour breaks theming. `--header-bg` exists only because the sticky header
needs a translucent fill that no existing token provides.

---

## 10. Content rules

- **Placeholder content.** The draft is a Pyodide-bundle approval email; field names,
  counts and char offsets are illustrative. No real schema is asserted anywhere. Replace
  all of it.
- **Never invent a field name.** If the engine does not expose it, it does not appear.
- **Voice** is DHK's: declarative, compressed, no hedging. Claim then turn. The refusals
  are the tonal core — "I will not guess", "I have not made it and I will not choose for
  you", "praxis locates changes; you make them" — and they must not be softened into
  friendliness.
- No emoji, no exclamation marks.

---

## 11. Not yet built

- Real data binding — everything is static placeholder content.
- `Release the protection` / `Keep it as written` are no-ops.
- Applying a change. There is deliberately no Apply button; if one is added, it belongs on
  the individual change, never on the set.
- Mobile. The two-pane assumes desktop width; the change list needs to become a sheet or
  collapse under the draft below roughly 900px.
- Move markers show origin but not destination. A leader line or a ghost at the target
  would close that.

---

## 12. Binding to the engine

*Added in this repository, not part of the design document. §10 requires every
placeholder to be replaced and forbids inventing a field name, so these are the
values the implementer binds to. Verified against `praxis.design.design()` at the
time of filing; re-derive rather than trust this table if the engine has moved.*

Everything below comes out of one call — `design(draft, contract, variants, mode)`
— which the browser worker already exposes as the `design` op alongside the
`brief` renderings (`web/src/worker.js`).

**Depth 02 — the scorecard.** `result["evaluation"]["dimensions"]`, a list of ten,
which is exactly the "10 dimensions" the spec assumes. Each carries `dimension`,
`question`, `status`, `finding`, `evidence`, `recommendation`. `status` is one of
`pass` / `gap` / `unknown` — the spec's three verdicts, unchanged. The ten:

`outcome_clarity`, `audience_fit`, `structural_fit`, `evidence_fit`,
`uncertainty_integrity`, `risk_calibration`, `relationship_fit`, `medium_fit`,
`voice_integrity`, `actionability`.

`finding` is the cell's sentence and `evidence` is the span it saw — a `pass` or a
`gap` with no evidence attached should not render as one.

**Depth 03 — the contract.** `praxis.contract.FIELDS` is 21 fields in 7 sections,
matching the spec's "21 fields" and "seven groups". The section *names* differ from
the placeholders and the counts are not three each:

| Section | Fields |
|---|---|
| `artifact` | 3 |
| `situation` | 4 |
| `reader` | 5 |
| `outcome` | 3 |
| `relationship` | 2 |
| `evidence` | 2 |
| `constraints` | 2 |

So the grid must not assume a uniform group height. Provenance for the stated/inferred
dot is `result["contract"]`, whose values carry `stated` or `inferred` — the engine's
own distinction, not a UI convention.

**Only 10 of the 21 fields have a closed domain** (`praxis.contract.SELECTORS`); the
other 11 are free text. §4.2's click-to-flip works for both, but an option picker
exists only for those ten. The worker's ready message ships the full catalogue —
`name`, `section`, `question`, `options`, `note`, `kind` — so no vocabulary needs
restating in the UI.

**Depth 01 — why this shape.** `brief.why(result)`, with `result["strategy"]`
carrying the chosen structure and the runners-up.

**The question card.** `brief.next_question(result)` returns `ask`, `field`,
`options`, and `changes` — `changes` is what §7 requires the card to name as the
consequence. The counter must use `result["questions_outstanding"]`, the true total,
not the length of the capped display list in `result["questions"]`.

**The transform gate.** `mode="transform"`, which `mode="auto"` never selects — the
engine enforces §1's second rule independently of the UI, and rejects a transform
with no draft rather than silently falling back.

**Edit markers.** Transform mode returns located `Edit` records with character
offsets and a `kind` of insert / revise / move / cut, plus `blocked_by` where an
edit collides with a protected span — §5's five kinds are the engine's own set.
`folded_into` and `no_edit_for` also come back and have no home in this spec: every
reported gap must produce an edit, fold into one, or be named, so a gap that did
none of those needs somewhere to appear.

**Protected spans** come from the writer's declared constraints, which is why §5.3
colours them as asserted rather than derived.

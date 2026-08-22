"""Prompts praxis writes and never sends.

Two of them now, and they share a principle: praxis packages everything a
model would need, hands it to a person, and stops. It calls nothing. The
person carries the prompt wherever they like and brings the result back.

`render_prompt` packages a transformation run's flagged items.
`corpus_prompt` packages everything needed to work on the detector
corpus — the claim each signal makes, the examples that exist, and the
cases praxis has been caught getting wrong — so that someone can extend
or attack it with a model of their choosing, without praxis, without this
repository, and without any of it having to be trusted.
"""

from .validation import protected_tokens

def render_prompt(result: dict) -> str:
    """Render the flagged items of a run as a self-contained LLM prompt.

    The pipeline stays deterministic: this only packages what was flagged for
    human judgment as portable Markdown. The user carries it to a model and
    brings the proposals back — the harness never calls one.

    Returns "" when nothing was flagged.
    """
    flagged = [t for t in result["transformations"] if not t["applied"]]
    if not flagged:
        return ""

    pack = result.get("pack", {})
    tokens = sorted(protected_tokens(result["final"]))
    token_list = ", ".join(f"`{t}`" for t in tokens) if tokens else "(none detected)"

    items = []
    for t in flagged:
        items.append(f"""### {t['id']} · rule {t['rule_id']} ({t['recommendation_id']})

Why it was flagged: {t['reason']}

Evidence:

> {t['before']}""")

    return f"""# praxis review handoff

This document was processed by praxis, a deterministic transformation pipeline
(pack: {pack.get('id', 'unknown')} v{pack.get('version', '?')} — {pack.get('title', '')}).
Mechanical fixes were already applied. The items below were flagged for human
judgment; the pipeline never edits them. Your job is to propose resolutions a
human can accept or reject.

## Instructions

For each flagged item, propose a concrete rewrite of the evidence — or state
"no change" with a one-sentence reason. Rules:

1. Protected tokens must appear verbatim in any rewrite: {token_list}
2. Preserve meaning. Do not add facts that are not in the document.
3. Answer with one section per item, titled by its ID, containing
   **Proposed rewrite:** and **Rationale:** — nothing else.

## Flagged items

{(chr(10) + chr(10)).join(items)}

## Document (after applied transformations)

```markdown
{result['final']}
```
"""


def corpus_prompt(detector: str | None = None, examples: list[dict] | None = None,
                  scores: dict | None = None, show: int = 6) -> str:
    """Everything needed to work on the detector corpus, as one prompt.

    praxis measures its detectors deterministically, which is the whole
    point of it. But the corpus those measurements run against is written
    by people, and a person may reasonably want a model's help widening
    it. This hands them the entire problem — what each signal claims to
    mean, the boundary it must not cross, the examples already held, and
    the specific cases praxis has been caught failing — in a form that
    needs neither praxis nor this repository to act on.

    The prompt is built so the **category supplies the label**. It asks
    for sentences in a named class rather than asking a model to write
    text and then decide what is in it, because the second measures
    agreement between two models and calls it ground truth.
    """
    from . import signals
    from .measure import load, score

    examples = load() if examples is None else examples
    scores = score(examples=examples, sources=("hand", "review", "corpus",
                                               "generated")) if scores is None else scores

    names = [detector] if detector else _weakest(scores, signals.DETECTORS)
    unknown = [n for n in names if n not in signals.DETECTORS]
    if unknown:
        raise KeyError(f"Unknown detector(s) {unknown}. "
                       f"Available: {', '.join(sorted(signals.DETECTORS))}")

    sections = [_signal_section(name, examples, scores, show) for name in names]
    return f"""# praxis corpus commission

praxis detects communication signals in prose — whether a message contains
a request, a deadline, a route to escalate, a named next update time. Each
signal is a compiled regular expression. praxis calls no language model at
any point; it is meant to be reproducible and auditable.

Those regular expressions were written by a language model, and it shows.
Independent review found seven cases of a detector firing on text it should
not have; three of the fixes introduced the next failure. The corpus below
exists to catch that class of mistake, and it is only as good as the cases
it contains — which is where you come in.

**You need nothing from praxis to do this.** Everything required is below.

## What I want

For each signal in this document, produce sentences that belong to a named
class. Two classes matter:

- **Positive** — the signal is genuinely present.
- **Negative** — the signal is genuinely *absent*, but the sentence is close
  enough that a careless pattern would fire on it anyway.

The negatives are the valuable half. A pattern is wrong at its boundary, not
in the middle.

**Do not write text and then decide what is in it.** Write to the class I
name. The class is the label. If you find yourself unsure which class a
sentence you wrote belongs to, discard the sentence — an ambiguous example
is worse than none, because it makes a wrong measurement look like a right
one.

Aim for {show * 3} sentences per signal, split roughly evenly between the
classes, and vary the phrasing hard: contractions, hard line breaks, British
and American spelling, sentence fragments, quoted replies, signature blocks.
Real messages are messy and generated ones tend not to be.

## Output format

One JSON object per line. Nothing else — no prose around it, no code fence.

```
{{"text": "...", "present": ["deadline"], "absent": ["uncertainty"], "source": "generated"}}
```

- `present` and `absent` name **only** the signals your sentence is about.
  Anything you do not name is treated as unlabelled and is not scored. Do
  not guess at signals to fill the object out; a sentence labelled for one
  signal is worth more than one guessed at for twelve.
- `source` must be `"generated"`. These are scored separately from
  human-written examples and never counted toward the headline figure,
  because the model that wrote the detectors and the model writing the
  examples share their blind spots. That is not a slight; it is the reason
  this commission is worth issuing at all.
- Do not reproduce any example already listed below.

{(chr(10) + chr(10)).join(sections)}
"""


def _weakest(scores: dict, detectors) -> list[str]:
    """The signals with the least evidence behind them, worst first."""
    counted = {name: bucket["labelled"] for name, bucket in scores["detectors"].items()}
    return sorted(detectors, key=lambda n: (counted.get(n, 0), n))[:3]


def _signal_section(name: str, examples: list[dict], scores: dict, show: int) -> str:
    from . import signals

    means, excludes = signals.MEANINGS[name]
    bucket = scores["detectors"].get(name, {})
    labelled = bucket.get("labelled", 0)
    coverage = (f"{labelled} labelled example(s) so far."
                if labelled else "**No labelled example at all** — this signal is "
                                 "entirely unmeasured, so it needs the most.")

    positive = [e for e in examples if name in e.get("present", [])]
    negative = [e for e in examples if name in e.get("absent", [])]
    caught = [e for e in examples
              if name in e.get("absent", []) and e.get("source") == "review"]

    return f"""## Signal: `{name}`

**Means:** {means}

**Does not mean:** {excludes}

{coverage}

**Examples already held — positive (the signal is present):**

{_bullets(positive, show) or "_none yet_"}

**Examples already held — negative (present in the text's neighbourhood, absent in fact):**

{_bullets(negative, show) or "_none yet_"}
{_caught_section(caught, show)}"""


def _caught_section(caught: list[dict], show: int) -> str:
    if not caught:
        return ""
    return f"""
**praxis was caught getting these wrong.** They are the shape of mistake to
hunt for; more like them is exactly what I am asking for:

{_bullets(caught, show, note=True)}"""


def _bullets(rows: list[dict], show: int, note: bool = False) -> str:
    lines = []
    for row in rows[:show]:
        text = f"- `{row['text']}`"
        if note and row.get("note"):
            text += f" — {row['note']}"
        lines.append(text)
    if len(rows) > show:
        lines.append(f"- _(and {len(rows) - show} more)_")
    return "\n".join(lines)

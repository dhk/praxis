"""Perkins — the prompt a design result commissions from a model.

Named for Maxwell Perkins, who edited Fitzgerald, Hemingway and Wolfe and
did not write their sentences. He cut ninety thousand words from Wolfe and
added none of his own: the job was to find what the book was trying to be
and hold the author to it. That is exactly the line praxis draws, so the
module that hands work to a model carries his name.

`commission(result)` turns a design result into a self-contained prompt.
Like `handoff.render_prompt`, it packages and never sends: the engine holds
no key, calls no model, and reaches no network, and this does not change
that. The person carries the prompt to whatever model they use.

Two things this is not:

- **Not the eleven prompts in `prompts/`.** Those carry per-genre weights
  from the alexandria organizational-writing study and are a snapshot of
  it. Perkins reads praxis's own contract and engine — a different source
  and a different prompt. Neither generates the other, and wiring the two
  together was considered and rejected.
- **Not a rewrite request.** The prompt forbids rewriting, scoring,
  guessing and questionnaires, in the text, as prohibitions. Those
  refusals are the product; without them a reviewer returns a wash of
  plausible edits, which is what the writer already had.
"""

from __future__ import annotations

import hashlib

from . import __version__
from . import strategy as strategy_mod
from .contract import FIELDS
from .strategy import STRUCTURES

#: What the reviewer may not do, and why each prohibition earns its place.
#: Data rather than prose in a template: these are the product surface, and
#: a rule nobody can enumerate is a rule that quietly erodes.
REFUSALS: tuple[tuple[str, str], ...] = (
    ("Do not rewrite the text, produce an improved version, or show me how it "
     "could read.",
     "A reviewer that rewrites has answered a question I did not ask, and the "
     "rewrite arrives without the reasoning that produced it. If I want that "
     "I will ask for it separately."),
    ("Do not give it a score, a grade, or a mark out of anything.",
     "There is no overall number here. Inventing one replaces a judgement "
     "with a figure and invites me to optimise the figure."),
    ("Do not guess at something I have not told you.",
     "\"I do not know, and here is the question that would settle it\" is a "
     "complete and useful answer."),
    ("Ask me one question at a time and wait for the answer.",
     "Never a form, never a numbered list of six things to fill in. Name what "
     "each question decides between, so I can see why it is worth answering."),
)


def fingerprint() -> str:
    """A short digest of the rule surface this prompt was generated from.

    Stamped into every prompt so a copy can be told from the current one.
    A prompt is a file someone keeps; without this, a reader has no way to
    know their copy predates a rule change, and the staleness is invisible
    rather than merely inconvenient.

    Covers the two tables that decide what a prompt says: the structures
    that produce the recommendation, and the contract fields that produce
    the questions. It deliberately does not cover prose — an edit to a
    refusal's wording is not a change in what praxis holds a draft to.
    """
    parts = [f"{s.id}|{s.sequence}|{s.favors}|{s.avoids}" for s in STRUCTURES]
    parts += [f"{f.name}|{f.domain}" for f in FIELDS]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:8]


def stamp() -> str:
    """The provenance line a copied prompt carries with it."""
    return f"praxis {__version__} · rules {fingerprint()}"


def _requirements(strategy: dict) -> list[str]:
    return [r for r in strategy.get("requirements", []) if r]


def commission(result: dict, draft: str = "") -> str:
    """The prompt this design result commissions, as self-contained Markdown.

    `draft` is appended verbatim when given; otherwise the prompt ends with
    a place to paste one. Nothing is recomputed here — every claim below is
    read off the result, so the prompt cannot say something the engine did
    not.
    """
    strategy = result.get("strategy", {})
    evaluation = result.get("evaluation") or {}
    dimensions = evaluation.get("dimensions", [])
    questions = result.get("questions", [])
    outstanding = result.get("questions_outstanding", 0)

    L: list[str] = ["# Review this message with me", ""]
    L.append("You are reviewing a piece of writing. You are not rewriting it.")
    L += ["", "## What you may not do", ""]
    for rule, because in REFUSALS:
        L.append(f"- **{rule}** {because}")

    L += ["", "## What this message has to do", ""]
    if strategy:
        L.append(f"It should be shaped **{strategy['title'].lower()}** — "
                 f"{strategy['summary'].rstrip('.').lower()}.")
        if strategy.get("sequence"):
            L.append("")
            L.append("In this order: " + " → ".join(strategy["sequence"]) + ".")
        because = strategy.get("because") or []
        if because:
            # A list, not a clause: each reason gets its gloss, which is what
            # makes the machine pair readable to someone who has never seen
            # the contract. Three of these inside one sentence do not fit.
            L += ["", "That shape follows from the situation, not from taste:", ""]
            L += [f"- {strategy_mod.inline(r)}" for r in because]
        confidence = strategy.get("confidence")
        runner = strategy.get("runner_up") or {}
        if confidence in ("low", "moderate") and runner.get("title"):
            L += ["", f"Confidence in that shape is **{confidence}** — "
                  f"{runner['title']} was the near alternative. If the draft "
                  "reads better the other way, say so."]
    reqs = _requirements(strategy)
    if reqs:
        L += ["", "At this level of risk the message owes the reader:", ""]
        L += [f"- {r}" for r in reqs]

    L += ["", "## What to hold it to", ""]
    if dimensions:
        L.append("Go dimension by dimension. For each, say pass, gap, or "
                 "unknown, and show the words in my draft that made you say "
                 "it. A verdict with no evidence attached is an opinion.")
        L.append("")
        for d in dimensions:
            mark = {"pass": "·", "gap": "!", "unknown": "?"}.get(d.get("status"), "·")
            L.append(f"- `{mark}` **{d['dimension']}** — {d['question']}")
        L += ["", "praxis has already read the draft against these and its "
              "reading is marked above: `!` where it found a gap, `?` where it "
              "could not tell, `·` where it passed. Check that reading rather "
              "than repeating it, and say where you disagree."]
    else:
        L.append("There is no draft yet, so there is nothing to hold to "
                 "anything. When I bring one, hold it to the requirements "
                 "above and to what the shape asks for.")

    L += ["", "## What is still unsettled", ""]
    if not questions:
        L.append("Nothing about the situation. praxis walked every unanswered "
                 "field across its possible values and none of them changed "
                 "the answer, so do not interrogate me about the brief — "
                 "whatever is unsettled is in the draft.")
    else:
        q = questions[0]
        L.append(f"**{q['question']}** I have not told you, and it changes the "
                 "answer.")
        decides = q.get("decides_between") or {}
        if decides:
            L.append("")
            for outcome, values in decides.items():
                L.append(f"- {', '.join(values)} → {outcome}")
        if outstanding > 1:
            L += ["", f"That is one of {outstanding} unsettled things. Ask it "
                  "first, take my answer, then ask the next or tell me you "
                  "have enough. Stop as soon as nothing further would change "
                  "your reading, and say so plainly."]

    L += ["", '## What "unknown" means', "",
          "It is not a failure and not a hedge. It means the answer depends on "
          "something I have not told you, or on something no reading of the "
          "text can settle. Use it often and say which of the two it is."]

    L += ["", "## Where this came from", "",
          "Generated by praxis from a stated communication situation — the "
          "reader, the stakes, the outcome, the relationship. praxis decides "
          "the shape and what the message owes; it writes no prose and calls "
          "no model. This prompt is the handoff, and you are the model.",
          "", f"`{stamp()}`",
          "", "If those rules have moved since this prompt was generated, this "
          "copy will not know. Regenerate rather than trusting an old file."]

    L += ["", "---", "",
          "My draft follows. Begin with what it currently does for its "
          "reader, in two or three sentences.", ""]
    if draft.strip():
        L += ["```", draft.rstrip(), "```"]
    elif result.get("draft_present"):
        # The result was built from a draft this caller did not hand over.
        # A paste placeholder here would tell the model no draft exists,
        # while every dimension mark above was read off one.
        L += ["```", "[paste the same draft praxis read — the dimension marks "
              "above were taken from it]", "```"]
    else:
        L += ["```", "[paste your draft here]", "```"]
    return "\n".join(L) + "\n"

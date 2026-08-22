"""Saying only as much as was asked for.

Praxis spends its whole argument on leading with the answer, asking only
what changes it, and letting the reader drill in — and then, for two
commits, answered every tool call with a page of JSON. This module is the
correction. It renders a design result at four depths, and the default is
the shallowest one that is still true.

The depths:

* ``answer`` — the shape to write to, and what is wrong with the draft.
  Two or three sentences. No reasoning, no rationale, no runner-up.
* ``why`` — which contract values chose that shape, what came second, and
  what this level of stakes obliges.
* ``findings`` — every dimension, including the passes and the honest
  unknowns.
* ``contract`` — the situation as praxis currently understands it,
  marked for what was stated and what was guessed.

`progress` is the piece that makes stopping a choice rather than a
guess. It reports how many questions would still *change* the answer —
not how many fields are blank — so "nothing else you could tell me would
change this" is a statement praxis can actually make. Most tools cannot
tell you when you are finished.
"""

from .contract import BY_NAME, SELECTORS

DEPTHS = ("answer", "why", "findings", "contract", "edits")


def answer(result: dict) -> str:
    """The shape, and what is wrong. Nothing else."""
    strategy = result["strategy"]
    shape = strategy["title"].lower()

    if "transform" in result:
        return _transform_answer(result, shape)

    if not result.get("draft_present"):
        steps = ", then ".join(strategy["sequence"])
        return f"Write it {shape}: {steps}."

    gaps = [d for d in result["evaluation"]["dimensions"] if d["status"] == "gap"]
    if not gaps:
        return f"Nothing to fix against this contract, and the shape holds ({shape})."

    shown = "; ".join(g["short"] or g["dimension"].replace("_", " ") for g in gaps[:3])
    rest = f" Plus {len(gaps) - 3} more." if len(gaps) > 3 else ""
    thing = "one thing" if len(gaps) == 1 else f"{len(gaps)} things"
    return f"Fix {thing} before sending: {shown}.{rest} Shape it {shape}."


def _transform_answer(result: dict, shape: str) -> str:
    """What to change, counted by kind, so the writer sees the shape of
    the work before the list of it."""
    edits = result["transform"]["edits"]
    if not edits:
        return f"Nothing to change against this contract. The shape holds ({shape})."
    by_kind: dict[str, int] = {}
    for edit in edits:
        by_kind[edit["kind"]] = by_kind.get(edit["kind"], 0) + 1
    counted = ", ".join(f"{n} to {kind}" for kind, n in sorted(by_kind.items()))
    blocked = result["transform"]["blocked"]
    warning = (f" {blocked} of them touch protected content and need your call."
               if blocked else "")
    return f"{len(edits)} located change(s): {counted}. Shape it {shape}.{warning}"


def edits(result: dict) -> str:
    """Every located change, as a line a person can act on."""
    if "transform" not in result:
        return "Not a transform run; call design_transform for located changes."
    rows = []
    for edit in result["transform"]["edits"]:
        place = (f"insert at {edit['at']}" if edit["at"] is not None
                 else f"{edit['where']['start']}-{edit['where']['end']}")
        row = f"[{edit['kind']}] {place} ({edit['dimension']}): {edit['instruction']}"
        if edit["where"]:
            row += f"\n    on: {edit['where']['text'][:100]!r}"
        if edit["blocked_by"]:
            row += "\n    BLOCKED: overlaps protected content — your call, not praxis's."
        rows.append(row)
    folded = result["transform"]["folded_into"]
    if folded:
        rows.append("Folded into another edit: "
                    + ", ".join(f"{k} → {v}" for k, v in folded.items()))
    if result["transform"]["no_edit_for"]:
        rows.append("No edit could be located for: "
                    + ", ".join(result["transform"]["no_edit_for"]))
    return "\n".join(rows)


def progress(result: dict) -> str:
    """How much is left, and — the useful half — how much is not.

    Counts only questions whose answers would change the recommendation.
    A blank field that changes nothing is not work outstanding, and
    reporting it as such is how a tool talks someone into an interview
    they did not need.
    """
    strategy = result["strategy"]
    outstanding = result.get("questions_outstanding", len(result["questions"]))
    parts = [f"{strategy['confidence']} confidence"]

    if outstanding:
        parts.append(f"{outstanding} question{'s' if outstanding > 1 else ''} "
                     "would still change this")
    else:
        settled = len(result.get("do_not_ask", []))
        parts.append("nothing else you could tell me would change it"
                     + (f" ({settled} unknowns checked)" if settled else ""))

    if result.get("draft_present"):
        counts = result["evaluation"]["summary"]
        hidden = counts["pass"] + counts["unknown"]
        if hidden:
            parts.append(f"{hidden} more finding{'s' if hidden > 1 else ''} not shown")
    return " · ".join(parts)


def why(result: dict) -> str:
    """The reasoning, for someone who asked for it."""
    s = result["strategy"]
    lines = [f"{s['title']} was chosen because {_join(s['because'])}."]
    runner = s["runner_up"]
    if runner["why_not"]:
        lines.append(f"{runner['title']} came second; {_join(runner['why_not'])}.")
    else:
        lines.append(f"{runner['title']} came second on a lower score.")
    lines.append("At these stakes the message needs: " + _join(s["requirements"]) + ".")
    lines.append(f"Evidence standard: {s['evidence_standard']}.")
    if result["shading"]["offer"]:
        # Both offered shades usually come from one tension; naming that
        # tension twice reads as two unrelated reasons for one choice.
        by_tension: dict[str, list[str]] = {}
        for x in result["shading"]["shades"]:
            by_tension.setdefault(x["tension"], []).append(x["title"])
        lines.append("Worth seeing an alternative because " + "; ".join(
            f"{tension} ({' or '.join(titles)})" for tension, titles in by_tension.items()) + ".")
    else:
        lines.append(f"One version, not a menu: {result['shading']['reason']}.")
    return "\n".join(lines)


def findings(result: dict) -> str:
    """Every dimension, passes and unknowns included."""
    if not result.get("draft_present"):
        return "No draft to evaluate yet."
    rows = []
    for d in result["evaluation"]["dimensions"]:
        line = f"[{d['status']}] {d['dimension'].replace('_', ' ')}: {d['finding']}"
        if d["recommendation"]:
            line += f" → {d['recommendation']}"
        rows.append(line)
    return "\n".join(rows)


def contract(result: dict) -> str:
    """The situation as praxis has it, marked stated or guessed."""
    c = result["contract"]
    provenance = c["provenance"]
    rows = []
    for section, fields in c["sections"].items():
        for name, value in fields.items():
            mark = " (guessed)" if provenance.get(name) == "inferred" else ""
            rows.append(f"{section}.{name}: {value}{mark}")
    if not rows:
        return "Nothing stated or inferred about this situation yet."
    return "\n".join(rows)


def next_question(result: dict) -> dict | None:
    """The single highest-value question, phrased for a person.

    One, not three. A writer who wants to keep going can ask for the
    rest; a writer who has had enough should not have to decline a list.
    """
    if not result["questions"]:
        return None
    q = result["questions"][0]
    field = BY_NAME[q["field"]]
    return {
        "field": q["field"],
        "ask": q["question"],
        "options": q["options"],
        "note": field.note or None,
        "already_guessed": q["current"] if q["status"] == "inferred" else None,
        "changes": _changes(q),
    }


def _changes(question: dict) -> str:
    """What the answers actually decide, in one readable line.

    When every outcome opens the same way — the shape holds and only the
    alternatives differ — that shared part is stated once. Repeating
    "Bottom line up front" against each branch buries the thing that
    actually varies.
    """
    outcomes = question["decides_between"]
    # A field like `intent` splits twelve ways. Enumerating all of them
    # costs more than the question is worth and buries the only thing the
    # writer needs to know, which is that the answer decides everything.
    if len(outcomes) > 3:
        return f"splits {len(outcomes)} ways — this decides the shape outright"
    shared = _common_prefix(list(outcomes))
    parts = [f"{'/'.join(values)} → {shape[len(shared):].strip() or 'the same'}"
             for shape, values in outcomes.items()]
    line = "; ".join(parts)
    return f"{shared.rstrip(', ')} either way — {line}" if shared else line


def _common_prefix(items: list[str]) -> str:
    """The longest shared opening, trimmed back to a comma boundary."""
    if len(items) < 2:
        return ""
    first, last = min(items), max(items)
    i = 0
    while i < len(first) and i < len(last) and first[i] == last[i]:
        i += 1
    prefix = first[:i]
    cut = prefix.rfind(",")
    return prefix[: cut + 1] if cut > 0 else ""


def _join(items: list[str]) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


RENDERERS = {"answer": answer, "why": why, "findings": findings,
             "contract": contract, "edits": edits}


def at_depth(result: dict, depth: str) -> str:
    if depth not in RENDERERS:
        raise KeyError(f"Unknown depth '{depth}'. Available: {', '.join(DEPTHS)}")
    return RENDERERS[depth](result)


def unresolved_count(result: dict) -> int:
    """Questions that would still change the answer — all of them.

    `result["questions"]` is the display list, capped at three. Reading
    the count off it reports "3" forever, which is the bug this helper
    is named to avoid.
    """
    return result.get("questions_outstanding", len(result["questions"]))


def settled_count(result: dict) -> int:
    """Unknowns praxis checked and decided were not worth asking about."""
    return len(result.get("do_not_ask", []))


__all__ = ["DEPTHS", "answer", "progress", "why", "findings", "contract", "edits",
           "next_question", "at_depth", "unresolved_count", "settled_count"]

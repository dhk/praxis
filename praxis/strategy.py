"""Choosing a communication structure, and knowing what to ask before you do.

Two deterministic operations live here.

`recommend` scores every known structure against the contract and returns
the winner *with its reasons* — which contract values pushed it up, which
pushed the runner-up down. The scoring table is pure data drawn from the
"best for / avoid when" tradition of structure selection; adding a
structure means adding a row, never editing the scorer.

`material_questions` is the more consequential one. The rule everybody
states and nobody implements is "ask only questions whose answers change
the strategy". That is decidable: take an unknown field, walk it across
its closed domain, re-run `recommend` for each value, and see whether the
recommendation actually moves. If every value lands on the same structure,
the question is intake and the assistant should not spend the writer's
attention on it. If the values split, the question is load-bearing and the
split itself is the reason to ask. No heuristic, no prompt, no model.
"""

from dataclasses import dataclass
from .contract import Contract, BY_NAME, SELECTORS, INFERRED

Weights = tuple[tuple[str, str, int], ...]


@dataclass(frozen=True)
class Structure:
    """One way to order a message, and the situations that call for it."""
    id: str
    title: str
    sequence: tuple[str, ...]
    favors: Weights
    avoids: Weights
    summary: str


STRUCTURES: tuple[Structure, ...] = (
    Structure("bluf", "Bottom line up front",
              ("bottom line", "what is needed", "why", "detail on request"),
              (("time_available", "low", 3), ("authority", "decides", 2),
               ("authority", "approves", 2), ("urgency", "today", 2),
               ("urgency", "immediate", 2), ("intent", "request", 2),
               ("intent", "escalate", 1), ("medium", "slack", 1), ("medium", "email", 1)),
              (("prior_knowledge", "none", 3), ("intent", "teach", 3),
               ("intent", "explain", 2), ("intent", "repair", 2)),
              "Lead with the conclusion; the reader can stop after the first line."),
    Structure("pyramid", "Pyramid principle",
              ("recommendation", "supporting arguments", "evidence per argument", "decision required"),
              (("intent", "recommend", 3), ("authority", "decides", 2),
               ("authority", "approves", 2), ("medium", "memo", 2), ("medium", "report", 2),
               ("medium", "proposal", 2), ("stakes", "high", 1), ("time_available", "medium", 1)),
              (("intent", "teach", 3), ("urgency", "immediate", 2), ("intent", "repair", 2)),
              "Answer first, then the grouped arguments that hold the answer up."),
    Structure("scqa", "Situation–complication–question–answer",
              ("shared situation", "what changed", "the question it raises", "your answer"),
              (("intent", "persuade", 3), ("prior_knowledge", "none", 2),
               ("medium", "proposal", 2), ("medium", "report", 1), ("time_available", "high", 1)),
              (("urgency", "immediate", 3), ("time_available", "low", 2),
               ("prior_knowledge", "expert", 2)),
              "Build the frame before the answer, for a reader who needs the problem first."),
    Structure("prep", "Point–reason–example–point",
              ("point", "reason", "example", "point restated"),
              (("intent", "persuade", 2), ("medium", "slack", 2),
               ("time_available", "low", 1), ("power_distance", "peer", 1)),
              (("stakes", "safety_critical", 3), ("stakes", "high", 2),
               ("intent", "teach", 2), ("intent", "explain", 1)),
              "Short advocacy that fits in a message, not a document."),
    Structure("sbar", "Situation–background–assessment–recommendation",
              ("situation", "background", "assessment", "recommendation"),
              (("intent", "escalate", 4), ("medium", "handoff", 3),
               ("stakes", "safety_critical", 3), ("urgency", "immediate", 2),
               ("stakes", "high", 1), ("authority", "decides", 1)),
              (("medium", "proposal", 2), ("intent", "teach", 2), ("intent", "persuade", 2)),
              "The escalation and handoff protocol: hand over state, then ask."),
    Structure("cer", "Claim–evidence–reasoning",
              ("claim", "evidence", "reasoning", "limits"),
              (("intent", "correct", 3), ("intent", "persuade", 2),
               ("prior_knowledge", "expert", 2), ("stakes", "high", 2), ("medium", "report", 1)),
              (("time_available", "low", 2), ("medium", "slack", 2), ("intent", "repair", 2)),
              "For a reader who will check the reasoning, not just the conclusion."),
    Structure("sia", "Situation–impact–action",
              ("what is happening", "who it affects", "what happens next", "when you will hear more"),
              (("intent", "warn", 3), ("intent", "inform", 2), ("urgency", "today", 2),
               ("urgency", "immediate", 2), ("stakes", "moderate", 1), ("stakes", "high", 1),
               ("medium", "slack", 1), ("medium", "email", 1)),
              (("intent", "teach", 2), ("intent", "persuade", 2), ("intent", "demonstrate", 2)),
              "The incident-update shape: state, blast radius, action, update cadence."),
    Structure("hazard_first", "Hazard–consequence–action–uncertainty",
              ("the hazard", "the consequence", "the protective action", "what is still unknown"),
              (("intent", "warn", 4), ("stakes", "crisis", 3), ("stakes", "safety_critical", 3),
               ("urgency", "immediate", 2)),
              (("intent", "teach", 3), ("intent", "demonstrate", 2), ("intent", "recommend", 1)),
              "Danger before explanation, because the reader may stop reading."),
    Structure("reassure", "Acknowledge–knowns–unknowns–action–cadence",
              ("acknowledge", "what is known", "what is not", "what is being done", "next update"),
              (("intent", "reassure", 4), ("stakes", "crisis", 3), ("sensitivity", "high", 1),
               ("urgency", "immediate", 1)),
              (("intent", "recommend", 2), ("intent", "demonstrate", 2), ("intent", "request", 1)),
              "Certainty about process where there is none about outcome."),
    Structure("repair", "Acknowledge–responsibility–repair–next behaviour",
              ("acknowledge impact", "take responsibility", "name the repair", "what changes"),
              (("intent", "repair", 5), ("sensitivity", "high", 2), ("power_distance", "downward", 1)),
              (("stakes", "safety_critical", 1), ("intent", "demonstrate", 2)),
              "Repair before explanation; an explanation offered first reads as a defence."),
    Structure("cme", "Concept–mechanism–example",
              ("the idea", "how it works", "a worked example", "check for understanding"),
              (("intent", "teach", 4), ("intent", "explain", 3), ("prior_knowledge", "none", 3),
               ("prior_knowledge", "partial", 1), ("time_available", "high", 1)),
              (("time_available", "low", 2), ("urgency", "immediate", 2), ("authority", "decides", 1)),
              "Build the model before the detail, for a reader who must be able to use it."),
    Structure("star", "Situation–task–action–result",
              ("situation", "task", "action", "result"),
              (("intent", "demonstrate", 4), ("medium", "doc", 1)),
              (("stakes", "high", 2), ("intent", "recommend", 2), ("urgency", "immediate", 2)),
              "Evidence of judgment, told as one episode."),
)

BY_ID = {s.id: s for s in STRUCTURES}


def _strategy_inputs() -> frozenset[str]:
    """The contract fields the rules genuinely read, structures and shades.

    Derived from the tables rather than assumed to be "every field with a
    closed domain". `voice` has a domain and no rule consults it, so
    treating the two as the same thing advertised it in `schema()` as
    strategy-selecting and let it raise the reported confidence of a
    contract the rules were no better informed about.
    """
    from .shading import rule_fields

    fields: set[str] = set(rule_fields())
    for structure in STRUCTURES:
        fields |= {name for name, _, _ in structure.favors}
        fields |= {name for name, _, _ in structure.avoids}
    return frozenset(fields)


STRATEGY_INPUTS = _strategy_inputs()

#: What a message must contain before it is safe to send, by stakes tier.
#: Each tier inherits everything below it — rigor rises with consequence,
#: it never resets.
REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "low": ("a clear reader takeaway",),
    "moderate": ("an explicit action", "a named owner", "a deadline"),
    "high": ("evidence for every consequential claim",
             "facts separated from inference and recommendation",
             "visible uncertainty on estimates"),
    "safety_critical": ("actor, action, and timing stated exactly",
                        "a confirmation mechanism (read-back, approval, or acknowledgement)",
                        "an escalation path"),
    "crisis": ("what is known and not known, stated plainly",
               "a named next update time"),
}
TIERS = ("low", "moderate", "high", "safety_critical", "crisis")


def requirements(stakes: str | None) -> list[str]:
    """Cumulative requirements up to and including `stakes`."""
    if stakes not in TIERS:
        return list(REQUIREMENTS["low"])
    out: list[str] = []
    for tier in TIERS[: TIERS.index(stakes) + 1]:
        out.extend(REQUIREMENTS[tier])
    return out


@dataclass(frozen=True)
class Scored:
    structure: Structure
    score: int
    contributions: tuple[tuple[str, str, int], ...]


def _score(structure: Structure, contract: Contract) -> Scored:
    hits: list[tuple[str, str, int]] = []
    total = 0
    for name, value, weight in structure.favors:
        if contract.get(name) == value:
            hits.append((name, value, weight))
            total += weight
    for name, value, weight in structure.avoids:
        if contract.get(name) == value:
            hits.append((name, value, -weight))
            total -= weight
    hits.sort(key=lambda h: -abs(h[2]))
    return Scored(structure, total, tuple(hits))


def rank(contract: Contract) -> list[Scored]:
    """Every structure, best first. Ties break on declaration order, so the
    same contract always yields the same recommendation."""
    scored = [_score(s, contract) for s in STRUCTURES]
    order = {s.id: i for i, s in enumerate(STRUCTURES)}
    scored.sort(key=lambda s: (-s.score, order[s.structure.id]))
    return scored


def recommend(contract: Contract) -> dict:
    """The recommended structure, why it won, and what it obliges."""
    ranked = rank(contract)
    best, runner = ranked[0], ranked[1]
    stakes = contract.get("stakes")
    return {
        "structure": best.structure.id,
        "title": best.structure.title,
        "summary": best.structure.summary,
        "sequence": list(best.structure.sequence),
        "score": best.score,
        "because": [_reason(n, v, w) for n, v, w in best.contributions[:3]],
        "runner_up": {"structure": runner.structure.id, "title": runner.structure.title,
                      "score": runner.score,
                      "why_not": [_reason(n, v, w) for n, v, w in runner.contributions
                                  if w < 0][:2],
                      "instead_of": divergences(best, runner)},
        "confidence": _confidence(best, runner, contract),
        "requirements": requirements(stakes),
        "evidence_standard": _evidence_standard(stakes),
        "considered": [{"structure": s.structure.id, "score": s.score} for s in ranked],
    }


def _reason(name: str, value: str, weight: int) -> dict:
    """One weight row, as the pair that decided it and a gloss of the field.

    Two fields rather than one string, because the three renderers put these
    in different containers. `render.py` and `perkins` emit a list, where a
    gloss earns its space; `brief.why` builds a sentence, where three glosses
    turn seventy-seven characters into two hundred and fifty-eight. Handing
    over both parts lets each decide, instead of one format losing to the
    other.

    `reason` keeps the machine pair verbatim: it is a receipt, and a reader
    checking the claim needs the name the contract actually uses. `gloss` is
    joined from `contract.Field.question`, never written here, so a field's
    meaning lives in exactly one place. A field with no question glosses to
    the empty string.
    """
    return {
        "reason": f"{_pair(name, value)} {_verb(weight)} it",
        "gloss": _gloss(name),
    }


def _pair(name: str, value: str) -> str:
    """The machine pair, verbatim. A receipt a reader can check against
    `contract.py` needs the name the contract actually uses."""
    return f"{name} = {value}"


def _gloss(name: str) -> str:
    """A field's meaning, joined from its own question so it lives in one
    place. A field the contract does not know glosses to the empty string
    rather than raising."""
    field = BY_NAME.get(name)
    question = field.question if field and field.question else ""
    return question.rstrip("?").strip().lower()


def _verb(weight: int | None) -> str:
    """How one weight row landed for one structure. `None` is the row the
    structure has no opinion about at all, which is a third outcome and not
    a zero — a structure that never mentions a fact is different from one
    that mentions it and shrugs."""
    if weight is None:
        return "does not count for"
    return "favours" if weight > 0 else "counts against"


def divergences(best: Scored, runner: Scored, limit: int = 3) -> list[dict]:
    """Every weight row the two structures treat differently, widest first.

    `why_not` answers "what pushed the runner-up down" and is empty for 90%
    of contracts — 91% of the *contested* ones, which is exactly where a
    writer asks. The cause is structural rather than a gap in the table: a
    structure that matches an `avoids` row loses points, so it rarely
    survives to be runner-up at all. The question has no answer because the
    losers who would have answered it are not in the comparison.

    The difference between the two sets always has one. A row belongs here
    whenever the two structures score it differently, which covers three
    shapes that all separate a winner from a runner-up:

        opposite signs   time_available = low favours bluf, counts against cme
        one side only    urgency = today favours bluf, does not count for cme
        same sign        intent = escalate favours sbar more than bluf

    Dropping the third would repeat the failure this exists to fix: for 38
    of 900 contracts it is the *only* thing separating them. So the test is
    weight inequality, not sign, and the result is empty if and only if the
    two structures scored identically on identical rows — a genuine tie,
    broken by declaration order. `test_a_tie_is_the_only_empty_divergence`
    holds that line.

    Ordered by how much each row moved the gap, so a capped list shows the
    rows that decided it rather than the first three found.
    """
    b = {(n, v): w for n, v, w in best.contributions}
    r = {(n, v): w for n, v, w in runner.contributions}
    keys = list(b) + [k for k in r if k not in b]
    rows = [(k, b.get(k), r.get(k)) for k in keys if b.get(k) != r.get(k)]
    rows.sort(key=lambda row: -abs((row[1] or 0) - (row[2] or 0)))
    return [{"reason": _pair(name, value), "gloss": _gloss(name),
             "winner": bw, "runner_up": rw}
            for (name, value), bw, rw in rows[:limit]]


#: How one divergence reads as a clause about the runner-up. The key is
#: (winner's weight, runner-up's weight) reduced to signs, where `None` is
#: the structure that never mentions the fact. Data rather than a branch
#: ladder, so a new shape is a row and not an edit to the renderer.
_CLAUSES: dict[tuple[str, str], str] = {
    ("+", "0"): "does not count {pair}",
    ("-", "0"): "does not count {pair}",
    ("0", "+"): "counts {pair} on its own",
    ("0", "-"): "counts {pair} against, on its own",
    ("+", "-"): "counts {pair} against",
    ("-", "+"): "counts {pair} in favour",
    ("+", "+"): "weighs {pair} {margin}",
    ("-", "-"): "weighs {pair} {margin}",
}


def _sign(weight: int | None) -> str:
    return "0" if weight is None else "+" if weight > 0 else "-"


def divergence(row: dict) -> str:
    """One divergence as a clause about the runner-up, naming neither side.

    Both surfaces that print this have already named the two structures in
    the sentence before. Putting the names back into every row spelled
    "situation-background-assessment-recommendation" three times inside one
    clause — the same failure #46 fixed for glosses, in the same surface.
    So the frame names each side once and the row stays a predicate whose
    subject is the runner-up.
    """
    w, r = row["winner"], row["runner_up"]
    margin = ""
    if w is not None and r is not None:
        margin = "more" if abs(r) > abs(w) else "less"
    return _CLAUSES[(_sign(w), _sign(r))].format(reason=row["reason"],
                                                 pair=row["reason"],
                                                 margin=margin)


def inline(reason: dict) -> str:
    """A reason and its gloss on one line, for a renderer that wants both.

    Shared so the two list-rendering surfaces cannot drift into two
    slightly different parenthetical styles.
    """
    gloss = reason.get("gloss")
    return reason["reason"] + (f" ({gloss})" if gloss else "")


def _confidence(best: Scored, runner: Scored, contract: Contract) -> str:
    """Low whenever the selectors are mostly unknown or the top two are close.

    A structure chosen from an empty contract is a default, not a finding,
    and saying so is the difference between disclosure and bluffing.
    """
    known = sum(1 for n in STRATEGY_INPUTS if contract.is_set(n))
    if known < 3 or best.score <= 0:
        return "low"
    if best.score - runner.score <= 1:
        return "contested"
    return "high" if known >= 6 else "moderate"


def strategy_inputs() -> list[str]:
    """The fields the rules read, in contract order."""
    return [n for n in SELECTORS if n in STRATEGY_INPUTS]


def _evidence_standard(stakes: str | None) -> str:
    return {
        "low": "ordinary care; no special substantiation",
        "moderate": "name the source of any figure the reader will act on",
        "high": "every consequential claim traceable to data, log, or named owner",
        "safety_critical": "traceable claims plus verification that the reader received them",
        "crisis": "traceable claims, explicit unknowns, and a named next update",
    }.get(stakes or "low", "ordinary care; no special substantiation")


def outcome(contract: Contract) -> str:
    """A one-line fingerprint of everything the contract decides.

    Both halves of the strategy count: the structure, and whether the
    situation warrants alternatives at all. A field that leaves the
    structure alone but flips a message from "one protocol-correct
    version" to "two priced alternatives" has changed the strategy, and
    an earlier version of this module was blind to exactly that.
    """
    from .shading import candidates  # local: shading reads contracts, not strategies

    from .shading import BY_ID as SHADE_BY_ID

    structure = BY_ID[recommend(contract)["structure"]].title
    shades = candidates(contract)
    if not shades["offer"]:
        return f"{structure}, one version"
    named = " or ".join(SHADE_BY_ID[s["shade"]].title for s in shades["shades"])
    return f"{structure}, offering {named}"


def material_questions(contract: Contract, limit: int = 3) -> list[dict]:
    """The questions whose answers would change the recommended strategy.

    Candidates are the selector fields that are unset, plus the ones the
    assistant merely inferred — an inference that moves the recommendation
    is exactly the assumption a human should be given the chance to
    overturn. Everything else is left alone, however incomplete it looks.
    """
    candidates = [n for n in SELECTORS
                  if not contract.is_set(n) or contract.origin(n) == INFERRED]
    found: list[dict] = []
    for name in candidates:
        outcomes: dict[str, list[str]] = {}
        for value in BY_NAME[name].domain or ():
            outcomes.setdefault(outcome(contract.with_value(name, value)), []).append(value)
        if len(outcomes) < 2:
            continue
        found.append({
            "field": name,
            "question": BY_NAME[name].question,
            "options": list(BY_NAME[name].domain or ()),
            "status": "inferred" if contract.is_set(name) else "unknown",
            "current": contract.get(name),
            "decides_between": {k: sorted(v) for k, v in sorted(outcomes.items())},
            "why_it_matters": f"answers here split the strategy {len(outcomes)} ways",
        })
    found.sort(key=lambda q: (-len(q["decides_between"]), SELECTORS.index(q["field"])))
    return found[:limit]


def settled_fields(contract: Contract) -> list[str]:
    """Unknown selectors that would not move the strategy.

    Not the same as irrelevant: `sensitivity` can leave the structure and
    the shading offer untouched and still decide whether the evaluator
    asks for an acknowledgement. These are the fields not worth
    *interrupting* the writer for, which is a narrower claim.
    """
    unknown = set(contract.unresolved())
    asked = {q["field"] for q in material_questions(contract, limit=len(SELECTORS))}
    return sorted(unknown - asked, key=SELECTORS.index)

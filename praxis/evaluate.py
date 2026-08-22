"""Fitness for purpose, without rewriting anything.

Evaluate answers one question: is this message fit for this reader, this
outcome, this medium, and this level of stakes? It never proposes prose.
A writer who wants a second opinion and not a second draft is otherwise
unserved — every mainstream tool answers a request for feedback by
producing replacement text.

Each dimension returns one of three statuses, and the third is the one
that keeps this honest:

* ``pass`` — the property was found, and the evidence is shown.
* ``gap``  — the property was required by the contract and not found.
* ``unknown`` — the contract does not say enough to judge, or prose can
  carry the property in a way a detector cannot see.

There is deliberately no overall score. A number with no criteria behind
it invites the writer to optimise the number; a list of gaps with the
evidence attached invites them to fix the message.
"""

from dataclasses import dataclass, asdict
from . import signals
from .contract import Contract
from .metrics import metrics
from .rules import split_sentences

PASS, GAP, UNKNOWN = "pass", "gap", "unknown"

#: Intents where the reader is expected to *do* something. The bar for
#: outcome clarity and actionability is higher here.
ACTION_INTENTS = frozenset({"request", "recommend", "escalate", "warn", "correct"})
#: Structures that put the conclusion first, and so can be checked by
#: looking at the opening alone.
CONCLUSION_FIRST = frozenset({"bluf", "pyramid", "hazard_first", "sia", "prep"})
#: Structures that deliberately withhold the conclusion until context lands.
CONTEXT_FIRST = frozenset({"cme", "scqa", "repair", "reassure"})

#: Words at which a medium starts costing the reader more than it should.
MEDIUM_BUDGET = {"slack": 150, "email": 400, "memo": 900, "handoff": 250}


@dataclass
class Finding:
    dimension: str
    question: str
    status: str
    finding: str
    evidence: list[str]
    recommendation: str = ""
    short: str = ""
    """A few words naming the gap, for the one-line answer.

    Written here rather than derived by the caller from `dimension`,
    because only this code knows *which* thing was missing — an
    actionability gap is "no deadline" or "no owner" depending on the
    draft, and a mapping table elsewhere would drift the moment a branch
    changed."""


def _list(items: list[str]) -> str:
    """Join for prose: "a", "a or b", "a, b, or c"."""
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return " or ".join(items)
    return f"{', '.join(items[:-1])}, or {items[-1]}"


def _f(dimension, question, status, finding, evidence=(), recommendation="", short="") -> Finding:
    return Finding(dimension, question, status, finding, list(evidence), recommendation, short)


def evaluate(text: str, contract: Contract, structure: str | None = None) -> dict:
    """Score `text` against `contract` on ten dimensions, with evidence."""
    m = metrics(text)
    found = {name: signals.find(name, text) for name in signals.DETECTORS}
    intent = contract.get("intent")
    stakes = contract.get("stakes")
    high_stakes = stakes in ("high", "safety_critical", "crisis")

    findings = [
        _outcome_clarity(found, intent),
        _audience_fit(m, contract, found),
        _structural_fit(text, found, structure),
        _evidence_fit(text, stakes),
        _uncertainty_integrity(found, contract, high_stakes),
        _risk_calibration(found, stakes),
        _relationship_fit(found, contract),
        _medium_fit(m, contract),
        _voice_integrity(),
        _actionability(found, intent),
    ]

    counts = {PASS: 0, GAP: 0, UNKNOWN: 0}
    for f in findings:
        counts[f.status] += 1
    priority = [f.dimension for f in findings if f.status == GAP]

    return {
        "dimensions": [asdict(f) for f in findings],
        "summary": counts,
        "priority": priority,
        "verdict": _verdict(counts, high_stakes),
        "note": "Detectors are conservative. 'unknown' means not machine-checkable here, "
                "not absent — a human still reads the draft.",
    }


def _verdict(counts: dict, high_stakes: bool) -> str:
    if counts[GAP] == 0:
        return "no gaps found against this contract"
    if high_stakes and counts[GAP]:
        return f"{counts[GAP]} gap(s) at raised stakes — resolve before sending"
    return f"{counts[GAP]} gap(s) to consider"


def _outcome_clarity(found, intent) -> Finding:
    q = "Is the intended reader action, decision, or understanding explicit?"
    if found["ask"]:
        return _f("outcome_clarity", q, PASS, "The draft states a request of the reader.",
                  found["ask"][:3])
    if intent in ACTION_INTENTS:
        return _f("outcome_clarity", q, GAP,
                  f"The intent is '{intent}' but no request of the reader was found.",
                  [], "State the one thing the reader must do, in its own sentence.",
                  "no request of the reader")
    return _f("outcome_clarity", q, UNKNOWN,
              "No explicit ask, which may be correct for this intent; whether the takeaway "
              "lands is a judgment about the prose.")


def _audience_fit(m, contract, found) -> Finding:
    q = "Does the message fit the reader's knowledge, authority, and available time?"
    time_available = contract.get("time_available")
    if not time_available:
        return _f("audience_fit", q, UNKNOWN, "The contract does not say how much attention the reader has.")
    if time_available == "low" and m["words"] > 200:
        return _f("audience_fit", q, GAP,
                  f"The reader has little time and the draft runs {m['words']} words"
                  + (" with no scannable structure." if not found["scan"] else "."),
                  [f"{m['words']} words", f"{m['sentences']} sentences"],
                  "Cut to the decision path, or add headings and short blocks so it can be scanned.",
                  f"{m['words']} words for a reader with little time")
    return _f("audience_fit", q, PASS,
              f"{m['words']} words suits a reader with {time_available} available attention.",
              [f"{m['words']} words"])


def _structural_fit(text, found, structure) -> Finding:
    q = "Does the information order serve the reader's task?"
    if not structure:
        return _f("structural_fit", q, UNKNOWN, "No structure was recommended for this contract.")
    opening = signals.first_words(text, 40)
    lead = signals.first_words(text, 15)
    if structure in CONCLUSION_FIRST:
        if signals.find("ask", opening) or signals.find("consequential", opening):
            return _f("structural_fit", q, PASS,
                      f"The opening carries the point, as {structure} requires.", [opening[:160]])
        return _f("structural_fit", q, GAP,
                  f"{structure} puts the conclusion first; the opening is background.",
                  [opening[:160]], "Move the request or the consequence into the first sentence.",
                  "the point is not in the opening")
    if structure in CONTEXT_FIRST:
        if signals.find("ask", lead):
            return _f("structural_fit", q, GAP,
                      f"{structure} builds context before the ask; the ask is in the first line.",
                      [lead], "Let the situation land before the request.",
                      "the ask lands before the context")
        return _f("structural_fit", q, PASS,
                  f"The opening establishes context, as {structure} requires.", [lead])
    return _f("structural_fit", q, UNKNOWN,
              f"Order for {structure} is not machine-checkable from the opening alone.")


def _evidence_fit(text, stakes) -> Finding:
    q = "Are consequential claims supported at the required standard?"
    sentences = [s for _, _, s in split_sentences(text)] or [text]
    unsupported = []
    for i, sentence in enumerate(sentences):
        if not signals.find("consequential", sentence):
            continue
        window = sentence + " " + (sentences[i + 1] if i + 1 < len(sentences) else "")
        if not signals.find("evidence", window):
            unsupported.append(sentence.strip()[:140])
    claims = [s for s in sentences if signals.find("consequential", s)]
    if not claims:
        # No claim was recognised, which is not the same as there being
        # none. Reporting `pass` here told a high-stakes draft its claims
        # were all supported on the strength of a detector finding nothing.
        return _f("evidence_fit", q, UNKNOWN,
                  "No consequential claim was recognised. That is a limit of the detector, "
                  "not a finding that the draft makes none.",
                  [], "Check by eye that any claim the reader will act on carries its support.")
    if not unsupported:
        return _f("evidence_fit", q, PASS,
                  f"All {len(claims)} consequential claim(s) sit near visible support.")
    if stakes in ("high", "safety_critical", "crisis"):
        return _f("evidence_fit", q, GAP,
                  f"{len(unsupported)} consequential claim(s) carry no figure, source, or reference.",
                  unsupported[:3], "Attach the number, log, or owner that makes each claim checkable.",
                  f"{len(unsupported)} unsupported claim(s)")
    return _f("evidence_fit", q, UNKNOWN,
              f"{len(unsupported)} claim(s) are unsupported; at {stakes or 'unstated'} stakes that "
              "may be acceptable.", unsupported[:3])


def _uncertainty_integrity(found, contract, high_stakes) -> Finding:
    q = "Are assumptions, estimates, and confidence limits visible?"
    declared = contract.get("uncertainty")
    if declared and not found["uncertainty"]:
        return _f("uncertainty_integrity", q, GAP,
                  "The contract records something still uncertain; the draft reads as settled.",
                  [str(declared)], "Mark what is estimated or pending where the claim is made.",
                  "reads as settled when it is not")
    if found["uncertainty"]:
        return _f("uncertainty_integrity", q, PASS,
                  "The draft distinguishes what is known from what is not.", found["uncertainty"][:3])
    if high_stakes:
        return _f("uncertainty_integrity", q, GAP,
                  "Nothing is marked estimated or unknown; at this level of stakes total "
                  "confidence is itself a claim.",
                  [], "State the confidence on any figure the reader will act on.",
                  "nothing marked uncertain")
    return _f("uncertainty_integrity", q, UNKNOWN, "No uncertainty markers, and none required here.")


def _risk_calibration(found, stakes) -> Finding:
    q = "Do precision, verification, and escalation match the consequences?"
    if not stakes:
        return _f("risk_calibration", q, UNKNOWN, "The contract does not state the stakes.")
    if stakes in ("low", "moderate"):
        return _f("risk_calibration", q, PASS, f"No verification machinery required at {stakes} stakes.")

    # What each tier owes, mirroring strategy.REQUIREMENTS. Checking only
    # owner and verification at every raised tier meant a crisis message
    # with no named next update, and a safety-critical one with no
    # escalation path, both passed — while `requirements()` told the
    # writer those were mandatory.
    required = {
        "high": ("owner", "verification"),
        "safety_critical": ("owner", "verification", "escalation"),
        "crisis": ("owner", "verification", "update_cadence"),
    }[stakes]
    missing = [n for n in required if not found[n]]
    if missing:
        return _f("risk_calibration", q, GAP,
                  f"At {stakes} stakes the draft lacks: {', '.join(n.replace('_', ' ') for n in missing)}.",
                  [span for n in required for span in found[n][:1]],
                  "Name who acts, how they confirm receipt, and "
                  + ("what to do if it is not resolved." if "escalation" in missing
                     else "when the next update comes." if "update_cadence" in missing
                     else "by when."),
                  f"no {_list([n.replace('_', ' ') for n in missing])}")
    return _f("risk_calibration", q, PASS,
              f"{', '.join(n.replace('_', ' ') for n in required)} all present, "
              f"as {stakes} stakes require.",
              [span for n in required for span in found[n][:1]])


def _relationship_fit(found, contract) -> Finding:
    q = "Is the stance appropriately direct, respectful, and accountable?"
    sensitivity = contract.get("sensitivity")
    upward = contract.get("power_distance") == "upward"
    if sensitivity == "high" and not found["acknowledgement"]:
        return _f("relationship_fit", q, GAP,
                  "The contract marks this relationship as sensitive; nothing in the draft "
                  "acknowledges the reader.", [],
                  "Acknowledge the reader's position once, without softening the ask.",
                  "no acknowledgement of the reader")
    if upward and len(found["hedge"]) >= 2:
        return _f("relationship_fit", q, GAP,
                  f"Writing upward with {len(found['hedge'])} hedges around the ask; deference "
                  "here reads as uncertainty about the request itself.",
                  found["hedge"][:3], "Keep the courtesy, drop the hedges on the ask itself.",
                  f"{len(found['hedge'])} hedges around the ask")
    if not sensitivity:
        return _f("relationship_fit", q, UNKNOWN, "The contract does not describe the relationship.")
    return _f("relationship_fit", q, PASS, f"Stance is consistent with {sensitivity} sensitivity.",
              found["acknowledgement"][:2])


def _medium_fit(m, contract) -> Finding:
    q = "Does the format fit the channel it will be read in?"
    medium = contract.get("medium")
    limit = contract.get("length_limit")
    if isinstance(limit, int) and m["words"] > limit:
        return _f("medium_fit", q, GAP, f"{m['words']} words against a stated limit of {limit}.",
                  [f"{m['words']} words"], f"Cut {m['words'] - limit} words.",
                  f"{m['words']} words against a {limit}-word limit")
    if not medium:
        return _f("medium_fit", q, UNKNOWN, "The contract does not name the medium.")
    budget = MEDIUM_BUDGET.get(medium)
    if budget and m["words"] > budget:
        return _f("medium_fit", q, GAP,
                  f"{m['words']} words is long for {medium} (comfortable at about {budget}).",
                  [f"{m['words']} words"], f"Trim toward {budget} words, or move detail to an attachment.",
                  f"{m['words']} words is long for {medium}")
    return _f("medium_fit", q, PASS, f"{m['words']} words suits {medium}.", [f"{m['words']} words"])


def _voice_integrity() -> Finding:
    return _f("voice_integrity", "Does the writing remain recognisably the author's?", UNKNOWN,
              "Voice is checked by comparing a variant to the author's own draft; there is no "
              "base text in an evaluate-only run.",
              [], "Run this as a transform to get a voice comparison.")


def _actionability(found, intent) -> Finding:
    # Scoped to the ask and the deadline. Owner and confirmation are real
    # requirements but they are stakes-dependent, and `risk_calibration`
    # already owns them — asking for them here reported a gap on every
    # ordinary low-stakes message, or (as it did) passed a draft while the
    # dimension's own question named four things it had not checked.
    q = "Is the next action clear, and is it bounded by a deadline?"
    present = [n for n in ("ask", "owner", "deadline", "verification") if found[n]]
    missing = [n for n in ("ask", "owner", "deadline", "verification") if not found[n]]
    if intent in ACTION_INTENTS and {"ask", "deadline"} & set(missing):
        return _f("actionability", q, GAP,
                  f"Present: {', '.join(present) or 'none'}. Missing: {', '.join(missing)}.",
                  [found[n][0] for n in present if found[n]][:3],
                  "An action without a deadline is a suggestion; add both.",
                  f"no {_list(missing)}")
    if len(present) >= 2:
        note = f"Present: {', '.join(present)}."
        if missing:
            note += (f" Not detected: {', '.join(missing)}"
                     + (" — risk_calibration decides whether that matters here."
                        if {"owner", "verification"} & set(missing) else "."))
        return _f("actionability", q, PASS, note,
                  [found[n][0] for n in present if found[n]][:3])
    return _f("actionability", q, UNKNOWN,
              f"Only {', '.join(present) or 'none'} detected, which may suit intent '{intent}'.")

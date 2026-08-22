"""Surgical changes: what to change, where, and what may not be touched.

Evaluate says a message has no deadline. Transform says the deadline goes
after the request on line three, that the sentence beginning "We found a
defect" belongs at the top, and that the eleven characters spelling
"3 p.m." are not available to be rewritten.

The engine still writes nothing. An edit carries a *kind*, a *place*, and
an instruction describing what the new text has to accomplish — never the
text itself. That division is the same one the whole layer rests on: the
client's model writes, praxis decides and audits.

Every edit is checked against the protected spans before it is offered.
Proposing a change that would overwrite content the writer declared
untouchable is a worse failure than proposing nothing, so an edit that
collides is reported as blocked rather than quietly dropped — the writer
should see that their own constraints are in tension with the advice.
"""

from dataclasses import dataclass, asdict, field

from . import spans
from .contract import Contract
from .evaluate import claims
from .spans import Span

#: Imported rather than restated. A copy here would silently disagree
#: with the evaluator the first time a structure was added to one set and
#: not the other, and the two decide the same property.
from .evaluate import CONCLUSION_FIRST  # noqa: E402  (documented import)

KINDS = ("insert", "revise", "move", "cut")

#: Gaps one edit legitimately answers on another's behalf. For a
#: conclusion-first structure with no request in the draft, "state the
#: action at the top" *is* the structural fix and *is* where the deadline
#: goes — three edits at the same offset would be one instruction split
#: into three. Recorded as data so a gap covered this way is reported as
#: folded rather than as unaddressed, which are very different things.
FOLDS_INTO = {"actionability": "outcome_clarity", "structural_fit": "outcome_clarity"}


@dataclass
class Edit:
    """One located change, and the constraint it must respect."""
    kind: str
    dimension: str
    instruction: str
    at: int | None = None
    where: dict | None = None
    blocked_by: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def transform(draft: str, contract: Contract, structure: str | None,
              evaluation: dict) -> dict:
    """Locate every gap the evaluation found, as an edit against the draft."""
    protected = spans.protected_spans(draft, contract.protected_strings())
    gaps = {d["dimension"]: d for d in evaluation["dimensions"] if d["status"] == "gap"}
    body = spans.body_start(draft)
    end = len(draft)

    edits: list[Edit] = []
    unaddressed: list[str] = []
    folded: dict[str, str] = {}
    for dimension, finding in gaps.items():
        builder = _BUILDERS.get(dimension)
        produced = builder(draft, contract, structure, finding, body, end, gaps) \
            if builder else []
        if produced:
            edits.extend(produced)
        else:
            unaddressed.append(dimension)

    # A gap with no edit is the failure this mode exists to avoid, so
    # separate the ones another edit answers from the ones nothing does.
    covering = {e.dimension for e in edits}
    for dimension in list(unaddressed):
        owner = FOLDS_INTO.get(dimension)
        if owner and owner in covering:
            folded[dimension] = owner
            unaddressed.remove(dimension)

    for edit in edits:
        region = _region(edit, draft)
        if region:
            edit.blocked_by = [p.to_dict() for p in protected if region.overlaps(p)]

    return {
        "edits": [e.to_dict() for e in edits],
        "protected": spans.to_dicts(protected),
        "unlocatable": spans.unlocatable(draft, contract.protected_strings()),
        "blocked": sum(1 for e in edits if e.blocked_by),
        "no_edit_for": unaddressed,
        "folded_into": folded,
        "note": "Instructions describe what the new text must do. praxis does not "
                "write it; nothing here is prose.",
    }


def _region(edit: Edit, draft: str) -> Span | None:
    """The characters an edit would disturb, for the protection check.

    An insertion disturbs nothing, but it still has to land somewhere
    legal: a zero-width span at the insertion point catches the case where
    the offset falls in the middle of a protected phrase.
    """
    if edit.where:
        return Span(edit.where["start"], edit.where["end"], edit.where["text"])
    if edit.at is not None:
        return Span(edit.at, edit.at, "")
    return None


def _edit(kind, dimension, instruction, at=None, where: Span | None = None) -> Edit:
    return Edit(kind=kind, dimension=dimension, instruction=instruction, at=at,
                where=where.to_dict() if where else None)


def _outcome_clarity(draft, contract, structure, finding, body, end, gaps):
    where = "in its own sentence at the top" if structure in CONCLUSION_FIRST else \
            "once the situation has landed"
    # When there is no request at all, the deadline has nothing to sit
    # beside, so it belongs in this instruction rather than in a second
    # edit pointing at the same offset and referring to a request that
    # does not exist yet.
    also = ("" if spans.locate("ask", draft) or "actionability" not in gaps
            else " Include the time by which it must happen.")
    return [_edit("insert", "outcome_clarity",
                  f"State the single action the reader must take, {where}. "
                  f"Name the actor and the action; do not describe the situation again.{also}",
                  at=body if structure in CONCLUSION_FIRST else end)]


def _actionability(draft, contract, structure, finding, body, end, gaps):
    # The end of the *sentence* carrying the request, not the end of the
    # detector match: `locate("ask")` on "Please approve the request."
    # ends after "approve", and inserting there splits the request from
    # its object — "Please approve by 3 p.m. the request."
    carriers = spans.carrying(draft, "ask")
    if "deadline" not in finding["short"] or not carriers:
        # No ask to attach it to: `_outcome_clarity` carries the deadline
        # into the sentence it is asking the writer to add.
        return []
    sentence = carriers[-1]
    at = sentence.end - 1 if sentence.text.endswith((".", "!", "?")) else sentence.end
    return [_edit("insert", "actionability",
                  "Add the time by which the action must happen, at the end of the "
                  "request itself rather than at the end of the message.", at=at)]


def _structural_fit(draft, contract, structure, finding, body, end, gaps):
    if structure not in CONCLUSION_FIRST:
        asks = spans.carrying(draft, "ask")
        return [_edit("move", "structural_fit",
                      f"{structure} builds context before the request. Move this "
                      "sentence below the situation it depends on.",
                      where=asks[0])] if asks else []
    carriers = spans.carrying(draft, "ask") or spans.carrying(draft, "consequential")
    if not carriers:
        # Nothing in the draft states the point, so there is nothing to
        # move: it has to be written. When outcome_clarity is already
        # asking for exactly that sentence at exactly this offset, this
        # folds into it rather than duplicating it.
        if "outcome_clarity" in gaps:
            return []
        return [_edit("insert", "structural_fit",
                      f"{structure} leads with the point, and no sentence in the draft "
                      "states it. Write the conclusion first, then let the background "
                      "follow.", at=body)]
    return [_edit("move", "structural_fit",
                  f"{structure} leads with the point. Move this sentence to the top "
                  "of the message, before the background.",
                  where=carriers[0])]


def _relationship_fit(draft, contract, structure, finding, body, end, gaps):
    if "hedge" in finding["short"]:
        return [_edit("revise", "relationship_fit",
                      "Remove this hedge. Keep the courtesy in the acknowledgement, "
                      "not in the request.", where=hedge)
                for hedge in spans.locate("hedge", draft)]
    return [_edit("insert", "relationship_fit",
                  "Acknowledge the reader's position once, before the request. One "
                  "sentence, specific to their situation, and it must not soften the ask.",
                  at=body)]


def _evidence_fit(draft, contract, structure, finding, body, end, gaps):
    _, unsupported = claims(draft)
    # Consumed in document order. Taking `found[0]` every time emitted two
    # edits against the first occurrence of a repeated sentence and none
    # against the second, so one reported gap pointed at the wrong place.
    remaining = list(spans.sentences(draft))
    located = []
    for sentence in unsupported:
        match = next((s for s in remaining if s.text.strip() == sentence.strip()), None)
        if match is None:
            continue
        remaining.remove(match)
        located.append(_edit("revise", "evidence_fit",
                             "Attach the figure, log, or named source that makes this "
                             "claim checkable, or state that it is an estimate.",
                             where=match))
    return located


def _uncertainty_integrity(draft, contract, structure, finding, body, end, gaps):
    declared = contract.get("uncertainty")
    detail = f" The contract records: {declared}." if declared else ""
    return [_edit("insert", "uncertainty_integrity",
                  "Mark what is still estimated or pending, at the point the claim is "
                  f"made rather than in a closing caveat.{detail}", at=body)]


def _risk_calibration(draft, contract, structure, finding, body, end, gaps):
    wanted = {"owner": "Name who is doing the work.",
              "verification": "Say how the reader confirms they received this — a "
                              "reply, an approval, or a read-back.",
              "escalation": "Give the route if this is not resolved: who to reach, "
                            "and when.",
              "update cadence": "Name the time of the next update, not just that one "
                                "is coming."}
    return [_edit("insert", "risk_calibration", instruction, at=end)
            for name, instruction in wanted.items() if name in finding["short"]]


def _too_long(dimension):
    def build(draft, contract, structure, finding, body, end, gaps):
        return [_edit("cut", dimension,
                      "Cut or split this sentence; it is among the longest in a draft "
                      "that is over its budget.", where=sentence)
                for sentence in spans.longest_sentences(draft, 3)]
    return build


_BUILDERS = {
    "outcome_clarity": _outcome_clarity,
    "actionability": _actionability,
    "structural_fit": _structural_fit,
    "relationship_fit": _relationship_fit,
    "evidence_fit": _evidence_fit,
    "uncertainty_integrity": _uncertainty_integrity,
    "risk_calibration": _risk_calibration,
    "audience_fit": _too_long("audience_fit"),
    "medium_fit": _too_long("medium_fit"),
}

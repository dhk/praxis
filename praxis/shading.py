"""Shading: bounded exploration of communication strategy, with proof.

A shade is a named, deliberate change to *how* a message works on a
reader — its order, its directness, its evidence visibility — applied to
a message whose substance does not move. The product claim is easy to
make and hard to keep: warmer must never mean less truthful, shorter must
never mean the caveat is gone. This module is where that claim is made
checkable.

Three things happen here.

`candidates` decides whether variants are warranted at all. The default
in this codebase is *one* version. Alternatives appear only where the
contract contains a real tension — urgency pulling against a fragile
relationship, defensibility against a reader with no time — and they are
suppressed outright where a protocol already decides the shape. Two
alternatives, never more.

`invariants` extracts what may not move, in two kinds. Verbatim
invariants (figures, links, commitments, the writer's protected strings)
must appear byte-identically. Presence invariants (there is an ask, a
deadline, an owner, a confirmation) must still be *there*, though the
wording is free to change — requiring an ask to survive rephrasing
verbatim would forbid the very rewriting shading exists to do.

`check` runs a variant against them and returns violations plus a
difference map. The difference map is what turns a rewriter into an
instrument: it says what moved, what was deliberately left alone, and
where the variant failed to be the shade it claims to be.
"""

from dataclasses import dataclass
import difflib
from . import signals
from .contract import Contract
from .metrics import metrics
from .validation import protected_tokens

MAX_ALTERNATIVES = 2


@dataclass(frozen=True)
class Shade:
    """One rhetorical texture, and the price it charges."""
    id: str
    title: str
    behaviour: str
    tradeoff: str
    expects: tuple[tuple[str, str], ...]  # (detector, "more" | "fewer")


SHADES: tuple[Shade, ...] = (
    Shade("neutral", "Neutral", "Direct and compact, with minimal interpersonal framing.",
          "Reads as efficient to a reader who is fine, and as cold to one who is not.",
          (("hedge", "fewer"),)),
    Shade("warm", "Warm",
          "Acknowledge the reader's effort or position before the substance; collaborative framing without false intimacy.",
          "Lowers defensiveness; spends words and can soften the outline of the ask.",
          (("acknowledgement", "more"),)),
    Shade("reassuring", "Reassuring",
          "State what is known, what is not, what is being done, and when the next update comes.",
          "Steadies a worried reader; can read as slower to act than the writer is.",
          (("uncertainty", "more"), ("verification", "more"))),
    Shade("decisive", "Decisive",
          "Lead with the conclusion, the requested action, the deadline, and the consequence.",
          "Shortest path to a decision; leaves the reader less room to reach it themselves.",
          (("ask", "more"), ("deadline", "more"), ("hedge", "fewer"))),
    Shade("evidence_forward", "Evidence-forward",
          "Make claims, sources, confidence, and caveats visible at the point of the claim.",
          "Survives scrutiny; heavier to read and slower to act on.",
          (("evidence", "more"), ("uncertainty", "more"))),
    Shade("scan_first", "Scan-first",
          "Headline, short blocks, descriptive labels, explicit action — built to be found, not read.",
          "Findable under interruption; loses the connective reasoning between points.",
          (("scan", "more"),)),
    Shade("teaching", "Teaching-oriented",
          "Context, causal explanation, worked example, and a check for understanding.",
          "Builds a model the reader keeps; costs their attention now.",
          (("evidence", "more"),)),
    Shade("repairing", "Relationship-repairing",
          "Acknowledge impact, take responsibility where warranted, name the repair, then the substance.",
          "Restores the relationship; postpones the business of the message.",
          (("acknowledgement", "more"),)),
)

BY_ID = {s.id: s for s in SHADES}

#: Tensions in the contract that make two shades genuinely different
#: choices rather than two flavours of the same one. Each row is
#: (predicate over the contract, shade a, shade b, what is being traded).
_TENSIONS: tuple[tuple[dict, str, str, str], ...] = (
    ({"urgency": ("today", "immediate"), "sensitivity": ("moderate", "high")},
     "decisive", "warm",
     "the deadline pulls toward bluntness; the relationship pulls the other way"),
    ({"stakes": ("high",), "time_available": ("low",)},
     "evidence_forward", "scan_first",
     "the claim needs support the reader has no time to read"),
    ({"intent": ("warn",)},
     "decisive", "reassuring",
     "lead with the protective action, or with the whole picture"),
    ({"intent": ("repair",)},
     "repairing", "neutral",
     "repair the relationship first, or get to the substance first"),
    ({"intent": ("reassure",)},
     "reassuring", "evidence_forward",
     "steadiness against full disclosure of what is still unknown"),
    ({"prior_knowledge": ("none",), "authority": ("decides", "approves")},
     "scan_first", "teaching",
     "a reader who must decide now against one who must understand"),
    ({"power_distance": ("upward",), "intent": ("request", "escalate")},
     "decisive", "warm",
     "asking upward: clarity of the ask against deference"),
)

#: Situations where a menu of options is the wrong answer. Ordered — the
#: first match wins, so the strongest reason is the one reported.
_SUPPRESSORS: tuple[tuple[dict, str], ...] = (
    ({"stakes": ("safety_critical", "crisis")},
     "at this level of stakes the structure is a protocol, not a preference; "
     "one protocol-correct version is safer than a menu"),
    ({"intent": ("request",), "stakes": ("low",)},
     "the ask is simple and unambiguous; alternatives would differ cosmetically"),
)


def rule_fields() -> set[str]:
    """Every contract field the shading rules actually read.

    Derived rather than listed, so a new tension cannot quietly add an
    input that the confidence calculation and `schema()` still think is
    decorative.
    """
    fields: set[str] = set()
    for rule, *_ in _TENSIONS:
        fields |= set(rule)
    for rule, _ in _SUPPRESSORS:
        fields |= set(rule)
    return fields


def _matches(rule: dict, contract: Contract) -> bool:
    return all(contract.get(field) in allowed for field, allowed in rule.items())


def candidates(contract: Contract) -> dict:
    """Whether to offer alternatives here, which ones, and why.

    Returns `offer: False` with a reason far more often than product
    instinct suggests it should. That is the point: unbounded variation
    is choice overload wearing the costume of helpfulness.
    """
    for rule, reason in _SUPPRESSORS:
        if _matches(rule, contract):
            return {"offer": False, "reason": reason, "shades": []}

    picked: list[dict] = []
    seen: set[str] = set()
    for rule, first, second, tension in _TENSIONS:
        if not _matches(rule, contract):
            continue
        for shade_id in (first, second):
            if shade_id in seen or len(picked) >= MAX_ALTERNATIVES:
                continue
            seen.add(shade_id)
            picked.append({"shade": shade_id, "title": BY_ID[shade_id].title,
                           "behaviour": BY_ID[shade_id].behaviour,
                           "tradeoff": BY_ID[shade_id].tradeoff, "tension": tension})
        if len(picked) >= MAX_ALTERNATIVES:
            break

    if not picked:
        return {"offer": False,
                "reason": "the contract contains no competing objectives; a second version "
                          "would differ in wording, not in strategy",
                "shades": []}
    return {"offer": True,
            "reason": "the contract contains a genuine tradeoff the writer should see priced",
            "shades": picked}


PRESENCE_INVARIANTS = ("ask", "deadline", "owner", "verification")


def invariants(base: str, contract: Contract) -> dict:
    """What must survive every variant of `base`.

    Verbatim content splits into two kinds that must be *checked*
    differently, even though a reader sees one list:

    * **tokens** — figures, percentages, links, bracketed references and
      citation years, found by the same extraction on both sides and
      compared as sets. Substring containment is not good enough here and
      the difference is not academic: `"40%" in "Costs rose 140%"` is
      true, so a substring check certified a changed figure as preserved.
      That is the one guarantee this product is sold on.
    * **phrases** — strings the writer declared protected. These are
      free-form ("without prejudice"), so containment is exactly right:
      the phrase must appear, and the surrounding wording may move.

    Presence invariants are the structural commitments — that an ask
    exists at all, that a deadline exists at all — whose wording may
    change freely.
    """
    tokens = sorted(protected_tokens(base))
    phrases = contract.protected_strings()
    present = {name: signals.find(name, base) for name in PRESENCE_INVARIANTS}
    return {
        "verbatim": sorted(set(tokens) | set(phrases)),
        "tokens": tokens,
        "phrases": phrases,
        "presence": {k: v for k, v in present.items() if v},
        "uncertainty_markers": signals.find("uncertainty", base),
        "note": "Verbatim tokens are compared byte-for-byte. Presence invariants must "
                "still be detectable after rewriting, in any wording.",
    }


def check(source: str, variant: str, contract: Contract, shade: str | None = None,
          compare_to: str | None = None, compare_label: str = "the source",
          source_label: str = "the source") -> dict:
    """Validate one variant and return its difference map.

    Two references, deliberately separate, because they answer different
    questions.

    `source` supplies the invariants — it is where the protected content
    and the commitments came from, so it is the writer's own draft
    whenever there is one. Losing a figure is measured against the truth,
    not against another rewrite.

    `compare_to` is what the difference map is measured against, and
    defaults to `source`. For an alternative it should be the
    **recommended version**, not the original draft: the writer is
    choosing between the recommendation and the alternative, and "how
    does this differ from the one I would otherwise send" is the question
    they are actually asking. Diffing both against the draft answers a
    question nobody asked and buries the distinction between them.
    """
    reference = source if compare_to is None else compare_to
    inv = invariants(source, contract)
    # Violations are measured against `source` and the difference map
    # against `reference`. When those differ, a bare count reads as a
    # contradiction — "uncertainty fell from 5 to 3" sitting above
    # "uncertainty unchanged (3)" — so every violation names its own
    # reference rather than leaving the reader to guess.
    violations: list[dict] = []

    kept = protected_tokens(variant)
    missing = sorted(set(inv["tokens"]) - kept
                     | {p for p in inv["phrases"] if p not in variant})
    if missing:
        violations.append({
            "kind": "content_loss", "severity": "block",
            "detail": f"protected content from {source_label} is absent from this version",
            "items": missing})

    lost = [name for name, found in inv["presence"].items() if found and not signals.find(name, variant)]
    if lost:
        violations.append({
            "kind": "commitment_loss", "severity": "block",
            "detail": f"{source_label} states these and this version no longer does",
            "items": lost})

    base_unc, variant_unc = len(inv["uncertainty_markers"]), len(signals.find("uncertainty", variant))
    if base_unc and not variant_unc:
        violations.append({
            "kind": "uncertainty_loss", "severity": "block",
            "detail": f"every marker of what is not yet known in {source_label} was "
                      "removed; a shorter or warmer version may not become a more "
                      "certain one",
            "items": inv["uncertainty_markers"]})
    elif base_unc and variant_unc < base_unc:
        violations.append({
            "kind": "uncertainty_reduced", "severity": "review",
            "detail": f"against {source_label}, markers of uncertainty fell from "
                      f"{base_unc} to {variant_unc}; confirm the message still claims "
                      "only what is known",
            "items": inv["uncertainty_markers"]})

    return {
        "status": "fail" if any(v["severity"] == "block" for v in violations)
                  else ("review" if violations else "pass"),
        "violations": violations,
        "difference_map": difference_map(reference, variant, shade, compare_label),
    }


def _direction_met(direction: str, before: int, after: int) -> bool:
    """Did the count move the way the shade promises?

    "fewer" against a base of zero is already satisfied — there was
    nothing to remove. Scoring that as a failure would report every
    hedge-free draft as a botched Decisive variant.
    """
    if direction == "fewer":
        return after < before or before == 0
    return after > before


def difference_map(base: str, variant: str, shade: str | None = None,
                   compared_to: str = "the source") -> dict:
    """What changed, what stayed, and whether the shade did what it claims.

    `compared_to` names the reference in the result so a reader is never
    left guessing whether a delta is measured against their own draft or
    against the recommended version — the same numbers mean different
    things under each.

    Shade fidelity is reported, never enforced. A variant can be good
    prose and a bad example of the shade it was labelled with, and
    conflating those two failures helps nobody.
    """
    bm, vm = metrics(base), metrics(variant)
    bs, vs = signals.signal_counts(base), signals.signal_counts(variant)

    moved: list[str] = []
    held: list[str] = []
    for name in sorted(bs):
        delta = vs[name] - bs[name]
        label = name.replace("_", " ")
        if delta:
            moved.append(f"{label}: {bs[name]} → {vs[name]}")
        elif bs[name]:
            held.append(f"{label} unchanged ({bs[name]})")

    base_open, variant_open = signals.first_words(base, 12), signals.first_words(variant, 12)
    fidelity: list[dict] = []
    if shade and shade in BY_ID:
        for detector, direction in BY_ID[shade].expects:
            met = _direction_met(direction, bs[detector], vs[detector])
            fidelity.append({"expected": f"{direction} {detector}", "met": met,
                             "observed": f"{bs[detector]} → {vs[detector]}"})

    return {
        "shade": shade,
        "compared_to": compared_to,
        "opening_changed": base_open.lower() != variant_open.lower(),
        "opening": {"before": base_open, "after": variant_open},
        "length": {"words_before": bm["words"], "words_after": vm["words"],
                   "delta_words": vm["words"] - bm["words"],
                   "sentences_before": bm["sentences"], "sentences_after": vm["sentences"]},
        "moved": moved,
        "held": held,
        "shade_fidelity": fidelity,
        "similarity": round(difflib.SequenceMatcher(None, base.split(), variant.split()).ratio(), 3),
    }

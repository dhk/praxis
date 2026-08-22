"""Wave 2: located changes, protected regions, and voice habits.

The theme is that a critique and a surgical change are different
artefacts. Evaluate can say a message has no deadline; transform has to
say where the deadline goes and which characters are not available to be
rewritten. Everything here is about positions and what may not move.
"""

import pytest

from praxis import spans, voice
from praxis.contract import build
from praxis.design import MODES, design
from praxis.evaluate import claims, evaluate
from praxis.spans import Span
from praxis.strategy import recommend
from praxis.transform import transform

DRAFT = ("Hi Priya,\n\nWe reviewed the release plan and found an issue with how record "
         "IDs are remapped, which we think could affect the cutover. It is possible this "
         "pushes the release out somewhat, and we may need additional engineering "
         "support.\n\nHappy to walk through the details — perhaps we could\ndiscuss the "
         "implications at our next meeting if that works for you.\n\nThanks,\nSam")
CONTRACT = {"intent": "request", "stakes": "high", "time_available": "low",
            "medium": "email", "sensitivity": "high", "power_distance": "upward"}


def _transform(values=None, draft=DRAFT):
    contract = build({**CONTRACT, **(values or {})})
    structure = recommend(contract)["structure"]
    return transform(draft, contract, structure,
                     evaluate(draft, contract, structure))


# --- locating ---------------------------------------------------------

def test_spans_agree_with_the_detector_they_come_from():
    """`locate` and `find` must never disagree about what matched."""
    from praxis import signals
    for name in signals.DETECTORS:
        located = [s.text for s in spans.locate(name, DRAFT)]
        found = [f for f in signals.find(name, DRAFT)]
        assert [t.strip() for t in located] == found, name


def test_a_span_covers_the_text_it_claims_to():
    for span in spans.locate("hedge", DRAFT):
        assert DRAFT[span.start:span.end] == span.text


def test_the_insertion_point_clears_the_salutation():
    """A bottom line goes below "Hi Priya,", not above it."""
    assert DRAFT[spans.body_start(DRAFT):].startswith("We reviewed")
    assert spans.body_start("Straight into it, no greeting.") == 0


def test_overlap_is_half_open():
    assert not Span(0, 5, "").overlaps(Span(5, 9, ""))
    assert Span(0, 6, "").overlaps(Span(5, 9, ""))


# --- protected regions ------------------------------------------------

def test_a_protected_phrase_is_found_across_a_line_break():
    """A writer types a phrase with spaces; a hard-wrapped draft contains
    a newline. Exact matching missed it *silently*, reporting the phrase
    absent while the writer believed it protected."""
    assert "perhaps we could discuss" not in DRAFT          # literally absent
    assert spans.contains_phrase(DRAFT, "perhaps we could discuss")
    assert spans.unlocatable(DRAFT, ["perhaps we could discuss"]) == []


def test_a_phrase_that_is_really_absent_is_reported():
    assert spans.unlocatable(DRAFT, ["no such words here"]) == ["no such words here"]


def test_an_edit_that_would_overwrite_protected_content_is_blocked():
    result = _transform({"protected": ["somewhat"]})
    blocked = [e for e in result["edits"] if e["blocked_by"]]
    assert result["blocked"] == 1
    assert blocked[0]["where"]["text"] == "somewhat"


def test_a_blocked_edit_is_reported_rather_than_dropped():
    """The writer's constraint and the advice are in tension; praxis says
    so instead of silently choosing."""
    with_protection = _transform({"protected": ["somewhat"]})
    without = _transform()
    assert len(with_protection["edits"]) == len(without["edits"])


def test_protected_content_never_blocks_something_it_does_not_touch():
    assert _transform({"protected": ["record IDs"]})["blocked"] == 0


# --- edits ------------------------------------------------------------

def test_every_gap_produces_an_edit_or_says_why_not():
    """A reported gap with no located change is the failure this mode
    exists to avoid."""
    contract = build(CONTRACT)
    structure = recommend(contract)["structure"]
    evaluation = evaluate(DRAFT, contract, structure)
    result = transform(DRAFT, contract, structure, evaluation)
    accounted = ({e["dimension"] for e in result["edits"]}
                 | set(result["folded_into"]) | set(result["no_edit_for"]))
    assert set(evaluation["priority"]) <= accounted


def test_a_folded_gap_is_not_reported_as_unaddressed():
    """Two different things: covered by another edit, versus missed."""
    result = _transform()
    assert result["folded_into"], "the fixture should fold at least one gap"
    assert result["no_edit_for"] == []
    assert not set(result["folded_into"]) & set(result["no_edit_for"])


def test_edits_carry_a_place_and_never_prose():
    for edit in _transform()["edits"]:
        assert (edit["at"] is not None) ^ (edit["where"] is not None)
        assert edit["instruction"]
        assert edit["kind"] in ("insert", "revise", "move", "cut")


def test_a_revise_edit_points_at_real_characters():
    for edit in _transform()["edits"]:
        if edit["where"]:
            assert DRAFT[edit["where"]["start"]:edit["where"]["end"]] == edit["where"]["text"]


def test_claims_are_analysed_once_for_both_callers():
    """`transform` and `evaluate` must not disagree about which claim is
    unsupported."""
    consequential, unsupported = claims(DRAFT)
    assert set(unsupported) <= set(consequential)


# --- modes ------------------------------------------------------------

def test_transform_must_be_asked_for():
    """"What is wrong" and "what to change" are different questions;
    answering the second unprompted is the rewriting habit this layer
    exists to avoid."""
    assert "transform" not in design(DRAFT, build(CONTRACT))
    assert "transform" in design(DRAFT, build(CONTRACT), mode="transform")


def test_mode_is_reported_and_validated():
    assert design(DRAFT, build(CONTRACT))["mode"] == "evaluate"
    assert design("", build(CONTRACT))["mode"] == "compose"
    with pytest.raises(ValueError, match="Unknown mode"):
        design(DRAFT, build(CONTRACT), mode="rewrite")
    assert set(MODES) == {"auto", "compose", "evaluate", "transform"}


# --- voice ------------------------------------------------------------

LONG = " ".join(["The migration step remains under review and the team is still "
                 "measuring the effect on the cutover window."] * 12)


def test_voice_reports_habits_not_authorship():
    """Function-word similarity was built, measured against pairs whose
    answer was known, and removed: same-author pairs scored below
    different-author pairs at these lengths."""
    result = voice.compare(LONG, LONG)
    assert result["status"] == "pass"
    assert "similarity" not in result
    assert "authorship" in result["note"]


def test_voice_never_reports_a_gap():
    """A dropped habit may be exactly what the rewrite was asked to do."""
    terse = " ".join(["Approve it."] * 60)
    assert voice.compare(LONG, terse)["status"] in ("pass", "review")


def test_a_changed_habit_is_named_with_its_numbers():
    terse = " ".join(["Ship it now."] * 60)
    moved = voice.compare(LONG, terse)["moved"]
    assert moved, "halving the sentence length should register"
    for habit in moved:
        assert {"habit", "before", "after", "unit"} <= set(habit)


def test_short_texts_report_unknown_rather_than_guessing():
    result = voice.compare("Too short to measure.", "Also short.")
    assert result["status"] == "unknown"
    assert str(voice.MINIMUM_WORDS) in result["finding"]


def test_voice_integrity_stays_unknown_without_a_reference():
    finding = next(d for d in evaluate(DRAFT, build(CONTRACT))["dimensions"]
                   if d["dimension"] == "voice_integrity")
    assert finding["status"] == "unknown"


def test_voice_integrity_reports_once_given_a_reference():
    finding = next(d for d in evaluate(LONG, build(CONTRACT), voice_reference=LONG)["dimensions"]
                   if d["dimension"] == "voice_integrity")
    assert finding["status"] == "pass"


def test_a_variant_is_compared_against_the_writer_not_another_rewrite():
    result = design(LONG, build(CONTRACT), [
        {"shade": "decisive", "text": " ".join(["Approve it now."] * 60), "recommended": True},
        {"shade": "warm", "text": " ".join(["Please approve it now."] * 60)}])
    for variant in result["variants"]:
        assert variant["voice"]["status"] in ("pass", "review", "unknown")


# --- rendering --------------------------------------------------------

def test_the_page_shows_located_changes():
    from praxis.render import document
    html = document(design(DRAFT, build({**CONTRACT, "protected": ["somewhat"]}),
                           mode="transform"))
    assert "Located changes" in html
    assert "characters" in html
    assert "protected" in html.lower()

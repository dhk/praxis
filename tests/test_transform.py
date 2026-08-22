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


# --- findings from the Copilot review on #34 ---------------------------

def test_a_sentence_span_matches_the_characters_it_claims():
    """`split_sentences` strips the body but not the offsets, so every
    sentence after the first claimed a range one character too wide and
    any edit built from it pointed at the wrong text."""
    text = "First one here. Second sentence follows. Third and last."
    for span in spans.sentences(text):
        assert text[span.start:span.end] == span.text


@pytest.mark.parametrize("text,expected", [
    ("Hi Priya,\n\nPlease approve.", "Please approve."),
    ("Hi Priya,\nPlease approve.", "Please approve."),      # single newline
    ("Dear Chen,\nThe report is ready.", "The report is ready."),
    ("Straight in, no greeting.", "Straight in, no greeting."),
    ("Hello there body.", "Hello there body."),              # not a greeting
])
def test_the_body_starts_below_the_greeting_however_it_is_wrapped(text, expected):
    """A greeting followed by one newline is the same *paragraph* as the
    body, so a paragraph-level test put the insertion above the greeting."""
    assert text[spans.body_start(text):].startswith(expected)


def test_an_insertion_inside_protected_content_is_blocked():
    """Zero-width spans: an insert exactly at a boundary disturbs nothing,
    but one strictly inside must be caught."""
    protected = Span(10, 20, "protected!")
    assert not Span(10, 10, "").overlaps(protected)   # touching the start
    assert not Span(20, 20, "").overlaps(protected)   # touching the end
    assert Span(15, 15, "").overlaps(protected)       # inside


def test_a_deadline_goes_at_the_end_of_the_request_not_inside_it():
    """Inserting at the end of the detector match produced "Please approve
    by 3 p.m. the request."."""
    draft = "We reviewed the plan. Please approve the request. Thanks."
    contract = build({**CONTRACT, "intent": "request"})
    structure = recommend(contract)["structure"]
    result = transform(draft, contract, structure, evaluate(draft, contract, structure))
    inserts = [e for e in result["edits"] if e["dimension"] == "actionability"]
    for edit in inserts:
        before, after = draft[:edit["at"]], draft[edit["at"]:]
        assert before.rstrip().endswith("request"), before
        assert after.startswith("."), after


def test_repeated_unsupported_sentences_get_their_own_spans():
    """Taking the first match every time emitted two edits against one
    occurrence and none against the other."""
    draft = "It risks the deadline. Something else entirely. It risks the deadline."
    contract = build({"stakes": "high", "intent": "inform"})
    structure = recommend(contract)["structure"]
    result = transform(draft, contract, structure, evaluate(draft, contract, structure))
    starts = [e["where"]["start"] for e in result["edits"]
              if e["dimension"] == "evidence_fit"]
    assert len(starts) == len(set(starts)), starts


def test_conclusion_first_is_defined_once():
    """A second copy would diverge the first time a structure was added to
    one set and not the other."""
    import praxis.evaluate as evaluate_module
    import praxis.transform as transform_module
    assert transform_module.CONCLUSION_FIRST is evaluate_module.CONCLUSION_FIRST


def test_transform_without_a_draft_is_refused():
    """Falling back to compose left `mode` saying transform while the
    result had no edits in it."""
    with pytest.raises(ValueError, match="needs a draft"):
        design("", build(CONTRACT), mode="transform")


def test_a_compose_variant_is_not_compared_with_itself():
    """`source` is the recommendation when there is no draft, so voice
    reported every habit held on the strength of no evidence."""
    result = design("", build(CONTRACT), [{"text": LONG, "recommended": True}])
    assert result["variants"][0]["voice"]["status"] == "unknown"


def test_a_supplied_voice_reference_reaches_the_variants():
    other = " ".join(["Ship it now; no delay."] * 40)
    result = design(LONG, build(CONTRACT), [{"text": other, "recommended": True}],
                    voice_reference=LONG)
    assert result["variants"][0]["voice"]["status"] in ("pass", "review")
    assert result["variants"][0]["voice"]["moved"]


def test_an_unlocatable_gap_is_not_reported_as_nothing_to_change():
    from praxis import brief
    result = {"strategy": {"title": "BLUF"}, "draft_present": True,
              "transform": {"edits": [], "blocked": 0, "folded_into": {},
                            "no_edit_for": ["evidence_fit"]}}
    answer = brief.answer(result)
    assert "Nothing to change" not in answer
    assert "evidence_fit" in answer


def test_the_depth_count_in_the_docstring_matches_the_tuple():
    from praxis import brief
    assert len(brief.DEPTHS) == 5
    assert "five depths" in brief.__doc__


def test_the_invariant_panel_does_not_claim_byte_identity_for_phrases():
    """Phrases match across re-wrapping now; the panel said otherwise."""
    from praxis.render import document
    html = document(design(DRAFT, build({**CONTRACT, "protected": ["record IDs"]})))
    assert "byte-for-byte" not in html
    assert "re-wrapped" in html


# --- rendering --------------------------------------------------------

def test_the_page_shows_located_changes():
    from praxis.render import document
    html = document(design(DRAFT, build({**CONTRACT, "protected": ["somewhat"]}),
                           mode="transform"))
    assert "Located changes" in html
    assert "characters" in html
    assert "protected" in html.lower()

"""Tests for the contextual communication design layer.

The load-bearing ones are the invariants, not the outputs: that a
question is only asked when its answers actually change the strategy,
that a variant cannot quietly drop a number or a caveat, and that the
browser bundle stays stdlib-only. Structure preferences can be argued
with and retuned; those three cannot move without the product changing
into something else.
"""

import ast
import json
import sys
from pathlib import Path

import pytest

from praxis import brief, shading, signals
from praxis.contract import SELECTORS, Contract, ContractError, build, schema
from praxis.design import design
from praxis.evaluate import GAP, PASS, UNKNOWN, evaluate
from praxis.render import document, fragment
from praxis.strategy import (STRUCTURES, material_questions, outcome, rank,
                             recommend, requirements, settled_fields)

DRAFT = ("We reviewed the release plan and identified a risk in the data-migration step. "
         "We may need additional engineering support, and I would like to discuss the "
         "implications in our next meeting.")


# --- contract ---------------------------------------------------------

def test_domains_are_enforced():
    with pytest.raises(ContractError, match="outside its domain"):
        build({"stakes": "apocalyptic"})
    with pytest.raises(ContractError, match="Unknown contract field"):
        build({"vibe": "chill"})


def test_stated_values_beat_inferred_ones():
    """A human's answer is never overwritten by the assistant's guess."""
    contract = build({"stakes": "high"}, {"stakes": "low"})
    assert contract.get("stakes") == "high"
    assert contract.origin("stakes") == "stated"
    assert "stakes" not in contract.assumptions()


def test_inferred_values_are_reported_as_assumptions():
    contract = build({}, {"authority": "approves"})
    assert contract.assumptions() == ["authority"]


def test_schema_marks_which_fields_select_the_strategy():
    by_name = {f["name"]: f for f in schema()}
    assert by_name["stakes"]["selects_strategy"] is True
    assert by_name["trigger"]["selects_strategy"] is False


# --- the question mechanism -------------------------------------------

def test_every_asked_question_actually_changes_the_strategy():
    """The product claim, as a test.

    'Ask only questions whose answers materially change strategy' is
    decidable here, so it is checked rather than asserted in a doc: walk
    each returned question across its domain and prove the outcome really
    does split.
    """
    contract = build({"intent": "request"})
    questions = material_questions(contract, limit=len(SELECTORS))
    assert questions, "a near-empty contract must have something worth asking"
    for question in questions:
        outcomes = {outcome(contract.with_value(question["field"], value))
                    for value in question["options"]}
        assert len(outcomes) > 1, f"{question['field']} was asked but changes nothing"


def test_no_settled_field_would_have_changed_the_strategy():
    """The converse: nothing suppressed was actually load-bearing."""
    contract = build({"intent": "request", "stakes": "high", "medium": "email"})
    for field in settled_fields(contract):
        outcomes = {outcome(contract.with_value(field, value))
                    for value in next(f["domain"] for f in schema() if f["name"] == field)}
        assert len(outcomes) == 1, f"{field} was suppressed but splits the strategy"


def test_questions_are_bounded():
    assert len(material_questions(build())) <= 3


def test_an_inferred_field_that_moves_the_strategy_is_offered_for_confirmation():
    contract = build({"intent": "request", "stakes": "high", "medium": "email"},
                     {"time_available": "low"})
    asked = {q["field"]: q for q in material_questions(contract)}
    assert "time_available" in asked
    assert asked["time_available"]["status"] == "inferred"


# --- strategy ---------------------------------------------------------

@pytest.mark.parametrize("values,expected", [
    ({"intent": "request", "authority": "approves", "time_available": "low"}, "bluf"),
    ({"intent": "escalate", "medium": "handoff"}, "sbar"),
    ({"intent": "teach", "prior_knowledge": "none"}, "cme"),
    ({"intent": "repair", "sensitivity": "high"}, "repair"),
    ({"intent": "warn", "stakes": "crisis"}, "hazard_first"),
    ({"intent": "demonstrate"}, "star"),
])
def test_structure_selection(values, expected):
    assert recommend(build(values))["structure"] == expected


def test_selection_is_deterministic():
    contract = build({"intent": "recommend", "stakes": "high"})
    assert [s.structure.id for s in rank(contract)] == [s.structure.id for s in rank(contract)]


def test_recommendation_explains_itself():
    result = recommend(build({"intent": "request", "time_available": "low"}))
    assert result["because"], "a recommendation with no stated reason is a black box"
    assert result["runner_up"]["structure"] != result["structure"]
    assert len(result["considered"]) == len(STRUCTURES)


def test_confidence_is_low_when_the_contract_is_nearly_empty():
    assert recommend(build())["confidence"] == "low"
    assert recommend(build({"intent": "request", "stakes": "high", "medium": "email",
                            "time_available": "low", "authority": "approves",
                            "urgency": "today"}))["confidence"] == "high"


def test_requirements_accumulate_with_stakes():
    low, high = requirements("low"), requirements("high")
    assert set(low).issubset(set(high))
    assert len(requirements("crisis")) > len(high)


# --- shading ----------------------------------------------------------

def test_variants_are_suppressed_where_a_protocol_decides_the_shape():
    for stakes in ("safety_critical", "crisis"):
        result = shading.candidates(build({"intent": "warn", "stakes": stakes}))
        assert result["offer"] is False
        assert "protocol" in result["reason"]


def test_variants_are_suppressed_for_a_simple_ask():
    assert shading.candidates(build({"intent": "request", "stakes": "low"}))["offer"] is False


def test_variants_are_offered_only_against_a_real_tension():
    offered = shading.candidates(build({"intent": "request", "urgency": "today",
                                        "sensitivity": "high"}))
    assert offered["offer"] is True
    assert 0 < len(offered["shades"]) <= shading.MAX_ALTERNATIVES
    assert all(s["tension"] for s in offered["shades"])


def test_a_variant_may_not_drop_protected_content():
    check = shading.check("Costs rose 40% in Q3.", "Costs rose sharply in Q3.", build())
    assert check["status"] == "fail"
    assert [v["kind"] for v in check["violations"]] == ["content_loss"]
    assert "40%" in check["violations"][0]["items"]


def test_a_variant_may_not_smooth_away_uncertainty():
    """Shorter must never mean the caveat is gone."""
    base = "The capacity estimate is preliminary and the fix may slip."
    check = shading.check(base, "The capacity number is firm and the fix lands Friday.", build())
    assert check["status"] == "fail"
    assert "uncertainty_loss" in [v["kind"] for v in check["violations"]]


def test_reducing_uncertainty_is_flagged_for_review_not_blocked():
    base = "The estimate is preliminary and the date may slip."
    check = shading.check(base, "The estimate is preliminary.", build())
    assert check["status"] == "review"
    assert check["violations"][0]["severity"] == "review"


def test_a_variant_may_not_drop_a_commitment_the_base_made():
    base = "Please approve by 3 p.m. so the team can start."
    check = shading.check(base, "The team is ready to start whenever. 3 p.m.", build())
    kinds = [v["kind"] for v in check["violations"]]
    assert "commitment_loss" in kinds


def test_rewording_an_ask_is_allowed():
    """Presence invariants survive rephrasing; that is the point of them."""
    base = "Please approve the request by 3 p.m."
    check = shading.check(base, "Can you sign off before 3 p.m.?", build())
    assert check["status"] == "pass"


def test_writer_declared_protected_strings_are_checked_verbatim():
    contract = build({"protected": ["without prejudice"]})
    ok = shading.check("Sent without prejudice.", "This is sent without prejudice.", contract)
    bad = shading.check("Sent without prejudice.", "Sent in good faith.", contract)
    assert ok["status"] == "pass" and bad["status"] == "fail"


def test_difference_map_reports_what_was_held_as_well_as_what_moved():
    base = "The estimate is preliminary. Please approve."
    dm = shading.difference_map(base, "Approve when you can. The estimate is preliminary.")
    assert any("uncertainty" in h for h in dm["held"])


def test_shade_fidelity_is_reported_not_enforced():
    dm = shading.difference_map("Please approve by 3 p.m.", "Thanks for your patience.", "warm")
    assert dm["shade_fidelity"][0]["met"] is True  # acknowledgement rose
    check = shading.check("Please approve by 3 p.m.", "Thanks for your patience.",
                          build(), "warm")
    assert check["status"] == "fail"  # ...and the lost ask is still a failure


# --- findings from the Copilot review on #32 ---------------------------

def test_a_changed_figure_is_not_preserved_content():
    """The guarantee the product is sold on, which substring containment
    quietly broke: `"40%" in "Costs rose 140%"` is true."""
    for base, variant in [("Costs rose 40% this quarter.", "Costs rose 140% this quarter."),
                          ("We need 4 engineers.", "We need 40 engineers."),
                          ("Ship 12 units.", "Ship 120 units.")]:
        check = shading.check(base, variant, build())
        assert check["status"] == "fail", f"{base} -> {variant}"
        assert "content_loss" in [v["kind"] for v in check["violations"]]


def test_moving_protected_content_around_is_still_allowed():
    """Exact comparison must not become positional."""
    check = shading.check("Costs rose 40% in Q3.", "In Q3, costs rose 40%.", build())
    assert check["status"] == "pass"


def test_a_declared_phrase_is_matched_as_a_phrase_not_a_token():
    contract = build({"protected": ["without prejudice"]})
    assert shading.check("Sent without prejudice.", "This is sent without prejudice, as agreed.",
                         contract)["status"] == "pass"
    assert shading.check("Sent without prejudice.", "Sent in good faith.",
                         contract)["status"] == "fail"


def test_a_url_keeps_its_identity_across_sentence_punctuation():
    """`\\S+` swallowed the full stop, so moving a link to the end of a
    sentence read as losing it."""
    check = shading.check("See [ref-1] and https://x.io/a.", "https://x.io/a, see [ref-1].", build())
    assert check["status"] == "pass"


def test_an_unrecognised_claim_is_not_a_clean_bill_of_health():
    """A detector finding nothing is not evidence there is nothing."""
    finding = _dimension("The colour of the sky is blue.", {"stakes": "high"}, "evidence_fit")
    assert finding["status"] == UNKNOWN
    assert "limit of the detector" in finding["finding"]


@pytest.mark.parametrize("stakes,required,text", [
    ("crisis", "update cadence", "I will own this. Please confirm receipt."),
    ("safety_critical", "escalation", "I will own this. Please confirm receipt."),
])
def test_raised_stakes_check_what_the_requirements_promise(stakes, required, text):
    """`requirements()` told the writer these were mandatory while the
    evaluator checked only owner and verification, and passed."""
    finding = _dimension(text, {"stakes": stakes}, "risk_calibration")
    assert finding["status"] == GAP
    assert required in finding["finding"]


def test_raised_stakes_pass_once_the_controls_are_there():
    ok = _dimension("I will own this. Please confirm receipt. I will update you at 5 p.m.",
                    {"stakes": "crisis"}, "risk_calibration")
    assert ok["status"] == PASS


def test_a_dimension_only_claims_to_check_what_it_checks():
    """Actionability's question named four things and tested two."""
    finding = _dimension("Please approve by 3 p.m.", {"intent": "request"}, "actionability")
    assert "owner" not in finding["question"]
    assert "risk_calibration" in finding["finding"]


def test_a_numeric_field_survives_the_command_line():
    """`--set length_limit=250` arrives as a string and was accepted, then
    silently ignored by an isinstance check."""
    contract = build({"length_limit": "250"})
    assert contract.get("length_limit") == 250
    finding = _dimension("word " * 300, {"length_limit": "250", "medium": "email"}, "medium_fit")
    assert finding["status"] == GAP
    with pytest.raises(ContractError, match="whole number"):
        build({"length_limit": "soon"})


def test_a_bare_protected_string_becomes_a_list():
    assert build({"protected": "3 p.m."}).protected_strings() == ["3 p.m."]


def test_strategy_inputs_are_derived_from_the_rules_not_from_having_a_domain():
    """`voice` has a closed domain and no rule reads it. Counting it as a
    strategy input made a contract look better informed than it was."""
    from praxis.strategy import STRATEGY_INPUTS
    assert "voice" in SELECTORS
    assert "voice" not in STRATEGY_INPUTS
    assert not [f for f in schema() if f["name"] == "voice" and f["selects_strategy"]]
    for name in STRATEGY_INPUTS:
        assert name in SELECTORS


def test_confidence_ignores_fields_no_rule_reads():
    inputs = {"intent": "request", "stakes": "high", "medium": "email"}
    without = recommend(build(inputs))["confidence"]
    with_voice = recommend(build({**inputs, "voice": "preserve"}))["confidence"]
    assert without == with_voice


def test_the_headline_reports_the_true_outstanding_count():
    result = design(DRAFT, build())
    assert f"{result['questions_outstanding']} question(s)" in result["headline"]
    assert result["questions_outstanding"] > len(result["questions"])


def test_the_unresolved_helper_is_not_the_capped_list():
    result = design(DRAFT, build())
    assert brief.unresolved_count(result) == result["questions_outstanding"]


def _dimension(text: str, values: dict, name: str) -> dict:
    return next(d for d in evaluate(text, build(values))["dimensions"]
                if d["dimension"] == name)


# --- evaluation -------------------------------------------------------

def test_every_dimension_reports_a_valid_status():
    result = evaluate(DRAFT, build({"intent": "request"}), "bluf")
    assert len(result["dimensions"]) == 10
    assert all(d["status"] in (PASS, GAP, UNKNOWN) for d in result["dimensions"])
    assert set(result["summary"]) == {PASS, GAP, UNKNOWN}


def test_an_empty_contract_produces_unknowns_not_gaps():
    """Absence of contract is not evidence of a defect."""
    result = evaluate(DRAFT, build())
    assert result["summary"][UNKNOWN] >= 5
    assert result["summary"][GAP] == 0


def test_an_action_intent_without_an_ask_is_a_gap():
    result = evaluate(DRAFT, build({"intent": "request"}))
    by_name = {d["dimension"]: d for d in result["dimensions"]}
    assert by_name["outcome_clarity"]["status"] == GAP
    assert by_name["actionability"]["status"] == GAP


def test_high_stakes_demands_visible_uncertainty_and_verification():
    text = "The migration will delay the release. Logs show a 40% failure rate."
    by_name = {d["dimension"]: d
               for d in evaluate(text, build({"stakes": "high"}))["dimensions"]}
    assert by_name["uncertainty_integrity"]["status"] == GAP
    assert by_name["risk_calibration"]["status"] == GAP


def test_consequential_claims_need_support_only_where_stakes_warrant():
    text = "This will delay the release."
    high = evaluate(text, build({"stakes": "high"}))
    low = evaluate(text, build({"stakes": "low"}))
    assert next(d for d in high["dimensions"] if d["dimension"] == "evidence_fit")["status"] == GAP
    assert next(d for d in low["dimensions"] if d["dimension"] == "evidence_fit")["status"] == UNKNOWN


def test_findings_carry_evidence_or_a_fix():
    for dimension in evaluate(DRAFT, build({"intent": "request", "stakes": "high"}))["dimensions"]:
        if dimension["status"] == GAP:
            assert dimension["recommendation"], f"{dimension['dimension']} names no fix"


def test_there_is_no_overall_score():
    """An opaque number invites optimising the number."""
    result = evaluate(DRAFT, build({"intent": "request"}))
    assert "score" not in result
    assert isinstance(result["verdict"], str)


# --- session ----------------------------------------------------------

def test_design_runs_without_a_draft():
    """A compose session has a situation before it has prose."""
    result = design("", build({"intent": "recommend"}))
    assert result["draft_present"] is False
    assert result["strategy"]["structure"]
    assert "evaluation" not in result


def test_design_result_is_json_serialisable():
    result = design(DRAFT, build({"intent": "request", "stakes": "high"}),
                    [{"shade": "decisive", "text": "Approve by 3 p.m. please."}])
    assert json.loads(json.dumps(result))["headline"]


def test_variants_are_checked_against_the_draft():
    result = design("Costs rose 40%.", build(),
                    [{"shade": "neutral", "text": "Costs rose a lot."}])
    assert result["variants"][0]["check"]["status"] == "fail"


# --- detectors --------------------------------------------------------

def test_a_polite_request_is_not_an_uncertainty_marker():
    """"Could you approve" is a request, not a hedge.

    Counting it inflated every courteous draft's uncertainty score and
    masked real losses: a variant that deleted every genuine caveat still
    scored a marker for saying "could you".
    """
    assert signals.find("uncertainty", "Could you approve this? May I suggest Thursday?") == []
    assert signals.find("uncertainty", "The fix may slip.") == ["may"]


def test_uncertainty_detection_survives_paraphrase():
    for text, expected in [("the estimate is preliminary", 2),
                           ("roughly 40 records, still investigating", 2),
                           ("the number is unconfirmed and the date is TBD", 2)]:
        assert len(signals.find("uncertainty", text)) >= expected - 1, text


def test_detectors_return_the_spans_they_matched():
    """A finding must be able to show what it saw."""
    found = signals.find("deadline", "Please reply by 3 p.m. today.")
    assert found and all(span.strip() for span in found)


# --- comparing versions against the recommendation --------------------

DRAFT_WITH_FACTS = "We may need help. Costs rose 40%. The estimate is preliminary."
RECOMMENDED = "Approve one engineer by 3 p.m. Costs rose 40%. The estimate is preliminary."
ALTERNATIVE = ("I know you are stretched. Could you approve one engineer by 3 p.m.? "
               "Costs rose 40%; the estimate is preliminary.")


def _versions(draft=DRAFT_WITH_FACTS, variants=None):
    return design(draft, build({"intent": "request", "stakes": "high"}),
                  variants or [{"shade": "decisive", "text": RECOMMENDED, "recommended": True},
                               {"shade": "warm", "text": ALTERNATIVE}])["variants"]


def test_an_alternative_is_measured_against_the_recommendation():
    """The writer is choosing between versions they could send, not
    between two edits of a draft they already decided to replace."""
    alternative = next(v for v in _versions() if v["role"] == "alternative")
    dm = alternative["check"]["difference_map"]
    assert dm["compared_to"] == "the recommended version"
    # Measured against the recommendation the warm version *gains* an
    # acknowledgement; measured against the draft that delta is invisible.
    assert any("acknowledgement" in m for m in dm["moved"])


def test_the_recommendation_is_measured_against_the_draft():
    recommended = next(v for v in _versions() if v["role"] == "recommended")
    assert recommended["check"]["difference_map"]["compared_to"] == "your draft"


def test_the_recommendation_is_listed_first_however_it_was_submitted():
    versions = _versions(variants=[{"shade": "warm", "text": ALTERNATIVE},
                                   {"shade": "decisive", "text": RECOMMENDED,
                                    "recommended": True}])
    assert [v["role"] for v in versions] == ["recommended", "alternative"]


def test_the_first_version_is_the_recommendation_when_none_is_marked():
    versions = _versions(variants=[{"shade": "decisive", "text": RECOMMENDED},
                                   {"shade": "warm", "text": ALTERNATIVE}])
    assert versions[0]["shade"] == "decisive"
    assert versions[0]["role"] == "recommended"


def test_invariants_still_come_from_the_draft_not_the_recommendation():
    """An alternative may not lose a figure just because the recommended
    version lost it first."""
    versions = _versions(variants=[
        {"shade": "decisive", "text": "Approve one engineer. The estimate is preliminary.",
         "recommended": True},
        {"shade": "warm", "text": "Could you approve one engineer? The estimate is preliminary."}])
    for version in versions:
        assert version["check"]["status"] == "fail"
        assert "40%" in version["check"]["violations"][0]["items"]


def test_compose_mode_checks_alternatives_against_the_recommendation():
    """With no draft the recommendation is the first prose that exists, so
    it becomes the reference. Before this, compose sessions went entirely
    unchecked."""
    versions = design("", build({"intent": "request"}), [
        {"shade": "decisive", "text": RECOMMENDED, "recommended": True},
        {"shade": "warm", "text": "Could you approve one engineer sometime?"}])["variants"]
    alternative = next(v for v in versions if v["role"] == "alternative")
    kinds = [x["kind"] for x in alternative["check"]["violations"]]
    assert "content_loss" in kinds  # dropped 3 p.m. and 40%
    assert "uncertainty_loss" in kinds


def test_a_compose_mode_recommendation_is_not_diffed_with_itself():
    versions = design("", build(), [{"shade": "decisive", "text": RECOMMENDED}])["variants"]
    assert versions[0]["check"] is None
    assert "baseline" in versions[0]["note"]


def test_every_difference_map_names_its_reference():
    """The same numbers mean different things under different references."""
    for version in _versions():
        if version["check"]:
            assert version["check"]["difference_map"]["compared_to"]


def test_a_violation_names_the_reference_it_was_measured_against():
    """A count with no reference reads as a contradiction beside the
    difference map, which uses a different one."""
    versions = _versions()
    alternative = next(v for v in versions if v["role"] == "alternative")
    for violation in alternative["check"]["violations"]:
        assert "your draft" in violation["detail"], violation["detail"]
    assert alternative["check"]["difference_map"]["compared_to"] == "the recommended version"


# --- answering at the depth that was asked for -------------------------

def test_the_answer_leads_with_the_conclusion_and_omits_the_reasoning():
    result = design(DRAFT, build({"intent": "request", "stakes": "high"}))
    text = brief.answer(result)
    assert text.startswith("Fix")
    assert "because" not in text and "favours" not in text
    assert len(text) < 260


def test_the_answer_is_a_shape_when_there_is_no_draft():
    text = brief.answer(design("", build({"intent": "teach", "prior_knowledge": "none"})))
    assert text.startswith("Write it concept–mechanism–example")


def test_the_answer_agrees_with_itself_grammatically():
    """'Fix 1 things' is the kind of seam that makes a tool feel unfinished."""
    one = design("Please approve this by 3 p.m.", build({"intent": "request", "stakes": "high"}))
    assert "1 things" not in brief.answer(one)


def test_outstanding_questions_actually_decrease_as_they_are_answered():
    """Progress that never moves reads as no progress.

    The displayed list is capped at three; the count must be the true
    total, or answering a question leaves it stubbornly at three.
    """
    counts = []
    values = {}
    for field, value in [("intent", "request"), ("stakes", "high"), ("medium", "email"),
                         ("time_available", "low"), ("authority", "approves")]:
        values[field] = value
        counts.append(design(DRAFT, build(dict(values)))["questions_outstanding"])
    assert counts == sorted(counts, reverse=True), counts
    assert counts[-1] < counts[0]


def test_progress_states_completion_rather_than_going_quiet():
    full = {"intent": "request", "stakes": "high", "medium": "email", "urgency": "today",
            "time_available": "low", "authority": "approves", "prior_knowledge": "partial",
            "sensitivity": "high", "power_distance": "upward", "voice": "preserve"}
    line = brief.progress(design(DRAFT, build(full)))
    assert "nothing else you could tell me would change it" in line


def test_only_one_question_is_surfaced_at_a_time():
    result = design(DRAFT, build())
    assert result["questions_outstanding"] > 1
    assert isinstance(brief.next_question(result), dict)


def test_a_widely_splitting_question_is_summarised_not_enumerated():
    """`intent` splits eleven ways; listing them all buries the point."""
    changes = brief.next_question(design(DRAFT, build()))["changes"]
    assert "decides the shape outright" in changes
    assert len(changes) < 90


def test_a_narrow_split_still_shows_what_it_decides():
    result = design(DRAFT, build({"intent": "request", "medium": "email"}))
    question = next(q for q in [brief.next_question(result)] if q)
    assert "→" in question["changes"]


def test_every_depth_renders():
    result = design(DRAFT, build({"intent": "request", "stakes": "high"}),
                    [{"shade": "decisive", "text": "Approve by 3 p.m."}])
    for depth in brief.DEPTHS:
        assert brief.at_depth(result, depth).strip()
    with pytest.raises(KeyError):
        brief.at_depth(result, "everything")


# --- rendering --------------------------------------------------------

def _rendered() -> str:
    return document(design(DRAFT, build({"intent": "request", "stakes": "high",
                                         "genre": "decision request"}),
                           [{"shade": "decisive", "text": "Approve by 3 p.m."}]))


def test_the_page_is_self_contained():
    """No script, no network: the page must render from itself alone."""
    html = _rendered()
    assert "<script" not in html.lower()
    assert "http://" not in html and "https://" not in html


def test_the_page_carries_both_themes():
    html = _rendered()
    assert "prefers-color-scheme:dark" in html
    assert '[data-theme=dark]' in html


def test_user_text_is_escaped():
    result = design("<script>alert(1)</script> and 40% risk.", build())
    html = document(result)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_fragment_is_the_document_body():
    result = design(DRAFT, build({"intent": "request"}))
    assert fragment(result) in document(result)


# --- boundaries -------------------------------------------------------

def test_the_browser_bundle_stays_stdlib_only():
    """`scripts/build_site.sh` copies `praxis/*.py` into Pyodide unchanged.

    A third-party import in any of those modules breaks the viewer, and
    it breaks it at runtime in a browser rather than here. The MCP
    subpackage is exempt: the non-recursive glob never copies it.
    """
    allowed = set(sys.stdlib_module_names)
    for path in sorted(Path("praxis").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [] if node.level else [(node.module or "").split(".")[0]]
            else:
                continue
            for name in names:
                assert name in allowed or name == "praxis", \
                    f"{path.name} imports {name!r}, which Pyodide will not have"


def test_the_engine_never_reaches_a_model_or_the_network():
    """The layer's cost model depends on this: no inference happens here."""
    banned = ("anthropic", "openai", "requests", "httpx", "urllib.request", "socket")
    for path in sorted(Path("praxis").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for name in banned:
            assert f"import {name}" not in source, f"{path.name} imports {name}"


def test_mcp_subpackage_is_excluded_from_the_browser_bundle():
    build_script = Path("scripts/build_site.sh").read_text(encoding="utf-8")
    assert "cp praxis/*.py dist/py/praxis/" in build_script, \
        "the bundle copy is no longer a non-recursive glob; praxis/mcp may now leak into Pyodide"

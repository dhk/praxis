"""Perkins hands a model a prompt. These check what it may never do."""

from praxis import perkins
from praxis.contract import build
from praxis.design import design


def _result(draft="", **stated):
    return design(draft, build(stated or {"intent": "request", "stakes": "high"}))


def test_the_refusals_are_always_present():
    # They are the product. A prompt that forgets to forbid rewriting is a
    # prompt that gets a rewrite back, which is the failure the whole layer
    # exists to avoid.
    prompt = perkins.commission(_result())
    for rule, _ in perkins.REFUSALS:
        assert rule in prompt
    assert "not rewriting it" in prompt


def test_a_prompt_carries_the_rule_surface_it_came_from():
    # A prompt is a file someone keeps. Without a stamp, a copy that predates
    # a rule change is indistinguishable from a current one.
    prompt = perkins.commission(_result())
    assert perkins.stamp() in prompt
    assert len(perkins.fingerprint()) == 8


def test_the_fingerprint_moves_when_a_rule_moves():
    before = perkins.fingerprint()
    original = perkins.STRUCTURES
    try:
        perkins.STRUCTURES = original[:-1]
        assert perkins.fingerprint() != before
    finally:
        perkins.STRUCTURES = original
    assert perkins.fingerprint() == before


def test_nothing_outstanding_is_stated_rather_than_omitted():
    # Silence reads as "praxis had nothing to say", when what it means is
    # "praxis has nothing left to ask" — the opposite instruction to a model.
    full = _result(intent="request", stakes="high", power_distance="upward",
                   time_available="low", authority="decides")
    assert not full["questions"]
    prompt = perkins.commission(full)
    assert "Nothing about the situation" in prompt
    assert "unsettled is in the draft" in prompt


def test_one_question_is_offered_never_a_list():
    sparse = _result(intent="request")
    assert sparse["questions_outstanding"] > 1
    prompt = perkins.commission(sparse)
    # The true total is reported; only one question is put.
    assert f"one of {sparse['questions_outstanding']} unsettled things" in prompt
    asked = [q["question"] for q in sparse["questions"] if q["question"] in prompt]
    assert len(asked) == 1


def test_an_analysed_draft_is_never_advertised_as_absent():
    # The dimension marks are read off a draft. Telling the model to paste
    # one implies none was seen, and invites it to distrust the marks.
    with_draft = _result("We should probably think about migrating.")
    assert with_draft["draft_present"]
    prompt = perkins.commission(with_draft)
    assert "[paste your draft here]" not in prompt
    assert "the same draft praxis read" in prompt
    # Handed the draft, it goes in verbatim and no placeholder survives.
    inline = perkins.commission(with_draft, "We should probably think about migrating.")
    assert "We should probably think about migrating." in inline
    assert "[paste" not in inline


def test_the_prompt_reports_the_engine_reading_rather_than_hiding_it():
    result = _result("We should probably think about migrating.")
    prompt = perkins.commission(result)
    for d in result["evaluation"]["dimensions"]:
        assert d["dimension"] in prompt
        assert d["question"] in prompt
    assert "say where you disagree" in prompt


def test_perkins_never_reaches_a_model_or_the_network():
    # The same guarantee the engine makes. Perkins packages and stops.
    source = (perkins.__file__ and open(perkins.__file__, encoding="utf-8").read())
    for forbidden in ("requests", "urllib", "http", "socket", "openai", "anthropic"):
        assert forbidden not in source

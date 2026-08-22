"""Session persistence and the MCP tool surface.

`praxis.mcp.store` has no third-party dependency, so it is always
tested. The server needs the `mcp` extra and is skipped without it — the
design layer has to remain testable in a checkout that never installed a
transport.

That skip is per-test, deliberately. A module-level `importorskip` reads
like the same thing and is not: it skips the whole file, so a checkout
without the extra silently lost the six store tests as well, and the
suite reported success having run neither.
"""

import json
from pathlib import Path

import pytest

from praxis.mcp import store

try:
    from praxis.mcp import server as mcp_server
except ImportError:  # the `mcp` extra is not installed
    mcp_server = None

needs_mcp = pytest.mark.skipif(mcp_server is None, reason="needs the `mcp` extra")


@pytest.fixture(autouse=True)
def workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXIS_HOME", str(tmp_path))
    return tmp_path


def test_round_trip():
    record = store.blank("VP staffing request", "We may need help.")
    record["values"] = {"intent": "request", "stakes": "high"}
    store.save(record)
    assert store.load(record["id"])["values"]["stakes"] == "high"
    assert [s["id"] for s in store.listing()] == [record["id"]]


def test_ids_are_readable_and_do_not_collide():
    first = store.save(store.blank("Release delay"))
    second = store.save(store.blank("Release delay"))
    assert first["id"] == "release-delay"
    assert second["id"] == "release-delay-2"


def test_a_session_id_cannot_escape_the_workspace(workspace):
    """Ids arrive from a model; a path fragment must stay a filename."""
    path = store.path_for("../../etc/passwd")
    assert path.parent == store.sessions_dir()
    assert workspace in path.parents
    with pytest.raises(ValueError):
        store.path_for("../..")


def test_missing_session_names_what_exists():
    store.save(store.blank("Only one"))
    with pytest.raises(FileNotFoundError, match="only-one"):
        store.load("nope")


def test_derived_analysis_is_never_persisted():
    """A stored verdict goes stale the moment a rule changes."""
    record = store.save(store.blank("Plan", "We may need help."))
    stored = json.loads(store.path_for(record["id"]).read_text())
    assert set(stored) == {"id", "title", "draft", "values", "inferred",
                           "variants", "created", "updated"}
    assert store.result_for(stored)["strategy"]["structure"]


def test_corrupt_session_files_do_not_break_the_listing():
    store.save(store.blank("Good"))
    (store.sessions_dir() / "broken.json").write_text("{not json", encoding="utf-8")
    assert [s["id"] for s in store.listing()] == ["good"]


DRAFT = ("We reviewed the release plan and identified a risk in the data-migration step. "
         "We may need additional engineering support, and I would like to discuss the "
         "implications in our next meeting.")


def test_a_long_title_does_not_hang_id_allocation():
    """`path_for` re-slugifies and truncates, so a title already at the
    48-character limit had `-2` appended and cut straight back to the
    original — which existed. `new_id` looped forever on a 61-character
    subject line."""
    title = "i wanted to flag something from our review of the release plan"
    ids = [store.save(store.blank(title))["id"] for _ in range(3)]
    assert len(set(ids)) == 3
    assert all(len(i) <= 48 for i in ids)


def test_an_id_is_reserved_when_it_is_allocated():
    """Checked-then-created let two design_open calls take the same id and
    the second save overwrite the first session."""
    first = store.blank("Release delay")
    assert store.path_for(first["id"]).exists(), "the id was not reserved"
    second = store.blank("Release delay")
    assert second["id"] != first["id"]


def test_an_unsaved_reservation_does_not_break_the_listing():
    store.blank("Reserved but never saved")
    store.save(store.blank("Real one"))
    assert [r["id"] for r in store.listing()] == ["real-one"]


@needs_mcp
def test_over_submitting_alternatives_is_refused():
    opened = mcp_server.design_open("We may need help with the migration.")
    result = mcp_server.design_shade(opened["session"], [
        {"text": "one", "recommended": True},
        {"text": "two"}, {"text": "three"}, {"text": "four"}])
    assert "at most 2" in result["error"]
    assert result["next_step"]


@needs_mcp
def test_every_reply_carries_a_next_step_including_the_error_ones():
    opened = mcp_server.design_open("We may need help with the migration.")
    bad = mcp_server.design_update(opened["session"], {"stakes": "enormous"})
    rendered = mcp_server.design_render(opened["session"], include_html=False)
    for reply in (opened, bad, rendered):
        assert reply.get("next_step"), reply


@needs_mcp
def test_the_rendered_size_is_bytes_not_code_points():
    opened = mcp_server.design_open("Costs rose 40% — the estimate is preliminary — in Q3.")
    rendered = mcp_server.design_render(opened["session"])
    assert rendered["bytes"] == len(rendered["html"].encode("utf-8"))
    assert rendered["bytes"] > len(rendered["html"]), "the draft has no non-ASCII to prove this"


def test_the_viewer_refuses_to_bind_a_public_interface():
    """It serves saved drafts and contracts with no authentication."""
    from praxis.mcp.serve import serve
    with pytest.raises(SystemExit, match="loopback only"):
        serve(host="0.0.0.0")


@needs_mcp
def test_the_first_call_answers_instead_of_interviewing():
    """There is no intake to get through. Even with nothing stated, the
    first call answers — at whatever confidence the situation supports,
    and says which."""
    opened = mcp_server.design_open(DRAFT)
    assert opened["answer"]
    assert "confidence" in opened["progress"]


@needs_mcp
def test_a_reply_is_the_answer_not_the_apparatus():
    """A regression guard on the thing this interface is for.

    An earlier version returned every dimension, the runner-up, the full
    contract and the invariants on every call — roughly 900 tokens to say
    something that fits in a sentence, from a tool whose whole argument is
    leading with the conclusion.
    """
    opened = mcp_server.design_open(DRAFT, stated={"intent": "request", "stakes": "high"})
    assert len(json.dumps(opened)) < 1600, "the reply is drifting back toward a data dump"
    assert not {"gaps", "invariants", "strategy", "assumptions_to_confirm"} & set(opened)


@needs_mcp
def test_at_most_one_question_is_offered():
    """One, not three. A writer who has had enough should not have to
    decline a list."""
    opened = mcp_server.design_open(DRAFT)
    assert "next_question" not in opened or isinstance(opened["next_question"], dict)
    question = opened.get("next_question")
    if question:
        assert question["ask"] and question["options"] and question["changes"]


@needs_mcp
def test_progress_says_when_nothing_further_would_help():
    """The completion signal, which is the unusual half of this."""
    full = {"intent": "request", "stakes": "high", "medium": "email", "urgency": "today",
            "time_available": "low", "authority": "approves", "prior_knowledge": "partial",
            "sensitivity": "high", "power_distance": "upward", "voice": "preserve"}
    opened = mcp_server.design_open(DRAFT, stated=full)
    assert "next_question" not in opened
    assert "nothing else you could tell me" in opened["progress"]


@needs_mcp
def test_detail_is_available_but_never_volunteered():
    opened = mcp_server.design_open(DRAFT, stated={"intent": "request", "stakes": "high"})
    blob = json.dumps(opened)
    assert "was chosen because" not in blob      # the reasoning
    assert "evidence standard" not in blob.lower()  # the obligations
    assert "runner" not in blob.lower()          # what came second

    why = mcp_server.design_detail(opened["session"], "why")
    assert "was chosen because" in why["detail"]
    findings = mcp_server.design_detail(opened["session"], "findings")
    assert findings["detail"].count("\n") >= 9  # all ten dimensions
    contract = mcp_server.design_detail(opened["session"], "contract")
    assert "situation.stakes: high" in contract["detail"]


@needs_mcp
def test_detail_can_return_every_question_at_once():
    opened = mcp_server.design_open(DRAFT)
    everything = mcp_server.design_detail(opened["session"], "questions")
    assert len(everything["questions"]) >= 1
    assert all(q["ask"] for q in everything["questions"])
    assert "not_worth_asking" in everything


@needs_mcp
def test_an_unknown_depth_lists_what_exists():
    opened = mcp_server.design_open(DRAFT)
    result = mcp_server.design_detail(opened["session"], "everything")
    assert "error" in result and "questions" in result["available"]


@needs_mcp
def test_the_tool_loop_runs_end_to_end():
    opened = mcp_server.design_open(
        DRAFT, stated={"intent": "request", "stakes": "high", "medium": "email"},
        inferred={"time_available": "low"})
    assert opened["next_step"]

    answered = mcp_server.design_update(opened["session"], {"urgency": "today"})
    assert answered["answer"]

    shaded = mcp_server.design_shade(opened["session"], [
        {"shade": "decisive", "recommended": True,
         "text": "Approve one engineer by 3 p.m. The estimate is preliminary."},
        {"shade": "warm",
         "text": "I know you are stretched. Could you approve one engineer by 3 p.m.? "
                 "The estimate is preliminary."}])
    assert [v["role"] for v in shaded["versions"]] == ["recommended", "alternative"]
    assert shaded["versions"][1]["compared_to"] == "the recommended version"

    rendered = mcp_server.design_render(opened["session"])
    assert Path(rendered["path"]).exists()
    assert rendered["html"].startswith("<!doctype html>")


@needs_mcp
def test_a_session_is_named_from_the_writing_not_the_salutation():
    opened = mcp_server.design_open("Hi Priya,\n\nWe found a defect in the migration step.")
    assert opened["session"].startswith("we-found-a-defect")


@needs_mcp
def test_a_bad_field_value_returns_an_error_not_an_exception():
    """A model guessing a value should be corrected, not crashed."""
    opened = mcp_server.design_open("Thing")
    result = mcp_server.design_update(opened["session"], {"stakes": "enormous"})
    assert "outside its domain" in result["error"]
    assert result["hint"]


@needs_mcp
def test_the_server_exposes_its_own_vocabulary():
    schema = mcp_server.design_schema()
    assert {"fields", "structures", "shades"} == set(schema)
    assert any(f["name"] == "stakes" for f in schema["fields"])

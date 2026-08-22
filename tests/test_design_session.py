"""Session persistence and the MCP tool surface.

`praxis.mcp.store` has no third-party dependency, so it is always
tested. The server itself needs the `mcp` extra and is skipped without
it — the design layer has to remain testable in a checkout that never
installed a transport.
"""

import json
from pathlib import Path

import pytest

from praxis.mcp import store


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


mcp_server = pytest.importorskip("praxis.mcp.server", reason="needs the `mcp` extra")


DRAFT = ("We reviewed the release plan and identified a risk in the data-migration step. "
         "We may need additional engineering support, and I would like to discuss the "
         "implications in our next meeting.")


def test_the_first_call_answers_instead_of_interviewing():
    """There is no intake to get through. Even with nothing stated, the
    first call answers — at whatever confidence the situation supports,
    and says which."""
    opened = mcp_server.design_open(DRAFT)
    assert opened["answer"]
    assert "confidence" in opened["progress"]


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


def test_at_most_one_question_is_offered():
    """One, not three. A writer who has had enough should not have to
    decline a list."""
    opened = mcp_server.design_open(DRAFT)
    assert "next_question" not in opened or isinstance(opened["next_question"], dict)
    question = opened.get("next_question")
    if question:
        assert question["ask"] and question["options"] and question["changes"]


def test_progress_says_when_nothing_further_would_help():
    """The completion signal, which is the unusual half of this."""
    full = {"intent": "request", "stakes": "high", "medium": "email", "urgency": "today",
            "time_available": "low", "authority": "approves", "prior_knowledge": "partial",
            "sensitivity": "high", "power_distance": "upward", "voice": "preserve"}
    opened = mcp_server.design_open(DRAFT, stated=full)
    assert "next_question" not in opened
    assert "nothing else you could tell me" in opened["progress"]


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


def test_detail_can_return_every_question_at_once():
    opened = mcp_server.design_open(DRAFT)
    everything = mcp_server.design_detail(opened["session"], "questions")
    assert len(everything["questions"]) >= 1
    assert all(q["ask"] for q in everything["questions"])
    assert "not_worth_asking" in everything


def test_an_unknown_depth_lists_what_exists():
    opened = mcp_server.design_open(DRAFT)
    result = mcp_server.design_detail(opened["session"], "everything")
    assert "error" in result and "questions" in result["available"]


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


def test_a_session_is_named_from_the_writing_not_the_salutation():
    opened = mcp_server.design_open("Hi Priya,\n\nWe found a defect in the migration step.")
    assert opened["session"].startswith("we-found-a-defect")


def test_a_bad_field_value_returns_an_error_not_an_exception():
    """A model guessing a value should be corrected, not crashed."""
    opened = mcp_server.design_open("Thing")
    result = mcp_server.design_update(opened["session"], {"stakes": "enormous"})
    assert "outside its domain" in result["error"]
    assert result["hint"]


def test_the_server_exposes_its_own_vocabulary():
    schema = mcp_server.design_schema()
    assert {"fields", "structures", "shades"} == set(schema)
    assert any(f["name"] == "stakes" for f in schema["fields"])

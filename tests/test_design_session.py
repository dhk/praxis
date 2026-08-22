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


def test_the_tool_loop_runs_end_to_end():
    opened = mcp_server.design_open(
        "Migration staffing",
        "We reviewed the release plan and identified a risk. We may need help.",
        stated={"intent": "request", "stakes": "high", "medium": "email"},
        inferred={"time_available": "low"})
    assert opened["strategy"]["structure"] == "bluf"
    assert "time_available" in opened["assumptions_to_confirm"]
    assert opened["next_step"]

    shaded = mcp_server.design_shade(opened["session"], [
        {"shade": "decisive", "text": "Approve one engineer by 3 p.m. The estimate is preliminary."}])
    assert shaded["variants"][0]["status"] in ("pass", "review", "fail")

    rendered = mcp_server.design_render(opened["session"])
    assert Path(rendered["path"]).exists()
    assert rendered["html"].startswith("<!doctype html>")


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

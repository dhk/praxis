import json
from pathlib import Path
from praxis.cli import run
from praxis.pipeline import run_pipeline

def test_harness_creates_artifacts(tmp_path: Path):
    source = Path("examples/concise_scientific_writing/input.md")
    out = tmp_path / "run"
    run(source, out)
    assert (out / "observations.json").exists()
    assert (out / "transformations.json").exists()
    assert (out / "validation.json").exists()
    assert (out / "final.md").exists()
    final = (out / "final.md").read_text()
    assert "It should be noted that" not in final
    assert "because" in final
    validation = json.loads((out / "validation.json").read_text())
    assert validation["status"] == "pass"

def test_run_pipeline_matches_cli_artifacts(tmp_path: Path):
    source = Path("examples/concise_scientific_writing/input.md")
    out = tmp_path / "run"
    run(source, out)
    result = run_pipeline(source.read_text(encoding="utf-8"))
    for name in ("observations", "recommendations", "transformations", "validation"):
        assert result[name] == json.loads((out / f"{name}.json").read_text())
    assert result["final"] == (out / "final.md").read_text()
    assert result["report"] == (out / "report.md").read_text()
    assert result["metrics"]["before"]["words"] >= result["metrics"]["after"]["words"]

def test_claude_skill_authoring_pack():
    source = Path("examples/claude_skill/SKILL.md").read_text(encoding="utf-8")
    result = run_pipeline(source, "claude_skill_authoring")
    rule_ids = {o["rule_id"] for o in result["observations"]}
    assert rule_ids == {"SKL-001", "SKL-002", "SKL-003", "SKL-004", "SKL-005", "SKL-006"}
    assert result["pack"]["id"] == "claude_skill_authoring"
    # Flags are never applied; phrase rules are.
    flagged = [t for t in result["transformations"] if not t["applied"]]
    assert all(t["safety"] == "review" for t in flagged)
    assert "utilize" not in result["final"]
    assert "Please note that" not in result["final"]
    assert result["validation"]["status"] == "pass"

def test_resume_writing_pack():
    source = Path("examples/resume/input.md").read_text(encoding="utf-8")
    result = run_pipeline(source, "resume_writing")
    rule_ids = {o["rule_id"] for o in result["observations"]}
    assert rule_ids == {"RES-001", "RES-002", "RES-003", "RES-004", "RES-005", "RES-006"}
    final = result["final"]
    assert "Responsible for" not in final
    assert "Managed the batch ingestion platform" in final
    # Facts survive the rewrite: dates, metrics, contact details.
    assert result["validation"]["status"] == "pass"
    for fact in ("2021", "23%", "$180K", "6.5", "90"):
        assert fact in final

def test_pack_registry_lists_all_packs():
    from praxis.packs import list_packs
    packs = {p["id"]: p for p in list_packs()}
    assert packs["concise_scientific_writing"]["transformations"] == 4
    assert packs["claude_skill_authoring"]["transformations"] == 6
    assert packs["resume_writing"]["transformations"] == 6

def test_unknown_pack_rejected():
    import pytest
    with pytest.raises(KeyError):
        run_pipeline("Some text.", "nonexistent_pack")

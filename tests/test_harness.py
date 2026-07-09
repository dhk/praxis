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

def test_render_prompt_packages_flagged_items():
    from praxis.handoff import render_prompt
    source = Path("examples/resume/input.md").read_text(encoding="utf-8")
    result = run_pipeline(source, "resume_writing")
    prompt = render_prompt(result)
    flagged = [t for t in result["transformations"] if not t["applied"]]
    assert flagged and all(t["id"] in prompt for t in flagged)
    assert "Proposed rewrite:" in prompt                 # response format stated
    assert result["final"] in prompt                     # document included
    assert "`2021`" in prompt                            # protected tokens listed
    # Applied items are not offered for re-litigation.
    applied_ids = [t["id"] for t in result["transformations"] if t["applied"]]
    assert all(f"### {tid} " not in prompt for tid in applied_ids)
    # A clean document produces no prompt.
    assert render_prompt(run_pipeline("A short note. Nothing here.")) == ""

def test_unknown_pack_rejected():
    import pytest
    with pytest.raises(KeyError):
        run_pipeline("Some text.", "nonexistent_pack")

def test_transform_never_applies_an_unobserved_match():
    # One rule's deletion used to be able to weld two fragments into a fresh
    # match for a later rule that was never present in (and never observed
    # against) the original text. 'In order' + 'it should be noted that ' +
    # 'to run' becomes 'In order to run' only after CSW-001 deletes the
    # middle phrase; CSW-002 must not then rewrite a match that only exists
    # in the intermediate, already-mutated string.
    text = "In order it should be noted that to run the test, do X."
    result = run_pipeline(text)
    observed_rule_ids = {o["rule_id"] for o in result["observations"]}
    applied_rule_ids = {t["rule_id"] for t in result["transformations"] if t["applied"]}
    assert applied_rule_ids <= observed_rule_ids
    assert "In order to" not in text or "in order to run" not in result["final"].lower()
    assert result["final"] == "In order to run the test, do X."

def test_transformation_recommendation_id_is_real():
    source = Path("examples/resume/input.md").read_text(encoding="utf-8")
    result = run_pipeline(source, "resume_writing")
    rec_ids = {r["id"] for r in result["recommendations"]}
    for t in result["transformations"]:
        assert t["recommendation_id"] in rec_ids

def test_validation_protects_percent_sign():
    from praxis.validation import protected_tokens, validate
    original = "Revenue grew 23% year over year."
    stripped = "Revenue grew 23 year over year."  # simulates a rule eating the '%'
    assert "23%" in protected_tokens(original)
    result = validate(original, stripped, [])
    assert result["status"] == "fail"
    assert "23%" in result["checks"]["missing_protected_tokens"]

def test_report_escapes_pipes_and_newlines_in_table_cells():
    text = ("It should be noted that the pipeline handles a | b | c cases well and this "
            "sentence must be long enough to exceed the thirty five word threshold used "
            "by the long sentence flag rule so it gets flagged for review in the observe "
            "pass of the harness today.")
    result = run_pipeline(text)
    log_start = result["report"].index("## Transformation Diff Log")
    log_end = result["report"].index("## Final Document")
    log_table = result["report"][log_start:log_end]
    data_rows = [ln for ln in log_table.splitlines() if ln.startswith("| T-")]
    assert len(data_rows) == 2
    import re
    for row in data_rows:
        delimiters = re.findall(r"(?<!\\)\|", row)
        assert len(delimiters) == 9  # 8 columns -> 9 unescaped delimiters
    flagged_row = next(row for row in data_rows if row.startswith("| T-002"))
    assert "\\|" in flagged_row  # the raw ' | ' from the evidence was escaped, not split on
    assert "\n" not in "".join(data_rows)

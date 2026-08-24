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

def test_same_document_treated_differently_by_each_pack():
    # Every pack test above uses a different, bespoke example file tailored
    # to that one pack, so none of them actually prove pack *selection* is
    # what drives the outcome, as opposed to each example simply tripping
    # its own pack's rules. Run one shared sentence — built to trip a
    # distinct rule in each pack — through all three and confirm they
    # diverge, with no cross-contamination between packs' rule ids.
    text = "It should be noted that I simply utilize this in order to succeed."
    pack_ids = ("concise_scientific_writing", "claude_skill_authoring", "resume_writing")
    results = {pack_id: run_pipeline(text, pack_id) for pack_id in pack_ids}

    rule_ids = {pack_id: sorted({o["rule_id"] for o in r["observations"]})
                for pack_id, r in results.items()}
    assert rule_ids["concise_scientific_writing"] == ["CSW-001", "CSW-002"]
    assert rule_ids["claude_skill_authoring"] == ["SKL-001", "SKL-002"]
    assert rule_ids["resume_writing"] == ["RES-004"]

    prefixes = {"concise_scientific_writing": "CSW-", "claude_skill_authoring": "SKL-", "resume_writing": "RES-"}
    for pack_id, ids in rule_ids.items():
        assert all(rid.startswith(prefixes[pack_id]) for rid in ids), \
            f"{pack_id} observed a rule id outside its own prefix: {ids}"

    finals = {pack_id: r["final"] for pack_id, r in results.items()}
    assert finals["concise_scientific_writing"] == "I simply utilize this to succeed."
    assert finals["claude_skill_authoring"] == "It should be noted that I use this in order to succeed."
    assert finals["resume_writing"] == text  # RES-004 is review-only; nothing applied
    assert len(set(finals.values())) == 3  # one input, three genuinely different outputs

def test_repo_docs_pack():
    source = Path("examples/repo_docs/input.md").read_text(encoding="utf-8")
    result = run_pipeline(source, "repo_docs")
    rule_ids = {o["rule_id"] for o in result["observations"]}
    assert rule_ids == {"RPD-001", "RPD-002", "RPD-003", "RPD-004", "RPD-005", "RPD-006"}
    assert result["pack"]["id"] == "repo_docs"
    final = result["final"]
    assert "Please note that" not in final
    assert "It is important to note that" not in final
    assert "utilize" not in final
    # The fenced shell command is documentation content, not prose to edit.
    assert "```bash\npip install example-project" in final
    assert "example-project run docs/input.md --out artifacts/\n```" in final
    assert result["validation"]["status"] == "pass"

def test_pm_writing_pack():
    source = Path("examples/pm_writing/input.md").read_text(encoding="utf-8")
    result = run_pipeline(source, "pm_writing")
    rule_ids = {o["rule_id"] for o in result["observations"]}
    assert rule_ids == {"PMW-001", "PMW-002", "PMW-003", "PMW-004", "PMW-005", "PMW-006"}
    assert result["pack"]["id"] == "pm_writing"
    final = result["final"]
    assert "Utilize" not in final and "utilize" not in final
    assert "in order to" not in final
    # Buzzwords and unquantified claims are flagged, never silently rewritten.
    flagged_reasons = {t["reason"] for t in result["transformations"] if not t["applied"]}
    assert any("Buzzword" in r for r in flagged_reasons)
    assert any("Superlative" in r for r in flagged_reasons)
    assert result["validation"]["status"] == "pass"

def test_pack_registry_lists_all_packs():
    from praxis.packs import list_packs
    packs = {p["id"]: p for p in list_packs()}
    assert packs["concise_scientific_writing"]["transformations"] == 4
    assert packs["claude_skill_authoring"]["transformations"] == 6
    assert packs["resume_writing"]["transformations"] == 6
    assert packs["repo_docs"]["transformations"] == 6
    assert packs["pm_writing"]["transformations"] == 6

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
    result = validate(original, stripped)
    assert result["status"] == "fail"
    assert "23%" in result["checks"]["missing_protected_tokens"]

def test_validation_protects_fenced_code_blocks():
    from praxis.validation import protected_tokens, validate
    original = "Run it:\n\n```bash\npip install example-project\n```\n\nDone."
    mutated = "Run it:\n\n```bash\npip install example\n```\n\nDone."  # simulates a rule editing inside the fence
    assert "```bash\npip install example-project\n```" in protected_tokens(original)
    result = validate(original, mutated)
    assert result["status"] == "fail"

def test_validation_protects_inline_code_spans():
    from praxis.validation import protected_tokens, validate
    original = "Utilize the `--apply` flag to write changes."
    mutated = "Utilize the `--apply-now` flag to write changes."  # simulates a rule editing inside the span
    assert "`--apply`" in protected_tokens(original)
    result = validate(original, mutated)
    assert result["status"] == "fail"

def test_validate_does_not_mutate_transformations():
    # validate() used to mutate Transformation.validation_status in place as
    # a side effect of a function that looked report-only. It's now pure;
    # apply_validation_status() is the explicit, separately-named step that
    # does the mutation.
    from praxis.validation import validate, apply_validation_status
    from praxis.models import Transformation

    t = Transformation(id="T-001", recommendation_id="R-001", rule_id="X",
                        location="char:0-1", before="a", after="b", reason="r", safety="safe", applied=True)
    result = validate("a document with 42", "a document with 42")
    assert t.validation_status == "pending"  # untouched by validate()
    apply_validation_status([t], result["status"])
    assert t.validation_status == "pass"

def test_recommend_raises_clear_error_for_unmatched_observation():
    # If an observation's rule_id doesn't fullmatch any phrase rule's pattern
    # against its own evidence (e.g. a future pack with ambiguous same-id
    # patterns, or a bug upstream in observe()), recommend() must fail loudly
    # with a clear message rather than an opaque StopIteration.
    from praxis.rules import recommend
    from praxis.packs import get_pack
    from praxis.models import Observation
    import pytest

    pack = get_pack("concise_scientific_writing")
    bogus_obs = Observation(id="O-999", rule_id="CSW-001", rule_title="Remove unnecessary introductory phrases",
                             location="char:0-3", evidence="xyz", reason="test", safety="safe")
    with pytest.raises(ValueError, match="No phrase rule"):
        recommend(pack, [bogus_obs])

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

def _parse_pack_yaml(path: Path) -> dict:
    """Minimal parser for this project's pack.yaml shape only: flat
    top-level scalar keys plus one list of flat dicts under
    `transformations:`. Not a general YAML parser — deliberately just
    enough to check packs/*/pack.yaml against packs.py without adding a
    YAML dependency (the project is stdlib-only; see CLAUDE.md).
    """
    top: dict = {}
    transformations: list[dict] = []
    current: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current is not None:
                transformations.append(current)
            current = {}
            key, _, value = stripped[2:].partition(":")
            current[key.strip()] = value.strip()
        elif raw.startswith(" ") and current is not None:
            key, _, value = stripped.partition(":")
            current[key.strip()] = value.strip()
        else:
            key, _, value = stripped.partition(":")
            key = key.strip()
            if key != "transformations":
                top[key] = value.strip()
    if current is not None:
        transformations.append(current)
    top["transformations"] = transformations
    return top

def test_pack_yaml_stays_in_sync_with_packs_py():
    # packs/<id>/pack.yaml is a hand-maintained metadata mirror (CLAUDE.md:
    # "not read by the code — keep it in sync by hand") with nothing to
    # catch drift. Parse it (test-only; the package itself still never
    # touches YAML) and cross-check against the registry.
    from praxis.packs import PACKS

    for pack in PACKS.values():
        yaml_path = Path(f"packs/{pack.id}/pack.yaml")
        assert yaml_path.exists(), f"missing packs/{pack.id}/pack.yaml"
        parsed = _parse_pack_yaml(yaml_path)
        assert parsed["id"] == pack.id
        assert parsed["version"] == pack.version
        assert parsed["title"] == pack.title

        expected = []
        seen_ids = set()
        for rule in pack.phrase_rules:
            if rule.id not in seen_ids:
                seen_ids.add(rule.id)
                expected.append({"id": rule.id, "title": rule.title, "safety": rule.safety})
        for rule in pack.flag_rules:
            if rule.id not in seen_ids:
                seen_ids.add(rule.id)
                expected.append({"id": rule.id, "title": rule.title, "safety": "review"})

        actual = [{"id": t["id"], "title": t["title"], "safety": t["safety"]} for t in parsed["transformations"]]
        assert actual == expected, f"packs/{pack.id}/pack.yaml is out of sync with packs.py"

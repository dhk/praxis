import json
from pathlib import Path
from praxis.cli import run

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

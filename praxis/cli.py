import argparse
import json
from pathlib import Path
from .rules import observe, recommend, transform
from .validation import validate
from .metrics import metrics
from .report import render_report
from .models import to_dicts

def run(input_path: Path, out_dir: Path) -> None:
    original = input_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)

    observations = observe(original)
    recommendations = recommend(observations)
    final, transformations = transform(original, observations, recommendations)
    validation = validate(original, final, transformations)

    before_metrics = metrics(original)
    after_metrics = metrics(final)
    report = render_report(before_metrics, after_metrics, validation, transformations, final)

    (out_dir / "observations.json").write_text(json.dumps(to_dicts(observations), indent=2), encoding="utf-8")
    (out_dir / "recommendations.json").write_text(json.dumps(to_dicts(recommendations), indent=2), encoding="utf-8")
    (out_dir / "transformations.json").write_text(json.dumps(to_dicts(transformations), indent=2), encoding="utf-8")
    (out_dir / "validation.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    (out_dir / "final.md").write_text(final, encoding="utf-8")
    (out_dir / "report.md").write_text(report, encoding="utf-8")

    print(f"Wrote artifact trail to {out_dir}")
    print(f"Validation: {validation['status']}")
    print(f"Words: {before_metrics['words']} -> {after_metrics['words']}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run an Praxis transformation pipeline.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("input", type=Path)
    run_p.add_argument("--out", type=Path, default=Path("artifacts/run"))
    args = parser.parse_args()
    if args.cmd == "run":
        run(args.input, args.out)

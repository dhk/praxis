import argparse
import json
from pathlib import Path
from .pipeline import run_pipeline
from .packs import DEFAULT_PACK_ID, PACKS

def run(input_path: Path, out_dir: Path, pack_id: str = DEFAULT_PACK_ID) -> None:
    original = input_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_pipeline(original, pack_id)

    (out_dir / "observations.json").write_text(json.dumps(result["observations"], indent=2), encoding="utf-8")
    (out_dir / "recommendations.json").write_text(json.dumps(result["recommendations"], indent=2), encoding="utf-8")
    (out_dir / "transformations.json").write_text(json.dumps(result["transformations"], indent=2), encoding="utf-8")
    (out_dir / "validation.json").write_text(json.dumps(result["validation"], indent=2), encoding="utf-8")
    (out_dir / "final.md").write_text(result["final"], encoding="utf-8")
    (out_dir / "report.md").write_text(result["report"], encoding="utf-8")

    print(f"Wrote artifact trail to {out_dir}")
    print(f"Validation: {result['validation']['status']}")
    print(f"Words: {result['metrics']['before']['words']} -> {result['metrics']['after']['words']}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Run an Praxis transformation pipeline.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("input", type=Path)
    run_p.add_argument("--out", type=Path, default=Path("artifacts/run"))
    run_p.add_argument("--pack", choices=sorted(PACKS), default=DEFAULT_PACK_ID)
    args = parser.parse_args()
    if args.cmd == "run":
        run(args.input, args.out, args.pack)

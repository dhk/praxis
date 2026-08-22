import argparse
import json
from pathlib import Path
from .pipeline import run_pipeline
from .packs import DEFAULT_PACK_ID, PACKS
from .handoff import render_prompt

def run(input_path: Path, out_dir: Path, pack_id: str = DEFAULT_PACK_ID, prompt: bool = False) -> None:
    original = input_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_pipeline(original, pack_id)

    (out_dir / "observations.json").write_text(json.dumps(result["observations"], indent=2), encoding="utf-8")
    (out_dir / "recommendations.json").write_text(json.dumps(result["recommendations"], indent=2), encoding="utf-8")
    (out_dir / "transformations.json").write_text(json.dumps(result["transformations"], indent=2), encoding="utf-8")
    (out_dir / "validation.json").write_text(json.dumps(result["validation"], indent=2), encoding="utf-8")
    (out_dir / "final.md").write_text(result["final"], encoding="utf-8")
    (out_dir / "report.md").write_text(result["report"], encoding="utf-8")

    if prompt:
        text = render_prompt(result)
        if text:
            (out_dir / "prompt.md").write_text(text, encoding="utf-8")
            print(f"Wrote review handoff prompt to {out_dir / 'prompt.md'}")
        else:
            print("No flagged items; no handoff prompt written.")

    print(f"Wrote artifact trail to {out_dir}")
    print(f"Validation: {result['validation']['status']}")
    print(f"Words: {result['metrics']['before']['words']} -> {result['metrics']['after']['words']}")

def design(input_path: Path | None, out: Path, values: list[str]) -> None:
    """Analyse a communication situation and write the artifact page.

    The design layer never writes prose, so this command has no --pack and
    no output document: it reports the strategy, the questions worth
    asking, and — when given a draft — where the draft falls short.
    """
    from .contract import build, ContractError
    from .design import design as run_design
    from .render import document

    stated: dict = {}
    for pair in values:
        if "=" not in pair:
            raise SystemExit(f"--set expects field=value, got {pair!r}")
        field, value = pair.split("=", 1)
        stated[field.strip()] = value.strip()
    try:
        contract = build(stated)
    except ContractError as exc:
        raise SystemExit(str(exc)) from exc

    draft = input_path.read_text(encoding="utf-8") if input_path else ""
    result = run_design(draft, contract)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(document(result), encoding="utf-8")

    print(result["headline"])
    print(f"Structure: {result['strategy']['title']} "
          f"({result['strategy']['confidence']} confidence)")
    for question in result["questions"]:
        print(f"  ask: {question['question']}  [{question['field']}]")
    for dimension in result.get("evaluation", {}).get("dimensions", []):
        if dimension["status"] == "gap":
            print(f"  gap: {dimension['dimension']} — {dimension['finding']}")
    print(f"Wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a praxis transformation pipeline.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("input", type=Path)
    run_p.add_argument("--out", type=Path, default=Path("artifacts/run"))
    run_p.add_argument("--pack", choices=sorted(PACKS), default=DEFAULT_PACK_ID)
    run_p.add_argument("--prompt", action="store_true",
                       help="also write prompt.md, an LLM review handoff for the flagged items")
    design_p = sub.add_parser("design", help="analyse a communication situation")
    design_p.add_argument("input", type=Path, nargs="?",
                          help="an existing draft; omit to plan before writing")
    design_p.add_argument("--out", type=Path, default=Path("artifacts/design.html"))
    design_p.add_argument("--set", dest="values", action="append", default=[],
                          metavar="FIELD=VALUE",
                          help="a contract field, repeatable (e.g. --set stakes=high)")

    serve_p = sub.add_parser("serve", help="browse saved design sessions locally")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)

    sub.add_parser("mcp", help="run the MCP server on stdio")

    args = parser.parse_args()
    if args.cmd == "run":
        run(args.input, args.out, args.pack, args.prompt)
    elif args.cmd == "design":
        design(args.input, args.out, args.values)
    elif args.cmd == "serve":
        from .mcp.serve import serve as serve_viewer
        serve_viewer(args.host, args.port)
    elif args.cmd == "mcp":
        from .mcp.server import main as run_mcp
        run_mcp()

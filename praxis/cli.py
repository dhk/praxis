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

def design(input_path: Path | None, out: Path, values: list[str], show_why: bool = False,
           as_transform: bool = False, voice_path: Path | None = None) -> None:
    """Analyse a communication situation and write the artifact page.

    Answer-first, like the MCP surface: the shape and what is wrong,
    then how much would still change it, then one question. The
    reasoning is behind `--why`, because a tool that argues for leading
    with the conclusion should not open with its own rationale.
    """
    from . import brief
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
    if as_transform and not draft.strip():
        raise SystemExit("--transform needs a draft to locate changes in")
    reference = voice_path.read_text(encoding="utf-8") if voice_path else ""
    result = run_design(draft, contract, mode="transform" if as_transform else "auto",
                        voice_reference=reference)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(document(result), encoding="utf-8")

    print(brief.answer(result))
    print(brief.progress(result))
    question = brief.next_question(result)
    if question:
        print(f"\n? {question['ask']}  ({'/'.join(question['options'])})")
        print(f"  --set {question['field']}=…  ({question['changes']})")
    if as_transform:
        print(f"\n{brief.edits(result)}")
    if show_why:
        print(f"\n{brief.why(result)}")
    print(f"\nWrote {out}")


def corpus(show_prompt: bool, detector: str | None, out: Path | None) -> None:
    """Report how the detectors score, or emit a prompt to widen the corpus.

    The report is the deterministic half praxis is for. The prompt is the
    other half: everything a person needs to take the problem to a model
    of their choosing, without praxis and without this repository.
    """
    from . import handoff
    from .measure import tiered_report

    if not show_prompt:
        print(tiered_report())
        return
    try:
        text = handoff.corpus_prompt(detector)
    except KeyError as exc:
        # `str(KeyError)` is the repr of its argument, so the quote
        # character depends on whether the message itself contains one.
        # Stripping double quotes worked only by accident.
        raise SystemExit(exc.args[0]) from exc
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)


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
    design_p.add_argument("--why", action="store_true",
                          help="also print the reasoning behind the recommendation")
    design_p.add_argument("--transform", action="store_true",
                          help="locate surgical changes in the draft instead of "
                               "evaluating it")
    design_p.add_argument("--voice", type=Path, metavar="PATH",
                          help="a sample of your own writing, to check which habits "
                               "the draft keeps")

    serve_p = sub.add_parser("serve", help="browse saved design sessions locally")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8765)

    sub.add_parser("mcp", help="run the MCP server on stdio")

    corpus_p = sub.add_parser("corpus", help="score the detectors, or commission "
                                             "work on the corpus")
    corpus_p.add_argument("--prompt", action="store_true",
                          help="emit a self-contained prompt for widening the corpus "
                               "with a model of your choosing")
    corpus_p.add_argument("--detector", metavar="NAME",
                          help="commission one signal; omit for the three with the "
                               "least evidence behind them")
    corpus_p.add_argument("--out", type=Path, help="write the prompt to a file")

    args = parser.parse_args()
    if args.cmd == "run":
        run(args.input, args.out, args.pack, args.prompt)
    elif args.cmd == "design":
        design(args.input, args.out, args.values, args.why, args.transform, args.voice)
    elif args.cmd == "serve":
        from .mcp.serve import serve as serve_viewer
        serve_viewer(args.host, args.port)
    elif args.cmd == "corpus":
        corpus(args.prompt, args.detector, args.out)
    elif args.cmd == "mcp":
        from .mcp.server import main as run_mcp
        run_mcp()

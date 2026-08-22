"""One design session, assembled: contract, strategy, questions, verdict.

`design()` is to the contextual-communication layer what
`pipeline.run_pipeline()` is to the transformation harness — the single
entry point every interface calls, returning a JSON-serialisable result
that nothing downstream is allowed to recompute differently. The MCP
server, the HTML renderer, and the CLI all consume this one shape.

The layer generates no prose. It cannot: there is no model here, no API
key, and no network. It decides the strategy, states what may not move,
asks only the questions that change the answer, and audits whatever text
comes back. The writing itself belongs to the writer and, where the
writer wants one, to whichever model they are already talking to — which
is why the whole layer costs nothing per run and stays inspectable.
"""

from . import shading, strategy as strategy_mod
from .contract import Contract, build
from .evaluate import evaluate
from .metrics import metrics

SCHEMA_VERSION = "design/0.1"


def design(draft: str = "", contract: Contract | None = None,
           variants: list[dict] | None = None) -> dict:
    """Analyse a communication situation and, if given, the text for it.

    `draft` may be empty — a compose session has a situation before it has
    prose, and the strategy, the questions, and the requirements are all
    computable without a word written.

    `variants` is a list of ``{"shade": id, "text": str, "label": str}``.
    Each is checked against `draft` as its base: protected content, the
    commitments the base made, and whether the shade did what it claims.
    """
    contract = contract or build()
    recommendation = strategy_mod.recommend(contract)
    result = {
        "schema_version": SCHEMA_VERSION,
        "contract": contract.to_dict(),
        "strategy": recommendation,
        "questions": strategy_mod.material_questions(contract),
        "do_not_ask": strategy_mod.settled_fields(contract),
        "shading": shading.candidates(contract),
        "draft_present": bool(draft.strip()),
        "variants": [],
    }

    if draft.strip():
        result["metrics"] = metrics(draft)
        result["invariants"] = shading.invariants(draft, contract)
        result["evaluation"] = evaluate(draft, contract, recommendation["structure"])

    for variant in variants or []:
        text = variant.get("text", "")
        shade = variant.get("shade")
        result["variants"].append({
            "label": variant.get("label") or (shading.BY_ID[shade].title if shade in shading.BY_ID else "Variant"),
            "shade": shade,
            "tradeoff": shading.BY_ID[shade].tradeoff if shade in shading.BY_ID else "",
            "text": text,
            "check": shading.check(draft, text, contract, shade) if draft.strip() else None,
        })

    result["headline"] = _headline(result)
    return result


def _headline(result: dict) -> str:
    """One line a chat client can show without rendering the whole artifact."""
    s = result["strategy"]
    parts = [f"{s['title']} ({s['confidence']} confidence)"]
    if result["questions"]:
        parts.append(f"{len(result['questions'])} question(s) would change that")
    if "evaluation" in result:
        parts.append(result["evaluation"]["verdict"])
    if result["variants"]:
        failed = sum(1 for v in result["variants"]
                     if v["check"] and v["check"]["status"] == "fail")
        parts.append(f"{len(result['variants'])} variant(s), {failed} failing invariants")
    elif result["shading"]["offer"]:
        parts.append(f"{len(result['shading']['shades'])} shade(s) worth exploring")
    return " · ".join(parts)

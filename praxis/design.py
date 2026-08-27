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

from . import shading, strategy as strategy_mod, voice as voice_mod
from .contract import Contract, build
from .evaluate import evaluate
from .metrics import metrics
from .transform import transform as build_edits

SCHEMA_VERSION = "design/0.5"  # every reason list carries its true length

#: The three modes the layer offers. `auto` picks between compose and
#: evaluate by whether a draft exists; transform has to be asked for,
#: because "tell me what is wrong" and "tell me what to change" are
#: different questions and answering the second unprompted is the
#: rewriting habit this product exists to avoid.
MODES = ("auto", "compose", "evaluate", "transform")


def design(draft: str = "", contract: Contract | None = None,
           variants: list[dict] | None = None, mode: str = "auto",
           voice_reference: str = "") -> dict:
    """Analyse a communication situation and, if given, the text for it.

    `draft` may be empty — a compose session has a situation before it has
    prose, and the strategy, the questions, and the requirements are all
    computable without a word written.

    `variants` is a list of ``{"shade": id, "text": str, "label": str}``,
    one of which may carry ``"recommended": true`` (the first is assumed
    otherwise). The recommendation is compared with the writer's draft;
    every alternative is compared with the **recommendation**, so the
    difference maps answer the question the writer is actually asking —
    how does this differ from the version I would otherwise send.
    """
    if mode not in MODES:
        raise ValueError(f"Unknown mode {mode!r}. Available: {', '.join(MODES)}")
    if mode == "transform" and not draft.strip():
        # Silently falling back to compose left `mode` saying transform
        # while the result had no edits in it, so callers of the library
        # saw a shape the CLI and MCP guards never let them see.
        raise ValueError("transform mode needs a draft to locate changes in")
    contract = contract or build()
    recommendation = strategy_mod.recommend(contract)
    resolved = mode if mode != "auto" else ("evaluate" if draft.strip() else "compose")
    # Every material question, then the few worth showing. Reporting the
    # capped list as the total made the count sit at three however many
    # the writer answered — progress that never moves reads as no
    # progress at all.
    outstanding = strategy_mod.material_questions(contract, limit=len(strategy_mod.SELECTORS))
    result = {
        "schema_version": SCHEMA_VERSION,
        "contract": contract.to_dict(),
        "strategy": recommendation,
        "questions": outstanding[:3],
        "questions_outstanding": len(outstanding),
        "do_not_ask": strategy_mod.settled_fields(contract),
        "shading": shading.candidates(contract),
        "draft_present": bool(draft.strip()),
        "mode": resolved,
        "variants": [],
    }

    if draft.strip():
        result["metrics"] = metrics(draft)
        result["invariants"] = shading.invariants(draft, contract)
        result["evaluation"] = evaluate(draft, contract, recommendation["structure"],
                                        voice_reference)
        if resolved == "transform":
            result["transform"] = build_edits(draft, contract,
                                              recommendation["structure"],
                                              result["evaluation"])

    result["variants"] = _review(draft, contract, variants or [], voice_reference)
    result["headline"] = _headline(result)
    return result


def _recommended_index(variants: list[dict]) -> int:
    """Which version is the recommendation the alternatives are priced against.

    A variant may mark itself with ``"recommended": true``. Absent that,
    the first one is taken as the recommendation — clients tend to send
    the recommended version first, and having no recommendation at all
    would leave the alternatives with nothing to be alternatives *to*.
    """
    for i, variant in enumerate(variants):
        if variant.get("recommended"):
            return i
    return 0


def _review(draft: str, contract: Contract, variants: list[dict],
            voice_reference: str = "") -> list[dict]:
    """Check every version, each against the right reference.

    The recommendation is measured against the writer's draft: "what did
    the recommended shape change about what I wrote". Every alternative
    is measured against the **recommendation**, because that is the
    comparison the writer is actually making — they are choosing between
    two versions they could send, not between two edits of a draft they
    have already decided to replace.

    Invariants always come from the draft where there is one. Protected
    content originates in the writer's own words, and an alternative must
    not be allowed to lose a figure just because the recommendation lost
    it first. With no draft — a compose session, where the recommendation
    is the first prose that exists — the recommendation becomes the
    source of invariants for the alternatives. This is also why compose
    sessions are checked at all now: with a single reference they were
    silently skipped.
    """
    if not variants:
        return []

    rec_index = _recommended_index(variants)
    rec_text = variants[rec_index].get("text", "")
    has_draft = bool(draft.strip())
    source = draft if has_draft else rec_text
    source_label = "your draft" if has_draft else "the recommended version"

    reviewed = []
    for i, variant in enumerate(variants):
        text = variant.get("text", "")
        shade = variant.get("shade")
        is_recommended = i == rec_index
        entry = {
            "label": variant.get("label") or _label(shade, is_recommended),
            "shade": shade,
            "role": "recommended" if is_recommended else "alternative",
            "tradeoff": shading.BY_ID[shade].tradeoff if shade in shading.BY_ID else "",
            "text": text,
        }
        if is_recommended:
            # Nothing to compare a compose-mode recommendation against: it is
            # the reference, and diffing it with itself would report a page
            # of zeroes as though that meant something.
            entry["check"] = (shading.check(draft, text, contract, shade,
                                            compare_label="your draft",
                                            source_label="your draft")
                              if has_draft else None)
            if not has_draft:
                entry["note"] = "the baseline every alternative is measured against"
        else:
            entry["check"] = shading.check(source, text, contract, shade,
                                           compare_to=rec_text,
                                           compare_label="the recommended version",
                                           source_label=source_label)
        # Voice is measured against the writer's own words, never against
        # another rewrite: the question is whether this still sounds like
        # them. In a compose session there are no such words — comparing
        # the recommendation with itself reported every habit held on the
        # strength of no evidence at all.
        reference = voice_reference or (draft if has_draft else "")
        entry["voice"] = (voice_mod.compare(reference, text) if reference.strip() else
                          {"status": "unknown", "moved": [], "held": [],
                           "finding": "No sample of the writer's own prose to compare "
                                      "with: this session composed from nothing."})
        reviewed.append(entry)

    reviewed.sort(key=lambda v: v["role"] != "recommended")
    return reviewed


def _label(shade: str | None, is_recommended: bool) -> str:
    if shade in shading.BY_ID:
        return shading.BY_ID[shade].title
    return "Recommended" if is_recommended else "Variant"


def _headline(result: dict) -> str:
    """One line a chat client can show without rendering the whole artifact."""
    s = result["strategy"]
    parts = [f"{s['title']} ({s['confidence']} confidence)"]
    outstanding = result["questions_outstanding"]
    if outstanding:
        parts.append(f"{outstanding} question(s) would change that")
    if "evaluation" in result:
        parts.append(result["evaluation"]["verdict"])
    if result["variants"]:
        failed = sum(1 for v in result["variants"]
                     if v["check"] and v["check"]["status"] == "fail")
        parts.append(f"{len(result['variants'])} variant(s), {failed} failing invariants")
    elif result["shading"]["offer"]:
        parts.append(f"{len(result['shading']['shades'])} shade(s) worth exploring")
    return " · ".join(parts)

"""The MCP surface: praxis as an instrument the conversation picks up.

The division of labour is the whole architecture, so it is worth stating
plainly. **This server never writes prose.** It holds no API key, calls
no model, and reaches no network. What it does is decide the strategy,
say which questions are worth the writer's attention, state what may not
move, and audit whatever text comes back against those constraints.

The prose comes from the model the writer is already talking to. That is
what makes the layer cost nothing per run: the only inference is the
inference the conversation was already paying for. It is also what keeps
it honest — a rewriter that grades its own rewriting is not an audit.

The intended loop, which `next_step` in every response nudges the client
along:

    open  →  answer the questions that matter  →  write the recommended
          version and any offered alternatives  →  submit them all for
          checking  →  render the page

The recommendation goes in with the alternatives, marked. It is the
reference every alternative is priced against: a writer choosing between
versions is asking how each differs from the one they would otherwise
send, not how each differs from a draft they have already decided to
replace.

`design_render` returns a complete self-contained HTML page. A client
that can publish artifacts should publish it: the contract, the
scorecard, and two variants with their difference maps are a comparison,
and no amount of chat prose substitutes for seeing them side by side.
"""

from __future__ import annotations

from typing import Any

from praxis import render
from praxis.contract import ContractError, schema
from praxis.shading import SHADES
from praxis.strategy import STRUCTURES
from praxis.mcp import store

INSTRUCTIONS = """praxis is a communication-design instrument, not a writer.

It decides how a message should be shaped for a specific reader, situation,
and level of stakes; it never generates prose. You write the prose. Submit
what you write to design_shade and praxis will check it against the
contract's invariants and report what actually changed.

Use it when the writing task has a real audience and real consequences —
a decision request, an incident update, bad news to a customer, a message
to a strained colleague. Skip it for casual or purely mechanical text.

Work the loop: design_open, then ask only the questions design_open returns
(it has already computed which ones change the answer — do not run your own
intake interview), then write, then design_shade, then design_render and
publish the page as an artifact."""


def _server():
    """Build the server object across mcp 1.x (FastMCP) and 2.x (MCPServer)."""
    try:
        from mcp.server.mcpserver import MCPServer
        return MCPServer("praxis", instructions=INSTRUCTIONS)
    except ImportError:
        from mcp.server.fastmcp import FastMCP
        return FastMCP("praxis", instructions=INSTRUCTIONS)


mcp = _server()


def _view(record: dict) -> dict:
    """The compact response shape. Deliberately not the whole result.

    A design result is a page's worth of structure. Returning all of it
    on every call would spend the conversation's context on things the
    model does not need to reason about — that is what design_render and
    the artifact are for. What comes back here is what changes the
    model's next move: the strategy, the questions, the gaps, and the
    constraints on writing.
    """
    result = store.result_for(record)
    strategy = result["strategy"]
    out: dict[str, Any] = {
        "session": record["id"],
        "headline": result["headline"],
        "strategy": {
            "structure": strategy["structure"], "title": strategy["title"],
            "sequence": strategy["sequence"], "because": strategy["because"],
            "confidence": strategy["confidence"], "requirements": strategy["requirements"],
            "evidence_standard": strategy["evidence_standard"],
        },
        "ask_the_writer": [
            {"field": q["field"], "question": q["question"], "options": q["options"],
             "status": q["status"], "decides_between": q["decides_between"]}
            for q in result["questions"]],
        "do_not_ask": result["do_not_ask"],
        "assumptions_to_confirm": result["contract"]["assumptions"],
        "shading": result["shading"],
    }
    if "evaluation" in result:
        out["gaps"] = [{"dimension": d["dimension"], "finding": d["finding"],
                        "fix": d["recommendation"]}
                       for d in result["evaluation"]["dimensions"] if d["status"] == "gap"]
        out["verdict"] = result["evaluation"]["verdict"]
        out["invariants"] = result["invariants"]
    if result["variants"]:
        out["variants"] = [{
            "label": v["label"], "shade": v["shade"], "role": v["role"],
            "status": v["check"]["status"] if v["check"] else "baseline",
            "compared_to": v["check"]["difference_map"]["compared_to"] if v["check"] else None,
            "violations": v["check"]["violations"] if v["check"] else [],
            "changed": v["check"]["difference_map"]["moved"] if v["check"] else [],
            "held": v["check"]["difference_map"]["held"] if v["check"] else [],
            "shade_fidelity": v["check"]["difference_map"]["shade_fidelity"] if v["check"] else [],
        } for v in result["variants"]]
    out["next_step"] = _next_step(result)
    return out


def _next_step(result: dict) -> str:
    if result["questions"]:
        fields = ", ".join(q["field"] for q in result["questions"])
        return (f"Ask the writer about: {fields}. These are the only unknowns that move the "
                "strategy; do not run a broader intake interview. Then call design_update "
                "with their answers.")
    if not result["draft_present"]:
        return ("The strategy is settled. Write the draft to the recommended sequence, then "
                "call design_update with it.")
    gaps = result.get("evaluation", {}).get("priority", [])
    if gaps and not result["variants"]:
        return (f"Close these gaps first: {', '.join(gaps)}. Then, if shading is offered, write "
                "the recommended version plus the offered shades and submit them all to "
                "design_shade, with the recommended one marked `recommended: true`.")
    if result["shading"]["offer"] and not result["variants"]:
        shades = ", ".join(s["shade"] for s in result["shading"]["shades"])
        return (f"Write the recommended version plus these shades: {shades}. Keep every verbatim "
                "invariant byte-identical. Submit all of them to design_shade, including the "
                "recommended one marked `recommended: true` — it is what the alternatives are "
                "compared against.")
    if result["variants"]:
        failed = [v["label"] for v in result["variants"]
                  if v["check"] and v["check"]["status"] == "fail"]
        if failed:
            return f"Fix and resubmit: {', '.join(failed)} lost protected content or a commitment."
        return "Call design_render and publish the page so the writer can compare the versions."
    return "Call design_render and publish the page."


@mcp.tool()
def design_open(title: str, draft: str = "", stated: dict | None = None,
                inferred: dict | None = None) -> dict:
    """Open a communication-design session and get the recommended strategy.

    Use this at the start of any writing task with a real reader and real
    consequences. It returns the recommended structure with its reasons,
    the (at most three) questions whose answers would change that
    recommendation, and — if a draft is supplied — where the draft falls
    short of what the contract requires.

    `stated` is what the writer told you. `inferred` is what you concluded
    on your own; keep the two apart, because an inference that changes the
    strategy comes back as an assumption for the writer to confirm rather
    than a fact. Call design_schema for the field names and their values.
    """
    record = store.blank(title, draft)
    return _update(record, stated, inferred, None)


@mcp.tool()
def design_update(session_id: str, stated: dict | None = None,
                  inferred: dict | None = None, draft: str = "") -> dict:
    """Record answers, corrections, or a new draft, and re-run the analysis.

    Everything derived — the strategy, the questions, the scorecard — is
    recomputed from scratch, so a corrected assumption changes the
    recommendation immediately rather than leaving a stale verdict behind.
    """
    return _update(store.load(session_id), stated, inferred, draft or None)


def _update(record: dict, stated: dict | None, inferred: dict | None, draft: str | None) -> dict:
    from praxis.contract import build  # validates domains; raises ContractError
    if draft is not None:
        record["draft"] = draft
    record["values"] = {**record.get("values", {}), **(stated or {})}
    record["inferred"] = {**record.get("inferred", {}), **(inferred or {})}
    try:
        build(record["values"], record["inferred"])
    except ContractError as exc:
        return {"error": str(exc), "hint": "call design_schema for the allowed values"}
    store.save(record)
    return _view(record)


@mcp.tool()
def design_shade(session_id: str, variants: list[dict]) -> dict:
    """Submit versions you have written and have each one audited.

    **Send the recommended version too, not only the alternatives.** Each
    entry is `{"shade": id, "text": "...", "label": "...", "recommended":
    true}`; mark exactly one as recommended (the first is assumed
    otherwise). The recommendation is what the alternatives are priced
    against, and without it the writer sees two options with nothing to
    compare them to.

    praxis reports, per version: protected content that went missing,
    commitments dropped, markers of uncertainty smoothed away, what
    measurably changed, what was deliberately held, and whether the
    version is actually the shade it claims to be. The recommendation is
    compared with the writer's draft; each alternative is compared with
    the recommendation, so `changed` answers "how does this differ from
    the version I would otherwise send". `compared_to` names the
    reference on every result — do not report a delta without it.

    A `fail` status means the version changed something it was not
    allowed to change. Rewrite it rather than explaining it away.
    """
    record = store.load(session_id)
    record["variants"] = [
        {"shade": v.get("shade"), "text": v.get("text", ""), "label": v.get("label", ""),
         "recommended": bool(v.get("recommended"))}
        for v in variants]
    store.save(record)
    return _view(record)


@mcp.tool()
def design_render(session_id: str, include_html: bool = True) -> dict:
    """Render the session as a self-contained HTML page and save it.

    Publish the returned HTML as an artifact. The contract, the scorecard,
    and the variants with their difference maps are a comparison; they do
    not survive being narrated in chat.
    """
    record = store.load(session_id)
    result = store.result_for(record)
    html = render.document(result)
    path = store.home() / "pages" / f"{record['id']}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    out = {"session": record["id"], "title": record.get("title", ""),
           "path": str(path), "bytes": len(html), "headline": result["headline"],
           "hint": "publish `html` as an artifact, or run `python -m praxis serve` to browse"}
    if include_html:
        out["html"] = html
    return out


@mcp.tool()
def design_list() -> dict:
    """List saved design sessions, most recently touched first."""
    return {"sessions": store.listing(), "workspace": str(store.home())}


@mcp.tool()
def design_schema() -> dict:
    """The contract fields, the structures, and the shades this server knows.

    Call it once before your first design_open so you set field values that
    exist. `selects_strategy` marks the fields that actually drive the
    recommendation — the rest describe the situation.
    """
    return {
        "fields": schema(),
        "structures": [{"id": s.id, "title": s.title, "summary": s.summary,
                        "sequence": list(s.sequence)} for s in STRUCTURES],
        "shades": [{"id": s.id, "title": s.title, "behaviour": s.behaviour,
                    "tradeoff": s.tradeoff} for s in SHADES],
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

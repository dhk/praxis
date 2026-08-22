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

## Answer first, then as much as they ask for

Every tool here returns the answer and stops. Not the reasoning, not the
runner-up, not the ten dimensions — those are one call away and most
people never need them. A writer asking "is this ready to send" wants a
sentence, and a tool that replies with a page of structure has answered
a question they did not ask.

This is not a style preference. Praxis's entire argument is leading with
the conclusion, asking only what changes it, and letting the reader drill
in. A version of it that opened with a wall of JSON would be advice its
own interface ignored.

So each reply carries four things: the **answer**, the **progress** (how
much would still change it, and — more useful — how much would not), **one
question** if one is worth asking, and where to drill in. Nothing is
hidden, but nothing is volunteered either.

## Nobody has to finish

There is no interview to complete. The first call answers immediately at
whatever confidence the situation supports, and says so. Every reply
offers exactly one more question and reports what is still outstanding,
so stopping is a decision the writer makes with the cost in front of them
rather than a corner they are backed into. Good enough is genuinely good
enough, and praxis is unusual in being able to say when *nothing* further
would help.

The loop, which `next_step` nudges the client along:

    open  →  answer a question or two, or don't  →  write the recommended
          version and any offered alternatives  →  submit them for
          checking  →  render the page

The recommendation goes in with the alternatives, marked. It is the
reference every alternative is priced against: a writer choosing between
versions is asking how each differs from the one they would otherwise
send, not how each differs from a draft they have already decided to
replace.
"""

from __future__ import annotations

from typing import Any

from praxis import brief, render
from praxis.contract import ContractError, build, schema
from praxis.shading import MAX_ALTERNATIVES, SHADES
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

**Relay the answer, not the apparatus.** Every reply gives you the answer,
one question worth asking, and what is still outstanding. Pass those on
roughly as they come. Do not fetch the reasoning, the full findings, or the
contract unless the writer asks why — design_detail exists for that moment
and not before. Never run your own intake interview: praxis has already
computed which questions change the answer, and asking beyond them wastes
the writer's attention on things that change nothing.

The writer decides when to stop. Offer the next question; do not press it.

"""

def _server():
    """Build the server object across mcp 1.x (FastMCP) and 2.x (MCPServer)."""
    try:
        from mcp.server.mcpserver import MCPServer
        return MCPServer("praxis", instructions=INSTRUCTIONS)
    except ImportError:
        from mcp.server.fastmcp import FastMCP
        return FastMCP("praxis", instructions=INSTRUCTIONS)


mcp = _server()


def _reply(record: dict, note: str = "") -> dict:
    """The answer, and only the answer.

    Four fields. The reasoning, the full scorecard, and the contract are
    each one `design_detail` call away — deliberately not included here,
    because a writer asking whether a message is ready to send wants a
    sentence, and volunteering a page of structure answers a question
    they did not ask.
    """
    result = store.result_for(record)
    out: dict[str, Any] = {
        "session": record["id"],
        "answer": brief.answer(result),
        "progress": brief.progress(result),
    }
    question = brief.next_question(result)
    if question:
        out["next_question"] = question
    if result["variants"]:
        out["versions"] = [{
            "label": v["label"], "role": v["role"],
            "status": v["check"]["status"] if v["check"] else "baseline",
            "compared_to": v["check"]["difference_map"]["compared_to"] if v["check"] else None,
            "changed": v["check"]["difference_map"]["moved"] if v["check"] else [],
            "held": v["check"]["difference_map"]["held"] if v["check"] else [],
            "problems": [x["detail"] for x in v["check"]["violations"]] if v["check"] else [],
        } for v in result["variants"]]
    out["next_step"] = _next_step(result)
    out["drill_in"] = "design_detail(session, 'why'|'findings'|'contract'|'questions') if asked"
    if note:
        out["note"] = note
    return out


def _next_step(result: dict) -> str:
    """One line telling the client what to do, never what to ask beyond one."""
    if not result["draft_present"] and not result["variants"]:
        return ("Write the draft to that shape, then send it back with design_update. "
                "Answering the question first is optional.")
    gaps = result.get("evaluation", {}).get("priority", [])
    if gaps and not result["variants"]:
        if result["shading"]["offer"]:
            shades = ", ".join(s["shade"] for s in result["shading"]["shades"])
            return (f"Fix those, then write the recommended version plus these alternatives: "
                    f"{shades}. Submit all of them to design_shade with the recommended one "
                    "marked `recommended: true`.")
        return "Fix those and send the revision back with design_update."
    if result["shading"]["offer"] and not result["variants"]:
        shades = ", ".join(s["shade"] for s in result["shading"]["shades"])
        return (f"Write the recommended version plus these alternatives: {shades}. Keep every "
                "verbatim invariant byte-identical. Submit them all to design_shade with the "
                "recommended one marked `recommended: true`.")
    if result["variants"]:
        failed = [v["label"] for v in result["variants"]
                  if v["check"] and v["check"]["status"] == "fail"]
        if failed:
            return f"Fix and resubmit: {', '.join(failed)} lost protected content or a commitment."
        return "Call design_render and publish the page so the writer can compare the versions."
    return "Call design_render and publish the page."


@mcp.tool()
def design_open(text: str = "", title: str = "", stated: dict | None = None,
                inferred: dict | None = None) -> dict:
    """Start here. Paste a draft, or describe the situation, and get an answer.

    Answers immediately — there is no interview to get through first. If
    the situation is barely described the answer says so and offers one
    question; if it is well described it may offer none, which is praxis
    telling you that nothing further would change its advice.

    `text` is the draft, or empty when composing. `stated` is what the
    writer told you; `inferred` is what you concluded yourself. Keep the
    two apart — an inference that changes the recommendation comes back
    as a question rather than passing as fact. See design_schema for the
    field names.

    Relay the `answer` and `progress`. Offer `next_question` once. Do not
    ask anything beyond it.
    """
    # Validate before allocating. `store.blank` reserves the id by
    # creating the file, so returning an error after it ran left a
    # zero-byte session — and the reply handed the client that id and told
    # it to call design_update, which then died on the unparseable file.
    try:
        build(stated or {}, inferred or {})
    except ContractError as exc:
        return {"error": str(exc),
                "next_step": "Call design_schema for the allowed values, then design_open "
                             "again. No session was created.",
                "hint": "call design_schema for the allowed values"}
    record = store.blank(title or _title_from(text), text)
    return _update(record, stated, inferred, None)


def _title_from(text: str) -> str:
    """Name the session from the writing itself, so nobody is asked for one.

    Requires a real sentence: a salutation is the first line of most
    messages and "Hi Priya" names nothing.
    """
    for line in text.splitlines():
        line = line.strip().lstrip("#").strip()
        if len(line.split()) >= 5:
            return line[:60]
    return "untitled message"


@mcp.tool()
def design_update(session_id: str, stated: dict | None = None,
                  inferred: dict | None = None, draft: str = "") -> dict:
    """Record an answer, a correction, or a new draft, and get a fresh answer.

    Everything is recomputed, so a corrected guess changes the advice
    immediately rather than leaving a stale verdict behind. Use this for
    each question the writer chooses to answer — and simply stop calling
    it when they have had enough.
    """
    return _update(store.load(session_id), stated, inferred, draft or None)


def _update(record: dict, stated: dict | None, inferred: dict | None, draft: str | None) -> dict:
    if draft is not None:
        record["draft"] = draft
    record["values"] = {**record.get("values", {}), **(stated or {})}
    record["inferred"] = {**record.get("inferred", {}), **(inferred or {})}
    try:
        build(record["values"], record["inferred"])
    except ContractError as exc:
        # Carries next_step like every other reply: this correction is an
        # ordinary turn in the loop, not an exit from it.
        return {"session": record["id"], "error": str(exc),
                "next_step": "Call design_schema for the allowed values, then design_update "
                             "again with a corrected value. Nothing was saved.",
                "hint": "call design_schema for the allowed values"}
    store.save(record)
    return _reply(record)


@mcp.tool()
def design_detail(session_id: str, depth: str = "why") -> dict:
    """Drill into the answer — call this only when the writer asks.

    - `why` — which contract values chose that shape, what came second,
      and what this level of stakes obliges.
    - `findings` — every dimension, including the passes and the honest
      unknowns, not just the gaps.
    - `contract` — the situation as praxis has it, marked for what was
      stated and what was guessed.
    - `questions` — every remaining question at once, for someone who
      would rather answer them all than be offered one at a time.
    """
    record = store.load(session_id)
    result = store.result_for(record)
    if depth == "questions":
        return {"session": record["id"],
                "questions": [brief.next_question({**result, "questions": [q]})
                              for q in result["questions"]],
                "not_worth_asking": result["do_not_ask"],
                "note": "Unknown, but every possible answer lands on the same advice."}
    try:
        return {"session": record["id"], "depth": depth, "detail": brief.at_depth(result, depth)}
    except KeyError as exc:
        return {"error": str(exc), "available": list(brief.DEPTHS) + ["questions"]}


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
    # Exactly one submission is the recommendation — the one marked, or
    # the first (see design._recommended_index) — so everything else is an
    # alternative. Counting unmarked entries instead rejected the three
    # unmarked versions this tool's own docstring says are supported.
    alternatives = max(0, len(variants) - 1)
    if len(variants) > 1 and alternatives > MAX_ALTERNATIVES:
        # The bound is the product, not a default. Auditing a dozen
        # versions would put them all in the reply and the rendered page,
        # reintroducing exactly the choice overload bounded shading exists
        # to prevent.
        return {"session": session_id,
                "error": f"{alternatives} alternatives submitted; at most "
                         f"{MAX_ALTERNATIVES} are accepted alongside the recommendation",
                "next_step": f"Pick the {MAX_ALTERNATIVES} that price a real tradeoff — "
                             "design_open names them — and resubmit with the recommended "
                             "version marked `recommended: true`."}
    record = store.load(session_id)
    record["variants"] = [
        {"shade": v.get("shade"), "text": v.get("text", ""), "label": v.get("label", ""),
         "recommended": bool(v.get("recommended"))}
        for v in variants]
    store.save(record)
    return _reply(record)


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
           "path": str(path),
           # write_text encodes UTF-8; len() counts code points, so any
           # non-ASCII draft under-reported the size of the saved file.
           "bytes": len(html.encode("utf-8")), "headline": result["headline"],
           "next_step": "Publish `html` as an artifact and give the writer the link. "
                        "The page is self-contained; it needs no assets.",
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

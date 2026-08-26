"""Rendering a design session as a page a human can actually look at.

The contract, the strategy and its rationale, the questions worth asking,
the scorecard, and two variants side by side with their difference maps —
none of this survives being read out as chat prose. It is a comparison,
and comparisons want columns.

The output is one self-contained document: no scripts, no fonts, no
network. `document()` returns a whole page for the HTTP surface or a
saved file; `fragment()` returns the same body for a client that wraps
its own. Both are pure string building over the dict `design.design()`
returns, so the page can never show something the harness did not
compute.
"""

from html import escape
from . import strategy
from .design import design as _design  # noqa: F401  (documents the input shape)

CSS = """
/* Three type roles, and the split carries meaning rather than decoration:
   serif is what a person wrote, mono is what the machine measured, and the
   UI face is the harness talking about them. A reader can tell at a glance
   whose text they are looking at. No web fonts — the page must render
   offline and reach nothing. */
:root{
--ui:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
--prose:"Iowan Old Style","Charter",Georgia,"Times New Roman",serif;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
--bg:#f6f7f9;--panel:#fff;--ink:#14181d;--muted:#5f6773;--line:#dee3e9;
--accent:#1f4a7a;--chip:#eceff4;
--pass:#1c6b49;--gap:#a4541c;--unknown:#6b7280;--block:#a12b2b;--review:#7f611a}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
--bg:#101317;--panel:#171b21;--ink:#e6e9ed;--muted:#97a0ad;--line:#262c35;
--accent:#8ab0da;--chip:#1e242c;
--pass:#5fb98d;--gap:#d9955f;--unknown:#97a0ad;--block:#e28080;--review:#cfae5f}}
:root[data-theme=dark]{
--bg:#101317;--panel:#171b21;--ink:#e6e9ed;--muted:#97a0ad;--line:#262c35;
--accent:#8ab0da;--chip:#1e242c;
--pass:#5fb98d;--gap:#d9955f;--unknown:#97a0ad;--block:#e28080;--review:#cfae5f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 var(--ui)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.wrap{max-width:1080px;margin:0 auto;padding:2.5rem 1.25rem 5rem}
h1{font-size:1.55rem;margin:0 0 .3rem;letter-spacing:-.015em;text-wrap:balance}
h2{font-size:.72rem;text-transform:uppercase;letter-spacing:.11em;color:var(--muted);
margin:2.5rem 0 .7rem;font-weight:650}
h3{font-size:1rem;margin:0 0 .4rem;letter-spacing:-.005em;text-wrap:balance}
.headline{color:var(--muted);margin:0 0 .5rem;max-width:68ch}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;
padding:1.1rem 1.25rem;margin-bottom:.75rem}
.grid{display:grid;gap:.75rem}
@media(min-width:820px){.grid.two{grid-template-columns:1fr 1fr}}
.kv{display:grid;grid-template-columns:minmax(9rem,auto) 1fr;gap:.3rem .9rem;font-size:.93rem}
.kv dt{color:var(--muted)}
.kv dd{margin:0}
.chip{display:inline-block;font:650 .68rem/1.5 var(--ui);letter-spacing:.06em;
text-transform:uppercase;padding:.1rem .45rem;border-radius:3px;background:var(--chip);
color:var(--muted);vertical-align:middle}
.chip.pass{color:var(--pass)}.chip.gap{color:var(--gap)}.chip.unknown{color:var(--unknown)}
.chip.stated{color:var(--accent)}
.chip.inferred{color:var(--gap);border:1px dashed currentColor;background:none}
.chip.block{color:var(--block)}.chip.review{color:var(--review)}
/* The recommended sequence is a real order — the reader works through it in
   this order — so it is numbered. Nothing else on the page is. */
.seq{display:flex;flex-wrap:wrap;gap:.4rem;margin:.6rem 0 0;padding:0;list-style:none;
counter-reset:step}
.seq li{background:var(--chip);border-radius:4px;padding:.24rem .6rem;font-size:.85rem;
counter-increment:step}
.seq li::before{content:counter(step) ". ";color:var(--muted);font-variant-numeric:tabular-nums}
ul.tight{margin:.4rem 0 0;padding-left:1.1rem}
ul.tight li{margin:.16rem 0}
.ev{font:12.5px/1.5 var(--mono);color:var(--muted);background:var(--chip);border-radius:3px;
padding:.1rem .35rem;display:inline-block;margin:.16rem .2rem 0 0;
font-variant-numeric:tabular-nums;max-width:100%;overflow-wrap:anywhere}
.row{border-top:1px solid var(--line);padding:.75rem 0}
.row:first-of-type{border-top:none;padding-top:.25rem}
.row .top{display:flex;gap:.55rem;align-items:baseline;flex-wrap:wrap}
.row .q{color:var(--muted);font-size:.85rem;margin:.15rem 0 .3rem}
.rec{font-size:.9rem;color:var(--accent);margin-top:.3rem}
.muted{color:var(--muted)}
.small{font-size:.85rem}
.nums{font-variant-numeric:tabular-nums}
/* The message itself, in the one face reserved for a person's own words. */
pre.doc{white-space:pre-wrap;word-wrap:break-word;font:15px/1.6 var(--prose);
background:var(--chip);padding:.9rem 1rem;border-radius:6px;margin:.55rem 0 0;
overflow-x:auto;max-width:62ch}
.violation{border-left:2px solid var(--block);padding-left:.7rem;margin:.55rem 0}
.violation.review{border-color:var(--review)}
footer{margin-top:3rem;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line);
padding-top:1rem;max-width:68ch}
"""


def _chip(text: str, kind: str = "") -> str:
    return f'<span class="chip {escape(kind)}">{escape(str(text))}</span>'


def _evidence(items) -> str:
    return "".join(f'<span class="ev">{escape(str(i))}</span>' for i in items)


def _section(title: str, body: str) -> str:
    return f"<h2>{escape(title)}</h2>{body}" if body else ""


def fragment(result: dict) -> str:
    """The page body for a design result: style block plus content."""
    parts = [f"<style>{CSS}</style>", '<div class="wrap">',
             f"<h1>{escape(_title(result))}</h1>",
             f'<p class="headline">{escape(result.get("headline", ""))}</p>']
    parts += [_strategy(result), _changes(result), _contract(result), _questions(result),
              _evaluation(result), _shading(result), _variants(result), _invariants(result)]
    parts.append(
        '<footer>Generated by praxis. Every statement above is computed from the contract '
        'and the draft — no model wrote this page, and none was called to produce it. '
        'Detectors are conservative: <em>unknown</em> means not machine-checkable, not absent.'
        "</footer></div>")
    return "".join(p for p in parts if p)


def document(result: dict) -> str:
    """A complete standalone HTML page."""
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{escape(_title(result))}</title></head><body>{fragment(result)}</body></html>")


def _title(result: dict) -> str:
    sections = result.get("contract", {}).get("sections", {})
    genre = sections.get("artifact", {}).get("genre")
    reader = sections.get("reader", {}).get("primary_reader")
    if genre and reader:
        return f"{genre} → {reader}"
    return genre or reader or "Communication design"


def _strategy(result: dict) -> str:
    s = result.get("strategy")
    if not s:
        return ""
    # A list item has room for the gloss; it goes in muted so the machine
    # pair stays the thing being read and the gloss stays the aside.
    because = "".join(
        f"<li>{escape(b['reason'])}"
        + (f' <span class="muted">({escape(b["gloss"])})</span>' if b.get("gloss") else "")
        + "</li>"
        for b in s["because"]
    ) or "<li>nothing in the contract selects it yet</li>"
    seq = "".join(f"<li>{escape(step)}</li>" for step in s["sequence"])
    runner = s["runner_up"]
    why_not = ("; ".join(strategy.inline(w) for w in runner["why_not"])
               or ("against this it "
                   + "; ".join(strategy.divergence(d)
                               for d in runner["instead_of"])
                   if runner["instead_of"] else "")
               or "it scored identically; the tie broke on declaration order")
    reqs = "".join(f"<li>{escape(r)}</li>" for r in s["requirements"])
    return _section("Recommended strategy", f"""<div class="panel">
<div class="top"><h3>{escape(s['title'])}</h3> {_chip(s['confidence'] + ' confidence')}</div>
<p class="small muted">{escape(s['summary'])}</p>
<ol class="seq">{seq}</ol>
<h2 style="margin-top:1.2rem">Because</h2><ul class="tight small">{because}</ul>
<p class="small muted">Runner-up: <strong>{escape(runner['title'])}</strong> — {escape(why_not)}.</p>
</div>
<div class="panel"><h3>What this level of stakes requires</h3>
<ul class="tight small">{reqs}</ul>
<p class="small muted">Evidence standard: {escape(s['evidence_standard'])}</p></div>""")


def _changes(result: dict) -> str:
    """The located edits, in document order.

    Ordered by position rather than by dimension: a writer works down the
    page, and grouping by which rule produced a change makes them jump
    around their own draft.
    """
    changes = result.get("transform")
    if not changes:
        return ""
    edits = sorted(changes["edits"],
                   key=lambda e: e["at"] if e["at"] is not None else e["where"]["start"])
    rows = []
    for edit in edits:
        place = (f"insert at {edit['at']}" if edit["at"] is not None
                 else f"characters {edit['where']['start']}\u2013{edit['where']['end']}")
        target = (f'<pre class="doc">{escape(edit["where"]["text"])}</pre>'
                  if edit["where"] else "")
        blocked = ('<div class="violation">' + _chip("blocked", "block")
                   + '<p class="small">This change overlaps content you marked protected. '
                     'Your constraint and the advice are in tension; praxis will not '
                     'choose between them.</p></div>') if edit["blocked_by"] else ""
        rows.append(f"""<div class="row"><div class="top">{_chip(edit['kind'])}
<h3>{escape(edit['dimension'].replace('_', ' '))}</h3>
<span class="small muted nums">{escape(place)}</span></div>
<p class="small">{escape(edit['instruction'])}</p>{target}{blocked}</div>""")

    body = f'<div class="panel">{"".join(rows)}</div>' if rows else (
        '<div class="panel small muted">No located changes against this contract.</div>')
    folded = changes["folded_into"]
    if folded:
        body += ('<div class="panel small muted"><strong>Folded into another change:</strong> '
                 + ", ".join(f"{escape(k)} &rarr; {escape(v)}" for k, v in folded.items())
                 + ". One instruction rather than three at the same spot.</div>")
    if changes["no_edit_for"]:
        body += ('<div class="panel small"><strong>No change could be located for:</strong> '
                 + _evidence(changes["no_edit_for"])
                 + '<p class="muted">These gaps are real and praxis could not point at '
                   'where to fix them. A human decides.</p></div>')
    if changes["unlocatable"]:
        body += ('<div class="panel small"><strong>Protected, but not in the draft:</strong> '
                 + _evidence(changes["unlocatable"])
                 + '<p class="muted">Declared untouchable and absent, so nothing was '
                   'protected by it.</p></div>')
    return _section("Located changes", body)


def _contract(result: dict) -> str:
    c = result.get("contract", {})
    sections = c.get("sections", {})
    if not sections:
        return _section("Contract", '<div class="panel muted small">Empty — nothing has been '
                                    'stated or inferred about this situation yet.</div>')
    prov = c.get("provenance", {})
    panels = []
    for name, fields in sections.items():
        rows = "".join(
            f"<dt>{escape(k)}</dt><dd>{escape(_fmt(v))} {_chip(prov.get(k, 'unset'), prov.get(k, ''))}</dd>"
            for k, v in fields.items())
        panels.append(f'<div class="panel"><h3>{escape(name)}</h3><dl class="kv">{rows}</dl></div>')
    body = f'<div class="grid two">{"".join(panels)}</div>'
    if c.get("assumptions"):
        body += ('<div class="panel"><h3>Assumptions to confirm</h3><p class="small muted">'
                 'Inferred, not stated. Each one is the assistant guessing.</p>'
                 f'<p>{_evidence(c["assumptions"])}</p></div>')
    return _section("Communication contract", body)


def _fmt(value) -> str:
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    return str(value)


def _questions(result: dict) -> str:
    questions = result.get("questions") or []
    skipped = result.get("do_not_ask") or []
    if not questions and not skipped:
        return ""
    rows = []
    for q in questions:
        splits = "".join(
            f"<li><strong>{escape(struct)}</strong> if {escape(', '.join(vals))}</li>"
            for struct, vals in q["decides_between"].items())
        rows.append(f"""<div class="row"><div class="top"><h3>{escape(q['question'])}</h3>
{_chip(q['status'], 'inferred' if q['status'] == 'inferred' else '')}</div>
<p class="q">field <code>{escape(q['field'])}</code> — {escape(q['why_it_matters'])}</p>
<ul class="tight small">{splits}</ul></div>""")
    hidden = result.get("questions_outstanding", len(questions)) - len(questions)
    if rows and hidden > 0:
        # The headline reports the true total; without this the page listed
        # three and gave no sign the other four existed.
        rows.append(f'<div class="row"><p class="small muted">{hidden} further question'
                    f'{"s" if hidden > 1 else ""} would also change the answer, shown once '
                    'these are settled.</p></div>')
    body = f'<div class="panel">{"".join(rows)}</div>' if rows else ""
    if skipped:
        body += ('<div class="panel"><h3>Would not change the strategy</h3><p class="small muted">'
                 'Unknown, but every possible answer lands on the same structure and the same '
                 'shading offer. Worth knowing, not worth interrupting the writer for.</p>'
                 f'<p>{_evidence(skipped)}</p></div>')
    return _section("Questions that would change the answer", body)


def _evaluation(result: dict) -> str:
    e = result.get("evaluation")
    if not e:
        return ""
    rows = []
    for d in e["dimensions"]:
        rec = f'<p class="rec small">→ {escape(d["recommendation"])}</p>' if d["recommendation"] else ""
        ev = f'<p>{_evidence(d["evidence"])}</p>' if d["evidence"] else ""
        rows.append(f"""<div class="row"><div class="top">{_chip(d['status'], d['status'])}
<h3>{escape(d['dimension'].replace('_', ' '))}</h3></div>
<p class="q">{escape(d['question'])}</p><p class="small">{escape(d['finding'])}</p>{ev}{rec}</div>""")
    s = e["summary"]
    head = (f'<p class="small muted">{s["pass"]} pass · {s["gap"]} gap · {s["unknown"]} unknown '
            f'— <strong>{escape(e["verdict"])}</strong>. No overall score: a number with no '
            "criteria behind it invites optimising the number.</p>")
    return _section("Fit for purpose", f'<div class="panel">{head}{"".join(rows)}</div>')


def _shading(result: dict) -> str:
    sh = result.get("shading")
    if not sh or result.get("variants"):
        return ""
    if not sh["offer"]:
        return _section("Variants", '<div class="panel"><h3>One version, not a menu</h3>'
                        f'<p class="small muted">{escape(sh["reason"])}.</p></div>')
    cards = "".join(f"""<div class="panel"><div class="top"><h3>{escape(s['title'])}</h3></div>
<p class="small">{escape(s['behaviour'])}</p>
<p class="small muted"><strong>Tradeoff:</strong> {escape(s['tradeoff'])}</p>
<p class="small muted"><strong>Tension:</strong> {escape(s['tension'])}</p></div>""" for s in sh["shades"])
    return _section("Shades worth exploring", f'<div class="grid two">{cards}</div>')


def _variants(result: dict) -> str:
    """The versions side by side.

    The recommendation comes first and says so. Every alternative names
    what its difference map was measured against, because the same
    numbers mean different things depending on the reference — a reader
    who assumes the deltas are against their own draft will misread every
    one of them.
    """
    variants = result.get("variants") or []
    if not variants:
        return ""
    cards = []
    for v in variants:
        check = v.get("check")
        if check is None:
            cards.append(f"""<div class="panel"><div class="top">{_chip(v['role'], 'stated')}
<h3>{escape(v['label'])}</h3></div>
<p class="small muted">{escape(v.get('tradeoff', ''))}</p>
<pre class="doc">{escape(v['text'])}</pre>
<p class="small muted">{escape(v.get('note', 'not checked'))}.</p></div>""")
            continue
        dm = check.get("difference_map", {})
        status = check.get("status", "unchecked")
        kind = {"pass": "pass", "review": "review", "fail": "block"}.get(status, "unknown")
        viol = "".join(
            f'<div class="violation {"review" if x["severity"] == "review" else ""}">'
            f'{_chip(x["kind"], "review" if x["severity"] == "review" else "block")}'
            f'<p class="small">{escape(x["detail"])}</p><p>{_evidence(x["items"])}</p></div>'
            for x in check.get("violations", []))
        moved = "".join(f'<li class="nums">{escape(m)}</li>' for m in dm.get("moved", []))
        held = "".join(f'<li class="nums">{escape(h)}</li>' for h in dm.get("held", []))
        fid = "".join(
            f'<li>{"&#10003;" if f["met"] else "&#10007;"} {escape(f["expected"])} '
            f'({escape(f["observed"])})</li>'
            for f in dm.get("shade_fidelity", []))
        length = dm.get("length", {})
        against = escape(dm.get("compared_to", "the source"))
        cards.append(f"""<div class="panel"><div class="top">{_chip(status, kind)}
{_chip(v['role'], 'stated' if v['role'] == 'recommended' else '')}
<h3>{escape(v['label'])}</h3></div>
<p class="small muted">{escape(v.get('tradeoff', ''))}</p>
<pre class="doc">{escape(v['text'])}</pre>
{viol}
<h2 style="margin-top:1rem">Changed, against {against}</h2>
<ul class="tight small">{moved or '<li class="muted">nothing a detector can see</li>'}</ul>
<h2>Deliberately unchanged</h2>
<ul class="tight small">{held or _nothing_held(dm)}</ul>
<h2>Did it do what the shade claims</h2>
<ul class="tight small">{fid or '<li class="muted">no shade declared</li>'}</ul>
{_voice(v)}
<p class="small muted nums">{length.get('words_before', '?')} &rarr; {length.get('words_after', '?')} words &middot;
similarity {dm.get('similarity', '?')}</p></div>""")
    return _section("Versions and difference maps", f'<div class="grid two">{"".join(cards)}</div>')


def _nothing_held(dm: dict) -> str:
    """An empty "held" list has two very different causes.

    Either the reference carried no detectable signals at all, or it
    carried them and every single one moved. Reporting both as "none"
    tells the reader nothing; the second is a finding.
    """
    if dm.get("moved"):
        return '<li class="muted">nothing held steady &mdash; every detected signal moved</li>'
    return '<li class="muted">no detectable signals in the reference</li>'


def _voice(variant: dict) -> str:
    """Which of the writer's habits this version kept.

    Never framed as a verdict. A dropped habit is often exactly what the
    version was asked to do, and praxis has no way to know which.
    """
    result = variant.get("voice")
    if not result:
        return ""
    if result["status"] == "unknown":
        return f'<h2>Voice</h2><p class="small muted">{escape(result["finding"])}</p>'
    moved = "".join(
        f'<li class="nums">{escape(m["habit"])}: {m["before"]} &rarr; {m["after"]} '
        f'{escape(m["unit"])}</li>' for m in result["moved"])
    if not moved:
        moved = '<li class="muted">every measured habit held</li>'
    held = ", ".join(escape(h) for h in result["held"])
    held_line = f'<p class="small muted">Held: {held}.</p>' if held else ""
    return ('<h2>Voice</h2><ul class="tight small">' + moved + "</ul>" + held_line
            + '<p class="small muted">Habits, not authorship &mdash; and a dropped habit '
              'may be what the version was for.</p>')


def _invariants(result: dict) -> str:
    inv = result.get("invariants")
    if not inv:
        return ""
    tokens = _evidence(inv.get("tokens", [])) or '<span class="muted small">none detected</span>'
    phrases = _evidence(inv.get("phrases", []))
    presence = "".join(f"<li><strong>{escape(k)}</strong>: {_evidence(v[:3])}</li>"
                       for k, v in inv["presence"].items())
    phrase_block = (f'<h3 style="margin-top:1rem">Phrases you declared</h3>'
                    '<p class="small muted">Must appear, and may be re-wrapped: a phrase '
                    'you typed with spaces still counts when the draft breaks the line '
                    'inside it.</p><p>' + phrases + "</p>") if phrases else ""
    return _section("What may not move", f"""<div class="panel">
<h3>Figures and references</h3><p class="small muted">Extracted from both versions and
compared exactly &mdash; a changed figure is not a preserved one.</p><p>{tokens}</p>
{phrase_block}
<h3 style="margin-top:1rem">Presence</h3><p class="small muted">Must still be detectable after
rewriting, in any wording.</p><ul class="tight small">{presence or '<li class="muted">none</li>'}</ul>
</div>""")

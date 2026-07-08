from .validation import protected_tokens

def render_prompt(result: dict) -> str:
    """Render the flagged items of a run as a self-contained LLM prompt.

    The pipeline stays deterministic: this only packages what was flagged for
    human judgment as portable Markdown. The user carries it to a model and
    brings the proposals back — the harness never calls one.

    Returns "" when nothing was flagged.
    """
    flagged = [t for t in result["transformations"] if not t["applied"]]
    if not flagged:
        return ""

    pack = result.get("pack", {})
    tokens = sorted(protected_tokens(result["final"]))
    token_list = ", ".join(f"`{t}`" for t in tokens) if tokens else "(none detected)"

    items = []
    for t in flagged:
        items.append(f"""### {t['id']} · rule {t['rule_id']} ({t['recommendation_id']})

Why it was flagged: {t['reason']}

Evidence:

> {t['before']}""")

    return f"""# praxis review handoff

This document was processed by praxis, a deterministic transformation pipeline
(pack: {pack.get('id', 'unknown')} v{pack.get('version', '?')} — {pack.get('title', '')}).
Mechanical fixes were already applied. The items below were flagged for human
judgment; the pipeline never edits them. Your job is to propose resolutions a
human can accept or reject.

## Instructions

For each flagged item, propose a concrete rewrite of the evidence — or state
"no change" with a one-sentence reason. Rules:

1. Protected tokens must appear verbatim in any rewrite: {token_list}
2. Preserve meaning. Do not add facts that are not in the document.
3. Answer with one section per item, titled by its ID, containing
   **Proposed rewrite:** and **Rationale:** — nothing else.

## Flagged items

{(chr(10) + chr(10)).join(items)}

## Document (after applied transformations)

```markdown
{result['final']}
```
"""

"""Where a design session lives between tool calls.

A session is the contract plus whatever prose has been written against
it. It has to outlive a single tool call for the obvious reason — the
questions are asked in one turn and answered in the next — and a less
obvious one: the contract is the artifact worth keeping. Drafts get
rewritten; the decision about who this is for and what may not move is
what a writer should be able to come back to next week.

Storage is a JSON file per session under the workspace directory. No
database, no schema migrations, no server. `PRAXIS_HOME` overrides the
location; the default follows the XDG data convention.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from praxis.contract import build
from praxis.design import design

SLUG = re.compile(r"[^a-z0-9]+")


def home() -> Path:
    root = os.environ.get("PRAXIS_HOME")
    if root:
        return Path(root).expanduser()
    base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return Path(base).expanduser() / "praxis"


def sessions_dir() -> Path:
    path = home() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slugify(text: str, fallback: str = "session") -> str:
    slug = SLUG.sub("-", (text or "").strip().lower()).strip("-")[:48]
    return slug or fallback


def path_for(session_id: str) -> Path:
    """Resolve a session id to a file inside the sessions directory.

    The id is slugified, not trusted: ids arrive from a model, and
    treating one as a path fragment is how `../../.ssh/id_rsa` becomes a
    session. Slugification collapses every separator, so the result can
    only ever name a file in this one directory.
    """
    safe = slugify(session_id, "")
    if not safe:
        raise ValueError(f"invalid session id {session_id!r}")
    return sessions_dir() / f"{safe}.json"


def new_id(title: str) -> str:
    """A readable, collision-free id: the title, suffixed if taken."""
    base = slugify(title)
    candidate, n = base, 2
    while path_for(candidate).exists():
        candidate, n = f"{base}-{n}", n + 1
    return candidate


def save(record: dict) -> dict:
    record["updated"] = _now()
    record.setdefault("created", record["updated"])
    path_for(record["id"]).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def load(session_id: str) -> dict:
    path = path_for(session_id)
    if not path.exists():
        raise FileNotFoundError(
            f"no session {session_id!r}. Known: {', '.join(s['id'] for s in listing()) or 'none'}")
    return json.loads(path.read_text(encoding="utf-8"))


def listing() -> list[dict]:
    """Every session, most recently touched first."""
    out = []
    for path in sessions_dir().glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        out.append({"id": record.get("id", path.stem), "title": record.get("title", ""),
                    "updated": record.get("updated", ""),
                    "has_draft": bool(record.get("draft", "").strip()),
                    "variants": len(record.get("variants", []))})
    return sorted(out, key=lambda r: r["updated"], reverse=True)


def blank(title: str, draft: str = "") -> dict:
    return {"id": new_id(title), "title": title, "draft": draft,
            "values": {}, "inferred": {}, "variants": [], "created": _now()}


def result_for(record: dict) -> dict:
    """Run the design layer over a stored session.

    Nothing derived is persisted — the strategy, the questions, and the
    scorecard are recomputed from the contract every time. A stored
    verdict would go stale the moment a rule changed and there would be
    no way to tell which sessions were carrying an old answer.
    """
    contract = build(record.get("values") or {}, record.get("inferred") or {})
    return design(record.get("draft", ""), contract, record.get("variants") or [])

"""A local viewer for saved design sessions.

Stdlib `http.server`, loopback only, no dependencies, no state of its
own. It exists because the artifact path assumes a client that can
publish pages, and a writer working from a terminal deserves the same
view. Pages are rendered on request from the stored contract, so a
browser refresh always shows what the current rules compute — never a
cached verdict from an older version of the harness.

This is not an application server. There is no upload, no mutation, no
account, and nothing listens beyond the loopback interface.
"""

from __future__ import annotations

import ipaddress
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from praxis import render
from praxis.mcp import store

INDEX_CSS = (render.CSS + "\na{color:var(--accent);text-decoration:none}"
             "\na:hover{text-decoration:underline}")


def _index() -> str:
    rows = "".join(
        f'<div class="row"><div class="top"><h3><a href="/s/{escape(s["id"])}">'
        f'{escape(s["title"] or s["id"])}</a></h3>'
        f'<span class="chip">{escape(str(s["variants"]))} variant(s)</span></div>'
        f'<p class="q">{escape(s["updated"])}</p></div>'
        for s in store.listing())
    body = rows or '<p class="muted small">No sessions yet. Open one through the MCP server.</p>'
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>praxis sessions</title><style>{INDEX_CSS}</style></head><body>"
            f'<div class="wrap"><h1>Design sessions</h1>'
            f'<p class="headline">{escape(str(store.home()))}</p>'
            f'<div class="panel">{body}</div></div></body></html>')


class Handler(BaseHTTPRequestHandler):
    server_version = "praxis"

    def do_GET(self) -> None:  # noqa: N802 (http.server's required name)
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/":
            return self._send(200, _index())
        if path.startswith("/s/"):
            session_id = path[3:]
            try:
                record = store.load(session_id)
            except (FileNotFoundError, ValueError):
                return self._send(404, self._error(f"No session {session_id!r}."))
            return self._send(200, render.document(store.result_for(record)))
        return self._send(404, self._error("Not found."))

    def _error(self, message: str) -> str:
        return ("<!doctype html><meta charset=\"utf-8\">"
                f"<style>{render.CSS}</style><div class=\"wrap\"><h1>praxis</h1>"
                f"<p class=\"headline\">{escape(message)}</p>"
                "<p><a href=\"/\">All sessions</a></p></div>")

    def _send(self, status: int, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args) -> None:
        """Quiet by default: this runs beside a conversation, not in a log."""


def _is_loopback(host: str) -> bool:
    """Is this address reachable only from this machine?

    Decided by parsing the address, not by matching a list of spellings.
    An earlier allowlist held the literal `""` — and `bind(("", port))`
    binds every interface, so `--host ""` walked straight through a guard
    written specifically to stop that. Anything that is not a parseable
    loopback address is refused, which covers `""`, `0.0.0.0` and `::`
    without needing to have thought of them.
    """
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    # The viewer serves saved drafts and contracts with no authentication
    # of any kind, on the stated understanding that it is reachable only
    # from this machine.
    if not _is_loopback(host):
        raise SystemExit(
            f"praxis serve binds loopback only; refused {host!r}.\n"
            "Saved drafts and contracts are served without authentication. "
            "To reach them from another machine, forward the port over a "
            "tunnel you control rather than binding a public interface.")
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"praxis viewer on http://{host}:{port}  (workspace: {store.home()})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()

# Vendored fonts

**Type:** guide · [document types](../../AGENTS.md#documents)

DM Mono, subset to latin, at the two weights the chrome uses.

These are **vendored rather than linked** because both pages promise the
same thing: the draft never leaves the browser, and the page works
offline. A Google Fonts `<link>` does not send the draft anywhere, but it
does tell Google the visitor's IP and that they opened the page — and it
breaks offline entirely. The claim on the page is unconditional, so the
implementation has to be.

`scripts/check_no_network.sh` enforces it, and CI runs it. That check
exists because the older one, "the rendered page reaches nothing", only
covered the CLI-rendered `artifacts/design.html` — the web pages named in
the same guarantee were never looked at, and carried a CDN font for
months.

| File | Weight | Source |
|---|---|---|
| `dm-mono-400-latin.woff2` | 400 | Google Fonts `dmmono/v16`, latin subset |
| `dm-mono-500-latin.woff2` | 500 | Google Fonts `dmmono/v16`, latin subset |

Licence: SIL Open Font License 1.1 — `OFL.txt`, copied from
[google/fonts](https://github.com/google/fonts/tree/main/ofl/dmmono).
The OFL requires the licence travel with the font, which is why it is
here rather than referenced.

To refresh, request the CSS with a browser user-agent (an older one is
served TTF instead of woff2), take the **latin** `src` URLs, and keep the
filenames above so `fonts.css` does not need editing.

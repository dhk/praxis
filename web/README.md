# praxis viewer

A static, single-page viewer for the praxis artifact trail (RFC-0002 /
`docs/design/praxis-viewer`). The user enters or uploads a document, runs the
pipeline **once**, then steps through the six passes and their artifacts.
Stepping is inspection, not execution — the artifact trail is the product.

## How it works

- The existing Python `praxis` package runs **unchanged in the browser** via
  Pyodide (CPython on WebAssembly), inside a web worker, so the UI is evidence
  of what the harness actually does. There is no TypeScript port of the rules.
- No backend, no accounts, no persistence — documents never leave the browser.
- The engine boundary is `src/engine.js`: the UI calls `runPipeline(source)`
  and gets the whole trail; only that module (and its worker) knows Python
  exists.
- A service worker caches everything on first load, so the site works offline
  afterwards.
- "Download artifact trail" produces a zip whose six files are byte-identical
  to what `python -m praxis run` writes.
- Packs are selectable in the Input panel; the pack list comes from the Python
  registry (`praxis/packs.py`) via the worker, so the UI can never drift from
  the harness. Bundled examples each select their matching pack.
- Step 7 (Compare) shows original and final side by side with proportional
  scroll sync.

## Build & run locally

```bash
bash scripts/build_site.sh     # downloads the Pyodide runtime on first run
python -m http.server 8000 -d dist
# open http://localhost:8000
```

The build copies this directory plus `praxis/*.py`, the pack, and the bundled
example into `dist/`, and vendors the Pyodide runtime so the deployed site is
fully same-origin (no CDN scripts at runtime).

## Deploy

**GitHub Pages** — `.github/workflows/deploy-pages.yml` builds and deploys on
every push to `main`. One-time setup: repository **Settings → Pages → Source →
GitHub Actions**.

**Vercel** — import the repo; `vercel.json` already sets the build command and
output directory. No framework, no environment variables.

All asset URLs are relative, so the site works at a subpath
(`https://<user>.github.io/praxis/`) as well as at a domain root.

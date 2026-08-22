# Praxis viewer

**Type:** guide · [document types](../AGENTS.md#documents)

**[Open the live viewer](https://dhk.github.io/praxis/).**

The viewer is the browser interface to Praxis's inspectable artifact trail. Paste or upload Markdown, choose a transformation pack, run the pipeline once, then move through its observations, recommendations, transformations, validation, report, and comparison. Stepping is inspection rather than repeated execution.

## Privacy and artifacts

The deployed application is static. It has no Praxis backend, accounts, database, or server-side document upload: source documents and results are processed locally in the browser. The page requests its display font from Google Fonts, but no code sends document contents with that request. A service worker caches the viewer's application assets after the initial load so the viewer can subsequently work offline.

“Download artifact trail” creates a zip containing the same six artifact files as the CLI. The files are intended to be byte-identical for the same input and pack, making the browser output portable to a local review or handoff.

## How the shared engine runs

The existing Python `praxis` package runs in a web worker through Pyodide (CPython compiled to WebAssembly). The viewer does not port transformation rules to JavaScript:

1. `src/engine.js` exposes a small `runPipeline(source, pack)` boundary to the UI.
2. `src/worker.js` loads Pyodide and the packaged Python source off the main thread.
3. Python's `run_pipeline` executes the same registry and operations used by `python -m praxis`.
4. The worker returns the complete result for inspection or packages the six-file zip.

The pack list also comes from the Python registry, preventing the UI from maintaining a separate list. See the repository [architecture documentation](../docs/architecture.md) for the full system view and trust boundary.

## Build and run locally

There is no npm package or published viewer bundle to install. Build from this repository checkout:

```bash
git clone https://github.com/dhk/praxis.git
cd praxis
bash scripts/build_site.sh
python3 -m http.server 8000 -d dist
```

Open <http://localhost:8000> and wait for the engine status to become ready. Stop the server with `Ctrl-C`.

The first build downloads pinned Pyodide 0.26.4 assets from the npm registry and caches them under `.cache/`. The build then copies `web/`, `praxis/*.py`, bundled examples, and the runtime into `dist/`. At runtime, the Python and Pyodide assets are same-origin and no CDN scripts are required; the stylesheet still requests the display font from Google Fonts.

## Deployment

GitHub Pages is the canonical deployment. `.github/workflows/deploy-pages.yml` builds and deploys the viewer after pushes to `main`; the configured public URL is <https://dhk.github.io/praxis/>.

`vercel.json` also describes a Vercel build using the same script and `dist/` output. No framework or environment variables are required. Asset URLs are relative so the result works at a domain root or a subpath such as `/praxis/`.

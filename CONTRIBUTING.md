# Contributing

**Type:** guide · [document types](AGENTS.md#documents)

Praxis is an early reference implementation. Contributions should strengthen its inspectable pipeline and preserve the contract shared by the CLI and browser viewer.

Every contribution should answer:

1. What observation does this enable?
2. What transformation does this introduce or improve?
3. How is the result validated?
4. How can another engineer test it?

Prefer another explicit operation over another opaque prompt.

## Development setup

Python 3.10 or newer is required. There is no published PyPI/npm package or curl installer; development uses a source checkout.

```bash
git clone https://github.com/dhk/praxis.git
cd praxis
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
python -m pytest
```

Run a smoke transformation and inspect the generated files:

```bash
python -m praxis run examples/concise_scientific_writing/input.md --out artifacts/demo
```

`Validation: pass` should be printed, and `artifacts/demo/` should contain the six files documented in the [artifact contract](docs/architecture.md#artifact-contract).

## Continuous integration

Every pull request runs [`.github/workflows/tests.yml`](.github/workflows/tests.yml):

| Job | What it proves |
| --- | --- |
| `pytest (py3.10, py3.13)` | The suite passes on the declared floor and on current Python. |
| `engine without the mcp extra` | `mcp` is genuinely optional — the engine works, and is tested, in a checkout that never installed a transport. |
| `documented commands` | Every command the README and CLAUDE.md promise actually runs, and the artifact contract they describe appears. |
| `viewer builds` | `scripts/build_site.sh` still works, and `praxis/mcp/` has not leaked into the browser bundle. |

CI is not a substitute for running the checks below. It runs what can be
automated; the browser and artifact checks in the table further down are
still yours to do.

## Validate the change you made

Always run the full Python suite:

```bash
python -m pytest
```

Then add the checks relevant to the change:

| Change | Required validation |
| --- | --- |
| Rules, packs, pipeline, validation, metrics, or reports | Add or update regression tests; run the CLI smoke command; inspect observations, transformations, validation, and report output. Keep `packs/*/pack.yaml` aligned with the Python registry. |
| Artifact names, shapes, serialization, or formatting | Verify all six CLI files and the browser zip remain byte-identical for the same source and pack. Treat intentional differences as architecture changes and document them. |
| CLI or installation documentation | Run every documented command in a clean virtual environment created from a fresh checkout. |
| Viewer UI or browser bridge | Run the Python suite, build the static site, serve it over HTTP, and exercise input, pack selection, pipeline inspection, and artifact download in a browser. |
| Build or deployment files | Run `bash scripts/build_site.sh`, serve `dist/`, check asset loading without runtime CDN requests, and verify subpath-safe URLs. |
| Documentation only | Check links and diagrams, then execute any commands the edited text tells readers to run. |

To build and serve the viewer locally:

```bash
bash scripts/build_site.sh
python -m http.server 8000 -d dist
```

Open <http://localhost:8000>. The first build downloads the pinned Pyodide runtime from the npm registry into `.cache/`; the running site uses the vendored, same-origin copy.

## Pull requests

- Keep each pull request focused and explain user or developer impact.
- Include the exact commands and manual checks used for validation.
- Update architecture or interface documentation when a boundary or artifact contract changes.
- Do not duplicate the Python rules in JavaScript; both interfaces must continue to use the shared engine.
- Do not commit generated `artifacts/`, `dist/`, virtual environments, or downloaded caches.

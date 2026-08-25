#!/usr/bin/env bash
# Build the static viewer site into dist/.
#
# The site is fully same-origin: the Pyodide runtime is downloaded here at
# build time (from the npm registry, cached in .cache/) rather than loaded
# from a CDN, so the deployed site works offline and needs no third-party
# script origins.
set -euo pipefail
cd "$(dirname "$0")/.."

PYODIDE_VERSION="0.26.4"
CACHE_DIR="${PYODIDE_CACHE_DIR:-.cache/pyodide-$PYODIDE_VERSION}"

rm -rf dist
mkdir -p dist
cp -r web/. dist/

# The Python package is served as source files and imported unchanged in the
# browser — the UI is evidence of what the harness actually does.
mkdir -p dist/py/praxis dist/examples
cp praxis/*.py dist/py/praxis/
cp examples/concise_scientific_writing/input.md dist/examples/technical-note.md
cp examples/hotaling_2020/input.md dist/examples/hotaling-2020.md
cp examples/drift_study/input.md dist/examples/drift-study.md
cp examples/claude_skill/SKILL.md dist/examples/claude-skill.md
cp examples/resume/input.md dist/examples/resume.md
cp examples/repo_docs/input.md dist/examples/repo-docs.md
cp examples/pm_writing/input.md dist/examples/pm-writing.md

files=$(cd praxis && ls *.py | sed 's/^/"/;s/$/"/' | paste -sd, -)
printf '{"files":[%s]}\n' "$files" > dist/py/manifest.json

mkdir -p "$CACHE_DIR" dist/vendor/pyodide
if [ ! -f "$CACHE_DIR/.complete" ]; then
  echo "Fetching pyodide $PYODIDE_VERSION from the npm registry"
  curl -fsSL --retry 3 \
    "https://registry.npmjs.org/pyodide/-/pyodide-$PYODIDE_VERSION.tgz" \
    -o "$CACHE_DIR/pyodide.tgz"
  tar -xzf "$CACHE_DIR/pyodide.tgz" -C "$CACHE_DIR" package/
  for f in pyodide.js pyodide.asm.js pyodide.asm.wasm python_stdlib.zip pyodide-lock.json; do
    mv "$CACHE_DIR/package/$f" "$CACHE_DIR/$f"
  done
  rm -rf "$CACHE_DIR/package" "$CACHE_DIR/pyodide.tgz"
  touch "$CACHE_DIR/.complete"
fi
cp "$CACHE_DIR"/pyodide.js "$CACHE_DIR"/pyodide.asm.js "$CACHE_DIR"/pyodide.asm.wasm \
   "$CACHE_DIR"/python_stdlib.zip "$CACHE_DIR"/pyodide-lock.json dist/vendor/pyodide/

echo "Built dist/ ($(du -sh dist | cut -f1))"

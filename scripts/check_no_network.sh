#!/usr/bin/env bash
# Every surface that claims the draft never leaves the browser must be
# provably offline. That claim is on the pages themselves — design.html's
# own meta description says "nothing leaves the browser" — so it is the
# implementation that has to be unconditional, not the wording.
#
# This exists because the older check, "the rendered page reaches nothing",
# only ever grepped the CLI-rendered artifacts/design.html. The web pages
# named in the same guarantee were never looked at, and carried a Google
# Fonts CDN link for months (#37).
#
# What counts as reaching the network is what the page fetches on its own:
# `src` on any element, and `href` on <link> (stylesheets, preconnect,
# prefetch, icons). An <a href> is navigation the reader chooses — the
# footer's links to dhk.io and the source repo are not requests this page
# makes, and flagging them would train everyone to ignore this check.
#
# Limits, stated rather than implied: it reads one line at a time, so a
# <link> split across lines would slip through, and it cannot see a URL
# assembled at runtime in JS. It is a backstop against the easy mistake,
# not a proof.
#
# Usage: bash scripts/check_no_network.sh [dir]   (default: web)
set -euo pipefail
root="${1:-web}"
fail=0

report() {   # file, message, hits
  echo "::error file=$1::$2"
  echo "$3" | sed 's/^/    /'
  fail=1
}

# data: URIs are local by definition — an inline SVG favicon is not a
# request. Protocol-relative //host is included: it is easy to miss by
# grepping for https alone.
remote='(https?:)?//'

while IFS= read -r -d '' f; do
  hits=$(grep -nE "src[[:space:]]*=[[:space:]]*[\"']${remote}" "$f" || true)
  [ -n "$hits" ] && report "$f" "fetches a remote resource; this page must work offline" "$hits"
  hits=$(grep -nE "<link[^>]*href[[:space:]]*=[[:space:]]*[\"']${remote}" "$f" || true)
  [ -n "$hits" ] && report "$f" "links a remote stylesheet, icon, or preconnect" "$hits"
done < <(find "$root" -name '*.html' -print0)

# A stylesheet can reach out too — @import and url() are the two ways.
while IFS= read -r -d '' f; do
  hits=$(grep -nE "@import[^;]*${remote}|url\([[:space:]]*[\"']?${remote}" "$f" || true)
  [ -n "$hits" ] && report "$f" "stylesheet fetches a remote resource" "$hits"
done < <(find "$root" -name '*.css' -print0)

if [ "$fail" -ne 0 ]; then
  echo "::error::a page promising the draft never leaves the browser reaches the network"
  exit 1
fi
echo "no page under $root/ reaches the network"

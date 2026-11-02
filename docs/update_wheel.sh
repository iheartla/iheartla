#!/bin/sh
# Rebuild the wheel the page's Python compiler installs in Pyodide
# (js/compile-worker.js), docs/iheartla-0.0.1-py3-none-any.whl, after changing
# the Python compiler. `uv build` builds the wheel from an sdist, so a stale
# build/ or untracked files don't leak in; the wheel drops
# iheartla/rust/iheartla.wasm, which the page loads from docs/rust/.
# Usage: sh docs/update_wheel.sh
set -e
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
uv build --quiet -o "$tmp" .
zip -q -d "$tmp"/iheartla-*.whl iheartla/rust/iheartla.wasm
cp "$tmp"/iheartla-*.whl docs/
ls -l docs/iheartla-*.whl

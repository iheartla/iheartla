#!/bin/sh
# Rebuild the wheel the page's Python compiler installs in Pyodide
# (js/compile-worker.js), docs/iheartla-0.0.1-py3-none-any.whl, after changing
# the Python compiler. It is built from the files git tracks, so a stale build/
# or untracked files don't leak in, and without iheartla/rust/iheartla.wasm:
# the page loads the Rust compiler from docs/rust/ (update_rust_wasm.sh).
# Usage: sh docs/update_wheel.sh
set -e
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
git ls-files -z | tar --null -T - -cf - | tar -xf - -C "$tmp"
uv build --quiet --wheel --no-create-gitignore -o "$tmp/dist" "$tmp"
zip -q -d "$tmp"/dist/iheartla-*.whl iheartla/rust/iheartla.wasm
cp "$tmp"/dist/iheartla-*.whl docs/
ls -l docs/iheartla-*.whl

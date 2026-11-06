#!/bin/sh
# Rebuild the wheel the page's Python compiler installs in Pyodide
# (js/compile-worker.js), docs/iheartla-0.0.1-py3-none-any.whl, after changing
# the Python compiler. `uv build` builds the wheel from an sdist, so a stale
# build/ or untracked files don't leak in. Also rebuild docs/iheartla-cpp.zip,
# the page's download of the C++ support code (iheartla/mesh/Cpp), with fixed
# timestamps, so that it changes only when the files do.
# Usage: sh docs/update_wheel.sh
set -e
cd "$(dirname "$0")/.."
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
uv build --quiet -o "$tmp" .
cp "$tmp"/iheartla-*.whl docs/
git ls-files iheartla/mesh/Cpp/include iheartla/mesh/Cpp/src | python3 -c '
import sys, zipfile
with zipfile.ZipFile("docs/iheartla-cpp.zip", "w") as z:
    for path in sys.stdin.read().split():
        info = zipfile.ZipInfo("iheartla-cpp/" + path[len("iheartla/mesh/Cpp/"):], (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        z.writestr(info, open(path, "rb").read())
    info = zipfile.ZipInfo("iheartla-cpp/README.txt", (1980, 1, 1, 0, 0, 0))
    info.external_attr = 0o644 << 16
    z.writestr(info, """C++ support code for the code that I❤️LA generates (https://github.com/iheartla/iheartla)

Code with meshes or derivatives includes headers from include/: put it on the
include path (-Iiheartla-cpp/include). With meshes, also compile and link the
sources in src/. Derivatives need autodiff (https://github.com/autodiff/autodiff),
which needs Eigen 3.4.
""".encode())
'
ls -l docs/iheartla-*.whl docs/iheartla-cpp.zip

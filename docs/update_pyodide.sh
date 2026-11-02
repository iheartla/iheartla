# Vendor the Pyodide runtime and the Python packages the in-browser compiler
# needs into docs/js/pyodide/, so the page doesn't depend on a CDN or PyPI.
# Usage: sh docs/update_pyodide.sh   (then rebuild the wheel: uv build --wheel --no-create-gitignore -o docs,
# and drop the Rust compiler the page loads separately:
# zip -d docs/iheartla-0.0.1-py3-none-any.whl iheartla/rust/iheartla.wasm)
set -e
PYODIDE=314.0.7
# pure-Python wheels from PyPI; keep TATSU within the range in pyproject.toml
TATSU=5.14.0
APPDIRS=1.4.4
cd "$(dirname "$0")/js"
rm -rf pyodide && mkdir pyodide
# Runtime only (~14 MB); the full distribution with every package is ~320 MB compressed.
curl -fsSL "https://github.com/pyodide/pyodide/releases/download/$PYODIDE/pyodide-core-$PYODIDE.tar.bz2" |
    tar -xj -C pyodide --strip-components=1 pyodide/pyodide.js pyodide/pyodide.mjs pyodide/pyodide.asm.mjs \
        pyodide/pyodide.asm.wasm pyodide/python_stdlib.zip pyodide/pyodide-lock.json
# Pyodide-built packages loaded by editor.js, plus their dependencies
for f in $(python3 - <<'PY'
import json
pkgs = json.load(open("pyodide/pyodide-lock.json"))["packages"]
need, todo = set(), ["micropip", "regex", "sympy"]
while todo:
    n = todo.pop()
    if n not in need:
        need.add(n)
        todo += pkgs[n].get("depends", [])
print("\n".join(sorted(pkgs[n]["file_name"] for n in need)))
PY
); do
    curl -fsSL -o "pyodide/$f" "https://cdn.jsdelivr.net/pyodide/v$PYODIDE/full/$f"
done
curl -fsSL -o pyodide/tatsu-$TATSU-py3-none-any.whl "https://files.pythonhosted.org/packages/py3/t/tatsu/tatsu-$TATSU-py3-none-any.whl"
curl -fsSL -o pyodide/appdirs-$APPDIRS-py2.py3-none-any.whl "https://files.pythonhosted.org/packages/py2.py3/a/appdirs/appdirs-$APPDIRS-py2.py3-none-any.whl"
du -sh pyodide

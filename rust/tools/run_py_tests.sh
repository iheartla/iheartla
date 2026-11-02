#!/bin/sh
# Run each Python test module in its own process; summarize OK/FAILED per module.
# usage: rust/tools/run_py_tests.sh <log-dir> [module...]
cd "$(dirname "$0")/../.."
: "${SDKROOT:=$(xcrun --show-sdk-path 2>/dev/null || echo /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk)}"
export SDKROOT
out=$1; shift
mkdir -p "$out"
mods="$*"
[ -z "$mods" ] && mods=$(ls test/test_*.py | xargs -n1 basename | sed 's/\.py$//')
for m in $mods; do
    .venv/bin/python -m unittest "test.$m" > "$out/$m.log" 2>&1
    echo "$m $(grep -E '^(Ran|OK|FAILED)' "$out/$m.log" | tr '\n' ' ')"
done
rm -f test/*.cpp

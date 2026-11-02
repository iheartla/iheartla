#!/bin/sh
# Record the I❤LA programs used by every test module (one process per module).
cd "$(dirname "$0")/../.."
: "${SDKROOT:=$(xcrun --show-sdk-path 2>/dev/null || echo /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk)}"
export SDKROOT
out=rust/corpus/tests.jsonl
mkdir -p rust/corpus
rm -f "$out"
for f in test/test_*.py; do
    m=$(basename "$f" .py)
    .venv/bin/python rust/tools/record_inputs.py "$out" "test.$m" > /dev/null 2>&1
done
rm -f test/*.cpp
wc -l "$out"

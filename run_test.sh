# Run each test module in its own process: a failed cppyy.cppdef can leave
# Cling in a broken state, cascading failures (or a crash) into later tests.
status=0
for f in test/test_*.py; do
    python3 -m unittest "test.$(basename "$f" .py)" || status=1
done
rm -f test/*.cpp
# rm test/*.m
exit $status

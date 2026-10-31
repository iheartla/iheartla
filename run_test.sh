# Run each test module in its own process: Cling (cppyy) can crash when
# every module's generated C++ is loaded into a single interpreter.
status=0
for f in test/test_*.py; do
    python3 -m unittest "test.$(basename "$f" .py)" || status=1
done
rm -f test/*.cpp
# rm test/*.m
exit $status

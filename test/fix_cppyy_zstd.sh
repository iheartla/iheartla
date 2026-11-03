# The cppyy-cling macOS arm64 wheel links libCling.so against MacPorts'
# /opt/local/lib/libzstd.1.dylib, so `import cppyy` fails without MacPorts.
# Point it at Homebrew's zstd (brew install zstd) instead. Run it after each
# (re)install of cppyy; it does nothing when the library doesn't need it.
# Usage: sh test/fix_cppyy_zstd.sh   (PYTHON=.venv/bin/python for another Python)
set -e
LIB=$("${PYTHON:-python3}" -c "import cppyy_backend, os; print(os.path.join(os.path.dirname(cppyy_backend.__file__), 'lib', 'libCling.so'))")
if [ "$(uname)" = Darwin ] && otool -L "$LIB" | grep -q /opt/local/lib/libzstd.1.dylib; then
    install_name_tool -change /opt/local/lib/libzstd.1.dylib "$(brew --prefix zstd)/lib/libzstd.1.dylib" "$LIB"
    codesign -f -s - "$LIB"
    echo "libCling.so now uses $(brew --prefix zstd)/lib/libzstd.1.dylib"
fi

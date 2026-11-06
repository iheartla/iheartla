# I❤️LA: Compilable Markdown for Math

I❤️LA is a compilable markdown for math. It can generate working code in your favorite language (C++, Python, MATLAB, more to come) and LaTeX from snippets like this:

```
∑_i a_i b_i
where
a ∈ ℝ^n
b ∈ ℝ^n
```

or this:

```
A_ij = { 1 if (i,j) ∈ E
         0 otherwise
where
A ∈ ℝ^(n × n)
E ∈ { ℤ × ℤ }
n ∈ ℤ
```

or this:

```
[ t^3 t^2 t 1 ] [ -1  3 -3  1
                   3 -6  3  0
                  -3  3  0  0
                   1  0  0  0 ] P
where
t ∈ ℝ
P ∈ ℝ^(4 × d)
```

In other words, I❤️LA is a linear algebra domain specific language (DSL) that targets other languages. Write once, use everywhere.

For more, see the [wiki](https://github.com/pressureless/linear_algebra/wiki) or the [website](https://iheartla.github.io/). Join the [Discord](https://discord.gg/JvfYb6BXqJ).

## Running

The easiest way to run is in the web browser. You can use the [hosted version](https://iheartla.github.io/iheartla/) (no installation needed) or `cd docs` and then `python3 -m http.server`.

The following instructions describe running the Python code directly.

To run the desktop GUI:

    python3 -m iheartla

You can also run as a command-line compiler:

    python3 -m iheartla --help

Or, without cloning, with [uv](https://docs.astral.sh/uv/):

    uvx --from 'git+https://github.com/iheartla/iheartla/' iheartla foo.ihla -o numpy,latex

On the `rust` branch, `iheartla-rust` runs the Rust compiler (built as WebAssembly, so no Rust toolchain is needed) with the same command line, plus `--name` and `--main`:

    uvx --from 'git+https://github.com/iheartla/iheartla/@rust' iheartla-rust foo.ihla -o numpy,latex

## Installing

You can find releases on the GitHub [release page](https://github.com/iheartla/iheartla/releases). The following instructions are for running from source.

I❤️LA depends on Python 3.10 or later and several modules, listed in `pyproject.toml`. The grammar needs the third-party `regex` module, which `import iheartla` substitutes for `re` so that TatSu uses it. TatSu is pinned to 5.15.1, the version that generates I❤️LA's parsers (see "Changing the grammar").

### uv

Install [uv](https://docs.astral.sh/uv/) and run:

    uv run python -m iheartla --help
    
    ## with the GUI
    uv run --extra gui python -m iheartla
    
    ## For development, also install the test suite's dependencies
    ## (see "Running the tests" below for the C++ setup the tests need):
    uv sync --extra test --extra viz

### Pip

    python3 -m venv .venv
    # activate your virtual environment via something like: source .venv/bin/activate
    
    pip3 install -e .
    ## or, with the GUI
    pip3 install -e '.[gui]'
    
    ## For development, also install:
    pip3 install -e '.[gui,viz,test]' pyinstaller

(2023-05-10: There is a known bug with Python >= 3.10 and wxPython 4.2.0's PDF viewer. It will be fixed in the next release of wxPython. For now, either run on Python 3.9, live without PDF rendering, compile top-of-tree wxPython yourself, or change `/` to `//` in `wx/lib/pdfviewer/viewer.py:354` (so that `self.Ypagepixels` is an `int`). The relevant commit is [here](https://github.com/wxWidgets/Phoenix/commit/aa4394773a8696444ce5d8a90273d67796e499d0).)

If you are developing I❤️LA, the test suite needs a working C++ compiler and, optionally, the Graphviz graph visualization software (e.g., `brew install graphviz`).

### Running the tests

The tests compile generated C++ with cppyy, against Eigen, autodiff and LBFGSpp, which `test/fetch_deps.sh` fetches into `test/third_party/`. On macOS, cppyy-cling's wheel looks for MacPorts' zstd; `test/fix_cppyy_zstd.sh` points it at Homebrew's (run it again after reinstalling cppyy):

    brew install zstd
    sh test/fetch_deps.sh
    PYTHON=.venv/bin/python sh test/fix_cppyy_zstd.sh
    . .venv/bin/activate && sh run_test.sh

Without MATLAB, the MATLAB checks can run in GNU Octave (`brew install octave`), through a stand-in for the MATLAB engine (`test/octave_engine.py`):

    uv sync --extra test --extra octave
    IHEARTLA_OCTAVE=1 sh run_test.sh

Set `IHEARTLA_OCTAVE_VERBOSE=1` too to print how many MATLAB functions ran. A few checks fail in Octave only: integrals, optimization, and ragged arrays.

`.github/workflows/test.yml` does the same.

**cppyy on macOS 26 and later.** cppyy-cling 6.32.8 (the latest, from 2024) can't parse the C++ headers of the macOS 26 SDK and later. `import cppyy` then fails with errors such as `use of undeclared identifier '__builtin_clzg'` or `'__GCC_DESTRUCTIVE_SIZE'`. CI avoids this by running on `macos-15`. Locally, download the macOS 15 SDK (only its headers are used) and point `SDKROOT` at it with an absolute path. The [joseluisq/macosx-sdks](https://github.com/joseluisq/macosx-sdks) releases have it:

    mkdir -p ~/SDKs && cd ~/SDKs
    curl -LO https://github.com/joseluisq/macosx-sdks/releases/download/15.5/MacOSX15.5.sdk.tar.xz
    shasum -a 256 MacOSX15.5.sdk.tar.xz   # c15cf0f3f17d714d1aa5a642da8e118db53d79429eb015771ba816aa7c6c1cbd
    tar -xJf MacOSX15.5.sdk.tar.xz
    export SDKROOT=~/SDKs/MacOSX15.5.sdk   # must be absolute; cling passes it to -isysroot
    python -c "import cppyy; cppyy.cppdef('int f() { return 3; }'); print(cppyy.gbl.f())"   # 3

Set `SDKROOT` the same way before `sh run_test.sh`. The SDK installed with Xcode or the Command Line Tools stays the default for everything else.

The `viz` extra installs the `graphviz` Python package. When it is present, compiling renders a graph with Graphviz's `dot`, so either install Graphviz or leave out `--extra viz` (`uv sync --extra test`), or every test fails with `ExecutableNotFound: failed to execute PosixPath('dot')`.

### Changing the grammar

The grammar is EBNF in `iheartla/la_grammar/`, and the parsers in `iheartla/la_local_parsers/` are TatSu's output for it, unedited. After changing the EBNF, regenerate them with the pinned TatSu, 5.15.1 (other versions generate different code):

    python -m iheartla --regenerate-grammar
    python -m iheartla.la_grammar.update_parsers --check   # (the test suite runs this too)

The script also fixes up TatSu's object model in two ways: every node class gets all the fields its rules define, and the classes are sorted so regenerating is stable (see `complete_model` in `iheartla/la_grammar/update_parsers.py`).

What a program declares changes what parses: declared multi-letter names, function names, imported builtins and their renames, and the constant `e`. The rules that depend on them are overridden in `iheartla/la_tools/configured_parser.py`, which configures the parser before each parse. On the `rust` branch, run `python rust/tools/gen_parser.py` afterwards to translate the parsers to Rust.

## Output Dependencies

To use the code output for the various backends, you will need:

* LaTeX: A working tex distribution with `xelatex` and `pdfcrop`
* Python: NumPy and SciPy
* MATLAB: MATLAB or Octave
* C++: Eigen. Compilation differs on different platforms. On macOS with Homebrew eigen: `c++ -I/usr/local/eigen3 output.cpp -o output`
* MATLAB: MATLAB or (untested) Octave

## Unicode Fonts

`DejaVu Sans Mono` is a font with good Unicode support. Windows users should install it. You can download it [here](https://dejavu-fonts.github.io/Download.html). The I❤️LA GUI will use it if installed.

## Building the web page and the package

The web page is the static site in `docs/`, served as is (by GitHub Pages, or `cd docs; python3 -m http.server`). Two of its files are built from the compilers and committed, so rebuild and commit them after changing a compiler:

* **The Python compiler**, which the page runs in Pyodide, is the wheel `docs/iheartla-0.0.1-py3-none-any.whl`. After changing `iheartla/`, run:

      sh docs/update_wheel.sh

  It runs `uv build`, which builds the wheel from an sdist (`uv build --wheel` would build in the source tree, where a stale `build/` can leak into it), and drops the Rust compiler from the wheel; the page loads it from `docs/rust/`.

* **The Rust compiler**, built as WebAssembly, is `docs/rust/iheartla.wasm` for the page and `iheartla/rust/iheartla.wasm` for the `iheartla-rust` command, which is how `uvx` installs from git get it. After changing `rust/` or the bundled modules in `iheartla/mesh/*.hlang`, run (once: `rustup target add wasm32-unknown-unknown`):

      sh docs/update_rust_wasm.sh

  It writes both copies, which git stores once.

The page's third-party files are vendored by `docs/update_vendor.sh` and `docs/update_pyodide.sh`.

## Packaging a desktop release

**macOS**: `pyinstaller iheartla.spec`. The output `iheartla.app` is placed into `dist/`. The parsers ship in `iheartla/la_local_parsers/`, so packaging doesn't regenerate them.

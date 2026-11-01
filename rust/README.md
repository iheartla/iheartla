# I❤️LA compiler in Rust

A Rust rewrite of the I❤️LA compiler. It keeps the Python compiler's parser
exactly. Everything after the parser is a redesign, not a line-by-line port.
The generated code has the same interface as the Python compiler's (`heartlib(params...)`
with one attribute per definition and one method per local function). The output is
validated by running the Python test suite on it, not by byte comparison.

```
cargo build --release                       # → target/release/iheartla
target/release/iheartla compile --backend numpy < program.la   # or eigen, matlab, latex, mathjax, macromathjax
target/release/iheartla compile --backend numpy --main < program.la   # also generateRandomData() and main()
target/release/iheartla parse [--init|--full] < program.la     # parse tree as JSON
```

## Status

| Part | State |
|---|---|
| Parser (both grammars) | Matches TatSu's parse trees and error positions on the whole corpus (557 parses) |
| Declarations pass (second-parse configuration) | 269/269 corpus programs |
| Type checker → typed AST | Covers every program in the Python test suite |
| NumPy backend | All 224 Python tests on `mesh` (as of the 2026-11-01 merge) |
| Eigen (C++) backend | All 224 Python tests, via cppyy and, for optimization, the system C++ compiler |
| LaTeX and MathJax backends | 261/261 corpus programs (including modules) give output identical to Python's |
| MacroMathJax backend (H❤️rtDown click handlers) | 253/253 corpus programs match Python's output: 251 byte-identical, and 2 equal once equation symbol lists are sorted |
| MATLAB backend | The test suite's MATLAB checks run in GNU Octave. With NumPy, Eigen and MATLAB all from Rust, 222 of 224 tests pass; the 2 failures are test issues (below) |
| I❤️MESH modules (`.hlang` imports, `MeshConnectivity`) | Supported in the NumPy, LaTeX and MathJax backends; all 8 bundled modules compile. `tools/mesh_check.py` (below) finds no differences for the three mesh examples and `FundamentalMeshAccessors`. `Neighborhoods` differs only on degenerate calls such as `EdgeIndex(i, i)`, which take "the first element" of a set with several elements: Rust takes the smallest, Python takes whatever its hash order gives. In Eigen, modules are nested structs. `tools/mesh_check_cpp.py` compiles the C++ output with the I❤️MESH C++ runtime and finds all 611 values equal to the NumPy output |
| Continuous optimization in C++ (`argmin` over ℝⁿ) | LBFGSpp v0.4.0. Bounds by expressions without the variables, and equalities, become box constraints; other constraints throw, naming the constraint. When the line search fails (near a non-smooth or exactly-zero minimum), the best point evaluated is used. `tools/opt_check_cpp.py` finds all 11 corpus optimization programs agree with NumPy, on random inputs and on the test suite's own |

To run the Python test suite with code from the Rust compiler:

```
IHEARTLA_RUST_BACKENDS=numpy,eigen python rust/tools/run_tests_rust.py          # all modules
RUST_TEST_VERBOSE=1 python rust/tools/run_tests_rust.py test.test_python_norm   # one module, verbose
```

The Python compiler still runs, but its output is replaced by the Rust compiler's for
the backends listed in `IHEARTLA_RUST_BACKENDS` (`numpy`, `eigen`, `matlab`).

With `matlab` in that list, the test suite's MATLAB checks run in GNU Octave:
- the runner needs `octave-cli`, which ships with Homebrew's `octave`, and `pip install oct2py`;
- a stand-in replaces the `matlab` engine module;
- `IHEARTLA_OCTAVE=1` runs the same checks on the Python compiler's MATLAB output.

The 2 failing tests are test issues:
- `test_set_init` compares an array to a list with `assertEqual`, which raises an error for
  any array.
- `test_nested_integral` expects a quadrature result to equal 9 exactly; Octave's
  `integral` gives 9 + 1.8e-15. Each test module runs in its own
process, because a C++ compile error can crash cling and end the whole run.

## `--main`: random data and a main

`--main` adds `generateRandomData()` and `main()` to the NumPy, Eigen and MATLAB output. This
is what the Python compiler emits with `class_only=False`, and what the web page shows.

The random arguments are drawn so that they fit together:
- integer parameters that size other parameters are drawn first;
- dimensions that one subscript ranges over are equal (the checker records these in
  `Program::dim_checks`);
- all sequences share one length, 4–9, or the mesh's vertex count when there is a mesh;
- random functions return values sized as their arguments imply;
- integers and `index` values stay below the smallest size.

A mesh parameter is an octahedron (NumPy and Eigen).

`tools/main_check.py` runs every corpus program's `main`: NumPy 224/224, Eigen 223/224,
MATLAB 219/224. The failures fall into two groups:
- programs that can't run on arbitrary random values (`f(2)` where 2 must be in a random
  set; subscripts like `a_(b+1)` or `a_(b-c)` with random `b` and `c`), so whether they
  fail depends on the draw;
- the 3 mesh programs in MATLAB, which doesn't support meshes.

## On the web

The web page in `docs/` has a **Compiler** choice: Python, which runs in Pyodide, or Rust. The
choice is kept in the URL as `?compiler=rust`, so "Copy as URL" keeps it.

How the Rust option works:
- **Build:** the Rust compiler is built for `wasm32-unknown-unknown` with a size-optimised
  profile. `docs/update_rust_wasm.sh` writes `docs/rust/iheartla.wasm` (2.7 MB, no imports).
- **Worker:** it runs in `docs/js/compile-worker-rust.js`, with the same messages as the
  Pyodide worker. Its interface is in `src/wasm.rs`.
- **Check:** `tools/web_check.py` tests the page in headless Chromium:
  `uv run --with playwright python rust/tools/web_check.py`.

With Rust, the page is ready in 0.08 s and compiles an I❤️MESH program importing two
modules in 0.1 s. With Pyodide, notes/Performance.md reports 5–9 s for NumPy alone and 40 s or
more for all outputs.

## Speed

Apple Silicon, release build, Python 3.12 and TatSu 5.14 (`python rust/tools/bench.py`).
Rust times include process start-up, which is about 4 ms (2 ms to exec and 2 ms to build
the grammar's regexes).

| | Python | Rust | Speed-up |
|---|---|---|---|
| `T₁` (test_gallery_10), NumPy | 0.24 s | 0.009 s | 28× |
| `T₁`, NumPy + Eigen (two Rust processes) | 0.24 s | 0.017 s | 14× |
| All 207 test programs, NumPy + Eigen | 23.1 s | 3.1 s | 7× |
| Parse `Neighborhoods.hlang` (first pass only) | 1.64 s | 0.016 s | 103× |
| I❤️MESH `one_ring` (imports Neighborhoods, which imports FundamentalMeshAccessors), NumPy | 4.91 s | 0.039 s | 126× |
| Same, NumPy + LaTeX + MathJax (three Rust processes) | 14.85 s | 0.114 s | 130× |

The parser speed-up is the one that matters for I❤️MESH. TatSu parses take almost all of
an I❤️MESH compile (see `notes/Performance.md`), and each imported module is
parsed twice per output type. In Rust, each module is parsed and checked once per
compilation (`modules.rs`), and the typed AST is shared by all backends.
(`python rust/tools/bench_mesh.py` gives the I❤️MESH rows.)

## Design

```
source ─ grammar::parse_init ─▶ parse tree ─ decls ─▶ ParserConfig
       ─ grammar::parse_default(config) ─▶ parse tree ─ check ─▶ ast::Program ─ back::{numpy,eigen}
```

- **Parser** (`peg.rs`, `pnode.rs`, `grammar/`): a PEG engine with TatSu's semantics.
  It builds the same parse trees, handles left recursion by seed growing, uses the same
  memoization, and produces the same `Expecting <rule>` errors. `grammar/*.rs` is
  generated from the TatSu grammars by `tools/gen_parser.py`. The two-pass scheme is
  kept, because the second grammar depends on declared names (how `AB` differs from `A B`).
- **Declarations** (`decls.rs`): compute the second parse's configuration (identifiers,
  functions, builtins, renames) from the first parse tree.
- **Modules** (`modules.rs`): `.hlang` modules are found first among the bundled modules,
  which are embedded in the binary, then in the importer's directory. The order is the
  same as Python's. Each module is compiled once per compilation. The importer binds its
  arguments to the module's parameters, substitutes them into the imported types (mesh
  sizes are dimension markers like `@mesh:M:v`), and adds the module's functions to its own
  second-parse configuration.
- **Checker** (`check.rs`, `ty.rs`, `dims.rs`): one pass over the parse tree. It produces
  a typed AST (`ast.rs`) where every expression carries an immutable `Ty`. Dimensions are
  symbolic (`dims::Sym`, a small SymPy subset). Statements are ordered by def–use
  dependencies, not by the Python compiler's multi-walker passes. Subscript extents,
  overloads (`f_0`, `f_1`), index sets (0-based `index` values used 1-based) and ragged
  sequences (`x_i ∈ ℝ^(n_i)`) are all resolved here, so backends never re-infer types.
- **Backends** (`back/`): the code backends are straightforward printers of the typed AST.
  The LaTeX and MathJax backends (`back/latex.rs`) print the parse tree instead, so the
  output shows the program as written. The checker supplies the types that the notation
  depends on, recording every expression's type by source span (`Program::expr_types`).
  That same span-to-type map can support correspondence links between prose, math and code.
  - NumPy follows the Python compiler's conventions: `np.asarray` parameters, shape
    asserts, `scipy.sparse` for sparse matrices.
  - Eigen emits a `struct heartlib` with fixed-size types where sizes are numeric.
    Integer vectors and matrices keep `int` elements (tests rely on this) and get
    `.cast<double>()` where they meet reals. Sums, piecewise expressions and block
    matrices become immediately invoked lambdas, so every expression stays an expression.

## Tools (`tools/`)

- `golden.py`, `record_all.sh`, `make_cases.py`, `record_inputs.py`: build the corpus
  (`corpus/`) of test-suite programs and their Python-compiler outputs.
- `cmp_backend.py BACKEND 'source text'`: show the Python output for a corpus program
  next to the Rust output.
- `run_tests_rust.py`: run the Python test suite on Rust output (see above).
- `cmp_all.py BACKEND [-v N]`: compare one backend's output with the goldens over the whole
  corpus (identical / equal up to whitespace / different / error).
- `bench.py`, `bench_mesh.py`: the timing tables above.
- `opt_check_cpp.py`: run the NumPy and Eigen outputs of the corpus's optimization programs
  and compare results. It needs LBFGSpp, which `test/fetch_deps.sh` fetches, and Eigen 3.4.
- `mesh_check_cpp.py`: compile the Rust Eigen output with the I❤️MESH C++ runtime
  (`iheartla/mesh/Cpp`, built with clang++), run it on the same octahedron, and compare
  every value with the Rust NumPy output.
- `mesh_check.py`: compile I❤️MESH programs with both compilers, run both on an octahedron,
  and compare every attribute and every function value over all element arguments.
  `mesh_runtime/triangle_mesh.py` adds `ElementSets` and `indicator` to the I❤️MESH
  Python runtime. Generated code (from either compiler) calls them, but
  `iheartla/mesh/Python/triangle_mesh.py` doesn't define them.
- `gen_parser.py`: regenerate `src/grammar/` from the TatSu grammars.

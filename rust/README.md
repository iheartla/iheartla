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
| Parser (both grammars) | Matches TatSu's parse trees and error positions on the whole corpus (697 parses) |
| Declarations pass (second-parse configuration) | 315/315 corpus programs |
| Type checker → typed AST | Covers every program in the Python test suite, all 23 H❤️rtDown gallery programs and all 10 I❤️MESH paper examples |
| NumPy backend | All 235 Python tests on `mesh` (as of the 2026-11-02 merge). On the 23 gallery programs, `tools/value_check.py` finds every attribute and local function value equal to the Python compiler's. Derivatives (`∂f/∂x`, and `∂²f/∂x²` of a scalar `f` with respect to a scalar, vector or sequence; other second derivatives are errors, as in Python) use autograd |
| Eigen (C++) backend | All 235 Python tests, via cppyy and, for optimization, the system C++ compiler. In a program with derivatives, the struct is a template over its real type (`heartlib` is `heartlib_t<double>`); a derivative recomputes the program as `heartlib_t<autodiff::var>` ([autodiff](https://github.com/autodiff/autodiff), reverse mode), differentiated twice for a second derivative with respect to a scalar |
| LaTeX and MathJax backends | 305/305 corpus programs (including modules, the gallery and the I❤️MESH examples) give output identical to Python's |
| MacroMathJax backend (H❤️rtDown click handlers) | All 305 corpus programs match Python's output: 303 byte-identical, and 2 equal once equation symbol lists are sorted |
| MATLAB backend | The test suite's MATLAB checks run in GNU Octave: with NumPy, Eigen and MATLAB all from Rust, all 235 tests pass. Names are converted as Python converts them (`μ` is `mu`, `λ` is `lambda_`). Meshes, modules, derivatives, `svd` and sets of vectors aren't supported |
| I❤️MESH modules (`.hlang` imports, `MeshConnectivity`) | Supported in the NumPy, LaTeX and MathJax backends; all 8 bundled modules compile. `tools/mesh_check.py` (below) finds no differences for the three mesh examples, `FundamentalMeshAccessors` and `Neighborhoods`. In Eigen, modules are nested structs. `tools/mesh_check_cpp.py` compiles the C++ output with the I❤️MESH C++ runtime and finds all 615 values equal to the NumPy output |
| I❤️MESH paper examples (`corpus/iheartmesh/`) | All 10 compile. On an octahedron, `mesh_check.py` finds `vertex_normal`, `bilateral_denoising`, `discrete_curvature` and `winding_number` equal to Python's NumPy (35,525 values), and `mesh_check_cpp.py` finds Rust's C++ equal to Rust's NumPy for those and `polygon_mesh` (1,066 values). `tools/paper_check.py` checks the four that use derivatives, `sequence()`, sets of vectors and `svd` against the paper's own C++: all 549 values agree, in C++ and NumPy. `mass_spring` needs a tetrahedral mesh, which the checks don't build |
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

Each test module runs in its own
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
- integers and `index` values stay below the smallest size;
- a dimension is at least the largest constant subscript into it (`n ≥ 10` for `x₁₀`
  of `x ∈ ℝ^n`; `Program::min_dims`).

A mesh parameter is an octahedron (NumPy and Eigen).

`tools/main_check.py` runs every corpus program's `main`: NumPy 286/290, Eigen 284/289,
MATLAB 252/273. The failures fall into these groups:
- programs that can't run on arbitrary random values (`f(2)` where 2 must be in a random
  set; subscripts like `a_(b+1)` or `a_(b-c)` with random `b` and `c`; a random set's
  integers used as subscripts, `v_j` for `j ∈ S`), so whether they fail depends on the draw;
- `mass_spring`, `mesh_deformation` (tetrahedral meshes) and `point_cloud` (an edge mesh):
  the random mesh is always a triangle mesh, an octahedron;
- optimization constraints that Eigen and MATLAB don't support (`t_others_11`, `t_others_12`);
- in MATLAB, the programs with meshes, modules, derivatives, `sequence()` or `svd`.

## On the web

The web page in `docs/` has a **Compiler** choice: Python, which runs in Pyodide, or Rust. The
choice is kept in the URL as `?compiler=rust`, so "Copy as URL" keeps it.

How the Rust option works:
- **Build:** the Rust compiler is built for `wasm32-unknown-unknown` with a size-optimised
  profile. `docs/update_rust_wasm.sh` writes `docs/rust/iheartla.wasm` (2.7 MB). It imports
  one function, which asks the host for a module that isn't builtin.
- **Worker:** it runs in `docs/js/compile-worker-rust.js`, with the same messages as the
  Pyodide worker. Its interface is in `src/wasm.rs`. (The page has no files, so it only
  finds the builtin modules.)
- **Command line:** `iheartla-rust` (`iheartla/rust_wasm.py`) runs the same module with
  wasmtime, finding other modules next to the input file as the Python compiler does. The
  Python package carries a copy, `iheartla/rust/iheartla.wasm`, which
  `docs/update_rust_wasm.sh` writes too.
- **Check:** `tools/web_check.py` tests the page in headless Chromium:
  `uv run --with playwright python rust/tools/web_check.py`.

With Rust, the page is ready in 0.08 s and compiles an I❤️MESH program importing two
modules in 0.1 s. With Pyodide, notes/Performance.md reports 5–9 s for NumPy alone and 40 s or
more for all outputs.

## Speed

For the current comparison, see `notes/Performance.md`. It covers native and web numbers
against the Python compiler with its parse-tree cache, and where Rust's time goes
(`IHEARTLA_TIMING=1`). The table below predates that cache, so its multi-output Python
numbers are higher than Python's today.

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
  (`corpus/`) of programs and their Python-compiler outputs. Besides the test suite's
  programs, it has the H❤️rtDown gallery's (`corpus/heartdown/`, from
  `extract_heartdown.py`) and the I❤️MESH paper's examples (`corpus/iheartmesh/`); see
  the README in each. A program in a file is compiled in its directory, where its
  imports are found (`path` in its golden file).
- `paper_check.py SUPPLEMENT_DIR`: build `paper_check/driver.cpp` with the I❤️MESH paper's own
  `heartlib.h` and with the Rust compiler's C++ for the four examples with derivatives,
  `sequence()`, sets of vectors and `svd`, and compare every value, and the Rust NumPy
  output's too. C++ derivatives need autodiff (Homebrew: `autodiff`) and Eigen 3.4.
- `value_check.py [id-prefix ...]`: run both compilers' NumPy output on the same random
  arguments (from `--main`) and compare every attribute and local function value
  (default: the gallery programs).
- `cmp_backend.py BACKEND 'source text'`: show the Python output for a corpus program
  next to the Rust output.
- `run_tests_rust.py`: run the Python test suite on Rust output (see above).
- `cmp_all.py BACKEND [-v N] [-p PREFIX]`: compare one backend's output with the goldens over
  the whole corpus, or the cases whose id starts with PREFIX (identical / equal up to
  whitespace / different / error).
- `bench.py`, `bench_mesh.py`: the timing tables above.
- `opt_check_cpp.py`: run the NumPy and Eigen outputs of the corpus's optimization programs
  and compare results. It needs LBFGSpp, which `test/fetch_deps.sh` fetches, and Eigen 3.4.
- `mesh_check_cpp.py`: compile the Rust Eigen output with the I❤️MESH C++ runtime
  (`iheartla/mesh/Cpp`, built with clang++), run it on the same octahedron, and compare
  every value with the Rust NumPy output.
- `mesh_check.py`: compile I❤️MESH programs with both compilers, run both on an octahedron,
  and compare every attribute and every function value over all element arguments (and a point in ℝ³).
  Calls that only Python rejects (its argument checks) aren't compared.
  `IHEARTLA_PYTHON_ROOT=<checkout>` takes the Python compiler from another checkout.
  `mesh_runtime/triangle_mesh.py` adds `ElementSets` and `indicator` to the I❤️MESH
  Python runtime. Generated code (from either compiler) calls them, but
  `iheartla/mesh/Python/triangle_mesh.py` doesn't define them.
- `gen_parser.py`: regenerate `src/grammar/` from the TatSu grammars.

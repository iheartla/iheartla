# I❤️LA compiler in Rust

A Rust rewrite of the I❤️LA compiler. It keeps the Python compiler's parser
exactly. Everything after the parser is a redesign, not a line-by-line port.
The generated code has the same interface as the Python compiler's (`heartlib(params...)`
with one attribute per definition and one method per local function). The output is
validated by running the Python test suite on it, not by byte comparison.

```
cargo build --release                       # → target/release/iheartla
target/release/iheartla compile --backend numpy < program.la   # or --backend eigen
target/release/iheartla parse [--init|--full] < program.la     # parse tree as JSON
```

## Status

| Part | State |
|---|---|
| Parser (both grammars) | Matches TatSu's parse trees and error positions on the whole corpus |
| Declarations pass (second-parse configuration) | 231 of 237 corpus programs. The other 6 import `.hlang` modules |
| Type checker → typed AST | Covers every program in the Python test suite |
| NumPy backend | 207/207 Python tests |
| Eigen (C++) backend | 207/207 Python tests (via cppyy) |
| LaTeX, MathJax, MATLAB backends | Not yet |
| I❤️MESH modules (`.hlang` imports, `MeshConnectivity`) | Not yet |
| Continuous optimization in C++ (`argmin` over ℝⁿ) | Throws at run time (Python uses LBFGSpp). Optimization over a finite set works |

To run the Python test suite with code from the Rust compiler:

```
IHEARTLA_RUST_BACKENDS=numpy,eigen python rust/tools/run_tests_rust.py          # all modules
RUST_TEST_VERBOSE=1 python rust/tools/run_tests_rust.py test.test_python_norm   # one module, verbose
```

The Python compiler still runs, but its output is replaced by the Rust compiler's for
the backends listed in `IHEARTLA_RUST_BACKENDS`. Each test module runs in its own
process, because a C++ compile error can crash cling and end the whole run.

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

The parser speed-up is the one that matters for I❤️MESH. TatSu parses take almost all of
the 28 s of an I❤️MESH compile (see `PERFORMANCE.md` in the main checkout), and each
imported module is parsed twice per output type. In Rust, those parses would take
milliseconds each, and the typed AST is built once and shared by all backends.

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
- **Checker** (`check.rs`, `ty.rs`, `dims.rs`): one pass over the parse tree. It produces
  a typed AST (`ast.rs`) where every expression carries an immutable `Ty`. Dimensions are
  symbolic (`dims::Sym`, a small SymPy subset). Statements are ordered by def–use
  dependencies, not by the Python compiler's multi-walker passes. Subscript extents,
  overloads (`f_0`, `f_1`), index sets (0-based `index` values used 1-based) and ragged
  sequences (`x_i ∈ ℝ^(n_i)`) are all resolved here, so backends never re-infer types.
- **Backends** (`back/`): straightforward printers of the typed AST.
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
- `bench.py`: the timing table above.
- `gen_parser.py`: regenerate `src/grammar/` from the TatSu grammars.

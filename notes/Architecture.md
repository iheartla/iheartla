# Compiler architecture

I❤️LA has two compilers for the same language:

- the **Python compiler** (`iheartla/`), the original;
- the **Rust compiler** (`rust/`), a rewrite that keeps the Python compiler's parser exactly
  and redesigns everything after it.

Both read an I❤️LA program and produce the same outputs:
- **code:** NumPy, C++/Eigen and MATLAB;
- **documents:** LaTeX, MathJax and MacroMathJax (MathJax with H❤️rtDown click handlers).

The generated code has the same interface in both: a class, struct or function `heartlib`
whose constructor takes the parameters and holds every definition. Optionally a
`generateRandomData()` and a `main()` follow. Both compilers can import I❤️MESH modules
(`.hlang` files).

This note covers what the two share, how each is built, and how the Rust compiler is
kept equivalent to the Python one. Speed is in `notes/Performance.md`; the Rust compiler's
status and tools are in `rust/README.md`.

## Shared parts

**The grammar.** I❤️LA is parsed by two TatSu-generated PEG parsers in
`iheartla/la_local_parsers/`:
- `init_parser.py`, from the simplified grammar, which only collects declarations;
- `default_parser.py`, the full grammar.

They are generated from the EBNF in `iheartla/la_grammar/` (`LA_ebnf.py`,
`simplified_grammar_ebnf.py`, and parts such as `types_ebnf.py` and `operators_ebnf.py`) and
then patched by hand. So the generated parsers, not the EBNF, define the language.

**Two parses per program and per module.** A declared multi-letter name like `AB` must
parse as one name, not as `A B` (a product). So:
1. The first parse, with the simplified grammar, collects the declarations: declared names,
   functions, imported builtins, renames, and whether `e` is a constant.
2. The full grammar is configured with them.
3. The program is parsed again.

Imported modules contribute the names of their functions to the importer's configuration.

**Modules.** `X, Y from Module(params)` imports from either a builtin package or a module:
- **Builtin packages:** `trigonometry`, `linearalgebra`, and `MeshConnectivity` (the mesh
  functions `ElementSets`, `BoundaryMatrices`, `NonZeros`, `IndicatorVector`, …).
- **Modules:** a `.hlang` file, looked up first among the bundled modules in
  `iheartla/mesh/` (`Neighborhoods`, `FundamentalMeshAccessors`, and their polygon,
  point-cloud and tetrahedron variants), then in the importing file's directory.

The importer binds its arguments to the module's parameters. A module's overloaded
functions are named `f`, `f_0`, `f_1`, …

**Runtimes the generated code calls** (I❤️MESH):
- **Python:** `iheartla/mesh/Python/triangle_mesh.py`, with `TriangleMesh`, `ElementSets`,
  `indicator`, and `nonzeros` returning frozensets.
- **C++:** `iheartla/mesh/Cpp`, with `FaceMesh`, `EdgeMesh`, `CellMesh`, and `MeshHelper`'s
  `nonzeros` and `indicator`.
- **MATLAB:** `iheartla/mesh/MATLAB`, with `ElementSets` and `indicator.m`.

C++ continuous optimization uses the header-only LBFGSpp v0.4.0, fetched by
`test/fetch_deps.sh`.

**Conventions.**
- Subscripts are 1-based.
- `index` values (and mesh elements) are 0-based in NumPy and C++, and 1-based in MATLAB.
- Sets are frozensets in Python, sorted vectors without duplicates in C++, and matrices with
  one row per element in MATLAB.

## The Python compiler

```
compile_la_content (la_parser/parser.py)
  └─ parse_ir_node, per output type
       ├─ first parse: init parser
       ├─ get_new_parser: imports, module compiles, ParserManager.modify_default_parser
       ├─ second parse: the reconfigured default parser   (both parses through parse_cached)
       ├─ TypeWalker (type_walker.py): parse tree → IR (ir.py) with types (la_types.py)
       └─ code generator per output (codegen_*.py, IRVisitor subclasses)
```

- **Entry point.** `compile_la_content` (`la_parser/parser.py`) takes the source and a set of
  output types (`ParserTypeEnum`). It is used by the CLI (`python -m iheartla`), the GUI,
  the tests and the web page.
  - A program without imports is type-walked once and generated once per output.
  - A program with imports runs `parse_ir_node` once per output type.
- **Parsers.** `la_tools/parser_manager.py` creates the TatSu parsers. The default parser
  is a single object, reconfigured in place for each program (`modify_default_parser`).
  `parse_cached` keeps an LRU cache of 128 parse trees, keyed by the parser configuration
  and the source text. So within a compile, each module and the program are parsed once,
  and repeat compiles in one process don't re-parse.
- **The `regex` swap.** The grammar uses `\p{…}` Unicode classes, so `iheartla/__init__.py`
  replaces `re` with the `regex` module before TatSu loads. Supported TatSu versions are
  5.8.3 through 5.14.
- **Type checking.** `TypeWalker` (`la_parser/type_walker.py`, about 5,600 lines) walks the
  parse tree and builds the IR (`ir.py`), annotating nodes with mutable type objects from
  `la_types.py`. It is a singleton, reset for each use. It handles:
  - symbols, scopes, dimensions (with SymPy for symbolic sizes), subscripts and sequences;
  - overloads and imported modules;
  - pre-walks, for statement order and overload names.

  Imported symbols' types are adjusted in place for the importer's arguments
  (`replace_sym_dims`). That is why the old type-walker cache (`module_manager.py`,
  `CACHE_MODULE = False`) can't be used.
- **Code generation.** One `IRVisitor` subclass per output: `codegen_numpy.py`,
  `codegen_eigen.py`, `codegen_matlab.py`, `codegen_latex.py`, `codegen_mathjax.py`,
  `codegen_macromathjax.py`, plus `codegen_mathml.py`, which is unused.
  - `get_codegen` creates a fresh generator each time, because reused generators leaked
    state between compiles.
  - Each module's code frame is generated per output type and nested in the importer's
    output.
  - `class_only=False` adds `generateRandomData()` and `main()`. The CLI's default is
    `CLASS_ONLY = True`; the web page passes `False`.
- **Web.** `docs/js/compile-worker.js` runs the compiler in Pyodide (vendored in
  `docs/js/pyodide`) in a module Web Worker. It installs the wheel built with
  `uv build --wheel --no-create-gitignore -o docs`.

## The Rust compiler

```
source ── grammar::parse_init ──▶ parse tree ── decls ──▶ ParserConfig
       ── grammar::parse_default(config) ──▶ parse tree ── check ──▶ ast::Program
       ── back::{numpy, eigen, matlab, latex} (+ back::random for --main)
```

The crate is `rust/` (library and `iheartla` binary). Its parts:

| Part | Files | What it does |
|---|---|---|
| PEG engine | `peg.rs`, `pnode.rs` | TatSu's semantics: ordered choice, its parse-tree construction (CST/AST, `_define`, closures), memoization, left recursion by seed growing, and its `Expecting <rule>` errors. Failure is a return value, not an exception |
| Grammars | `grammar/init.rs`, `grammar/default.rs` (generated), `grammar/special.rs` | `rust/tools/gen_parser.py` translates TatSu's generated parsers, hand patches included, into Rust. The rules that consult the configuration are hand-written in `special.rs`. The parse trees equal TatSu's on the whole corpus (557/557) |
| Declarations | `decls.rs` | The second parse's configuration from the first parse tree (269/269 corpus programs match Python's) |
| Modules | `modules.rs` | Finds `.hlang` modules (the bundled ones are embedded in the binary), compiles each once per compilation, and shares it among importers |
| Checker | `check.rs`, `ty.rs`, `dims.rs`, `ast.rs` | One pass over the second parse tree that produces a typed program |
| Backends | `back/numpy.rs`, `eigen.rs`, `matlab.rs`, `latex.rs`, `random.rs`, `names.rs` | Print the typed program, or for LaTeX the parse tree |
| Entry points | `lib.rs`, `main.rs`, `wasm.rs` | Library functions `front_end`, `generate` and `compile`; the CLI; the WebAssembly interface |

**The checker and the typed program.** `Checker::check` turns the second parse tree into
an `ast::Program`. It contains:
- parameters and their dimension symbols;
- statements in def–use order;
- definitions;
- the overload table;
- mesh parameters and imported modules.

Every expression carries an immutable `Ty`: scalar (real, int, `index`, vertex/edge/face/tet),
vector, matrix (dense or sparse), sequence, set, tuple, function or mesh. Dimensions are
symbolic (`dims::Sym`, a small SymPy-compatible subset). Everything that depends on types is
resolved here, so backends never re-infer types:
- subscript extents;
- overload names;
- `index` values;
- ragged sequences;
- block-matrix sizes;
- mesh sizes (as markers like `@mesh:M:v`).

The checker also records, by source span, every expression's type
(`Program::expr_types`) and every indexed symbol's type. The LaTeX printers use these maps,
and they are a basis for linking math spans to code.

Compared with the Python compiler:
- one pass with immutable types, instead of a mutable IR revised by several walkers;
- statement order from def–use dependencies;
- imported types are substituted (`subst_ty`) instead of mutated, so a module is compiled
  once and shared.

**Backends.**
- **NumPy:** a class whose imported modules are nested classes.
- **C++/Eigen:**
  - fixed-size types where sizes are numbers;
  - integer matrices that keep `int`, with casts where they meet reals;
  - lambdas for sums, piecewise expressions, block matrices and set expressions;
  - nested structs for modules;
  - LBFGSpp for continuous optimization: bounds become box constraints, and the best point
    evaluated is used if the line search fails.
- **MATLAB:** a function returning a struct; local functions are nested functions.
- **LaTeX, MathJax and MacroMathJax:** a printer over the parse tree, so the output shows
  the program as written. It reproduces the Python printers, including their rules for
  which symbols an equation's click handler lists.
- **`--main` (`back/random.rs`):** random arguments that fit together:
  - integer parameters that size other parameters are drawn first;
  - dimensions a subscript ranges over together are made equal;
  - sequences share one length;
  - random functions return values sized as their arguments imply.

**WebAssembly.** The library builds for `wasm32-unknown-unknown`, with the `wasm` Cargo
profile. `wasm.rs` exports `ih_alloc`, `ih_free` and `ih_compile_json`, which takes a JSON
request (source, backends, name, main) and returns JSON with the outputs. It imports one
function, `iheartla.read_module`, through which the loader asks the host for a module that
isn't builtin. `docs/js/compile-worker-rust.js` runs it with the same messages as the
Pyodide worker (and finds no modules); the page's Compiler choice (`?compiler=rust`) picks
the worker. `iheartla-rust` (`iheartla/rust_wasm.py`) runs it with wasmtime and reads
modules from the input file's directory. Rebuild with `docs/update_rust_wasm.sh`.

## Keeping the two equivalent

The Python compiler is the reference. The Rust compiler is checked against it in
`rust/tools/`:

| Check | Tool | Current result |
|---|---|---|
| The Python test suite, run on the Rust compiler's NumPy, Eigen and MATLAB output (MATLAB in GNU Octave) | `run_tests_rust.py` | 222/224. The 2 failures are test issues |
| Parse trees and second-parse configurations against the goldens | `iheartla check-parses`, `iheartla check-config` | 557/557, 269/269 |
| LaTeX, MathJax and MacroMathJax against the goldens | `cmp_all.py` | 261/261, 261/261, 253/253 |
| I❤️MESH programs run on an octahedron, Python- against Rust-compiled NumPy | `mesh_check.py` | All values equal, except where a function takes "the first element" of a set with several (Rust takes the smallest; Python takes its hash order) |
| Rust C++ against Rust NumPy on the same mesh | `mesh_check_cpp.py` | 611/611 values |
| C++ optimization against NumPy | `opt_check_cpp.py` | 13/13 |
| Every corpus program's generated `main` | `main_check.py` | NumPy 224/224, C++ 223/224, MATLAB 219/224 (programs that need particular values; meshes in MATLAB) |
| The web page with both compilers | `web_check.py` | No page errors |

The goldens (`rust/corpus/golden/*.json`) are the Python compiler's parse trees and outputs
for every program the test suite compiles, plus the examples and the bundled modules. When
the Python compiler changes, regenerate them:
1. `sh rust/tools/record_all.sh`, which records the test programs;
2. `python rust/tools/make_cases.py`;
3. `python rust/tools/golden.py`.

Then re-run the checks. When the grammar changes, regenerate the Rust parsers with
`python rust/tools/gen_parser.py`. The bundled `.hlang` modules are compiled into the Rust
binary, so a change to them needs a rebuild, and for the web page a rebuild of
`docs/rust/iheartla.wasm`.

The Rust compiler differs from the Python one in a few deliberate ways:
- **First element of a set:** it takes the smallest element, where Python's depends on hash
  order.
- **MATLAB names** are always valid: ASCII, at most 63 characters.
- **Mesh programs in MATLAB** fail with a clear "not supported" error.
- **Python bugs it doesn't reproduce:** C++ for continuous optimization that returned the
  iteration count or ignored constraints (since fixed on `mesh`), and MATLAB output
  containing Python syntax.

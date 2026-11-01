# Compiler performance

Measurements from 2026-10-31 on an Apple Silicon Mac, Python 3.12, TatSu 5.14.0,
unless noted. "Browser" means the in-browser compiler in `docs/` (Pyodide 314.0.7,
Python 3.14), driven with Playwright in Chromium 156, Firefox 157, and WebKit 27.2.

Two test programs:

- **Plain I❤️LA**: the `T₁` example from `test_gallery_10` (no modules).
- **I❤️MESH**: a 7-line program that imports `ElementSets` from `MeshConnectivity`
  and `VertexOneRing` from `Neighborhoods(M)`; those modules import others.

## Summary

| | Native | Browser |
|---|---|---|
| Plain program, all 6 outputs | 0.2–0.3 s | 0.25–0.45 s, plus a fixed 1 s `setTimeout` in `editor.js` |
| I❤️MESH program, NumPy only | 4.6 s | 5.3–8.8 s |
| I❤️MESH program, all 6 outputs (what the web page requests) | 28 s | 40 s to 15+ min (see below) |

Plain programs are fast. Programs that import modules are slow, and almost all of
that time is spent in the TatSu parser, not in I❤️LA's own type checking or code
generation (about 2 s of 66 s in a profile).

These are the Python compiler's numbers before the changes described below. For the
compiler after those changes (7.1 s, or 0.46 s for a repeat compile, for the I❤️MESH
program with all 6 outputs), see "Changes made". For the Rust compiler (0.04–0.23 s, and
0.10 s on the web page), see "The Rust compiler" at the end.

## Where the time goes

Three causes multiply:

1. **Everything is re-parsed once per output type.** `compile_la_content` with the
   default `parser_type` produces NumPy, Eigen, LaTeX, MathJax, MATLAB, and
   MacroMathJax. For programs that import modules, it runs `parse_ir_node` once per
   output type, and each run re-reads and re-parses every imported module
   (`get_compiled_module`). The I❤️MESH program performs 31 TatSu parses: 28.4 s for
   all outputs versus 4.8 s for NumPy alone. (Programs without modules are already
   parsed once; only code generation runs per output type.)
2. **Every module is parsed twice.** A first parse collects declared names; the parser
   is then rebuilt with those names (`get_new_parser`) and the source parsed again.
   This is how I❤️LA distinguishes a declared multi-letter name like `AB` from `A·B`.
3. **TatSu is slow on this grammar.** Parsing the 64-line `Neighborhoods.hlang`
   takes about 1.7 s: 81,000 rule calls (about 35 per character) at roughly 20 µs
   each. The core expression rules (`expression`, `term`, `factor`, and 12 others) are
   left-recursive, and 42 rules, including all operators, are not memoized. TatSu
   handles left recursion by re-parsing the same span as the match grows, so
   `factor` is tried about 125 times per line. Every failed alternative raises a
   `FailedParse` exception that copies the rule stack (2.9 million exceptions per
   compile). By self time: TatSu 47 s, Python's `contextlib` (TatSu's context
   managers) 9.5 s, I❤️LA about 2 s.

The module cache (`module_manager.py`) was meant to avoid re-parsing modules, but it
never worked with current TatSu: deep-copying a type walker fails on a TatSu
`FailedParse` object, and the cache is keyed by output type anyway. It would also be
unsafe if it worked, because importers modify a module's type walker in place
(`replace_sym_dims`). It is now turned off (`CACHE_MODULE = False`) in favor of the
parse-tree cache described below.

Upgrading TatSu 5.7.3 → 5.14.0 alone cut the I❤️MESH compile from 68 s to 29 s.

## Browsers

Python itself runs at similar speed in all three engines, within about 1.5× of each
other and of native CPython:

| Benchmark (seconds) | Native | Chromium | Firefox | WebKit |
|---|---|---|---|---|
| 3M-iteration loop | 0.041 | 0.083 | 0.097 | 0.072 |
| 300k exceptions | 0.014 | 0.032 | 0.035 | 0.024 |
| 300k `contextmanager`s | 0.092 | 0.199 | 0.284 | 0.162 |
| Compile plain program, NumPy only | 0.22 | 0.30 | 0.44 | 0.25 |
| Compile I❤️MESH program, NumPy only | 4.6 | 6.2 | 8.8 | 5.3 |

The large Firefox and WebKit slowdowns appear only in long (minutes-long) all-output
compiles that block the page's main thread, and they vary widely from run to run in
the same browser:

| I❤️MESH program, all 6 outputs | Chromium | Firefox | WebKit |
|---|---|---|---|
| Compile button | 40 s | 80 s, 290 s | 82 s, 900+ s |
| Same call via `pyodide.runPythonAsync` | | 57 s | 308 s |

Memory is not the cause (Python peak 29 MB, WebAssembly memory 130 MB). The likely
cause is how these engines, or Playwright's builds of them, behave when the main
thread is blocked for minutes; this is unconfirmed. Not yet tested in real Safari or
Firefox.

## Options

| Change | Expected effect | Effort |
|---|---|---|
| Parse modules once per compile instead of once per output type | ~5× for module-importing programs with all outputs | small–medium; **done** |
| Working module cache, not keyed by output type | repeat compiles with the same modules nearly instant | small–medium; **done** (as a parse-tree cache) |
| Ship prebuilt caches for the built-in modules | first I❤️MESH compile also fast | medium |
| Rewrite left-recursive rules as loops (`term {op term}`); order keyword alternatives | likely several× faster parsing (unmeasured) | medium; parse-tree shape changes, so the type walker changes |
| Newer TatSu (5.15+) | unknown; needs porting (`FailedCut` was removed) | small–medium |
| Patch TatSu not to copy the rule stack into every `FailedParse` | 6% (measured) | small |
| Different parser (Lark LALR, tree-sitter, hand-written Pratt) | likely 10–100× | large |
| Split declared multi-letter names at the token level instead of re-parsing | removes the double parse | large |
| Web page: remove the 1 s `setTimeout`; compile in a Web Worker | 1 s off every compile; page stays responsive | small; **done** |

## Changes made (2026-10-31) and results

**Parse-tree cache** (`parse_cached` in `la_parser/parser.py`). Every TatSu parse goes
through an in-memory LRU cache (128 entries) keyed by the parser's configuration (the
declared names it was rebuilt with) and the source text. Within one compile, each
module and the program are now parsed once instead of once per output type; across
compiles in the same process (the web page, the GUI), unchanged programs and modules
are not parsed again. Only parse trees are cached: type checking reruns on a fresh
walker, so nothing an importer does to a module's symbols can leak between uses.

**Fresh state per compile.** Measuring repeat compiles exposed state leaking between
compiles in the same process, which made outputs depend on what was compiled before:

- Code generators were created once and reused; one that raised mid-compile left a
  scope pushed, and every later compile failed (`KeyError: 'sum_0'`). Others leaked
  substitutions into MATLAB output and local-function labels into MacroMathJax
  output, even within one compile (a module's local function labeled the main
  program's function). `get_codegen` now creates a new generator each time, and
  `init_type` resets the scope stack.
- Eigen type aliases (`DT`, `DT_`, `DT__`, ...) came from a process-wide counter, so a
  program's Eigen output gained underscores with every earlier compile. The counter
  is now reset at the start of each top-level compile.

Check: all 183 programs from the test suite plus the I❤️MESH program, compiled twice in
one process, match the output of compiling each in a fresh process with the previous
code, except the corrected MacroMathJax label (1 program). With the previous code, the
same run matched for only 10 of 184 programs in the first pass (mostly because of the
growing `DT_...` names) and 12 programs failed that compile on their own; in the second
pass none matched and only 11 compiled. The test suite passes (207/207).

**Native timings, I❤️MESH program, all 6 outputs:**

| | Before | After |
|---|---|---|
| First compile | 29.9 s | 7.1 s |
| Repeat compile (same process) | 60.2 s | 0.46 s |
| NumPy only, repeat | 7.5 s | 0.08 s |
| Plain program, first / repeat | 0.37 / 0.31 s | 0.30 / under 0.01 s |

**Web page.** The compiler runs in a module Web Worker (`docs/js/compile-worker.js`;
Pyodide requires module workers), the 1 s `setTimeout` is gone, and the page requests
only the five outputs it shows (MacroMathJax was computed and discarded). Errors now
show I❤️LA's message with line, column, and a caret instead of "Compile error!"; this
needed a fix to `is_new_tatsu_version`, which read `tatsu._version.__version__`
(`'1.14.0'` in TatSu 5.14) and compared versions as strings, so the parse-error
formatter crashed in the GUI and CLI too.

| Web page, I❤️MESH program | Chromium | WebKit |
|---|---|---|
| Before: first compile | 40 s | 82 s to 900+ s |
| After: first compile | 6.7–7.8 s | 5.9–6.3 s |
| After: repeat compile | 0.6–0.75 s | 1.5–1.6 s |
| After: worst main-thread latency during a compile | 1 ms | 1 ms |

Plain programs: 0.4–0.6 s per compile (previously 1.3–1.5 s, including the fixed 1 s
delay). Firefox could not be launched by Playwright in this session (its test build
exits with "Could not find profile folder"), so the worker version is untested in
Firefox; Firefox has supported module workers since version 114, and it passed the
earlier tests of the page.

Still open: TatSu's own speed (the grammar's left recursion), the double parse per
module, and shipping prebuilt caches; see Options.

## The Rust compiler (2026-11-01)

The Rust rewrite (`rust/`, see `notes/Architecture.md`) compiles the same language to the
same outputs. Measured on the same Mac (Rust release build) with the current Python
compiler, which includes the parse-tree cache above. The Python numbers are compile time
inside a fresh process after imports: "first" is a compile in a new process, "repeat" is
the same program again in that process. The Rust numbers are wall time of the `iheartla`
process, start-up included (about 4 ms: 2 ms to start and 2 ms to build the grammar's
regexes), best of 5. The CLI compiles one output per run, so "all 6 outputs" is 6
processes, each recompiling everything.

| Program | Outputs | Python first | Python repeat | Rust | Speed-up over Python first |
|---|---|---|---|---|---|
| Plain (`T₁`) | NumPy | 0.214 s | 0.001 s | 0.009 s | 24× |
| Plain (`T₁`) | all 6 (6 processes) | 0.221 s | 0.004 s | 0.054 s | 4× |
| I❤️MESH (`rust/corpus/mesh/one_ring.ila`) | NumPy | 5.20 s | 0.078 s | 0.039 s | 132× |
| I❤️MESH | all 6 (6 processes) | 5.24 s | 0.48 s | 0.228 s | 23× |
| I❤️MESH | all 6, one front end (as on the web page) | 5.24 s | 0.48 s | ≈0.04 s | ≈130× |

The last row is the front end once (34 ms) plus all six generators (together under 1 ms),
plus process start-up. The web page compiles this way, through `rust/src/wasm.rs`.

The 239 programs the Python test suite compiles, NumPy + Eigen: Python 37.0 s (one process,
with its cache), Rust 3.9 s (478 processes; mostly start-up).

Python's repeat compiles beat Rust's cold compile for plain programs, because Python
reuses cached parse trees and Rust doesn't cache. An in-process Rust cache would make
repeat compiles nearly free too, but at 9–40 ms per compile it hasn't been needed.

**Where Rust's time goes** (`IHEARTLA_TIMING=1 iheartla compile …` prints each phase), for
the I❤️MESH program, which imports `Neighborhoods`, which imports
`FundamentalMeshAccessors`:

| Phase | Time |
|---|---|
| First parse: program, Neighborhoods, FundamentalMeshAccessors | 5.0, 9.9, 3.2 ms |
| Second parse: FundamentalMeshAccessors, Neighborhoods, program | 5.0, 11.8, 0.8 ms |
| Type checking (each) | 0.02–0.3 ms |
| Front end, total | 34–38 ms |
| Generate NumPy, Eigen, LaTeX, MathJax, MATLAB, MacroMathJax | 0.22, 0.49, 0.03, 0.03, 0.01, 0.04 ms |

Parsing is still almost all the time, as in Python, but each module parse takes
milliseconds, not seconds. Parsing `Neighborhoods.hlang` (first pass) takes 16 ms including
start-up, against 1.64 s with TatSu (103×).

Why Rust is faster:
- **The parser** (`rust/src/peg.rs`) has TatSu's semantics (the same parse trees and
  errors, left recursion by seed growing) but memoizes cheaply and signals failure with
  return values instead of exceptions.
- **Each module is parsed and checked once per compilation** (`rust/src/modules.rs`), and
  one typed program serves every output.
- **There is no interpreter.** Type checking and code generation, about 2 s of the 66 s
  in the old Python profile, take under a millisecond.

**Web page** (`docs/`, headless Chromium 156 through Playwright, `rust/tools/web_check.py`).
The page has a Compiler choice. The Rust compiler is a 2.7 MB WebAssembly module
(`docs/rust/iheartla.wasm`, built by `docs/update_rust_wasm.sh`) and runs in its own Web
Worker. It returns the five outputs the page shows plus `generateRandomData()` and
`main()`.

| Web page | Python (Pyodide) | Rust (WebAssembly) |
|---|---|---|
| Compiler ready after page load | 2.8 s | 0.08–0.17 s |
| Plain program | 0.22 s | 0.09 s |
| I❤️MESH program, first compile | 6.8 s | 0.10 s |
| I❤️MESH program, repeat compile | 0.64 s | 0.10 s |

In Node 22, without the page, the WebAssembly module compiles the plain program in
32 ms and the I❤️MESH program in 65 ms, about 1.7× native.

Reproduce:
- `python rust/tools/bench_notes.py`: the first table and the test-program totals.
- `python rust/tools/bench.py` and `rust/tools/bench_mesh.py`: older tables, in `rust/README.md`.
- `uv run --with playwright python rust/tools/web_check.py`: the web page.

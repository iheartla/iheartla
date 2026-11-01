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

"""
The `iheartla-rust` command: the Rust I❤️LA compiler, built as WebAssembly
(docs/update_rust_wasm.sh), run with wasmtime, so no Rust toolchain is
needed. The command line is the `iheartla` command's (iheartla/__main__.py),
plus --name and --main. The module's interface is documented in
rust/src/wasm.rs.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

from iheartla.la_tools.babyheartdown import heartdown2lines

WASM = Path(__file__).parent / "rust" / "iheartla.wasm"
# the backends and the suffixes of the files they write, as `iheartla` writes them
SUFFIXES = {"numpy": ".py", "eigen": ".h", "latex": ".tex", "mathjax": ".tex", "matlab": ".m"}
DEFAULTS = ["latex", "numpy", "eigen", "matlab"]


class Compiler:
    """The WebAssembly module, finding modules that aren't builtin in `module_dir`."""

    def __init__(self):
        import wasmtime
        self.store = wasmtime.Store()
        self.module_dir = Path(".")
        i32 = wasmtime.ValType.i32()
        read_module = wasmtime.Func(self.store, wasmtime.FuncType([i32, i32], [i32]), self._read_module)
        self.exports = wasmtime.Instance(self.store, wasmtime.Module.from_file(self.store.engine, str(WASM)), [read_module]).exports(self.store)
        self.memory = self.exports["memory"]

    def _put(self, data):
        """`data` in a buffer allocated in the module: its address."""
        ptr = self.exports["ih_alloc"](self.store, len(data))
        self.memory.write(self.store, data, ptr)
        return ptr

    def _read_module(self, ptr, length):
        # as the Python compiler searches (la_parser/parser.py, get_compiled_module)
        name = bytes(self.memory.read(self.store, ptr, ptr + length)).decode()
        for path in (self.module_dir / (name + ".hlang"), self.module_dir / (name + ".ihla")):
            if path.is_file():
                src = path.read_bytes()
                return self._put(struct.pack("<I", len(src)) + src)
        return 0

    def compile(self, source, backends, name, main):
        """{backend: code}, or raises ValueError with the compiler's message."""
        request = json.dumps({"source": source, "backends": backends, "name": name, "main": main}).encode()
        ptr = self._put(request)
        result = self.exports["ih_compile_json"](self.store, ptr, len(request))
        self.exports["ih_free"](self.store, ptr, len(request))
        (length,) = struct.unpack("<I", bytes(self.memory.read(self.store, result, result + 4)))
        response = json.loads(bytes(self.memory.read(self.store, result + 4, result + 4 + length)))
        self.exports["ih_free"](self.store, result, length + 4)
        if "error" in response:
            raise ValueError(response["error"])
        return response["outputs"]


def main():
    arg_parser = argparse.ArgumentParser(description='The HeartLang Compiler (Rust, as WebAssembly)')
    arg_parser.add_argument('-o', '--output', help='The output language(s), comma-separated: numpy, eigen, latex, mathjax, matlab (e.g. -o numpy,eigen)')
    arg_parser.add_argument('--name', help="The generated class's or function's name (default: the input file's name, or heartlib for -)")
    arg_parser.add_argument('--main', action='store_true', help='Also generate generateRandomData() and main()')
    arg_parser.add_argument('input', nargs='+', help="The HeartLang files to compile ('-' for standard input, which prints the outputs).")
    args = arg_parser.parse_args()
    backends = args.output.split(",") if args.output else DEFAULTS
    for out in backends:
        if out not in SUFFIXES:
            arg_parser.error("Parameters after -o or --output can only be numpy, eigen, latex, mathjax, or matlab")
    compiler = Compiler()
    failed = False
    for input in args.input:
        if input == "-":
            source, name = sys.stdin.read(), "heartlib"
            compiler.module_dir = Path(".")
        else:
            source, name = Path(input).read_text(encoding="utf-8"), Path(input).stem
            compiler.module_dir = Path(input).parent
        try:
            outputs = compiler.compile(heartdown2lines(source), backends, args.name or name, args.main)
        except ValueError as e:
            print(e, file=sys.stderr)
            failed = True
            continue
        for backend, code in outputs.items():
            if input == "-":
                print(code)
            else:
                Path(input).with_suffix(SUFFIXES[backend]).write_text(code, encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()

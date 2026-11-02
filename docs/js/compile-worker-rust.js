// Runs the Rust I❤️LA compiler, built as WebAssembly (rust/iheartla.wasm; see
// docs/update_rust_wasm.sh), off the main thread. Same messages as
// compile-worker.js: main -> worker {id, source}; worker -> main {ready: true}
// once, then {id, code: [numpy, eigen, latex, mathjax, matlab]} or {id, error}.
// The module's interface is documented in rust/src/wasm.rs.

const wasmURL = new URL("../rust/iheartla.wasm", import.meta.url);
// The outputs the page shows, in its order.
const BACKENDS = ["numpy", "eigen", "latex", "mathjax", "matlab"];

// The page has no files: a module that isn't builtin is never found.
const imports = { iheartla: { read_module: () => 0 } };

async function instantiate() {
    try {
        const { instance } = await WebAssembly.instantiateStreaming(fetch(wasmURL), imports);
        return instance;
    } catch (e) {
        // (a server that doesn't send application/wasm)
        const bytes = await (await fetch(wasmURL)).arrayBuffer();
        const { instance } = await WebAssembly.instantiate(bytes, imports);
        return instance;
    }
}

let instance = instantiate();
instance.then(() => self.postMessage({ ready: true }),
              e => self.postMessage({ ready: false, error: "Failed to load the compiler: " + e.message }));

function compile(exports, source) {
    // main: also generateRandomData() and main(), as the Python compiler's page shows
    const request = JSON.stringify({ source, backends: BACKENDS, main: true });
    const input = new TextEncoder().encode(request);
    const ptr = exports.ih_alloc(input.length);
    new Uint8Array(exports.memory.buffer, ptr, input.length).set(input);
    const result = exports.ih_compile_json(ptr, input.length);
    exports.ih_free(ptr, input.length);
    const length = new DataView(exports.memory.buffer).getUint32(result, true);
    const json = new TextDecoder().decode(new Uint8Array(exports.memory.buffer, result + 4, length));
    exports.ih_free(result, length + 4);
    const out = JSON.parse(json);
    return out.error !== undefined ? out : { code: BACKENDS.map(b => out.outputs[b]) };
}

self.onmessage = async (event) => {
    const { id, source } = event.data;
    const exports = (await instance).exports;
    try {
        const out = compile(exports, source);
        if (out.error !== undefined) {
            self.postMessage({ id, error: out.error });
        } else {
            self.postMessage({ id, code: out.code });
        }
    } catch (e) {
        // a compiler bug (a panic): report it, and start a fresh instance for the next compile
        console.log(e);
        self.postMessage({ id, error: "Compile error! (internal error in the Rust compiler: " + e.message + ")" });
        instance = instantiate();
    }
};

// Runs the Rust I❤️LA compiler, built as WebAssembly (rust/iheartla.wasm; see
// docs/update_rust_wasm.sh), off the main thread. Same messages as
// compile-worker.js: main -> worker {id, source}; worker -> main {ready: true}
// once, then {id, code: [numpy, eigen, latex, mathjax, matlab]} or {id, error}.
// The module's interface is documented in rust/src/wasm.rs.

const wasmURL = new URL("../rust/iheartla.wasm", import.meta.url);

async function instantiate() {
    try {
        const { instance } = await WebAssembly.instantiateStreaming(fetch(wasmURL), {});
        return instance;
    } catch (e) {
        // (a server that doesn't send application/wasm)
        const bytes = await (await fetch(wasmURL)).arrayBuffer();
        const { instance } = await WebAssembly.instantiate(bytes, {});
        return instance;
    }
}

let instance = instantiate();
instance.then(() => self.postMessage({ ready: true }),
              e => self.postMessage({ ready: false, error: "Failed to load the compiler: " + e.message }));

function compile(exports, source) {
    const input = new TextEncoder().encode(source);
    const ptr = exports.ih_alloc(input.length);
    new Uint8Array(exports.memory.buffer, ptr, input.length).set(input);
    // 1: also generateRandomData() and main(), as the Python compiler's page shows
    const result = exports.ih_compile(ptr, input.length, 1);
    exports.ih_free(ptr, input.length);
    const length = new DataView(exports.memory.buffer).getUint32(result, true);
    const json = new TextDecoder().decode(new Uint8Array(exports.memory.buffer, result + 4, length));
    exports.ih_free(result, length + 4);
    return JSON.parse(json);
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

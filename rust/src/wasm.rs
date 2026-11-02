//! The compiler as a WebAssembly module (`wasm32-unknown-unknown`), for the
//! web page in `docs/` (see `docs/js/compile-worker-rust.js`) and the
//! `iheartla-rust` command (`iheartla/rust_wasm.py`).
//!
//! A plain C-style interface, so no bindings generator is needed. Buffers
//! the module returns are a 4-byte little-endian length followed by that
//! many bytes of UTF-8.
//!
//! - `ih_alloc(n)` reserves `n` bytes; `ih_free(ptr, n)` releases them.
//! - `ih_compile_json(ptr, len)` compiles the JSON request in the `len`
//!   bytes at `ptr`, `{"source": str, "backends": [str], "name": str,
//!   "main": bool}` (`name` defaults to "heartlib", `main` to false; see
//!   `crate::generate` for the backends), and returns a buffer of JSON:
//!   `{"outputs": {backend: code}}` in the request's order, or `{"error":
//!   message}`. The caller frees the request and the result.
//!
//! The module imports one function, `iheartla.read_module(ptr, len)`: given
//! a module name (UTF-8, `len` bytes at `ptr`), the host returns a buffer
//! allocated with `ih_alloc` holding the module's source, which the module
//! frees, or 0 if there is no such module. The builtin I❤️MESH modules are
//! compiled in, so the host is only asked for the others.

use serde_json::{json, Value};
use std::alloc::{alloc, dealloc, Layout};

#[link(wasm_import_module = "iheartla")]
extern "C" {
    fn read_module(ptr: *const u8, len: usize) -> *mut u8;
}

#[no_mangle]
pub extern "C" fn ih_alloc(n: usize) -> *mut u8 {
    unsafe { alloc(Layout::from_size_align(n.max(1), 4).unwrap()) }
}

#[no_mangle]
pub extern "C" fn ih_free(ptr: *mut u8, n: usize) {
    unsafe { dealloc(ptr, Layout::from_size_align(n.max(1), 4).unwrap()) }
}

#[no_mangle]
pub extern "C" fn ih_compile_json(ptr: *const u8, len: usize) -> *mut u8 {
    let request = unsafe { std::slice::from_raw_parts(ptr, len) };
    let response = match serde_json::from_slice(request) {
        Ok(request) => compile(&request),
        Err(e) => json!({ "error": format!("Invalid request: {e}") }),
    };
    let bytes = response.to_string().into_bytes();
    let out = ih_alloc(bytes.len() + 4);
    unsafe {
        std::ptr::copy_nonoverlapping((bytes.len() as u32).to_le_bytes().as_ptr(), out, 4);
        std::ptr::copy_nonoverlapping(bytes.as_ptr(), out.add(4), bytes.len());
    }
    out
}

fn compile(request: &Value) -> Value {
    let Some(src) = request["source"].as_str() else {
        return json!({ "error": "Invalid request: no source" });
    };
    let name = request["name"].as_str().unwrap_or("heartlib");
    let with_main = request["main"].as_bool().unwrap_or(false);
    let (tree, prog) = match crate::front_end_with(src, &crate::modules::Loader::with_host(host_module)) {
        Ok(x) => x,
        Err(e) => return json!({ "error": e }),
    };
    let mut outputs = serde_json::Map::new();
    for b in request["backends"].as_array().into_iter().flatten() {
        let Some(b) = b.as_str() else {
            return json!({ "error": "Invalid request: backends must be strings" });
        };
        match crate::generate(&tree, &prog, b, name, with_main) {
            Ok(code) => outputs.insert(b.to_string(), Value::String(code)),
            Err(e) => return json!({ "error": e }),
        };
    }
    json!({ "outputs": outputs })
}

/// A module's source, from the host.
fn host_module(name: &str) -> Option<String> {
    let ptr = unsafe { read_module(name.as_ptr(), name.len()) };
    if ptr.is_null() {
        return None;
    }
    unsafe {
        let len = u32::from_le_bytes(*(ptr as *const [u8; 4])) as usize;
        let src = String::from_utf8_lossy(std::slice::from_raw_parts(ptr.add(4), len)).into_owned();
        ih_free(ptr, len + 4);
        Some(src)
    }
}

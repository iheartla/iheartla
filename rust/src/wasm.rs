//! The compiler as a WebAssembly module (`wasm32-unknown-unknown`), for the
//! web page in `docs/` (see `docs/js/compile-worker-rust.js`).
//!
//! A plain C-style interface, so no bindings generator is needed:
//! `ih_alloc(n)` reserves `n` bytes for the UTF-8 source; `ih_compile(ptr,
//! len, with_main)` compiles it to every backend the page shows and returns a
//! pointer to a 4-byte little-endian length followed by that many bytes of
//! JSON: `{"code": [numpy, eigen, latex, mathjax, matlab]}` or
//! `{"error": message}`; `ih_free(ptr, n)` releases either buffer.

use std::alloc::{alloc, dealloc, Layout};

/// The outputs the page shows, in its order.
const BACKENDS: [&str; 5] = ["numpy", "eigen", "latex", "mathjax", "matlab"];

#[no_mangle]
pub extern "C" fn ih_alloc(n: usize) -> *mut u8 {
    unsafe { alloc(Layout::from_size_align(n.max(1), 4).unwrap()) }
}

#[no_mangle]
pub extern "C" fn ih_free(ptr: *mut u8, n: usize) {
    unsafe { dealloc(ptr, Layout::from_size_align(n.max(1), 4).unwrap()) }
}

#[no_mangle]
pub extern "C" fn ih_compile(ptr: *const u8, len: usize, with_main: u32) -> *mut u8 {
    let src = unsafe { std::slice::from_raw_parts(ptr, len) };
    let json = match std::str::from_utf8(src) {
        Ok(src) => compile_all(src, with_main != 0),
        Err(_) => serde_json::json!({ "error": "The source is not valid UTF-8" }),
    };
    let bytes = json.to_string().into_bytes();
    let out = ih_alloc(bytes.len() + 4);
    unsafe {
        std::ptr::copy_nonoverlapping((bytes.len() as u32).to_le_bytes().as_ptr(), out, 4);
        std::ptr::copy_nonoverlapping(bytes.as_ptr(), out.add(4), bytes.len());
    }
    out
}

fn compile_all(src: &str, with_main: bool) -> serde_json::Value {
    let (tree, prog) = match crate::front_end(src) {
        Ok(x) => x,
        Err(e) => return serde_json::json!({ "error": e }),
    };
    let mut code = Vec::new();
    for b in BACKENDS {
        match crate::generate(&tree, &prog, b, "heartlib", with_main) {
            Ok(c) => code.push(c),
            Err(e) => return serde_json::json!({ "error": e }),
        }
    }
    serde_json::json!({ "code": code })
}

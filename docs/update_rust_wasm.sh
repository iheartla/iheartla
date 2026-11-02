#!/bin/sh
# Build the Rust I❤️LA compiler as WebAssembly, for the web page (the "Rust"
# compiler choice; js/compile-worker-rust.js loads rust/iheartla.wasm) and for
# the iheartla-rust command (iheartla/rust_wasm.py), which the Python package
# carries as iheartla/rust/iheartla.wasm. Commit both copies (git stores them once).
# Needs the target: rustup target add wasm32-unknown-unknown
set -e
cd "$(dirname "$0")"
cargo build --manifest-path ../rust/Cargo.toml --lib --profile wasm --target wasm32-unknown-unknown
mkdir -p rust ../iheartla/rust
cp ../rust/target/wasm32-unknown-unknown/wasm/iheartla.wasm rust/iheartla.wasm
cp ../rust/target/wasm32-unknown-unknown/wasm/iheartla.wasm ../iheartla/rust/iheartla.wasm
ls -l rust/iheartla.wasm ../iheartla/rust/iheartla.wasm

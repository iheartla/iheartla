//! I❤️LA compiler.

pub mod decls;
pub mod dims;
pub mod grammar;
pub mod helper;
pub mod peg;
pub mod pnode;

/// Map byte offsets in `text` to character offsets (Python string indices).
pub fn char_offsets(text: &str) -> Vec<usize> {
    let mut map = vec![0; text.len() + 1];
    let mut n = 0;
    for (i, c) in text.char_indices() {
        for k in 0..c.len_utf8() {
            map[i + k] = n;
        }
        n += 1;
    }
    map[text.len()] = n;
    map
}

/// The source text of a parse node.
pub fn node_text<'a>(src: &'a str, node: &pnode::Val) -> &'a str {
    match node.node().and_then(|n| n.span) {
        Some((a, b)) => &src[a..b],
        None => "",
    }
}

//! (stub, to be ported from la_parser/codegen_mathjax.py)

use super::*;

pub struct CodeGenMathjax {
    pub b: VisitorBase,
}

impl CodeGenMathjax {
    pub fn new() -> Self {
        CodeGenMathjax { b: VisitorBase::new(Kind::Mathjax) }
    }
}

impl Backend for CodeGenMathjax {
    fn base(&self) -> &VisitorBase {
        &self.b
    }
    fn base_mut(&mut self) -> &mut VisitorBase {
        &mut self.b
    }
}

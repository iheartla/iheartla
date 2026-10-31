//! (stub, to be ported from la_parser/codegen_latex.py)

use super::*;

pub struct CodeGenLatex {
    pub b: VisitorBase,
}

impl CodeGenLatex {
    pub fn new() -> Self {
        CodeGenLatex { b: VisitorBase::new(Kind::Latex) }
    }
}

impl Backend for CodeGenLatex {
    fn base(&self) -> &VisitorBase {
        &self.b
    }
    fn base_mut(&mut self) -> &mut VisitorBase {
        &mut self.b
    }
}

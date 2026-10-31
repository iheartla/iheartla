//! (stub, to be ported from la_parser/codegen_macromathjax.py)

use super::*;

pub struct CodeGenMacroMathjax {
    pub b: VisitorBase,
}

impl CodeGenMacroMathjax {
    pub fn new() -> Self {
        CodeGenMacroMathjax { b: VisitorBase::new(Kind::MacroMathjax) }
    }
}

impl Backend for CodeGenMacroMathjax {
    fn base(&self) -> &VisitorBase {
        &self.b
    }
    fn base_mut(&mut self) -> &mut VisitorBase {
        &mut self.b
    }
}

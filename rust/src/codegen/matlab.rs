//! (stub, to be ported from la_parser/codegen_matlab.py)

use super::*;

pub struct CodeGenMatlab {
    pub b: VisitorBase,
}

impl CodeGenMatlab {
    pub fn new() -> Self {
        CodeGenMatlab { b: VisitorBase::new(Kind::Matlab) }
    }
}

impl Backend for CodeGenMatlab {
    fn base(&self) -> &VisitorBase {
        &self.b
    }
    fn base_mut(&mut self) -> &mut VisitorBase {
        &mut self.b
    }
}

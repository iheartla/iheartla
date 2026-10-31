//! (stub, to be ported from la_parser/codegen_numpy.py)

use super::*;

pub struct CodeGenNumpy {
    pub b: VisitorBase,
}

impl CodeGenNumpy {
    pub fn new() -> Self {
        CodeGenNumpy { b: VisitorBase::new(Kind::Numpy) }
    }
}

impl Backend for CodeGenNumpy {
    fn base(&self) -> &VisitorBase {
        &self.b
    }
    fn base_mut(&mut self) -> &mut VisitorBase {
        &mut self.b
    }
}

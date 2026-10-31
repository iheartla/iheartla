//! (stub, to be ported from la_parser/codegen_eigen.py)

use super::*;

pub struct CodeGenEigen {
    pub b: VisitorBase,
}

impl CodeGenEigen {
    pub fn new() -> Self {
        CodeGenEigen { b: VisitorBase::new(Kind::Eigen) }
    }
}

impl Backend for CodeGenEigen {
    fn base(&self) -> &VisitorBase {
        &self.b
    }
    fn base_mut(&mut self) -> &mut VisitorBase {
        &mut self.b
    }
}

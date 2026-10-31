//! (stub, to be ported)

use super::*;

impl TypeWalker {
    pub(super) fn walk_ElementConvertFunc(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_ElementConvertFunc".into()))
    }
    pub(super) fn walk_ArithExpression(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_ArithExpression".into()))
    }
    pub(super) fn walk_ArithSubexpression(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_ArithSubexpression".into()))
    }
    pub(super) fn walk_ArithBinary(&mut self, _node: &Val, _kw: &Kwargs, _class: &str) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_ArithBinary".into()))
    }
    pub(super) fn walk_ArithFactor(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_ArithFactor".into()))
    }
    pub(super) fn walk_builtin_func(&mut self, _node: &Val, _kw: &Kwargs, _class: &str) -> WResult<Option<NodeInfo>> {
        Err(WalkError::Other("not ported: walk_builtin_func".into()))
    }
}

//! (stub, to be ported)

use super::*;

impl TypeWalker {
    pub(super) fn walk_MultiCondExpr(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_MultiCondExpr".into()))
    }
    pub(super) fn walk_MultiIfs(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_MultiIfs".into()))
    }
    pub(super) fn walk_SingleIf(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_SingleIf".into()))
    }
    pub(super) fn walk_Vector(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Vector".into()))
    }
    pub(super) fn walk_Set(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Set".into()))
    }
    pub(super) fn walk_Matrix(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Matrix".into()))
    }
    pub(super) fn walk_MatrixRows(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_MatrixRows".into()))
    }
    pub(super) fn walk_MatrixRow(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_MatrixRow".into()))
    }
    pub(super) fn walk_MatrixRowCommas(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_MatrixRowCommas".into()))
    }
    pub(super) fn walk_ExpInMatrix(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_ExpInMatrix".into()))
    }
    pub(super) fn walk_NumMatrix(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_NumMatrix".into()))
    }
}

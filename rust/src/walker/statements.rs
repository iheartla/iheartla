//! (stub, to be ported)

use super::*;

impl TypeWalker {
    pub(super) fn walk_LocalFunc(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_LocalFunc".into()))
    }
    pub(super) fn walk_Destructure(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Destructure".into()))
    }
    pub(super) fn walk_Assignment(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Assignment".into()))
    }
    pub(super) fn walk_GeneralAssignment(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_GeneralAssignment".into()))
    }
    pub(super) fn walk_Summation(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Summation".into()))
    }
    pub(super) fn walk_Optimize(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Optimize".into()))
    }
    pub(super) fn walk_MultiCond(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<Vec<N>> {
        Err(WalkError::Other("not ported: walk_MultiCond".into()))
    }
    pub(super) fn walk_Domain(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_Domain".into()))
    }
    pub(super) fn walk_Integral(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Integral".into()))
    }
}

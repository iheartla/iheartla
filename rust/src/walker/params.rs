//! (stub, to be ported)

#![allow(unused_imports)]
use super::*;
use crate::helper::ParseInfo;
use crate::types::T;

impl TypeWalker {
    pub(super) fn walk_Start(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_Start".into()))
    }
    pub(super) fn walk_ParamsBlock(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_ParamsBlock".into()))
    }
    pub(super) fn walk_WhereConditions(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_WhereConditions".into()))
    }
    pub(super) fn walk_WhereCondition(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_WhereCondition".into()))
    }
    pub(super) fn walk_MatrixType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_MatrixType".into()))
    }
    pub(super) fn walk_VectorType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_VectorType".into()))
    }
    pub(super) fn walk_ScalarType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_ScalarType".into()))
    }
    pub(super) fn walk_NamedType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_NamedType".into()))
    }
    pub(super) fn walk_SetType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_SetType".into()))
    }
    pub(super) fn walk_TupleType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_TupleType".into()))
    }
    pub(super) fn walk_FunctionType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_FunctionType".into()))
    }
    pub(super) fn walk_MappingType(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_MappingType".into()))
    }
    pub(super) fn walk_ImportVar(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<Walked> {
        Err(WalkError::Other("not ported: walk_ImportVar".into()))
    }
    pub(super) fn walk_Import(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<N> {
        Err(WalkError::Other("not ported: walk_Import".into()))
    }
}

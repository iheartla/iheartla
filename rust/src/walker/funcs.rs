//! (stub, to be ported)

#![allow(unused_imports)]
use super::*;
use crate::helper::ParseInfo;
use crate::types::T;

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

impl TypeWalker {
    /// `type_inference(op, left_info, right_info)`: may replace `left.ir` /
    /// `right.ir` (ToDouble/ToMatrix wrappers); returns (ret_type or None, need_cast).
    pub(super) fn type_inference(
        &mut self,
        _op: crate::types::TypeInference,
        _left: &mut NodeInfo,
        _right: &mut NodeInfo,
    ) -> WResult<(Option<T>, bool)> {
        Err(WalkError::Other("not ported: type_inference".into()))
    }

    /// `get_sum_value(dim_list)`
    pub(super) fn get_sum_value(&self, _dims: &[crate::dims::Dim]) -> crate::dims::Dim {
        panic!("not ported: get_sum_value")
    }

    /// `check_bmat_validity(type_array, mat_size)` -> (valid, undef_list, type_array, real_dims)
    pub(super) fn check_bmat_validity(
        &mut self,
        _type_array: Vec<Vec<T>>,
        _mat_size: Option<(crate::dims::Dim, crate::dims::Dim)>,
    ) -> (bool, Vec<(usize, usize)>, Vec<Vec<T>>, (crate::dims::Dim, crate::dims::Dim)) {
        panic!("not ported: check_bmat_validity")
    }

    /// `create_math_node_info(func_type, param_info, remains)`
    pub(super) fn create_math_node_info(
        &mut self,
        _func_type: crate::ir::MathFuncType,
        _param_info: NodeInfo,
        _remains: Vec<NodeInfo>,
    ) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: create_math_node_info".into()))
    }
}

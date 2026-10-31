//! (stub, to be ported)

#![allow(unused_imports)]
use super::*;
use crate::helper::ParseInfo;
use crate::types::T;

impl TypeWalker {
    pub(super) fn walk_Function(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Function".into()))
    }
    pub(super) fn walk_IfCondition(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_IfCondition".into()))
    }
    pub(super) fn walk_AndCondition(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_AndCondition".into()))
    }
    pub(super) fn walk_AtomCondition(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_AtomCondition".into()))
    }
    pub(super) fn walk_InCondition(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_InCondition".into()))
    }
    pub(super) fn walk_NotInCondition(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_NotInCondition".into()))
    }
    pub(super) fn walk_BinComp(&mut self, _node: &Val, _kw: &Kwargs, _class: &str) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_BinComp".into()))
    }
    pub(super) fn walk_IdentifierSubscript(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_IdentifierSubscript".into()))
    }
    pub(super) fn walk_IdentifierAlone(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_IdentifierAlone".into()))
    }
    pub(super) fn walk_Factor(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Factor".into()))
    }
    pub(super) fn walk_Constant(&mut self, _node: &Val, _kw: &Kwargs, _class: &str) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Constant".into()))
    }
    pub(super) fn walk_Integer(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Integer".into()))
    }
    pub(super) fn walk_SubInteger(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_SubInteger".into()))
    }
    pub(super) fn walk_SupInteger(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_SupInteger".into()))
    }
    pub(super) fn walk_Double(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Double".into()))
    }
    pub(super) fn walk_Fraction(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<NodeInfo> {
        Err(WalkError::Other("not ported: walk_Fraction".into()))
    }
    pub(super) fn walk_Mantissa(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<String> {
        Err(WalkError::Other("not ported: walk_Mantissa".into()))
    }
    pub(super) fn walk_Exponent(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<String> {
        Err(WalkError::Other("not ported: walk_Exponent".into()))
    }
    pub(super) fn walk_Float(&mut self, _node: &Val, _kw: &Kwargs) -> WResult<String> {
        Err(WalkError::Other("not ported: walk_Float".into()))
    }
}

impl TypeWalker {
    /// `create_id_node_info(left_content, right_content, parse_info)`
    pub(super) fn create_id_node_info(&mut self, _left: &str, _right: Vec<String>, _pi: Option<ParseInfo>) -> NodeInfo {
        panic!("not ported: create_id_node_info")
    }

    /// `update_sub_sym_lists(main_sym, right_sym_list)`
    pub(super) fn update_sub_sym_lists(&mut self, _main: &str, _right: &[String]) {
        panic!("not ported: update_sub_sym_lists")
    }
}

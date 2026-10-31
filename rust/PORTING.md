# Porting conventions (Python compiler → rust/)

The goal is a **faithful, line-by-line port**: the Rust compiler must produce
byte-identical output to the Python compiler (goldens in `corpus/golden/*.json`).
Keep Python method names (`walk_Assignment`, `visit_summation`, `get_rand_test_str`)
and Python control flow, including its quirks and bugs. Do not "improve" logic.
Where Python would raise (KeyError, IndexError, AttributeError on None), it is
fine to `panic!`/`unwrap()` — the type walker catches panics where Python
catches `Exception`.

## Core types (read these files first)

- `src/types.rs` — `T` is a shared mutable type (`Rc<RefCell<LaType>>`, Python
  object semantics). Getters: `t.rows()`, `t.elem()` (element_type, panics if
  None), `t.is_matrix()`, ... Mutation: `t.set(|x| x.rows = 3.into())`.
  Constructors mirror Python: `T::scalar()`, `T::scalar_int(true)`,
  `T::matrix(r, c)` (shared default element type, see module docs),
  `T::matrix_with(r, c, Some(elem))`, `T::vector(r)`, `T::sequence(size, elem)`,
  `T::set_type(...)`, `T::tuple(..)`, `T::function(params, ret)`,
  `T::vertex(owner)`, `T::vertex_set(length, owner)`, ... `.with_owner(o)`.
  `copy.deepcopy(t)` is `t.deep_copy()`. `t1 == t2` is identity (`is`).
- `src/dims.rs` — `Dim` = Python dims (`None`/int/str/SymPy expr).
  `isinstance(d, int)` → `d.is_int()`, `str(d)`/`format` → `d.to_string()`,
  Python `==` → `d.py_eq(&e)`, `is_same_expr(a, b)`, `mul_dims`, `add_syms`,
  `simpify`. `"{}".format(d)` of None prints "None".
- `src/ir.rs` — `N` is a shared IR node. Every attribute of every Python IR
  class is a field of `IrNode`; read with `n.left()`, `n.value()` (clones),
  write with `n.set(|x| x.left = Some(l))`. Renamed fields are listed in the
  module docs (e.g. `lefts`, `int_value`, `op_str`, `set_node`, `loop_`).
  `node.la_type` → `n.la_type()`; set with `n.set_la_type(Some(t))`.
  `node.node_type == IRNodeType.X` → `n.is_node(IRNodeType::X)`.
  Methods `get_name`, `get_main_id`, `contain_subscript`, `get_all_ids`, ...
- `src/helper.rs` — Python string predicates (`py_isnumeric`, `str_isnumeric`,
  ...), `ParseInfo`/`LineInfo`, error messages `get_err_msg_info`,
  `get_err_msg`, Unicode tables, `is_keyword`.
- `src/packages.rs` — la_package.py (mesh helper names/types, `Backend` enum).
- `src/walker/data.rs` — `ParamsData` (shared as `PD` =
  `Rc<RefCell<ParamsData>>`), `Symtab` (shared `IndexMap<String, T>`),
  `NodeInfo`, `Kwargs`, `Walked`, `WalkError`, `Content`, `LaTy`.

Python dicts → `IndexMap` (insertion order). Python sets → `IndexSet`.
Python `None` → `Option`. Formatting: use `format!` reproducing Python's
`str.format` output exactly (e.g. Python `True`/`False`, `None`).

## Type walker (`src/walker/*.rs`)

`impl TypeWalker` blocks; signatures are fixed by the stubs/dispatch in
`walker/mod.rs`. Parse nodes are `&Val` (`src/pnode.rs`): `node.get("left")`
returns `&Val` (`Val::None` if absent), `node.class()` is the TatSu class
name (`type(node).__name__`), `node.items()` iterates lists, `.as_str()`,
`.truthy()`. `node.text` → `self.text(node)` (Option) / `self.text_s(node)`;
`node.parseinfo` → `self.pinfo(node)` (Option<ParseInfo>).

- `self.walk(x, **kwargs)` → `self.walk(x, kw)?` (returns `Walked`; use
  `.info()`, `.node()`); helpers `self.wi(x, kw)?` (NodeInfo) and
  `self.wi0(x)?` for `self.walk(x)` *without* kwargs (fresh kwargs!).
- kwargs: `&Kwargs`. To modify (`kwargs[LHS] = ...`), clone into a local
  `let mut kw = kw.clone();`. Note `la_remove_key(...)` in Python is a no-op
  (it receives a copy) — do not remove anything.
- `self.assert_expr(cond, msg)` → `self.assert_expr(cond, || msg)?`.
  `get_err_msg_info(node.parseinfo, "...")` →
  `TypeWalker::err_info(&self.pinfo(node), "...")` or
  `get_err_msg_info(ir.parse_info().as_ref(), "...")`.
  Plain Python `assert` → `self.py_assert(...)?`.
- `raise RecursiveException` → `return Err(WalkError::Recursive)`.
- Symbol tables: `self.symtable` (global, `Symtab`), current scope:
  `self.cur_symtable()` / `self.get_cur_param_data()` (PD). Lookups
  `self.get_sym_type(s)`, `self.is_sym_existed(s)`, `self.add_sym(...)`.
- `NodeInfo(la_type, content, symbols, ir)`: `NodeInfo::with(t, Content::Str(..),
  symbols, ir)`, or build the struct. `node_info.la_type` may be a list:
  `LaTy::List`. `info.t()` gets the single type, `info.ir()` the node.
- IR construction: `N::with(IRNodeType::Add, self.pinfo(node), self.text(node))`
  then `n.set(|x| {x.left = ...; x.right = ...})`, `n.set_la_type(Some(t))`,
  `child.set_parent(&n)`.

## Code generators (`src/codegen/<backend>.rs`)

A backend is a struct `{ b: VisitorBase, ...own fields... }` implementing
`codegen::Backend` (`base()`, `base_mut()`, then override `visit_*` methods
and add helper methods). `VisitorBase` holds the IRVisitor attributes and
helpers (`get_sym_type`, `symtable()`, `parameters()`, `generate_var_name`,
`convert_unicode`, `trim_content`, `get_main_id`, `get_all_ids`,
`update_prelist_str`, ...). `self.code_frame` → `self.b.code_frame`.
Visits return `CodeNodeInfo { content, pre_list }` (LaTeX-family backends
return strings in Python: return `CodeNodeInfo::new(s)` and use `.s()`).
`**kwargs` → `&Kw` (a small map: `kw.has("x")`, `kw.with("x", KwVal::Bool(true))`).
`super().visit_x(node, **kwargs)` → `super_visit_x(self, node, kw)` (free
functions in `codegen/mod.rs` holding the base-class bodies). For class
hierarchies inside the port (MathJax extends LaTeX, MacroMathJax extends
MathJax), give the subclass struct a field holding the parent struct, or
write the parent's methods as free generic functions that both use.

## Checking your work

`cd rust && cargo build --release` must pass. Run `cargo test --release` for
unit tests. Golden outputs: `python3 tools/show_golden.py <case> numpy` (etc.)
shows the expected output for a case; `corpus/golden/*.json` has all cases.

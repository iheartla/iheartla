//! Type checker: lowers the parse tree of the full grammar to a typed
//! `ast::Program`.
//!
//! Design (compared with the Python compiler's type walker):
//! - types are immutable values (`ty::Ty`); nothing is patched after the fact;
//! - statements are ordered by their dependencies (which names each one
//!   defines and uses), not by retrying them until they succeed;
//! - the extent of an implicit subscript (`∑_i x_i`, `y_i = 2 x_i`) is
//!   inferred from the shapes of what it subscripts;
//! - errors carry the source position and use the Python compiler's message
//!   format ("Error on line L at column C. message.").

use crate::ast::*;
use crate::decls::ident_name;
use crate::dims::{add_syms, is_same_expr, mul_dims, Dim};
use crate::helper::{get_err_msg_info, get_unicode_fraction, get_unicode_number, get_unicode_sub_number, ParseInfo, Source};
use crate::pnode::Val;
use crate::ty::*;
use indexmap::{IndexMap, IndexSet};
use std::collections::HashMap;
use std::rc::Rc;

#[derive(Debug, Clone)]
pub struct CheckError {
    pub message: String,
}

type R<T> = Result<T, CheckError>;

/// What a name refers to.
#[derive(Clone, Debug)]
enum Sym {
    Param(Ty),
    Def(Ty),
    /// a dimension symbol (an integer read from a parameter's shape)
    Dim,
    /// a local (function parameter, summation index, subscript variable)
    Local(Ty),
    Func(Ty),
}

impl Sym {
    fn ty(&self) -> Ty {
        match self {
            Sym::Param(t) | Sym::Def(t) | Sym::Local(t) | Sym::Func(t) => t.clone(),
            Sym::Dim => Ty::int(),
        }
    }
}

pub struct Checker<'a> {
    src: &'a str,
    source: Rc<Source>,
    globals: IndexMap<String, Sym>,
    scopes: Vec<IndexMap<String, Sym>>,
    params: Vec<Param>,
    dims: Vec<DimSym>,
    dim_checks: Vec<(Dim, Dim)>,
    min_dims: IndexMap<String, i64>,
    derivatives: bool,
    /// renamed builtins: new name -> builtin name
    builtin_names: IndexMap<String, String>,
    const_e: bool,
    /// subscript variables whose extent is being inferred: var -> extents seen
    extents: Vec<IndexMap<String, Vec<Dim>>>,
    defs: Vec<(String, Ty)>,
    counter: usize,
    /// number of definitions of each function name (several: overloads)
    func_counts: IndexMap<String, usize>,
    /// overloads of each function name: (type, name of this overload)
    overloads: IndexMap<String, Vec<(Ty, String)>>,
    /// matrices declared in a where block but defined by an assignment
    declared_only: IndexSet<String>,
    expr_types: HashMap<(usize, usize), Ty>,
    base_types: HashMap<(usize, usize), Ty>,
    loader: Option<Rc<crate::modules::Loader>>,
    meshes: Vec<(String, MeshKind)>,
    modules: Vec<ModuleUse>,
    opt_vars: IndexMap<String, Ty>,
}

impl<'a> Checker<'a> {
    pub fn new(src: &'a str) -> Self {
        Checker {
            src,
            source: Source::new(src),
            globals: IndexMap::new(),
            scopes: Vec::new(),
            params: Vec::new(),
            dims: Vec::new(),
            dim_checks: Vec::new(),
            min_dims: IndexMap::new(),
            derivatives: false,
            builtin_names: IndexMap::new(),
            const_e: false,
            extents: Vec::new(),
            defs: Vec::new(),
            counter: 0,
            func_counts: IndexMap::new(),
            overloads: IndexMap::new(),
            declared_only: IndexSet::new(),
            expr_types: HashMap::new(),
            base_types: HashMap::new(),
            loader: None,
            meshes: Vec::new(),
            modules: Vec::new(),
            opt_vars: IndexMap::new(),
        }
    }

    /// Find and compile imported modules with `loader`.
    pub fn with_loader(mut self, loader: Rc<crate::modules::Loader>) -> Self {
        self.loader = Some(loader);
        self
    }

    // -- positions and errors ------------------------------------------------

    fn pinfo(&self, node: &Val) -> Option<ParseInfo> {
        let (a, b) = node.node()?.span?;
        Some(ParseInfo { src: self.source.clone(), pos: self.source.char_of_byte(a), endpos: self.source.char_of_byte(b) })
    }

    fn text(&self, node: &Val) -> String {
        crate::node_text(self.src, node).to_string()
    }

    fn err<T>(&self, node: &Val, msg: impl AsRef<str>) -> R<T> {
        Err(CheckError { message: get_err_msg_info(self.pinfo(node).as_ref(), msg.as_ref()) })
    }

    fn ensure(&self, cond: bool, node: &Val, msg: impl FnOnce() -> String) -> R<()> {
        if cond {
            Ok(())
        } else {
            self.err(node, msg())
        }
    }

    // -- symbols -------------------------------------------------------------

    fn lookup(&self, name: &str) -> Option<Sym> {
        for s in self.scopes.iter().rev() {
            if let Some(x) = s.get(name) {
                return Some(x.clone());
            }
        }
        self.globals.get(name).cloned()
    }

    fn is_defined(&self, name: &str) -> bool {
        self.lookup(name).is_some()
    }

    fn define_local(&mut self, name: &str, ty: Ty) {
        match self.scopes.last_mut() {
            Some(s) => {
                s.insert(name.to_string(), Sym::Local(ty));
            }
            None => {
                self.globals.insert(name.to_string(), Sym::Local(ty));
            }
        }
    }

    fn fresh(&mut self, base: &str) -> String {
        self.counter += 1;
        format!("{base}_{}", self.counter)
    }

    // -- program -------------------------------------------------------------

    pub fn check(mut self, start: &Val) -> R<Program> {
        let vblocks: Vec<Val> = start.get("vblock").items().to_vec();
        // count definitions of each function name, to name overloads
        for b in &vblocks {
            match b.class() {
                "ParamsBlock" => {
                    for cond in b.get("conds").get("value").items() {
                        if cond.get("type").class() == "FunctionType" {
                            for id in cond.get("id").items() {
                                *self.func_counts.entry(crate::decls::main_name(id)).or_default() += 1;
                            }
                        }
                    }
                }
                "Statements" if b.get("stat").class() == "LocalFunc" => {
                    *self.func_counts.entry(local_func_name(b.get("stat"))).or_default() += 1;
                }
                _ => {}
            }
        }
        for b in vblocks.iter().filter(|b| b.class() == "Import") {
            self.import(b)?;
        }
        for b in vblocks.iter().filter(|b| b.class() == "ParamsBlock") {
            for cond in b.get("conds").get("value").items() {
                self.where_condition(cond, true)?;
            }
        }
        let stmts: Vec<Val> = vblocks.iter().filter(|b| b.class() == "Statements").map(|b| b.get("stat").clone()).collect();
        let last_index = stmts.len().saturating_sub(1);
        let order = self.def_use_order(&stmts);
        let mut out = Vec::new();
        let mut ret = None;
        for i in order {
            let s = &stmts[i];
            let is_last = i == last_index;
            match s.class() {
                "Assignment" | "GeneralAssignment" => {
                    let st = self.assignment(s)?;
                    if is_last {
                        ret = Some(match &st {
                            Stmt::Assign(a) => a.lhs.clone(),
                            Stmt::Multi { lhs, .. } => lhs.last().unwrap().0.clone(),
                            Stmt::Func(f) => f.name.clone(),
                        });
                    }
                    out.push(st);
                }
                "Destructure" => {
                    let st = self.destructure(s)?;
                    if is_last {
                        if let Stmt::Multi { lhs, .. } = &st {
                            ret = Some(lhs.last().unwrap().0.clone());
                        }
                    }
                    out.push(st);
                }
                "LocalFunc" => {
                    let f = self.local_func(s)?;
                    out.push(Stmt::Func(f));
                }
                _ => {
                    // an expression: its value is the result `ret`
                    let rhs = self.expr(s)?;
                    let ty = rhs.ty.clone();
                    let name = "ret".to_string();
                    self.globals.insert(name.clone(), Sym::Def(ty.clone()));
                    self.defs.push((name.clone(), ty.clone()));
                    out.push(Stmt::Assign(Assign {
                        lhs: name.clone(),
                        subs: vec![],
                        ty,
                        rhs,
                        accumulate: false,
                        update: false,
                        text: self.text(s),
                        extents: vec![],
                    }));
                    if is_last {
                        ret = Some(name);
                    }
                }
            }
        }
        // matrices declared in a where block but defined by an assignment are
        // not parameters; then find where to read each dimension
        let declared_only = self.declared_only.clone();
        self.params.retain(|p| !declared_only.contains(&p.name));
        for p in self.params.clone() {
            self.register_dims(&p.name, &p.ty);
        }
        Ok(Program {
            source: self.src.to_string(),
            params: self.params,
            dims: self.dims,
            dim_checks: self.dim_checks,
            min_dims: self.min_dims.into_iter().collect(),
            derivatives: self.derivatives,
            stmts: out,
            ret,
            defs: self.defs,
            expr_types: self.expr_types,
            base_types: self.base_types,
            meshes: self.meshes,
            modules: self.modules,
            funcs: self.overloads.into_iter().collect(),
            opt_vars: self.opt_vars.into_iter().collect(),
        })
    }

    /// Order statements so that every statement comes after the statements
    /// defining the names it uses (keeping source order otherwise).
    fn def_use_order(&self, stmts: &[Val]) -> Vec<usize> {
        let defines: Vec<IndexSet<String>> = stmts.iter().map(stmt_defines).collect();
        let uses: Vec<IndexSet<String>> = stmts.iter().map(|s| {
            let mut u = IndexSet::new();
            collect_names(s, &mut u);
            u
        }).collect();
        let mut done = vec![false; stmts.len()];
        let mut order = Vec::new();
        while order.len() < stmts.len() {
            let ready = (0..stmts.len()).find(|&i| {
                !done[i]
                    && uses[i].iter().all(|n| {
                        (0..stmts.len()).all(|j| j == i || done[j] || !defines[j].contains(n))
                    })
            });
            // a cycle (or a use of an undefined name): continue in source order
            let i = ready.unwrap_or_else(|| (0..stmts.len()).find(|&i| !done[i]).unwrap());
            done[i] = true;
            order.push(i);
        }
        order
    }

    fn import(&mut self, node: &Val) -> R<()> {
        let pkg = ident_name(node.get("package"));
        let Some(names) = crate::decls::package_names(&pkg) else {
            return self.import_module(node, &pkg);
        };
        let mut imported: Vec<(String, String)> = Vec::new();
        if node.get("star").truthy() {
            imported = names.iter().map(|n| (n.to_string(), n.to_string())).collect();
        }
        for v in node.get("names").items() {
            let name = ident_name(v.get("name"));
            let r = if v.get("r").truthy() { ident_name(v.get("r")) } else { name.clone() };
            if !names.contains(&name.as_str()) {
                return self.err(node, format!("Function {name} not exist"));
            }
            imported.push((name, r));
        }
        for (name, r) in imported {
            if name == "e" {
                self.const_e = true;
            } else {
                self.builtin_names.insert(r, name);
            }
        }
        Ok(())
    }

    /// `X, Y from Module(args)`: compile the module and bind its parameters
    /// to the arguments; the imported symbols get the module's types with
    /// the parameters substituted.
    fn import_module(&mut self, node: &Val, pkg: &str) -> R<()> {
        let Some(loader) = self.loader.clone() else {
            return self.err(node, format!("Module {pkg} is not supported here"));
        };
        let prog = match loader.load(pkg) {
            Ok(p) => p,
            Err(e) => return self.err(node, e),
        };
        let args: Vec<String> = node.get("params").items().iter().map(ident_name).collect();
        let mparams: Vec<String> = prog.params.iter().map(|p| p.name.clone()).collect();
        if args.len() != mparams.len() {
            return self.err(node, format!("Module {pkg} takes {} parameters, {} given", mparams.len(), args.len()));
        }
        let map: HashMap<String, String> = mparams.into_iter().zip(args.iter().cloned()).collect();
        let mut wanted: Vec<(String, String)> = Vec::new();
        if node.get("star").truthy() {
            for (n, _) in &prog.funcs {
                wanted.push((n.clone(), n.clone()));
            }
            for (n, _) in &prog.defs {
                wanted.push((n.clone(), n.clone()));
            }
        }
        for v in node.get("names").items() {
            let name = ident_name(v.get("name"));
            let r = if v.get("r").truthy() { ident_name(v.get("r")) } else { name.clone() };
            wanted.push((name, r));
        }
        let mut syms = Vec::new();
        for (name, r) in wanted {
            if let Some((_, list)) = prog.funcs.iter().find(|(n, _)| *n == name) {
                // every overload, named here as in the module (or after the new name)
                for (k, (t, imp)) in list.iter().enumerate() {
                    let here = if r == name { imp.clone() } else if k == 0 { r.clone() } else { format!("{r}_{}", k - 1) };
                    self.overloads.entry(r.clone()).or_default().push((subst_ty(t, &map), here.clone()));
                    syms.push((imp.clone(), here));
                }
                *self.func_counts.entry(r.clone()).or_default() += list.len();
                self.globals.insert(r.clone(), Sym::Func(subst_ty(&list[0].0, &map)));
            } else if let Some((_, t)) = prog.defs.iter().find(|(n, _)| *n == name) {
                self.globals.insert(r.clone(), Sym::Def(subst_ty(t, &map)));
                syms.push((name, r));
            } else {
                return self.err(node, format!("Symbol {name} doesn't exist in module {pkg}"));
            }
        }
        self.modules.push(ModuleUse { name: pkg.to_string(), prog, args, syms });
        Ok(())
    }

    // -- parameters ----------------------------------------------------------

    fn where_condition(&mut self, cond: &Val, global: bool) -> R<Vec<(String, Ty)>> {
        let tnode = cond.get("type");
        let mut ty = if tnode.class() == "MappingType" && tnode.get("s").truthy() {
            // x ∈ S: an element of the set S (x ⊂ S: a subset)
            let set_name = crate::decls::main_name(tnode.get("s"));
            match self.lookup(&set_name).map(|s| s.ty()) {
                Some(t @ Set { .. }) => {
                    if cond.get("subset").truthy() {
                        t
                    } else {
                        match &t {
                            Set { elems, .. } if elems.len() == 1 => Scalar(elems[0]),
                            Set { elems, .. } => Tuple(elems.iter().map(|e| Scalar(*e)).collect()),
                            _ => unreachable!(),
                        }
                    }
                }
                Some(_) => return self.err(tnode, format!("Symbol {set_name} should be a set")),
                None => return self.err(tnode, format!("Symbol {set_name} is not defined")),
            }
        } else {
            self.la_type(tnode, global)?
        };
        if let Some(a) = cond.get("attrib").as_str() {
            let elem = match a {
                "vertices" => Elem::Vertex,
                "edges" => Elem::Edge,
                "faces" => Elem::Face,
                "tets" => Elem::Tet,
                _ => Elem::Index,
            };
            ty = match ty {
                Set { elems, length } => Set { elems: vec![elem; elems.len()], length },
                t => t.with_elem(elem),
            };
        }
        let desc = cond.get("desc").as_str().map(|s| s.trim().to_string()).filter(|s| !s.is_empty());
        let mut out = Vec::new();
        for id in cond.get("id").items() {
            if let (Func { params, rets }, "IdentifierSubscript") = (&ty, id.class()) {
                // D_i ∈ ℝ^3 -> ℝ: a function of its subscripts too, D: ℤ × ℝ^3 -> ℝ, as for
                // local functions (f_i(x) = ...): D_i(u_i) calls D(i, u_i)
                let name = ident_name(id.get("left"));
                let mut ps = vec![Ty::int(); id.get("right").items().len()];
                ps.extend(params.iter().cloned());
                let pty = Func { params: ps, rets: rets.clone() };
                if global {
                    let impl_name = self.add_func(&name, pty.clone(), id)?;
                    self.params.push(Param { name: impl_name, ty: pty.clone(), desc: desc.clone() });
                }
                out.push((name, pty));
                continue;
            }
            let (name, seq) = match id.class() {
                "IdentifierSubscript" => {
                    let main = ident_name(id.get("left"));
                    let subs = id.get("right").items();
                    self.ensure(subs.len() == 1, id, || format!("Parameter {main} can't use multiple subscripts"))?;
                    if subs[0].class() == "Integer" || subs[0].class() == "SubInteger" {
                        return self.err(id, format!("Parameter {main} can't have constant subscript"));
                    }
                    (main, true)
                }
                _ => (ident_name(id), false),
            };
            let pty = if seq {
                // x_i ∈ ℝ^n: a sequence whose size is read from the argument
                let size = format!("{}_n", name);
                Seq { size: Dim::Str(size), elem: Box::new(ty.clone()) }
            } else {
                ty.clone()
            };
            if let (Mesh(kind), true) = (&pty, global) {
                self.meshes.push((name.clone(), *kind));
            }
            if global {
                if pty.is_func() {
                    let impl_name = self.add_func(&name, pty.clone(), id)?;
                    self.params.push(Param { name: impl_name, ty: pty.clone(), desc: desc.clone() });
                } else {
                    if self.globals.get(&name).is_some_and(|s| !matches!(s, Sym::Dim)) {
                        return self.err(id, format!("Parameter {name} has been defined."));
                    }
                    self.globals.insert(name.clone(), Sym::Param(pty.clone()));
                    self.params.push(Param { name: name.clone(), ty: pty.clone(), desc: desc.clone() });
                    self.note_dim_symbols(&pty);
                }
            }
            out.push((name, pty));
        }
        Ok(out)
    }

    /// Record where each dimension symbol of a parameter's type can be read.
    fn register_dims(&mut self, param: &str, ty: &Ty) {
        let mut axes: Vec<Dim> = Vec::new();
        match ty {
            Seq { size, elem } => {
                axes.push(size.clone());
                axes.push(elem.rows());
                if elem.is_matrix() {
                    axes.push(elem.cols());
                }
                if elem.is_scalar() || elem.is_func() || elem.is_set() {
                    axes.truncate(1);
                }
            }
            Vector { rows, .. } => axes.push(rows.clone()),
            Matrix { rows, cols, .. } => {
                axes.push(rows.clone());
                axes.push(cols.clone());
            }
            _ => {}
        }
        for (axis, d) in axes.into_iter().enumerate() {
            if let Dim::Str(name) = &d {
                if is_simple_name(name) {
                    if self.dims.iter().any(|x| &x.name == name) || self.params.iter().any(|p| &p.name == name) {
                        continue;
                    }
                    self.dims.push(DimSym { name: name.clone(), param: param.to_string(), axis });
                }
            }
        }
    }

    /// Record that the extents a subscript ranges over must be equal (e.g. the
    /// columns of `w` and the length of `M` in `∑_j w_i,j M_j`).
    fn note_equal_extents(&mut self, frame: &IndexMap<String, Vec<Dim>>) {
        for seen in frame.values() {
            if let Some(first) = seen.first() {
                for d in &seen[1..] {
                    if !is_same_expr(first, d) && !self.dim_checks.iter().any(|(a, b)| is_same_expr(a, first) && is_same_expr(b, d)) {
                        self.dim_checks.push((first.clone(), d.clone()));
                    }
                }
            }
        }
    }

    /// Define the dimension symbols of a parameter's type.
    fn note_dim_symbols(&mut self, ty: &Ty) {
        let dims = match ty {
            Seq { size, elem } => vec![size.clone(), elem.rows(), elem.cols()],
            t => vec![t.rows(), t.cols()],
        };
        for d in dims {
            if let Dim::Str(name) = &d {
                if is_simple_name(name) {
                    self.globals.entry(name.clone()).or_insert(Sym::Dim);
                }
            }
        }
    }

    /// Define a function (a parameter or local function); returns the name
    /// of this definition (`f_0`, `f_1`, ... when `f` is overloaded).
    fn add_func(&mut self, name: &str, ty: Ty, node: &Val) -> R<String> {
        let count = self.func_counts.get(name).copied().unwrap_or(1);
        let list = self.overloads.entry(name.to_string()).or_default();
        if list.iter().any(|(t, _)| same_signature(t, &ty)) {
            return self.err(node, "Multiple functions with same signature");
        }
        // the first definition keeps the name, later ones are f_0, f_1, ...
        let impl_name = if count > 1 && !list.is_empty() { format!("{name}_{}", list.len() - 1) } else { name.to_string() };
        list.push((ty.clone(), impl_name.clone()));
        if count <= 1 && self.globals.get(name).is_some_and(|s| !matches!(s, Sym::Dim)) {
            return self.err(node, format!("Symbol {name} has been defined"));
        }
        self.globals.insert(name.to_string(), Sym::Func(ty));
        Ok(impl_name)
    }

    fn la_type(&mut self, t: &Val, global: bool) -> R<Ty> {
        let elem = |n: &Val| if n.get("type").as_str() == Some("ℤ") { Elem::Int } else { Elem::Real };
        let sparse = |n: &Val| n.get("attr").items().iter().any(|a| a.as_str() == Some("sparse"));
        Ok(match t.class() {
            "ScalarType" => Scalar(if t.get("z").truthy() { Elem::Int } else { Elem::Real }),
            "VectorType" => {
                let rows = self.dim(t.get("id1"))?;
                Vector { rows, elem: elem(t) }
            }
            "MatrixType" => {
                let rows = self.dim(t.get("id1"))?;
                let cols = self.dim(t.get("id2"))?;
                Matrix { rows, cols, elem: elem(t), sparse: sparse(t) }
            }
            "SetType" => {
                let mut elems = Vec::new();
                if t.get("type").truthy() {
                    for x in t.get("type").items() {
                        elems.push(if x.flat_text() == "ℤ" { Elem::Int } else { Elem::Real });
                    }
                } else if t.get("type1").truthy() || t.get("type2").truthy() {
                    let e = if t.get("type1").flat_text() == "ℤ" || t.get("type2").flat_text() == "ℤ" { Elem::Int } else { Elem::Real };
                    let n = match t.get("cnt") {
                        Val::None => 1,
                        c => self.int_literal(c).unwrap_or(1),
                    };
                    elems = vec![e; n.max(1) as usize];
                } else {
                    let sub = if t.get("sub_types").truthy() { t.get("sub_types") } else { t.get("homogeneous_types") };
                    for s in sub.items() {
                        elems.push(self.la_type(s, global)?.elem());
                    }
                }
                Set { elems, length: Dim::None }
            }
            "TupleType" => Tuple(t.get("sub_types").items().iter().map(|s| self.la_type(s, global)).collect::<R<_>>()?),
            "FunctionType" => {
                let params = t.get("params").items().iter().map(|s| self.la_type(s, global)).collect::<R<_>>()?;
                let rets = t.get("ret").items().iter().map(|s| self.la_type(s, global)).collect::<R<_>>()?;
                Func { params, rets }
            }
            "NamedType" => {
                let m = t.get("m");
                if m.truthy() {
                    Mesh(if m.get("e").truthy() {
                        MeshKind::Edge
                    } else if m.get("c").truthy() {
                        MeshKind::Cell
                    } else {
                        MeshKind::Face
                    })
                } else if t.get("s").as_str() == Some("CellularSet") {
                    let set = |e| Set { elems: vec![e], length: Dim::None };
                    Tuple(vec![set(Elem::Vertex), set(Elem::Edge), set(Elem::Face), set(Elem::Tet)])
                } else if let Some(e) = t.get("s").as_str().and_then(set_kind) {
                    Set { elems: vec![e], length: Dim::None }
                } else {
                    let e = if t.get("v").truthy() {
                        Elem::Vertex
                    } else if t.get("e").truthy() {
                        Elem::Edge
                    } else if t.get("f").truthy() {
                        Elem::Face
                    } else {
                        Elem::Tet
                    };
                    Set { elems: vec![e], length: Dim::None }
                }
            }
            other => return self.err(t, format!("Unsupported type {other}")),
        })
    }

    fn int_literal(&self, n: &Val) -> Option<i64> {
        match n.class() {
            "Integer" => n.get("value").flat_text().parse().ok(),
            "SupInteger" => digits(n.get("value"), get_unicode_number),
            "SubInteger" => digits(n.get("value"), get_unicode_sub_number),
            _ => None,
        }
    }

    /// A dimension in a type: an integer, a symbol, or an arithmetic expression.
    fn dim(&mut self, n: &Val) -> R<Dim> {
        match n.class() {
            "ArithExpression" => {
                let v = self.dim(n.get("value"))?;
                if n.get("sign").truthy() {
                    return Ok(arith("-1", '*', &v));
                }
                Ok(v)
            }
            "ArithSubexpression" => self.dim(n.get("value")),
            "ArithAdd" | "ArithSubtract" | "ArithMultiply" | "ArithDivide" => {
                let l = self.dim(n.get("left"))?;
                let r = self.dim(n.get("right"))?;
                let op = match n.class() {
                    "ArithAdd" => '+',
                    "ArithSubtract" => '-',
                    "ArithMultiply" => '*',
                    _ => '/',
                };
                Ok(arith_dims(&l, op, &r))
            }
            "ArithFactor" => {
                if n.get("num").truthy() {
                    return match self.int_literal(n.get("num")) {
                        Some(i) => Ok(Dim::Int(i)),
                        None => self.err(n, "Dimension must be an integer"),
                    };
                }
                if n.get("sub").truthy() {
                    return self.dim(n.get("sub"));
                }
                let id = n.get("id0");
                if id.class() == "IdentifierSubscript" {
                    // a dimension that varies per sequence item: n_i
                    return Ok(Dim::Str(format!("{}[i]", ident_name(id.get("left")))));
                }
                Ok(Dim::Str(ident_name(id)))
            }
            "Integer" | "SupInteger" | "SubInteger" => Ok(Dim::Int(self.int_literal(n).unwrap())),
            _ => self.err(n, "Invalid dimension"),
        }
    }

    // -- statements ----------------------------------------------------------

    fn assignment(&mut self, s: &Val) -> R<Stmt> {
        let lefts = s.get("left").items().to_vec();
        let rights = s.get("right").items().to_vec();
        let accumulate = s.get("op").as_str() == Some("+=");
        let text = self.text(s);
        if lefts.len() > 1 {
            // a, b = f(x), or a, b = v (as in a sum's where)
            let rhs = self.expr(&rights[0])?;
            return self.unpack(s, &lefts, rhs, text);
        }
        let left = &lefts[0];
        let right = &rights[0];
        match left.class() {
            "IdentifierSubscript" => self.elementwise(left, right, accumulate, text),
            _ => {
                let name = ident_name(left);
                let rhs = self.expr(right)?;
                let ty = rhs.ty.clone();
                if accumulate {
                    self.ensure(self.is_defined(&name), left, || format!("{name} hasn't been defined"))?;
                } else {
                    self.define_global(left, &name, ty.clone())?;
                }
                Ok(Stmt::Assign(Assign { lhs: name, subs: vec![], ty, rhs, accumulate, update: false, text, extents: vec![] }))
            }
        }
    }

    fn define_global(&mut self, node: &Val, name: &str, ty: Ty) -> R<()> {
        if let Some(sym) = self.lookup(name) {
            let msg = if matches!(sym, Sym::Param(_)) {
                format!("{name} is a parameter, can not be assigned")
            } else {
                format!("{name} has been assigned before")
            };
            return self.err(node, msg);
        }
        if self.scopes.is_empty() {
            self.globals.insert(name.to_string(), if ty.is_func() { Sym::Func(ty.clone()) } else { Sym::Def(ty.clone()) });
            self.defs.push((name.to_string(), ty));
        } else {
            self.define_local(name, ty);
        }
        Ok(())
    }

    /// `y_i = …` (a sequence or vector) or `A_ij = …` (a matrix), elementwise.
    fn elementwise(&mut self, left: &Val, right: &Val, accumulate: bool, text: String) -> R<Stmt> {
        let name = ident_name(left.get("left"));
        let subs: Vec<String> = left.get("right").items().iter().map(|s| sub_name(s)).collect();
        // an existing matrix: either declared in a where block and defined
        // here (a sparse matrix over an index set), or updated elementwise
        let mut update = false;
        let mut declared: Option<Ty> = None;
        if let Some(sym) = self.lookup(&name) {
            match (&sym, sym.ty()) {
                (Sym::Param(_), t @ Matrix { .. })
                    if subs.len() == 2 && right.class() == "MultiCondExpr" && !self.declared_only.contains(&name) =>
                {
                    self.declared_only.insert(name.clone());
                    self.globals.shift_remove(&name);
                    declared = Some(t);
                }
                (Sym::Def(_), Matrix { .. }) if subs.len() == 2 => update = true,
                (Sym::Def(_), Vector { .. }) | (Sym::Def(_), Seq { .. }) if subs.len() == 1 => update = true,
                _ if accumulate => {}
                (Sym::Param(_), _) => return self.err(left, format!("{name} is a parameter, can not be assigned")),
                _ => return self.err(left, format!("{}_{} has been assigned before", name, subs.concat())),
            }
        }
        for s in &subs {
            if s != "*" && self.is_defined(s) {
                return self.err(left, format!("Subscript {s} has been defined"));
            }
        }
        let mut scope = IndexMap::new();
        let mut frame = IndexMap::new();
        for s in &subs {
            scope.insert(s.clone(), Sym::Local(Ty::int()));
            frame.insert(s.clone(), Vec::new());
        }
        self.scopes.push(scope);
        self.extents.push(frame);
        let rhs = self.expr(right);
        self.scopes.pop();
        let frame = self.extents.pop().unwrap();
        self.note_equal_extents(&frame);
        let rhs = rhs?;
        let mut extents = Vec::new();
        let existing = if update { self.lookup(&name).map(|s| s.ty()) } else { declared.clone() };
        // a row or column at a time (m_i,* = v_i): the * axis is the vector's length
        let star = subs.iter().position(|s| s == "*");
        if let Some(k) = star {
            self.ensure(subs.len() == 2 && subs[1 - k] != "*", left, || "Only one * is allowed as subscripts".into())?;
            self.ensure(rhs.ty.is_vector(), right, || format!("A {} is defined by a vector", if k == 1 { "row" } else { "column" }))?;
        }
        for (k, s) in subs.iter().enumerate() {
            let known = existing.as_ref().and_then(|t| axis_extent(t, k));
            if Some(k) == star {
                extents.push(known.unwrap_or_else(|| rhs.ty.rows()));
                continue;
            }
            match frame[s].first().cloned().or(known) {
                Some(d) => extents.push(d),
                None => return self.err(left, "Subscript hasn't been used on rhs"),
            }
        }
        if update {
            let ty = self.lookup(&name).unwrap().ty();
            return Ok(Stmt::Assign(Assign { lhs: name, subs, ty, rhs, accumulate, update: true, text, extents }));
        }
        if let Some(Matrix { rows, cols, elem, .. }) = declared {
            let ty = Matrix { rows, cols, elem: elem.join(rhs.ty.elem()), sparse: true };
            self.define_global(left, &name, ty.clone())?;
            return Ok(Stmt::Assign(Assign { lhs: name, subs, ty, rhs, accumulate, update: false, text, extents }));
        }
        let ty = match subs.len() {
            1 => {
                if rhs.ty.is_scalar() {
                    Vector { rows: extents[0].clone(), elem: rhs.ty.elem() }
                } else {
                    Seq { size: extents[0].clone(), elem: Box::new(rhs.ty.clone()) }
                }
            }
            2 if star.is_some() => Matrix { rows: extents[0].clone(), cols: extents[1].clone(), elem: rhs.ty.elem(), sparse: false },
            2 => {
                self.ensure(rhs.ty.is_scalar(), right, || "RHS has to be scalar".into())?;
                Matrix {
                    rows: extents[0].clone(),
                    cols: extents[1].clone(),
                    elem: rhs.ty.elem(),
                    sparse: subs[0] == subs[1],
                }
            }
            _ => return self.err(left, "Too many subscripts"),
        };
        if !accumulate {
            self.define_global(left, &name, ty.clone())?;
        }
        Ok(Stmt::Assign(Assign { lhs: name, subs, ty, rhs, accumulate, update: false, text, extents }))
    }

    fn destructure(&mut self, s: &Val) -> R<Stmt> {
        let rhs = self.expr(&s.get("right").items()[0])?;
        let lefts = s.get("left").items().to_vec();
        self.unpack(s, &lefts, rhs, self.text(s))
    }

    /// `a, b = rhs`: one name per item of a tuple, sequence, set or vector.
    fn unpack(&mut self, s: &Val, lefts: &[Val], rhs: Expr, text: String) -> R<Stmt> {
        let tys: Vec<Ty> = match &rhs.ty {
            Tuple(v) => v.clone(),
            Seq { elem, .. } => vec![(**elem).clone(); lefts.len()],
            Vector { elem, .. } => vec![Scalar(*elem); lefts.len()],
            Set { elems, .. } => vec![Scalar(elems.first().copied().unwrap_or_default()); lefts.len()],
            _ => return self.err(s, "Can only unpack tuples, sequences, sets and vectors"),
        };
        self.ensure(tys.len() == lefts.len(), s, || format!("Can only unpack all items: {} lhs and {} items", lefts.len(), tys.len()))?;
        let mut lhs = Vec::new();
        for (l, t) in lefts.iter().zip(tys) {
            let name = ident_name(l);
            self.define_global(l, &name, t.clone())?;
            lhs.push((name, t));
        }
        Ok(Stmt::Multi { lhs, rhs, text })
    }

    fn local_func(&mut self, s: &Val) -> R<LocalFunc> {
        let name = local_func_name(s);
        let mut scope = IndexMap::new();
        let mut defs = IndexMap::new();
        for d in s.get("defs").items() {
            for (n, t) in self.where_condition(d, false)? {
                defs.insert(n, t);
            }
        }
        let mut params = Vec::new();
        let mut pnodes: Vec<Val> = s.get("params").items().to_vec();
        // f_x(...): subscripts are parameters too
        let mut subs: Vec<Val> = if s.get("name").class() == "IdentifierSubscript" {
            s.get("name").get("right").items().to_vec()
        } else {
            s.get("subs").items().to_vec()
        };
        subs.extend(pnodes);
        pnodes = subs;
        for p in &pnodes {
            let pn = ident_name(p);
            match defs.get(&pn) {
                Some(t) => {
                    params.push((pn.clone(), t.clone()));
                    scope.insert(pn, Sym::Local(t.clone()));
                }
                None => return self.err(p, format!("Parameter {pn} hasn't been defined")),
            }
        }
        self.scopes.push(scope);
        let mut body = Vec::new();
        let extras: Vec<Val> = s.get("extra").items().to_vec();
        let order = self.def_use_order(&extras);
        for i in order {
            let st = match extras[i].class() {
                "Destructure" => self.destructure(&extras[i]),
                _ => self.assignment(&extras[i]),
            };
            match st {
                Ok(st) => body.push(st),
                Err(e) => {
                    self.scopes.pop();
                    return Err(e);
                }
            }
        }
        let exprs = s.get("expr").items().to_vec();
        // a recursive function, f(n) = { ... f(m) otherwise }, gets a provisional
        // type, its parameters to the type of its first branch that checks
        let mut names = IndexSet::new();
        exprs.iter().for_each(|e| collect_names(e, &mut names));
        let recursive = names.contains(&name) && !self.globals.contains_key(&name) && exprs.len() == 1;
        if recursive {
            let mut branches = Vec::new();
            piecewise_branches(&exprs[0], &mut branches);
            let ret = branches.iter().find_map(|b| self.expr(b).ok()).map(|x| x.ty);
            match ret {
                Some(t) => {
                    let ty = Func { params: params.iter().map(|(_, t)| t.clone()).collect(), rets: vec![t] };
                    self.globals.insert(name.clone(), Sym::Func(ty));
                }
                None => {
                    self.scopes.pop();
                    return self.err(s, format!("Can't find the return type of the recursive function {name}"));
                }
            }
        }
        let mut rets = Vec::new();
        let mut expr = None;
        for e in &exprs {
            match self.expr(e) {
                Ok(x) => {
                    rets.push(x.ty.clone());
                    expr = Some(x);
                }
                Err(err) => {
                    self.scopes.pop();
                    if recursive {
                        self.globals.shift_remove(&name);
                    }
                    return Err(err);
                }
            }
        }
        self.scopes.pop();
        if recursive {
            self.globals.shift_remove(&name);
        }
        let ty = Func { params: params.iter().map(|(_, t)| t.clone()).collect(), rets };
        let impl_name = self.add_func(&name, ty.clone(), s)?;
        // parameters declared as elements of a set (`v ∈ V`) are checked
        let mut checks = Vec::new();
        for d in s.get("defs").items() {
            let t = d.get("type");
            if t.class() == "MappingType" && t.get("s").truthy() && !d.get("subset").truthy() {
                let set = crate::decls::main_name(t.get("s"));
                for id in d.get("id").items() {
                    checks.push((ident_name(id), set.clone()));
                }
            }
        }
        Ok(LocalFunc { name: impl_name, base: name, checks, params, body, expr: expr.unwrap(), ty, text: self.text(s) })
    }

    // -- expressions ---------------------------------------------------------

    /// Check an expression, recording its type under its source span.
    pub fn expr(&mut self, n: &Val) -> R<Expr> {
        let e = self.expr_kind(n)?;
        if let Some(span) = n.node().and_then(|x| x.span) {
            self.expr_types.insert(span, e.ty.clone());
        }
        Ok(e)
    }

    fn expr_kind(&mut self, n: &Val) -> R<Expr> {
        match n.class() {
            "Expression" | "ExpInMatrix" => {
                let v = self.expr(n.get("value"))?;
                if n.get("sign").truthy() {
                    let ty = v.ty.clone();
                    return Ok(Expr::new(ExprKind::Neg(v), ty));
                }
                Ok(v)
            }
            "Subexpression" => {
                let mut e = self.expr(n.get("value"))?;
                e.paren = true;
                Ok(e)
            }
            "Factor" => self.factor(n),
            "Add" | "Subtract" => self.add_sub(n),
            "Multiply" => self.multiply(n),
            "Divide" => {
                let l = self.expr(n.get("left"))?;
                let r = self.expr(n.get("right"))?;
                self.ensure(r.ty.is_scalar(), n, || self.mismatch("divide", &l, &r, n))?;
                self.ensure(l.ty.is_scalar() || l.ty.is_vector() || l.ty.is_matrix(), n, || self.mismatch("divide", &l, &r, n))?;
                let ty = l.ty.with_elem(l.ty.elem().join(r.ty.elem()));
                let ty = if r.ty.is_int() && l.ty.is_int() { ty.with_elem(Elem::Real) } else { ty };
                Ok(Expr::new(ExprKind::Div(l, r), ty))
            }
            "MultiCondExpr" => self.piecewise(n),
            "Optimize" => self.optimize(n),
            other => self.err(n, format!("Unsupported expression {other}")),
        }
    }

    fn mismatch(&self, op: &str, l: &Expr, r: &Expr, n: &Val) -> String {
        format!(
            "Dimension mismatch. Can't {} {} {} and {} {}",
            op,
            l.ty.desc(),
            self.text(n.get("left")),
            r.ty.desc(),
            self.text(n.get("right"))
        )
    }

    fn add_sub(&mut self, n: &Val) -> R<Expr> {
        let l = self.expr(n.get("left"))?;
        let r = self.expr(n.get("right"))?;
        let add = n.class() == "Add";
        let op = if add { "add" } else { "subtract" };
        let ok = match (&l.ty, &r.ty) {
            (Scalar(_), Scalar(_)) => true,
            (Vector { rows: a, .. }, Vector { rows: b, .. }) => is_same_expr(a, b),
            (Matrix { rows: r1, cols: c1, .. }, Matrix { rows: r2, cols: c2, .. }) => {
                is_same_expr(r1, r2) && is_same_expr(c1, c2)
            }
            (Set { .. }, Set { .. }) => true,
            _ => false,
        };
        self.ensure(ok, n, || self.mismatch(op, &l, &r, n))?;
        if l.ty.is_set() {
            let ty = l.ty.clone();
            let k = if add { SetOpKind::Union } else { SetOpKind::Difference };
            return Ok(Expr::new(ExprKind::SetOp(k, l, r), set_of(&ty)));
        }
        let (li, ri) = (l.ty.elem() == Elem::Index, r.ty.elem() == Elem::Index);
        // an index plus an integer is an index; the difference of two indices is not
        let elem = if (li || ri) && l.ty.is_int() && r.ty.is_int() && !(li && ri && !add) {
            Elem::Index
        } else {
            l.ty.elem().join(r.ty.elem())
        };
        let ty = match &l.ty {
            Matrix { rows, cols, sparse, .. } => {
                Matrix { rows: rows.clone(), cols: cols.clone(), elem, sparse: *sparse && r.ty.is_sparse() }
            }
            t => t.with_elem(elem),
        };
        Ok(Expr::new(if add { ExprKind::Add(l, r) } else { ExprKind::Sub(l, r) }, ty))
    }

    fn multiply(&mut self, n: &Val) -> R<Expr> {
        let l = self.expr(n.get("left"))?;
        let r = self.expr(n.get("right"))?;
        let dot = n.get("op").as_str() == Some("⋅");
        if dot && l.ty.is_vector() && r.ty.is_vector() && is_same_expr(&l.ty.rows(), &r.ty.rows()) {
            let ty = Scalar(l.ty.elem().join(r.ty.elem()));
            return Ok(Expr::new(ExprKind::Dot(l, r), ty));
        }
        let ty = self.product_type(&l, &r, n)?;
        Ok(Expr::new(ExprKind::Mul(l, r), ty))
    }

    fn product_type(&self, l: &Expr, r: &Expr, n: &Val) -> R<Ty> {
        let elem = l.ty.elem().join(r.ty.elem());
        let bad = || self.mismatch("multiply", l, r, n);
        Ok(match (&l.ty, &r.ty) {
            (Scalar(_), t) => {
                self.ensure(t.is_scalar() || t.is_vector() || t.is_matrix(), n, bad)?;
                t.with_elem(elem)
            }
            (t, Scalar(_)) => {
                self.ensure(t.is_vector() || t.is_matrix(), n, bad)?;
                t.with_elem(elem)
            }
            (Matrix { rows, cols, sparse: s1, .. }, Matrix { rows: r2, cols: c2, sparse: s2, .. }) => {
                self.ensure(is_same_expr(cols, r2), n, bad)?;
                if rows.py_eq(&Dim::Int(1)) && c2.py_eq(&Dim::Int(1)) {
                    Scalar(elem)
                } else {
                    Matrix { rows: rows.clone(), cols: c2.clone(), elem, sparse: *s1 && *s2 }
                }
            }
            (Matrix { rows, cols, .. }, Vector { rows: r2, .. }) => {
                self.ensure(is_same_expr(cols, r2), n, bad)?;
                if rows.py_eq(&Dim::Int(1)) {
                    Scalar(elem)
                } else {
                    Vector { rows: rows.clone(), elem }
                }
            }
            (Vector { rows, .. }, Matrix { rows: r2, cols: c2, .. }) => {
                self.ensure(r2.py_eq(&Dim::Int(1)), n, bad)?;
                Matrix { rows: rows.clone(), cols: c2.clone(), elem, sparse: false }
            }
            _ => return self.err(n, bad()),
        })
    }

    fn factor(&mut self, n: &Val) -> R<Expr> {
        let child = ["id0", "num", "sub", "m", "v", "s", "nm", "op", "c"]
            .iter()
            .find_map(|k| {
                let v = n.get(k);
                v.truthy().then(|| (*k, v.clone()))
            });
        let Some((kind, v)) = child else { return self.err(n, "Empty factor") };
        match kind {
            "id0" => self.identifier(&v),
            "num" => self.number(&v),
            "sub" => {
                let mut e = self.expr(v.get("value"))?;
                e.paren = true;
                Ok(e)
            }
            "m" => self.block_matrix(&v),
            "v" => self.vector_literal(&v),
            "s" => self.set_literal(&v),
            "nm" => self.num_matrix(&v),
            "c" => self.constant(&v),
            _ => self.operation(&v),
        }
    }

    fn constant(&mut self, v: &Val) -> R<Expr> {
        let c = match v.class() {
            "Pi" => Constant::Pi,
            "E" => Constant::E,
            _ => Constant::Inf,
        };
        Ok(Expr::new(ExprKind::Const(c), Ty::real()))
    }

    fn number(&mut self, v: &Val) -> R<Expr> {
        match v.class() {
            "Integer" | "SupInteger" | "SubInteger" => Ok(Expr::new(ExprKind::Int(self.int_literal(v).unwrap()), Ty::int())),
            "Double" => Ok(Expr::new(ExprKind::Real(self.text(v)), Ty::real())),
            "Fraction" => {
                let c = v.get("value").flat_text().chars().next().unwrap();
                let (a, b) = get_unicode_fraction(c).unwrap();
                Ok(Expr::new(ExprKind::Fraction(a, b), Ty::real()))
            }
            _ => self.err(v, "Unsupported number"),
        }
    }

    /// A name, or a subscripted name (indexing, or a dimension-less identity).
    fn identifier(&mut self, id: &Val) -> R<Expr> {
        if id.class() == "IdentifierSubscript" {
            return self.subscripted(id);
        }
        let name = ident_name(id);
        if name == "e" && self.const_e && !self.is_defined("e") {
            return Ok(Expr::new(ExprKind::Const(Constant::E), Ty::real()));
        }
        match self.lookup(&name) {
            Some(sym) => Ok(Expr::new(ExprKind::Var(name), sym.ty())),
            None => self.err(id, format!("Symbol {name} is not defined")),
        }
    }

    fn subscripted(&mut self, id: &Val) -> R<Expr> {
        let base = ident_name(id.get("left"));
        let idx_nodes: Vec<Val> = if id.get("exp").truthy() {
            id.get("exp").items().to_vec()
        } else {
            id.get("right").items().to_vec()
        };
        if base == "I" && !self.is_defined("I") {
            // I_n: identity matrix
            let d = self.index_dim(&idx_nodes[0])?;
            return Ok(Expr::new(ExprKind::Identity(d.clone()), Ty::matrix(d.clone(), d)));
        }
        let Some(sym) = self.lookup(&base) else {
            return self.err(id, format!("Symbol {base} is not defined"));
        };
        let bty = sym.ty();
        if let Some(span) = id.node().and_then(|x| x.span) {
            self.base_types.insert(span, bty.clone());
        }
        let mut idx = Vec::new();
        for (axis, node) in idx_nodes.iter().enumerate() {
            if node.as_str() == Some("*") {
                idx.push(Idx::All);
                continue;
            }
            let e = self.index_expr(node)?;
            // infer the extent of a subscript variable from this axis
            if let ExprKind::Var(v) = &*e.kind {
                let mut extent = axis_extent(&bty, axis);
                if let (VecSet { .. }, 0) = (&bty, axis) {
                    extent = Some(Dim::Str(format!("@size:{base}")));
                }
                // a ragged sequence (x_i ∈ ℝ^(n_i)): the extent depends on the item
                if let (Some(Dim::Str(s)), Some(Idx::At(first))) = (&extent, idx.first()) {
                    if s.ends_with("[i]") && axis >= 1 {
                        let item = match &*first.kind {
                            ExprKind::Var(n) => n.clone(),
                            ExprKind::Int(i) => i.to_string(),
                            _ => "1".into(),
                        };
                        extent = Some(Dim::Str(format!("@len:{base}:{item}:{}", axis - 1)));
                    }
                }
                for frame in self.extents.iter_mut().rev() {
                    if let Some(seen) = frame.get_mut(v) {
                        if let Some(d) = extent.clone() {
                            seen.push(d);
                        }
                        break;
                    }
                }
            }
            idx.push(Idx::At(e));
        }
        for (axis, i) in idx.iter().enumerate() {
            if let (Idx::At(e), Some(Dim::Str(d))) = (i, axis_extent(&bty, axis)) {
                if let ExprKind::Int(k) = &*e.kind {
                    let m = self.min_dims.entry(d).or_insert(*k);
                    *m = (*m).max(*k);
                }
            }
        }
        let ty = self.index_type(&bty, &idx, id)?;
        Ok(Expr::new(ExprKind::Index { base, base_ty: bty, idx }, ty))
    }

    fn index_expr(&mut self, node: &Val) -> R<Expr> {
        match node.class() {
            "IdentifierAlone" => {
                let name = ident_name(node);
                match self.lookup(&name) {
                    Some(s) => Ok(Expr::new(ExprKind::Var(name), s.ty())),
                    None => self.err(node, format!("Subscript {name} has not been defined")),
                }
            }
            "Integer" | "SubInteger" => Ok(Expr::new(ExprKind::Int(self.int_literal(node).unwrap()), Ty::int())),
            _ => self.expr(node),
        }
    }

    fn index_dim(&mut self, node: &Val) -> R<Dim> {
        match node.class() {
            "IdentifierAlone" => Ok(Dim::Str(ident_name(node))),
            _ => match self.int_literal(node) {
                Some(i) => Ok(Dim::Int(i)),
                None => self.err(node, "Invalid identity matrix"),
            },
        }
    }

    fn index_type(&self, bty: &Ty, idx: &[Idx], node: &Val) -> R<Ty> {
        let all = |i: usize| matches!(idx.get(i), Some(Idx::All));
        Ok(match (bty, idx.len()) {
            (Vector { elem, .. }, 1) => Scalar(*elem),
            (Matrix { elem, .. }, 2) => match (all(0), all(1)) {
                (false, false) => Scalar(*elem),
                (true, false) => Vector { rows: bty.rows(), elem: *elem },
                (false, true) => Vector { rows: bty.cols(), elem: *elem },
                _ => return self.err(node, "Only one * is allowed as subscripts"),
            },
            (Seq { elem, .. }, 1) => (**elem).clone(),
            (Seq { elem, .. }, 2) if elem.is_vector() => Scalar(elem.elem()),
            (Seq { elem, .. }, 3) if elem.is_matrix() => match (all(1), all(2)) {
                (false, false) => Scalar(elem.elem()),
                (true, false) => Vector { rows: elem.rows(), elem: elem.elem() },
                (false, true) => Ty::matrix(1, elem.cols()),
                _ => return self.err(node, "Only one * is allowed as subscripts"),
            },
            (Set { elems, .. }, 1) => Scalar(elems.first().copied().unwrap_or_default()),
            (VecSet { rows, elem }, 1) => Vector { rows: rows.clone(), elem: *elem },
            (Tuple(v), 1) => match &idx[0] {
                Idx::At(e) => match &*e.kind {
                    ExprKind::Int(i) if *i >= 1 && (*i as usize) <= v.len() => v[*i as usize - 1].clone(),
                    _ => return self.err(node, "Subscript has to be int value when indexing tuple"),
                },
                Idx::All => return self.err(node, "Subscript can't be *"),
            },
            (Func { .. }, _) => return self.err(node, "Invalid assignment for function"),
            _ => return self.err(node, format!("Invalid subscripts for {}", bty.desc())),
        })
    }

    fn vector_literal(&mut self, v: &Val) -> R<Expr> {
        let mut items = Vec::new();
        let mut rows = Dim::Int(0);
        let mut elem = Elem::Int;
        for e in v.get("exp").items() {
            let x = self.expr(e)?;
            self.ensure(x.ty.is_scalar() || x.ty.is_vector(), v, || "Item in vector must be scalar or vector".into())?;
            rows = add_dims(&rows, &x.ty.rows());
            elem = elem.join(x.ty.elem());
            items.push(x);
        }
        Ok(Expr::new(ExprKind::Stack(items), Vector { rows, elem }))
    }

    fn set_literal(&mut self, v: &Val) -> R<Expr> {
        if v.get("enum").truthy() {
            return self.set_comprehension(v);
        }
        let items: Vec<Expr> = v.get("exp").items().iter().map(|e| self.expr(e)).collect::<R<_>>()?;
        let elems = vec![items.first().map(|x| x.ty.elem()).unwrap_or_default()];
        Ok(Expr::new(ExprKind::SetLit(items), Set { elems, length: Dim::None }))
    }

    /// `∪_(i ∈ S) e`: as in the Python compiler, a variable ranging over
    /// `index` values is the 1-based index (the element plus 1).
    fn union(&mut self, op: &Val) -> R<Expr> {
        if !op.get("enum").truthy() {
            return self.union_indexed(op);
        }
        let range = self.set_expr(op.get("range"))?;
        let elems = match &range.ty {
            Set { elems, .. } => elems.clone(),
            _ => return self.err(op, "The range of a union must be a set"),
        };
        let vars: Vec<String> = op.get("enum").items().iter().map(ident_name).collect();
        self.ensure(vars.len() == elems.len(), op, || "Union: the variables don't match the set's elements".into())?;
        let mut scope = IndexMap::new();
        let mut one_based = Vec::new();
        for (v, e) in vars.iter().zip(&elems) {
            let plus1 = *e == Elem::Index;
            scope.insert(v.clone(), Sym::Local(Scalar(if plus1 { Elem::Int } else { *e })));
            one_based.push(plus1);
        }
        self.scopes.push(scope);
        let body = self.expr(op.get("exp"));
        self.scopes.pop();
        let body = body?;
        self.ensure(body.ty.is_set(), op, || "A union's terms must be sets".into())?;
        let ty = set_of(&body.ty);
        Ok(Expr::new(ExprKind::Union { vars, range: SumRange::Set(range), body, one_based }, ty))
    }

    /// `∪_i U_i` (over the extent of what i subscripts) or `∪_(i=a)^b U_i`.
    /// Bounds that are `index` values (0-based) are shifted to the 1-based
    /// subscripts used everywhere else.
    fn union_indexed(&mut self, op: &Val) -> R<Expr> {
        let id = if op.get("id").truthy() { op.get("id") } else { op.get("sub") };
        let v = ident_name(id);
        if self.is_defined(&v) {
            return self.err(id, "Subscript has been defined");
        }
        let mut bounds = None;
        if op.get("lower").truthy() {
            let mut b = Vec::new();
            for n in [op.get("lower"), op.get("upper")] {
                // (the upper bound is a factor: a number, a name or an expression)
                let e = match self.int_literal(n) {
                    Some(i) => Expr::new(ExprKind::Int(i), Ty::int()),
                    None if n.class() == "IdentifierAlone" => self.identifier(n)?,
                    None => self.expr(n)?,
                };
                self.ensure(e.ty.is_scalar() && e.ty.is_int(), n, || "The bounds of a union must be integers".into())?;
                b.push(if matches!(e.ty, Scalar(Elem::Index)) {
                    Expr::new(ExprKind::Add(e, Expr::new(ExprKind::Int(1), Ty::int())), Ty::int())
                } else {
                    e
                });
            }
            bounds = Some((b.remove(0), b.remove(0)));
        } else if op.get("cond").truthy() {
            return self.err(op, "Unions with a condition aren't supported");
        }
        self.scopes.push(IndexMap::from([(v.clone(), Sym::Local(Ty::int()))]));
        self.extents.push(IndexMap::from([(v.clone(), Vec::new())]));
        let body = self.expr(op.get("exp"));
        self.scopes.pop();
        let frame = self.extents.pop().unwrap();
        self.note_equal_extents(&frame);
        let body = body?;
        self.ensure(body.ty.is_set(), op, || "A union's terms must be sets".into())?;
        let range = match bounds {
            Some((lo, hi)) => SumRange::Explicit(lo, hi),
            None => match frame[&v].first() {
                Some(d) => SumRange::Implicit(d.clone()),
                None => return self.err(op, "Subscript hasn't been used in union"),
            },
        };
        let ty = set_of(&body.ty);
        Ok(Expr::new(ExprKind::Union { vars: vec![v], range, body, one_based: vec![false] }, ty))
    }

    /// A set: an expression, or a bare name or call (as in `x ∈ S`, `x ∈ f(y)`).
    fn set_expr(&mut self, n: &Val) -> R<Expr> {
        match n.class() {
            "IdentifierAlone" | "IdentifierSubscript" => self.identifier(n),
            "Function" => self.call(n),
            _ => self.expr(n),
        }
    }

    /// `{ e for x ∈ S if cond }`
    fn set_comprehension(&mut self, v: &Val) -> R<Expr> {
        let range = self.set_expr(v.get("range"))?;
        let elems = match &range.ty {
            Set { elems, .. } => elems.clone(),
            _ => return self.err(v.get("range"), "The range of a set comprehension must be a set"),
        };
        let vars: Vec<String> = v.get("enum").items().iter().map(ident_name).collect();
        let mut scope = IndexMap::new();
        if vars.len() == elems.len() {
            for (x, e) in vars.iter().zip(&elems) {
                scope.insert(x.clone(), Sym::Local(Scalar(*e)));
            }
        } else if vars.len() == 1 {
            scope.insert(vars[0].clone(), Sym::Local(Tuple(elems.iter().map(|e| Scalar(*e)).collect())));
        } else {
            return self.err(v, "Set comprehension: the variables don't match the set's elements");
        }
        self.scopes.push(scope);
        let result = (|| -> R<(Option<Cond>, Expr)> {
            let cond = if v.get("cond").truthy() { Some(self.condition(v.get("cond"))?) } else { None };
            let items = v.get("exp").items().to_vec();
            let item = self.expr(&items[0])?;
            Ok((cond, item))
        })();
        self.scopes.pop();
        let (cond, item) = result?;
        if let Vector { rows, elem } = &item.ty {
            let ty = VecSet { rows: rows.clone(), elem: *elem };
            return Ok(Expr::new(ExprKind::SetComp { vars, range, cond, item }, ty));
        }
        self.ensure(item.ty.is_scalar() || item.ty.is_tuple(), &v.get("exp").items()[0], || {
            format!("A set's items are numbers, tuples or vectors, not {}", item.ty.desc())
        })?;
        let out = match &item.ty {
            Tuple(ts) => ts.iter().map(|t| t.elem()).collect(),
            t => vec![t.elem()],
        };
        Ok(Expr::new(ExprKind::SetComp { vars, range, cond, item }, Set { elems: out, length: Dim::None }))
    }

    fn num_matrix(&mut self, v: &Val) -> R<Expr> {
        let value = if v.get("left").flat_text() == "0" { 0 } else { 1 };
        let rows = self.index_dim(v.get("id1"))?;
        let cols = if v.get("id2").truthy() { Some(self.index_dim(v.get("id2"))?) } else { None };
        let ty = match &cols {
            Some(c) => Matrix { rows: rows.clone(), cols: c.clone(), elem: Elem::Int, sparse: false },
            None => Vector { rows: rows.clone(), elem: Elem::Int },
        };
        Ok(Expr::new(ExprKind::Filled { value, rows, cols }, ty))
    }

    /// `[a b; c d]`, with blocks.
    fn block_matrix(&mut self, m: &Val) -> R<Expr> {
        let mut rows: Vec<Vec<Val>> = Vec::new();
        flatten_rows(m.get("value"), &mut rows);
        let mut items: Vec<Vec<Expr>> = Vec::new();
        for r in &rows {
            let mut row = Vec::new();
            for e in r {
                row.push(self.matrix_item(e)?);
            }
            items.push(row);
        }
        let n_rows = items.len();
        let n_cols = items.iter().map(|r| r.len()).max().unwrap_or(0);
        let is_block = items.iter().flatten().any(|e| !e.ty.is_scalar() || is_lifted(e));
        let elem = items.iter().flatten().fold(Elem::Int, |acc, e| acc.join(e.ty.elem()));
        if !is_block {
            return Ok(Expr::new(ExprKind::Block(items), Matrix { rows: Dim::Int(n_rows as i64), cols: Dim::Int(n_cols as i64), elem, sparse: false }));
        }
        // block dimensions: height of each block row, width of each block column
        let mut heights: Vec<Option<Dim>> = vec![None; n_rows];
        let mut widths: Vec<Option<Dim>> = vec![None; n_cols];
        for (i, row) in items.iter().enumerate() {
            for (j, e) in row.iter().enumerate() {
                // 0, 1 and I take the size of their block; other scalars are 1×1
                let adapts = matches!(&*e.kind, ExprKind::Int(0) | ExprKind::Int(1)) || matches!(&*e.kind, ExprKind::Var(n) if n == "I");
                if e.ty.is_scalar() && (adapts || is_lifted(e)) {
                    continue;
                }
                let (h, w) = (e.ty.rows(), e.ty.cols());
                match &heights[i] {
                    None => heights[i] = Some(h),
                    Some(x) if !is_same_expr(x, &h) => return self.err(m, "Block matrix error. Invalid dimensions"),
                    _ => {}
                }
                match &widths[j] {
                    None => widths[j] = Some(w),
                    Some(x) if !is_same_expr(x, &w) => return self.err(m, "Block matrix error. Invalid dimensions"),
                    _ => {}
                }
            }
        }
        // I is square: it sizes a block row or column that nothing else does
        for (i, row) in items.iter().enumerate() {
            for (j, e) in row.iter().enumerate() {
                if matches!(&*e.kind, ExprKind::Var(n) if n == "I") && e.ty.is_scalar() {
                    match (&heights[i], &widths[j]) {
                        (Some(h), None) => widths[j] = Some(h.clone()),
                        (None, Some(w)) => heights[i] = Some(w.clone()),
                        (None, None) => return self.err(m, "Block matrix error. Can't infer the size of I; write I_n"),
                        _ => {}
                    }
                }
            }
        }
        let heights: Vec<Dim> = heights.into_iter().map(|h| h.unwrap_or(Dim::Int(1))).collect();
        let widths: Vec<Dim> = widths.into_iter().map(|w| w.unwrap_or(Dim::Int(1))).collect();
        // give scalar 0/1 items and I the size of their block
        for (i, row) in items.iter_mut().enumerate() {
            for (j, e) in row.iter_mut().enumerate() {
                if e.ty.is_scalar() {
                    let (h, w) = (heights[i].clone(), widths[j].clone());
                    if let ExprKind::Var(name) = &*e.kind {
                        if name == "I" {
                            *e = Expr::new(ExprKind::Identity(h.clone()), Ty::matrix(h, w));
                            continue;
                        }
                    }
                    if !(h.py_eq(&Dim::Int(1)) && w.py_eq(&Dim::Int(1))) {
                        let v = match &*e.kind {
                            ExprKind::Int(v) if *v == 0 || *v == 1 => *v,
                            _ => return self.err(m, "Block matrix error. Invalid dimensions"),
                        };
                        *e = Expr::new(ExprKind::Filled { value: v, rows: h.clone(), cols: Some(w.clone()) }, Ty::matrix(h, w));
                    }
                }
            }
        }
        let total_rows = heights.iter().fold(Dim::Int(0), |a, b| add_dims(&a, b));
        let total_cols = widths.iter().fold(Dim::Int(0), |a, b| add_dims(&a, b));
        let sparse = items.iter().flatten().any(|e| e.ty.is_sparse());
        Ok(Expr::new(ExprKind::Block(items), Matrix { rows: total_rows, cols: total_cols, elem, sparse }))
    }

    fn matrix_item(&mut self, e: &Val) -> R<Expr> {
        // an undefined I inside a block matrix is an identity block
        if e.class() == "ExpInMatrix" && !e.get("sign").truthy() {
            let f = e.get("value");
            if f.class() == "Factor" && f.get("id0").class() == "IdentifierAlone" && ident_name(f.get("id0")) == "I" && !self.is_defined("I") {
                return Ok(Expr::new(ExprKind::Var("I".into()), Ty::int()));
            }
        }
        self.expr(e)
    }

    fn piecewise(&mut self, n: &Val) -> R<Expr> {
        let mut singles = Vec::new();
        flatten_ifs(n.get("ifs"), &mut singles);
        let mut cases = Vec::new();
        let mut ty: Option<Ty> = None;
        for s in &singles {
            let c = self.condition(s.get("cond"))?;
            let e = self.expr(s.get("stat"))?;
            ty = Some(match ty {
                None => e.ty.clone(),
                Some(t) => t.with_elem(t.elem().join(e.ty.elem())),
            });
            cases.push((c, e));
        }
        let otherwise = if n.get("other").truthy() { Some(self.expr(n.get("other"))?) } else { None };
        let mut ty = ty.unwrap();
        if let Some(o) = &otherwise {
            ty = ty.with_elem(ty.elem().join(o.ty.elem()));
        }
        Ok(Expr::new(ExprKind::Piecewise { cases, otherwise }, ty))
    }

    fn condition(&mut self, c: &Val) -> R<Cond> {
        match c.class() {
            "IfCondition" => {
                if c.get("single").truthy() {
                    return self.condition(c.get("single"));
                }
                Ok(Cond::Or(Box::new(self.condition(c.get("se"))?), Box::new(self.condition(c.get("other"))?)))
            }
            "AndCondition" => {
                if c.get("atom").truthy() {
                    return self.condition(c.get("atom"));
                }
                Ok(Cond::And(Box::new(self.condition(c.get("se"))?), Box::new(self.condition(c.get("other"))?)))
            }
            "AtomCondition" => {
                if c.get("p").truthy() {
                    self.condition(c.get("p"))
                } else {
                    self.condition(c.get("cond"))
                }
            }
            "InCondition" | "NotInCondition" => {
                let items: Vec<Expr> = c.get("left").items().iter().map(|e| self.expr(e)).collect::<R<_>>()?;
                let r = c.get("right");
                let set = match r.class() {
                    "IdentifierAlone" | "IdentifierSubscript" => self.identifier(r)?,
                    "Function" => self.call(r)?,
                    _ => self.expr(r)?,
                };
                Ok(if c.class() == "InCondition" { Cond::In(items, set) } else { Cond::NotIn(items, set) })
            }
            cls => {
                let op = match cls {
                    "EqCondition" => CmpOp::Eq,
                    "NeCondition" => CmpOp::Ne,
                    "LessCondition" => CmpOp::Lt,
                    "LessEqualCondition" => CmpOp::Le,
                    "GreaterCondition" => CmpOp::Gt,
                    "GreaterEqualCondition" => CmpOp::Ge,
                    other => return self.err(c, format!("Unsupported condition {other}")),
                };
                let l = self.expr(c.get("left"))?;
                let r = self.expr(c.get("right"))?;
                Ok(Cond::Cmp(op, l, r))
            }
        }
    }

    fn optimize(&mut self, n: &Val) -> R<Expr> {
        let kind = if n.get("min").truthy() {
            OptKind::Min
        } else if n.get("max").truthy() {
            OptKind::Max
        } else if n.get("amin").truthy() {
            OptKind::Argmin
        } else {
            OptKind::Argmax
        };
        let mut scope = IndexMap::new();
        let mut vars = Vec::new();
        for d in n.get("defs").items() {
            for (name, t) in self.where_condition(d, false)? {
                scope.insert(name.clone(), Sym::Local(t.clone()));
                self.opt_vars.entry(name.clone()).or_insert_with(|| t.clone());
                vars.push((name, t));
            }
        }
        self.scopes.push(scope);
        let objective = self.expr(n.get("exp"));
        let mut constraints = Vec::new();
        let mut cur = n.get("cond").clone();
        let mut conds = Vec::new();
        while cur.truthy() {
            conds.push(cur.get("cond").clone());
            cur = cur.get("m_cond").clone();
        }
        conds.reverse();
        let texts: Vec<String> = conds.iter().map(|c| self.text(c).trim().to_string()).collect();
        let mut failed = None;
        for c in &conds {
            match self.condition(c) {
                Ok(c) => constraints.push(c),
                Err(e) => failed = Some(e),
            }
        }
        self.scopes.pop();
        let objective = objective?;
        if let Some(e) = failed {
            return Err(e);
        }
        self.ensure(objective.ty.is_scalar(), n, || "Objective function must return a scalar".into())?;
        let ty = match kind {
            OptKind::Min | OptKind::Max => Ty::real(),
            _ if vars.len() == 1 => vars[0].1.clone(),
            _ => Tuple(vars.iter().map(|(_, t)| t.clone()).collect()),
        };
        Ok(Expr::new(ExprKind::Optimize { kind, vars, objective, constraints, texts }, ty))
    }

    /// Operators and function calls (`Factor.op`).
    fn operation(&mut self, op: &Val) -> R<Expr> {
        match op.class() {
            "Power" => self.power(op),
            "Transpose" => {
                let f = self.expr(op.get("f"))?;
                let ty = transpose_type(&f.ty).ok_or(()).or_else(|_| self.err(op, "Transpose error. The base must be a matrix or vector"))?;
                Ok(Expr::new(ExprKind::Transpose(f), ty))
            }
            "PseudoInverse" => {
                let f = self.expr(op.get("f"))?;
                let ty = transpose_type(&f.ty).ok_or(()).or_else(|_| self.err(op, "Pseudoinverse error. The base must be a matrix or vector"))?;
                Ok(Expr::new(ExprKind::PseudoInverse(f), ty))
            }
            "Squareroot" => {
                let f = self.expr(op.get("f"))?;
                self.ensure(f.ty.is_scalar(), op, || "Squareroot error. The base must be a scalar".into())?;
                Ok(Expr::new(ExprKind::Sqrt(f), Ty::real()))
            }
            "Solver" => self.solver(op),
            "Norm" => self.norm(op),
            "Summation" => self.summation(op),
            "Function" => self.call(op),
            "Integral" => self.integral(op),
            "InnerProduct" => {
                let l = self.expr(op.get("left"))?;
                let r = self.expr(op.get("right"))?;
                self.ensure(l.ty.is_vector() && r.ty.is_vector(), op, || "Inner product error. Parameters must be vectors".into())?;
                let sub = if op.get("sub").truthy() { Some(self.identifier(op.get("sub"))?) } else { None };
                Ok(Expr::new(ExprKind::Inner(l, r, sub), Ty::real()))
            }
            "FroProduct" | "HadamardProduct" | "CrossProduct" | "KroneckerProduct" => self.product(op),
            "Intersection" | "Union" => {
                let l = self.expr(op.get("left"))?;
                let r = self.expr(op.get("right"))?;
                self.ensure(l.ty.is_set() && r.ty.is_set(), op, || "Set operations need sets".into())?;
                let k = if op.class() == "Union" { SetOpKind::Union } else { SetOpKind::Intersection };
                let ty = set_of(&l.ty);
                Ok(Expr::new(ExprKind::SetOp(k, l, r), ty))
            }
            "ElementConvertFunc" => self.element_convert(op),
            "SizeOp" => {
                let x = self.identifier(op.get("i"))?;
                Ok(Expr::new(ExprKind::Size(x), Ty::int()))
            }
            cls if cls.ends_with("Func") => self.builtin(op),
            "Partial" => self.partial(op),
            other => self.err(op, format!("Unsupported operation {other}")),
        }
    }

    fn power(&mut self, op: &Val) -> R<Expr> {
        let base = self.expr(op.get("base"))?;
        let power_text = op.get("power").node().and_then(|_| Some(self.text(op.get("power"))));
        if op.get("t").truthy() || power_text.as_deref() == Some("ᵀ") {
            if !self.is_defined("T") {
                let ty = transpose_type(&base.ty).ok_or(()).or_else(|_| self.err(op, "Transpose error. The base must be a matrix or vecotr"))?;
                return Ok(Expr::new(ExprKind::Transpose(base), ty));
            }
        }
        if op.get("r").truthy() {
            return match &base.ty {
                Matrix { rows, cols, .. } => {
                    self.ensure(is_same_expr(rows, cols), op, || "Inverse matrix error. The rows should be the same as the columns".into())?;
                    let ty = Ty::matrix(rows.clone(), rows.clone());
                    Ok(Expr::new(ExprKind::Inverse(base), ty))
                }
                Scalar(_) => Ok(Expr::new(ExprKind::Inverse(base), Ty::real())),
                _ => self.err(op, "Inverse error. The base must be a matrix or scalar"),
            };
        }
        let power = if op.get("t").truthy() || power_text.as_deref() == Some("ᵀ") {
            Expr::new(ExprKind::Var("T".into()), self.lookup("T").unwrap().ty())
        } else {
            let p = op.get("power");
            match p.class() {
                "SupInteger" => Expr::new(ExprKind::Int(self.int_literal(p).unwrap()), Ty::int()),
                "IdentifierAlone" => {
                    // a superscript letter: x^a
                    let name = crate::helper::get_unicode_superscript(&p.get("value").flat_text());
                    match self.lookup(&name) {
                        Some(s) => Expr::new(ExprKind::Var(name), s.ty()),
                        None => return self.err(p, format!("Symbol {name} is not defined")),
                    }
                }
                _ => self.expr(p)?,
            }
        };
        self.ensure(power.ty.is_scalar(), op, || "Power must be scalar".into())?;
        let ty = match &base.ty {
            Scalar(e) => {
                if e.is_int() && power.ty.is_int() && matches!(&*power.kind, ExprKind::Int(v) if *v >= 0) {
                    Ty::int()
                } else {
                    Ty::real()
                }
            }
            Matrix { rows, cols, .. } => {
                self.ensure(is_same_expr(rows, cols), op, || "Power error. Rows must be the same as columns".into())?;
                base.ty.clone()
            }
            _ => return self.err(op, "Base of power must be scalar or matrix"),
        };
        Ok(Expr::new(ExprKind::Pow(base, power), ty))
    }

    fn solver(&mut self, op: &Val) -> R<Expr> {
        let l = self.expr(op.get("left"))?;
        let r = self.expr(op.get("right"))?;
        if l.ty.is_scalar() {
            // a⁻¹ b with a scalar
            let inv = Expr::new(ExprKind::Inverse(l), Ty::real());
            let ty = self.product_type(&inv, &r, op)?;
            return Ok(Expr::new(ExprKind::Mul(inv, r), ty));
        }
        if l.ty.is_set() {
            // A \ B: set difference
            let ty = set_of(&l.ty);
            return Ok(Expr::new(ExprKind::SetOp(SetOpKind::Difference, l, r), ty));
        }
        self.ensure(l.ty.is_matrix(), op, || format!("Parameter {} must be a matrix", self.text(op.get("left"))))?;
        self.ensure(is_same_expr(&l.ty.rows(), &r.ty.rows()), op, || {
            format!("Parameters {} and {} should have the same rows", self.text(op.get("left")), self.text(op.get("right")))
        })?;
        let ty = match &r.ty {
            // sparse when both are (spsolve returns a sparse result), as in Python
            Matrix { cols, sparse, .. } => {
                Matrix { rows: l.ty.cols(), cols: cols.clone(), elem: Elem::Real, sparse: *sparse && l.ty.is_sparse() }
            }
            Vector { .. } => Ty::vector(l.ty.cols()),
            _ => return self.err(op, format!("Parameter {} must be a matrix or vector", self.text(op.get("right")))),
        };
        Ok(Expr::new(ExprKind::Solve(l, r), ty))
    }

    fn norm(&mut self, op: &Val) -> R<Expr> {
        let arg = self.expr(op.get("value"))?;
        let single = op.get("single").truthy();
        let sub = op.get("sub");
        let (kind, p) = match &arg.ty {
            Scalar(_) => {
                self.ensure(single, op, || "Norm error. Scalar type has to use | rather than ||".into())?;
                (NormKind::Abs, None)
            }
            Set { .. } => (NormKind::Size, None),
            Matrix { .. } if single => (NormKind::Det, None),
            Matrix { .. } => match sub.as_str() {
                Some("*") => (NormKind::Nuclear, None),
                _ if sub.is_none() || self.text(sub) == "F" => (NormKind::Frobenius, None),
                _ => return self.err(op, "Norm error. Invalid norm for Matrix"),
            },
            Vector { .. } => {
                self.ensure(!single, op, || "Norm error. Vector type has to use || rather than |".into())?;
                match sub {
                    Val::None => (NormKind::P, None),
                    Val::Str(s) if &**s == "∞" => (NormKind::Max, None),
                    Val::Str(s) if &**s == "*" => return self.err(op, "Norm error. Invalid norm for Vector"),
                    s => {
                        let e = if s.class() == "IdentifierAlone" && ident_name(s) == "∞" {
                            return Ok(Expr::new(ExprKind::Norm { arg, kind: NormKind::Max, p: None }, Ty::real()));
                        } else if let Some(i) = self.int_literal(s) {
                            Expr::new(ExprKind::Int(i), Ty::int())
                        } else {
                            self.identifier(s)?
                        };
                        (NormKind::P, Some(e))
                    }
                }
            }
            _ => return self.err(op, "Norm error. Invalid type"),
        };
        let ty = if kind == NormKind::Size { Ty::int() } else { Ty::real() };
        let mut e = Expr::new(ExprKind::Norm { arg, kind, p }, ty);
        let power = op.get("power");
        if power.truthy() {
            let pw = match self.int_literal(power) {
                Some(i) => Expr::new(ExprKind::Int(i), Ty::int()),
                None => self.expr(power)?,
            };
            e = Expr::new(ExprKind::Pow(e, pw), Ty::real());
        }
        Ok(e)
    }

    fn summation(&mut self, op: &Val) -> R<Expr> {
        if op.get("u").truthy() {
            return self.union(op);
        }
        let mut scope = IndexMap::new();
        let vars: Vec<String>;
        let mut range_kind = 0; // 0 implicit, 1 explicit, 2 cond, 3 set
        let mut lo = None;
        let mut hi = None;
        let mut set_expr = None;
        if op.get("enum").truthy() {
            let set = self.set_expr(op.get("range"))?;
            let elems = match &set.ty {
                Set { elems, .. } => elems.clone(),
                _ => return self.err(op, "Range of a summation must be a set"),
            };
            vars = op.get("enum").items().iter().map(ident_name).collect();
            if vars.len() == elems.len() {
                for (v, e) in vars.iter().zip(&elems) {
                    scope.insert(v.clone(), Sym::Local(Scalar(*e)));
                }
            } else {
                self.ensure(vars.len() == 1, op, || "Invalid size".into())?;
                let t = if elems.len() == 1 { Scalar(elems[0]) } else { Tuple(elems.iter().map(|e| Scalar(*e)).collect()) };
                scope.insert(vars[0].clone(), Sym::Local(t));
            }
            set_expr = Some(set);
            range_kind = 3;
        } else {
            let id = if op.get("id").truthy() { op.get("id") } else { op.get("sub") };
            let v = ident_name(id);
            if self.is_defined(&v) {
                return self.err(id, "Subscript has been defined");
            }
            vars = vec![v.clone()];
            scope.insert(v, Sym::Local(Ty::int()));
            if op.get("lower").truthy() {
                lo = Some(self.expr(op.get("lower"))?);
                let u = op.get("upper");
                hi = Some(match self.int_literal(u) {
                    Some(i) => Expr::new(ExprKind::Int(i), Ty::int()),
                    None if u.class() == "IdentifierAlone" => self.identifier(u)?,
                    None => self.expr(u)?,
                });
                range_kind = 1;
            } else if op.get("cond").truthy() {
                range_kind = 2;
            }
        }
        let mut frame = IndexMap::new();
        for v in &vars {
            frame.insert(v.clone(), Vec::new());
        }
        self.scopes.push(scope);
        self.extents.push(frame);
        let result = (|| -> R<(Vec<Stmt>, Option<Cond>, Expr)> {
            let mut extras = Vec::new();
            let ex: Vec<Val> = op.get("extra").items().to_vec();
            for i in self.def_use_order(&ex) {
                extras.push(self.assignment(&ex[i])?);
            }
            let cond = if range_kind == 2 { Some(self.condition(op.get("cond"))?) } else { None };
            let body = self.expr(op.get("exp"))?;
            Ok((extras, cond, body))
        })();
        self.scopes.pop();
        let frame = self.extents.pop().unwrap();
        self.note_equal_extents(&frame);
        let (extras, cond, body) = result?;
        let implicit = || -> R<Dim> {
            match frame[&vars[0]].first() {
                Some(d) => Ok(d.clone()),
                None => self.err(op, "Subscript hasn't been used in summation"),
            }
        };
        let range = match range_kind {
            0 => SumRange::Implicit(implicit()?),
            1 => SumRange::Explicit(lo.unwrap(), hi.unwrap()),
            2 => SumRange::Cond(implicit()?, cond.unwrap()),
            _ => SumRange::Set(set_expr.unwrap()),
        };
        let mut body = body;
        if op.get("sign").truthy() {
            let t = body.ty.clone();
            body = Expr::new(ExprKind::Neg(body), t);
        }
        let ty = body.ty.clone();
        Ok(Expr::new(ExprKind::Sum { var: vars, range, body, extras }, ty))
    }

    fn integral(&mut self, op: &Val) -> R<Expr> {
        let var = ident_name(op.get("id"));
        let (lo, hi) = if op.get("d").truthy() {
            (self.expr(op.get("d").get("lower"))?, self.expr(op.get("d").get("upper"))?)
        } else {
            (self.sub_factor(op.get("lower"))?, self.sub_factor(op.get("upper"))?)
        };
        let mut scope = IndexMap::new();
        scope.insert(var.clone(), Sym::Local(Ty::real()));
        self.scopes.push(scope);
        let body = self.expr(op.get("exp"));
        self.scopes.pop();
        Ok(Expr::new(ExprKind::Integral { var, lo, hi, body: body? }, Ty::real()))
    }

    fn sub_factor(&mut self, n: &Val) -> R<Expr> {
        match n.class() {
            "IdentifierAlone" => self.identifier(n),
            "Subexpression" => {
                let mut e = self.expr(n.get("value"))?;
                e.paren = true;
                Ok(e)
            }
            "Pi" | "Infinity" | "E" => self.constant(n),
            _ => self.number(n),
        }
    }

    fn product(&mut self, op: &Val) -> R<Expr> {
        let l = self.expr(op.get("left"))?;
        let r = self.expr(op.get("right"))?;
        let name = match op.class() {
            "FroProduct" => "Frobenius",
            "HadamardProduct" => "Hadamard",
            "CrossProduct" => "Cross",
            _ => "Kronecker",
        };
        match op.class() {
            "FroProduct" => Ok(Expr::new(ExprKind::Frobenius(l, r), Ty::real())),
            "HadamardProduct" => {
                self.ensure(l.ty.same(&r.ty), op, || format!("{name} product error. Parameters must have the same dimension"))?;
                let ty = l.ty.with_elem(l.ty.elem().join(r.ty.elem()));
                Ok(Expr::new(ExprKind::Hadamard(l, r), ty))
            }
            "CrossProduct" => {
                let ok = l.ty.is_vector() && r.ty.is_vector() && l.ty.rows().py_eq(&Dim::Int(3)) && r.ty.rows().py_eq(&Dim::Int(3));
                self.ensure(ok, op, || "Cross product error. The dimension of parameters must be 3".into())?;
                // (integer only if both are)
                let elem = l.ty.elem().join(r.ty.elem());
                Ok(Expr::new(ExprKind::Cross(l, r), Vector { rows: Dim::Int(3), elem }))
            }
            _ => {
                let ty = Matrix {
                    rows: mul_dims(&l.ty.rows(), &r.ty.rows()),
                    cols: mul_dims(&l.ty.cols(), &r.ty.cols()),
                    elem: l.ty.elem().join(r.ty.elem()),
                    sparse: l.ty.is_sparse() || r.ty.is_sparse(),
                };
                Ok(Expr::new(ExprKind::Kronecker(l, r), ty))
            }
        }
    }

    /// A call `f(x)` of a local function, function parameter or sequence item.
    fn call(&mut self, op: &Val) -> R<Expr> {
        let name = func_name(&op.get("name").flat_text());
        let mut args = Vec::new();
        for s in op.get("subs").items() {
            args.push(self.index_expr(s)?);
        }
        for p in op.get("params").items() {
            args.push(self.expr(p)?);
        }
        let local = self.scopes.iter().rev().any(|s| s.contains_key(&name));
        if let Some(b) = self.builtin_names.get(&name).cloned() {
            if crate::decls::package_names(crate::decls::MESH_HELPER).unwrap().contains(&b.as_str()) && !self.is_defined(&name) {
                return self.mesh_call(op, &b, args);
            }
        }
        let (callee, fty) = match self.lookup(&name) {
            Some(sym) if sym.ty().is_func() => match self.overloads.get(&name) {
                Some(list) if list.len() > 1 && !local => {
                    let fits = |t: &Ty, exact: bool| match t {
                        Func { params, .. } => {
                            params.len() == args.len()
                                && params.iter().zip(&args).all(|(p, a)| p.same(&a.ty) && same_kind(p, &a.ty) && (!exact || p.is_int() == a.ty.is_int()))
                        }
                        _ => false,
                    };
                    let found = list.iter().find(|(t, _)| fits(t, true)).or_else(|| list.iter().find(|(t, _)| fits(t, false)));
                    match found {
                        Some((t, n)) => (Callee::Named(n.clone()), t.clone()),
                        None => return self.err(op, "Function error. Can't find function with current parameter types."),
                    }
                }
                _ => (Callee::Named(name.clone()), sym.ty()),
            },
            Some(_) => return self.err(op, format!("{name} is not a function")),
            None => return self.err(op, format!("Symbol {name} is not defined")),
        };
        let Func { params, rets } = fty else { unreachable!() };
        self.ensure(params.len() == args.len(), op, || "Function error. Parameters count mismatch".into())?;
        // dimension templates: a parameter dimension not known globally is
        // bound by the argument's dimension
        let mut binding: IndexMap<String, Dim> = IndexMap::new();
        for (p, a) in params.iter().zip(&args) {
            let pairs: Vec<(Dim, Dim)> = match (p, &a.ty) {
                (Vector { rows, .. }, Vector { rows: r2, .. }) => vec![(rows.clone(), r2.clone())],
                (Matrix { rows, cols, .. }, Matrix { rows: r2, cols: c2, .. }) => {
                    vec![(rows.clone(), r2.clone()), (cols.clone(), c2.clone())]
                }
                (Scalar(_), Scalar(_)) | (Set { .. }, Set { .. }) | (Func { .. }, Func { .. }) | (Seq { .. }, Seq { .. }) | (Tuple(_), Tuple(_)) | (Mesh(_), Mesh(_)) => vec![],
                _ => return self.err(op, format!("Function error. Parameter type mismatch: {p} vs {}", a.ty)),
            };
            for (pd, ad) in pairs {
                match &pd {
                    Dim::Str(s) if !self.is_defined(s) => {
                        binding.entry(s.clone()).or_insert(ad);
                    }
                    _ => self.ensure(is_same_expr(&pd, &ad), op, || "Function error. Parameter type mismatch".into())?,
                }
            }
        }
        let subst = |d: &Dim| -> Dim {
            match d {
                Dim::Str(s) => binding.get(s).cloned().unwrap_or_else(|| d.clone()),
                _ => d.clone(),
            }
        };
        let rets: Vec<Ty> = rets
            .iter()
            .map(|t| match t {
                Vector { rows, elem } => Vector { rows: subst(rows), elem: *elem },
                Matrix { rows, cols, elem, sparse } => Matrix { rows: subst(rows), cols: subst(cols), elem: *elem, sparse: *sparse },
                t => t.clone(),
            })
            .collect();
        let ty = if rets.len() == 1 { rets[0].clone() } else { Tuple(rets) };
        Ok(Expr::new(ExprKind::Call { callee, args }, ty))
    }

    /// `vertexset(S)`, `vertices(i)`, `tuple(a, b)`, `CellularSet(V, E, F)`, ...
    fn element_convert(&mut self, op: &Val) -> R<Expr> {
        let text = self.text(op);
        let name = text.split('(').next().unwrap_or("").trim().to_string();
        let args: Vec<Expr> = op.get("params").items().iter().map(|p| self.expr(p)).collect::<R<_>>()?;
        let kind = |c: &str| match c {
            "vertex" | "vertices" => Some(Elem::Vertex),
            "edge" | "edges" => Some(Elem::Edge),
            "face" | "faces" => Some(Elem::Face),
            "tet" | "tets" | "cell" | "cells" => Some(Elem::Tet),
            _ => None,
        };
        let ty = if let Some(e) = name.strip_suffix("set").and_then(kind) {
            self.ensure(args.len() == 1 && args[0].ty.is_set(), op, || format!("{name} needs a set"))?;
            Set { elems: vec![e], length: Dim::None }
        } else if let Some(e) = kind(&name) {
            self.ensure(args.len() == 1 && args[0].ty.is_scalar(), op, || format!("{name} needs an integer"))?;
            Scalar(e)
        } else if name == "CellularSet" {
            // vertices, edges, faces and tetrahedra (missing ones are empty)
            let kinds = [Elem::Vertex, Elem::Edge, Elem::Face, Elem::Tet];
            self.ensure(args.len() <= 4 && args.iter().all(|a| a.ty.is_set()), op, || "CellularSet takes up to 4 sets".into())?;
            Tuple(kinds.iter().map(|k| Set { elems: vec![*k], length: Dim::None }).collect())
        } else if name == "tuple" {
            Tuple(args.iter().map(|a| a.ty.clone()).collect())
        } else if name == "sequence" {
            return self.sequence(op, args);
        } else {
            return self.err(op, format!("Conversion {name} is not supported yet"));
        };
        Ok(Expr::new(ExprKind::Convert(args), ty))
    }

    /// `∂f/∂x`, `∂²f/∂x²` (types as the Python compiler's get_derivative_type
    /// and get_hessian_type).
    fn partial(&mut self, op: &Val) -> R<Expr> {
        let lowers = op.get("lower").items().to_vec();
        self.ensure(lowers.len() == 1, op, || "Mixed second derivatives (∂²f/∂x∂y) aren't supported".into())?;
        let var = ident_name(&lowers[0]);
        let vty = match self.globals.get(&var) {
            Some(Sym::Param(t)) => t.clone(),
            _ => return self.err(&lowers[0], format!("Symbol {var} isn't a param")),
        };
        let order = |n: &Val| if n.truthy() { self.int_literal(n).or_else(|| digits(n, get_unicode_number)).unwrap_or(0) } else { 1 };
        let uorder = order(op.get("uorder"));
        let lorder = op.get("lorder").items().first().map(|n| order(n)).unwrap_or(1);
        self.ensure(uorder == lorder, op, || "Order doesn't match".into())?;
        self.ensure(uorder == 1 || uorder == 2, op, || "Only first and second derivatives are supported".into())?;
        let upper_node = op.get("upper");
        let upper = self.expr(upper_node)?;
        self.ensure(upper.ty.is_scalar() || upper.ty.is_vector(), upper_node, || "Only support scalar or vector types".into())?;
        // the length of the flattened variable
        let n = match &vty {
            Scalar(_) => Dim::Int(1),
            Vector { rows, .. } => rows.clone(),
            Matrix { rows, cols, .. } => mul_dims(rows, cols),
            Seq { size, elem } if elem.is_scalar() => size.clone(),
            Seq { size, elem } if elem.is_vector() => mul_dims(size, &elem.rows()),
            _ => return self.err(&lowers[0], format!("Can't differentiate with respect to {}", vty.desc())),
        };
        let ty = match (uorder, &upper.ty) {
            (1, Scalar(_)) if vty.is_scalar() => Ty::real(),
            (1, Scalar(_)) => Ty::vector(n),
            (1, Vector { rows, .. }) if vty.is_scalar() => Ty::vector(rows.clone()),
            (1, Vector { rows, .. }) => Ty::matrix(rows.clone(), n),
            (2, Scalar(_)) if vty.is_scalar() => Ty::real(),
            (2, Scalar(_)) if !vty.is_matrix() => Ty::matrix(n.clone(), n),
            (2, Scalar(_)) => return self.err(op, "Second derivatives are supported with respect to a scalar, vector or sequence"),
            _ => return self.err(op, "Second derivatives are supported for scalars only"),
        };
        // ∂e/∂x of the program's definition e: recomputed, not differentiated as an expression
        let def = match (&*upper.kind, self.globals.get(&ident_name(upper_node.get("id0")))) {
            (ExprKind::Var(name), Some(Sym::Def(_))) => Some(name.clone()),
            _ => None,
        };
        self.derivatives = true;
        Ok(Expr::new(ExprKind::Partial { upper, var, hessian: uorder == 2, def }, ty))
    }

    /// `sequence(U, x, …)` (U a sequence: x, … appended to a copy) or `sequence(a, b, …)`.
    fn sequence(&mut self, op: &Val, mut args: Vec<Expr>) -> R<Expr> {
        self.ensure(!args.is_empty(), op, || "sequence needs items".into())?;
        let base = match &args[0].ty {
            Seq { .. } if args.len() > 1 => Some(args.remove(0)),
            _ => None,
        };
        let elem = match &base {
            Some(b) => match &b.ty {
                Seq { elem, .. } => (**elem).clone(),
                _ => unreachable!(),
            },
            None => args[0].ty.clone(),
        };
        for a in &args {
            self.ensure(same_kind(&elem, &a.ty) && elem.same(&a.ty), op, || {
                format!("sequence: items must have one type ({} and {})", elem, a.ty)
            })?;
        }
        // (the length is known only when the sequence is built)
        let ty = Seq { size: Dim::None, elem: Box::new(elem) };
        Ok(Expr::new(ExprKind::Sequence { base, items: args }, ty))
    }

    /// A MeshConnectivity function.
    fn mesh_call(&mut self, op: &Val, func: &str, args: Vec<Expr>) -> R<Expr> {
        let mesh_of = |this: &Self, a: Option<&Expr>| -> R<(String, MeshKind)> {
            match a.map(|a| (&*a.kind, &a.ty)) {
                Some((ExprKind::Var(n), Mesh(k))) => Ok((n.clone(), *k)),
                _ => this.err(op, format!("{func} needs a mesh")),
            }
        };
        let dim = |m: &str, e: Elem| Dim::Str(format!("@mesh:{m}:{}", elem_letter(e)));
        let set = |m: &str, e: Elem| Set { elems: vec![e], length: dim(m, e) };
        let bmat = |m: &str, a: Elem, b: Elem| Matrix { rows: dim(m, a), cols: dim(m, b), elem: Elem::Int, sparse: true };
        use Elem::*;
        let (f, mesh, ty) = match func {
            "ElementSets" => {
                let (m, k) = mesh_of(self, args.first())?;
                let mut v = vec![set(&m, Vertex), set(&m, Edge)];
                if k != MeshKind::Edge {
                    v.push(set(&m, Face));
                }
                if k == MeshKind::Cell {
                    v.push(set(&m, Tet));
                }
                (MeshFunc::ElementSets, m, Tuple(v))
            }
            "BoundaryMatrices" | "UnsignedBoundaryMatrices" => {
                let (m, k) = mesh_of(self, args.first())?;
                let mut v = vec![bmat(&m, Vertex, Edge)];
                if k != MeshKind::Edge {
                    v.push(bmat(&m, Edge, Face));
                }
                if k == MeshKind::Cell {
                    v.push(bmat(&m, Face, Tet));
                }
                let f = if func == "BoundaryMatrices" { MeshFunc::BoundaryMatrices } else { MeshFunc::UnsignedBoundaryMatrices };
                // (an edge mesh has one boundary matrix)
                let ty = if v.len() == 1 { v.pop().unwrap() } else { Tuple(v) };
                (f, m, ty)
            }
            "NonZeros" | "ValueSet" => {
                let ok = args.first().is_some_and(|a| a.ty.is_matrix() || a.ty.is_vector());
                self.ensure(ok, op, || format!("{func} needs a matrix or vector"))?;
                let f = if func == "NonZeros" { MeshFunc::NonZeros } else { MeshFunc::ValueSet };
                (f, String::new(), Set { elems: vec![Int], length: Dim::None })
            }
            "IndicatorVector" => {
                let e = match args.first().map(|a| &a.ty) {
                    Some(Set { elems, .. }) if elems.len() == 1 && elems[0].is_mesh_element() => elems[0],
                    _ => return self.err(op, "IndicatorVector needs a set of mesh elements"),
                };
                // the mesh the elements belong to (programs have one mesh)
                let Some((m, _)) = self.meshes.first().cloned() else {
                    return self.err(op, "IndicatorVector needs a mesh");
                };
                let ty = Matrix { rows: dim(&m, e), cols: Dim::Int(1), elem: Int, sparse: true };
                (MeshFunc::IndicatorVector(e), m, ty)
            }
            _ => return self.err(op, format!("Function {func} is not supported yet")),
        };
        Ok(Expr::new(ExprKind::MeshCall { func: f, mesh, args }, ty))
    }

    /// Builtin functions (`sin`, `trace`, `exp`, ...).
    fn builtin(&mut self, op: &Val) -> R<Expr> {
        let cls = op.class();
        let canonical = match cls {
            "AsinFunc" | "AcosFunc" | "AtanFunc" | "AsinhFunc" | "AcoshFunc" | "AtanhFunc" | "TraceFunc" => {
                // the name actually written (asin/arcsin, ...), canonicalized
                let written = op.get("name").flat_text();
                let written = self.builtin_names.get(&written).cloned().unwrap_or(written);
                match written.as_str() {
                    "arcsin" => "asin".into(),
                    "arccos" => "acos".into(),
                    "arctan" => "atan".into(),
                    "arsinh" => "asinh".into(),
                    "arcosh" => "acosh".into(),
                    "artanh" => "atanh".into(),
                    "tr" => "trace".into(),
                    w => w.to_string(),
                }
            }
            "LogFunc" => {
                if op.get("f").truthy() {
                    "log2".into()
                } else if op.get("s").truthy() {
                    "log10".into()
                } else {
                    "log".into()
                }
            }
            "MinmaxFunc" => (if op.get("min").truthy() { "min" } else { "max" }).into(),
            c => c.trim_end_matches("Func").to_lowercase(),
        };
        let mut args = Vec::new();
        if op.get("param").truthy() {
            args.push(self.expr(op.get("param"))?);
        }
        for k in ["second", "origin"] {
            if op.get(k).truthy() {
                args.push(self.expr(op.get(k))?);
            }
        }
        for p in op.get("params").items().iter().chain(op.get("extra").items()) {
            args.push(self.expr(p)?);
        }
        let a0 = args.first().map(|a| a.ty.clone()).unwrap_or(Ty::real());
        let ty = match canonical.as_str() {
            "sin" | "asin" | "cos" | "acos" | "tan" | "atan" | "sinh" | "asinh" | "cosh" | "acosh" | "tanh" | "atanh"
            | "cot" | "sec" | "csc" | "exp" | "log" | "log2" | "log10" | "ln" | "sqrt" => {
                self.ensure(a0.is_scalar() || a0.is_vector() || a0.is_matrix(), op, || "Parameter must be scalar, vector or matrix type".into())?;
                a0.with_elem(Elem::Real)
            }
            "atan2" => Ty::real(),
            "trace" | "det" | "rank" => {
                self.ensure(a0.is_matrix(), op, || "Parameter must be valid matrix type".into())?;
                Ty::real()
            }
            "inv" => {
                self.ensure(a0.is_matrix() && is_same_expr(&a0.rows(), &a0.cols()), op, || "Parameter must be valid matrix type".into())?;
                Ty::matrix(a0.rows(), a0.cols())
            }
            "svd" => {
                // U (rows × rows), the singular values, and V (cols × cols), as Eigen gives them
                self.ensure(a0.is_matrix() && !a0.is_sparse(), op, || "Parameter must be a dense matrix".into())?;
                Tuple(vec![Ty::matrix(a0.rows(), a0.rows()), Ty::vector(Dim::None), Ty::matrix(a0.cols(), a0.cols())])
            }
            "diag" => match &a0 {
                Matrix { rows, .. } => Ty::vector(rows.clone()),
                Vector { rows, .. } => Ty::matrix(rows.clone(), rows.clone()),
                _ => return self.err(op, "Parameter must be valid matrix or vector type"),
            },
            "vec" => match &a0 {
                Matrix { rows, cols, elem, .. } => Vector { rows: mul_dims(rows, cols), elem: *elem },
                _ => return self.err(op, "Parameter must be valid matrix type"),
            },
            "min" | "max" => {
                if args.len() > 1 {
                    Ty::real()
                } else {
                    Scalar(a0.elem())
                }
            }
            other => return self.err(op, format!("Function {other} is not supported yet")),
        };
        let mut e = Expr::new(ExprKind::Call { callee: Callee::Builtin(canonical), args }, ty);
        // sin²(x)
        let power = op.get("power");
        if power.truthy() {
            let p = Expr::new(ExprKind::Int(self.int_literal(power).unwrap_or(1)), Ty::int());
            let t = e.ty.clone();
            e = Expr::new(ExprKind::Pow(e, p), t);
        }
        Ok(e)
    }
}

// -- helpers -----------------------------------------------------------------

fn digits(v: &Val, f: fn(char) -> Option<i64>) -> Option<i64> {
    let s = v.flat_text();
    let mut n = 0i64;
    for c in s.chars() {
        n = n * 10 + f(c)?;
    }
    Some(n)
}

fn is_simple_name(s: &str) -> bool {
    !s.is_empty() && !s.contains(['+', '-', '*', '/', '(', ')', ' ', '[', ':', '@'])
}

/// A set type like `t` but of unknown length (the result of a set operation).
fn set_of(t: &Ty) -> Ty {
    match t {
        Set { elems, .. } => Set { elems: elems.clone(), length: Dim::None },
        t => t.clone(),
    }
}

/// The element kind of a set type keyword.
fn set_kind(s: &str) -> Option<Elem> {
    match s {
        "VertexSet" => Some(Elem::Vertex),
        "EdgeSet" => Some(Elem::Edge),
        "FaceSet" => Some(Elem::Face),
        "CellSet" | "TetSet" => Some(Elem::Tet),
        _ => None,
    }
}

/// The letter of a mesh element kind in a mesh dimension (`@mesh:M:v`).
pub fn elem_letter(e: Elem) -> char {
    match e {
        Elem::Vertex => 'v',
        Elem::Edge => 'e',
        Elem::Face => 'f',
        _ => 't',
    }
}

/// Mesh elements of different kinds (a vertex and a face, a vertex set and
/// an edge set) are different types for overloading.
fn same_kind(a: &Ty, b: &Ty) -> bool {
    let k = |t: &Ty| match t {
        Scalar(e) if e.is_mesh_element() => Some(*e),
        Set { elems, .. } if elems.len() == 1 && elems[0].is_mesh_element() => Some(elems[0]),
        _ => None,
    };
    match (k(a), k(b)) {
        (Some(x), Some(y)) => x == y,
        _ => true,
    }
}

/// A module's type with its parameters replaced by the importer's arguments.
fn subst_ty(t: &Ty, map: &HashMap<String, String>) -> Ty {
    let d = |d: &Dim| -> Dim {
        match d {
            Dim::Str(s) => {
                if let Some(a) = map.get(s) {
                    return Dim::Str(a.clone());
                }
                if let Some(rest) = s.strip_prefix("@mesh:") {
                    if let Some((m, k)) = rest.split_once(':') {
                        if let Some(a) = map.get(m) {
                            return Dim::Str(format!("@mesh:{a}:{k}"));
                        }
                    }
                }
                d.clone()
            }
            _ => d.clone(),
        }
    };
    match t {
        Vector { rows, elem } => Vector { rows: d(rows), elem: *elem },
        Matrix { rows, cols, elem, sparse } => Matrix { rows: d(rows), cols: d(cols), elem: *elem, sparse: *sparse },
        Seq { size, elem } => Seq { size: d(size), elem: Box::new(subst_ty(elem, map)) },
        Set { elems, length } => Set { elems: elems.clone(), length: d(length) },
        Tuple(v) => Tuple(v.iter().map(|x| subst_ty(x, map)).collect()),
        Func { params, rets } => Func { params: params.iter().map(|x| subst_ty(x, map)).collect(), rets: rets.iter().map(|x| subst_ty(x, map)).collect() },
        t => t.clone(),
    }
}

fn arith(a: &str, op: char, b: &Dim) -> Dim {
    crate::dims::simpify(&format!("({a}){op}({b})"))
}

fn arith_dims(l: &Dim, op: char, r: &Dim) -> Dim {
    if let (Dim::Int(a), Dim::Int(b)) = (l, r) {
        return Dim::Int(match op {
            '+' => a + b,
            '-' => a - b,
            '*' => a * b,
            _ => a / b,
        });
    }
    crate::dims::simpify(&format!("({l}){op}({r})"))
}

fn add_dims(a: &Dim, b: &Dim) -> Dim {
    match (a, b) {
        (Dim::Int(x), Dim::Int(y)) => Dim::Int(x + y),
        (Dim::Int(0), d) | (d, Dim::Int(0)) => d.clone(),
        _ => add_syms(a, b),
    }
}

/// The extent of axis `axis` of a value of type `t` (the size of what the
/// subscript at that position ranges over).
fn axis_extent(t: &Ty, axis: usize) -> Option<Dim> {
    match (t, axis) {
        (Vector { rows, .. }, 0) => Some(rows.clone()),
        (Matrix { rows, .. }, 0) => Some(rows.clone()),
        (Matrix { cols, .. }, 1) => Some(cols.clone()),
        (Seq { size, .. }, 0) => Some(size.clone()),
        (Seq { elem, .. }, a) => axis_extent(elem, a - 1),
        (Set { length, .. }, 0) => Some(length.clone()),
        _ => None,
    }
}

fn transpose_type(t: &Ty) -> Option<Ty> {
    match t {
        Matrix { rows, cols, elem, sparse } => Some(Matrix { rows: cols.clone(), cols: rows.clone(), elem: *elem, sparse: *sparse }),
        Vector { rows, elem } => Some(Matrix { rows: Dim::Int(1), cols: rows.clone(), elem: *elem, sparse: false }),
        _ => None,
    }
}

fn is_lifted(e: &Expr) -> bool {
    matches!(&*e.kind, ExprKind::Var(v) if v == "I")
}

fn sub_name(s: &Val) -> String {
    match s {
        Val::Str(x) => x.to_string(),
        n if n.class() == "Integer" => n.get("value").flat_text(),
        n => ident_name(n),
    }
}

/// Matrix rows as lists of item expressions.
fn flatten_rows(rows: &Val, out: &mut Vec<Vec<Val>>) {
    if rows.get("rs").truthy() {
        flatten_rows(rows.get("rs"), out);
    }
    if rows.get("r").truthy() {
        let mut items = Vec::new();
        flatten_row(rows.get("r"), &mut items);
        out.push(items);
    }
}

fn flatten_row(row: &Val, out: &mut Vec<Val>) {
    match row.class() {
        "MatrixRow" => {
            if row.get("value").truthy() {
                for r in row.get("value").items() {
                    flatten_row(r, out);
                }
            }
            if row.get("rc").truthy() {
                flatten_row(row.get("rc"), out);
            }
            if row.get("exp").truthy() {
                out.push(row.get("exp").clone());
            }
        }
        "MatrixRowCommas" => {
            if row.get("value").truthy() {
                flatten_row(row.get("value"), out);
            }
            if row.get("exp").truthy() {
                out.push(row.get("exp").clone());
            }
        }
        _ => out.push(row.clone()),
    }
}

fn flatten_ifs(ifs: &Val, out: &mut Vec<Val>) {
    if ifs.get("ifs").truthy() {
        flatten_ifs(ifs.get("ifs"), out);
    }
    if ifs.get("value").truthy() {
        out.push(ifs.get("value").clone());
    }
}

/// The branches of the piecewise expression an expression is (or nothing).
fn piecewise_branches(n: &Val, out: &mut Vec<Val>) {
    match n.class() {
        "Expression" | "Factor" => {
            let inner = if n.get("value").truthy() { n.get("value") } else { n.get("op") };
            if inner.node().is_some() {
                piecewise_branches(inner, out);
            }
        }
        "MultiCondExpr" => {
            let mut singles = Vec::new();
            flatten_ifs(n.get("ifs"), &mut singles);
            out.extend(singles.iter().map(|s| s.get("stat").clone()));
            if n.get("other").truthy() {
                out.push(n.get("other").clone());
            }
        }
        _ => {}
    }
}

/// The name of a local function definition.
fn local_func_name(s: &Val) -> String {
    match s.get("name") {
        Val::Str(n) => n.to_string(),
        n => crate::decls::main_name(n),
    }
}

/// Whether two function types have the same parameter signature (exact
/// element kinds), so they cannot overload each other.
fn same_signature(a: &Ty, b: &Ty) -> bool {
    match (a, b) {
        (Func { params: p1, .. }, Func { params: p2, .. }) => {
            p1.len() == p2.len() && p1.iter().zip(p2).all(|(x, y)| x.same(y) && same_kind(x, y) && x.is_int() == y.is_int())
        }
        _ => false,
    }
}

/// A function name as written: backticks are dropped from plain words.
fn func_name(raw: &str) -> String {
    crate::decls::strip_backticks(raw)
}

/// Names a statement defines.
fn stmt_defines(s: &Val) -> IndexSet<String> {
    let mut d = IndexSet::new();
    match s.class() {
        "Assignment" | "Destructure" | "GeneralAssignment" => {
            for l in s.get("left").items() {
                d.insert(crate::decls::main_name(l));
            }
        }
        "LocalFunc" => {
            let n = match s.get("name") {
                Val::Str(x) => x.to_string(),
                n => crate::decls::main_name(n),
            };
            d.insert(n);
        }
        _ => {}
    }
    d
}

/// All names used in a parse tree.
fn collect_names(n: &Val, out: &mut IndexSet<String>) {
    match n {
        Val::Node(p) => {
            match p.class {
                Some("IdentifierAlone") => {
                    out.insert(ident_name(n));
                }
                Some("Function") => {
                    let name = n.get("name").flat_text();
                    out.insert(name.split('_').next().unwrap_or("").to_string());
                    out.insert(name);
                }
                _ => {}
            }
            for (_, v) in &p.fields {
                collect_names(v, out);
            }
        }
        Val::List(v) | Val::Closure(v) | Val::Tuple(v) => v.iter().for_each(|x| collect_names(x, out)),
        _ => {}
    }
}

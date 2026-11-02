//! Modules: `.hlang` files imported with `X from Module(params)`.
//!
//! A module is found, as in the Python compiler, first among the modules
//! that come with I❤️LA (`iheartla/mesh/*.hlang`, embedded in the binary),
//! then in the search directories (the importing file's directory): `.hlang`
//! files, then `.ihla` files (which H❤️rtDown writes for each context). Each
//! module is compiled once per compilation and shared by all its importers.

use crate::ast::Program;
use std::cell::RefCell;
use std::collections::HashMap;
use std::path::PathBuf;
use std::rc::Rc;

/// The modules that come with I❤️LA.
const BUILTIN: &[(&str, &str)] = &[
    ("FundamentalMeshAccessors", include_str!("../../iheartla/mesh/FundamentalMeshAccessors.hlang")),
    ("FundamentalPointCloudAccessors", include_str!("../../iheartla/mesh/FundamentalPointCloudAccessors.hlang")),
    ("FundamentalPolygonAccessors", include_str!("../../iheartla/mesh/FundamentalPolygonAccessors.hlang")),
    ("FundamentalTetrahedronAccessors", include_str!("../../iheartla/mesh/FundamentalTetrahedronAccessors.hlang")),
    ("Neighborhoods", include_str!("../../iheartla/mesh/Neighborhoods.hlang")),
    ("PointCloudNeighborhoods", include_str!("../../iheartla/mesh/PointCloudNeighborhoods.hlang")),
    ("PolygonNeighborhoods", include_str!("../../iheartla/mesh/PolygonNeighborhoods.hlang")),
    ("TetrahderonNeighborhoods", include_str!("../../iheartla/mesh/TetrahderonNeighborhoods.hlang")),
];

#[derive(Default)]
pub struct Loader {
    /// directories searched after the builtin modules
    pub dirs: Vec<PathBuf>,
    cache: RefCell<HashMap<String, Rc<Program>>>,
    /// modules being compiled (to report import cycles)
    loading: RefCell<Vec<String>>,
}

impl Loader {
    pub fn new(dirs: Vec<PathBuf>) -> Rc<Loader> {
        Rc::new(Loader { dirs, ..Default::default() })
    }

    /// The source of a module, if it exists.
    pub fn source(&self, name: &str) -> Option<String> {
        if let Some((_, src)) = BUILTIN.iter().find(|(n, _)| *n == name) {
            return Some(src.to_string());
        }
        ["hlang", "ihla"]
            .iter()
            .flat_map(|ext| self.dirs.iter().map(move |d| d.join(format!("{name}.{ext}"))))
            .find(|p| p.is_file())
            .and_then(|p| std::fs::read_to_string(p).ok())
    }

    pub fn exists(&self, name: &str) -> bool {
        self.cache.borrow().contains_key(name) || self.source(name).is_some()
    }

    /// The compiled module.
    pub fn load(self: &Rc<Self>, name: &str) -> Result<Rc<Program>, String> {
        if let Some(p) = self.cache.borrow().get(name) {
            return Ok(p.clone());
        }
        if self.loading.borrow().iter().any(|n| n == name) {
            return Err(format!("Module {name} imports itself"));
        }
        let src = self.source(name).ok_or_else(|| format!("Module {name} is not found"))?;
        self.loading.borrow_mut().push(name.to_string());
        let result = crate::front_end_with(&src, self);
        self.loading.borrow_mut().pop();
        let (_, prog) = result.map_err(|e| format!("In module {name}:\n{e}"))?;
        let prog = Rc::new(prog);
        self.cache.borrow_mut().insert(name.to_string(), prog.clone());
        Ok(prog)
    }

    /// The names of the functions a module defines (for the importer's parser
    /// configuration), or None if there is no such module.
    pub fn function_names(self: &Rc<Self>, name: &str) -> Option<Vec<String>> {
        if !self.exists(name) {
            return None;
        }
        let prog = self.load(name).ok()?;
        Some(prog.funcs.iter().map(|(n, _)| n.clone()).collect())
    }
}

//! LaTeX and MathJax backends.
//!
//! Unlike the code backends, these print the program as written: they walk
//! the (second) parse tree, so parentheses, descriptions and the order of
//! statements are the source's. Types from the checker (`Program::expr_types`,
//! `Program::base_types`) decide what depends on them: `|x|` or `‖x‖`, and the
//! form of an indexing subscript. The output follows the Python compiler's
//! `codegen_latex.py` / `codegen_mathjax.py`.

use crate::ast::Program;
use crate::decls::ident_name;
use crate::helper::{get_unicode_number, get_unicode_sub_number};
use crate::pnode::Val;
use crate::ty::Ty;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Flavor {
    /// a standalone LaTeX document
    Latex,
    /// an `align*` block for MathJax
    Mathjax,
    /// MathJax for H❤️rtDown: symbols and equations carry click handlers
    /// (`\idlabel`, `\eqlabel`) naming each symbol and its definitions and uses
    MacroMathjax,
}

const LATEX_PRE: &str = r"\documentclass[12pt]{article}
\usepackage{mathdots}
\usepackage[bb=boondox]{mathalfa}
\usepackage{mathtools}
\usepackage{amssymb}
\usepackage{unicode-math}
\usepackage{libertine}
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\usepackage[paperheight=8in,paperwidth=4in,margin=.3in,heightrounded]{geometry}
\let\originalleft\left
\let\originalright\right
\renewcommand{\left}{\mathopen{}\mathclose\bgroup\originalleft}
\renewcommand{\right}{\aftergroup\egroup\originalright}
\begin{document}

\begin{center}
\resizebox{\textwidth}{!}
{
\begin{minipage}[c]{\textwidth}
\begin{align*}
";

const LATEX_POST: &str = r"\end{align*}
\end{minipage}
}
\end{center}

\end{document}
";

const MATHJAX_PRE: &str = r"\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator*{\argmin}{arg\,min}
\begin{align*}
";

const MATHJAX_POST: &str = "\\end{align*}\n";

/// Unicode characters LaTeX (pdflatex with these packages) can't show as is.
const UNICODE_LATEX: &[(&str, &str)] = &[
    ("ᵢ", "\\textsubscript{i}"),
    ("ⱼ", "\\textsubscript{j}"),
    ("ᵣ", "\\textsubscript{r}"),
    ("ᵤ", "\\textsubscript{u}"),
    ("ᵥ", "\\textsubscript{v}"),
    ("𝟙", "\\mathbb{ 1 }"),
    ("𝐚", "\\textbf{a}"),
    ("𝐛", "\\textbf{b}"),
    ("𝐜", "\\textbf{c}"),
    ("𝐝", "\\textbf{d}"),
    ("𝐞", "\\textbf{e}"),
    ("𝐟", "\\textbf{f}"),
    ("𝐠", "\\textbf{g}"),
    ("𝐡", "\\textbf{h}"),
    ("𝐢", "\\textbf{i}"),
    ("𝐣", "\\textbf{j}"),
    ("𝐤", "\\textbf{k}"),
    ("𝐥", "\\textbf{l}"),
    ("𝐦", "\\textbf{m}"),
    ("𝐧", "\\textbf{n}"),
    ("𝐨", "\\textbf{o}"),
    ("𝐩", "\\textbf{p}"),
    ("𝐪", "\\textbf{q}"),
    ("𝐫", "\\textbf{r}"),
    ("𝐬", "\\textbf{s}"),
    ("𝐭", "\\textbf{t}"),
    ("𝐮", "\\textbf{u}"),
    ("𝐯", "\\textbf{v}"),
    ("𝐰", "\\textbf{w}"),
    ("𝐱", "\\textbf{x}"),
    ("𝐲", "\\textbf{y}"),
    ("𝐳", "\\textbf{z}"),
    ("⩽", "\\leq"),
    ("⩾", "\\geq"),
];

pub fn generate(prog: &Program, tree: &Val, flavor: Flavor) -> String {
    // names declared in where blocks
    let mut declared = std::collections::HashSet::new();
    for b in tree.get("vblock").items().iter().filter(|b| b.class() == "ParamsBlock") {
        for c in b.get("conds").get("value").items() {
            for id in c.get("id").items() {
                declared.insert(crate::decls::main_name(id));
            }
        }
    }
    // functions imported from MeshConnectivity (printed as plain calls)
    let mut mesh_funcs = std::collections::HashSet::new();
    for b in tree.get("vblock").items().iter().filter(|b| b.class() == "Import") {
        if ident_name(b.get("package")) == crate::decls::MESH_HELPER {
            for v in b.get("names").items() {
                let r = if v.get("r").truthy() { v.get("r") } else { v.get("name") };
                mesh_funcs.insert(ident_name(r));
            }
        }
    }
    // parameters of local functions (for MacroMathJax's labels)
    let mut local_params = std::collections::HashSet::new();
    for b in tree.get("vblock").items().iter().filter(|b| b.class() == "Statements" && b.get("stat").class() == "LocalFunc") {
        let f = b.get("stat");
        for x in f.get("params").items().iter().chain(f.get("subs").items()) {
            local_params.insert(ident_name(x));
        }
        // (and its local definitions)
        for e in f.get("extra").items() {
            for l in e.get("left").items() {
                local_params.insert(crate::decls::main_name(l));
            }
        }
    }
    let mut p = Printer {
        prog,
        flavor,
        in_sum: false,
        local_func: false,
        align_local: false,
        declared,
        mesh_funcs,
        local_params,
        no_label: 0,
        defining: false,
        local_func_name: String::new(),
    };
    let body = p.start(tree);
    match flavor {
        Flavor::Latex => {
            let mut body = body;
            for (k, v) in UNICODE_LATEX {
                body = body.replace(k, v);
            }
            // (the Python compiler's preamble has a trailing space here; kept in
            // code because editors strip trailing whitespace from the constant)
            let pre = LATEX_PRE.replace("{!}\n", "{!} \n");
            format!("{pre}{body}{LATEX_POST}")
        }
        Flavor::Mathjax | Flavor::MacroMathjax => format!("{MATHJAX_PRE}{body}{MATHJAX_POST}"),
    }
}

/// A symbol for JavaScript in a click handler.
fn js_content(s: &str) -> String {
    s.replace('\\', "\\\\\\\\").replace('`', "").replace('"', "\\\\\"").replace('\'', "\\\\'")
}

/// URL-safe base64 (an equation's source in its click handler).
fn b64(s: &str) -> String {
    crate::helper::base64_encode(s).replace('+', "-").replace('/', "_")
}

/// `\mathit` for a multi-letter name.
fn special_marks(name: &str) -> String {
    if ['\u{303}', '\u{302}', '\u{304}'].iter().any(|m| name.contains(*m)) {
        return format!("\\textit{{{name}}}");
    }
    if name.contains('∂') {
        return name.to_string();
    }
    if name.chars().count() > 1 {
        format!("\\mathit{{{name}}}")
    } else {
        name.to_string()
    }
}

/// Escape LaTeX's special characters in text.
fn special_syms(text: &str) -> String {
    let mut t = text.replace('\\', "\\textbackslash{}");
    for c in ['_', '&', '^', '%', '$', '#', '{', '}'] {
        t = t.replace(c, &format!("\\{c}"));
    }
    t
}

/// A name as LaTeX: backticked names are text, with `$…$` parts as math.
fn convert_name(name: &str) -> String {
    if !name.contains('`') {
        return special_marks(name);
    }
    let name = if !name.contains("`$") && !name.contains("$`") {
        let inner: String = name.chars().skip(1).take(name.chars().count().saturating_sub(2)).collect();
        format!("`${inner}$`")
    } else {
        name.to_string()
    };
    let text = name.replace('`', "");
    let re = regex::Regex::new(r"\$(?P<context>.*)\$").unwrap();
    let mut res = String::new();
    let mut first = true;
    let mut end = 0;
    // positions in `name` (with backticks) as the Python compiler uses them on `text`
    for m in re.captures_iter(&name) {
        let whole = m.get(0).unwrap();
        if first {
            let start = whole.start().saturating_sub(1).min(text.len());
            let tmp = special_syms(&text[..start]);
            if !tmp.is_empty() {
                res += &format!("\\textit{{{tmp}}}");
            }
            first = false;
        }
        end = whole.end();
        res += m.name("context").unwrap().as_str();
    }
    let from = end.saturating_sub(1).min(text.len());
    let tmp = special_syms(&text[from..]);
    if !tmp.is_empty() {
        res += &format!("\\textit{{{tmp}}}");
    }
    res
}

/// Python's `repr` of a float.
fn py_float(text: &str) -> String {
    let Ok(v) = text.parse::<f64>() else { return text.to_string() };
    let a = v.abs();
    if a != 0.0 && !(1e-4..1e16).contains(&a) {
        let s = format!("{v:e}");
        let (m, e) = s.split_once('e').unwrap();
        let exp: i32 = e.parse().unwrap();
        return format!("{m}e{}{:02}", if exp < 0 { '-' } else { '+' }, exp.abs());
    }
    let s = format!("{v:?}");
    if s.contains('.') || s.contains('e') {
        s
    } else {
        format!("{s}.0")
    }
}

struct Printer<'p> {
    prog: &'p Program,
    flavor: Flavor,
    in_sum: bool,
    local_func: bool,
    align_local: bool,
    declared: std::collections::HashSet<String>,
    mesh_funcs: std::collections::HashSet<String>,
    local_params: std::collections::HashSet<String>,
    /// > 0: inside subscripts, where names are not labeled
    no_label: usize,
    /// printing a definition (an assignment's left side, a function's name)
    defining: bool,
    /// the last local function printed (MacroMathJax)
    local_func_name: String,
}

fn span(n: &Val) -> Option<(usize, usize)> {
    n.node().and_then(|x| x.span)
}

impl<'p> Printer<'p> {
    fn src(&self, n: &Val) -> String {
        crate::node_text(&self.prog.source, n).to_string()
    }

    /// The type of a program-level symbol.
    fn symbol_type(&self, name: &str) -> Option<&Ty> {
        self.prog.defs.iter().find(|(n, _)| n == name).map(|(_, t)| t).or_else(|| self.prog.params.iter().find(|p| p.name == name).map(|p| &p.ty))
    }

    fn defined(&self, name: &str) -> bool {
        self.symbol_type(name).is_some()
    }

    fn ty(&self, n: &Val) -> Option<&Ty> {
        self.prog.expr_types.get(&span(n)?)
    }

    fn macro_(&self) -> bool {
        self.flavor == Flavor::MacroMathjax
    }

    /// A symbol's LaTeX `content`, with MacroMathJax's click handler.
    fn label(&self, full: &str, main: &str, content: String) -> String {
        if !self.macro_() || self.no_label > 0 {
            return content;
        }
        let func = "heartlib";
        let use_type = if self.defining { "def" } else { "use" };
        let (local, lf) = if self.local_func {
            (self.local_params.contains(full), self.local_func_name.as_str())
        } else {
            (false, "")
        };
        let m = js_content(main);
        let json = format!(
            "{{\"onclick\":\"event.stopPropagation(); onClickSymbol(this, '{m}', '{func}', '{use_type}', {}, '{lf}')\", \"id\":\"{func}-{}\", \"sym\":\"{m}\", \"func\":\"{func}\",  \"localFunc\":\"{lf}\", \"type\":\"{use_type}\", \"case\":\"equation\"}}",
            if local { "true" } else { "false" },
            js_content(full)
        );
        format!("\\idlabel{{ {json} }}{{ {{{content}}} }}")
    }

    /// The program symbols an expression uses (for MacroMathJax's equation
    /// labels), in order of first use, without subscripts. Like the Python
    /// compiler, it leaves out what piecewise expressions, integrals, norm
    /// and inner product subscripts, summation conditions and optimization
    /// constraints use, and includes optimization variables and a block
    /// matrix's I.
    fn symbols(&self, n: &Val, out: &mut Vec<String>) {
        self.symbols_in(n, out, false);
    }

    fn symbols_in(&self, n: &Val, out: &mut Vec<String>, in_matrix: bool) {
        if n.is_seq() {
            for x in n.items() {
                self.symbols_in(x, out, in_matrix);
            }
            return;
        }
        let Some(node) = n.node() else { return };
        let in_matrix = in_matrix || n.class() == "Matrix";
        if n.class() == "Integral" {
            return;
        }
        if n.class() == "Summation" && n.get("u").truthy() {
            for v in n.get("enum").items() {
                let name = ident_name(v);
                if !out.contains(&name) {
                    out.push(name);
                }
            }
        }
        if n.class() == "Optimize" {
            for d in n.get("defs").items() {
                for id in d.get("id").items() {
                    let v = crate::decls::main_name(id);
                    if !out.contains(&v) {
                        out.push(v);
                    }
                }
            }
        }
        if in_matrix && n.class() == "IdentifierAlone" && ident_name(n) == "I" && !out.contains(&"I".to_string()) {
            out.push("I".into());
        }
        let name = match n.class() {
            "IdentifierAlone" => Some(ident_name(n)),
            "IdentifierSubscript" => Some(ident_name(n.get("left"))),
            "Function" => n.get("name").as_str().map(crate::decls::strip_backticks),
            _ => None,
        };
        if let Some(name) = name {
            let known = self.defined(&name) || self.prog.funcs.iter().any(|(f, _)| *f == name) || self.mesh_funcs.contains(&name);
            if known && !out.contains(&name) {
                out.push(name);
            }
        }
        if n.class() == "IdentifierSubscript" {
            return;
        }
        for (k, v) in &node.fields {
            let skip = matches!((n.class(), *k), ("Summation", "cond") | ("Summation", "range") | ("Optimize", "cond") | ("Optimize", "defs") | ("Norm", "sub") | ("InnerProduct", "sub"));
            if !skip {
                self.symbols_in(v, out, in_matrix);
            }
        }
    }

    /// MacroMathJax's click handler for an equation.
    fn eqlabel(&self, syms: &[String], tail: &str) -> String {
        let list: Vec<String> = syms.iter().map(|x| format!("'{}'", js_content(x))).collect();
        // (the used symbols sorted, as the Python compiler lists them; the defined one last)
        let mut list = list;
        if let Some(last) = list.pop() {
            list.sort();
            list.dedup();
            list.push(last);
        }
        format!("\\\\\\eqlabel{{ {{\"onclick\":\"event.stopPropagation(); onClickEq(this, 'heartlib', [{}], {tail});\"}} }}{{}}\n", list.join(", "))
    }

    // -- blocks --------------------------------------------------------------

    fn start(&mut self, tree: &Val) -> String {
        let mut content = String::new();
        let (mut pre_param, mut pre_exp) = (false, false);
        for b in tree.get("vblock").items() {
            let is_params = b.class() == "ParamsBlock";
            if !is_params {
                let stat = if b.class() == "Statements" { b.get("stat") } else { b };
                let mut s = self.statement(stat);
                let cls = stat.class();
                match self.flavor {
                    Flavor::Latex => {
                        if !matches!(cls, "Assignment" | "GeneralAssignment" | "Destructure" | "LocalFunc" | "Equation") {
                            s = format!(" \\omit \\span {s}");
                        }
                    }
                    Flavor::Mathjax | Flavor::MacroMathjax => {
                        if !matches!(cls, "Assignment" | "GeneralAssignment") {
                            s = format!(" & {s}");
                        }
                    }
                }
                content += &s;
                content += " \\\\\n";
            } else {
                let annotated = b.get("annotation").truthy();
                if (pre_param || pre_exp) && !annotated {
                    content += "\\\\\n";
                }
                content += &self.params_block(b);
            }
            pre_param = is_params;
            pre_exp = !is_params;
        }
        content
    }

    fn params_block(&mut self, b: &Val) -> String {
        let mut content = String::new();
        for c in b.get("conds").get("value").items() {
            content += &self.where_condition(c);
            content += " \\\\\n";
        }
        if b.get("annotation").truthy() {
            let a = b.get("annotation").flat_text();
            content = match self.flavor {
                Flavor::Latex => format!("\\intertext{{{a}}} \n{content}"),
                Flavor::Mathjax | Flavor::MacroMathjax => format!("{a} \\\\\n{content}"),
            };
        }
        content + "\\\\\n"
    }

    fn where_condition(&mut self, c: &Val) -> String {
        let ids: Vec<String> = c.get("id").items().iter().map(|i| self.id_node(i)).collect();
        let ty = c.get("type");
        let mut belong = if c.get("belong").truthy() { c.get("belong").flat_text() } else { "\\in".into() };
        if ty.class() == "MappingType" && (c.get("subset").truthy() || ty.get("subset").truthy()) {
            belong = "\\subset".into();
        }
        let t = self.la_type(ty);
        let mut content = if self.local_func && !self.align_local {
            format!("{} {belong} {t}", ids.join(","))
        } else {
            format!("{} & {belong} {t}", ids.join(","))
        };
        if c.get("attrib").truthy() {
            content += &format!(" ,\\text{{ {}}}", c.get("attrib").flat_text());
        }
        if c.get("desc").truthy() {
            content += &format!(" \\text{{ {}}}", special_syms(&c.get("desc").flat_text()));
        }
        content
    }

    fn field(t: &Val) -> &'static str {
        if t.flat_text() == "ℤ" {
            "\\mathbb{Z}"
        } else {
            "\\mathbb{R}"
        }
    }

    fn la_type(&mut self, t: &Val) -> String {
        match t.class() {
            "ScalarType" => (if t.get("z").truthy() { "\\mathbb{Z}" } else { "\\mathbb{R}" }).into(),
            "VectorType" => format!("{}^{{ {}}}", Self::field(t.get("type")), self.dim(t.get("id1"))),
            "MatrixType" => {
                let mut s = format!("{}^{{ {} \\times {} }}", Self::field(t.get("type")), self.dim(t.get("id1")), self.dim(t.get("id2")));
                if t.get("attr").flat_text().contains("sparse") {
                    s += " ,\\text{ sparse}";
                }
                s
            }
            "NamedType" => format!("\\text{{ {}}}", self.src(t)),
            "SetType" => {
                let mut content = String::new();
                if t.get("type").truthy() {
                    let parts: Vec<&str> = t.get("type").items().iter().map(Self::field).collect();
                    content = if parts.is_empty() { Self::field(t.get("type")).to_string() } else { parts.join(" \\times ") };
                } else if t.get("type1").truthy() || t.get("type2").truthy() {
                    let f = if t.get("type1").truthy() { t.get("type1") } else { t.get("type2") };
                    content = format!("{}^{{ {} }}", Self::field(f), self.int_text(t.get("cnt")));
                }
                format!("\\{{{content}\\}}")
            }
            "TupleType" => t.get("sub_types").items().iter().map(|s| self.la_type(s)).collect::<Vec<_>>().join("\\times"),
            "FunctionType" => {
                let params = t.get("params").items();
                let ret: Vec<String> = t.get("ret").items().iter().map(|r| self.la_type(r)).collect();
                let ret = if ret.is_empty() { self.la_type(t.get("ret")) } else { ret.join(",") };
                let params_str = if params.is_empty() {
                    if t.get("empty").truthy() { "\\varnothing".to_string() } else { "\\{\\}".to_string() }
                } else {
                    self.joined(params, t.get("separators"), |p, x| p.la_type(x))
                };
                format!("{params_str}\\rightarrow {ret}")
            }
            "MappingType" => {
                if t.get("src").truthy() {
                    format!("{}\\rightarrow {}", self.la_type(t.get("src")), self.la_type(t.get("dst")))
                } else if t.get("s").truthy() {
                    let st = t.get("s");
                    if matches!(st.class(), "IdentifierAlone" | "IdentifierSubscript") {
                        self.id_node(st)
                    } else {
                        self.la_type(st)
                    }
                } else {
                    self.src(t)
                }
            }
            _ => self.src(t),
        }
    }

    /// Items joined with their source separators (`a,b`).
    fn joined(&mut self, items: &[Val], seps: &Val, mut f: impl FnMut(&mut Self, &Val) -> String) -> String {
        let seps = seps.items();
        let mut s = String::new();
        for (i, x) in items.iter().enumerate() {
            s += &f(self, x);
            if i + 1 < items.len() {
                s += &seps.get(i).map(|v| v.flat_text()).unwrap_or_else(|| ",".into());
            }
        }
        s
    }

    fn int_text(&self, n: &Val) -> String {
        match n.class() {
            "SupInteger" => digits(&n.get("value").flat_text(), get_unicode_number),
            "SubInteger" => digits(&n.get("value").flat_text(), get_unicode_sub_number),
            "Integer" => n.get("value").flat_text(),
            _ => n.flat_text(),
        }
    }

    /// A dimension (in a type).
    fn dim(&mut self, n: &Val) -> String {
        match n.class() {
            "ArithExpression" => {
                let v = self.dim(n.get("value"));
                if n.get("sign").truthy() {
                    format!("{}{v}", n.get("sign").flat_text())
                } else {
                    v
                }
            }
            "ArithFactor" => {
                if n.get("id0").truthy() {
                    self.dim(n.get("id0"))
                } else if n.get("num").truthy() {
                    self.dim(n.get("num"))
                } else {
                    format!("\\left( {} \\right)", self.dim(n.get("sub").get("value")))
                }
            }
            "ArithSubexpression" => format!("\\left( {} \\right)", self.dim(n.get("value"))),
            "ArithAdd" | "ArithSubtract" => format!("{} {} {}", self.dim(n.get("left")), n.get("op").flat_text(), self.dim(n.get("right"))),
            "ArithMultiply" => format!("{} {}", self.dim(n.get("left")), self.dim(n.get("right"))),
            "ArithDivide" => format!("\\frac{{{}}}{{{}}}", self.dim(n.get("left")), self.dim(n.get("right"))),
            "IdentifierAlone" => self.id_node(n),
            "IdentifierSubscript" => {
                let name = ident_name(n.get("left"));
                let main = self.label(&name, &name, convert_name(&name));
                let subs: Vec<String> = self.subscripts(n).iter().map(|s| self.sub_name(s)).collect();
                format!("{main}_{{ {} }}", subs.join(", "))
            }
            "Integer" | "SupInteger" | "SubInteger" => self.int_text(n),
            _ => self.expr(n),
        }
    }

    // -- statements ----------------------------------------------------------

    fn statement(&mut self, s: &Val) -> String {
        match s.class() {
            "Import" => self.import(s),
            "Assignment" | "GeneralAssignment" | "Destructure" => self.assignment(s),
            "LocalFunc" if self.macro_() => self.macro_local_func(s),
            "LocalFunc" => self.local_func(s),
            "Equation" => format!("{} & = {}", self.expr(s.get("left")), self.expr(s.get("right"))),
            _ => {
                let e = self.expr(s);
                if self.macro_() && optimize_node(s).is_some() {
                    let mut syms = Vec::new();
                    self.symbols(s, &mut syms);
                    return e + &self.eqlabel(&syms, &format!("false, [], [], '{}', false", b64(&self.src(s))));
                }
                e
            }
        }
    }

    fn import(&mut self, s: &Val) -> String {
        let names: Vec<String> = s.get("names").items().iter().map(|n| self.src(n).replace('_', "\\_")).collect();
        let name_str = if s.get("star").truthy() { "*".to_string() } else { names.join(", ") };
        let params = s.get("params").items().to_vec();
        let params_str = self.joined(&params, s.get("separators"), |p, x| p.expr(x)).replace("\\mathit{", "\\textit{");
        let package = self.src(s.get("package")).replace('_', "\\_");
        if params.is_empty() {
            format!("\\text{{ {name_str} from {package} }}\\\\\n")
        } else {
            format!("\\text{{ {name_str} from {package}({params_str}) }}\\\\\n")
        }
    }

    fn sides(&mut self, v: &Val) -> Vec<Val> {
        if v.is_seq() {
            v.items().to_vec()
        } else if v.truthy() {
            vec![v.clone()]
        } else {
            vec![]
        }
    }

    fn assignment(&mut self, s: &Val) -> String {
        let left = self.sides(s.get("left"));
        let right = self.sides(s.get("right"));
        self.defining = true;
        let lhs: Vec<String> = left.iter().map(|l| self.lhs(l)).collect();
        self.defining = false;
        let label = |this: &Self| -> String {
            if !this.macro_() || this.in_sum {
                return String::new();
            }
            let mut syms = Vec::new();
            // (a sparse matrix defined piecewise, `A_ij = { … if (i,j) ∈ E`)
            let piecewise = |r: &Val| r.class() == "MultiCondExpr" || r.get("value").class() == "MultiCondExpr";
            let sparse_def = left.len() == 1
                && left[0].class() == "IdentifierSubscript"
                && right.first().is_some_and(piecewise)
                && this.symbol_type(&ident_name(left[0].get("left"))).is_some_and(|t| t.is_sparse());
            if left.len() == 1 && !sparse_def {
                for r in &right {
                    this.symbols(r, &mut syms);
                }
            }
            if let Some(l) = left.first() {
                syms.push(crate::decls::main_name(l));
            }
            this.eqlabel(&syms, &format!("false, [], [], '{}'", b64(&this.src(s))))
        };
        if let Some(r) = right.first() {
            if let Some(opt) = optimize_node(r) {
                return self.optimize(&opt, Some(lhs.join(", "))) + &label(self);
            }
        }
        let rhs: Vec<String> = right.iter().map(|r| if self.macro_() { self.expr(r) } else { self.strip_parens(r) }).collect();
        for l in &left {
            self.declared.insert(crate::decls::main_name(l));
        }
        let eq = if self.in_sum { " = " } else { " & = " };
        format!("{}{eq}{}", lhs.join(","), rhs.join(",")) + &label(self)
    }

    /// An expression, without the parentheses of a parenthesized whole.
    fn strip_parens(&mut self, e: &Val) -> String {
        if let Some(inner) = sub_expr(e) {
            return self.expr(&inner);
        }
        self.expr(e)
    }

    fn lhs(&mut self, l: &Val) -> String {
        match l.class() {
            // an elementwise definition: formatted as an indexing of what it defines
            "IdentifierSubscript" => {
                let name = ident_name(l.get("left"));
                let main = self.label(&name, &name, convert_name(&name));
                let subs: Vec<String> = self.subscripts(l).iter().map(|s| self.sub_name(s)).collect();
                // (the indexing form; for a matrix, only if already declared or defined)
                let ty = self.symbol_type(&name).filter(|t| !t.is_matrix() || self.declared.contains(&name));
                match ty {
                    Some(Ty::Matrix { .. }) if subs.len() == 2 => format!("{main}_{{{}, {}}}", subs[0], subs[1]),
                    Some(Ty::Vector { .. } | Ty::Seq { .. }) if subs.len() == 1 => format!("{main}_{{ {} }}", subs[0]),
                    _ => self.id_node(l),
                }
            }
            "IdentifierAlone" | "IdentifierSubscript" => self.id_node(l),
            _ => self.expr(l),
        }
    }

    fn local_func(&mut self, s: &Val) -> String {
        self.local_func = true;
        let extras = s.get("extra").items().to_vec();
        self.align_local = !extras.is_empty();
        let subs = s.get("subs").items().to_vec();
        let params = s.get("params").items().to_vec();
        let params_str = self.joined(&params, s.get("separators"), |p, x| p.id_node(x));
        let def_params = if s.get("def_p").truthy() {
            format!("\\left( {params_str} \\right)")
        } else if s.get("def_s").truthy() {
            format!("\\left[ {params_str} \\right]")
        } else {
            String::new()
        };
        let exprs: Vec<String> = self.sides(s.get("expr")).iter().map(|e| self.expr(e)).collect();
        let mut name = self.id_node(s.get("name"));
        if !subs.is_empty() {
            let sl: Vec<String> = subs.iter().map(|x| self.id_node(x)).collect();
            name = format!("{name}_{{{}}}", sl.join(","));
        }
        let mut content = format!("{name}{def_params} & = {}", exprs.join(", "));
        if !extras.is_empty() {
            content += "\\\\ & \\begin{aligned}[t]";
        }
        let defs = s.get("defs").items().to_vec();
        if !defs.is_empty() {
            let pars: Vec<String> = defs.iter().map(|d| self.where_condition(d)).collect();
            if !extras.is_empty() {
                content += &format!(" \\text{{ where }}& \\\\ {}", pars.join("\\\\ "));
            } else {
                content += &format!(" \\text{{{{ where }}}}  {}", pars.join(", "));
            }
        }
        if !extras.is_empty() {
            let ex: Vec<String> = extras.iter().map(|e| self.statement(e)).collect();
            content += &format!("\\\\{}\\end{{aligned}} ", ex.join("\\\\"));
        }
        self.local_func = false;
        self.align_local = false;
        content
    }

    /// A local function as MacroMathJax prints it (as the Python compiler
    /// does: parameters in brackets unless parenthesized, `where` inline, and
    /// labels of later symbols still naming this function).
    fn macro_local_func(&mut self, s: &Val) -> String {
        self.local_func = true;
        self.defining = true;
        let name = self.id_node(s.get("name"));
        self.defining = false;
        self.local_func_name = js_content(&ident_name(s.get("name")));
        let params: Vec<Val> = s.get("subs").items().iter().chain(s.get("params").items()).cloned().collect();
        let params_str = self.joined(&params, s.get("separators"), |p, x| p.id_node(x));
        let def_params = if s.get("def_p").truthy() { format!("\\left( {params_str} \\right)") } else { format!("\\left[ {params_str} \\right]") };
        let exprs: Vec<String> = self.sides(s.get("expr")).iter().map(|e| self.expr(e)).collect();
        let mut content = format!("{name}{def_params} & = {}", exprs.join(", "));
        let defs = s.get("defs").items().to_vec();
        if !defs.is_empty() {
            let pars: Vec<String> = defs.iter().map(|d| self.where_condition(d)).collect();
            content += &format!(" \\text{{{{ where }}}}  {}", pars.join(", "));
        }
        content
    }

    // -- identifiers ---------------------------------------------------------

    /// A name as written (with subscripts as `_{…}`), not an indexing.
    fn id_node(&mut self, n: &Val) -> String {
        match n.class() {
            "IdentifierAlone" => {
                let name = ident_name(n);
                self.label(&name, &name, convert_name(&name))
            }
            "IdentifierSubscript" => {
                let name = ident_name(n.get("left"));
                let subs: Vec<String> = self.subscripts(n).iter().map(|s| self.sub_name(s)).collect();
                let raw: Vec<String> = self.subscripts(n).iter().map(|s| s.as_str().map(str::to_string).unwrap_or_else(|| self.src(s))).collect();
                let full = format!("{name}_{}", raw.join(""));
                format!("{}_{{{}}}", self.label(&full, &name, convert_name(&name)), subs.join(","))
            }
            _ => self.expr(n),
        }
    }

    fn subscripts(&self, n: &Val) -> Vec<Val> {
        if n.get("exp").truthy() {
            n.get("exp").items().to_vec()
        } else {
            n.get("right").items().to_vec()
        }
    }

    fn sub_name(&mut self, s: &Val) -> String {
        if let Some(t) = s.as_str() {
            return t.to_string();
        }
        self.no_label += 1;
        let out = self.sub_name_inner(s);
        self.no_label -= 1;
        out
    }

    fn sub_name_inner(&mut self, s: &Val) -> String {
        match s.class() {
            "IdentifierAlone" => convert_name(&ident_name(s)),
            "Integer" | "SubInteger" | "SupInteger" => self.int_text(s),
            _ => self.expr(s),
        }
    }

    /// A subscripted name in an expression: an indexing, formatted by the
    /// type of what it indexes.
    fn indexing(&mut self, n: &Val) -> String {
        let name = ident_name(n.get("left"));
        let main = if name == "I" && !self.defined("I") { convert_name(&name) } else { self.label(&name, &name, convert_name(&name)) };
        let subs: Vec<String> = self.subscripts(n).iter().map(|s| self.sub_name(s)).collect();
        let base = span(n).and_then(|sp| self.prog.base_types.get(&sp));
        if base.is_none() && ident_name(n.get("left")) == "I" {
            return format!("I_{{ {} }}", subs.join(","));
        }
        match (base, subs.len()) {
            (Some(Ty::Matrix { .. }), 2) => format!("{main}_{{{}, {}}}", subs[0], subs[1]),
            (Some(Ty::Vector { .. }) | Some(Ty::Set { .. }) | Some(Ty::Tuple(_)), 1) => format!("{main}_{{ {} }}", subs[0]),
            (Some(Ty::Seq { .. }), 1) => format!("{main}_{{ {} }}", subs[0]),
            (Some(Ty::Seq { .. }), 2) => format!("{main}_{{ {}, {} }}", subs[0], subs[1]),
            (Some(Ty::Seq { .. }), 3) => format!("{main}_{{ {}, {}, {}}}", subs[0], subs[1], subs[2]),
            _ => format!("{main}_{{{}}}", subs.join(",")),
        }
    }

    // -- expressions ---------------------------------------------------------

    fn expr(&mut self, n: &Val) -> String {
        if let Some(s) = n.as_str() {
            return s.to_string();
        }
        match n.class() {
            "Expression" | "ExpInMatrix" => {
                let v = self.expr(n.get("value"));
                if n.get("sign").truthy() {
                    format!("{}{v}", n.get("sign").flat_text())
                } else {
                    v
                }
            }
            "Subexpression" => format!("\\left( {} \\right)", self.expr(n.get("value"))),
            "Factor" => self.factor(n),
            "Add" | "Subtract" => {
                let l = self.expr(n.get("left"));
                let r = self.expr(n.get("right"));
                let op = if n.class() == "Add" { "+" } else { "-" };
                if self.ty(n).is_some_and(|t| t.is_set()) {
                    let op = if op == "+" { " + " } else { "-" };
                    return format!("{l}{op}{r}");
                }
                format!("{l} {op} {r}")
            }
            "Multiply" => {
                let l = self.expr(n.get("left"));
                let r = self.expr(n.get("right"));
                if n.get("op").as_str() == Some("⋅") {
                    format!("{l} \\cdot {r}")
                } else {
                    format!("{l} {r}")
                }
            }
            "Divide" => {
                if n.get("op").as_str() == Some("÷") {
                    return format!("{}÷{}", self.expr(n.get("left")), self.expr(n.get("right")));
                }
                let l = self.strip_factor_parens(n.get("left"));
                let r = self.strip_factor_parens(n.get("right"));
                format!("\\frac{{{l}}}{{{r}}}")
            }
            "Intersection" => format!("{}\\cap{}", self.expr(n.get("left")), self.expr(n.get("right"))),
            "Union" => format!("{} \\cup {}", self.expr(n.get("left")), self.expr(n.get("right"))),
            "MultiCondExpr" => {
                let ifs = self.ifs(n.get("ifs"));
                if n.get("other").truthy() {
                    let o = self.expr(n.get("other"));
                    format!("\\begin{{cases}} {ifs} {o} & \\text{{otherwise}} \\end{{cases}}")
                } else {
                    format!("\\begin{{cases}} {ifs} \\end{{cases}} ")
                }
            }
            "Optimize" => self.optimize(n, None),
            "IdentifierAlone" => {
                let name = ident_name(n);
                self.label(&name, &name, convert_name(&name))
            }
            "IdentifierSubscript" => self.indexing(n),
            "Integer" | "SupInteger" | "SubInteger" => self.int_text(n),
            "Double" => py_float(&self.src(n)),
            "Fraction" => n.get("value").flat_text(),
            _ => self.operation(n),
        }
    }

    /// `(e)` as a fraction's numerator or denominator: without parentheses.
    fn strip_factor_parens(&mut self, n: &Val) -> String {
        if n.class() == "Factor" && n.get("sub").truthy() {
            return self.expr(n.get("sub").get("value"));
        }
        self.expr(n)
    }

    fn ifs(&mut self, n: &Val) -> String {
        let mut singles = Vec::new();
        collect_ifs(n, &mut singles);
        let mut s = String::new();
        for x in singles {
            let stat = self.expr(x.get("stat"));
            let cond = self.condition(x.get("cond"));
            s += &format!("{stat} & \\text{{if }}  {cond} \\\\");
        }
        s
    }

    fn factor(&mut self, n: &Val) -> String {
        for k in ["id0", "num", "sub", "m", "v", "s", "nm", "op", "c"] {
            let v = n.get(k);
            if !v.truthy() {
                continue;
            }
            return match k {
                "sub" => self.expr(v),
                "m" => format!("\\begin{{bmatrix}}\n{}\\end{{bmatrix}}", self.matrix_rows(v.get("value"))),
                "v" => {
                    let items: Vec<String> = v.get("exp").items().iter().map(|x| self.expr(x)).collect();
                    format!("\\begin{{pmatrix}}\n{}\\end{{pmatrix}}", items.join("\\\\"))
                }
                "s" => self.set_literal(v),
                "nm" => self.num_matrix(v),
                "c" => match v.class() {
                    "Pi" => "\\pi".into(),
                    "E" => "e".into(),
                    "Infinity" => "\\infty".into(),
                    _ => self.src(v),
                },
                _ => self.expr(v),
            };
        }
        self.src(n)
    }

    fn matrix_rows(&mut self, n: &Val) -> String {
        match n.class() {
            "MatrixRows" => {
                let mut s = String::new();
                if n.get("rs").truthy() {
                    s += &self.matrix_rows(n.get("rs"));
                }
                if n.get("r").truthy() {
                    s += &self.matrix_rows(n.get("r"));
                }
                s
            }
            "MatrixRow" => {
                let mut parts = Vec::new();
                if n.get("rc").truthy() {
                    parts.push(self.matrix_rows(n.get("rc")));
                }
                if n.get("exp").truthy() {
                    parts.push(self.expr(n.get("exp")));
                }
                parts.join(" & ") + "\\\\\n"
            }
            "MatrixRowCommas" => {
                let mut parts = Vec::new();
                if n.get("value").truthy() {
                    parts.push(self.matrix_rows(n.get("value")));
                }
                if n.get("exp").truthy() {
                    parts.push(self.expr(n.get("exp")));
                }
                parts.join(" & ")
            }
            _ => self.expr(n),
        }
    }

    fn set_literal(&mut self, n: &Val) -> String {
        let items: Vec<String> = self.sides(n.get("exp")).iter().map(|x| self.expr(x)).collect();
        let mut content = items.join(", ");
        if n.get("enum").truthy() {
            let e: Vec<String> = n.get("enum").items().iter().map(|x| special_marks(&ident_name(x))).collect();
            let range = self.expr(n.get("range"));
            content += &format!(" \\mid {}\\in {range}", e.join(","));
            if n.get("cond").truthy() {
                content += &format!(", {}", self.condition(n.get("cond")));
            }
        }
        format!("\\{{{content}\\}}")
    }

    fn num_matrix(&mut self, n: &Val) -> String {
        self.no_label += 1;
        let out = self.num_matrix_inner(n);
        self.no_label -= 1;
        out
    }

    fn num_matrix_inner(&mut self, n: &Val) -> String {
        let id1 = self.dim(n.get("id1"));
        let left = n.get("left").flat_text();
        if left == "I" {
            return format!("I_{{ {id1} }}");
        }
        let c = format!("\\mathbb{{ {left} }}");
        if n.get("id2").truthy() {
            format!("{c}_{{ {id1},{} }}", self.dim(n.get("id2")))
        } else {
            format!("{c}_{{ {id1} }}")
        }
    }

    fn condition(&mut self, c: &Val) -> String {
        match c.class() {
            "IfCondition" => {
                if c.get("single").truthy() {
                    return self.condition(c.get("single"));
                }
                // (literal braces, as in the Python compiler's output)
                format!("{} \\text{{{{ or }}}}{}", self.condition(c.get("se")), self.condition(c.get("other")))
            }
            "AndCondition" => {
                if c.get("atom").truthy() {
                    return self.condition(c.get("atom"));
                }
                format!("{} \\text{{{{ and }}}}{}", self.condition(c.get("se")), self.condition(c.get("other")))
            }
            "AtomCondition" => {
                if c.get("p").truthy() {
                    self.condition(c.get("p"))
                } else {
                    self.condition(c.get("cond"))
                }
            }
            "InCondition" | "NotInCondition" => {
                let items: Vec<String> = c.get("left").items().iter().map(|x| self.expr(x)).collect();
                let set = self.expr(c.get("right"));
                let op = if c.class() == "InCondition" { "\\in" } else { "\\notin" };
                if items.len() > 1 {
                    format!("\\left( {} \\right) {op} {set} ", items.join(", "))
                } else {
                    format!("{} {op} {set} ", items.join(", "))
                }
            }
            _ => {
                let op = c.get("op").flat_text();
                format!("{} {op} {}", self.expr(c.get("left")), self.expr(c.get("right")))
            }
        }
    }

    fn operation(&mut self, op: &Val) -> String {
        match op.class() {
            "Power" => {
                let base = self.expr(op.get("base"));
                let pw = op.get("power");
                let transpose = pw.class() == "IdentifierAlone" && pw.get("value").flat_text() == "ᵀ" && !self.defined("T");
                if op.get("t").truthy() || transpose {
                    return format!("{{{base}}}^T");
                }
                if op.get("r").truthy() {
                    return format!("{base}^{{-1}}");
                }
                let p = self.strip_factor_parens(op.get("power"));
                if is_norm(op.get("base")) {
                    format!("{base}^{{{p}}}")
                } else {
                    format!("{{{base}}}^{{{p}}}")
                }
            }
            "Transpose" => format!("{{{}}}^T", self.expr(op.get("f"))),
            "PseudoInverse" => format!("{{{}}}^+", self.expr(op.get("f"))),
            "Squareroot" => format!("\\sqrt{{{}}}", self.strip_factor_parens(op.get("value"))),
            "Solver" => {
                let (l, r) = (self.expr(op.get("left")), self.expr(op.get("right")));
                if self.ty(op.get("left")).is_some_and(|t| t.is_set()) {
                    return format!("{l}\\smallsetminus{r}");
                }
                if op.get("p").truthy() {
                    format!("{l}^{{-1}}{r}")
                } else {
                    format!("{l} \\smallsetminus {r}")
                }
            }
            "Norm" => self.norm(op),
            "Summation" => self.summation(op),
            "Function" => self.call(op),
            "Integral" => {
                let (lo, hi) = if op.get("d").truthy() {
                    (self.expr(op.get("d").get("lower")), self.expr(op.get("d").get("upper")))
                } else {
                    (self.expr(op.get("lower")), self.expr(op.get("upper")))
                };
                let e = self.expr(op.get("exp"));
                let b = self.expr(op.get("id"));
                format!("\\int_{{{lo}}}^{{{hi}}} {e} d{b}")
            }
            "InnerProduct" => {
                let c = format!("\\langle {} , {}\\rangle", self.expr(op.get("left")), self.expr(op.get("right")));
                if op.get("sub").truthy() {
                    format!("{{{c}}}_{}", self.expr(op.get("sub")))
                } else {
                    c
                }
            }
            "FroProduct" => format!("{} : {}", self.expr(op.get("left")), self.expr(op.get("right"))),
            "HadamardProduct" => format!("{} \\circ {}", self.expr(op.get("left")), self.expr(op.get("right"))),
            "CrossProduct" => format!("{} × {}", self.expr(op.get("left")), self.expr(op.get("right"))),
            "KroneckerProduct" => format!("{} \\otimes {}", self.expr(op.get("left")), self.expr(op.get("right"))),
            "DotProduct" => format!("{} \\cdot {}", self.expr(op.get("left")), self.expr(op.get("right"))),
            "SizeOp" => format!("\\#{}", self.expr(op.get("p"))),
            "ElementConvertFunc" => {
                let name = ["e", "es", "f", "fs", "s", "se", "t", "ts", "tu", "v", "vs"]
                    .iter()
                    .map(|k| op.get(k))
                    .find(|v| v.truthy())
                    .map(|v| v.flat_text())
                    .unwrap_or_default();
                let params = op.get("params").items().to_vec();
                let p = self.joined(&params, op.get("separators"), |s, x| s.expr(x));
                format!("\\textit{{{name}}}({p})")
            }
            cls if cls.ends_with("Func") => self.builtin(op),
            _ => self.src(op),
        }
    }

    fn norm(&mut self, op: &Val) -> String {
        let v = self.expr(op.get("value"));
        let ty = self.ty(op.get("value")).cloned();
        let sub = op.get("sub");
        let mut content = match &ty {
            Some(t) if t.is_scalar() || t.is_set() => format!("\\left|{v}\\right|"),
            _ if op.get("single").truthy() => format!("\\left|{v}\\right|"),
            Some(Ty::Vector { .. }) => {
                let mut c = format!("\\left\\|{v}\\right\\|");
                if sub.truthy() {
                    let s = sub.as_str().map(str::to_string).unwrap_or_else(|| self.src(sub));
                    if s == "∞" {
                        c += "_\\infty";
                    } else if matches!(sub.class(), "Integer" | "SubInteger") {
                        c += &format!("_{}", self.int_text(sub));
                    } else {
                        c += &format!("_{{{}}}", self.expr(sub));
                    }
                }
                c
            }
            Some(Ty::Matrix { .. }) => {
                let mut c = format!("\\left\\|{v}\\right\\|");
                match sub.as_str() {
                    Some("*") => c += "_*",
                    _ if sub.truthy() => c += "_F",
                    _ => {}
                }
                c
            }
            _ => format!("\\left\\|{v}\\right\\|"),
        };
        if op.get("power").truthy() {
            content = format!("{content}^{{{}}}", self.int_or_expr(op.get("power")));
        }
        content
    }

    fn int_or_expr(&mut self, n: &Val) -> String {
        match n.class() {
            "Integer" | "SupInteger" | "SubInteger" => self.int_text(n),
            _ => self.expr(n),
        }
    }

    fn summation(&mut self, op: &Val) -> String {
        let s = self.summation_inner(op);
        // ∪_(i ∈ S): the same notation with a big cup
        if op.get("u").truthy() {
            return s.replacen("\\sum_", "\\bigcup_", 1);
        }
        s
    }

    fn summation_inner(&mut self, op: &Val) -> String {
        let saved = self.in_sum;
        self.in_sum = true;
        let mut content = if op.get("cond").truthy() {
            format!("\\sum_{{{}}}", self.condition(op.get("cond")))
        } else if op.get("enum").truthy() {
            let e: Vec<String> = op.get("enum").items().iter().map(|x| convert_name(&ident_name(x))).collect();
            let range = self.expr(op.get("range"));
            format!("\\sum_{{{}\\in {range}}} ", e.join(","))
        } else if op.get("lower").truthy() {
            let id = if op.get("id").truthy() { op.get("id") } else { op.get("sub") };
            let s = self.id_node(id);
            let lo = self.expr(op.get("lower"));
            let hi = self.int_or_expr(op.get("upper"));
            format!("\\sum_{{{s}={lo}}}^{{ {hi}}}")
        } else {
            let id = if op.get("id").truthy() { op.get("id") } else { op.get("sub") };
            self.no_label += 1;
            let s = self.id_node(id);
            self.no_label -= 1;
            format!("\\sum_{{{s}}} ")
        };
        if op.get("sign").truthy() {
            content += &op.get("sign").flat_text();
        }
        content += &self.expr(op.get("exp"));
        let extras = op.get("extra").items().to_vec();
        if !extras.is_empty() {
            let ex: Vec<String> = extras.iter().map(|e| self.statement(e)).collect();
            content += &format!(" \\qquad \\text{{{{ where }}}}  {}", ex.join(", "));
        }
        self.in_sum = saved;
        content
    }

    fn call(&mut self, op: &Val) -> String {
        let subs = op.get("subs").items().to_vec();
        let params = op.get("params").items().to_vec();
        let params_str = self.joined(&params, op.get("separators"), |s, x| s.expr(x));
        let name = op.get("name");
        if let Some(raw) = name.as_str() {
            if self.mesh_funcs.contains(&crate::decls::strip_backticks(raw)) {
                let p: Vec<String> = params.iter().map(|x| self.expr(x)).collect();
                let n = raw.replace('_', "\\_");
                let n = if n.chars().count() > 1 { format!("\\mathit{{{n}}}") } else { n };
                return format!("{n}({})", p.join(", "));
            }
        }
        // a function's name as written: backticked names print as text
        let mut content = match name.as_str() {
            Some(raw) => {
                let n = crate::decls::strip_backticks(raw);
                self.label(&n, &n, convert_name(&n))
            }
            None => self.id_node(name),
        };
        if !subs.is_empty() {
            let sl: Vec<String> = subs.iter().map(|x| self.expr(x)).collect();
            content = format!("{content}_{{{}}}", sl.join(","));
        }
        if params.is_empty() && !op.get("p").truthy() {
            return content;
        }
        format!("{content}\\left( {params_str} \\right)")
    }

    fn builtin(&mut self, op: &Val) -> String {
        let cls = op.class();
        let param = self.expr(op.get("param"));
        let name = if op.get("name").truthy() { op.get("name").flat_text() } else { String::new() };
        let f = |s: &str| format!("{s}\\left( {param} \\right)");
        let base = match cls {
            "SinFunc" => f("sin"),
            "CosFunc" => f("cos"),
            "TanFunc" => f("tan"),
            "SinhFunc" => f("sinh"),
            "CoshFunc" => f("cosh"),
            "TanhFunc" => f("tanh"),
            "CotFunc" => f("cot"),
            "SecFunc" => f("sec"),
            "CscFunc" => f("csc"),
            "AsinFunc" | "AcosFunc" | "AtanFunc" | "AsinhFunc" | "AcoshFunc" | "AtanhFunc" | "TraceFunc" => f(&name),
            "Atan2Func" => {
                let second = self.expr(op.get("second"));
                format!("atan2\\left( {param}{} {second} \\right)", op.get("separator").flat_text())
            }
            "ExpFunc" => return format!("e^{{{param}}}"),
            "LogFunc" => {
                return if op.get("f").truthy() {
                    format!(" \\log_2{{ {param} }}")
                } else if op.get("s").truthy() {
                    format!(" \\log_{{10}}{{ {param} }}")
                } else {
                    format!(" \\log{{ {param} }}")
                }
            }
            "LnFunc" => return format!(" \\ln{{ {param} }}"),
            "SqrtFunc" => return format!(" \\sqrt{{ {param} }}"),
            "DiagFunc" => f(" \\mathop{\\text{diag}}"),
            "VecFunc" => f(" \\mathop{\\text{vec}}"),
            "DetFunc" => f(" \\mathop{\\text{det}}"),
            "RankFunc" => f(" \\mathop{\\text{rank}}"),
            "NullFunc" => f(" \\mathop{\\text{null}}"),
            "OrthFunc" => f(" \\mathop{\\text{orth}}"),
            "InvFunc" => f(" \\mathop{\\text{inv}}"),
            "SvdFunc" => f(" \\mathop{\\text{svd}}"),
            _ => f(&special_marks(&name)),
        };
        if op.get("power").truthy() {
            return format!("{{{base}}}^{{{}}}", self.int_or_expr(op.get("power")));
        }
        base
    }

    fn optimize(&mut self, n: &Val, lhs: Option<String>) -> String {
        let cat = if n.get("min").truthy() {
            "\\min"
        } else if n.get("max").truthy() {
            "\\max"
        } else if n.get("amin").truthy() {
            "\\argmin"
        } else {
            "\\argmax"
        };
        let mut content = "\\begin{aligned} ".to_string();
        if let Some(l) = lhs {
            content += &format!("{l} = ");
        }
        self.no_label += 1;
        let defs: Vec<String> = n.get("defs").items().iter().map(|d| self.where_condition(d)).collect();
        self.no_label -= 1;
        let e = self.expr(n.get("exp"));
        content += &format!("{cat}_{{{}}} \\quad & {e} \\\\\n", defs.join(", ").replace('&', ""));
        let mut conds = Vec::new();
        let mut cur = n.get("cond").clone();
        while cur.truthy() {
            conds.push(cur.get("cond").clone());
            cur = cur.get("m_cond").clone();
        }
        conds.reverse();
        if !conds.is_empty() {
            content += "\\textrm{s.t.} \\quad &";
            let cs: Vec<String> = conds.iter().map(|c| self.condition(c)).collect();
            content += &cs.join("\\\\\n & ");
            content += "\n";
        }
        content + "\\end{aligned}"
    }
}

fn digits(s: &str, f: fn(char) -> Option<i64>) -> String {
    s.chars().map(|c| f(c).map(|d| char::from_digit(d as u32, 10).unwrap()).unwrap_or(c)).collect()
}

fn collect_ifs(n: &Val, out: &mut Vec<Val>) {
    if n.is_seq() {
        for x in n.items() {
            collect_ifs(x, out);
        }
        return;
    }
    match n.class() {
        "SingleIf" => out.push(n.clone()),
        "MultiIfs" => {
            collect_ifs(n.get("ifs"), out);
            collect_ifs(n.get("value"), out);
        }
        _ => {}
    }
}

/// The parenthesized expression of `(e)` (an Expression whose value is a
/// parenthesized factor).
fn sub_expr(e: &Val) -> Option<Val> {
    if e.class() == "Expression" && !e.get("sign").truthy() {
        let f = e.get("value");
        if f.class() == "Factor" && f.get("sub").truthy() {
            return Some(f.get("sub").get("value").clone());
        }
    }
    None
}

fn optimize_node(e: &Val) -> Option<Val> {
    if e.class() == "Optimize" {
        return Some(e.clone());
    }
    if e.class() == "Expression" && !e.get("sign").truthy() {
        let v = e.get("value");
        if v.class() == "Optimize" {
            return Some(v.clone());
        }
        if v.class() == "Factor" && v.get("op").class() == "Optimize" {
            return Some(v.get("op").clone());
        }
    }
    None
}

fn is_norm(e: &Val) -> bool {
    match e.class() {
        "Norm" => true,
        "Factor" => e.get("op").class() == "Norm",
        "Expression" => !e.get("sign").truthy() && is_norm(e.get("value")),
        _ => false,
    }
}

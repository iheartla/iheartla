//! I❤️LA compiler.
//!
//! Pipeline: `grammar` parses the source twice (the first parse, with the
//! simplified grammar, feeds `decls`, which finds declared names; the
//! second parse uses the full grammar), `check` turns the parse tree into a
//! typed `ast::Program`, and the backends in `back` generate code.

pub mod ast;
pub mod back;
pub mod check;
pub mod decls;
pub mod dims;
pub mod grammar;
pub mod helper;
pub mod modules;
pub mod peg;
pub mod pnode;
pub mod ty;

/// Map byte offsets in `text` to character offsets (Python string indices).
pub fn char_offsets(text: &str) -> Vec<usize> {
    let mut map = vec![0; text.len() + 1];
    let mut n = 0;
    for (i, c) in text.char_indices() {
        for k in 0..c.len_utf8() {
            map[i + k] = n;
        }
        n += 1;
    }
    map[text.len()] = n;
    map
}

/// The source text of a parse node.
pub fn node_text<'a>(src: &'a str, node: &pnode::Val) -> &'a str {
    match node.node().and_then(|n| n.span) {
        Some((a, b)) => &src[a..b],
        None => "",
    }
}

/// Format a parse error like the Python compiler.
fn parse_error_message(src: &str, e: &peg::ParseError) -> String {
    let source = helper::Source::new(src);
    let pos = source.char_of_byte(e.pos);
    let li = source.line_info(pos);
    let rule = e.stack.iter().find_map(|r| rule_description(r)).unwrap_or("None");
    let mut text = li.text.clone();
    if !text.ends_with('\n') {
        text.push('\n');
    }
    format!(
        "{}. Failed to parse {}: {}\n{}{}",
        helper::get_line_desc(&li),
        rule,
        e.message,
        text,
        helper::get_pos_marker(li.col)
    )
}

fn rule_description(rule: &str) -> Option<&'static str> {
    Some(match rule {
        "identifier_alone" => "identifier",
        "statements" => "statement",
        "where_conditions" => "where conditions",
        "where_condition" => "where condition",
        "matrix_type" => "matrix type",
        "vector_type" => "vector type",
        "scalar_type" => "scalar type",
        "expression" => "expression",
        "matrix" => "matrix",
        "addition" => "addition",
        "multiplication" => "multiplication",
        "power_operator" => "power",
        "sum_operator" => "sum",
        "norm_operator" => "norm",
        "function_operator" => "function",
        _ => return None,
    })
}

/// Parse a program (both passes) and check it: the second parse tree and
/// the typed program.
pub fn front_end(src: &str) -> Result<(pnode::Val, ast::Program), String> {
    let dir = std::env::current_dir().map(|d| vec![d]).unwrap_or_default();
    front_end_with(src, &modules::Loader::new(dir))
}

/// The front end, with modules found and compiled by `loader`.
pub fn front_end_with(src: &str, loader: &std::rc::Rc<modules::Loader>) -> Result<(pnode::Val, ast::Program), String> {
    let first = grammar::parse_init(src).map_err(|e| parse_error_message(src, &e))?;
    let config = decls::second_parse_config_with(&first, &|n| node_text(src, n).to_string(), &|m| loader.function_names(m));
    let tree = grammar::parse_default(src, &config).map_err(|e| parse_error_message(src, &e))?;
    let prog = check::Checker::new(src).with_loader(loader.clone()).check(&tree).map_err(|e| e.message)?;
    Ok((tree, prog))
}

/// Parse and check a program.
pub fn check_source(src: &str) -> Result<ast::Program, String> {
    front_end(src).map(|(_, p)| p)
}

/// Compile to a LaTeX document.
pub fn compile_latex(src: &str) -> Result<String, String> {
    let (tree, prog) = front_end(src)?;
    Ok(back::latex::generate(&prog, &tree, back::latex::Flavor::Latex))
}

/// Compile to MATLAB (or Octave) code.
pub fn compile_matlab(src: &str, func_name: &str) -> Result<String, String> {
    let prog = check_source(src)?;
    Ok(back::matlab::generate(&prog, func_name))
}

/// Compile to MathJax for H❤️rtDown (with click handlers).
pub fn compile_macromathjax(src: &str) -> Result<String, String> {
    let (tree, prog) = front_end(src)?;
    Ok(back::latex::generate(&prog, &tree, back::latex::Flavor::MacroMathjax))
}

/// Compile to MathJax (an `align*` block).
pub fn compile_mathjax(src: &str) -> Result<String, String> {
    let (tree, prog) = front_end(src)?;
    Ok(back::latex::generate(&prog, &tree, back::latex::Flavor::Mathjax))
}

/// Compile to NumPy (Python) code.
pub fn compile_numpy(src: &str, class_name: &str) -> Result<String, String> {
    let prog = check_source(src)?;
    Ok(back::numpy::generate(&prog, class_name))
}

/// Compile to C++/Eigen code.
pub fn compile_eigen(src: &str, struct_name: &str) -> Result<String, String> {
    let prog = check_source(src)?;
    Ok(back::eigen::generate(&prog, struct_name))
}

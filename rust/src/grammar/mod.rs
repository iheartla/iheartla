//! The two grammars of I❤LA: `init` (the simplified grammar used for a first
//! pass that collects declared names) and `default` (the full grammar).

#[allow(non_snake_case, unused_variables, unused_mut, clippy::all)]
pub mod default;
#[allow(non_snake_case, unused_variables, unused_mut, clippy::all)]
pub mod init;
#[allow(non_snake_case)]
pub mod special;

use crate::peg::{Grammar, ParseError, Parser, ParserConfig};
use crate::pnode::Val;
use regex::Regex;
use std::sync::OnceLock;

static INIT_RE: OnceLock<Vec<Regex>> = OnceLock::new();
static DEFAULT_RE: OnceLock<Vec<Regex>> = OnceLock::new();

pub static INIT: Grammar = Grammar {
    rules: &init::RULES,
    patterns: &init::PATTERNS,
    compiled: &INIT_RE,
    start: init::R_START,
};

pub static DEFAULT: Grammar = Grammar {
    rules: &default::RULES,
    patterns: &default::PATTERNS,
    compiled: &DEFAULT_RE,
    start: default::R_START,
};

/// First pass: parse with the simplified grammar.
pub fn parse_init(text: &str) -> Result<Val, ParseError> {
    let config = ParserConfig::default();
    Parser::new(text, &INIT, &config).parse()
}

/// Second pass: parse with the full grammar, configured with declared names.
pub fn parse_default(text: &str, config: &ParserConfig) -> Result<Val, ParseError> {
    Parser::new(text, &DEFAULT, config).parse()
}

//! Rules of the full grammar that read the parser configuration. The Python
//! compiler patched these by hand into its TatSu-generated default parser
//! (iheartla/la_local_parsers/default_parser.py); this is a line-by-line port.

use super::default::*;
use crate::peg::{PResult, Parser};

const ID_ALONE: &str = r"[A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*";

/// `func_id`: the declared function names, or nothing (`'!!!'`).
pub fn default_func_id(p: &mut Parser) -> PResult {
    if !p.config.funcs.is_empty() {
        let funcs = p.config.funcs.clone();
        p.choice(|p| {
            for f in &funcs {
                if p.option(|p| p.dyn_pattern(f)) {
                    return Ok(());
                }
            }
            Err(p.error("no available options"))
        })
    } else {
        p.token("!!!")
    }
}

/// The default single-letter identifier, or a backticked one.
fn letter_or_backticks(p: &mut Parser) -> PResult {
    p.choice(|p| {
        if p.option(|p| {
            p.group(|p| p.dyn_pattern(ID_ALONE))?;
            p.name_last_node("value");
            Ok(())
        }) {
            return Ok(());
        }
        if p.option(|p| {
            p.token("`")?;
            p.dyn_pattern("[^`]*")?;
            p.name_last_node("id");
            p.token("`")?;
            p.define(&["id"], &[]);
            Ok(())
        }) {
            return Ok(());
        }
        Err(p.error("expecting one of: '`' [A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*"))
    })
}

/// `identifier_alone`: a declared multi-letter identifier (`const`), or a
/// single letter that does not begin a keyword or a declared identifier.
pub fn default_identifier_alone(p: &mut Parser) -> PResult {
    let ids = p.config.ids.clone();
    if !ids.is_empty() {
        p.choice(|p| {
            if p.option(|p| {
                p.group(|p| {
                    p.choice(|p| {
                        for id in &ids {
                            if p.option(|p| p.dyn_pattern(id)) {
                                return Ok(());
                            }
                        }
                        Err(p.error("no available options"))
                    })
                })?;
                p.name_last_node("const");
                Ok(())
            }) {
                return Ok(());
            }
            if p.option(|p| {
                p.ifnot(|p| {
                    p.group(|p| {
                        p.choice(|p| {
                            if p.option(|p| p.call(R_KEYWORDS_U)) {
                                return Ok(());
                            }
                            for id in &ids {
                                if p.option(|p| p.dyn_pattern(id)) {
                                    return Ok(());
                                }
                            }
                            Err(p.error("no available options"))
                        })
                    })
                })?;
                p.group(|p| letter_or_backticks_ids(p))?;
                p.define(&["id", "value"], &[]);
                Ok(())
            }) {
                return Ok(());
            }
            if p.option(|p| {
                p.group(|p| {
                    p.choice(|p| {
                        if p.option(|p| p.call(R_PREFIX_KEYWORD_U)) {
                            return Ok(());
                        }
                        for id in &ids {
                            if p.option(|p| p.dyn_pattern(id)) {
                                return Ok(());
                            }
                        }
                        Err(p.error("no available options"))
                    })?;
                    p.group(|p| p.dyn_pattern(ID_ALONE))
                })?;
                p.name_last_node("value");
                Ok(())
            }) {
                return Ok(());
            }
            Err(p.error("expecting one of: <KEYWORDS> <PREFIX_KEYWORD>"))
        })?;
        p.define(&["const", "id", "value"], &[]);
        Ok(())
    } else {
        p.choice(|p| {
            if p.option(|p| {
                p.ifnot(|p| p.call(R_KEYWORDS_U))?;
                p.group(letter_or_backticks)?;
                p.define(&["id", "value"], &[]);
                Ok(())
            }) {
                return Ok(());
            }
            if p.option(|p| {
                p.group(|p| {
                    p.call(R_PREFIX_KEYWORD_U)?;
                    p.group(|p| p.dyn_pattern(ID_ALONE))
                })?;
                p.name_last_node("value");
                Ok(())
            }) {
                return Ok(());
            }
            Err(p.error("expecting one of: <KEYWORDS> <PREFIX_KEYWORD>"))
        })
    }
}

/// In the patched rule, the backticked alternative defines only `id`.
fn letter_or_backticks_ids(p: &mut Parser) -> PResult {
    p.choice(|p| {
        if p.option(|p| {
            p.group(|p| p.dyn_pattern(ID_ALONE))?;
            p.name_last_node("value");
            Ok(())
        }) {
            return Ok(());
        }
        if p.option(|p| {
            p.token("`")?;
            p.dyn_pattern("[^`]*")?;
            p.name_last_node("id");
            p.token("`")?;
            p.define(&["id"], &[]);
            Ok(())
        }) {
            return Ok(());
        }
        Err(p.error("expecting one of: '`' [A-Za-z\\p{Ll}\\p{Lu}\\p{Lo}]\\p{M}*"))
    })
}

/// `builtin_operators`: imported builtin functions, then the predefined ones.
pub fn default_builtin_operators(p: &mut Parser) -> PResult {
    if !p.config.builtins.is_empty() {
        let builtins = p.config.builtins.clone();
        p.choice(|p| {
            for b in &builtins {
                if p.option(|p| p.call_named(b)) {
                    return Ok(());
                }
            }
            if p.option(|p| p.call(R_PREDEFINED_BUILT_OPERATORS)) {
                return Ok(());
            }
            Err(p.error("no available options"))
        })
    } else {
        p.call(R_PREDEFINED_BUILT_OPERATORS)
    }
}

/// `constant`: π and ∞, and e when imported.
pub fn default_constant(p: &mut Parser) -> PResult {
    let const_e = p.config.const_e;
    p.choice(|p| {
        if p.option(|p| p.call(R_PI)) {
            return Ok(());
        }
        if p.option(|p| p.call(R_INFINITY)) {
            return Ok(());
        }
        if const_e && p.option(|p| p.call(R_E)) {
            return Ok(());
        }
        Err(p.error(if const_e { "no available options" } else { "expecting one of: <infinity> <pi> π ∞" }))
    })
}

/// `KEYWORDS`: the builtin keywords, and e when imported.
pub fn default_KEYWORDS(p: &mut Parser) -> PResult {
    if p.config.const_e {
        p.choice(|p| {
            if p.option(|p| p.call(R_BUILTIN_KEYWORDS_U)) {
                return Ok(());
            }
            if p.option(|p| p.call(R_E)) {
                return Ok(());
            }
            Err(p.error("no available options"))
        })
    } else {
        p.call(R_BUILTIN_KEYWORDS_U)
    }
}

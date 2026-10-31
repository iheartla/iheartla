//! Helpers from la_tools/la_helper.py and la_tools/la_msg.py: Python string
//! predicates, source positions and error messages, Unicode tables.

use regex::Regex;
use std::cell::RefCell;
use std::fmt;
use std::rc::Rc;
use std::sync::OnceLock;

// -- Python str predicates (per character) ----------------------------------

fn char_re(re: &'static OnceLock<Regex>, pat: &str, c: char) -> bool {
    let re = re.get_or_init(|| Regex::new(pat).unwrap());
    let mut buf = [0u8; 4];
    re.is_match(c.encode_utf8(&mut buf))
}

/// `str.isalpha()` for one character (Unicode letters).
pub fn py_isalpha(c: char) -> bool {
    if c.is_ascii() {
        return c.is_ascii_alphabetic();
    }
    static RE: OnceLock<Regex> = OnceLock::new();
    char_re(&RE, r"^\p{L}$", c)
}

/// `str.isnumeric()` for one character (Unicode numbers, e.g. '²', '½').
pub fn py_isnumeric(c: char) -> bool {
    if c.is_ascii() {
        return c.is_ascii_digit();
    }
    static RE: OnceLock<Regex> = OnceLock::new();
    char_re(&RE, r"^\p{N}$", c)
}

/// `str.isdigit()` for one character.
pub fn py_isdigit(c: char) -> bool {
    if c.is_ascii() {
        return c.is_ascii_digit();
    }
    static RE: OnceLock<Regex> = OnceLock::new();
    // decimal digits plus superscript/subscript digits (Numeric_Type=Digit)
    char_re(&RE, r"^\p{Nd}$", c) || "⁰¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉".contains(c)
}

/// `str.isalnum()` for one character.
pub fn py_isalnum(c: char) -> bool {
    py_isalpha(c) || py_isnumeric(c)
}

/// `str.isspace()` for one character.
pub fn py_isspace(c: char) -> bool {
    c.is_whitespace() || matches!(c, '\x1c'..='\x1f')
}

/// `s.isnumeric()` for a string (false when empty).
pub fn str_isnumeric(s: &str) -> bool {
    !s.is_empty() && s.chars().all(py_isnumeric)
}

/// `s.isdigit()`
pub fn str_isdigit(s: &str) -> bool {
    !s.is_empty() && s.chars().all(py_isdigit)
}

/// `s.isalnum()`
pub fn str_isalnum(s: &str) -> bool {
    !s.is_empty() && s.chars().all(py_isalnum)
}

/// Python's `str.splitlines(True)`.
pub fn splitlines_keep(text: &str) -> Vec<String> {
    let mut lines = Vec::new();
    let mut cur = String::new();
    let mut chars = text.chars().peekable();
    while let Some(c) = chars.next() {
        cur.push(c);
        let brk = match c {
            '\r' => {
                if chars.peek() == Some(&'\n') {
                    cur.push(chars.next().unwrap());
                }
                true
            }
            '\n' | '\x0b' | '\x0c' | '\x1c' | '\x1d' | '\x1e' | '\u{85}' | '\u{2028}' | '\u{2029}' => true,
            _ => false,
        };
        if brk {
            lines.push(std::mem::take(&mut cur));
        }
    }
    if !cur.is_empty() {
        lines.push(cur);
    }
    lines
}

// -- source text and positions ----------------------------------------------

/// A source text, with TatSu's per-character line cache.
pub struct Source {
    pub text: String,
    chars: Vec<char>,
    /// byte offset of each character (and of the end)
    byte_of: Vec<usize>,
    /// (line start, line number, line length) per character, plus a sentinel
    line_cache: Vec<(usize, usize, usize)>,
}

impl fmt::Debug for Source {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Source({} chars)", self.chars.len())
    }
}

impl Source {
    pub fn new(text: &str) -> Rc<Source> {
        let chars: Vec<char> = text.chars().collect();
        let mut byte_of = Vec::with_capacity(chars.len() + 1);
        for (b, _) in text.char_indices() {
            byte_of.push(b);
        }
        byte_of.push(text.len());
        let mut line_cache = Vec::with_capacity(chars.len() + 1);
        let mut i = 0;
        let lines = splitlines_keep(text);
        for (n, line) in lines.iter().enumerate() {
            let len = line.chars().count();
            for _ in 0..len {
                line_cache.push((i, n, len));
            }
            i += len;
        }
        let mut n = lines.len();
        if lines.last().is_some_and(|l| l.ends_with('\r') || l.ends_with('\n')) {
            n += 1;
        }
        line_cache.push((i, n, 0));
        Rc::new(Source { text: text.to_string(), chars, byte_of, line_cache })
    }

    pub fn len_chars(&self) -> usize {
        self.chars.len()
    }

    /// Text between character offsets.
    pub fn slice(&self, pos: usize, endpos: usize) -> &str {
        let a = self.byte_of[pos.min(self.chars.len())];
        let b = self.byte_of[endpos.min(self.chars.len())];
        &self.text[a..b]
    }

    /// Character offset of a byte offset.
    pub fn char_of_byte(&self, byte: usize) -> usize {
        self.byte_of.partition_point(|&b| b < byte)
    }

    /// TatSu's `Buffer.line_info(pos)`.
    pub fn line_info(&self, pos: usize) -> LineInfo {
        let last = self.line_cache.len() as isize - 2;
        let p = (pos as isize).min(last);
        let (start, line, length) = if p < 0 {
            *self.line_cache.last().unwrap()
        } else {
            self.line_cache[p as usize]
        };
        let end = start + length;
        let col = if p < 0 { 0 } else { p as usize - start };
        LineInfo { line, col, start, end, text: self.slice(start, end).to_string() }
    }
}

#[derive(Clone, Debug)]
pub struct LineInfo {
    pub line: usize,
    pub col: usize,
    pub start: usize,
    pub end: usize,
    pub text: String,
}

/// TatSu's `ParseInfo`: where a node came from (character offsets).
#[derive(Clone, Debug)]
pub struct ParseInfo {
    pub src: Rc<Source>,
    pub pos: usize,
    pub endpos: usize,
}

impl ParseInfo {
    pub fn text(&self) -> &str {
        self.src.slice(self.pos, self.endpos)
    }
    pub fn line_info(&self) -> LineInfo {
        self.src.line_info(self.pos)
    }
}

// -- error messages (la_msg.py) ---------------------------------------------

thread_local! {
    /// LaMsg singleton state (only `cur_msg`/`cur_code` are read, by the GUI).
    pub static LA_MSG: RefCell<(String, String)> = const { RefCell::new((String::new(), String::new())) };
}

pub fn get_line_desc(line_info: &LineInfo) -> String {
    format!("Error on line {} at column {}", line_info.line + 1, line_info.col + 1)
}

pub fn get_line_desc_with_col(line: usize, col: usize) -> String {
    format!("Error on line {} at column {}", line + 1, col + 1)
}

pub fn get_pos_marker(column: usize) -> String {
    format!("{}^\n", " ".repeat(column))
}

/// `get_err_msg(line_info, col, error_msg)`
pub fn get_err_msg(line_info: &LineInfo, col: usize, error_msg: &str) -> String {
    let line_msg = get_line_desc_with_col(line_info.line, col);
    let mut raw_text = line_info.text.clone();
    if !raw_text.ends_with('\n') {
        raw_text.push('\n');
    }
    LA_MSG.with(|m| *m.borrow_mut() = (error_msg.to_string(), line_info.text.clone()));
    format!("{}. {}.\n{}{}", line_msg, error_msg, raw_text, get_pos_marker(col))
}

/// `get_err_msg_info(parse_info, error_msg)`
pub fn get_err_msg_info(parse_info: Option<&ParseInfo>, error_msg: &str) -> String {
    match parse_info {
        Some(pi) => {
            let li = pi.line_info();
            get_err_msg(&li, li.col, error_msg)
        }
        None => error_msg.to_string(),
    }
}

/// Python's `str.find(sub)` as a character index (-1 when absent), used for
/// error-marker columns.
pub fn py_find(haystack: &str, needle: &str) -> isize {
    match haystack.find(needle) {
        Some(b) => haystack[..b].chars().count() as isize,
        None => -1,
    }
}

/// A column computed with `str.find` (which may be -1; Python then puts the
/// marker at column -1, i.e. no spaces, and reports column 0).
pub fn find_col(haystack: &str, needle: &str, offset: isize) -> usize {
    (py_find(haystack, needle) + offset).max(0) as usize
}

// -- names and identifiers (la_helper.py) -----------------------------------

const PY_KEYWORDS: &[&str] = &[
    "False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del",
    "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
];

const CPP_KEYWORDS: &str = "Asm auto bool break case catch char class const_cast continue default delete do double else \
                enum dynamic_cast extern false float for union unsigned using friend goto if \
                inline int long mutable virtual namespace new operator private protected public \
                register void reinterpret_cast return short signed sizeof static static_cast volatile \
                struct switch template this throw true try typedef typeid unsigned wchar_t while";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum KeywordSet {
    Numpy,
    Eigen,
    Both,
}

/// `is_keyword(name, parser_type)`. The C++ list is split on single spaces
/// as in Python, so it contains empty strings and words only.
pub fn is_keyword(name: &str, set: KeywordSet) -> bool {
    match set {
        KeywordSet::Numpy => PY_KEYWORDS.contains(&name),
        KeywordSet::Eigen => CPP_KEYWORDS.split(' ').any(|k| k == name),
        KeywordSet::Both => is_keyword(name, KeywordSet::Numpy) || is_keyword(name, KeywordSet::Eigen),
    }
}

fn backtick_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| Regex::new("`[^`]*`").unwrap())
}

/// `contains_sub_symbol(identifier)`
pub fn contains_sub_symbol(identifier: &str) -> bool {
    if identifier.contains('`') {
        let mut new_id = identifier.to_string();
        for m in backtick_re().find_iter(identifier) {
            new_id = new_id.replace(m.as_str(), "");
        }
        return new_id.contains('_');
    }
    identifier.contains('_')
}

/// `split_sub_string(identifier)`
pub fn split_sub_string(identifier: &str) -> Vec<String> {
    if identifier.contains('`') {
        let mut new_id = identifier.to_string();
        let mut convert: Vec<(String, String)> = Vec::new();
        for m in backtick_re().find_iter(identifier) {
            let item = m.as_str();
            if item.contains('_') {
                let new_item = item.replace('_', "``");
                convert.push((new_item.clone(), item.to_string()));
                new_id = new_id.replace(item, &new_item);
            }
        }
        let mut results: Vec<String> = new_id.split('_').map(String::from).collect();
        for r in results.iter_mut() {
            if let Some((_, orig)) = convert.iter().find(|(k, _)| k == r) {
                *r = orig.clone();
            }
        }
        return results;
    }
    identifier.split('_').map(String::from).collect()
}

fn block_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"^(?P<main>(`[^`]*`)|([A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)(_)(?P<sub>((`[^`]*`)|([A-Za-z0-9\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)|(,)|(\*)?)+)$").unwrap()
    })
}

fn unicode_sub_re() -> &'static Regex {
    static RE: OnceLock<Regex> = OnceLock::new();
    RE.get_or_init(|| {
        Regex::new(r"^(?P<main>(`[^`]*`)|([A-Za-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*([A-Z0-9a-z\p{Ll}\p{Lu}\p{Lo}]\p{M}*)*)?)(?P<sub>[\u{2080}-\u{2089},]+)$").unwrap()
    })
}

/// `filter_subscript(symbol)`: x_i -> x
pub fn filter_subscript(symbol: &str) -> String {
    if let Some(m) = block_re().captures(symbol) {
        return m.name("main").map_or("", |x| x.as_str()).to_string();
    }
    if let Some(m) = unicode_sub_re().captures(symbol) {
        return m.name("main").map_or("", |x| x.as_str()).to_string();
    }
    symbol.to_string()
}

pub fn get_unicode_number(c: char) -> Option<i64> {
    "⁰¹²³⁴⁵⁶⁷⁸⁹".chars().position(|x| x == c).map(|i| i as i64)
}

pub fn get_unicode_sub_number(c: char) -> Option<i64> {
    "₀₁₂₃₄₅₆₇₈₉".chars().position(|x| x == c).map(|i| i as i64)
}

pub fn get_unicode_fraction(c: char) -> Option<(i64, i64)> {
    let table = [
        ('¼', (1, 4)), ('½', (1, 2)), ('¾', (3, 4)), ('⅐', (1, 7)), ('⅑', (1, 9)), ('⅒', (1, 10)), ('⅓', (1, 3)),
        ('⅔', (2, 3)), ('⅕', (1, 5)), ('⅖', (2, 5)), ('⅗', (3, 5)), ('⅘', (4, 5)), ('⅙', (1, 6)), ('⅚', (5, 6)),
        ('⅛', (1, 8)), ('⅜', (3, 8)), ('⅝', (5, 8)), ('⅞', (7, 8)),
    ];
    table.iter().find(|(k, _)| *k == c).map(|(_, v)| *v)
}

/// `get_unicode_subscript(s)`: maps a whole string if it is one subscript letter.
pub fn get_unicode_subscript(s: &str) -> String {
    let table = [
        ("ₐ", "a"), ("ₑ", "e"), ("ₒ", "o"), ("ₓ", "x"), ("ₕ", "h"), ("ₖ", "k"), ("ₗ", "l"), ("ₘ", "m"), ("ₙ", "n"),
        ("ₚ", "p"), ("ₛ", "s"), ("ₜ", "t"), ("ᵢ", "i"), ("ⱼ", "j"),
    ];
    table.iter().find(|(k, _)| *k == s).map_or_else(|| s.to_string(), |(_, v)| v.to_string())
}

/// `get_unicode_superscript(s)`
pub fn get_unicode_superscript(s: &str) -> String {
    let table = [
        ("ᵃ", "a"), ("ᵇ", "b"), ("ᶜ", "c"), ("ᵈ", "d"), ("ᵉ", "e"), ("ᶠ", "f"), ("ᵍ", "g"), ("ʰ", "h"), ("ⁱ", "i"),
        ("ʲ", "j"), ("ᵏ", "k"), ("ˡ", "l"), ("ᵐ", "m"), ("ⁿ", "n"), ("ᵒ", "o"), ("ᵖ", "p"), ("ʳ", "r"), ("ˢ", "s"),
        ("ᵗ", "t"), ("ᵘ", "u"), ("ᵛ", "v"), ("ʷ", "w"), ("ˣ", "x"), ("ʸ", "y"), ("ᶻ", "z"), ("ᴬ", "A"), ("ᴮ", "B"),
        ("ᴰ", "D"), ("ᴱ", "E"), ("ᴳ", "G"), ("ᴴ", "H"), ("ᴵ", "I"), ("ᴶ", "J"), ("ᴷ", "K"), ("ᴸ", "L"), ("ᴹ", "M"),
        ("ᴺ", "N"), ("ᴼ", "O"), ("ᴾ", "P"), ("ᴿ", "R"), ("ᵀ", "T"), ("ᵁ", "U"), ("ⱽ", "V"), ("ᵂ", "W"),
    ];
    table.iter().find(|(k, _)| *k == s).map_or_else(|| s.to_string(), |(_, v)| v.to_string())
}

/// `base64_encode(content)`
pub fn base64_encode(content: &str) -> String {
    const T: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let b = content.as_bytes();
    let mut out = String::with_capacity((b.len() + 2) / 3 * 4);
    for chunk in b.chunks(3) {
        let n = (chunk[0] as u32) << 16 | (*chunk.get(1).unwrap_or(&0) as u32) << 8 | *chunk.get(2).unwrap_or(&0) as u32;
        out.push(T[(n >> 18) as usize & 63] as char);
        out.push(T[(n >> 12) as usize & 63] as char);
        out.push(if chunk.len() > 1 { T[(n >> 6) as usize & 63] as char } else { '=' });
        out.push(if chunk.len() > 2 { T[n as usize & 63] as char } else { '=' });
    }
    out
}

/// Python's `re.escape` (as used for parser keyword patterns), followed by
/// the compiler's `.replace('/', '\\/')`.
pub fn py_re_escape(s: &str) -> String {
    let mut out = String::new();
    for c in s.chars() {
        // Python 3.7+ escapes only regex-special characters
        if "()[]{}?*+-|^$\\.&~# \t\n\r\x0b\x0c".contains(c) {
            out.push('\\');
        }
        out.push(c);
    }
    out.replace('/', "\\/")
}

/// Python `str.title()`-free helpers used by code generators.
pub fn py_bool(b: bool) -> &'static str {
    if b {
        "True"
    } else {
        "False"
    }
}

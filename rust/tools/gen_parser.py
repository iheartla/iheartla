"""Translate the TatSu-generated I❤LA parsers into Rust.

The Python compiler parses with two TatSu-generated parsers in
iheartla/la_local_parsers/: init_parser.py (the "simplified" grammar used to
collect declarations) and default_parser.py (the full grammar). Both were
patched by hand after generation, so they, not the EBNF in la_grammar/, define
the language. This script translates their rule methods into Rust functions
for the PEG engine in rust/src/peg.rs, which reimplements TatSu's semantics
(ordered choice, CST/AST construction, memoization, left recursion).

The hand-patched rules that consult the parser's configuration (declared
multi-letter identifiers, function names, imported builtins, renames, the
constant e) are not translated; they call hand-written functions in
rust/src/grammar/special.rs instead.

usage: python rust/tools/gen_parser.py   (writes rust/src/grammar/{init,default}.rs)
"""
import ast
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'iheartla', 'la_local_parsers')
OUT = os.path.join(ROOT, 'rust', 'src', 'grammar')

# rules whose generated code was patched to read the parser configuration
SPECIAL = {'func_id', 'identifier_alone', 'builtin_operators', 'constant', 'KEYWORDS'}


def rust_str(s):
    out = []
    for ch in s:
        if ch == '\\':
            out.append('\\\\')
        elif ch == '"':
            out.append('\\"')
        elif ch == '\n':
            out.append('\\n')
        elif ch == '\t':
            out.append('\\t')
        elif ch == '\r':
            out.append('\\r')
        elif ch == '\f':
            out.append('\\u{c}')
        else:
            out.append(ch)
    return '"' + ''.join(out) + '"'


def ident(rule):
    return 'r_' + rule


def const(rule):
    return 'R_' + rule.upper() + ('_U' if rule.isupper() else '')


class Translator:
    def __init__(self, variant):
        self.variant = variant
        self.patterns = []          # pattern strings, index = id
        self.pattern_ids = {}
        self.rules = []             # (name, class, leftrec, memo)
        self.bodies = {}

    def pattern_id(self, pat):
        if pat not in self.pattern_ids:
            self.pattern_ids[pat] = len(self.patterns)
            self.patterns.append(pat)
        return self.pattern_ids[pat]

    def translate(self, path):
        tree = ast.parse(open(path, encoding='utf-8').read())
        parser_cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name.endswith('Parser'))
        for fn in parser_cls.body:
            if not isinstance(fn, ast.FunctionDef) or not (fn.name.startswith('_') and fn.name.endswith('_')) \
                    or fn.name.startswith('__'):
                continue
            name = fn.name[1:-1]
            cls, leftrec, memo = None, False, True
            for d in fn.decorator_list:
                if isinstance(d, ast.Call) and getattr(d.func, 'id', '') == 'tatsumasu':
                    if d.args:
                        cls = d.args[0].value
                elif isinstance(d, ast.Name):
                    if d.id == 'leftrec':
                        leftrec, memo = True, False
                    elif d.id == 'nomemo':
                        memo = False
                    else:
                        raise ValueError('decorator ' + d.id)
            self.rules.append((name, cls, leftrec, memo))
            if name in SPECIAL and self.variant == 'default':
                self.bodies[name] = None
            else:
                self.bodies[name] = self.block(fn.body, {}, 1)

    # -- statements ---------------------------------------------------------

    def block(self, stmts, blocks, ind):
        """Translate a statement list into Rust lines ending with a Result expression."""
        lines = []
        blocks = dict(blocks)
        pad = '    ' * ind
        for i, st in enumerate(stmts):
            last = i == len(stmts) - 1
            if isinstance(st, ast.FunctionDef):          # def blockN(): ...  (closure body)
                blocks[st.name] = st.body
                continue
            if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant):
                continue                                  # docstring
            if isinstance(st, ast.With):
                lines += self.with_stmt(st, blocks, ind)
                continue
            if isinstance(st, ast.If):
                lines += self.if_stmt(st, blocks, ind)
                continue
            if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
                call = st.value
                meth = call.func.attr if isinstance(call.func, ast.Attribute) else None
                if meth == '_error':
                    lines.append(pad + 'return Err(p.error({}));'.format(rust_str(self.str_arg(call.args[0]))))
                    return lines
                lines.append(pad + self.call(call, blocks, ind))
                continue
            raise ValueError('unsupported statement: ' + ast.dump(st)[:200])
        lines.append(pad + 'Ok(())')
        return lines

    def str_arg(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.JoinedStr):
            raise ValueError('f-string')
        # implicit concatenation is folded by the parser into one Constant
        raise ValueError(ast.dump(node))

    def closure_body(self, node, blocks, ind):
        body = blocks[node.id]
        inner = self.block(body, blocks, ind + 1)
        return '|p| {\n' + '\n'.join(inner) + '\n' + '    ' * ind + '}'

    def call(self, call, blocks, ind):
        f = call.func
        assert isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == 'self', ast.dump(call)
        m = f.attr
        if m == '_token':
            return 'p.token({})?;'.format(rust_str(call.args[0].value))
        if m == '_pattern':
            return 'p.pattern({})?;'.format(self.pattern_id(call.args[0].value))
        if m == 'name_last_node':
            return 'p.name_last_node({});'.format(rust_str(call.args[0].value))
        if m == 'add_last_node_to_name':
            return 'p.add_last_node_to_name({});'.format(rust_str(call.args[0].value))
        if m == '_define':
            keys = [k.value for k in call.args[0].elts]
            lkeys = [k.value for k in call.args[1].elts] if len(call.args) > 1 else []
            return 'p.define(&[{}], &[{}]);'.format(', '.join(rust_str(k) for k in keys),
                                                    ', '.join(rust_str(k) for k in lkeys))
        if m == '_closure':
            return 'p.closure({})?;'.format(self.closure_body(call.args[0], blocks, ind))
        if m == '_positive_closure':
            return 'p.positive_closure({})?;'.format(self.closure_body(call.args[0], blocks, ind))
        if m == '_check_eof':
            return 'p.check_eof()?;'
        if m.startswith('_') and m.endswith('_') and not call.args:
            return 'p.call({})?;'.format(const(m[1:-1]))
        raise ValueError('unsupported call self.' + m)

    def with_stmt(self, st, blocks, ind):
        pad = '    ' * ind
        ctx = st.items[0].context_expr
        kind = ctx.func.attr
        if kind == '_choice':
            out = [pad + 'p.choice(|p| {']
            out += self.choice_body(st.body, blocks, ind + 1)
            out.append(pad + '})?;')
            return out
        if kind == '_option':
            raise ValueError('option outside choice')
        wrapper = {'_group': 'p.group', '_optional': 'p.optional', '_ifnot': 'p.ifnot', '_if': 'p.lookahead'}[kind]
        inner = self.block(st.body, blocks, ind + 1)
        tail = ';' if kind == '_optional' else '?;'
        return [pad + wrapper + '(|p| {'] + inner + [pad + '})' + tail]

    def choice_body(self, stmts, blocks, ind):
        pad = '    ' * ind
        lines = []
        for st in stmts:
            if isinstance(st, ast.With) and st.items[0].context_expr.func.attr == '_option':
                inner = self.block(st.body, blocks, ind + 1)
                lines += [pad + 'if p.option(|p| {'] + inner + [pad + '}) {', pad + '    return Ok(());', pad + '}']
            elif isinstance(st, ast.Expr) and st.value.func.attr == '_error':
                lines.append(pad + 'Err(p.error({}))'.format(rust_str(self.str_arg(st.value.args[0]))))
                return lines
            elif isinstance(st, ast.FunctionDef):
                blocks = dict(blocks)
                blocks[st.name] = st.body
            else:
                raise ValueError('unsupported in choice: ' + ast.dump(st)[:200])
        lines.append(pad + 'Ok(())')
        return lines

    def if_stmt(self, st, blocks, ind):
        # if 'sin' in self.conversion_dict: self._pattern(self.conversion_dict['sin'])
        # else: self._pattern('sin')
        pad = '    ' * ind
        test = st.test
        if isinstance(test, ast.Compare) and isinstance(test.ops[0], ast.In) and \
                getattr(test.comparators[0], 'attr', '') == 'conversion_dict':
            key = test.left.value
            default = st.orelse[0].value.args[0].value
            return [pad + 'p.renamed_pattern({}, {})?;'.format(rust_str(key), self.pattern_id(default))]
        raise ValueError('unsupported if: ' + ast.unparse(test))

    # -- output -------------------------------------------------------------

    def emit(self):
        v = self.variant
        out = ['// @generated by rust/tools/gen_parser.py from iheartla/la_local_parsers/{}_parser.py.'.format(v),
               '// Do not edit; regenerate instead.',
               '#![allow(clippy::all, unused_imports)]',
               '',
               'use crate::peg::{Parser, PResult, RuleId, RuleInfo};',
               'use super::special;',
               '']
        for i, (name, cls, leftrec, memo) in enumerate(self.rules):
            out.append('pub const {}: RuleId = {};'.format(const(name), i))
        out.append('')
        out.append('pub static RULES: [RuleInfo; {}] = ['.format(len(self.rules)))
        for name, cls, leftrec, memo in self.rules:
            body = ident(name) if self.bodies[name] is not None else 'special::{}_{}'.format(v, name)
            out.append('    RuleInfo {{ name: {}, class: {}, leftrec: {}, memo: {}, body: {} }},'.format(
                rust_str(name), 'Some({})'.format(rust_str(cls)) if cls else 'None',
                'true' if leftrec else 'false', 'true' if memo else 'false', body))
        out.append('];')
        out.append('')
        out.append('pub static PATTERNS: [&str; {}] = ['.format(len(self.patterns)))
        for pat in self.patterns:
            out.append('    {},'.format(rust_str(pat)))
        out.append('];')
        out.append('')
        out.append('pub fn rule_by_name(name: &str) -> Option<RuleId> {')
        out.append('    RULES.iter().position(|r| r.name == name)')
        out.append('}')
        out.append('')
        for name, cls, leftrec, memo in self.rules:
            body = self.bodies[name]
            if body is None:
                continue
            out.append('fn {}(p: &mut Parser) -> PResult {{'.format(ident(name)))
            out += body
            out.append('}')
            out.append('')
        return '\n'.join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    for variant in ['init', 'default']:
        t = Translator(variant)
        t.translate(os.path.join(SRC, variant + '_parser.py'))
        with open(os.path.join(OUT, variant + '.rs'), 'w', encoding='utf-8') as f:
            f.write(t.emit())
        print(variant, len(t.rules), 'rules', len(t.patterns), 'patterns')


if __name__ == '__main__':
    main()

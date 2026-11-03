"""
H❤️rtDown's compiles with the Rust I❤️LA compiler (the WebAssembly module of rust_wasm.py, run by wasmtime or, in
Pyodide, by the browser).

compile_la_content() takes the arguments of the Python compiler's compile_la_content(..., get_json=True) that
H❤️rtDown passes, and returns what that does: the code frames of the outputs ({ParserTypeEnum: frame}) and the
equation data (EquationData). The Rust side is rust/src/heartdown.rs.
"""
from pathlib import Path

from .la_parser.equation_data import DependenceData, EquationData
from .la_tools.la_helper import ParserTypeEnum
from .la_tools.la_msg import LaMsg

# the outputs, by their names in the Rust compiler
BACKENDS = {
    ParserTypeEnum.NUMPY: "numpy",
    ParserTypeEnum.EIGEN: "eigen",
    ParserTypeEnum.MATLAB: "matlab",
    ParserTypeEnum.MATHJAX: "mathjax",
    ParserTypeEnum.MACROMATHJAX: "macromathjax",
}

_compiler = None


def compiler():
    """The WebAssembly module (instantiated once)."""
    global _compiler
    if _compiler is None:
        from .rust_wasm import Compiler
        _compiler = Compiler()
    return _compiler


class CodeFrame(object):
    """An output's parts, as H❤️rtDown reads them from the Python compiler's CodeFrame."""

    def __init__(self, include='', struct='', pre_str='', post_str='', expr_dict=None):
        self.include = include      # imports or includes (code)
        self.struct = struct        # the class, struct or function (code)
        self.pre_str = pre_str      # before the equations (MathJax)
        self.post_str = post_str    # after them (MathJax)
        self.expr_dict = expr_dict if expr_dict is not None else {}  # source text of an equation: its MathJax


class RustType(object):
    """A type from the Rust compiler, as JSON; get_json_content() prints it as the Python compiler's types do."""

    def __init__(self, t):
        self.t = t

    def get_json_content(self):
        return type_json_content(self.t)


def type_json_content(t):
    if not t:
        return ''
    is_int = "True" if t.get("is_int") else "False"
    kind = t["type"]
    if kind == "scalar":
        return """{{"type": "scalar", "is_int":"{}"}}""".format(is_int)
    if kind == "vector":
        return """{{"type": "vector", "is_int":"{}", "element":{}, "rows":"{}"}}""".format(is_int, type_json_content(t["element"]), t["rows"])
    if kind == "matrix":
        return """{{"type": "matrix", "is_int":"{}", "element":{}, "rows":"{}", "cols":"{}"}}""".format(is_int, type_json_content(t["element"]), t["rows"], t["cols"])
    if kind == "sequence":
        return """{{"type": "sequence", "is_int":"{}", "element":{}, "size":"{}"}}""".format(is_int, type_json_content(t["element"]), t["size"])
    if kind == "set":
        return """{{"type": "set", "is_int":"{}", "element":[{}], "size":"{}"}}""".format(is_int, ','.join('"{}"'.format(e) for e in t["element"]), t["size"])
    if kind == "function":
        return """{{"type": "function", "params":[{}], "ret":[{}]}}""".format(','.join(type_json_content(p) for p in t["params"]), ','.join(type_json_content(r) for r in t["ret"]))
    # (types the Python compiler doesn't describe: meshes, tuples, sets of vectors)
    return """{{"type": "{}", "is_int":"{}"}}""".format(kind, is_int)


class ParamsData(object):
    def __init__(self, parameters, symtable):
        self.parameters = parameters  # names
        self.symtable = symtable      # name: type, for the parameters and the function's other symbols


class FuncData(object):
    """A local function, as H❤️rtDown reads it from the Python compiler's func_data_dict."""

    def __init__(self, params_data):
        self.params_data = params_data


def compile_la_content(la_content, parser_type=ParserTypeEnum.NUMPY | ParserTypeEnum.EIGEN | ParserTypeEnum.MATLAB | ParserTypeEnum.MATHJAX | ParserTypeEnum.MACROMATHJAX,
                       func_name=None, path=None, struct=True, get_json=True):
    """
    Compile a H❤️rtDown context's I❤️LA code, finding modules it imports in path.
    Raises AssertionError on an error in the code, with LaMsg's cur_msg and cur_code set as the Python compiler sets them.
    :return: ({ParserTypeEnum: CodeFrame}, EquationData)
    """
    name = func_name or "heartlib"
    backends = [b for t, b in BACKENDS.items() if parser_type & t]
    c = compiler()
    c.module_dir = Path(path) if path else Path(".")
    response = c.request("ih_heartdown_json", {"source": la_content, "name": name, "backends": backends})
    if "error" in response:
        msg = LaMsg.getInstance()
        msg.cur_msg = response.get("msg", "")
        msg.cur_code = response.get("code", "")
        raise AssertionError(response["error"])
    code_dict = {}
    for t, b in BACKENDS.items():
        if b not in response["frames"]:
            continue
        f = response["frames"][b]
        if "exprs" in f:
            code_dict[t] = CodeFrame(pre_str=f["pre"], post_str=f["post"], expr_dict=dict(f["exprs"]))
        else:
            code_dict[t] = CodeFrame(include=f["include"], struct=f["struct"])
    return code_dict, equation_data(response["equation"], la_content)


def equation_data(e, la_content):
    symtable = {name: RustType(t) for name, t in e["types"].items()}
    func_data_dict = {}
    for f in e["local_funcs"]:
        f_symtable = {name: RustType(t) for name, t in f["types"].items()}
        for name in f["symbols"]:
            f_symtable.setdefault(name, RustType(None))
        func_data_dict[f["name"]] = FuncData(ParamsData(f["parameters"], f_symtable))
    dependence = [DependenceData(d["module"], d["args"], d["names"]) for d in e["dependence"]]
    return EquationData('', e["parameters"], e["definition"], dependence, symtable, e["desc"], la_content,
                        func_data_dict, dict(e["expr_symbols"]), e["opt_syms"])

// Runs Pyodide and the I❤️LA compiler off the main thread, so the page stays
// responsive during long compiles (e.g., programs that import I❤️MESH modules).
// Messages: main -> worker {id, source}; worker -> main {ready: true} once, then
// {id, code: [numpy, eigen, latex, mathjax, matlab]} or {id, error}.

// Pyodide and all Python packages are vendored in js/pyodide/ (see docs/update_pyodide.sh).
// Pyodide needs a module worker: new Worker(url, { type: "module" }).
import { loadPyodide } from "./pyodide/pyodide.mjs";
const local = new URL("pyodide/", import.meta.url).href;

const COMPILE = `
from iheartla.la_parser.parser import compile_la_content
from iheartla.la_tools.la_helper import ParserTypeEnum
# only the outputs the page shows
targets = [ParserTypeEnum.NUMPY, ParserTypeEnum.EIGEN, ParserTypeEnum.LATEX, ParserTypeEnum.MATHJAX, ParserTypeEnum.MATLAB]
parser_type = ParserTypeEnum.INVALID
for t in targets:
    parser_type |= t
from tatsu.exceptions import FailedParse
from iheartla.la_tools.la_msg import LaMsg
try:
    result = compile_la_content(source_code, parser_type)
    code = result if isinstance(result, str) else [result[t] for t in targets]
except FailedParse as e:      # syntax error, with line, column, and a caret
    code = LaMsg.getInstance().get_parse_error(e)
except AssertionError as e:   # I❤️LA reports type errors this way, with the location
    code = str(e.args[0]) if e.args else "Compile error!"
except Exception as e:
    code = "Compile error! {}: {}".format(type(e).__name__, e)
`;

const ready = (async () => {
    const pyodide = await loadPyodide({ indexURL: local });
    await pyodide.loadPackage(["micropip", "regex", "sympy"]);
    // The iheartla wheel is built from this repository with: uv build --wheel --no-create-gitignore -o docs
    pyodide.globals.set("wheels", [local + "appdirs-1.4.4-py2.py3-none-any.whl",
                                   local + "tatsu-5.14.0-py3-none-any.whl",
                                   new URL("../iheartla-0.0.1-py3-none-any.whl", import.meta.url).href]);
    await pyodide.runPythonAsync("import micropip\nawait micropip.install(wheels.to_py())");
    pyodide.runPython("import iheartla.la_parser.parser");  // load the compiler now, not on the first compile
    return pyodide;
})();
ready.then(() => self.postMessage({ ready: true }),
           e => self.postMessage({ ready: false, error: "Failed to load the compiler: " + e.message }));

self.onmessage = async (event) => {
    const { id, source } = event.data;
    const pyodide = await ready;
    try {
        pyodide.globals.set("source_code", source);
        pyodide.runPython(COMPILE);
        const code = pyodide.globals.get("code");
        if (typeof code === "string") {
            self.postMessage({ id, error: code });
        } else {
            self.postMessage({ id, code: code.toJs() });
            code.destroy();
        }
    } catch (e) {
        console.log(e.message);
        self.postMessage({ id, error: "Compile error!\n" + String(e.message).split("\n").slice(-2).join("\n") });
    }
};

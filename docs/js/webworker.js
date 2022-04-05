importScripts(self.location.origin + "/js/pyodide/pyodide.js");

self.onmessage = async(event) => {
    let pythonCode = event.data
    if (pythonCode === ''){
        // Initialize pyodide
        await loadPyodide({
          indexURL : self.location.origin + "/js/pyodide/"
        });
        let wheel = self.location.origin + `/linear_algebra-0.0.1-py3-none-any.whl`
        pythonCode = `
import micropip
micropip.install('appdirs')
micropip.install('tatsu')
micropip.install('${wheel}')
`
    }
    // console.log('code is:' + pythonCode);
    try {
        await self.pyodide.runPythonAsync(pythonCode)
        let code = pyodide.globals.get('code').toJs();
        self.postMessage({
            results: code
        });
    }
    catch (error){
        console.log('error')
        self.postMessage({error : error.message});
    }
}

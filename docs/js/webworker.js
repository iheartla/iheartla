importScripts(self.location.origin + "/iheartla/js/pyodide/pyodide.js");

self.onmessage = async(event) => {
    let pythonCode = event.data
    if (pythonCode === ''){
        // Initialize pyodide
        await loadPyodide({
          indexURL : self.location.origin + "/iheartla/js/pyodide/"
        });
        let wheel = self.location.origin + `/iheartla-0.0.1-py3-none-any.whl`
        let tatsu = self.location.origin + `/TatSu-4.4.0-py2.py3-none-any.whl`
        pythonCode = `
import micropip
micropip.install('appdirs') 
micropip.install('regex') 
micropip.install('${tatsu}')
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

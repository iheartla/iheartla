// webworker.js

// Setup your project to serve `py-worker.js`. You should also serve
// `pyodide.js`, and all its associated `.asm.js`, `.data`, `.json`,
// and `.wasm` files as well:
self.languagePluginUrl = 'https://cdn.jsdelivr.net/pyodide/v0.16.1/full/';
importScripts('https://cdn.jsdelivr.net/pyodide/v0.16.1/full/pyodide.js');
importScripts('https://cdn.jsdelivr.net/npm/js-base64@3.6.0/base64.min.js');

let pythonLoading;
async function loadPythonPackages(){
    await languagePluginLoader;
    pythonCode = `
import micropip
micropip.install('appdirs')
micropip.install('tatsu')
micropip.install('http://45.77.237.80/static/iheartla-0.0.1-py3-none-any.whl')
print(2)
    `
    console.log('test111');
    // pythonLoading = await self.pyodide.runPython(pythonCode);
    pythonLoading = self.pyodide.loadPackage(['micropip']).then(() => {
        console.log('test222');
        self.pyodide.version();
        self.pyodide.runPython(pythonCode);
    }).then(() => {
        console.log('finished');
        pythonLoading = self.pyodide;
    });

}

self.onmessage = async(event) => {
    // loadPythonPackages();
    await languagePluginLoader;
     // since loading package is asynchronous, we need to make sure loading is done:
    await pythonLoading;
    pythonCode = event.data['python']
      pythonCode = Base64.decode(pythonCode);
      console.log(pythonCode);
      console.log(event.data);
    // Now is the easy part, the one that is similar to working in the main thread:
    try {
        pyodide.runPythonAsync(pythonCode)
        .then(output => self.postMessage({
            'results':  output
        }))
        .catch((err) => { console.log(err) });
    }
    catch (error){
        self.postMessage(
            {error : error.message}
        );
    }
}

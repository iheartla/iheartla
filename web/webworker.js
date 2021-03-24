self.languagePluginUrl = 'https://cdn.jsdelivr.net/pyodide/v0.16.1/full/';
importScripts('https://cdn.jsdelivr.net/pyodide/v0.16.1/full/pyodide.js');

self.onmessage = async(event) => {
    await languagePluginLoader;
    let pythonCode = event.data
    if (pythonCode === ''){
        let wheel = self.location.origin + `/iheartla-0.0.1-py3-none-any.whl`
        pythonCode = `
        import micropip
        micropip.install('appdirs')
        micropip.install('tatsu')
        micropip.install('${wheel}')
        `
    }
    console.log('code is:' + pythonCode);
    try {
        pyodide.runPythonAsync(pythonCode)
        .then(output => self.postMessage({
            'results':  output
        }))
        .catch((err) => { console.log(err) });
    }
    catch (error){
        console.log('error')
        self.postMessage(
            {error : error.message}
        );
    }
}

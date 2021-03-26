const pyodideWorker = new Worker('js/webworker.js')

function run(script, onSuccess, onError){
    pyodideWorker.onerror = onError;
    pyodideWorker.onmessage = (e) => onSuccess(e.data);
    pyodideWorker.postMessage(script);
}

function asyncRun(script) {
    return new Promise(function(onSuccess, onError) {
        run(script, onSuccess, onError);
    });
}

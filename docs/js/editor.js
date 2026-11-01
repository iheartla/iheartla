let unicode_dict = {'R': 'ℝ', 'Z': 'ℤ', 'x': '×', 'times': '×', 'inf': '∞', 'in': '∈', 'sum': '∑',
                             'had': '∘', 'kro': '⊗', 'dot': '⋅', 'T': 'ᵀ', '^T': 'ᵀ', 'par': '∂', 'emp': '∅',
                             'arr': '→', 'int': '∫', 'dbl': '‖', 'pi': 'π', 'sig': 'σ', 'rho': 'ρ',
                             'phi': 'ϕ', 'theta': 'θ', 'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta':'δ', 'epsilon': 'ε',
                             'zeta':'ζ', 'eta':'η', 'iota':'ι', 'kappa':'κ', 'lambda':'λ', 'mu':'μ', 'nu':'ν', 'xi':'ξ', 'omicron':'ο',
                             'sigma':'σ', 'tau':'τ', 'upsilon':'υ', 'chi':'χ', 'psi':'ψ', 'omega':'ω',
                             'u0': '₀', 'u1': '₁', 'u2': '₂', 'u3': '₃', 'u4': '₄', 'u5': '₅', 'u6': '₆', 'u7': '₇', 'u8': '₈', 'u9': '₉',
                             '_0': '₀', '_1': '₁', '_2': '₂', '_3': '₃', '_4': '₄', '_5': '₅', '_6': '₆', '_7': '₇', '_8': '₈', '_9': '₉',
                             's0': '⁰', 's1': '¹', 's2': '²', 's3': '³', 's4': '⁴', 's5': '⁵', 's6': '⁶', 's7': '⁷', 's8': '⁸', 's9': '⁹', 's-1': '⁻¹', '^-1': '⁻¹',
                             '^0': '⁰', '^1': '¹', '^2': '²', '^3': '³', '^4': '⁴', '^5': '⁵', '^6': '⁶', '^7': '⁷', '^8': '⁸', '^9': '⁹',
                             '_a': 'ₐ', '_e': 'ₑ', '_h': 'ₕ', '_i': 'ᵢ', '_j': 'ⱼ', '_k': 'ₖ',
                             '_l': 'ₗ', '_m': 'ₘ', '_n': 'ₙ', '_o': 'ₒ', '_p': 'ₚ', '_s': 'ₛ', '_t': 'ₜ', '_u': 'ᵤ',
                             '_v': 'ᵥ', '_x': 'ₓ', '1': '𝟙', 'cdot': '⋅', 'nabla': '∇',
                             'sqrt': '√', '+-': '±', '<=': '≤', '<=>': '⇔', '>=': '≥', '1/2': '½',
                             '1/3': '⅓', '1/4': '¼', '1/5': '⅕', '1/6': '⅙', '1/7': '⅐', '1/8': '⅛', '1/9': '⅑', '1/10': '⅒',
                             '2/3': '⅔', '2/5': '⅖', '3/4': '¾', '3/5': '⅗', '3/8': '⅜', '4/5': '⅘', '5/6': '⅚', '5/8': '⅝', '7/8': '⅞',
                             'heart': '❤️', 'iheartla': 'I❤️LA',
                             'le':'≤', 'ge':'≥', 'ne': '≠', 'notin':'∉', 'div':'÷', 'nplus': '±',
                             'linner': '⟨', 'rinner':'⟩', 'num1': '𝟙',
                             'hat': '\u0302', 'bar': '\u0304'
                             }
function checkBrowserVer(){
    // Pyodide runs in any browser with WebAssembly (current Chrome, Firefox, Safari, Edge).
    let result = typeof WebAssembly === "object";
    let msg = result ? "Valid browser!" : "This browser does not support WebAssembly, which the compiler needs.";
    console.log(msg);

    // Also check for a secure context.
    // UPDATE: This isn't needed.
    /*
    if( !window.isSecureContext ) {
        result = false;
        msg = "This is not a secure context. You must use 'https://' or 'http://localhost'."
        console.log(msg);
    }
    */

    // Make sure we're not running from a file: URL (if the user double-clicked index.html)
    // Source: https://stackoverflow.com/questions/3920892/how-to-detect-if-a-web-page-is-running-from-a-website-or-local-file-system
    /// It turns out we don't need a secure context.
    // if( !window.isSecureContext ) {
    /// But a file: URL won't work.
    if( window.location.protocol === "file:" ) {
        result = false;
        msg = "Please run via a local webserver. Try `python3 -m http.server` and then browse to 'http://localhost:8000/'."
        console.log(msg);
    }

    return [ result, msg ];
}

function isChrome(){
    let nAgt = navigator.userAgent;
    if (nAgt.indexOf("Chrome")!=-1) {
        return true;
    }
    return false;
}

// The compiler runs in a Web Worker so long compiles don't block the page: the
// Python compiler in Pyodide (js/compile-worker.js), or the Rust compiler as
// WebAssembly (js/compile-worker-rust.js). Both take the same messages. The
// choice is the URL parameter `compiler` (python or rust).
let compileWorker = null;
let compileCallbacks = {};
let nextCompileId = 0;
const compilerWorkers = { python: "js/compile-worker.js", rust: "js/compile-worker-rust.js" };

function compilerChoice(){
    const choice = new URL(window.location.href).searchParams.get("compiler");
    return compilerWorkers[choice] ? choice : "python";
}

// Switch compilers (from the Compiler buttons): remember the choice in the
// URL (so "Copy as URL" keeps it) and restart the worker.
function setCompiler(choice){
    const url = new URL(window.location.href);
    url.searchParams.set("compiler", choice);
    window.history.replaceState(null, "", url.toString());
    if (compileWorker){
        compileWorker.terminate();
    }
    compileCallbacks = {};
    initBtnStatus();
    initCompiler();
}

function initPyodide(){
    initCompiler();
}

function initCompiler(){
    const choice = compilerChoice();
    const radio = document.getElementById("compiler-" + choice);
    if (radio){
        radio.checked = true;
    }
    compileWorker = new Worker(compilerWorkers[choice], { type: "module" });
    compileWorker.onerror = function(event){
        updateError("Failed to start the compiler: " + (event.message || "see the browser console"));
    };
    compileWorker.onmessage = function(event){
        let msg = event.data;
        if (msg.ready !== undefined){
            if (msg.ready){
                activateBtnStatus();
            }
            else{
                updateError(msg.error);
            }
            return;
        }
        let callback = compileCallbacks[msg.id];
        delete compileCallbacks[msg.id];
        if (callback){
            callback(msg);
        }
    };
}

function convert(input) {
    output = document.getElementById('output');
    output.innerHTML = '';
    MathJax.texReset();
    var options = MathJax.getMetricsFor(output);
    options.display = 1;
    MathJax.tex2chtmlPromise(input, options).then(function (node) {
        output.appendChild(node);
        MathJax.startup.document.clear();
        MathJax.startup.document.updateDocument();
    }).catch(function (err) {
        output.appendChild(document.createElement('pre')).appendChild(document.createTextNode(err.message));
    }).then(function () {
    });
}

function updateEditor(code) {
    showMsg('Compile succeeded');
    var cpp = ace.edit("cpp");
    cpp.session.setValue(code[1]);
    var python = ace.edit("python");
    python.session.setValue(code[0]);
    var latex = ace.edit("latex");
    latex.session.setValue(code[2]);
    convert(code[3]);
    var matlab = ace.edit("matlab");
    matlab.session.setValue(code[4]);
    // reset UI
    activateBtnStatus();
}

function updateError(err) {
    showMsg(err, true);
    activateBtnStatus();
}

function compileFunction(){
    var iheartla = ace.edit("editor");
    var source = iheartla.getValue();
    console.log(source)
    let id = nextCompileId++;
    compileCallbacks[id] = function(msg){
        if (msg.error !== undefined){
            updateError(msg.error);
        }
        else{
            updateEditor(msg.code);
        }
    };
    compileWorker.postMessage({ id: id, source: source });
}

function clickCompile(){
    hideMsg();
    try {
        document.getElementById("compile").disabled = true;
        document.getElementById("compile").innerHTML = `<i id="submit_icon" class="fa fa-refresh fa-spin"></i> Compiling`;
        compileFunction();
    } catch (error) {
        console.error(error);
        activateBtnStatus();
    }
    finally {
    }
}

function clickCopy() {
    // Base the URL off the current one.
    const url = new URL(window.location.href);
    const source = editor.getValue();
    url.searchParams.set( "code", source );
    
    navigator.clipboard.writeText( url.toString() ).then(function() {
        /* clipboard successfully set */
        showMsg( "Copied a shareable code URL to the clipboard." );
    }, function() {
        /* clipboard write failed */
        showMsg( "Failed to copy to the clipboard." );
    });
    
    
    
}

function showMsg(msg, error=false){
    msg = msg.replaceAll('\n', '<br>')
    let el = document.getElementById("msg");
    el.hidden = false;
    el.innerHTML = msg;

    // Alert types: https://getbootstrap.com/docs/4.0/components/alerts/
    // Edit class: https://stackoverflow.com/questions/195951/how-can-i-change-an-elements-class-with-javascript
    el.classList.remove('alert-primary');
    el.classList.remove('alert-danger');
    if(error) {
        el.classList.add('alert-danger');
    } else {
        // notice, auto hide
        el.classList.add('alert-primary');
        setTimeout(hideMsg, 2000);
    }
}

function hideMsg(){
    document.getElementById("msg").hidden = true; document.getElementById("msg").innerHTML = '';
}

function setBtnTitle(text){
    document.getElementById("compile").innerHTML = `<i id="submit_icon" class="fa fa-refresh"></i> ` + text;
}

function initBtnStatus(){
    document.getElementById("compile").disabled = true;
    document.getElementById("compile").innerHTML = `Initializing...`;
}

function activateBtnStatus(){
    document.getElementById("compile").disabled = false;
    setBtnTitle("Compile");
}

function onEditIhla(e){
    hideMsg();
    let editor = ace.edit("editor");
    for (let key in unicode_dict) {
        let old_str = '\\' + key + ' ';
        let result = editor.find(old_str);
        if (result){
            editor.replaceAll(unicode_dict[key]);
            editor.gotoLine(result.start.row+1, result.start.column+unicode_dict[key].length)
            editor.clearSelection();
            break;
        }
    }
}

// Set the contents of the code editor to a `code` parameter if present.
function loadCodeFromURLParameter() {
    const url = new URL(window.location.href);
    const code = url.searchParams.get("code");
    if( code !== null ) {
        // If this is called after the ace editor is created, then we need
        // to set the code a different way.
        document.getElementById("editor").innerHTML = code;
    }
}

function captureHotKeys() {
    // https://stackoverflow.com/questions/93695/best-cross-browser-method-to-capture-ctrls-with-jquery
    window.addEventListener( 'keydown', function(event) {
        if (event.ctrlKey || event.metaKey) {
            switch (String.fromCharCode(event.which).toLowerCase()) {
            case 'r':
                event.preventDefault();
                clickCompile();
                break;
            }
        }
    });
}

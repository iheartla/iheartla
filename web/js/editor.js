let unicode_dict = {'R': 'ℝ', 'Z': 'ℤ', 'x': '×', 'times': '×', 'inf': '∞', 'in': '∈', 'sum': '∑',
                             'had': '∘', 'kro': '⊗', 'dot': '⋅', 'T': 'ᵀ', '^T': 'ᵀ', 'par': '∂', 'emp': '∅',
                             'arr': '→', 'int': '∫', 'dbl': '‖', 'pi': 'π', 'sig': 'σ', 'rho': 'ρ',
                             'phi': 'ϕ', 'the': 'θ', 'alp': 'α', 'bet': 'β',  'gam': 'γ',
                             'u0': '₀', 'u1': '₁', 'u2': '₂', 'u3': '₃', 'u4': '₄', 'u5': '₅', 'u6': '₆', 'u7': '₇', 'u8': '₈', 'u9': '₉',
                             '_0': '_', '_1': '₁', '_2': '₂', '_3': '₃', '_4': '₄', '_5': '₅', '_6': '₆', '_7': '₇', '_8': '₈', '_9': '₉',
                             's0': '⁰', 's1': '¹', 's2': '²', 's3': '³', 's4': '⁴', 's5': '⁵', 's6': '⁶', 's7': '⁷', 's8': '⁸', 's9': '⁹', 's-1': '⁻¹', '^-1': '⁻¹',
                             '^0': '⁰', '^1': '¹', '^2': '²', '^3': '³', '^4': '⁴', '^5': '⁵', '^6': '⁶', '^7': '⁷', '^8': '⁸', '^9': '⁹',
                             '_a': 'ₐ', '_e': 'ₑ', '_h': 'ₕ', '_i': 'ᵢ', '_j': 'ⱼ', '_k': 'ₖ',
                             '_l': 'ₗ', '_m': 'ₘ', '_n': 'ₙ', '_o': 'ₒ', '_p': 'ₚ', '_s': 'ₛ', '_t': 'ₜ', '_u': 'ᵤ',
                             '_v': 'ᵥ', '_x': 'ₓ', '1': '𝟙', 'cdot': '⋅', 'nabla': '∇',
                             'sqrt': '√', '+-': '±', '<=': '≤', '<=>': '⇔', '>=': '≥', '1/2': '½',
                             '1/3': '⅓', '1/4': '¼', '1/5': '⅕', '1/6': '⅙', '1/8': '⅛', '2/3': '⅔', '2/5': '⅖',
                             '3/4': '¾', '3/5': '⅗', '3/8': '⅜', '4/5': '⅘', '5/6': '⅚', '5/8': '⅝', '7/8': '⅞',
                             'heart': '❤️', 'iheartla': 'I❤️LA',
                             'le':'≤', 'ge':'≥', 'ne': '≠', 'notin':'∉', 'div':'÷', 'nplus': '±',
                             'linner': '⟨', 'rinner':'⟩', 'num1': '𝟙'
                             }
function checkBrowserVer(){
    var nVer = navigator.appVersion;
    var nAgt = navigator.userAgent;
    var browserName  = navigator.appName;
    var fullVersion  = ''+parseFloat(navigator.appVersion);
    var majorVersion = parseInt(navigator.appVersion,10);
    var nameOffset,verOffset,ix;
    var validBrowser = false;
    // In Opera, the true version is after "Opera" or after "Version"
    if ((verOffset=nAgt.indexOf("Opera"))!=-1) {
        browserName = "Opera";
        fullVersion = nAgt.substring(verOffset+6);
        if ((verOffset=nAgt.indexOf("Version"))!=-1)
            fullVersion = nAgt.substring(verOffset+8);
    }
    // In MSIE, the true version is after "MSIE" in userAgent
    else if ((verOffset=nAgt.indexOf("MSIE"))!=-1) {
        browserName = "Microsoft Internet Explorer";
        fullVersion = nAgt.substring(verOffset+5);
    }
    // In Chrome, the true version is after "Chrome"
    else if ((verOffset=nAgt.indexOf("Chrome"))!=-1) {
        browserName = "Chrome";
        fullVersion = nAgt.substring(verOffset+7);
        validBrowser = true;
    }
    // In Safari, the true version is after "Safari" or after "Version"
    else if ((verOffset=nAgt.indexOf("Safari"))!=-1) {
        browserName = "Safari";
        fullVersion = nAgt.substring(verOffset+7);
        if ((verOffset=nAgt.indexOf("Version"))!=-1)
            fullVersion = nAgt.substring(verOffset+8);
        }
    // In Firefox, the true version is after "Firefox"
    else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) {
        browserName = "Firefox";
        fullVersion = nAgt.substring(verOffset+8);
        validBrowser = true;
    }
    // In most other browsers, "name/version" is at the end of userAgent
    else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) <
            (verOffset=nAgt.lastIndexOf('/')) )
    {
        browserName = nAgt.substring(nameOffset,verOffset);
        fullVersion = nAgt.substring(verOffset+1);
        if (browserName.toLowerCase()==browserName.toUpperCase()) {
            browserName = navigator.appName;
        }
    }
    // trim the fullVersion string at semicolon/space if present
    if ((ix=fullVersion.indexOf(";"))!=-1)
        fullVersion=fullVersion.substring(0,ix);
    if ((ix=fullVersion.indexOf(" "))!=-1)
        fullVersion=fullVersion.substring(0,ix);

    majorVersion = parseInt(''+fullVersion,10);
    if (isNaN(majorVersion)) {
        fullVersion  = ''+parseFloat(navigator.appVersion);
        majorVersion = parseInt(navigator.appVersion,10);
    }
    if (validBrowser){
        msg = "Valid browser!";
    }
    else{
        msg = "You are using " + browserName + ", please use Chrome or Firefox!";
    }
    console.log(msg);
    return msg;
}

function isChrome(){
    let nAgt = navigator.userAgent;
    if (nAgt.indexOf("Chrome")!=-1) {
        return true;
    }
    return false;
}

 async function initPyodide(){
    await loadPyodide({
          indexURL : "https://cdn.jsdelivr.net/pyodide/v0.17.0/full/"
        });
    let wheel = "./iheartla-0.0.1-py3-none-any.whl";
    pythonCode = `
    import micropip
    micropip.install('appdirs')
    micropip.install('tatsu')
    micropip.install('${wheel}')
    `
    await pyodide.loadPackage(['micropip']);
    await pyodide.runPython(pythonCode);
    activateBtnStatus();
}

async function background(source){
    try {
        const {results, error} = await asyncRun(source);
        activateBtnStatus();
        if (results) {
            console.log('pyodideWorker return results: ', results);
            if (Array.isArray(results)){
              updateEditor(results);
            }
            else{
                console.log(results)
                updateError(results);
            }
        } else if (error) {
            updateError(error);
            console.log('pyodideWorker error: ', error);
        }
    }
    catch (e){
        console.log(`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`)
        activateBtnStatus();
    }
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
    pythonCode = `
import iheartla.la_parser.parser
source_code = r"""${source}"""
code = iheartla.la_parser.parser.compile_la_content(source_code)
`
    setTimeout(function(){
        try {
            pyodide.runPython(pythonCode);
            let code = pyodide.globals.get('code');
            if (typeof code === 'string'){
                updateError(code);
            }
            else{
                updateEditor(code.toJs());
            }
        }
        catch (error){
            console.log('Compile error!');
            updateError('Compile error!');
        }
        }, 1000);
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

function showMsg(msg, error=false){
    msg = msg.replaceAll('\n', '<br>')
    document.getElementById("msg").hidden = false;
    document.getElementById("msg").innerHTML = msg;
    if(!error) {
        // notice, auto hide
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



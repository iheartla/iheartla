"""Check the web page (docs/) in a headless browser with both compilers.

usage: uv run --with playwright python rust/tools/web_check.py
  (first: uv run --with playwright python -m playwright install chromium)

Serves docs/ locally, opens the page with ?compiler=rust, compiles a program
and an I❤️MESH program, checks the NumPy/C++/LaTeX/MATLAB editors and the
rendered MathJax, then switches to the Python compiler (Pyodide) and
compiles again. Prints timings.
"""
import functools
import http.server
import os
import threading
import time

from playwright.sync_api import sync_playwright

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'docs')
PROGRAM = """y_i = b ⋅ (A_i x_i) + c
where
A_i ∈ ℝ^(m×n)
x_i ∈ ℝ^n
b ∈ ℝ^m
c ∈ ℝ"""
MESH = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'corpus', 'mesh', 'one_ring.ila')).read()

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
handler.log_message = lambda *a: None
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = 'http://127.0.0.1:{}/index.html'.format(server.server_address[1])


def compile_on(page, source, timeout_ms):
    page.evaluate("src => ace.edit('editor').setValue(src, -1)", source)
    page.evaluate("() => ace.edit('python').setValue('', -1)")
    t = time.time()
    page.click('#compile')
    page.wait_for_function("() => ace.edit('python').getValue().length > 0 || document.getElementById('msg').innerText.length > 0", timeout=timeout_ms)
    elapsed = time.time() - t
    get = lambda e: page.evaluate("id => ace.edit(id).getValue()", e)
    return elapsed, {e: get(e) for e in ['python', 'cpp', 'latex', 'matlab']}, page.inner_text('#msg')


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    t = time.time()
    page.goto(url + '?compiler=rust')
    page.wait_for_function("() => !document.getElementById('compile').disabled", timeout=60000)
    print('rust: ready in {:.2f} s; selected: {}'.format(time.time() - t, page.is_checked('#compiler-rust')))
    for name, src in [('program', PROGRAM), ('I❤️MESH program', MESH)]:
        elapsed, out, msg = compile_on(page, src, 60000)
        page.wait_for_function("() => !document.getElementById('compile').disabled", timeout=60000)
        print('rust: {} compiled in {:.2f} s; sizes {}; msg {!r}; numpy has main: {}; c++ has main: {}; matlab has random data: {}'.format(
            name, elapsed, {k: len(v) for k, v in out.items()}, msg[:80], 'generateRandomData' in out['python'] and "__main__" in out['python'],
            'int main(' in out['cpp'], 'generateRandomData' in out['matlab']))
    page.wait_for_function("() => !document.getElementById('compile').disabled", timeout=60000)
    elapsed, out, msg = compile_on(page, MESH, 60000)
    print('rust: I❤️MESH program, repeat compile: {:.2f} s'.format(elapsed))
    page.wait_for_function("() => !document.getElementById('compile').disabled", timeout=60000)
    elapsed, out, msg = compile_on(page, 'x = = 1', 60000)
    print('rust: syntax error message: {!r}'.format(msg[:120]))
    print('rust: MathJax rendered: {}'.format(page.evaluate("() => document.getElementById('output').innerHTML.includes('mjx')")))
    # switch to the Python compiler
    t = time.time()
    page.click("label[for=compiler-python]")
    page.wait_for_function("() => !document.getElementById('compile').disabled", timeout=600000)
    print('python: ready in {:.2f} s; url: {}'.format(time.time() - t, page.url.split('?')[1][:40]))
    elapsed, out, msg = compile_on(page, PROGRAM, 600000)
    print('python: program compiled in {:.2f} s; sizes {}; msg {!r}'.format(elapsed, {k: len(v) for k, v in out.items()}, msg[:80]))
    for k in range(2):
        page.wait_for_function("() => !document.getElementById('compile').disabled", timeout=600000)
        elapsed, out, msg = compile_on(page, MESH, 600000)
        print('python: I❤️MESH program, {} compile: {:.2f} s ({!r})'.format('first' if k == 0 else 'repeat', elapsed, msg[:40]))
    print('page errors:', errors or 'none')
    browser.close()
server.shutdown()

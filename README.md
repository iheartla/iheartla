# I❤️LA: Compilable Markdown for Math

I❤️LA is a compilable markdown for math. It can generate working code in your favorite language (C++, Python, MATLAB, more to come) and LaTeX from snippets like this:

```
∑_i a_i b_i
where
a ∈ ℝ^n
b ∈ ℝ^n
```

or this:

```
A_ij = { 1 if (i,j) ∈ E
         0 otherwise
where
A ∈ ℝ^(n × n)
E ∈ { ℤ × ℤ }
n ∈ ℤ
```

or this:

```
[ t^3 t^2 t 1 ] [ -1  3 -3  1
                   3 -6  3  0
                  -3  3  0  0
                   1  0  0  0 ] P
where
t ∈ ℝ
P ∈ ℝ^(4 × d)
```

In other words, I❤️LA is a linear algebra domain specific language (DSL) that targets other languages. Write once, use everywhere.

For more, see the [wiki](https://github.com/pressureless/linear_algebra/wiki) or the [website](https://iheartla.github.io/). Join the [Discord](https://discord.gg/JvfYb6BXqJ).

## Running

The easiest way to run is in the web browser. You can use the [hosted version](https://iheartla.github.io/iheartla/) (no installation needed) or `cd web` and then `python3 -m http.server`.

The following instructions describe running the Python code directly.

To run the desktop GUI:

    python3 -m iheartla

or, if installed via conda,

    pythonw -m iheartla

You can also run as a command-line compiler:

    python3 -m iheartla --help

## Installing

You can find releases on the GitHub [release page](https://github.com/iheartla/iheartla/releases). The following instructions are for running from source.

I❤️LA depends on Python 3.x (>= Python 3.9) and several modules.

### Pip

Install the modules via `pip`:

    python3 -m venv .venv
    # activate your virtual environment via something like: source .venv/bin/activate
    
    pip3 install -r requirements.txt
    ## or directly
    pip3 install tatsu==5.8.3 regex appdirs wxpython PyMuPDF sympy
    
    ## For development, also install:
    pip3 install graphviz cppyy numpy scipy pyinstaller

(2023-05-10: There is a known bug with Python >= 3.10 and wxPython 4.2.0's PDF viewer. It will be fixed in the next release of wxPython. For now, either run on Python 3.9, live without PDF rendering, compile top-of-tree wxPython yourself, or change `/` to `//` in `wx/lib/pdfviewer/viewer.py:354` (so that `self.Ypagepixels` is an `int`). The relevant commit is [here](https://github.com/wxWidgets/Phoenix/commit/aa4394773a8696444ce5d8a90273d67796e499d0).)

### Poetry

Install the [Poetry](https://python-poetry.org/) dependency manager and run:

    poetry install --no-root --no-dev
    poetry shell

### Conda

Install [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
Miniconda is faster to install. (On Windows, choose the 64-bit Python 3.x version. Launch the Anaconda shell from the Start menu and navigate to this directory.)
Then:

    conda env create -f environment-{cli,gui,dev}.yml
    conda activate iheartla-{cli,gui,dev}

Choose `environment-{cli,gui,dev}.yml` according to whether you only want the command line (`cli`), also the GUI (`gui`), or also the development test suite (`dev`).
To update an already created environment if the `environment.yml` file changes or to change environments, activate and then run `conda env update --file environment-{cli,gui,dev}.yml --prune`.

If you are developing I❤️LA, the test suite needs a working C++ compiler and, optionally, the Graphviz graph visualization software (`brew install graphviz` if you're not using conda).

## Output Dependencies

To use the code output for the various backends, you will need:

* LaTeX: A working tex distribution with `xelatex` and `pdfcrop`
* Python: NumPy and SciPy
* MATLAB: MATLAB or Octave
* C++: Eigen. Compilation differs on different platforms. On macOS with Homebrew eigen: `c++ -I/usr/local/eigen3 output.cpp -o output`
* MATLAB: MATLAB or (untested) Octave

## Unicode Fonts

`DejaVu Sans Mono` is a font with good Unicode support. Windows users should install it. You can download it [here](https://dejavu-fonts.github.io/Download.html). The I❤️LA GUI will use it if installed.

## Packaging a release

To update the browser-based compiler, run `python3 setup.py sdist bdist_wheel` and then copy `dist/iheartla-0.0.1-py3-none-any.whl` to the `docs` directory.

**macOS**: `pyinstaller iheartla.spec`. The output `iheartla.app` is placed into `dist/`. Whoever is packaging should run `python3 -m iheartla --regenerate-grammar` at least once.

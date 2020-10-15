# I❤️LA: Compilable Markdown for Math

I❤️LA is a compilable markdown for math. It can generate working code in your favorite language (C++, Python, more to come) and LaTeX from snippets like this:

```
∑_i a_i b_i
where
a_i: ℝ
b_i: ℝ
```

or this:

```
A_ij = { 1 if (i,j) ∈ E
         0 otherwise
where
A: ℝ^(n,n)
E: { ℤ × ℤ }
n: ℤ
```

or this:

```
[ t^3 t^2 t 1 ] [ -1  3 -3  1
                   3 -6  3  0
                  -3  3  0  0
                   1  0  0  0 ] P
where
t: ℝ
P: ℝ^(4,d)
```

In other words, I❤️LA is a linear algebra domain specific language (DSL) that targets other languages. Write once, use everywhere.

For more, see the [wiki](https://github.com/pressureless/linear_algebra/wiki).

## Running

To run the GUI:

    python3 linear_algebra.py

You can also run as a command-line compiler:

    python3 linear_algebra.py --help

## Installing

You can find releases on the GitHub [release page](https://github.com/pressureless/linear_algebra/releases). The following instructions are for running from source.

I❤️LA depends on Python 3.x and several modules. You can install the modules via `pip`:

    pip3 install tatsu==4.4 regex wxpython PyMuPDF
    ## For development, also install:
    pip3 install graphviz cppyy numpy scipy pyinstaller

or install the [Poetry](https://python-poetry.org/) dependency manager and run:

    poetry env use python3.8 # needed only if you installed poetry via Homebrew
    poetry install --no-root --no-dev
    poetry shell

**NOTE**: As of this writing (2020-10-14), installing poetry via homebrew has a bug whose workaround is to type `poetry env use python3.8` before you run `poetry install --no-root --no-dev`.

If you are developing I❤️LA, the test suite needs a working C++ compiler and, optionally, the Graphviz graph visualization software (`brew install graphviz`).

### Output Dependencies

To use the code output for the various backends, you will need:

* LaTeX: A working tex distribution with `xelatex` and `pdfcrop`
* Python: NumPy and SciPy
* C++: Eigen. Compilation differs on different platforms. On macOS with Homebrew eigen `c++ -I/usr/local/eigen3 output.cpp -o output`

### Packaging a release

**macOS**: `pyinstaller --windowed --icon docs/icon/icon.icns linear_algebra.py`. The output `linear_algebra.app` is placed into `dist/`

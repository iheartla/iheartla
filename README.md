# I❤️LA

A linear algebra domain specific language (DSL) that targets other languages. Write once, use everywhere.

## Running

To run the GUI:

    python3 linear_algebra.py

or

    poetry run python linear_algebra.py

or

    pipenv run python linear_algebra.py

## Dependencies

Python 3.x and some modules:

    pip3 install tatsu wxpython graphviz PyMuPDF cppyy regex

or

    poetry install --no-root

or

    python3 -m venv .venv
    pipenv install

The first line (`python3 -m venv .venv`) works around wxPython needing a Framework Python on macOS [[1]](https://wiki.wxpython.org/wxPythonVirtualenvOnMac), [[2]](https://github.com/pypa/pipenv/issues/15). If you don't do it, you will need to run on macOS using `PYTHONHOME=$(pipenv --venv) python3 linear_algebra.py`.)

(We can do `pipenv run python linear_algebra.py` because wxPython needs a Framework python.)



Graphviz: Graph Visualization Software:

    brew install graphviz

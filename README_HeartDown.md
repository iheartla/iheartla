# H❤️rtDown: Authoring Linear Algebra Papers that Compile to Code Libraries for Execution and Metadata for Enhanced Reading

H❤️rtDown is an authoring environment for linear algebra papers. The papers compile to interactive web pages and code libraries that can be used inline to create figures or in external code.

## Installing

Install [Anaconda](https://www.anaconda.com/products/individual) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).
Miniconda is faster to install. (On Windows, choose the 64-bit Python 3.x version. Launch the Anaconda shell from the Start menu and navigate to this directory.)
Then:

    conda env create -f environment-heartdown.yml
    conda activate heartdown

To update an already created environment if the `environment-heartdown.yml` file changes or to change environments, activate and then run `conda env update --file environment-heartdown.yml --prune`.

## Running

To launch the editor, run:

    python server.py path/to/document.md

and then open `http://localhost:8000/` in a browser (Chrome is most tested).

To compile a paper from the command line:

    python server.py --paper path/to/document.md

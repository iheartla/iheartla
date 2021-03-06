# I ❤️LA + Pygments

This implements a lexer for I❤LA for pygments.

Usage:
Install pygments via pip or homebrew (`pip3 install pygments` or `brew install pygments`).

Basic usage:
`pygmentize -l ./iheartla_lexer.py -x -o <output_file.html> -O style=pastie -O full -O linenos <input file>`

The options `full` and `linenos` enable generating a full HTML file and line numbers, respectively.
To see possible styles, run `pygmentize -L styles`.

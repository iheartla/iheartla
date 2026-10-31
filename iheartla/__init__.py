# The grammar uses Unicode classes like \p{Lu}, which only the third-party
# `regex` module supports. TatSu (>= 5.7.4) compiles patterns with whatever
# `re` is, so make `import re` return `regex` before TatSu is imported.
# (Previously only __main__.py did this, so library use such as
# compile_la_content() needed TatSu <= 5.7.3, which imports regex itself.)
import sys
import regex
if "tatsu" in sys.modules and sys.modules.get("re") is not regex:
    import warnings
    warnings.warn("tatsu was imported before iheartla; I❤️LA's grammar needs tatsu to use the `regex` module. Import iheartla first.")
sys.modules["re"] = regex

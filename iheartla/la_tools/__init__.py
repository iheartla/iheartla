import sys

try:
    import regex as _regex
    sys.modules['re'] = _regex
except ImportError:
    # regex is a required dependency, but keep the original re module if it's truly unavailable.
    _regex = None

__all__ = ["la_helper",
           "la_logger",
           "la_msg",
           "la_visualizer",
           "parser_manager"]

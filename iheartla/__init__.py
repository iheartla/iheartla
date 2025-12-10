import sys

try:
    import regex as _regex  # Third-party module with Unicode \p support
    sys.modules['re'] = _regex
except Exception:
    # If regex is unavailable, keep stdlib re; downstream code will emit a clear error.
    _regex = None

try:
    from tatsu.util import misc as _tatsu_misc
except Exception:
    _tatsu_misc = None
else:
    def _ihla_match_to_find(match):
        if match is None:
            return None
        groups = match.groups(default=match.string[0:0])
        if not groups:
            return match.group()
        if len(groups) == 1:
            return groups[0] if groups[0] else match.group()
        return groups or match.group()

    _tatsu_misc.match_to_find = _ihla_match_to_find
    try:
        from tatsu import buffering as _tatsu_buffering
    except Exception:
        _tatsu_buffering = None
    else:
        _tatsu_buffering.match_to_find = _ihla_match_to_find

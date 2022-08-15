from .de_walker import *
from .de_light_walker import *

_de_walker = None
_de_light_walker = None


def get_de_walker():
    global _de_walker
    if _de_walker:
        _de_walker.reset()
    else:
        _de_walker = DeWalker()
    return _de_walker


def get_de_light_walker():
    global _de_light_walker
    if _de_light_walker:
        _de_light_walker.reset()
    else:
        _de_light_walker = DeLightWalker()
    return _de_light_walker


def parse_de_content(model, content):
    de_light_walker = get_de_light_walker()
    de_light_walker.walk(model)
    if de_light_walker.has_de:
        ConfMgr.getInstance().parse(de_light_walker)
        de_walker = get_de_walker()
        new_content = de_walker.walk(model)
        return new_content
    return content

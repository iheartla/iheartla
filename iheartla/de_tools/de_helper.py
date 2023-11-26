import base64
import copy
import os
import time
from enum import Enum, Flag
from tatsu._version import __version__
import sys
from textwrap import dedent
import keyword
from sympy import *
import regex as re
from pathlib import Path


class DParserTypeEnum(Flag):
    INVALID = 0
    #
    MESH = 1  # export iheartmesh code
    FEM = 2   # fem library
    SYM = 4   # symbolic
    MC = 8    # other

"""Run the test suite's MATLAB checks in GNU Octave instead of MATLAB.

`install()` puts a stand-in for MathWorks' `matlab` engine module in sys.modules:
matlab.double(...) and the integer types are NumPy arrays, and functions are called
through oct2py. base_python_test.py installs it when IHEARTLA_OCTAVE is set:

    IHEARTLA_OCTAVE=1 sh run_test.sh

It needs `octave-cli` (Homebrew's `octave` has it; OCTAVE_EXECUTABLE overrides the name)
and `pip install oct2py`. With IHEARTLA_OCTAVE_VERBOSE set, it prints how many MATLAB
functions ran, to show the MATLAB checks weren't skipped.
"""
import atexit
import os
import sys
import types

import numpy as np

calls = [0]


class Engine:
    def __init__(self):
        import oct2py
        self.oc = oct2py.Oct2Py(executable=os.environ['OCTAVE_EXECUTABLE'])

    def genpath(self, d):
        return os.path.abspath(d)

    def addpath(self, d, nargout=0):
        self.oc.addpath(d)

    def __getattr__(self, name):
        def call(*args):
            calls[0] += 1
            # (the test writes each function's .m file just before calling it)
            self.oc.eval('rehash')
            return self.oc.feval(name, *args)
        return call


def install():
    # (oct2py starts a session with this executable when it is imported)
    os.environ.setdefault('OCTAVE_EXECUTABLE', 'octave-cli')
    matlab = types.ModuleType('matlab')
    for t in ['double', 'single', 'int8', 'int16', 'int32', 'int64', 'uint8', 'int']:
        setattr(matlab, t, lambda x, t=t: np.array(x, dtype=float if t in ('double', 'single') else np.int64))
    matlab.engine = types.ModuleType('matlab.engine')
    matlab.engine.start_matlab = Engine
    sys.modules['matlab'] = matlab
    sys.modules['matlab.engine'] = matlab.engine
    if os.environ.get('IHEARTLA_OCTAVE_VERBOSE'):
        atexit.register(lambda: print('MATLAB functions run in Octave:', calls[0]))

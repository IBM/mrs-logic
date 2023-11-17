from .context import *
from .mrs_logic import *
from .solution import *
from .solver import *

__all__ = [
    'Context',
    'Solution',
    'Solver',
    'SolverError',
    'get_current_context',
    'parse',
    'solve',
    'solve1',
]

__version__ = '0.1'

Context._stack.append(Context())

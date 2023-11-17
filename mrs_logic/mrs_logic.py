from delphin.codecs import simplemrs
from delphin.mrs._mrs import MRS

from . import util
from .context import Context
from .solver import Solver

__all__ = [
    'get_current_context',
    'parse',
    'solve',
    'solve1',
]

# Override Delphin's MRS.__str__ method to pretty-print MRS.
MRS.__str__ = (lambda x: simplemrs.encode(
    x, indent=True, properties=False, lnk=False))

MRS._md5sum = property(lambda x: util.md5(
    str(x).encode('utf-8')).hexdigest())


def get_current_context():
    """Gets the current MRS Logic context.

    Returns:
       An MRS Logic :class:`Context`.
    """
    return Context._get()


def parse(input, start=0, stop=None, step=1, grammar=None, context=None):
    """Parses input sentence.

    Parameters:
       input: Sentence to parse or ACE parser response.
       start: Start of MRS sequence.
       stop: Stop of MRS sequence.
       step: Step of MRS sequence.
       grammar: Grammar file to use.
       context: :class:`Context`.

    Returns:
        An MRS iterator.
    """
    context = Context._get(context)
    if isinstance(input, str):
        ret = _parse(input, grammar, context)
    else:
        ret = input
    n = ret.get('readings', 0)
    if stop is None:
        stop = n
    else:
        stop = min(n, stop)
    for i in range(start, stop, step):
        yield ret.result(i).mrs()


def _parse(input, grammar=None, context=None):
    context = Context._get(context)
    if grammar:
        ace = context._mk_ace(grammar=grammar)
    else:
        ace = context.ace
    return ace.parse(input)


def solve(
        input, start=0, stop=None, step=1, order='dfs',
        modulo_entailment=False, entailment_method='z3',
        grammar=None, context=None):
    """Parses and solves input sentence, MRS, or MRS iterator.

    Parameters:
       input: Sentence to parse, MRS, or MRS iterator.
       start: Start of MRS sequence.
       stop: Stop of MRS sequence.
       step: Step of MRS sequence.
       order: Order of traversal of solutions ('dfs' or 'bfs').
       modulo_entailment: Whether to skip solutions which are
          entailed by some other solution in the resulting sequence.
       entailment_method: Entailment method to use.
       grammar: Grammar file to use.
       context: :class:`Context`.

    Returns:
       A :class:`Solution` iterator.

    The call:

    .. code-block:: python

       it = solve('The sky is blue')

    is equivalent to:

    .. code-block:: python

       it = solve(parse('The sky is blue'))
    """
    if isinstance(input, str):
        it = parse(input, start, stop, step, grammar, context)
    else:
        if isinstance(input, MRS):
            input = [input]
        it = util.islice_extended(input, start, stop, step)
    sn_it = _solve(
        it,
        order=order,
        modulo_entailment=modulo_entailment,
        entailment_method=entailment_method,
        context=context)
    if modulo_entailment:
        def cmp(s, t):
            if s.entails(t, entailment_method):
                return 0
            else:
                return -1
        return util.unique_everseen(sn_it, util.cmp_to_key(cmp))
    else:
        return sn_it


def _solve(mrs_it, **kwargs):
    order = kwargs.pop('order')
    context = kwargs.pop('context')
    if order == 'dfs':
        for mrs in mrs_it:
            sn_it = (Solver(mrs, context=context)
                     .iterate_solutions(**kwargs))
            for sn in sn_it:
                yield sn
    else:
        sn_it = list(map((lambda mrs: Solver(mrs, context=context)
                          .iterate_solutions(**kwargs)),
                         mrs_it))
        while True:
            done = True
            for it in sn_it:
                sn = next(it, None)
                if sn is not None:
                    done = False
                    yield sn
            if done:
                break


def solve1(input, start=0, stop=None, step=1, index=0, grammar=None,
           context=None):
    """Parses and solves input sentence, MRS, or MRS iterator.

    Parameters:
       input: Sentence to parse, MRS, or MRS iterator.
       start: Start of MRS sequence.
       stop: Stop of MRS sequence.
       step: Step of MRS sequence.
       index: Solution index.
       grammar: Grammar file to use.
       context: :class:`Context`.

    Returns:
      The :class:`Solution` at index in the solution sequence, or None (no
      such solution).
    """
    it = solve(
        input, start=start, stop=stop, step=step, grammar=grammar,
        context=context)
    return util.nth(it, index)

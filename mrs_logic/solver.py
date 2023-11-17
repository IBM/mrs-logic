from delphin.codecs import mrsprolog

from . import util
from .context import Context
from .solution import Solution
from .utool import UTool, UToolError

__all__ = [
    'Solver',
    'SolverError',
]


class SolverError(util.Error):
    """Raised on :class:`Solver` errors."""
    pass


class Solver(util.Base):
    """MRS solver.

    Parameters:
       mrs: MRS to solve.
       context: :class:`Context`.

    The *solver* computes solutions to a given MRS."""

    def __init__(self, mrs, context=None):
        self._context = Context._get(context)
        self._mrs = mrs
        self._mrs.icons = []    # UTool  can't handler ICONS.
        self._scopes = self._mrs.scopes()[1]
        self._scopes_set = set(self._scopes)

        pmap = {}
        for h,eps in mrs.scopes()[1].items():
            for e in eps:
                for a,v in e.args.items():
                    if v in pmap:
                        pmap[v].append(h)
                    else:
                        pmap[v] = [h]
        self.pre_map = pmap

        try:
            self._utool = UTool(mrsprolog.encode(mrs))
        except UToolError as err:
            raise SolverError(str(err))
        self._senses = None

    @property
    def context(self):
        """The associated :class:`Context`."""
        return self._context

    @property
    def mrs(self):
        """The associated MRS."""
        return self._mrs

    @property
    def scopes(self):
        """The associated MRS scopes."""
        return self._scopes

    @property
    def senses(self):
        """The senses associated to EPs."""
        if self._senses is None:
            self._senses = self._context.ukb.resolve(self._mrs)
        return self._senses

    def is_solvable(self):
        """Tests whether MRS is solvable.

        Returns:
           ``True`` if successful; ``False`` otherwise.
        """
        return self._utool.is_solvable()

    def count_solutions(self):
        """Counts the number of solutions to MRS.

        Returns:
           The number of solutions to MRS.
        """
        return self._utool.count_solved_forms()

    def get_root(self, plugs):
        map = self.pre_map.copy()
        for h,l in plugs.items():
            if l in map:
                raise Exception('a label from plugs in the pre map')
            else:
                map[l] = [h]
                
        root = self.mrs.scopes()[0]
        while ( root in map ):
            root = map[root][0]
        return root


    def iterate_solutions(
            self, start=0, stop=None, step=1,
            modulo_entailment=False, entailment_method='z3'):
        """Iterates over the solutions to MRS.

        Parameters:
           start: Start of solution sequence.
           stop: Stop of solution sequence.
           step: Step of solution sequence.
           modulo_entailment: Whether to skip solutions which are
              entailed by some other solution in the resulting sequence.
           entailment_method: Entailment method to use.

        Returns:
           A :class:`Solution` iterator.
        """
        if modulo_entailment:
            return self._iterate_solutions_modulo_entailment(
                start, stop, step, entailment_method)
        else:
            return self._iterate_solutions(start, stop, step)

    def _iterate_solutions(self, start, stop, step):
        it_index = util.islice_extended(util.count(), start, stop, step)
        it_forms = util.islice_extended(
            self._utool.iterate_solved_forms(), start, stop, step)
        for i, (plugs, subst) in zip(it_index, it_forms):
            root = self.get_root(plugs)
            yield Solution(self, i, root, plugs)

    def _iterate_solutions_modulo_entailment(
            self, start, stop, step, method):
        keep = set(self.iterate_solutions(start, stop, step))
        for s, t in util.combinations(keep, 2):
            if s not in keep or t not in keep:
                continue
            if s.entails(t, method=method):  # s ⊢ t
                keep.remove(t)
            elif t.entails(s, method=method):  # t ⊢ s
                keep.remove(s)
        return iter(sorted(keep, key=lambda s: s.index))

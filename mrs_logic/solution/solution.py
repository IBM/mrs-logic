from .. import util
from ..context import Context
from .converter import Converter
from .converter_pydot import ConverterPydot
from .converter_ulkb import ConverterULKB

__all__ = [
    'Solution',
]


class Solution(util.Base):
    """A solution to an MRS."""

    def __init__(self, solver, index, root, plugs, context=None):
        self._context = Context._get(context)
        self._solver = solver
        self._index = index
        self._root = root
        self._plugs = plugs

    @property
    def solver(self):
        """The associated :class:`Solver`."""
        return self._solver

    @property
    def context(self):
        """The associated :class:`Context`."""
        return self._context

    @property
    def mrs(self):
        """The associated MRS."""
        return self._solver._mrs

    @property
    def scopes(self):
        """The associated MRS scopes."""
        return self._solver._scopes

    @property
    def senses(self):
        """The senses associated to EPs."""
        return self._solver.senses

    @property
    def index(self):
        """Solution index."""
        return self._index

    @property
    def root(self):
        """Solution root."""
        return self._root

    @property
    def plugs(self):
        """Solution plugs."""
        return self._plugs

    def entails(self, other, method='z3'):
        """Tests whether this solution entails another.

        Parameters:
           other: Another :class:`Solution`.
           method: Entailment method to use.

        Returns:
           ``True`` if successful; ``False`` otherwise.
        """
        import z3
        try:
            s = z3.Solver()
            s.add(z3.Not(z3.Implies(self.to_z3(), other.to_z3())))
            return s.check() == z3.unsat
        except z3.Z3Exception:
            return False

    def to_dot(self, **kwargs):
        """Converts solution to dot string.

        Parameters:
           kwargs: Options to converter.

        Returns:
           The resulting string.
        """
        return self._solver._utool.serialize(
            encoder='domgraph-dot', index=self.index)

    def to_prolog(self, **kwargs):
        """Converts solution to Prolog string.

        Parameters:
           kwargs: Options to converter.

        Returns:
           The resulting string.
        """
        return self._solver._utool.serialize(
            encoder='term-prolog', index=self.index)

    def to_pydot(self, **kwargs):
        """Converts solution to Pydot graph.

        Parameters:
           kwargs: Options to converter.

        Returns:
           The resulting graph.
        """
        return Converter.convert(
            self, format=ConverterPydot.format, context=self.context,
            **kwargs)

    @util.lru_cache
    def to_ulkb(self, context=None, **kwargs):
        """Converts solution to ULKB formula.

        Parameters:
           context (:class:`Context`): MRS Logic context.
           kwargs: Options to converter.

        Returns:
           The resulting ULKB formula.

        The supported options are listed below.  Their default values are
        kept in an entry called ``to_ulkb`` in :attr:`Context.options`.

        * **annotate_ep_lnk** (bool, default ``False``) -- Whether to
          annotate constants with EP surface alignment (i.e., "lnk").

        * **annotate_ep_properties** (bool, default ``False``) -- Whether to
          annotate variables with EP properties (e.g., "PERS", "NUM", "IND",
          etc.).

        * **annotate_sense_labels** (bool, default ``False``) -- Whether to
          annotate sense labels into constants.

        * **annotate_senses** (bool, default ``False``) -- Whether to
          resolve and annotate senses into constants.

        * **bind_evars** (bool, default ``True``) -- Whether to bind
          *e*-vars using existentials.

        * **bind_ivars** (bool, default ``True``) -- Whether to bind
          *i*-vars using existentials.

        * **bind_uvars** (bool, default ``True``) -- Whether to bind
          *u*-vars using existentials.

        * **drop_evars** (bool, default ``False``) -- Whether to drop
          (ignore) *e*-vars.

        * **drop_ivars** (bool, default ``False``) -- Whether to drop
          (ignore) *i*-vars.

        * **drop_uvars** (bool, default ``False``) -- Whether to drop
          (ignore) *u*-vars.

        * **mk_p_equal** (list, default ``[]``) -- Semantic predicates to
          treat as logical equality.

        * **mk_p_not** (list, default ``[]``) -- Semantic predicates to
          treat as logical negation.

        * **mk_q_exists** (list, default ``[]``) -- Semantic
          predicates to treat as existentials.

        * **mk_q_exists1** (list, default ``[]``) -- Semantic
          predicates to treat as unique existentials.

        * **mk_q_forall** (list, default ``[]``) -- Semantic predicates to
          treat as universals.

        * **mk_q_forall_implies_not** (list, default ``[]``) -- Semantic
          predicates to treat as universals implying a negation.

        * **passthrough** (list, default ``[]``) -- Semantic predicates to
          pass-through unaltered.

        * **translate_predicates** (bool, default ``True``) -- Whether to
          translate semantic predicates referring to known logical
          predicates.

        * **translate_quantifiers** (bool, default ``True``) -- Whether to
          translate semantic predicates referring known logical quantifiers.

        * **universe_type** (ULKB type, default ``None``) -- Type to use as
          universe type.  If ``None``, new type variables *a0*, *a1*, *a2*,
          etc., are generated and used whenever a distinct type is needed.

        """
        return Converter.convert(
            self, format=ConverterULKB.format, context=self.context,
            **kwargs)

    def to_z3(self, **kwargs):
        """Converts solution to Z3 formula.

        Parameters:
           kwargs: Options to converter.

        Returns:
           The resulting Z3 formula.
        """
        return self.to_ulkb(**kwargs).to_z3()

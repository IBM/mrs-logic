from . import util
from .ace import ACE
from .ukb import UKB

__all__ = [
    'Context',
    'Options',
]


class Options(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __deepcopy__(self, memo=None):
        return self.__class__(util.deepcopy(dict(self), memo=memo))


class Context(util.Base):
    """MRS Logic context.

    Parameters:
       grammar: Grammar file to use.
       ace: ACE instance.
       ukb: UKB instance.

    The *context* stores the global parameters of the MRS Logic library,
    including the current ACE parser and UKB resolver to use.

    Most API functions accept a :code:`context` argument which can be used
    to change the context in which the function executes.  For example, to
    run :func:`parse` in a custom context we can use:

    .. code-block:: python

       parse('The sky is blue.', context=Context(grammar='custom-erg.dat'))

    Alternatively, we can also use Python's :code:`with` to change the
    current context of a given block.  For example:

    .. code-block:: python

       with Context(grammar='custom-erg.dat'):
          parse('The sky is blue.')
    """

    _stack = []
    _mk_ace = ACE
    _mk_ukb = UKB
    _default_options = Options(dict())

    @classmethod
    def get_current_context(cls):
        assert cls._stack
        return cls._stack[-1]

    @classmethod
    def _get(cls, context=None):
        if context is None:
            return cls.get_current_context()
        else:
            return context

    def __init__(self, grammar=None, ace=None, ukb=None):
        self._grammar = grammar
        self._ace = ace
        self._ukb = ukb
        self._options = util.deepcopy(self._default_options)

    def __enter__(self):
        self._stack.append(self)
        return self

    def __exit__(self, *args):
        self._stack.pop()

    @property
    def options(self):
        """The associated options dictionary."""
        return self._options

    @property
    def ace(self):
        """The associated ACE instance."""
        if self._ace is None:
            self.reset_ace()
            assert self._ace is not None
        return self._ace

    @property
    def ukb(self):
        """The associated UKB instance."""
        if self._ukb is None:
            self.reset_ukb()
            assert self._ukb is not None
        return self._ukb

    def reset_ace(self, **kwargs):
        """Resets ACE instance.

        Parameters:
           kwargs: Options to ACE.

        Returns:
           The reset :class:`ACE` instance.
        """
        self._ace = ACE(
            grammar=kwargs.pop('grammar', self._grammar), **kwargs)
        return self._ace

    def reset_ukb(self, **kwargs):
        """Resets UKB instance.

        Parameters:
           kwargs: Options to ACE.

        Returns:
           The reset :class:`UKB` instance.
        """
        self._ukb = UKB(**kwargs)
        return self._ukb

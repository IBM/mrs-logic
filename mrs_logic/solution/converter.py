from .. import util
from ..context import Context

__all__ = [
    'Converter',
]


class Converter(util.ABC):

    converters = dict()

    @classmethod
    def __init_subclass__(cls, **kwargs):
        kwargs['class'] = cls
        cls.format = kwargs['format']
        cls.converters[cls.format] = kwargs

    @classmethod
    def convert(cls, solution, format='ulkb', context=None, **kwargs):
        if format not in cls.converters:
            raise ValueError(f'bad format: {format}')
        conv_cls = cls.converters[format]['class']
        return conv_cls(solution, context=context, **kwargs)._do_convert()

    def __init__(self, solution, context=None, **kwargs):
        self._context = Context._get(context)
        self._solution = solution
        self._kwargs = kwargs

    @util.abstractclassmethod
    def _do_convert(self):
        raise NotImplementedError

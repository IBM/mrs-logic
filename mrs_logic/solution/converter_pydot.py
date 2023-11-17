from .. import util
from .converter import Converter

__all__ = [
    'ConverterPydot',
]


class ConverterPydot(Converter, format='pydot'):

    def __init__(self, solution, **kwargs):
        import pydot
        super().__init__(solution, **kwargs)
        self._pydot = pydot

    def _do_convert(self):
        self._dot = self._solution.to_dot()
        graph = self._pydot.graph_from_dot_data(self._dot)[0]

        def show():
            from IPython.display import SVG, display
            display(SVG(graph.create_svg()))
        setattr(graph, 'show', show)
        return graph

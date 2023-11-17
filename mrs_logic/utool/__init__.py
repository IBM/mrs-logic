import os

import jpype

from .. import util

__all__ = [
    'UToolError',
    'UTool',
]

UTOOL_JAR = os.getenv(
    'UTOOL_JAR',
    str(util.Path(__file__).resolve().parent / 'utool-3.4.jar'))

jpype.startJVM(classpath=[UTOOL_JAR])

java_io = jpype.JPackage('java.io')
ByteArrayInputStream = java_io.ByteArrayInputStream
FileWriter = java_io.FileWriter
InputStreamReader = java_io.InputStreamReader
OutputStreamWriter = java_io.OutputStreamWriter
StringWriter = java_io.StringWriter

java_lang = jpype.JPackage('java.lang')
System = java_lang.System

domgraph = jpype.JPackage('de.saar.chorus.domgraph')
Chart = domgraph.chart.Chart
ChartSolver = domgraph.chart.ChartSolver
CodecManager = domgraph.codec.CodecManager
DomGraph = domgraph.graph.DomGraph
NodeLabels = domgraph.graph.NodeLabels
SolvedFormIterator = domgraph.chart.SolvedFormIterator

_codec_manager = CodecManager()
_codec_manager.registerAllDeclaredCodecs()


class UToolError(util.Error):
    pass


class UTool(util.Base):

    @classmethod
    def _get_decoder(self, name, options):
        dec = _codec_manager.getInputCodecForName(name, options)
        if dec is None:
            raise UToolError(f'no such decoder: {name}')
        return dec

    @classmethod
    def _get_encoder(self, name, options):
        enc = _codec_manager.getOutputCodecForName(name, options)
        if enc is None:
            raise UToolError(f'no such encoder: {name}')
        return enc

    def __init__(
            self, input, decoder='mrs-prolog', decoder_options=''):
        self._graph = DomGraph()
        self._labels = NodeLabels()
        self._chart = None
        self._solve_status = None
        self._solved_forms_count = None
        self._load(input, decoder, decoder_options)

    def _load(self, input, decoder, decoder_options):
        dec = self._get_decoder(decoder, decoder_options)
        reader = InputStreamReader(
            ByteArrayInputStream(input.encode('utf-8')))
        try:
            dec.decode(reader, self._graph, self._labels)
        except Exception as err:
            raise UToolError(str(err))

    def solve(self):
        if self._solve_status is None:
            self._chart = Chart(self._labels)
            self._solve_status = ChartSolver.solve(self._graph, self._chart)
        return self._solve_status

    def is_solvable(self):
        return self.solve()

    def count_solved_forms(self):
        if self._solved_forms_count is None:
            self._solved_forms_count = (
                self._chart.countSolvedForms().longValue()
                if self.solve() else 0)
        return self._solved_forms_count

    def iterate_solved_forms(self):
        if not self.solve():
            return iter([])
        for spec in SolvedFormIterator(self._chart, self._graph):
            domedges, subst = spec.getDomEdges(), spec.getSubstitution()
            yield (
                dict(map(lambda e: (e.getSrc(), e.getTgt()), domedges)),
                dict(subst))

    def serialize(
            self, to=None, index=None,
            encoder='plugging-oz', encoder_options=''):
        enc = self._get_encoder(encoder, encoder_options)
        if to is None:
            writer = StringWriter()
        else:
            writer = FileWriter(to)
        if index is None:
            self._serialize(enc, writer)
        else:
            self._serialize_ith(enc, writer, index)
        writer.flush()
        return str(writer.toString()) if to is None else None

    def _serialize(self, enc, writer):
        enc.print_header(writer)
        if self._solve_status is None:
            enc.encode(self._graph, self._labels, writer)
        else:
            enc.print_start_list(writer)
            it = SolvedFormIterator(self._chart, self._graph)
            for i, spec in enumerate(it):
                if i > 0:
                    enc.print_list_separator(writer)
                enc.encode(
                    self._graph.makeSolvedForm(spec),
                    self._labels.makeSolvedForm(spec),
                    writer)
            enc.print_end_list(writer)
        enc.print_footer(writer)

    def _serialize_ith(self, enc, writer, i):
        it = iter(SolvedFormIterator(self._chart, self._graph))
        spec = util.nth_or_last(it, i)
        enc.encode(
            self._graph.makeSolvedForm(spec),
            self._labels.makeSolvedForm(spec),
            writer)

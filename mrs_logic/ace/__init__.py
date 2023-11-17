from .. import util

__all__ = [
    'ACE_Error',
    'ACE',
]


class ACE_Error(util.Error):
    pass


class ACE(util.Base):
    _envvars = {
        'ACE_GRAMMAR': None,
        'ACE_LOG': None,
    }

    def __init__(self, grammar=None, log=None):
        from delphin.ace import ACEParser, ACEProcessError
        self._grammar = grammar or self._getenv('ACE_GRAMMAR', 'erg.dat')
        self._log = None
        if not util.Path(self._grammar).is_file():
            raise ACE_Error(f'no such grammar file: {self._grammar}')
        self._log = log or self._getenv('ACE_LOG', util.os.devnull)
        self._log = open(self._log, 'a')
        try:
            self._parser = ACEParser(self._grammar, stderr=self._log)
        except ACEProcessError as err:
            raise ACE_Error(str(err))

    def __del__(self):
        if self._log is not None:
            self._log.close()

    def parse(self, text):
        return self._parser.process_item(text)

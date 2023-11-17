import logging
import re
import subprocess

from .. import util

__all__ = [
    'UKB_Error',
    'UKB',
]


class UKB_Error(util.Error):
    pass


class UKB(util.Base):
    _envvars = {
        'UKB_HOST': 'localhost',
        'UKB_PORT': 2803,
        'UKB_WSD_BIN': 'ukb_wsd',
        'UKB_WSD_ARGS': '--daemon --ppr',
        'UKB_WSD_ARGS_EXTRA': '',
        'UKB_KB_BIN': None,
        'UKB_DICT_TXT': None,
    }

    _server = None              # server process
    _client_counter = 0         # total number of active clients

    @classmethod
    def _run_cmd(cls, cmd, err_prefix):
        try:
            res = subprocess.run(
                cmd, shell=True, text=True, capture_output=True)
        except Exception as err:
            raise UKB_Error(err_prefix + str(err))
        if res.returncode != 0:
            raise UKB_Error(err_prefix + res.stderr or '(no explanation)')
        return res

    @classmethod
    def _server_start(cls):
        from pathlib import Path
        kb_bin = cls._getenv(
            'UKB_KB_BIN', cls._getdir() / 'wn30g.bin')
        dict_txt = cls._getenv(
            'UKB_DICT_TXT', cls._getdir() / 'wn30_dict.txt')
        cmd = ' '.join([
            cls._getenv('UKB_WSD_BIN'),
            cls._getenv('UKB_WSD_ARGS'),
            cls._getenv('UKB_WSD_ARGS_EXTRA'),
            f'--port {cls._getenv("UKB_PORT")}',
            f'-K {kb_bin}',
            f'-D {dict_txt}',
        ])
        cls._logger.info(f'running: {cmd}')
        cls._run_cmd(cmd, 'cannot start UKB server: ')
        cls._logger.info('server started')

    @classmethod
    def _server_stop(cls):
        cmd = ' '.join([
            cls._getenv('UKB_WSD_BIN'),
            f'--port {cls._getenv("UKB_PORT")}',
            '--shutdown',
        ])
        cls._logger.info(f'running: {cmd}')
        cls._run_cmd(cmd, 'cannot stop server: ')
        cls._logger.info('server stopped')

    def __init__(self, start_server=True):
        self._host = self._getenv('UKB_HOST')
        self._port = self._getenv('UKB_PORT')
        self._start_server = start_server
        self.__class__._client_counter += 1
        if start_server and self.__class__._client_counter == 1:
            self._server_start()

    def __del__(self):
        self.__class__._client_counter -= 1
        if self.__class__._client_counter == 0:
            self._server_stop()

    def _get_words(
            self, mrs, _tab={'n': 'n', 'j': 'a', 'r': 'r', 'v': 'v'}):
        from delphin import predicate
        words = []
        for p in mrs.rels:
            r = predicate.split(p.predicate)
            s = predicate.is_surface(p.predicate)
            lemma, pos = None, None
            if s and r[1] and r[1] in 'nav':
                lemma, pos = r[0], r[1]
            elif s and r[1] and r[1] == 'u':
                lemma, pos = r[0].split('/')
                pos = _tab[pos[0]]
            elif not s and r[0] == 'named':
                lemma, pos = p.carg.lower(), 'n'
            else:
                continue
            words.append({'id': p.id, 'lemma': lemma, 'pos': pos})
        return words

    def _parse_response(
            self, text, re_answer=re.compile(
                r'^sentence_1\s*(\w+)\s*([\w\-]*)\s*!!\s*(\w+)$')):
        for line in text.split('\n'):
            m = re_answer.match(line)
            if m:
                var, wnid, word = m.groups()
                yield (var, (wnid, word))

    def resolve(self, mrs):
        from subprocess import run
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(
                prefix='ukb_', suffix='.txt', mode='w', delete=True) as temp:
            text = 'sentence_1\n'
            for w in self._get_words(mrs):
                text += f"{w['lemma']}#{w['pos']}#{w['id']}#1 "
            text += '\n'
            temp.write(text)
            temp.flush()
            cmd = ' '.join([
                self._getenv('UKB_WSD_BIN'),
                '--client',
                '-v',
                f'--port {self._getenv("UKB_PORT")}',
                temp.name,
            ])
            self._logger.debug('Sent:\n%s', text)
            res = self._run_cmd(cmd, 'resolve failed: ')
            self._logger.debug('Received:\n%s', res.stdout)
            return dict(self._parse_response(res.stdout))

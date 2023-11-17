import logging
import os
from abc import ABC, ABCMeta, abstractclassmethod, abstractmethod
from copy import deepcopy
from functools import cached_property, cmp_to_key, lru_cache
from hashlib import md5
from itertools import chain, combinations, count, repeat
from pathlib import Path

from more_itertools import (islice_extended, nth, nth_or_last, peekable,
                            take, unique_everseen)


class BaseMeta(ABCMeta):
    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)
        cls._logger = logging.getLogger(cls.__qualname__)
        return cls


class Base(ABC, metaclass=BaseMeta):
    _envvars = {}

    @classmethod
    def _getenv(cls, key, default=None):
        val = cls._envvars.get(key, None)
        return os.getenv(key, val if val is not None else default)

    @classmethod
    def _getdir(cls):
        return get_module_dir(cls.__module__)


class Error(Exception):
    def __init__(self, msg=None):
        super().__init__(self, msg)
        self.msg = msg

    def __str__(self):
        return self.msg


def get_module_dir(modname):
    from importlib import util as importlib_util
    return Path(importlib_util.find_spec(modname).origin).parent

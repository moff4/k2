#!/use/bin/env python3

import os

from k2.aeon.responses.base_response import Response
from k2.utils.autocfg import AutoCFG
from k2.utils.http import (
    SMTH_HAPPENED,
    NOT_FOUND,
    CONTENT_HTML,
    content_type as content_type,
)

from .runner import ScriptRunner

BIN = 'binary'
TEXT = 'text'


class StaticResponse(Response):

    defaults = {
        'cache_min': 120,
        'max_response_size': (2 ** 18),
    }

    def __init__(self, request, **kwargs):
        super().__init__()
        self.cfg = AutoCFG(self.defaults).update_fields(kwargs)
        self.content_mod = None
        self.vars = kwargs.get('vars') or {}
        self.req = request
        self._data = ''

    def usefull_inserts(self, az):
        """
            az - list of tuples:
              [.., (template, data), ..]
            find template => change into data
        """
        if self.content_mod == TEXT:
            for i in az:
                while i[0] in self._data:
                    j = self._data.index(i[0])
                    self._data = self._data[:j] + i[1] + self._data[j + len(i[0]):]
        return self

    async def _run_scripts(self):
        if self.content_mod == TEXT and self._data:
            sr = ScriptRunner(text=self._data, logger=self.req.logger)
            if await sr.run(args=self.vars):
                self._data = sr.export()
            else:
                self._data = SMTH_HAPPENED
                self.code = 500
        return self._data

    async def load_static_file(self, filename):
        """
            load static file
            return True in case of success
        """
        if os.path.isfile(filename):
            await self.req.logger.debug(f'send file "{filename}"')
            size = os.path.getsize(filename)
            if size <= self.cfg.max_response_size:
                with open(filename, 'rb') as f:
                    self._data = f.read()
                _code = 200
            else:
                _from = 0
                _to = self.cfg.max_response_size
                if self.req is not None and 'range' in self.req.headers:
                    tmp = self.req.headers['range'].split('=')
                    if tmp[0] == 'bytes':
                        a, b = tmp[1].split('-')
                        _from = int(a) if a else 0
                        _to = int(b) if b else (_from + self.cfg.max_response_size)
                with open(filename, 'rb') as f:
                    if _from > 0:
                        f.read(_from)
                    self._data = f.read(_to - _from)
                    self.add_headers(
                        {
                            'Content-Range': f'bytes={_from}-{_to}/{size}',
                        }
                    )
                _code = 206
            headers = content_type(filename)
            self.content_mod = (
                TEXT
                if next(
                    headers[i] for i in headers
                ).startswith('text') else
                BIN
            )
            headers['Cache-Control'] = f'max-age={self.cfg.cache_min}'
            self.add_headers(headers)
            self.code = _code
            return True
        else:
            await self.req.logger.debug(f'file not found "{filename}"')
            self._data = NOT_FOUND
            self.add_headers(CONTENT_HTML)
            self.code = 404
            return False

    def rederict(self, url, permanent=False):
        self.code = 307 + permanent
        self.add_headers(Location=url)

    async def _extra_prepare_data(self):
        return await self._run_scripts()

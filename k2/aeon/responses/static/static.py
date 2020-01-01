#!/use/bin/env python3
import os
import sys
import gzip

from k2.aeon.responses.base_response import Response
from k2.utils.autocfg import (
    AutoCFG,
    CacheDict,
)
from k2.utils.http import (
    SMTH_HAPPENED,
    NOT_FOUND,
    CONTENT_HTML,
    content_type as content_type,
)

from .runner import ScriptRunner

BIN = 'binary'
TEXT = 'text'

# key - <public> + '@' + 'path'
# or <private> + ':' + uid + '@' + 'path'
ServerCache = CacheDict(timeout=120 * ('--no-cache' not in sys.argv))

STATIC_RESPONSE_DEFAULTS = {
    'cache_min': 120,  # max-age
    'cache_public': True,  # public/private
    'cache_of_uid': None,  # if cache is private and server_cache -> uid of owner
    'max_response_size': (2 ** 18),  # <=> chunk size
    'server_cache': True,  # cache on server
    'compress': 'gzip',  # compress data; allowed: 'gzip' or None
}


class StaticResponse(Response):
    def __init__(self, request, **kwargs):
        super().__init__()
        self.cfg = AutoCFG(STATIC_RESPONSE_DEFAULTS).update_fields(kwargs)
        self.content_mod = None
        self.vars = dict(
            {
                'req': request,
            },
            **(kwargs.get('vars') or {})
        )
        self.req = request
        self._data = ''
        self._cached = False

    def __get_cache_key(self):
        if not self.cfg.cache_public and self.cfg.cache_of_uid is None:
            raise ValueError('UID must be set for private cache')
        return ''.join(
            ['public@', self.req.url, '?', str(self.req.args)]
            if self.cfg.cache_public else
            ['private:', str(self.cfg.cache_of_uid), '@', self.req.url, '?', str(self.req.args)]
        )

    async def _run_scripts(self):
        if self.content_mod == TEXT and self._data:
            if await (sr := ScriptRunner(text=self._data, logger=self.req.logger)).run(args=self.vars):
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
        if self.cfg.server_cache:
            await self.req.logger.debug('get file from cache')
            try:
                self._data = (data := ServerCache[self.__get_cache_key()])['data']
                self.headers.update(data['headers'])
                self.code = data['code']
                self._cached = True
                return True
            except KeyError:
                pass

        if os.path.isfile(filename):
            await self.req.logger.debug(f'send file "{filename}"')
            size = os.path.getsize(filename)
            if not self.cfg.max_response_size or size <= self.cfg.max_response_size:
                with open(filename, 'rb') as f:
                    self._data = f.read()
                _code = 200
            else:
                _from = 0
                _to = self.cfg.max_response_size
                if self.req and 'range' in self.req.headers:
                    if (tmp := self.req.headers['range'].split('='))[0] == 'bytes':
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
            await self.req.logger.debug(f'file "{filename}" loaded: {len(self._data)}b')
            headers = content_type(filename)
            self.content_mod = (
                TEXT
                if next(
                    value for value in headers.values()
                ).startswith('text') else
                BIN
            )
            headers['Cache-Control'] = 'max-age={cache_min}, {cache_public}'.format(
                cache_min=self.cfg.cache_min,
                cache_public='public' if self.cfg.cache_public else 'private'
            )
            self.headers.update(headers)
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

    async def _cache_n_zip(self, data):
        if self.content_mod == TEXT:
            if 'gzip' not in self.req.headers.get('accept-encoding', ''):
                return data
            if self.cfg.compress == 'gzip':
                await self.req.logger.debug('compress data {} -> {}', len(data), len(data := gzip.compress(data)))
                self.headers['Content-Encoding'] = 'gzip'

        if self.cfg.server_cache and self.code not in {204, 206}:
            await self.req.logger.debug('save data to cache')
            ServerCache[self.__get_cache_key()] = {
                'data': data,
                'headers': self.headers,
                'code': self.code,
            }
        return data

    async def _extra_prepare_data(self):
        if not self._cached:
            return await self._run_scripts()
        else:
            return self._data

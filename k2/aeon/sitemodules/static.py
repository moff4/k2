#!/usr/bin/env python3
import os

from k2.aeon import AeonResponse
from k2.aeon import Response


class StaticSiteModule:
    def __init__(self, static_root, show_index=False, chunk_size=(2 ** 18)):
        self._static_root = static_root
        self._show_index = show_index
        self._chunk_size = chunk_size

    def get(self, req):
        headers = {}
        code = 404
        data = b''
        filename = self._static_root + req.url
        if os.path.isfile(filename):
            filesize = os.path.getsize(filename)
            if filesize < self._chunk_size:
                with open(filename, 'rb') as f:
                    data = f.read()
                    code = 200
            else:
                offset = 0
                size = self._chunk_size
                if 'range' in req.headers:
                    if not req.headers['range'].startswith('bytes='):
                        raise AeonResponse('Unsupportable range type "%s"' % req.headers['range'], code=400)

                    if ',' in req.headers['range']:
                        raise AeonResponse('Multirange not supported', code=400)

                    r = [i.strip() for i in req.headers['range'][6:].split('-')]
                    if len(r) != 2 or any((not i.isdigit() for i in r)):
                        raise AeonResponse('Invalid range header', code=400)
                    offset = int(r[0])
                    size = int(r[1]) - offset
                    if size > self._chunk_size:
                        size = self._chunk_size

                with open(filename) as f:
                    f.seek(offset)
                    data = f.read(size if size > 0 else 0)
                    code = 206
        elif self._show_index and os.path.isdir(filename):
            pass
            # FIXME
            # generate index page

        return Response(
            data=data,
            code=code,
            headers=headers,
        )

#!/usr/bin/env python3
import os

from k2.aeon.exceptions import AeonResponse
from k2.aeon.responses import (
    Response,
    StaticResponse,
)
from k2.aeon.sitemodules.base import SiteModule


class StaticSiteModule(SiteModule):
    def __init__(self, static_root, show_index=False, chunk_size=(2 ** 18), allow_links=False, cache_min=120):
        self._static_root = static_root
        self._show_index = show_index
        self._chunk_size = chunk_size
        self._allow_links = allow_links
        self._cache_min = cache_min

    async def get(self, req):
        headers = {}
        code = 404
        data = b''
        filename = self._static_root + req.url
        if os.path.isfile(filename):
            resp = StaticResponse(
                request=req,
                cache_min=self._cache_min,
                max_response_size=self._chunk_size,
            )
            await resp.load_static_file(
                filename=filename,
            )
            return resp
        elif self._show_index and os.path.isdir(filename):
            urls = []
            url = req.url.rstrip('/')
            for _fn in os.listdir(filename):
                fn = ''.join([filename, _fn])
                if os.path.isdir(fn):
                    urls.append(
                        {
                            'name': _fn,
                            'type': 'Dir',
                            'url': '/'.join([url, _fn, '']),
                        }
                    )
                elif os.path.islink(fn):
                    if self._allow_links:
                        urls.append(
                            {
                                'name': _fn,
                                'type': 'Link',
                                'url': '/'.join([url, _fn]),
                            }
                        )
                elif os.path.isfile(fn):
                    urls.append(
                        {
                            'name': _fn,
                            'type': 'File',
                            'url': '/'.join([url, _fn]),
                        }
                    )
            data = f'''
            <html>
                <body>
                    <h1>index of {req.url}</h1>
                    {
                        ''.join(
                            [
                                f'<div>{item["type"]}: <a href="{item["url"]}">{item["name"]}</a></div>'
                                for item in urls
                            ]
                        )
                    }
                </body>
            </html>
            '''
            code = 200
            headers['Cache-Control'] = f'max-age={self._cache_min}'

        return Response(
            data=data,
            code=code,
            headers=headers,
        )

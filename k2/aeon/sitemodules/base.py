#!/usr/bin/env python3

import asyncio

from k2.aeon.responses import Response
from k2.utils.http import NOT_FOUND


class BaseSiteModule:

    async def handle(self, request, **args):
        f_name = request.method.lower()
        if not hasattr(self, f_name):
            return Response(data=NOT_FOUND, code=404)

        handler = getattr(self, f_name)
        if asyncio.iscoroutinefunction(handler):
            return await handler(request, **args)
        else:
            return handler(request, **args)

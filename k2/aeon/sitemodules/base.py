#!/usr/bin/env python3

import asyncio

from k2.aeon.responses import Response
from k2.utils.http import NOT_FOUND


class BaseSiteModule:

    async def handle(self, request, **args):
        if not hasattr(self, f_name := request.method.lower()):
            return Response(data=NOT_FOUND, code=404)

        if asyncio.iscoroutinefunction(handler := getattr(self, f_name)):
            return await handler(request, **args)
        else:
            return handler(request, **args)

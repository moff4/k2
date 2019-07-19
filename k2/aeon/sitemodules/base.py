#!/usr/bin/env python3

import asyncio


class SiteModule:

    async def handle(self, req):
        f_name = req.method.lower()
        if not hasattr(self, f_name):
            return Response(data=NOT_FOUND, code=404)

        handler = getattr(module, f_name)
        if asyncio.iscoroutinefunction(handler):
            return await handler(req, **args)
        else:
            return handler(req, **args)

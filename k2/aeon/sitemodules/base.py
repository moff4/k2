import asyncio

from k2.aeon.responses import Response
from k2.utils.http import NOT_FOUND
from k2.utils.tools import call_corofunc


class BaseSiteModule:
    async def handle(self, request, **args):
        return (
            await call_corofunc(getattr(self, f_name), request, **args)
            if hasattr(self, f_name := request.method.lower()) else
            Response(data=NOT_FOUND, code=404)
        )

#!/usr/bin/env python3

try:
    import ujson as json
except ImportError:
    import json

from k2.aeon.exceptions import AeonResponse
from k2.aeon.responses import Response
from k2.aeon.sitemodules.sm import SiteModule
from k2.utils.jschema import apply
from k2.utils.http import (
    REST_DEFAULT_GETTERS,
    REST_DEFAULT_SETTERS,
)


class RestSM(SiteModule):

    async def __check_schema(self, request):
        if (schema := getattr(self, '%s_schema' % request.method, None)) is None:
            return
        if (getter := getattr(self, '%s_getter' % request.method, REST_DEFAULT_GETTERS.get(request.method, None))) is None:
            return
        if (setter := getattr(self, '%s_setter' % request.method, REST_DEFAULT_SETTERS.get(request.method, None))) is None:
            return
        if (deserializer := getattr(self, 'deserializer', json.loads)) is None:
            return
        try:
            if isinstance(data := getter(request), (str, bytes)):
                data = deserializer(data)
            data = apply(data, schema)
        except ValueError as e:
            await request.logger.warning(str(e))
            raise AeonResponse(code=400, data='invalid schema')
        setter(request, data)

    async def handle(self, request, **args):
        await self.__check_schema(request)
        if not isinstance(res := await super().handle(request, **args), Response):
            res = Response(
                data=(
                    getattr(self, 'serializer')
                    if hasattr(self, 'serializer') else
                    json.dumps
                )(res),
                code=200,
            )
        return res

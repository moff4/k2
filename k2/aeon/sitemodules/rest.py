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

    def __check_schema(self, request):
        schema = getattr(self, '%s_schema' % request.method, None)
        if schema is None:
            return
        getter = getattr(self, '%s_getter' % request.method, REST_DEFAULT_GETTERS.get(request.method, None))
        if getter is None:
            return
        setter = getattr(self, '%s_setter' % request.method, REST_DEFAULT_SETTERS.get(request.method, None))
        if setter is None:
            return
        deserializer = getattr(self, 'deserializer', json.loads)
        if deserializer is None:
            return
        data = getter(request)
        try:
            if isinstance(data, (str, bytes)):
                data = deserializer(data)
            data = apply(data, schema)
        except ValueError as e:
            await request.logger.warning(str(e))
            raise AeonResponse(code=400, data='invalid schema')
        setter(request, data)

    async def handle(self, request, **args):
        self.__check_schema(request)
        res = await super().handle(request, **args)
        if not isinstance(res, Response):
            serializer = (
                getattr(self, 'serializer')
                if hasattr(self, 'serializer') else
                json.dumps
            )
            res = Response(
                data=serializer(res),
                code=200,
            )
        return res

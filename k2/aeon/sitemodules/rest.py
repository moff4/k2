#!/usr/bin/env python3

try:
    import ujson as json
except ImportError:
    import json

from k2.aeon.sitemodules.base import SiteModule
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
        serializer = getattr(self, 'serializer', json.loads)
        if serializer is None:
            return
        data = getter(request)
        if isinstance(data, (str, bytes)):
            data = serializer(data)
        data = apply(data, schema)
        setter(request, data)

    async def handle(self, request, **args):
        self.__check_schema(request)
        return await super().handle(request, **args)

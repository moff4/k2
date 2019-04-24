#!/usr/bin/env python3

from k2.aeon.abstract_aeon import AbstractAeon
# from k2.aeon.parser import parse_data
from k2.aeon.requests import Request
from k2.aeon.responses import Response


class Aeon(AbstractAeon):

    async def client_connected_cb(self, reader, writer):
        req = Request(writer.get_extra_info('peername'), reader, writer)
        await req.read()
        resp = Response(data=req.url, code=200)
        await req.send(resp)

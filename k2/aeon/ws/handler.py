#!/usr/bin/env python3
from k2.aeon.ws.base import BaseWSHandler


class WSHandler(BaseWSHandler):
    """
        Prototype of WS handler
        inherit and overwrite all handlers you need
    """

    async def on_validate(self):
        """
            Will be called just after ws handshake
            Example: for cookie check / adding ws to pool
        """
        await self.req.logger.debug('validation done!')

    async def on_request(self):
        """
            Will be called before ws handshake
            Example: for Origin check
        """
        await self.req.logger.debug('got request!')

    async def on_end(self):
        """
            Will be called after ws been closed
            Example: for deleteing from ws from pool
        """
        await self.req.logger.debug('connection is over!')

    async def handle_incoming_msg(self, message):
        """
            Will be called on new incoming text message
            For example: Origin check
        """
        await self.req.logger.debug(f'new message: {message}')

    async def handle_incoming_bin(self, message):
        """
            Will be called on new incoming binary message
            For example: Origin check
        """
        await self.req.logger.debug(f'new message: {str(message)}')

    async def close(self):
        """
            on close connection
        """
        await super().close()

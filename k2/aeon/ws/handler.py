#!/usr/bin/env python3
import logging
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
        logging.debug('validation done!')

    async def on_request(self):
        """
            Will be called before ws handshake
            Example: for Origin check
        """
        logging.debug('got request!')

    async def on_end(self):
        """
            Will be called after ws been closed
            Example: for deleteing from ws from pool
        """
        logging.debug('connection is over!')

    async def handle_incoming_msg(self, message):
        """
            Will be called on new incoming text message
            For example: Origin check
        """
        logging.debug('new message: %s' % message)

    async def handle_incoming_bin(self, message):
        """
            Will be called on new incoming binary message
            For example: Origin check
        """
        logging.debug('new message: %s' % str(message))

    def close(self):
        """
            Will be called when server is shutting down
            You should send message to close connection / reconnect
            if you are ready to close connection, call super().close()
            otherwise server will wait for client close connection
        """
        super().close()

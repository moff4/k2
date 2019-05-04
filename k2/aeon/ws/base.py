#!/usr/bin/env python3
import asyncio
import socket
import struct
import errno
from base64 import b64encode
from hashlib import sha1
from socket import error as SocketError
import logging

from k2.aeon.responses import Response
from k2.utils.autocfg import AutoCFG
from k2.utils.ws import (
    encode_to_UTF8,
    try_decode_UTF8,
)

'''
+-+-+-+-+-------+-+-------------+-------------------------------+
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                     Payload Data continued ...                |
+---------------------------------------------------------------+
'''


class BaseWSHandler:
    """
        Base WS handler
        Implemetation of WebSocket Protocol
    """

    FIN = 0x80
    OPCODE = 0x0f
    MASKED = 0x80
    PAYLOAD_LEN = 0x7f
    PAYLOAD_LEN_EXT16 = 0x7e
    PAYLOAD_LEN_EXT64 = 0x7f

    OPCODE_CONTINUATION = 0x0
    OPCODE_TEXT = 0x1
    OPCODE_BINARY = 0x2
    OPCODE_CLOSE_CONN = 0x8
    OPCODE_PING = 0x9
    OPCODE_PONG = 0xA

    GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    def __init__(self, req, **kwargs):
        self.req = req
        self.alive = True
        self.rfile, self.wfile = req.get_rw()
        self.args = AutoCFG(kwargs)
        self.handler_map = {
            self.OPCODE_TEXT: self.handle_incoming_msg,
            self.OPCODE_BINARY: self.handle_incoming_bin,
            self.OPCODE_PING: self.send_pong,
            self.OPCODE_PONG: lambda msg: msg,
        }

    def setup(self):
        self.keep_alive = True
        self.handshake_done = False
        self.valid_client = False

    async def __call(self, handler, *a, **b):
        if asyncio.iscoroutinefunction(handler):
            await handler(*a, **b)
        else:
            handler(*a, **b)

    async def handle_incoming_msg(self, message):
        pass

    async def handle_incoming_bin(self, message):
        pass

    def on_request(self):
        pass

    def on_validate(self):
        pass

    def on_end(self):
        pass

    async def close(self):
        await self.finish()

    async def mainloop(self):
        self.setup()
        try:
            while self.keep_alive:
                if not self.handshake_done:
                    await self.handshake()
                elif self.valid_client:
                    await self.read_next_message()
        except Exception as e:
            logging.exception('Loop: %s', e)
        finally:
            await self.finish()

    async def read_next_message(self):
        try:
            b1, b2 = await self.rfile.read(2)
        except SocketError as e:  # to be replaced with ConnectionResetError for py3
            if e.errno == errno.ECONNRESET:
                # Client closed connection
                self.keep_alive = False
                return
            b1, b2 = 0, 0
        except ValueError as e:
            b1, b2 = 0, 0

        # fin = b1 & FIN
        opcode = b1 & self.OPCODE
        masked = b2 & self.MASKED
        payload_length = b2 & self.PAYLOAD_LEN

        if opcode == self.OPCODE_CLOSE_CONN:
            # Client asked to close connection.
            self.keep_alive = False
            return
        if not masked:
            # Client must always be masked
            self.keep_alive = False
            return

        if opcode == self.OPCODE_CONTINUATION:
            # Continuation frames are not supported
            return
        elif opcode not in self.handler_map:
            # 'Unknown opcode %#x.' % opcode
            self.keep_alive = False
            return

        if payload_length == 126:
            payload_length = struct.unpack('>H', await self.rfile.read(2))[0]
        elif payload_length == 127:
            payload_length = struct.unpack('>Q', await self.rfile.read(8))[0]

        masks = await self.rfile.read(4)
        message_bytes = bytearray()
        for message_byte in await self.rfile.read(payload_length):
            message_byte ^= masks[len(message_bytes) % 4]
            message_bytes.append(message_byte)
        handler = self.handler_map[opcode]
        await self.__call(handler, message_bytes.decode('utf8'))

    async def send_message(self, message):
        await self.send_text(message, self.OPCODE_TEXT)

    async def send_binary(self, message):
        await self.send_text(message, self.OPCODE_BINARY)

    async def send_pong(self, message):
        await self.send_text(message, self.OPCODE_PONG)

    async def send_text(self, message, opcode=None):
        """
            Important: Fragmented(=continuation) messages are not supported since
            their usage cases are limited - when we don't know the payload length.
        """
        if opcode is None:
            opcode = self.OPCODE_TEXT

        # Validate message
        if isinstance(message, bytes):
            message = try_decode_UTF8(message)  # this is slower but ensures we have UTF-8
            if not message:
                # 'Can\'t send message, message is not valid UTF-8'
                return False
        elif isinstance(message, str):
            pass
        else:
            # 'Can\'t send message, message has to be a string or bytes. Given type is %s' % type(message)
            return False

        header = bytearray()
        payload = encode_to_UTF8(message)
        payload_length = len(payload)

        if payload_length <= 125:
            header.append(self.FIN | opcode)
            header.append(payload_length)
        elif payload_length >= 126 and payload_length <= 65535:
            header.append(self.FIN | opcode)
            header.append(self.PAYLOAD_LEN_EXT16)
            header.extend(struct.pack('>H', payload_length))
        elif payload_length < 18446744073709551616:
            header.append(self.FIN | opcode)
            header.append(self.PAYLOAD_LEN_EXT64)
            header.extend(struct.pack('>Q', payload_length))
        else:
            raise Exception('Message is too big. Consider breaking it into chunks.')

        try:
            self.wfile.write(header + payload)
            await self._writer.drain()
        except Exception as e:
            logging.debug('[%s:%s] send-text: %s' % (self.req.ip, self.req.port, e))
            self.keep_alive = False

    async def handshake(self):
        if 'upgrade' not in self.req.headers or self.req.headers['upgrade'].lower() != 'websocket':
            self.keep_alive = False
            return

        await self.__call(self.on_request)

        key = self.req.headers.get('sec-websocket-key')
        if key is None:
            # 'Client tried to connect but was missing a key'
            self.keep_alive = False
            return

        await self.req.send(
            Response(
                code=101,
                headers={
                    'Upgrade': 'websocket',
                    'Connection': 'Upgrade',
                    'Sec-WebSocket-Accept': self.calculate_response_key(key),
                },
            ),
        )
        self.handshake_done = True
        self.valid_client = True
        await self.__call(self.on_validate)

    @classmethod
    def calculate_response_key(cls, key):
        hash = sha1(key.encode() + cls.GUID)
        response_key = b64encode(hash.digest()).strip()
        return response_key.decode('ASCII')

    async def finish(self):
        await self.__call(self.on_end)
        self.keep_alive = False
        self.alive = False

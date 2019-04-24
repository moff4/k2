#!/usr/bin/env python3
import sys
import asyncio
import socket

from k2.utils.autocfg import AutoCFG


class AbstractAeon:
    """
        Simple echo server using asyncio
        U can r
    """

    __defaults = {
        'host': '',
        'port': 8888,
        'loop': None,
        'family': socket.AF_INET,
        'flags': socket.AI_PASSIVE,
        'sock': None,
        'backlog': 100,
        'ssl': None,
        'reuse_address': None,
        'reuse_port': None,
        'ssl_handshake_timeout': None,
        'start_serving': True
    }

    def __init__(self, **kwargs):
        self.cfg = AutoCFG({k: kwargs.get(k, self.__defaults[k]) for k in self.__defaults})
        if self.cfg.loop is None:
            self.cfg.loop = asyncio.get_event_loop()
        self._task = None
        self._server = None

    async def client_connected_cb(self, reader, writer):
        try:
            data = True
            while data:
                data = await reader.read(100)
                message = data.decode()
                addr = writer.get_extra_info('peername')
                print('recived [{host}:{port}] {msg}'.format(host=addr[0], port=addr[1], msg=message.rstrip()))
                writer.write(data)
                await writer.drain()
        except Exception as e:
            print('Error')
        finally:
            writer.close()

    @property
    def task(self):
        if self._task is None:
            args = {
                'client_connected_cb': self.client_connected_cb,
                'host': self.cfg.host,
                'port': self.cfg.port,
                'loop': self.cfg.loop,
                'family': self.cfg.family,
                'flags': self.cfg.flags,
                'sock': self.cfg.sock,
                'backlog': self.cfg.backlog,
                'ssl': self.cfg.ssl,
                'reuse_address': self.cfg.reuse_address,
                'reuse_port': self.cfg.reuse_port,
            }
            if sys.version_info[0] >= 3 and sys.version_info[1] >= 7:
                args.update(
                    {
                        'ssl_handshake_timeout': self.cfg.ssl_handshake_timeout,
                        'start_serving': self.cfg.start_serving,
                    }
                )
            self._task = asyncio.start_server(**args)
        return self._task

    def run(self):
        self._server = self.cfg.loop.run_until_complete(self.task)
        try:
            self.cfg.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self._server.close()
            self.cfg.loop.run_until_complete(self._server.wait_closed())
            self.cfg.loop.close()

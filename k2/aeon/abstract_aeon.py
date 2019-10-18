#!/usr/bin/env python3
import sys
import ssl
import asyncio
import socket

import k2.logger as logger
from k2.utils.autocfg import AutoCFG


class AbstractAeon:
    """
        Simple echo server using asyncio
        U can overwrite client_connected_cb for your own server
    """

    __defaults = {
        'host': '',
        'port': 8888,
        'use_ssl': False,
        'https_port': 8889,
        'loop': None,
        'family': socket.AF_INET,
        'flags': socket.AI_PASSIVE,
        'backlog': 100,
        'ssl': None,
        'ca_cert': None,
        'certs': None,  # or dict: host => {certfile, keyfile, keypassword}
        'reuse_address': None,
        'reuse_port': None,
        'ssl_handshake_timeout': None,
        'start_serving': True,
        'site_dir': './var/',
        'logger': {},
    }

    def __init__(self, **kwargs):
        self.cfg = AutoCFG({k: kwargs.get(k, self.__defaults[k]) for k in self.__defaults})
        if self.cfg.loop is None:
            self.cfg.loop = asyncio.get_event_loop()
        self._contexts = {}
        if self.cfg.ssl is None and self.cfg.certs:
            for host in self.cfg.certs:
                context = ssl.create_default_context(
                    purpose=ssl.Purpose.CLIENT_AUTH,
                    cafile=self.cfg.ca_cert,
                )
                context.load_cert_chain(
                    certfile=self.cfg.certs[host]['certfile'],
                    keyfile=self.cfg.certs[host]['keyfile'],
                    password=self.cfg.certs[host].get('keypassword', None),
                )
                self._contexts[host] = context
            self.cfg.ssl = ssl.create_default_context(
                purpose=ssl.Purpose.CLIENT_AUTH,
                cafile=self.cfg.ca_cert,
            )
            self.cfg.ssl.set_servername_callback(self.servername_callback)
        self._task = None
        self._server = None
        self._logger = logger.new_channel(
            key='aeon',
            parent=logger.get_channel('base_logger'),
            **self.cfg.logger,
        )
        self.running_tasks = []

    def servername_callback(self, sock, req_hostname, cb_context, as_callback=True):
        """
            ssl context callback
        """
        context = self._contexts.get(req_hostname)
        if context is None:
            context = self._contexts.get('*')
        if context is not None:
            sock.context = context

    async def client_connected_cb(self, reader, writer):
        try:
            data = True
            while data:
                data = await reader.read(100)
                message = data.decode()
                addr = writer.get_extra_info('peername')
                await self._logger.debug(f'recived [{addr[0]}:{addr[1]}] {message.rstrip()}')
                writer.write(data)
                await writer.drain()
        except Exception as e:
            await self._logger.error('Error: %s' % e)
        finally:
            writer.close()

    @property
    def tasks(self):
        if self._task is None:
            tasks = []
            http_args = {
                'client_connected_cb': self.client_connected_cb,
                'host': self.cfg.host,
                'port': self.cfg.port,
                'loop': self.cfg.loop,
                'family': self.cfg.family,
                'flags': self.cfg.flags,
                'backlog': self.cfg.backlog,
                'ssl': None,
                'reuse_address': self.cfg.reuse_address,
                'reuse_port': self.cfg.reuse_port,
            }
            if sys.version_info[0] >= 3 and sys.version_info[1] >= 7:
                http_args.update(
                    {
                        'ssl_handshake_timeout': self.cfg.ssl_handshake_timeout,
                        'start_serving': self.cfg.start_serving,
                    }
                )
            tasks.append(asyncio.start_server(**http_args))

            if self.cfg.use_ssl:
                https_args = {
                    'client_connected_cb': self.client_connected_cb,
                    'host': self.cfg.host,
                    'port': self.cfg.https_port,
                    'loop': self.cfg.loop,
                    'family': self.cfg.family,
                    'flags': self.cfg.flags,
                    'backlog': self.cfg.backlog,
                    'ssl': self.cfg.ssl,
                    'reuse_address': self.cfg.reuse_address,
                    'reuse_port': self.cfg.reuse_port,
                }
                if sys.version_info[0] >= 3 and sys.version_info[1] >= 7:
                    https_args.update(
                        {
                            'ssl_handshake_timeout': self.cfg.ssl_handshake_timeout,
                            'start_serving': self.cfg.start_serving,
                        }
                    )
                tasks.append(asyncio.start_server(**https_args))
            self._task = tasks
        return self._task

    def run(self):
        ports = f'{self.cfg.port}, {self.cfg.https_port}' if self.cfg.use_ssl else self.cfg.port
        self.running_tasks = []
        try:
            self.running_tasks = [
                asyncio.ensure_future(
                    self._logger.info(
                        'server started on {}',
                        ports,
                    )
                )
            ]

            self.running_tasks.extend(
                asyncio.ensure_future(task)
                for task in self.tasks
            )
            self.cfg.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            for task in self.running_tasks:
                task.cancel()
            self.cfg.loop.run_until_complete(
                asyncio.ensure_future(
                    self._logger.info(
                        'server stopped on {}',
                        ports,
                    )
                )
            )

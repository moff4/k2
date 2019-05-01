#!/usr/bin/env python3
import logging
from k2.aeon import (
    Aeon,
    WSHandler,
)


def main():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.setLevel(logging.DEBUG)
    server = Aeon(
        site_dir='.',
    )
    server.add_ws_handler(
        '/ws/',
        WSHandler
    )
    server.run()


if __name__ == '__main__':
    main()

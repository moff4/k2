#!/usr/bin/env python3
import logging

from k2.aeon import Aeon, Response


def main():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.setLevel(logging.DEBUG)
    server = Aeon()
    server.add_site_module(
        '/',
        type(
            'CGI',
            (),
            {
                'get': lambda self, request: Response(
                    code=200,
                    data=request.url
                )
            }
        )()
    )
    server.run()


if __name__ == '__main__':
    main()

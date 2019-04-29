#!/usr/bin/env python3
import logging

from k2.aeon import (
    Aeon,
    Response,
    StaticSiteModule,
)


def main():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.setLevel(logging.DEBUG)
    server = Aeon(
        site_dir='.',
    )
    server.add_site_module(
        '/',
        StaticSiteModule(
            static_root='.',
            show_index=True,
        )
    )
    server.run()


if __name__ == '__main__':
    main()

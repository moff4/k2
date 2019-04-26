#!/usr/bin/env python3
import logging

from k2.aeon.aeon import Aeon


def main():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.setLevel(logging.DEBUG)
    Aeon().run()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

from typing import Any

from .parser import Parser
from .coder import Coder


def marshal(data: Any, mask: bytes=None, random: bool=True) -> bytes:
    """
        convert data to bytes
        mask - some mask to be applied on marshaled data
    """
    c = Coder(data, random=random)
    c.magic()
    if mask is None:
        return c.export()
    else:
        data = c.export()
        return bytes([data[i] ^ mask[i % len(mask)] for i in range(len(data))])


def unmarshal(data: bytes=None, fd=None, mask: bytes=None) -> Any:
    """
        convert data as bytes() or from fd {interface : read() }
    """
    if data is None and fd is None:
        raise ValueError('Expected param "data" of "fd"')
    if data is not None and all(map(lambda x: not isinstance(data, x), {bytes, str})):
        raise ValueError(f'Unexpected type of "data" ({type(data)}), expected bytes or str')
    return Parser(
        mask=mask,
        fd=fd,
        data=data
    ).magic().export()

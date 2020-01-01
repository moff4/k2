#!/usr/bin/env python3

import io

from .consts import (
    INT_POS,
    INT_NEG,
    FLOAT_POS,
    FLOAT_NEG,
    BYTES,
    STRING,
    LIST,
    MAP,
    TRUE,
    FALSE,
    NULL,
)


class Parser:
    def __init__(self, mask=None, fd=None, data=None):
        self.convert_map = {
            INT_POS: self._get_int,
            INT_NEG: lambda: self._get_int() * (-1),
            FLOAT_POS: self._get_float,
            FLOAT_NEG: lambda: self._get_float() * (-1),
            BYTES: self._get_bytes,
            STRING: lambda: self._get_bytes().decode(),
            LIST: self._get_list,
            MAP: self._get_map,
            TRUE: lambda: True,
            FALSE: lambda: False,
            NULL: lambda: None,
        }
        self.result = None
        self.input_fd = None

        self.mask = mask

        self._read_total = 0
        self._len = None

        if fd is not None:
            self.set_fd(fd)
        elif data is not None:
            self.set_data(data if isinstance(data, bytes) else data.encode())

    def _get(self):
        if self._len is not None and self._read_total >= self._len:
            raise RuntimeError('Reached end of input')

        if isinstance(res := self.input_fd.read(1), bytes):
            if not res:
                raise RuntimeError('reached EOF')
            res = res[0]
        if self.mask:
            res = res ^ self.mask[self._read_total % len(self.mask)]
        self._read_total += 1
        return res

    def _get_int(self, z=None):
        """
            1 Integer
        """
        x = 0
        while True:
            if z is not None:
                y = z
                z = None
            else:
                y = self._get()
            if y < 128:
                x = x * 128 + y
            else:
                return x * 128 + y % 128

    def _get_float(self):
        """
            2 Float
        """
        return float(self._get_int()) / 10.0**self._get_int()

    def _get_bytes(self):
        """
            3 Bytes
        """
        c = 0
        st = []
        while c < 2:
            if (x := self._get()) == 0:
                c += 1
            elif c:
                st.extend([0] * self._get_int(x))
                c = 0
            else:
                st.append(x)
        return bytes(st)

    def _get_list(self):
        """
            4 List
        """
        az = []
        while (x := self._type()) is not None:
            az.append(x)
        return az

    def _get_map(self):
        """
            5 Map
        """
        az = {}
        while key := self._type(unallowed_types={LIST, MAP}):
            az[key] = self._type()
        return az

    def _type(self, unallowed_types: set = None):
        t = self._get() & 0x0F
        if unallowed_types and t in unallowed_types:
            raise ValueError(f'Unexpected element type of {t}')
        if t in self.convert_map:
            return self.convert_map[t]()
        raise ValueError(f'Unexpected type number: {t}')

# ==========================================================================
#                                 USER API
# ==========================================================================

    def set_fd(self, fd):
        if not hasattr(fd, 'read'):
            raise ValueError('Filed descriptor does not has methods "read"')
        self.input_fd = fd
        return self

    def set_data(self, data):
        self.input_fd = io.BytesIO(data)
        return self

    def magic(self):
        self._len = self._get_int() + self._read_total
        self.result = self._type()
        return self

    def export(self):
        return self.result

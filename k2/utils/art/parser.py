#!/usr/bin/env python3

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
        self.result = None
        self.input_fd = None
        self.input_data = None
        self.input_status = None

        self.mask = mask

        self._read_total = 0
        self._len = None

        if fd is not None:
            self.set_fd(fd)
        elif data is not None:
            self.set_data(data if isinstance(data, bytes) else data.encode())

    def _get(self):
        if self._len is not None and self._read_total >= self._len:
            raise RuntimeError('Reaced end of input')
        if self.input_status == 'fd':
            if hasattr(self.input_fd, 'read'):
                res = self.input_fd.read(1)
            elif hasattr(self.input_fd, 'recv'):
                res = self.input_fd.recv(1)
            else:
                raise TypeError('Excepted IOstream/File/Socket with method "read" or "recv"')
        elif self._read_total < len(self.input_data):
            res = self.input_data[self._read_total]
        else:
            raise ValueError('Unexpetedly reached end of input')
        if isinstance(res, bytes):
            if not res:
                raise RuntimeError('reached EOF')
            res = res[0]
        if self.mask is not None:
            res = res ^ self.mask[self._read_total % len(self.mask)]
        self._read_total += 1
        return res

    def _load(self, x):
        if self.input_status == 'fd':
            if hasattr(self.input_fd, 'read'):
                self.input_data = self.input_fd.read(x)
            elif hasattr(self.input_fd, 'recv'):
                self.input_data = self.input_fd.recv(x)
            else:
                raise TypeError('Excepted IOstream/File/Socket with method "read" or "recv"')
            self.input_status = 'dt'

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
        return x

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
            x = self._get()
            if x == 0:
                c += 1
            elif c != 0:
                st += [0 for i in range(self._get_int(x))]
                c = 0
            else:
                st.append(x)
        return bytes(st)

    def _get_list(self):
        """
            4 List
        """
        az = []
        while True:
            x = self._type()
            if x is None:
                return az
            else:
                az.append(x)
        return az

    def _get_map(self):
        """
            5 Map
        """
        az = {}
        while True:
            key = self._type(unallowed_types={LIST, MAP})
            if key is None:
                return az
            value = self._type()
            az[key] = value
        return az

    def _type(self, unallowed_types=()):
        convert_map = {
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
        t = self._get() & 0x0F
        if t in unallowed_types:
            raise ValueError(f'Unexpected element type of {t}')
        if t in convert_map:
            return convert_map[t]()
        else:
            raise ValueError(f'Unexpected type number: {t}')

# ==========================================================================
#                                 USER API
# ==========================================================================

    def set_fd(self, fd):
        if not hasattr(fd, 'read') and not hasattr(fd, 'recv'):
            raise ValueError('Filed descriptor does not has needed interface')
        self.input_fd = fd
        self.input_status = 'fd'
        return self

    def set_data(self, data):
        self.input_data = data
        self.input_status = 'dt'
        return self

    def magic(self):
        i = self._get_int()
        self._len = i + self._read_total
        self.result = self._type()
        return self

    def export(self):
        return self.result

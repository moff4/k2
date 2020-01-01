#!/usr/bin/env python3

from os import urandom

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


class Coder:
    def __init__(self, data, random=True):
        self.result = b''
        self.data = data
        self.rand = random
        self.convert_map = {
            int: self._int,
            float: self._float,
            str: lambda x, *a, **b: self._bytes(x.encode(), *a, string=True, **b),
            bytes: self._bytes,
            list: self._list,
            tuple: lambda x, *a, **b: self._list(list(x), *a, **b),
            dict: self._map,
            bool: self._bool,
            type(None): lambda *a, **b: self._none(),
        }

    def _gen_type(self, t):
        """
            generate type with noice
        """
        return [t | (urandom(1)[0] & 0xF0)] if self.rand else [t]

    def _int(self, data, just=False):
        """
            Positive Integer
        """
        if data != 0:
            st = []
            data = -data if (sign := data < 0) else data
            while data > 0:
                st.append(data % 128)
                data //= 128
            (st := st[::-1])[-1] |= 0x80
        else:
            st = [0x80]
            sign = False
        return st if just else [*self._gen_type(INT_NEG if sign else INT_POS), *st]

    def _float(self, data, just=False):
        """
            Float
        """
        sign = data < 0
        c = 0
        while data != round(data):
            data *= 10
            c += 1
        st = [*self._int(int(data), just=True), *self._int(int(c), just=True)]
        return st if just else [*self._gen_type(FLOAT_NEG if sign else FLOAT_POS), *st]

    def _bytes(self, data, string=False, just=False):
        """
            String
        """
        st = []
        c = 0
        for i in data:
            if i == 0:
                c += 1
            elif c != 0:
                c = 0
                st.extend([0, *self._int(c, just=True), i])
            else:
                st.append(i)
        if c:
            st.append(0)
            st.extend(self._int(c, just=True))
        st.extend((0, 0))
        return st if just else [*self._gen_type(STRING if string else BYTES), *st]

    def _list(self, data, just=False):
        """
            list
        """
        st = [] if just else self._gen_type(LIST)
        st.extend(j for i in data for j in self._type(i))
        st.extend(self._none())
        return st

    def _map(self, data, just=False):
        """
            dict
        """
        st = [] if just else self._gen_type(MAP)
        st.extend(
            k
            for key in data
            for j in (
                self._type(data=key, unallowed_types=(dict, list, tuple)),
                self._type(data=data[key])
            )
            for k in j
        )
        st.extend(self._none())
        return st

    def _bool(self, data):
        """
            Bool
        """
        return self._gen_type(TRUE if data else FALSE)

    def _none(self):
        """
            None
        """
        return self._gen_type(NULL)

    def _type(self, data, unallowed_types=()):
        if isinstance(data, unallowed_types):
            raise ValueError(f'This type ({type(data)}) is not allowed here')
        try:
            return next(
                (
                    self.convert_map[key]
                    for key in self.convert_map
                    if isinstance(data, key)
                )
            )(data)
        except StopIteration:
            raise TypeError(f'Unexpected type: {type(data)} for {str(data)}')

    def magic(self):
        tmp = self._type(self.data)
        self.result = self._int(len(tmp), just=True)
        self.result.extend(tmp)
        self.result = bytes(self.result)
        return self.result

    def export(self):
        return self.result

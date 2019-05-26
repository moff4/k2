#!/usr/bin/env python3

import time
import binascii
from os import urandom
from pygost.gost28147 import cfb_decrypt, cfb_encrypt

from k2.logger import new_channel
from k2.utils.autocfg import AutoCFG
from k2.utils import jschema
from k2.utils import art


class Tokenazer:
    """
        This module is to encrypt and descrypt tokens
        like cookie - session_id
        sessin_id = art(
            {
                'd': cfb_encrypt(
                    art(
                        <users data>,
                        XOR( mask_1 , mask_local )
                    )
                )
                'i': iv
            },
            mask_0
        )
    """

    __defaults = {
        'mask_0': None,
        'mask_1': None,
    }

    cookie_scheme = {
        'type': dict,
        'value': {
            'create': {
                'type': int
            },
            'uid': {
                'type': int,
            },
            'exp': {
                'type': int,
                'default': None
            },
        }
    }

    def __init__(self, secret, **kwargs):
        """
            sercret - secret key for crypto
            kwargs:
                mask_0 - bytes - extra sercret (default: None)
                mask_1 - bytes - extra sercret (default: None)
        """
        self.cfg = AutoCFG(self.__defaults).update_fields(kwargs)
        self.secret = secret
        self.logger = new_channel('tokenazer')

    async def __decode_cookie(self, cookie, mask=None):
        """
            return decoded cookie as dict
            or None in case of error
        """
        try:
            data = art.unmarshal(
                data=cookie,
                mask=self.cfg.mask_0
            )
            return jschema.apply(
                obj=art.unmarshal(
                    data=cfb_decrypt(
                        self.secret,
                        data=data['d'],
                        iv=data['i']
                    ),
                    mask=(
                        (
                            bytes(
                                mask[i] ^ self.cfg.mask_1[i % len(self.cfg.mask_1)]
                                for i in range(len(mask))
                            )
                            if mask else
                            self.cfg.mask_1
                        )
                        if self.cfg.mask_1 else
                        mask
                    ),
                ),
                scheme=self.cookie_scheme,
                key='cookie'
            )
        except Exception as e:
            await self.logger.exception('decode cookie: {}', e, level='warning')
            return None

# ==========================================================================
#                               USER API
# ==========================================================================

    def generate_cookie(self, user_id, **kwargs):
        """
            generate cookie
            must:
              user_id     - int - user identificator
            optional:
              expires     - int - num of seconds this cookie is valid
              mask        - bytes - extra mask
            return str() as value of cookie
        """
        data = {
            'create': int(time.time()),
            'uid': user_id,
        }
        kwargs['user_id'] = user_id
        params = {
            'expires': 'exp',
        }
        if 'mask' in kwargs and self.cfg.mask_1:
            mask = bytes(
                kwargs['mask'][i] ^ self.cfg.mask_1[i % len(self.cfg.mask_1)]
                for i in range(len(kwargs['mask']))
            )
        elif 'mask' in kwargs:
            mask = kwargs['mask']
        elif self.cfg.mask_1:
            mask = self.cfg.mask_1
        else:
            mask = None
        data.update({params[i]: kwargs[i] for i in params if i in kwargs})
        data = art.marshal(data, mask=mask, random=True)

        iv = urandom(8)
        data = cfb_encrypt(
            self.secret,
            data=data,
            iv=iv
        )

        return binascii.hexlify(
            art.marshal(
                {
                    'd': data,
                    'i': iv
                },
                mask=self.cfg.mask_0,
                random=True
            )
        ).decode()

    async def valid_cookie(self, cookie, mask=None):
        """
            return decoded cookie as dict if cookie is valid
            or None if cookie is not valid
        """
        cookie = await self.__decode_cookie(
            binascii.unhexlify(
                cookie
            ),
            mask,
        )
        if (
            cookie is None
        ) or (
            cookie['exp'] is not None and (cookie['create'] + cookie['exp']) < time.time()
        ):
            return None
        else:
            return cookie

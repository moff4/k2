#!/usr/bin/env python3

import time
import binascii
from os import urandom
from typing import Any, Optional, Dict
from pygost.gost28147 import cfb_decrypt, cfb_encrypt  # type: ignore

from k2.logger import new_channel
from k2.utils.autocfg import AutoCFG
from k2.utils import jschema
from k2.utils import art


class Tokenazer:
    """
        This module is to encrypt and descrypt tokens
        like cookie - session_id
        session_id = art(
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
            'create': int,
            'uid': {
                'pre_call': str,
                'type': str,
            },
            'exp': {
                'type': int,
                'default': None
            },
        }
    }

    def __init__(self, secret: bytes, **kwargs) -> None:
        """
            secret - secret key for crypto
            kwargs:
                mask_0 - bytes - extra secret (default: None)
                mask_1 - bytes - extra secret (default: None)
        """
        self.cfg = AutoCFG(self.__defaults).update_fields(kwargs)
        self.secret = secret
        self.logger = new_channel('tokenazer')

    async def __decode_cookie(self, cookie: bytes, mask: Optional[bytes] = None) -> Optional[Dict[str, Any]]:
        """
            :rtype dict: decoded cookie as dict
            or None in case of error
        """
        try:
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
            ) if (
                data := art.unmarshal(
                    data=cookie,
                    mask=self.cfg.mask_0
                )
            ) else None
        except Exception as e:
            await self.logger.exception('decode cookie: {}', e, level='warning')
            return None

# ==========================================================================
#                               USER API
# ==========================================================================

    def generate_cookie(self, user_id: str, **kwargs) -> str:
        """
            generate cookie
            must:
              user_id     - str - any user identificator
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
        data = cfb_encrypt(
            self.secret,
            data=art.marshal(data, mask=mask, random=True),
            iv=(iv := urandom(8)),
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

    async def valid_cookie(self, cookie: str, mask: Optional[bytes] = None) -> Optional[Dict[str, Any]]:
        """
            return decoded cookie as dict if cookie is valid
            or None if cookie is not valid
        """
        try:
            ck = await self.__decode_cookie(
                binascii.unhexlify(cookie),
                mask,
            )
            if (
                ck is None
            ) or (
                ck['exp'] is not None and (ck['create'] + ck['exp']) < time.time()
            ):
                return None
            else:
                return ck
        except binascii.Error as ex:
            await self.logger.warning('validate: {}', ex)
            return None

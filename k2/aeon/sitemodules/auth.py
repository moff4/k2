#!/usr/bin/env python3

from k2.aeon.exceptions import AeonResponse
from k2.aeon.sitemodules.sm import SiteModule


class AuthSM(SiteModule):

    async def _check_auth(self, request, **args):
        if hasattr(self, 'authorizator'):
            try:
                return getattr(self, 'authorizator')(request, **args)
            except AeonResponse:
                raise
            except Exception:
                await request.logger.exception('auth failed:')
                return False
        return True

    async def handle(self, request, **args):
        if not await self._check_auth(request, **args):
            raise AeonResponse(code=403)
        return await super().handle(request, **args)

#!/usr/bin/env python3

from .base import SiteModule
from .rest import RestSM
from .rederict import Rederict
from .static import StaticSiteModule

__all__ = [
    'RestSM',
    'Rederict',
    'SiteModule',
    'StaticSiteModule',
]

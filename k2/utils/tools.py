#!/usr/bin/env python3
import asyncio
from typing import Optional


def encode_to_utf8(data: str) -> Optional[bytes]:
    try:
        return data.encode('UTF-8')
    except UnicodeEncodeError:
        return None
    except Exception as e:
        raise e


async def call_corofunc(handler, *a, **b):
    if asyncio.iscoroutinefunction(handler):
        return await handler(*a, **b)
    else:
        return handler(*a, **b)

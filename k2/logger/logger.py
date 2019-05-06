#!/usr/bin/env python3

from .channel import Channel


# key - channel name
# value - LogChannel
Channels = {}


def new_channel(key, **kwargs):
    Channels[key] = Channel(key=key, **kwargs)


def delete_channel(key):
    Channels.pop(key, None)


async def exception(key, ex, level='error', *args, **kwargs):
    await Channels[key].exception(
        ex=ex,
        level=level,
        *args,
        **kwargs,
    )


async def error(key, msg, *args, **kwargs):
    await Channels[key].error(
        msg=msg,
        level='error',
        *args,
        **kwargs,
    )


async def warning(key, msg, *args, **kwargs):
    await Channels[key].warning(
        msg=msg,
        level='warning',
        *args,
        **kwargs,
    )


async def info(key, msg, *args, **kwargs):
    await Channels[key].info(
        msg=msg,
        level='info',
        *args,
        **kwargs,
    )


async def debug(key, msg, *args, **kwargs):
    await Channels[key].debug(
        msg=msg,
        level='debug',
        *args,
        **kwargs,
    )


def get_channel(key):
    return Channels.get(key)


def clear(key):
    return Channels.clear(key)


def export(key):
    if key in Channels:
        return Channels[key].export()
    else:
        raise KeyError(f'channel "{key}" not exists')

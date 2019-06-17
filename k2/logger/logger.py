#!/usr/bin/env python3

from .channel import Channel


# key - channel name
# value - LogChannel
Channels = {}


def new_channel(key, parent=None, inherite_rights={'stdout', 'debug', 'autosave'}, **kwargs):
    Channels[key] = Channel(key=key, **kwargs)
    if parent is not None:
        Channels[key].add_parent(
            parent=parent if isinstance(parent, Channel) else Channels[parent],
            inherite_rights=inherite_rights
        )
    return Channels[key]


def update_channel(key, **kwargs):
    if key in Channels:
        return Channels[key].update(**kwargs)
    else:
        raise KeyError(f'channel "{key}" not exists')


def delete_channel(key):
    Channels.pop(key, None)


async def exception(key, msg, *args, **kwargs):
    await Channels[key].exception(
        msg=msg,
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

BaseLogger = new_channel('base_logger')

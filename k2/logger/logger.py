#!/usr/bin/env python3

from typing import Optional, Dict, Iterable, Any, Union, List

from .channel import Channel


# key - channel name
# value - LogChannel
Channels = {}  # type: Dict[str, Channel]


def new_channel(key, parent: Union[str, Channel] = 'base_logger', inherite_rights: Optional[Iterable] = None, **kwargs):
    if inherite_rights is None:
        inherite_rights = {'stdout', 'debug', 'autosave', 'std_logging'}
    Channels[key] = Channel(key=key, **kwargs)
    if parent is not None:
        parent = parent if isinstance(parent, Channel) else Channels[parent]
        if key != parent.cfg.key:
            Channels[key].add_parent(
                parent=parent,
                inherite_rights=inherite_rights
            )
    return Channels[key]


def update_channel(key: str, **kwargs) -> None:
    if key in Channels:
        return Channels[key].update(**kwargs)
    raise KeyError(f'channel "{key}" not exists')


def delete_channel(key: str) -> None:
    if isinstance(key, Channel):
        key = key.cfg.key
    Channels.pop(key, None)


async def exception(key: str, msg: str, *args: Any, **kwargs: Any) -> None:
    await Channels[key].exception(
        msg=msg,
        *args,
        **kwargs,
    )


async def error(key: str, msg: str, *args, **kwargs) -> None:
    await Channels[key].error(
        msg=msg,
        level='error',
        *args,
        **kwargs,
    )


async def warning(key: str, msg: str, *args: Any, **kwargs: Any) -> None:
    await Channels[key].warning(
        msg=msg,
        level='warning',
        *args,
        **kwargs,
    )


async def info(key: str, msg: str, *args: Any, **kwargs: Any) -> None:
    await Channels[key].info(
        msg=msg,
        level='info',
        *args,
        **kwargs,
    )


async def debug(key: str, msg: str, *args: Any, **kwargs: Any) -> None:
    await Channels[key].debug(
        msg=msg,
        level='debug',
        *args,
        **kwargs,
    )


def get_channel(key: str) -> Optional[Channel]:
    return Channels.get(key)


def clear() -> None:
    return Channels.clear()


def export(key: str) -> List[Dict[str, Union[str, int]]]:
    if key in Channels:
        return Channels[key].export()
    raise KeyError(f'channel "{key}" not exists')


BaseLogger = new_channel('base_logger')

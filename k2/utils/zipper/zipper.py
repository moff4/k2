from collections import defaultdict
from typing import Dict, List, Tuple

from k2.utils.zipper.classes import (
    Part,
    Node,
    Archive,
)


def compress(
    files: List[Tuple[str, bytes]],
    options: Dict[str, bytes],
    max_arch_size: int=175 * 2 ** 20,
) -> List[bytes]:
    """
        :param list: files list of tulples (filename, data)
        :param dict: options
        :param max_arch_size: max size of any archive
        :rtype list: list of bytes
    """
    nodes = []  # type: List[Node]
    parts = []
    max_part_size = max_arch_size - 20
    for filename, data in files:
        nodes.append(
            node := Node(
                fid=str(len(nodes)),
                name=filename,
            )
        )
        payloads = []
        while data:
            payloads.append(data[:max_part_size])
            data = data[max_part_size:]
        parts.extend(
            [
                Part(
                    fid=node.fid,
                    data=payload,
                    idx=idx,
                    count=len(payloads),
                )
                for idx, payload in enumerate(payloads)
            ]
        )
    parts = sorted(parts, key=lambda p: len(p.data))
    archs = []
    _p = []  # type: List[Part]
    tmp = []  # type: List[Part]
    while parts:
        left = max_arch_size - sum(len(p.data) for p in _p)
        tmp = [
            p
            for p in parts
            if len(p.data) <= left
        ]
        if tmp:
            _p.append(parts.pop(parts.index(tmp[0])))
        else:
            fids = {p.fid for p in _p}
            archs.append(
                Archive(
                    nodes=[n for n in nodes if n.fid in fids],
                    parts=_p
                )
            )
            _p = []
    if tmp:
        fids = {p.fid for p in _p}
        archs.append(
            Archive(
                nodes=[n for n in nodes if n.fid in fids],
                parts=_p
            )
        )

    return [a.marshal(options) for a in archs]


def arch_info(archs: List[bytes], options: Dict[str, bytes]) -> List[Tuple[str, bytes]]:
    """
        :param list: list of bytes
        :param dict: options
        :rtype list: list of tulples (fid, filename)
    """
    _archs = [Archive.unmarshal(a, options) for a in archs]
    return [
        (fid, name)
        for fid, name in {
            n.fid: n.name
            for a in _archs
            for n in a.nodes
        }.items()
    ]


def decompress(archs: List[bytes], options: Dict[str, bytes]) -> List[Tuple[str, bytes]]:
    """
        :param list: list of bytes
        :param dict: options
        :rtype list: list of tulples (filename, data)
    """
    _archs = [Archive.unmarshal(a, options) for a in archs]
    map_fid_name = {
        n.fid: n.name
        for a in _archs
        for n in a.nodes
    }
    fp = defaultdict(list)  # type: Dict[str, List[Part]]
    for a in _archs:
        for p in a.parts:
            if p.fid not in map_fid_name:
                raise ValueError('unknown fid "%s"' % p.fid)
            fp[map_fid_name[p.fid]].append(p)
    return [
        (
            filename,
            b''.join(
                p.data
                for p in sorted(parts, key=lambda p: p.idx)
            )
        )
        for filename, parts in fp.items()
    ]

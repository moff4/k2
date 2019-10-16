from collections import defaultdict

from k2.utils.zipper.classes import (
    Part,
    Node,
    Archive,
)


def compress(files: list, options: dict, max_arch_size: int=175 * 2 ** 20) -> list:
    """
        :param list: files list of tulples (filename, data)
        :param dict: options
        :param max_arch_size: max size of any archive
        :rtype list: list of bytes
    """
    nodes = []
    parts = []
    max_part_size = max_arch_size - 20
    for filename, data in files:
        node = Node(
            fid=len(nodes),
            name=filename,
        )
        nodes.append(node)
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
    _p = []
    tmp = []
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


def arch_info(archs: list, options: dict) -> list:
    """
        :param list: list of bytes
        :param dict: options
        :rtype list: list of tulples (fid, filename)
    """
    archs = [Archive.unmarshal(a, options) for a in archs]
    return [
        (fid, name)
        for fid, name in {
            n.fid: n.name
            for a in archs
            for n in a.nodes
        }.items()
    ]


def decompress(archs: list, options: dict) -> list:
    """
        :param list: list of bytes
        :param dict: options
        :rtype list: list of tulples (filename, data)
    """
    archs = [Archive.unmarshal(a, options) for a in archs]
    map_fid_name = {
        n.fid: n.name
        for a in archs
        for n in a.nodes
    }
    fp = defaultdict(list)
    for a in archs:
        for p in a.parts:
            if p.fid not in map_fid_name:
                raise ValueError('unknown fid "%s"' % p.fid)
            fp[map_fid_name[p.fid]].append(p)
    for filename, parts in fp.items():
        if any((parts[0].count != p.count) for p in parts) or len(parts) != parts[0].count:
            raise ValueError('idx error with "%s"' % filename)
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


from dataclasses import dataclass

from k2.utils.zipper.artfull import ArtMarshalable


@dataclass
class Part(ArtMarshalable):
    fid: str
    data: bytes
    idx: int
    count: int

    def export(self):
        return {
            'f': self.fid,
            'd': self.data,
            'i': self.idx,
            'c': self.count,
        }

    @classmethod
    def _import(cls, data):
        return cls(
            fid=data['f'],
            data=data['d'],
            idx=data['i'],
            count=data['c'],
        )


@dataclass
class Node:
    fid: str
    name: str

    def export(self):
        return {
            'f': self.fid,
            'n': self.name,
        }

    @classmethod
    def _import(cls, data):
        return cls(
            fid=data['f'],
            name=data['n'],
        )


@dataclass
class Archive(ArtMarshalable):
    nodes: list
    parts: list

    def export(self):
        return {
            'n': [node.export() for node in self.nodes],
            'p': [part.export() for part in self.parts],
        }

    @classmethod
    def _import(cls, data):
        return cls(
            nodes=[Node._import(node) for node in data['n']],
            parts=[Part._import(part) for part in data['p']],
        )


from k2.utils import art


class ArtMarshalable:
    def export(self):
        raise NotImplemented

    def import_(self, data):
        raise NotImplemented

    def marshal(self, options):
        return art.marshal(self.export(), mask=options.get('art_mask'))

    @classmethod
    def unmarshal(cls, data, options):
        return cls.import_(art.unmarshal(data, mask=options.get('art_mask')))

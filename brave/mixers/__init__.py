from brave.abstract_collection import AbstractCollection
from brave.mixers.mixer import Mixer


class MixerCollection(AbstractCollection):
    def add(self, **args):
        args['id'] = self.get_new_id()
        mixer = Mixer(**args, collection=self)
        self._items[args['id']] = mixer
        return mixer

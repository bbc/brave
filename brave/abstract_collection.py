'''
Abstract superclass of InputCollection, OutputCollection, MixerCollection, OverlayCollection
'''
import collections.abc
from brave.helpers import get_pipeline_details


class AbstractCollection(collections.abc.MutableMapping):
    def __init__(self, session):
        self.session = session
        self._items = {}
        self._next_id = 1

    def __getitem__(self, key):
        if key in self._items:
            return self._items[key]
        raise KeyError

    def __delitem__(self, key):
        if key in self._items:
            del self._items[key]

    def __setitem__(self, key, value):
        raise Exception('Do not add to a collection directly; use add()')

    def __iter__(self):
        return self._items.__iter__()

    def __len__(self):
        return len(self._items)

    def get_new_id(self):
        #ISTO FAZ COM QUE ELE CRIE POR ORDEM OS IDS
        self._next_id = 1
        while self._next_id in self._items:
            self._next_id += 1
        return self._next_id

    def summarise(self, for_config_file=False):
        s = []
        for id, obj in self.items():
            s.append(obj.summarise())
        return s

    def print_state_summary(self):
        for id, obj in self.items():
            obj.print_state_summary()

    def get_pipeline_details(self, show_inside_bin_elements):
        details = {}
        for id, obj in self.items():
            if hasattr(obj, 'pipeline'):
                details[id] = get_pipeline_details(obj.pipeline, show_inside_bin_elements)
        return details

    def get_entry_with_lowest_id(self):
        '''
        Returns the item with the lowest ID, or None, if there are no items.
        '''
        ids = sorted(self._items.keys())
        if len(ids) == 0:
            return None
        return self._items[ids[0]]

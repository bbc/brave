from brave.abstract_collection import AbstractCollection
from brave.connections.connection import Connection
from brave.connections.connection_to_mixer import ConnectionToMixer
from brave.inputs.input import Input
from brave.outputs.output import Output
from brave.mixers.mixer import Mixer
from brave.exceptions import InvalidConfiguration


class ConnectionCollection(AbstractCollection):
    '''
    A collection of all Connections.
    A Connection connects inputs, mixers, and outputs.
    '''

    def add(self, src, dest, **args):
        if isinstance(src, Output):
            raise ValueError('Cannot have a connection with output as src')
        if isinstance(dest, Input):
            raise ValueError('Cannot have a connection with input as src')
        if isinstance(dest, Output):
            if dest.src_connection() is not None:
                raise InvalidConfiguration('Output %d is already connected to a source' % dest.id)

        args['id'] = self.get_new_id()
        if isinstance(dest, Mixer):
            self._items[args['id']] = ConnectionToMixer(src=src, dest=dest, collection=self, **args)
        else:
            self._items[args['id']] = Connection(src=src, dest=dest, collection=self, **args)
        return self._items[args['id']]

    def get_first_collection_for_src(self, src):
        return next((x for x in self._items.values() if x.src == src), None)

    def get_all_collections_for_src(self, src):
        return list(filter(lambda x: x.src == src, self._items.values()))

    def get_first_collection_for_dest(self, dest):
        return next((x for x in self._items.values() if x.dest == dest), None)

    def get_all_collections_for_dest(self, dest):
        return list(filter(lambda x: x.dest == dest, self._items.values()))

    def get_connection_between_src_and_dest(self, src, dest):
        return next((x for x in self._items.values() if (x.src == src and x.dest == dest)), None)

    def get_or_add_connection_between_src_and_dest(self, src, dest):
        c = self.get_connection_between_src_and_dest(src, dest)
        if c is None:
            return self.add(src, dest)
        else:
            return c

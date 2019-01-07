from brave.abstract_collection import AbstractCollection
from brave.connections.connection_to_mixer import ConnectionToMixer
from brave.connections.connection_to_output import ConnectionToOutput
from brave.inputs.input import Input
from brave.outputs.output import Output
from brave.mixers.mixer import Mixer
from brave.exceptions import InvalidConfiguration


class ConnectionCollection(AbstractCollection):
    '''
    A collection of all Connections.
    A Connection connects inputs, mixers, and outputs.
    '''

    def add(self, source, dest, **args):
        if isinstance(source, Output):
            raise ValueError('Cannot have a connection with output as source')
        if isinstance(dest, Input):
            raise ValueError('Cannot have a connection with input as source')
        if isinstance(dest, Output):
            if dest.source_connection() is not None:
                raise InvalidConfiguration('Output %d is already connected to a source' % dest.id)

        args['id'] = self.get_new_id()
        if isinstance(dest, Mixer):
            self._items[args['id']] = ConnectionToMixer(source=source, dest=dest, collection=self, **args)
        else:
            self._items[args['id']] = ConnectionToOutput(source=source, dest=dest, collection=self, **args)
        return self._items[args['id']]

    def get_first_for_source(self, source):
        return next((x for x in self._items.values() if x.source == source), None)

    def get_all_for_source(self, source):
        return list(filter(lambda x: x.source == source, self._items.values()))

    def get_first_for_dest(self, dest):
        return next((x for x in self._items.values() if x.dest == dest), None)

    def get_all_for_dest(self, dest):
        return list(filter(lambda x: x.dest == dest, self._items.values()))

    def get_connection_between_source_and_dest(self, source, dest):
        return next((x for x in self._items.values() if (x.source == source and x.dest == dest)), None)

    def get_or_add_connection_between_source_and_dest(self, source, dest):
        c = self.get_connection_between_source_and_dest(source, dest)
        if c is None:
            return self.add(source, dest)
        else:
            return c

from brave.mixers.source import Source


class SourceCollection():
    def __init__(self, mixer):
        self.mixer = mixer
        self._items = []

    def get_or_create(self, input_or_mixer):
        '''
        Gets or creates the source that connects an input (or mixer as an an input) to a mixer.
        '''
        already_there = next((x for x in self._items if x.input_or_mixer == input_or_mixer), None)
        if already_there:
            return already_there
        else:
            source = Source(input_or_mixer, self)
            self._items.append(source)
            return source

    def get_for_input_or_mixer(self, input_or_mixer):
        return next((x for x in self._items if x.input_or_mixer == input_or_mixer), None)

    def delete_for_input_or_mixer(self, input_or_mixer):
        source = self.get_for_input_or_mixer(input_or_mixer)
        if source:
            source.delete()

    def get_as_pretty_object(self):
        pretty_sources = []
        for source in self._items:
            input = source.input_or_mixer
            pretty = {
                'id': input.id,
                'type': input.input_output_overlay_or_mixer(),
                'in_mix': source.in_mix()
            }
            pretty_sources.append(pretty)

        return pretty_sources

    def __iter__(self):
        return self._items.__iter__()

    def __len__(self):
        return len(self._items)

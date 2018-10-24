from brave.mixers.source import Source


class SourceCollection():
    def __init__(self, mixer):
        self.mixer = mixer
        self._items = []

    def add(self, input_or_mixer):
        '''
        This connects a source (input or mixer) to a mixer.
        '''
        already_there = next((x for x in self._items if x.input_or_mixer == input_or_mixer), None)
        if not already_there:
            self._items.append(Source(input_or_mixer, self))

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
                'in_mix': input.in_mix()
            }
            pretty_sources.append(pretty)

        return pretty_sources

    def __iter__(self):
        return self._items.__iter__()

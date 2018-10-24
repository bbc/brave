from gi.repository import Gst


class Source():
    '''
    A source for a mixer.
    A source can be either an input or another mixer.
    '''

    def __init__(self, input_or_mixer, collection):
        self.input_or_mixer = input_or_mixer
        self.collection = collection
        self.elements = []

    def set_element_state(self, state):
        for e in self.elements:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.input_or_mixer.logger.warn('Unable to set %s to %s state' % (e.name, state.value_nick.upper()))

    def delete(self):
        self._remove_all_elements()
        self.collection._items.remove(self)

    def _remove_all_elements(self):
        self.set_element_state(Gst.State.NULL)
        for e in self.elements:
            if not self.collection.mixer.pipeline.remove(e):
                self.collection.mixer.logger.warn('Unable to remove %s' % e.name)

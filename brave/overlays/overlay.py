from gi.repository import Gst
from brave.inputoutputoverlay import InputOutputOverlay
import brave.exceptions


class Overlay(InputOutputOverlay):
    '''
    An abstract superclass representing an overlay.
    '''

    def __init__(self, **args):
        super().__init__(**args)
        self.visible = self.props['visible']
        self.create_elements()
        if self.visible:
            self._make_visible()

    def input_output_overlay_or_mixer(self):
        return 'overlay'

    def permitted_props(self):
        return {
            **super().permitted_props(),
            'mixer_id': {
                'type': 'int',
                'default': 0
            }
        }

    def has_audio(self):
        return False   # no such thing as audio on overlays

    def get_state(self):
        if not hasattr(self, 'element'):
            return Gst.State.NULL
        return self.element.get_state(0).state

    def set_state(self, state):
        return self.element.set_state(state) == Gst.StateChangeReturn.SUCCESS

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        self.set_element_values_from_props()
        if not self.props['visible'] and self.visible:
            self._make_invisible()
        if self.props['visible'] and not self.visible:
            self._make_visible()

    def mixer(self):
        '''
        Returns the mixer that this overlay is for
        '''
        return self.session().mixers[self.props['mixer_id']]

    def delete(self):
        '''
        Delete this overlay. Works whether the overlay is visible or not.
        '''
        self._make_invisible()
        if not self.mixer().pipeline.remove(self.element):
            self.logger.warning('Whilst deleting me, unable to remove element')
        self.collection.pop(self.id)
        return True

    def _make_visible(self):
        self.logger.debug('Becoming visible')
        self.element.sync_state_with_parent()
        self.visible = True

        # Reconsider how overlay elements are linked:
        self.collection.ensure_overlays_are_correctly_connected(self.mixer())

    def _make_invisible(self):
        self.logger.debug('Becoming invisible')
        self.visible = False

        # This will remove the connections to/from this overlay:
        self.collection.ensure_overlays_are_correctly_connected(self.mixer())
        self.element.set_state(Gst.State.NULL)

    def ensure_src_pad_not_blocked(self):
        '''
        When unlinking the source (output) pad, it is blocked.
        This unblocks it again, so should be called when it is reconnected.
        '''
        if hasattr(self, 'src_block_probe'):
            src_pad = self.element.get_static_pad('src')
            src_pad.remove_probe(self.src_block_probe)
            delattr(self, 'src_block_probe')

    def getSortValue(self):
        return self.id

    def _update_props(self, new_props):
        '''
        Overrided to validate that the mixer provided exists.
        '''
        if 'mixer_id' in new_props:
            if new_props['mixer_id'] not in self.session().mixers:
                raise brave.exceptions.InvalidConfiguration('Invalid mixer ID provided: "%s"' % new_props['mixer_id'])

        super()._update_props(new_props)

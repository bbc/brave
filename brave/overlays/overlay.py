from gi.repository import Gst
from brave.inputoutputoverlay import InputOutputOverlay
import brave.exceptions


class Overlay(InputOutputOverlay):
    '''
    An abstract superclass representing an overlay.
    '''

    def __init__(self, **args):
        source_uid = None
        if 'source' in args:
            source_uid = args['source']
            del args['source']

        super().__init__(**args)
        self._set_source(source_uid)
        self.visible = self.visible

    def input_output_overlay_or_mixer(self):
        return 'overlay'

    def has_audio(self):
        return False   # no such thing as audio on overlays

    def summarise(self, for_config_file=False):
        s = super().summarise(for_config_file)
        s['source'] = self.source.uid if self.source else None
        return s

    def update(self, updates):
        '''
        Handle updates to this overlay. Overridden to handle update to the input/mixer source.
        '''
        if 'source' in updates and self.source != updates['source']:
            self._set_source(updates['source'])
            self.report_update_to_user()
            del updates['source']

        if 'visible' in updates:
            if not self.visible and updates['visible']:
                if not self.source:
                    raise brave.exceptions.InvalidConfiguration(
                        'Cannot make overlay %d visible - source not set' % self.id)
                self.logger.debug('Becoming visible')
                self._make_visible()
            if self.visible and not updates['visible']:
                self.logger.debug('Becoming invisible')
                self._make_invisible()

        return super().update(updates)

    def _set_source(self, new_source_uid):
        '''
        Called when a new source (input or mixer) is set by the user (either creation or update).
        '''
        if not hasattr(self, 'source'):
            self.source = None

        # Special case - user specifying no source
        if new_source_uid is None:
            if self.source is None:
                return
            self._delete_elements()
            self.source = None
            return

        if hasattr(self, 'source') and self.source is not None and self.source.uid == new_source_uid:
            return

        # If overlay is visible, then it's attached. We must make it invisible first.
        visible = hasattr(self, 'visible') and self.visible
        self._delete_elements()

        self.source = self.session().uid_to_block(new_source_uid, error_if_not_exists=True)

        if self.source is not None:
            self.create_elements()
            if visible:
                self._make_visible()

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        if self.source is None:
            return
        self.set_element_values_from_props()

    def set_element_values_from_props(self):
        pass

    def delete(self):
        '''
        Delete this overlay. Works whether the overlay is visible or not.
        '''
        self._delete_elements()
        self.collection.pop(self.id)
        self.session().report_deleted_item(self)

    def _delete_elements(self):
        if self.source is not None:
            self._make_invisible()
            self.element.set_state(Gst.State.NULL)
            if not self.element.parent.remove(self.element):
                self.logger.warning('Whilst deleting, unable to remove elements')

    def _make_visible(self):
        self.element.sync_state_with_parent()
        self.visible = True
        self.collection.ensure_overlays_are_correctly_connected(self.source)

    def _make_invisible(self):
        self.visible = False
        self.collection.ensure_overlays_are_correctly_connected(self.source)

    def ensure_src_pad_not_blocked(self):
        '''
        When unlinking the source (output) pad, it is blocked.
        This unblocks it again, so should be called when it is reconnected.
        '''
        if hasattr(self, 'src_block_probe'):
            src_pad = self.element.get_static_pad('src')
            src_pad.remove_probe(self.src_block_probe)
            delattr(self, 'src_block_probe')

    def get_sort_value(self):
        return self.id

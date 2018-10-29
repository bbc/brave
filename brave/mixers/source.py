from gi.repository import Gst, GLib
import traceback


class Source():
    '''
    A Source is for a Mixer.
    A Source is part of exactly one SourceCollection.
    A Source can be either an Input or another Mixer.
    '''

    def __init__(self, input_or_mixer, collection):
        self.input_or_mixer = input_or_mixer
        self.logger = input_or_mixer.logger
        self.collection = collection
        self.elements = []

    def mixer(self):
        '''Return the mixer that this source is for'''
        return self.collection.mixer

    def cut(self):
        '''
        Cuts to this source (i.e. replaces all other inputs currently showing with the provided one).
        '''
        # Add first, then remove, so we don't have a period of showing the background.
        if not self.in_mix():
            self.add_to_mix()
        for source in self.mixer().sources:
            if source != self:
                source.remove_from_mix()

    def set_element_state(self, state):
        '''
        Sets all the elements that speifically belong to this source bit of this input
        '''
        for e in self.elements:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.input_or_mixer.logger.warn('Unable to set %s to %s state' % (e.name, state.value_nick.upper()))

    def delete(self, callback=None):
        '''
        Deletes this source. Don't get confused with remove_from_mix()
        '''

        def after_removed_from_mix():
            self._remove_all_elements()
            self.collection._items.remove(self)
            if callback:
                callback()

        self.remove_from_mix(after_removed_from_mix)

    def add_element(self, factory_name, name=None):
        '''
        Add an element on the mixer's pipeline, on behalf of this source
        '''
        e = self.collection.mixer.add_element(factory_name, self.input_or_mixer, name)
        self.elements.append(e)
        return e

    def in_mix(self):
        '''
        Returns True iff this is currently included in the mix
        (and actually showing, not just linked).
        '''
        in_video_mix = hasattr(self.input_or_mixer, 'video_pad_to_connect_to_mix') and \
            self.input_or_mixer.video_pad_to_connect_to_mix.is_linked()
        in_audio_mix = hasattr(self.input_or_mixer, 'audio_pad_to_connect_to_mix') and \
            self.input_or_mixer.audio_pad_to_connect_to_mix.is_linked()
        return in_video_mix or in_audio_mix

    def add_to_mix(self):
        '''
        Places (adds) this input onto the mixer.
        If you want to replace what's on the mix. use source.cut()
        '''
        self.logger.debug('Overlaying to mixer %d' % self.mixer().id)
        if self.input_or_mixer.has_video():
            self._add_video_to_mix()
        if self.input_or_mixer.has_audio():
            self._add_audio_to_mix()
        self._unblock_mix_pads()

        self.set_element_state(self.mixer().pipeline.get_state(0).state)
        self.mixer().report_update_to_user()

    def remove_from_mix(self, callback=None):
        '''
        Removes this source from showing on this mixer
        '''
        if not self.in_mix():
            if callback:
                callback()
            return

        def _set_my_mixer_elements_to_null():
            self.set_element_state(Gst.State.NULL)
            self.logger.info('Completed removal from mix.')
            self.mixer().report_update_to_user()
            if callback:
                callback()

        def _after_removal_from_both_mixes():
            # We set the state of these elements to NULL because we don't need them running.
            # But one of the elements (queue) is the one that this callback is for.
            # So we cannot directly set the state or else a deadlock will occur.
            # Instead, we ask the g event look to do this at the next idle moment.
            GLib.idle_add(_set_my_mixer_elements_to_null)
            self.logger.debug('Completed removal of from mix, except setting state to NULL.')

        def _after_removal_from_video_mix():
            if self.input_or_mixer.has_audio():
                self._remove_from_audio_mix(_after_removal_from_both_mixes)
            else:
                _after_removal_from_both_mixes()

        if self.input_or_mixer.has_video():
            self._remove_from_video_mix(_after_removal_from_video_mix)
        else:
            _after_removal_from_video_mix()

    def handle_updated_props(self):
        '''
        Called after the props have been set/updated, to update the elements
        '''
        if self.input_or_mixer.has_audio():
            self._handle_audio_mix_props()
        if self.input_or_mixer.has_video():
            self._handle_video_mix_props()

    def _add_video_to_mix(self):
        # 'video_pad_to_connect_to_mix' may not exist for test_video if the
        # decoder hasn't kicked in
        if not hasattr(self.input_or_mixer, 'video_pad_to_connect_to_mix'):
            return

        if (self.input_or_mixer.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to mix when already there')
            return

        if hasattr(self, 'video_mix_request_pad'):
            traceback.print_stack()
            self.logger.warn('Already have video_mix_request_pad, should not be possible')

        self.video_mix_request_pad = self.mixer().get_video_mixer_request_pad(self)
        if (self.input_or_mixer.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to video mix when already there')
            return

        self._handle_video_mix_props()
        print('****** TEMP CRASH DISCOVERY: linking input to mix STARTING (%s/%s)' %
              (self.input_or_mixer.video_pad_to_connect_to_mix, self.video_mix_request_pad))
        self.input_or_mixer.video_pad_to_connect_to_mix.link(self.video_mix_request_pad)
        print('****** TEMP CRASH DISCOVERY:  linking input to mix COMPLETE')

    def _add_audio_to_mix(self):
        if (hasattr(self.input_or_mixer, 'audio_pad_to_connect_to_mix') and
                self.input_or_mixer.audio_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to mix when already there')
            return

        if hasattr(self, 'audio_mix_request_pad'):
            self.logger.warn('Already have audio_mix_request_pad, should not be possible')

        self.audio_mix_request_pad = self.mixer().get_audio_mixer_request_pad(self)
        if (self.input_or_mixer.audio_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to audio mix when already there')
            return

        self.input_or_mixer.audio_pad_to_connect_to_mix.link(self.audio_mix_request_pad)
        self._handle_audio_mix_props()

    def _handle_video_mix_props(self):
        '''
        Update the video mixer with the props from this - position on screen, and z-order.
        '''
        if not hasattr(self, 'video_mix_request_pad'):
            return

        self.video_mix_request_pad.set_property('xpos', self.input_or_mixer.props['xpos'])
        self.video_mix_request_pad.set_property('ypos', self.input_or_mixer.props['ypos'])
        self._set_mixer_width_and_height()

        # Setting zorder to what's already set can cause a segfault.
        current_zorder = self.video_mix_request_pad.get_property('zorder')
        if current_zorder != self.input_or_mixer.props['zorder']:
            self.logger.debug('Setting zorder to %d (current state: %s)' %
                              (self.input_or_mixer.props['zorder'],
                               self.mixer().video_mixer.get_state(0).state.value_nick.upper()))
            self.video_mix_request_pad.set_property('zorder', self.input_or_mixer.props['zorder'])

    def _handle_audio_mix_props(self):
        '''
        Update the audio mixer with the props from this - just volume at the moment
        '''
        if not hasattr(self, 'audio_mix_request_pad'):
            return

        prev_volume = self.audio_mix_request_pad.get_property('volume')
        volume = self.input_or_mixer.props['volume']

        if volume != prev_volume:
            # self.logger.debug(f'Setting volume from {str(prev_volume)} to {str(volume)}')
            self.audio_mix_request_pad.set_property('volume', float(volume))

    def _set_mixer_width_and_height(self):
        # First stage: go with mixer's size
        width = self.mixer().props['width']
        height = self.mixer().props['height']

        # Second stage: if input is smaller, go with that
        if 'width' in self.input_or_mixer.props and self.input_or_mixer.props['width'] < width:
            width = self.input_or_mixer.props['width']
        if 'height' in self.input_or_mixer.props and self.input_or_mixer.props['height'] < height:
            height = self.input_or_mixer.props['height']

        # Third stage: if positioned to go off the side, reduce the size.
        if width + self.input_or_mixer.props['xpos'] > self.mixer().props['width']:
            width = self.mixer().props['width'] - self.input_or_mixer.props['xpos']
        if height + self.input_or_mixer.props['ypos'] > self.mixer().props['height']:
            height = self.mixer().props['height'] - self.input_or_mixer.props['ypos']

        self.video_mix_request_pad.set_property('width', width)
        self.video_mix_request_pad.set_property('height', height)
        self.logger.debug('Setting width and height in mixer to be %s and %s' %
                          (self.video_mix_request_pad.get_property('width'),
                           self.video_mix_request_pad.get_property('height')))

    def _unblock_mix_pads(self):
        '''
        Mix pads will have been blocked if previously removed from a mix. This unblocks them.
        '''
        if hasattr(self, 'video_pad_to_mix_probe'):
            self.input_or_mixer.video_pad_to_connect_to_mix.remove_probe(self.video_pad_to_mix_probe)
            delattr(self, 'video_pad_to_mix_probe')
            self.logger.info('Remove block from video mix pad')
        if hasattr(self, 'audio_pad_to_mix_probe'):
            self.input_or_mixer.audio_pad_to_connect_to_mix.remove_probe(self.audio_pad_to_mix_probe)
            delattr(self, 'audio_pad_to_mix_probe')
            self.logger.info('Remove block from audio mix pad')

    def _remove_from_video_mix(self, callback):
        if (not self.input_or_mixer.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to remove from mix when not in video mix')
            callback()
            return

        on_blocked_function_called = False

        def _remove_from_video_mix_now_blocked(*_):
            nonlocal on_blocked_function_called
            if on_blocked_function_called:
                return Gst.PadProbeReturn.OK
            on_blocked_function_called = True

            if hasattr(self, 'video_mix_request_pad'):
                # First, unlink this input from the mixer:
                self.input_or_mixer.video_pad_to_connect_to_mix.unlink(self.video_mix_request_pad)
                # Then, tell the mixer to remove the request (input) pad
                self.mixer().video_mixer.release_request_pad(self.video_mix_request_pad)
                delattr(self, 'video_mix_request_pad')
            callback()

            # We must keep the block in place as the elements are still in PLAYING state:
            return Gst.PadProbeReturn.OK

        self.video_pad_to_mix_probe = self.input_or_mixer.video_pad_to_connect_to_mix.add_probe(
            Gst.PadProbeType.BLOCKING, _remove_from_video_mix_now_blocked, None)

    def _remove_from_audio_mix(self, callback):
        if (not self.input_or_mixer.audio_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to remove from mix when not in audio mix')
            callback()
            return

        on_blocked_function_called = False

        def _remove_from_audio_mix_now_blocked(*_):
            nonlocal on_blocked_function_called
            if on_blocked_function_called:
                return Gst.PadProbeReturn.OK
            on_blocked_function_called = True

            if hasattr(self, 'audio_mix_request_pad'):
                self.input_or_mixer.audio_pad_to_connect_to_mix.unlink(self.audio_mix_request_pad)
                self.mixer().audio_mixer.release_request_pad(self.audio_mix_request_pad)
                delattr(self, 'audio_mix_request_pad')
            callback()

            # We must keep the block in place as the elements are still in PLAYING state:
            return Gst.PadProbeReturn.OK

        self.audio_pad_to_mix_probe = self.input_or_mixer.audio_pad_to_connect_to_mix.add_probe(
            Gst.PadProbeType.BLOCKING, _remove_from_audio_mix_now_blocked)

    def _remove_all_elements(self):
        self.set_element_state(Gst.State.NULL)
        for e in self.elements:
            if not self.mixer().pipeline.remove(e):
                self.collection.mixer.logger.warn('Unable to remove %s' % e.name)

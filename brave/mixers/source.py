from gi.repository import Gst, GLib
from brave.helpers import create_intersink_channel_name, block_pad, unblock_pad
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
        self.elements_on_mixer_pipeline = []
        self.elements_on_input_pipeline = []
        self.probes = {}

    def mixer(self):
        '''
        Return the mixer that this source is for
        '''
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

    def set_mixer_element_state(self, state):
        '''
        Sets all the elements that speifically belong to this source bit of this input
        '''
        for e in self.elements_on_mixer_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.logger.warn('Unable to set mixer element %s to %s state' % (e.name, state.value_nick.upper()))

    def set_input_element_state(self, state):
        '''
        Sets all the elements that speifically belong to this source bit of this input
        '''
        for e in self.elements_on_input_pipeline:
            if e.set_state(state) != Gst.StateChangeReturn.SUCCESS:
                self.logger.warn('Unable to set input element %s to %s state' % (e.name, state.value_nick.upper()))

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

    def in_mix(self):
        '''
        Returns True iff this is currently included in the mix
        (and actually showing, not just linked).
        '''
        in_video_mix = hasattr(self, 'video_pad_to_connect_to_mix') and \
            self.video_pad_to_connect_to_mix.is_linked()
        in_audio_mix = hasattr(self, 'audio_pad_to_connect_to_mix') and \
            self.audio_pad_to_connect_to_mix.is_linked()
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

        self.set_mixer_element_state(self.mixer().pipeline.get_state(0).state)
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
            self.set_mixer_element_state(Gst.State.NULL)
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

    def on_input_pipeline_start(self):
        '''
        Called when the input (or source mixer) starts
        '''
        self._unblock_intersrc_if_mixer_is_ready()

    def set_new_caps(self, new_caps):
        if hasattr(self, 'capsfilter_after_intervideosrc'):
            self.capsfilter_after_intervideosrc.set_property('caps', new_caps)
            # caps-change-mode=1 allows the old caps to temporarily exist during the crossover period.
            self.capsfilter_after_intervideosrc.set_property('caps-change-mode', 1)

    def _unblock_intersrc_if_mixer_is_ready(self):
        if self.mixer().get_state() in [Gst.State.PLAYING, Gst.State.PAUSED]:
                unblock_pad(self, 'intervideosrc_src_pad')
                unblock_pad(self, 'interaudiosrc_src_pad')
        # otherwise, mixer will unblock when it does start.

    def _add_video_to_mix(self):

        # Connect the input (or source mixer) and the mixer, unless that's already been done
        if not hasattr(self, 'video_is_linked'):
            self._create_intervideo_elements()
            self.video_is_linked = True

        # 'video_pad_to_connect_to_mix' may not exist if decoder hasn't kicked in
        if not hasattr(self, 'video_pad_to_connect_to_mix'):
            return

        if (self.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to mix when already there')
            return

        if hasattr(self, 'video_mix_request_pad'):
            traceback.print_stack()
            self.logger.warn('Already have video_mix_request_pad, should not be possible')

        self.video_mix_request_pad = self.mixer().get_video_mixer_request_pad(self)
        if (self.video_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to video mix when already there')
            return

        self._handle_video_mix_props()
        # print('****** TEMP CRASH DISCOVERY: linking input to mix STARTING (%s/%s)' %
        #       (self.video_pad_to_connect_to_mix, self.video_mix_request_pad))
        # print('****** TEMP CRASH DISCOVERY: parent 1:',self.video_pad_to_connect_to_mix.parent)
        # print('****** TEMP CRASH DISCOVERY: parent 2:',self.video_mix_request_pad.parent)
        # print('****** TEMP CRASH DISCOVERY: grandparent 1:',self.video_pad_to_connect_to_mix.parent.parent)
        # print('****** TEMP CRASH DISCOVERY: grandparent 2:',self.video_mix_request_pad.parent.parent)
        self.video_pad_to_connect_to_mix.link(self.video_mix_request_pad)
        # print('****** TEMP CRASH DISCOVERY:  linking input to mix COMPLETE')

    def _add_audio_to_mix(self):
        # Connect the input (or source mixer) and the mixer, unless that's already been done
        if not hasattr(self, 'audio_is_linked'):
            self._create_interaudio_elements()
            self.audio_is_linked = True

        if (hasattr(self, 'audio_pad_to_connect_to_mix') and
                self.audio_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to mix when already there')
            return

        if hasattr(self, 'audio_mix_request_pad'):
            self.logger.warn('Already have audio_mix_request_pad, should not be possible')

        self.audio_mix_request_pad = self.mixer().get_audio_mixer_request_pad(self)
        if (self.audio_pad_to_connect_to_mix.is_linked()):
            self.logger.info('Attempted to add to audio mix when already there')
            return

        self.audio_pad_to_connect_to_mix.link(self.audio_mix_request_pad)
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
            self.video_pad_to_connect_to_mix.remove_probe(self.video_pad_to_mix_probe)
            delattr(self, 'video_pad_to_mix_probe')
            self.logger.debug('Remove block from video mix pad')
        if hasattr(self, 'audio_pad_to_mix_probe'):
            self.audio_pad_to_connect_to_mix.remove_probe(self.audio_pad_to_mix_probe)
            delattr(self, 'audio_pad_to_mix_probe')
            self.logger.debug('Remove block from audio mix pad')

    def _create_intervideo_elements(self):
        '''
        Create the 'intervideosrc' element, which accepts the video input that's come from a separate pipeline.
        Then connects intervideosrc to the convert/scale/queue elements, ready for mixing.
        '''

        intervideosrc = self._create_intervideosrc()
        intervideosink = self._create_intersink('video')

        # Give the 'inter' elements a channel name. It doesn't matter what, so long as they're unique.
        channel_name = create_intersink_channel_name()
        intervideosink.set_property('channel', channel_name)
        intervideosrc.set_property('channel', channel_name)

        videoscale = self._add_element_to_mixer_pipeline('videoscale')
        intervideosrc.link(videoscale)

        # Decent scaling options:
        videoscale.set_property('method', 3)
        videoscale.set_property('dither', True)

        videoconvert = self._add_element_to_mixer_pipeline('videoconvert')
        videoscale.link(videoconvert)

        self.capsfilter_after_intervideosrc = self._add_element_to_mixer_pipeline('capsfilter')
        videoconvert.link(self.capsfilter_after_intervideosrc)

        queue = self._add_element_to_mixer_pipeline('queue', name='video_queue')
        self.capsfilter_after_intervideosrc.link(queue)

        self.video_pad_to_connect_to_mix = queue.get_static_pad('src')
        self._sync_element_states()

    def _create_interaudio_elements(self):
        '''
        The audio equivalent of _create_intervideo_elements
        '''
        interaudiosrc = self._create_interaudiosrc()
        interaudiosink = self._create_intersink('audio')

        # Give the 'inter' elements a channel name. It doesn't matter what, so long as they're unique.
        channel_name = create_intersink_channel_name()
        interaudiosink.set_property('channel', channel_name)
        interaudiosrc.set_property('channel', channel_name)

        self.audio_pad_to_connect_to_mix = interaudiosrc.get_static_pad('src')
        self._sync_element_states()

    def _create_intervideosrc(self):
        '''
        The intervideosrc goes on the destination (mixer) pipeline, so that it
        can accept video from the source pipeline.
        '''
        # Create the receiving 'inter' element to accept the AV into the main pipeline
        intervideosrc = self._add_element_to_mixer_pipeline('intervideosrc')
        self.intervideosrc_src_pad = intervideosrc.get_static_pad('src')

        # We ask the src to hold the frame for 24 hours (basically, a very long time)
        # This is optional, but prevents it from going black when it's better to show the last frame.
        intervideosrc.set_property('timeout', Gst.SECOND * 60 * 60 * 24)

        # We block the source (output) pad of this intervideosrc until we're sure video is being sent.
        # Otherwise we can get a partial message, which causes an error.
        block_pad(self, 'intervideosrc_src_pad')
        return intervideosrc

    def _create_interaudiosrc(self):
        '''
        The interaudiosrc goes on the destination (mixer) pipeline, so that it
        can accept audio from the source pipeline.
        '''
        # Create the receiving 'inter' elements to accept the AV into the main pipeline
        interaudiosrc = self._add_element_to_mixer_pipeline('interaudiosrc')
        self.interaudiosrc_src_pad = interaudiosrc.get_static_pad('src')

        # Blocks the src pad to stop incomplete messages.
        # Note, this has caused issues in the past.
        block_pad(self, 'interaudiosrc_src_pad')
        return interaudiosrc

    def _create_intersink(self, audio_or_video):
        '''
        The intervideosink/interaudiosink goes on the source (input/mixer) pipeline, so that it can
        connect to the mixer pipeline.
        '''
        assert(audio_or_video in ['audio', 'video'])
        element_name = 'inter%ssink' % audio_or_video
        if audio_or_video == 'video':
            input_bin = self.input_or_mixer.final_video_tee.parent
            tee = self.input_or_mixer.final_video_tee
        else:
            input_bin = self.input_or_mixer.final_audio_tee.parent
            tee = self.input_or_mixer.final_audio_tee
        element = self._add_element_to_input_pipeline(element_name, input_bin=input_bin)
        queue = self._add_element_to_input_pipeline('queue', input_bin=input_bin)
        if not element or not queue:
            return

        # Increasing to 3 seconds allows different encoders to share a pipeline.
        # This can be reconsidered if/when outputs are put on different pipelines.
        MAX_SIZE_IN_SECONDS = 3
        queue.set_property('max-size-time', MAX_SIZE_IN_SECONDS * 1000000000)
        queue.set_property('max-size-bytes', MAX_SIZE_IN_SECONDS * 10485760)

        tee_src_pad_template = tee.get_pad_template("src_%u")
        tee_src_pad = tee.request_pad(tee_src_pad_template, None, None)

        sink = queue.get_static_pad('sink')
        if tee_src_pad.link(sink) != Gst.PadLinkReturn.OK:
            self.logger.error('Failed to connect tee to queue before %s' % element_name)

        if not queue.link(element):
            self.logger.error('Failed to connect queue to %s' % element_name)
        return element

    def _remove_from_video_mix(self, callback):
        if (not self.video_pad_to_connect_to_mix.is_linked()):
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
                self.video_pad_to_connect_to_mix.unlink(self.video_mix_request_pad)
                # Then, tell the mixer to remove the request (input) pad
                self.mixer().video_mixer.release_request_pad(self.video_mix_request_pad)
                delattr(self, 'video_mix_request_pad')
            callback()

            # We must keep the block in place as the elements are still in PLAYING state:
            return Gst.PadProbeReturn.OK

        self.video_pad_to_mix_probe = self.video_pad_to_connect_to_mix.add_probe(
            Gst.PadProbeType.BLOCKING, _remove_from_video_mix_now_blocked, None)

    def _remove_from_audio_mix(self, callback):
        if (not self.audio_pad_to_connect_to_mix.is_linked()):
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
                self.audio_pad_to_connect_to_mix.unlink(self.audio_mix_request_pad)
                self.mixer().audio_mixer.release_request_pad(self.audio_mix_request_pad)
                delattr(self, 'audio_mix_request_pad')
            callback()

            # We must keep the block in place as the elements are still in PLAYING state:
            return Gst.PadProbeReturn.OK

        self.audio_pad_to_mix_probe = self.audio_pad_to_connect_to_mix.add_probe(
            Gst.PadProbeType.BLOCKING, _remove_from_audio_mix_now_blocked)

    def _remove_all_elements(self):
        '''
        Remove all elements for this rouce, which will be partly on the mixer and partly on the input.
        '''
        self.set_mixer_element_state(Gst.State.NULL)
        for e in self.elements_on_mixer_pipeline:
            if not self.mixer().pipeline.remove(e):
                self.collection.mixer.logger.warn('Unable to remove %s' % e.name)

        self.set_input_element_state(Gst.State.NULL)
        for e in self.elements_on_input_pipeline:
            if not self.input_or_mixer.pipeline.remove(e):
                self.collection.mixer.logger.warn('Unable to remove %s' % e.name)

    def _add_element_to_mixer_pipeline(self, factory_name, name=None):
        '''
        Add an element on the mixer's pipeline, on behalf of this source
        '''
        e = self.collection.mixer.add_element(factory_name, self.input_or_mixer, name)
        self.elements_on_mixer_pipeline.append(e)
        return e

    def _add_element_to_input_pipeline(self, factory_name, input_bin, name=None):
        '''
        Add an element on the mixer's pipeline, on behalf of this source
        '''
        e = Gst.ElementFactory.make(factory_name, name)
        if not input_bin.add(e):
            self.logger.error('Unable to add element %s' % factory_name)
            return None
        self.elements_on_input_pipeline.append(e)
        return e

    def _sync_element_states(self):
        '''
        Make sure the elements created on the source and destination have their state set to match their pipeline.
        '''
        for e in self.elements_on_mixer_pipeline:
            if not e.sync_state_with_parent():
                self.logger.warn('Unable to set %s to state of parent source' % e.name)
        for e in self.elements_on_input_pipeline:
            if not e.sync_state_with_parent():
                self.logger.warn('Unable to set %s to state of parent source' % e.name)
